"""
Research-grade ML training pipeline.

Trains and compares:
  A. Random Forest (sklearn)
  B. XGBoost       (xgboost)
  C. CNN           (TensorFlow/Keras)
  D. LSTM          (TensorFlow/Keras)

Key design decisions for publication-trustworthy results:
  - File-based or temporal split (NOT random) to prevent train/test leakage
  - Class-aware deduplication
  - BENIGN undersampling (2x attack count)
  - Regularised hyperparameters (depth caps, dropout, early stopping)
  - Isolation Forest for unknown threat detection
  - Full research metrics (Macro-F1, ADR, FPR, FNR, ROC-AUC)
  - Automatic accuracy > 95% warning

Usage:
    cd backend
    python ml_model/train_research_models.py
    python ml_model/train_research_models.py --split temporal
    python ml_model/train_research_models.py --split attack_holdout --holdout PortScan
    python ml_model/train_research_models.py --fast
    python ml_model/train_research_models.py --skip-deep   # skip CNN/LSTM
"""

import argparse
import logging
import sys
import os
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.utils.class_weight import compute_sample_weight

from research_preprocess import research_pipeline, DATASET_DIR
from leakage_checker import check_leakage
from feature_engineering import describe_features
from evaluation import evaluate_and_report
from unknown_attack_detector import train_isolation_forest

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

BASE_DIR         = Path(__file__).parent
SAVED_MODELS_DIR = BASE_DIR / "saved_models"
REPORTS_DIR      = BASE_DIR / "reports"


# ── Random Forest ─────────────────────────────────────────────────────────────

def train_random_forest(X_train: np.ndarray, y_train: np.ndarray,
                         X_test: np.ndarray,  y_test: np.ndarray) -> dict:
    log.info("\n" + "-" * 50)
    log.info("Training: RANDOM FOREST (research)")
    model = RandomForestClassifier(
        n_estimators   = 300,
        max_depth       = 15,
        min_samples_leaf= 4,
        max_features    = "sqrt",
        class_weight    = "balanced",
        n_jobs          = -1,
        random_state    = 42,
    )
    t0 = time.perf_counter()
    model.fit(X_train, y_train)
    train_time = time.perf_counter() - t0
    log.info(f"  Train time: {train_time:.2f}s")

    t1     = time.perf_counter()
    y_pred = model.predict(X_test)
    pred_t = time.perf_counter() - t1

    y_proba = model.predict_proba(X_test) if hasattr(model, "predict_proba") else None

    SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = SAVED_MODELS_DIR / "random_forest_research.pkl"
    joblib.dump(model, path)
    log.info(f"  Saved → {path}")
    return {"model": model, "y_pred": y_pred, "y_proba": y_proba,
            "y_test": y_test, "train_time": train_time, "pred_time": pred_t}


# ── XGBoost ───────────────────────────────────────────────────────────────────

def train_xgboost(X_train: np.ndarray, y_train: np.ndarray,
                   X_test: np.ndarray,  y_test: np.ndarray) -> dict | None:
    try:
        from xgboost import XGBClassifier
    except ImportError:
        log.warning("xgboost not installed — skipping XGBoost training.")
        return None

    log.info("\n" + "-" * 50)
    log.info("Training: XGBOOST (research)")
    n_classes = len(np.unique(y_train))
    model     = XGBClassifier(
        n_estimators         = 300,
        max_depth            = 7,
        learning_rate        = 0.08,
        subsample            = 0.85,
        colsample_bytree     = 0.85,
        reg_alpha            = 0.1,
        reg_lambda           = 1.0,
        use_label_encoder    = False,
        eval_metric          = "mlogloss",
        objective            = "multi:softprob",
        num_class            = n_classes,
        n_jobs               = -1,
        random_state         = 42,
        verbosity            = 0,
    )
    sw = compute_sample_weight("balanced", y_train)
    t0 = time.perf_counter()
    model.fit(X_train, y_train, sample_weight=sw,
              eval_set=[(X_test, y_test)], verbose=False)
    train_time = time.perf_counter() - t0
    log.info(f"  Train time: {train_time:.2f}s")

    t1     = time.perf_counter()
    y_pred = model.predict(X_test)
    pred_t = time.perf_counter() - t1

    y_proba = model.predict_proba(X_test) if hasattr(model, "predict_proba") else None

    path = SAVED_MODELS_DIR / "xgboost_research.pkl"
    joblib.dump(model, path)
    log.info(f"  Saved → {path}")
    return {"model": model, "y_pred": y_pred, "y_proba": y_proba,
            "y_test": y_test, "train_time": train_time, "pred_time": pred_t}


