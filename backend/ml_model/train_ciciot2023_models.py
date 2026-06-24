"""
Train all 7 ML models on CICIoT2023 dataset with train/validation/test split.

Models trained:
  1. Random Forest
  2. XGBoost
  3. Decision Tree
  4. Logistic Regression
  5. SVM (with Calibration)
  6. KNN
  7. Naive Bayes

Reports generated:
  - model_comparison_ciciot2023.csv
  - classification_report_ciciot2023.txt
  - confusion_matrix_ciciot2023.png
  - per_class_metrics_ciciot2023.csv
  - latency_report_ciciot2023.csv
  - research_summary_ciciot2023.txt

Usage (from backend/):
    python ml_model/train_ciciot2023_models.py
    python ml_model/train_ciciot2023_models.py --fast   # subsample SVM/KNN
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
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split as stratified_subsample
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, balanced_accuracy_score,
)
import xgboost as xgb

from sklearn.ensemble import RandomForestClassifier as cuRF
from sklearn.linear_model import LogisticRegression as cuLR
from sklearn.neighbors import KNeighborsClassifier as cuKNN

try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False

try:
    xgb_info = xgb.build_info()
    GPU_AVAILABLE = xgb_info.get("USE_CUDA", False)
except Exception:
    GPU_AVAILABLE = False

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

GPU_MODELS = {"xgboost"}

# ── Paths ──────────────────────────────────────────────────────────────────────
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
    "random_forest": 50_000,
    "decision_tree": 100_000,
    "logistic_regression": 50_000,
    "svm": 15_000,
    "knn": 20_000,
    "xgboost": 100_000,
    "naive_bayes": 100_000,
}
DEFAULT_FAST_SAMPLE = 50_000

NEEDS_SCALING = {"logistic_regression", "svm", "knn"}
SLOW_MODELS = {"random_forest", "decision_tree", "logistic_regression", "svm", "knn", "xgboost", "naive_bayes"}


def build_model_registry(class_weight="balanced") -> dict:
    """Initialize all 7 models with optimized hyperparameters (GPU-accelerated where possible)."""
    gpu_status = "[GPU]" if GPU_AVAILABLE else "[CPU]"

    return {
        "random_forest": cuRF(
            n_estimators=200,
            max_depth=20,
            min_samples_leaf=5,
            random_state=42,
        ),
        "decision_tree": DecisionTreeClassifier(
            max_depth=15,
            min_samples_leaf=5,
            class_weight=class_weight,
            random_state=42,
        ),
        "logistic_regression": cuLR(
            C=0.5,
            max_iter=100,
            class_weight=class_weight,
            random_state=42,
        ),
        "svm": CalibratedClassifierCV(
            SVC(kernel="rbf", C=1.0, class_weight=class_weight, random_state=42),
            ensemble=False,
        ),
        "knn": cuKNN(
            n_neighbors=7,
            weights="distance",
        ),
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


def train_all(data: dict, fast_mode: bool = False) -> dict:
    """Train all models on train set, validate on validation set."""
    models = build_model_registry()
    results = {}

    gpu_prefix = "[GPU] " if GPU_AVAILABLE else "[CPU] "

    for name, model in tqdm(models.items(), desc="Training models", unit="model"):
        log.info(f"\n{'-'*50}")
        accel = "[GPU]" if GPU_AVAILABLE and name in GPU_MODELS else "[CPU]"
        log.info(f"Training: {name.upper()} {accel}")

        X_tr = data["X_train_scaled"] if name in NEEDS_SCALING else data["X_train"]
        X_val = data["X_val_scaled"] if name in NEEDS_SCALING else data["X_val"]
        X_te = data["X_test_scaled"] if name in NEEDS_SCALING else data["X_test"]
        y_tr = data["y_train"]
        y_val = data["y_val"]
        y_te = data["y_test"]

        if fast_mode and name in SLOW_MODELS:
            n = min(FAST_MODE_SAMPLE.get(name, DEFAULT_FAST_SAMPLE), len(X_tr))
            log.info(f"  [FAST] Stratified subsample {name} to {n:,} rows")
            _, X_tr, _, y_tr = stratified_subsample(
                X_tr, y_tr,
                test_size=n / len(X_tr),
                stratify=y_tr,
                random_state=42,
            )

        t0 = time.perf_counter()
        log.info(f"  Training... (fit in progress)")
        if name == "gradient_boosting":
            sw = compute_sample_weight("balanced", y_tr)
            model.fit(X_tr, y_tr, sample_weight=sw)
        elif name == "xgboost":
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


def compute_metrics(y_true, y_pred, class_names):
    """Compute detailed metrics."""
    benign_idx = None
    if class_names:
        try:
            benign_idx = list(class_names).index("BENIGN")
        except ValueError:
            pass

    weighted_p = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    weighted_r = recall_score(y_true, y_pred, average="weighted", zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    macro_p = precision_score(y_true, y_pred, average="macro", zero_division=0)
    macro_r = recall_score(y_true, y_pred, average="macro", zero_division=0)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)

    attack_labels = [lbl for lbl in np.unique(y_true) if lbl != benign_idx]
    if attack_labels:
        attack_recall = recall_score(
            y_true, y_pred, labels=attack_labels, average="macro", zero_division=0
        )
    else:
        attack_recall = 0.0

    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "precision": weighted_p,
        "recall": weighted_r,
        "f1": weighted_f1,
        "macro_precision": macro_p,
        "macro_recall": macro_r,
        "macro_f1": macro_f1,
        "attack_detection_rate": attack_recall,
    }


def evaluate_and_report(results: dict, data: dict, reports_dir: Path) -> None:
    """Generate all reports."""
    reports_dir.mkdir(parents=True, exist_ok=True)

    y_val = data["y_val"]
    y_test = data["y_test"]
    class_names = data["class_names"]

    rows = []
    for name, res in results.items():
        y_pred = res["y_pred_test"]
        m = compute_metrics(y_test, y_pred, class_names=class_names)
        rows.append({
            "model_name": name,
            "accuracy": round(m["accuracy"], 4),
            "balanced_accuracy": round(m["balanced_accuracy"], 4),
            "precision": round(m["precision"], 4),
            "recall": round(m["recall"], 4),
            "f1_score": round(m["f1"], 4),
            "macro_precision": round(m["macro_precision"], 4),
            "macro_recall": round(m["macro_recall"], 4),
            "macro_f1": round(m["macro_f1"], 4),
            "attack_detection_rate": round(m["attack_detection_rate"], 4),
            "train_time_s": round(res["train_time"], 3),
            "pred_time_s": round(res["pred_time_test"], 6),
        })

    comparison_df = pd.DataFrame(rows).sort_values("macro_f1", ascending=False)
    comparison_path = reports_dir / "model_comparison_ciciot2023.csv"
    comparison_df.to_csv(comparison_path, index=False)
    log.info(f"Saved model comparison -> {comparison_path}")

    # Classification report
    primary = "random_forest"
    if primary in results:
        present_labels = sorted(set(y_test) | set(results[primary]["y_pred_test"]))
        present_names = [class_names[i] for i in present_labels if i < len(class_names)]
        report_text = classification_report(
            y_test,
            results[primary]["y_pred_test"],
            labels=present_labels,
            target_names=present_names,
            zero_division=0,
        )
        report_path = reports_dir / "classification_report_ciciot2023.txt"
        report_path.write_text(
            f"Classification Report — Random Forest (Primary Model)\n"
            f"Dataset: CICIoT2023\n"
            f"{'='*60}\n{report_text}",
            encoding="utf-8",
        )
        log.info(f"Saved classification report -> {report_path}")

    # Confusion matrix
    if primary in results:
        present_labels = sorted(set(y_test) | set(results[primary]["y_pred_test"]))
        present_names = [class_names[i] for i in present_labels if i < len(class_names)]
        _save_confusion_matrix(
            y_test,
            results[primary]["y_pred_test"],
            present_names,
            reports_dir / "confusion_matrix_ciciot2023.png",
            title="Random Forest — Confusion Matrix (CICIoT2023)",
            labels=present_labels,
        )

    # Per-class metrics
    per_class_rows = []
    for name, res in results.items():
        y_pred = res["y_pred_test"]
        for label_idx, class_name in enumerate(class_names):
            mask = y_test == label_idx
            if mask.sum() == 0:
                continue
            class_p = precision_score(
                y_test[mask], y_pred[mask], average="micro", zero_division=0
            ) if mask.sum() > 0 else 0
            class_r = recall_score(
                y_test[mask], y_pred[mask], average="micro", zero_division=0
            ) if mask.sum() > 0 else 0
            class_f1 = f1_score(
                y_test[mask], y_pred[mask], average="micro", zero_division=0
            ) if mask.sum() > 0 else 0

            per_class_rows.append({
                "model": name,
                "class": class_name,
                "precision": round(class_p, 4),
                "recall": round(class_r, 4),
                "f1": round(class_f1, 4),
            })

    per_class_df = pd.DataFrame(per_class_rows)
    per_class_path = reports_dir / "per_class_metrics_ciciot2023.csv"
    per_class_df.to_csv(per_class_path, index=False)
    log.info(f"Saved per-class metrics -> {per_class_path}")

    # Latency report
    latency_rows = []
    for name, res in results.items():
        latency_rows.append({
            "model": name,
            "train_time_s": round(res["train_time"], 3),
            "pred_time_ms": round(res["pred_time_test"] * 1000, 3),
        })

    latency_df = pd.DataFrame(latency_rows).sort_values("train_time_s")
    latency_path = reports_dir / "latency_report_ciciot2023.csv"
    latency_df.to_csv(latency_path, index=False)
    log.info(f"Saved latency report -> {latency_path}")

    # Summary text
    summary_path = reports_dir / "research_summary_ciciot2023.txt"
    best = comparison_df.iloc[0] if len(comparison_df) > 0 else {}
    summary_text = f"""
