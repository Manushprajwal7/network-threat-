"""
Train only the remaining models (XGBoost and Naive Bayes).
Skips already-trained models: Random Forest, Decision Tree, Logistic Regression, SVM, KNN.
"""

import argparse
import sys
import os
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import joblib
import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split as stratified_subsample
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, balanced_accuracy_score,
)
import xgboost as xgb

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns
except Exception:
    pass

from preprocess_ciciot2023 import preprocess_ciciot2023

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# GPU detection
try:
    xgb_info = xgb.build_info()
    GPU_AVAILABLE = xgb_info.get("USE_CUDA", False)
except Exception:
    GPU_AVAILABLE = False

DATASET_DIR = Path(
    os.environ.get(
        "CICIOT_DATASET_DIR",
        r"C:\Users\Manus\OneDrive\Desktop\L-thirupathi\dataset\archive (3)\CICIOT23",
    )
)
BASE_DIR = Path(__file__).parent
SAVED_MODELS_DIR = BASE_DIR / "saved_models"
REPORTS_DIR = BASE_DIR / "reports"

FAST_MODE_SAMPLE = {
    "xgboost": 100_000,
    "naive_bayes": 100_000,
}

NEEDS_SCALING = set()


def build_model_registry() -> dict:
    """Initialize only remaining models (XGBoost and Naive Bayes)."""
    return {
        "xgboost": xgb.XGBClassifier(
            n_estimators=150,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            tree_method="hist",
            device="cuda" if GPU_AVAILABLE else "cpu",
        ),
        "naive_bayes": GaussianNB(),
    }


def train_remaining(data: dict, fast_mode: bool = False) -> dict:
    """Train only XGBoost and Naive Bayes."""
    models = build_model_registry()
    results = {}

    for name, model in tqdm(models.items(), desc="Training remaining models", unit="model"):
        log.info(f"\n{'-'*50}")
        accel = "[GPU]" if GPU_AVAILABLE and name == "xgboost" else "[CPU]"
        log.info(f"Training: {name.upper()} {accel}")

        X_tr = data["X_train_scaled"] if name in NEEDS_SCALING else data["X_train"]
        X_val = data["X_val_scaled"] if name in NEEDS_SCALING else data["X_val"]
        X_te = data["X_test_scaled"] if name in NEEDS_SCALING else data["X_test"]
        y_tr = data["y_train"]
        y_val = data["y_val"]
        y_te = data["y_test"]

        if fast_mode and name in FAST_MODE_SAMPLE:
            n = min(FAST_MODE_SAMPLE[name], len(X_tr))
            log.info(f"  [FAST] Stratified subsample {name} to {n:,} rows")
            _, X_tr, _, y_tr = stratified_subsample(
                X_tr, y_tr,
                test_size=n / len(X_tr),
                stratify=y_tr,
                random_state=42,
            )

        t0 = time.perf_counter()
        log.info(f"  Training... (fit in progress)")
        if name == "xgboost":
            sw = compute_sample_weight("balanced", y_tr)
            model.fit(X_tr, y_tr, sample_weight=sw)
        else:
            model.fit(X_tr, y_tr)
        train_time = time.perf_counter() - t0
        log.info(f"  ✓ Train time: {train_time:.2f}s")

        # Predict on all three sets
        t1_val = time.perf_counter()
        y_pred_val = model.predict(X_val)
        pred_time_val = time.perf_counter() - t1_val

        t1_te = time.perf_counter()
        y_pred_te = model.predict(X_te)
        pred_time_te = time.perf_counter() - t1_te

        results[name] = {
            "model": model,
            "y_pred_val": y_pred_val,
            "y_val": y_val,
            "y_pred_test": y_pred_te,
            "y_test": y_te,
            "train_time": train_time,
            "pred_time_val": pred_time_val,
            "pred_time_test": pred_time_te,
        }

        SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
        out_path = SAVED_MODELS_DIR / f"{name}.pkl"
        joblib.dump(model, out_path)
        log.info(f"  Saved -> {out_path}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Train remaining CICIoT2023 models (XGBoost, Naive Bayes)")
    parser.add_argument("--fast", action="store_true", help="Use subsampling for faster training")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("CICIoT2023 - Training Remaining Models (XGBoost + Naive Bayes)")
    log.info("=" * 60)
    if GPU_AVAILABLE:
        log.info("GPU Acceleration: ENABLED (NVIDIA CUDA)")
        log.info("  - XGBoost -> GPU (tree_method='hist', device='cuda')")
        log.info("  - Naive Bayes -> CPU (scikit-learn)")
    else:
        log.info("GPU Acceleration: DISABLED (using CPU)")
    log.info("=" * 60)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    data = preprocess_ciciot2023(
        dataset_dir=DATASET_DIR,
        saved_models_dir=SAVED_MODELS_DIR,
    )

    results = train_remaining(data, fast_mode=args.fast)

    log.info("\n" + "=" * 60)
    log.info("Training complete!")
    log.info("Trained models: " + ", ".join(results.keys()))
    log.info("Models saved to: " + str(SAVED_MODELS_DIR))
    log.info("=" * 60)


if __name__ == "__main__":
    main()