# ── CNN ───────────────────────────────────────────────────────────────────────

def train_cnn(X_train: np.ndarray, y_train: np.ndarray,
              X_test: np.ndarray,  y_test: np.ndarray,
              n_classes: int) -> dict | None:
    try:
        import tensorflow as tf
        from tensorflow import keras
    except ImportError:
        log.warning("TensorFlow not installed — skipping CNN training.")
        return None

    log.info("\n" + "-" * 50)
    log.info("Training: CNN (research)")
    tf.random.set_seed(42)

    n_features = X_train.shape[1]
    X_tr_3d    = X_train.reshape(-1, n_features, 1)
    X_te_3d    = X_test.reshape(-1,  n_features, 1)

    sw = compute_sample_weight("balanced", y_train)

    inputs = keras.Input(shape=(n_features, 1))
    x = keras.layers.Conv1D(64,  kernel_size=5, padding="same", activation="relu")(inputs)
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
        optimizer = keras.optimizers.Adam(learning_rate=0.001),
        loss      = "sparse_categorical_crossentropy",
        metrics   = ["accuracy"],
    )

    callbacks = [
        keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True, monitor="val_loss"),
        keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=3, monitor="val_loss"),
    ]

    t0 = time.perf_counter()
    model.fit(
        X_tr_3d, y_train,
        epochs          = 50,
        batch_size      = 512,
        validation_split= 0.1,
        sample_weight   = sw,
        callbacks       = callbacks,
        verbose         = 1,
    )
    train_time = time.perf_counter() - t0
    log.info(f"  Train time: {train_time:.2f}s")

    t1     = time.perf_counter()
    y_proba = model.predict(X_te_3d, verbose=0)
    y_pred  = np.argmax(y_proba, axis=1)
    pred_t  = time.perf_counter() - t1

    path = SAVED_MODELS_DIR / "cnn_research.keras"
    model.save(path)
    log.info(f"  Saved → {path}")
    return {"model": model, "y_pred": y_pred, "y_proba": y_proba,
            "y_test": y_test, "train_time": train_time, "pred_time": pred_t}


# ── LSTM ──────────────────────────────────────────────────────────────────────

