"""
Train CNN and LSTM on the CICIoT2023 dataset and persist real per-epoch
training history (accuracy/loss) for research-paper learning-curve figures.

This reuses the SAME CNN/LSTM architectures defined in train_research_models.py,
but loads the CICIoT2023 train/validation/test folders (the data that is actually
present on this machine) via preprocess_ciciot2023, and uses the dedicated
validation folder for validation instead of a random validation_split.

Outputs (consumed by the figure generator — no fabricated numbers):
  reports/training_history_cnn_research.json
  reports/training_history_lstm_research.json

Usage:
    cd backend
    python ml_model/train_deep_curves.py
    python ml_model/train_deep_curves.py --fast   # subsample for a quick run
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from sklearn.utils.class_weight import compute_sample_weight

from preprocess_ciciot2023 import preprocess_ciciot2023

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
SAVED_MODELS_DIR = BASE_DIR / "saved_models"
REPORTS_DIR = BASE_DIR / "reports"
DATASET_DIR = Path(
    os.environ.get(
        "CICIOT_DATASET_DIR",
        r"C:\Users\Manus\OneDrive\Desktop\L-thirupathi\dataset\archive (3)\CICIOT23",
    )
)


def _write_history(model_key: str, hist: dict) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "model": model_key,
        "dataset": "CICIoT2023",
        "epochs": len(next(iter(hist.values()))) if hist else 0,
        "history": hist,
    }
    path = REPORTS_DIR / f"training_history_{model_key}.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2)


def _save_history(model_key: str, history) -> None:
    hist = {k: [float(v) for v in vals] for k, vals in history.history.items()}
    _write_history(model_key, hist)
    log.info(f"  Saved training history -> "
             f"{REPORTS_DIR / f'training_history_{model_key}.json'}")


def _history_callback(model_key: str):
    """Keras callback that persists per-epoch history JSON after EVERY epoch,
    so an interruption (sleep/kill) never loses completed-epoch data."""
    from tensorflow import keras

    class _Saver(keras.callbacks.Callback):
        def __init__(self):
            super().__init__()
            self.acc = {}

        def on_epoch_end(self, epoch, logs=None):
            logs = logs or {}
            for k, v in logs.items():
                self.acc.setdefault(k, []).append(float(v))
            _write_history(model_key, self.acc)

    return _Saver()


def train_cnn(X_train, y_train, X_val, y_val, n_classes):
    from tensorflow import keras
    import tensorflow as tf

    log.info("\n" + "-" * 50)
    log.info("Training: CNN (CICIoT2023)")
    tf.random.set_seed(42)

    n_features = X_train.shape[1]
    X_tr_3d = X_train.reshape(-1, n_features, 1)
    X_va_3d = X_val.reshape(-1, n_features, 1)

    sw = compute_sample_weight("balanced", y_train)

    inputs = keras.Input(shape=(n_features, 1))
    x = keras.layers.Conv1D(64, kernel_size=5, padding="same", activation="relu")(inputs)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.Conv1D(128, kernel_size=3, padding="same", activation="relu")(x)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.GlobalAveragePooling1D()(x)
    x = keras.layers.Dense(256, activation="relu")(x)
    x = keras.layers.Dropout(0.4)(x)
    x = keras.layers.Dense(128, activation="relu")(x)
    x = keras.layers.Dropout(0.3)(x)
    outputs = keras.layers.Dense(n_classes, activation="softmax")(x)

    model = keras.Model(inputs, outputs)
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks = [
        keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True, monitor="val_loss"),
        keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=3, monitor="val_loss"),
        _history_callback("cnn_research"),
    ]

    t0 = time.perf_counter()
    history = model.fit(
        X_tr_3d, y_train,
        epochs=25,
        batch_size=512,
        validation_data=(X_va_3d, y_val),
        sample_weight=sw,
        callbacks=callbacks,
        verbose=2,
    )
    log.info(f"  Train time: {time.perf_counter() - t0:.2f}s")

    model.save(SAVED_MODELS_DIR / "cnn_research.keras")
    _save_history("cnn_research", history)


def train_lstm(X_train, y_train, X_val, y_val, n_classes):
    from tensorflow import keras
    import tensorflow as tf

    log.info("\n" + "-" * 50)
    log.info("Training: LSTM (CICIoT2023)")
    tf.random.set_seed(42)

    n_features = X_train.shape[1]
    timesteps = 10
    remainder = n_features % timesteps
    if remainder:
        pad = timesteps - remainder
        X_train = np.hstack([X_train, np.zeros((len(X_train), pad))])
        X_val = np.hstack([X_val, np.zeros((len(X_val), pad))])
        n_features = X_train.shape[1]
    feat_per_ts = n_features // timesteps

    X_tr_seq = X_train.reshape(-1, timesteps, feat_per_ts)
    X_va_seq = X_val.reshape(-1, timesteps, feat_per_ts)

    sw = compute_sample_weight("balanced", y_train)

    inputs = keras.Input(shape=(timesteps, feat_per_ts))
    x = keras.layers.LSTM(128, return_sequences=True)(inputs)
    x = keras.layers.Dropout(0.3)(x)
    x = keras.layers.LSTM(64)(x)
    x = keras.layers.Dropout(0.3)(x)
    x = keras.layers.Dense(128, activation="relu")(x)
    x = keras.layers.Dropout(0.25)(x)
    outputs = keras.layers.Dense(n_classes, activation="softmax")(x)

    model = keras.Model(inputs, outputs)
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks = [
        keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True, monitor="val_loss"),
        keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=3, monitor="val_loss"),
        _history_callback("lstm_research"),
    ]

    t0 = time.perf_counter()
    history = model.fit(
        X_tr_seq, y_train,
        epochs=25,
        batch_size=512,
        validation_data=(X_va_seq, y_val),
        sample_weight=sw,
        callbacks=callbacks,
        verbose=2,
    )
    log.info(f"  Train time: {time.perf_counter() - t0:.2f}s")

    model.save(SAVED_MODELS_DIR / "lstm_research.keras")
    _save_history("lstm_research", history)


CACHE_DIR = BASE_DIR / "saved_models" / "_deep_cache"


def _load_or_cache_data(train_n: int, val_n: int):
    """Preprocess once, then cache subsampled scaled arrays to .npy so repeated
    runs skip the expensive 5-min CICIoT2023 load/clip/scale step."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    files = {k: CACHE_DIR / f"{k}.npy" for k in
             ["X_train", "y_train", "X_val", "y_val"]}
    meta = CACHE_DIR / "n_classes.txt"

    if all(f.exists() for f in files.values()) and meta.exists():
        log.info("Loading cached preprocessed arrays (skipping dataset load)...")
        X_train = np.load(files["X_train"]); y_train = np.load(files["y_train"])
        X_val = np.load(files["X_val"]); y_val = np.load(files["y_val"])
        n_classes = int(meta.read_text().strip())
        return X_train, y_train, X_val, y_val, n_classes

    data = preprocess_ciciot2023(dataset_dir=DATASET_DIR, saved_models_dir=SAVED_MODELS_DIR)
    X_train = data["X_train_scaled"]; y_train = data["y_train"]
    X_val = data["X_val_scaled"]; y_val = data["y_val"]
    n_classes = len(data["class_names"])

    if len(X_train) > train_n:
        idx = np.random.default_rng(42).choice(len(X_train), train_n, replace=False)
        X_train, y_train = X_train[idx], y_train[idx]
    if len(X_val) > val_n:
        vidx = np.random.default_rng(7).choice(len(X_val), val_n, replace=False)
        X_val, y_val = X_val[vidx], y_val[vidx]

    np.save(files["X_train"], X_train); np.save(files["y_train"], y_train)
    np.save(files["X_val"], X_val); np.save(files["y_val"], y_val)
    meta.write_text(str(n_classes))
    log.info(f"Cached preprocessed arrays -> {CACHE_DIR}")
    return X_train, y_train, X_val, y_val, n_classes