CICIoT2023 Model Training Summary
==================================
Dataset: CICIoT2023 (Train/Validation/Test Split)
Total Classes: {len(class_names)}
Classes: {', '.join(class_names)}

Best Model: {best.get('model_name', 'N/A')}
  - Accuracy: {best.get('accuracy', 0):.4f}
  - Macro-F1: {best.get('macro_f1', 0):.4f}
  - Attack Detection Rate: {best.get('attack_detection_rate', 0):.4f}
  - Training Time: {best.get('train_time_s', 0):.3f}s

All Models Trained:
{comparison_df.to_string()}
"""
    summary_path.write_text(summary_text, encoding="utf-8")
    log.info(f"Saved summary -> {summary_path}")

    _print_summary(comparison_df)


def _save_confusion_matrix(y_true, y_pred, class_names, out_path: Path, title: str = "", labels=None):
    try:
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        fig, ax = plt.subplots(figsize=(max(8, len(class_names)), max(6, len(class_names) - 1)))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=class_names,
                    yticklabels=class_names, ax=ax)
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.set_xlabel("Predicted", fontsize=11)
        ax.set_ylabel("Actual", fontsize=11)
        plt.xticks(rotation=45, ha="right")
        plt.yticks(rotation=0)
        plt.tight_layout()
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        log.info(f"Saved confusion matrix -> {out_path}")
    except Exception as e:
        log.warning(f"Could not save confusion matrix: {e}")


def _print_summary(df: pd.DataFrame):
    sep = "-" * 110
    print("\n" + "=" * 110)
    print("  CICIoT2023 MODEL COMPARISON (sorted by Macro-F1)")
    print("=" * 110)
    header = (
        f"{'Model':<25} {'Accuracy':>10} {'W-F1':>8} "
        f"{'Macro-F1':>10} {'MacroRec':>10} {'AtkDetect':>10} {'Train(s)':>10}"
    )
    print(header)
    print(sep)
    for _, row in df.iterrows():
        print(
            f"{row['model_name']:<25} "
            f"{row['accuracy']:>10.4f} "
            f"{row['f1_score']:>8.4f} "
            f"{row['macro_f1']:>10.4f} "
            f"{row['macro_recall']:>10.4f} "
            f"{row['attack_detection_rate']:>10.4f} "
            f"{row['train_time_s']:>10.3f}"
        )
    print("=" * 110)


def main():
    parser = argparse.ArgumentParser(description="Train CICIoT2023 threat detection models")
    parser.add_argument("--fast", action="store_true",
                        help="Subsample SVM/KNN to 15k rows for faster training")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("CICIoT2023 - Multi-Level Threat Detection Training")
    log.info("Split strategy: Separate train/validation/test folders")
    if GPU_AVAILABLE:
        log.info("GPU Acceleration: ENABLED (NVIDIA CUDA)")
        log.info("  - XGBoost -> GPU (tree_method='hist', device='cuda')")
        log.info("  - Other models -> CPU (scikit-learn)")
        if CUPY_AVAILABLE:
            log.info("  - CuPy: Available for GPU-accelerated array operations")
    else:
        log.info("GPU Acceleration: DISABLED (using CPU for all models)")
    log.info("=" * 60)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    data = preprocess_ciciot2023(
        dataset_dir=DATASET_DIR,
        saved_models_dir=SAVED_MODELS_DIR,
    )

    results = train_all(data, fast_mode=args.fast)
    evaluate_and_report(results, data, REPORTS_DIR)

    log.info("\n" + "=" * 60)
    log.info("Training complete.")
    log.info("Models : " + str(SAVED_MODELS_DIR))
    log.info("Reports: " + str(REPORTS_DIR))
    log.info("=" * 60)


if __name__ == "__main__":
    main()
