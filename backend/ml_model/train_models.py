"""
Train all ML models on CICIDS2017 and save as .pkl files.

Key design decisions for publication-grade (85-92%) accuracy:
  - All-days merge + exact-duplicate removal + BENIGN undersampling (3x attacks)
  - Stratified 80/20 split (same distribution in train and test)
  - Regularised models: depth caps + min_samples_leaf prevent memorisation
  - Outlier clipping in preprocess.py

Usage (from backend/):
    python ml_model/train_models.py
    python ml_model/train_models.py --fast   # subsample SVM/KNN/GB to save time
"""

import argparse
import sys
import os
import time
import logging
from pathlib import Path

# Allow bare imports (preprocess, evaluate_models) when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent))

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split as _stratified_subsample
from sklearn.utils.class_weight import compute_sample_weight

from preprocess import preprocess_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
DATASET_DIR = Path(
    os.environ.get(
        "CICIDS_DATASET_DIR",
        r"C:\Users\Manus\OneDrive\Desktop\L thirupathi\dataset\csv\MachineLearningCSV\MachineLearningCVE",
    )
)
BASE_DIR         = Path(__file__).parent
SAVED_MODELS_DIR = BASE_DIR / "saved_models"
REPORTS_DIR      = BASE_DIR / "reports"

FAST_MODE_SAMPLE = {
    "svm":                15_000,   # RBF kernel scales O(n^2)
    "knn":                20_000,   # lazy learner; more rows = slower predict
    "gradient_boosting":  25_000,   # 25k gives better generalization than 15k
}
DEFAULT_FAST_SAMPLE = 15_000

NEEDS_SCALING = {"logistic_regression", "svm", "knn"}
SLOW_MODELS   = {"svm", "knn", "gradient_boosting"}


def build_model_registry(class_weight="balanced") -> dict:
    """
    Regularised model settings to produce honest generalisation performance.

    Random Forest  — max_depth=20 prevents fully-grown trees that memorise
                     individual flows; min_samples_leaf=5 smooths leaf estimates.
    Decision Tree  — max_depth=15 keeps the tree interpretable and avoids
                     overfitting to session-level patterns.
    Gradient Boost — shallow trees (max_depth=5) with 150 estimators strike the
                     bias-variance balance on imbalanced multiclass data.
    Logistic Reg   — C=0.5 adds L2 regularisation (default C=1.0 is too relaxed
                     for 77 collinear flow features).
    SVM            — RBF kernel with C=1.0; subsampled in fast mode.
    KNN            — k=7 reduces noise sensitivity vs k=5.
    Naive Bayes    — Gaussian NB is kept as a fast baseline; known to struggle
                     with correlated features.
    """
    return {
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_leaf=5,
            max_features="sqrt",
            class_weight=class_weight,
            n_jobs=-1,
            random_state=42,
        ),
        "decision_tree": DecisionTreeClassifier(
            max_depth=15,
            min_samples_leaf=5,
            class_weight=class_weight,
            random_state=42,
        ),
        "logistic_regression": LogisticRegression(
            C=0.5,
            max_iter=1000,
            class_weight=class_weight,
            random_state=42,
        ),
        "svm": CalibratedClassifierCV(
            SVC(kernel="rbf", C=1.0, class_weight=class_weight, random_state=42),
            ensemble=False,
        ),
        "knn": KNeighborsClassifier(
            n_neighbors=7,
            weights="distance",
            n_jobs=-1,
        ),
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=150,
            max_depth=5,
            min_samples_leaf=5,
            learning_rate=0.1,
            subsample=0.8,
            random_state=42,
        ),
        "naive_bayes": GaussianNB(),
    }


def train_all(data: dict, fast_mode: bool = False) -> dict:
    models  = build_model_registry()
    results = {}

    for name, model in models.items():
        log.info(f"\n{'-'*50}")
        log.info(f"Training: {name.upper()}")

        X_tr = data["X_train_scaled"] if name in NEEDS_SCALING else data["X_train"]
        X_te = data["X_test_scaled"]  if name in NEEDS_SCALING else data["X_test"]
        y_tr = data["y_train"]
        y_te = data["y_test"]

        if fast_mode and name in SLOW_MODELS:
            n = min(FAST_MODE_SAMPLE.get(name, DEFAULT_FAST_SAMPLE), len(X_tr))
            log.info(f"  [FAST] Stratified subsample {name} to {n:,} rows")
            # Use stratified sampling so every attack class keeps proportional
            # representation.  Un-stratified random sampling can drop small
            # attack classes entirely when the subsample is small.
            _, X_tr, _, y_tr = _stratified_subsample(
                X_tr, y_tr,
                test_size=n / len(X_tr),
                stratify=y_tr,
                random_state=42,
            )

        t0 = time.perf_counter()
        # GradientBoostingClassifier has no class_weight parameter; use
        # sample_weight to give the balanced class weighting during fit.
        if name == "gradient_boosting":
            sw = compute_sample_weight("balanced", y_tr)
            model.fit(X_tr, y_tr, sample_weight=sw)
        else:
            model.fit(X_tr, y_tr)
        train_time = time.perf_counter() - t0
        log.info(f"  Train time: {train_time:.2f}s")

        t1     = time.perf_counter()
        y_pred = model.predict(X_te)
        pred_time = time.perf_counter() - t1

        results[name] = {
            "model":      model,
            "y_pred":     y_pred,
            "y_test":     y_te,
            "train_time": train_time,
            "pred_time":  pred_time,
        }

        SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
        out_path = SAVED_MODELS_DIR / f"{name}.pkl"
        joblib.dump(model, out_path)
        log.info(f"  Saved -> {out_path}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Train CICIDS2017 threat detection models")
    parser.add_argument("--fast", action="store_true",
                        help="Subsample SVM/KNN/GradientBoosting to 15k rows")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("CICIDS2017 - Multi-Level Threat Detection Training")
    log.info("Split strategy: all-days merge + stratified 80/20 split")
    log.info("=" * 60)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    data = preprocess_pipeline(
        dataset_dir=DATASET_DIR,
        saved_models_dir=SAVED_MODELS_DIR,
    )

    results = train_all(data, fast_mode=args.fast)

    from evaluate_models import evaluate_and_report
    evaluate_and_report(results, data, REPORTS_DIR)

    log.info("\n" + "=" * 60)
    log.info("Training complete.")
    log.info("Models : " + str(SAVED_MODELS_DIR))
    log.info("Reports: " + str(REPORTS_DIR))
    log.info("=" * 60)


if __name__ == "__main__":
    main()