def train_lstm(X_train: np.ndarray, y_train: np.ndarray,
               X_test: np.ndarray,  y_test: np.ndarray,
               n_classes: int) -> dict | None:
    try:
        import tensorflow as tf
        from tensorflow import keras
    except ImportError:
        log.warning("TensorFlow not installed — skipping LSTM training.")
        return None

    log.info("\n" + "-" * 50)
    log.info("Training: LSTM (research)")
    tf.random.set_seed(42)

    n_features  = X_train.shape[1]
    timesteps   = 10
    feat_per_ts = n_features // timesteps
    remainder   = n_features % timesteps

    # Pad to make divisible by timesteps
    if remainder:
        pad     = timesteps - remainder
        X_train = np.hstack([X_train, np.zeros((len(X_train), pad))])
        X_test  = np.hstack([X_test,  np.zeros((len(X_test),  pad))])
        n_features = X_train.shape[1]
        feat_per_ts = n_features // timesteps

    X_tr_seq = X_train.reshape(-1, timesteps, feat_per_ts)
    X_te_seq = X_test.reshape( -1, timesteps, feat_per_ts)

    sw = compute_sample_weight("balanced", y_train)

    inputs = keras.Input(shape=(timesteps, feat_per_ts))
    x      = keras.layers.LSTM(128, return_sequences=True)(inputs)
    x      = keras.layers.Dropout(0.3)(x)
    x      = keras.layers.LSTM(64)(x)
    x      = keras.layers.Dropout(0.3)(x)
    x      = keras.layers.Dense(128, activation="relu")(x)
    x      = keras.layers.Dropout(0.25)(x)
    outputs= keras.layers.Dense(n_classes, activation="softmax")(x)

    model = keras.Model(inputs, outputs)
    model.compile(
        optimizer = "adam",
        loss      = "sparse_categorical_crossentropy",
        metrics   = ["accuracy"],
    )

    callbacks = [
        keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True, monitor="val_loss"),
        keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=3, monitor="val_loss"),
    ]

    t0 = time.perf_counter()
    model.fit(
        X_tr_seq, y_train,
        epochs          = 40,
        batch_size      = 512,
        validation_split= 0.1,
        sample_weight   = sw,
        callbacks       = callbacks,
        verbose         = 1,
    )
    train_time = time.perf_counter() - t0
    log.info(f"  Train time: {train_time:.2f}s")

    t1      = time.perf_counter()
    y_proba = model.predict(X_te_seq, verbose=0)
    y_pred  = np.argmax(y_proba, axis=1)
    pred_t  = time.perf_counter() - t1

    path = SAVED_MODELS_DIR / "lstm_research.keras"
    model.save(path)
    log.info(f"  Saved → {path}")
    return {"model": model, "y_pred": y_pred, "y_proba": y_proba,
            "y_test": y_test, "train_time": train_time, "pred_time": pred_t}


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Research-grade CICIDS2017 ML pipeline")
    parser.add_argument("--split",   default="file",
                        choices=["random", "file", "temporal", "attack_holdout"],
                        help="Train/test split strategy (default: file)")
    parser.add_argument("--holdout", default="PortScan",
                        help="Attack family to hold out (attack_holdout mode)")
    parser.add_argument("--fast",    action="store_true",
                        help="Use smaller sample caps for faster iteration")
    parser.add_argument("--skip-deep", action="store_true",
                        help="Skip CNN and LSTM training (faster)")
    parser.add_argument("--no-leakage-check", action="store_true",
                        help="Skip data leakage check")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("CICIDS2017 — Research ML Training Pipeline")
    log.info(f"Split mode : {args.split}")
    log.info(f"Fast mode  : {args.fast}")
    log.info(f"Skip deep  : {args.skip_deep}")
    log.info("=" * 60)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Preprocess ─────────────────────────────────────────────────────────────
    data = research_pipeline(
        dataset_dir      = DATASET_DIR,
        saved_models_dir = SAVED_MODELS_DIR,
        split_mode       = args.split,
        holdout_attack   = args.holdout,
        fast_mode        = args.fast,
    )

    X_train        = data["X_train"]
    X_test         = data["X_test"]
    X_train_scaled = data["X_train_scaled"]
    X_test_scaled  = data["X_test_scaled"]
    y_train        = data["y_train"]
    y_test         = data["y_test"]
    n_classes      = len(data["class_names"])

    # ── Leakage check (quick, on subsample) ────────────────────────────────────
    if not args.no_leakage_check:
        import pandas as pd
        files = sorted(DATASET_DIR.glob("*.csv"))
        if files:
            log.info("\nRunning leakage check on first CSV file...")
            df_sample = pd.read_csv(files[0], low_memory=False)
            df_sample.columns = df_sample.columns.str.strip()
            lc = next((c for c in df_sample.columns if "label" in c.lower()), None)
            if lc:
                check_leakage(df_sample, lc, REPORTS_DIR)

    # ── Train models ──────────────────────────────────────────────────────────
    results = {}

    rf = train_random_forest(X_train, y_train, X_test, y_test)
    results["random_forest_research"] = rf

    xgb = train_xgboost(X_train, y_train, X_test, y_test)
    if xgb:
        results["xgboost_research"] = xgb

    if not args.skip_deep:
        cnn = train_cnn(X_train_scaled, y_train, X_test_scaled, y_test, n_classes)
        if cnn:
            results["cnn_research"] = cnn

        lstm = train_lstm(X_train_scaled, y_train, X_test_scaled, y_test, n_classes)
        if lstm:
            results["lstm_research"] = lstm

    # ── Evaluate ──────────────────────────────────────────────────────────────
    evaluate_and_report(results, data, REPORTS_DIR, split_mode=args.split)

    # ── Train Isolation Forest for unknown threat detection ────────────────────
    log.info("\nTraining Isolation Forest for unknown threat detection...")
    train_isolation_forest(X_train_scaled, y_train, data["label_encoder"])

    # ── Done ──────────────────────────────────────────────────────────────────
    log.info("\n" + "=" * 60)
    log.info("Research training complete.")
    log.info(f"Models  : {SAVED_MODELS_DIR}")
    log.info(f"Reports : {REPORTS_DIR}")
    log.info("=" * 60)
    log.info("\nKey reports generated:")
    for f in sorted(REPORTS_DIR.iterdir()):
        log.info(f"  {f.name}")


if __name__ == "__main__":
    main()