def main():
    parser = argparse.ArgumentParser(description="Train CNN/LSTM on CICIoT2023 and save learning curves")
    parser.add_argument("--fast", action="store_true",
                        help="Subsample train set to 200k rows for a quick run")
    parser.add_argument("--prep-only", action="store_true",
                        help="Only build the preprocessed cache, then exit")
    parser.add_argument("--cnn-only", action="store_true", help="Train CNN only")
    parser.add_argument("--lstm-only", action="store_true", help="Train LSTM only")
    parser.add_argument("--train-n", type=int, default=200_000)
    parser.add_argument("--val-n", type=int, default=150_000)
    args = parser.parse_args()

    try:
        import tensorflow as tf  # noqa: F401
    except ImportError:
        log.error("TensorFlow is not installed. Run: pip install tensorflow")
        sys.exit(1)

    train_n = 100_000 if args.fast else args.train_n
    val_n = 80_000 if args.fast else args.val_n

    X_train, y_train, X_val, y_val, n_classes = _load_or_cache_data(train_n, val_n)
    log.info(f"Train: {X_train.shape} | Val: {X_val.shape} | Classes: {n_classes}")

    if args.prep_only:
        log.info("Prep-only: cache built, exiting.")
        return

    SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if not args.lstm_only:
        train_cnn(X_train, y_train, X_val, y_val, n_classes)
    if not args.cnn_only:
        train_lstm(X_train, y_train, X_val, y_val, n_classes)

    log.info("\n" + "=" * 60)
    log.info("Done. Learning-curve history written to:")
    log.info(f"  {REPORTS_DIR / 'training_history_cnn_research.json'}")
    log.info(f"  {REPORTS_DIR / 'training_history_lstm_research.json'}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
