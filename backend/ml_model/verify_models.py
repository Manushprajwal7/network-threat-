"""
verify_models.py — Evaluate all saved models against the held-out test set.

Uses the same preprocessing pipeline as training (all-days merge, exact-dedup,
BENIGN undersampling, stratified 80/20 split) so results are directly comparable.

Usage (from backend/):
    python ml_model/verify_models.py
"""

import sys
import time
import logging
from pathlib import Path

import numpy as np
import joblib
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, balanced_accuracy_score,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preprocess import preprocess_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

DATASET_DIR = Path(
    r"C:\Users\Manus\OneDrive\Desktop\L thirupathi\dataset\csv\MachineLearningCSV\MachineLearningCVE"
)
BASE_DIR   = Path(__file__).parent
MODELS_DIR = BASE_DIR / "saved_models"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

ALL_MODELS    = ["random_forest", "decision_tree", "logistic_regression",
                 "svm", "knn", "gradient_boosting", "naive_bayes"]
NEEDS_SCALING = {"logistic_regression", "svm", "knn"}


def evaluate_model(name, X_raw, X_scaled, y_test, le=None):
    pkl = MODELS_DIR / f"{name}.pkl"
    if not pkl.exists():
        log.warning(f"  {name}.pkl not found - skipping")
        return None

    model  = joblib.load(pkl)
    X      = X_scaled if name in NEEDS_SCALING else X_raw

    t0     = time.perf_counter()
    y_pred = model.predict(X)
    pred_t = time.perf_counter() - t0

    # Attack detection rate: macro recall over non-BENIGN classes only
    benign_idx = None
    if le is not None:
        try:
            benign_idx = list(le.classes_).index("BENIGN")
        except ValueError:
            pass
    attack_labels = [lbl for lbl in np.unique(y_test) if lbl != benign_idx]
    attack_recall = (
        recall_score(y_test, y_pred, labels=attack_labels, average="macro", zero_division=0)
        if attack_labels else 0.0
    )

    return {
        "name":                  name,
        "y_pred":                y_pred,
        "accuracy":              accuracy_score(y_test, y_pred),
        "balanced_accuracy":     balanced_accuracy_score(y_test, y_pred),
        "precision":             precision_score(y_test, y_pred, average="weighted", zero_division=0),
        "recall":                recall_score(   y_test, y_pred, average="weighted", zero_division=0),
        "f1":                    f1_score(       y_test, y_pred, average="weighted", zero_division=0),
        "macro_precision":       precision_score(y_test, y_pred, average="macro",    zero_division=0),
        "macro_recall":          recall_score(   y_test, y_pred, average="macro",    zero_division=0),
        "macro_f1":              f1_score(       y_test, y_pred, average="macro",    zero_division=0),
        "attack_detection_rate": attack_recall,
        "pred_time":             pred_t,
    }


def write_classification_report(y_test, y_pred, le):
    present = sorted(set(y_test) | set(y_pred))
    names   = [le.classes_[i] for i in present if i < len(le.classes_)]
    text    = classification_report(y_test, y_pred, labels=present,
                                    target_names=names, zero_division=0)
    path = REPORTS_DIR / "classification_report.txt"
    path.write_text(
        f"Classification Report - Random Forest (Primary Model)\n{'='*60}\n{text}",
        encoding="utf-8",
    )
    log.info(f"Saved -> {path}")
    return text, present, names


def write_confusion_matrix(y_test, y_pred, labels, names):
    cm  = confusion_matrix(y_test, y_pred, labels=labels)
    n   = len(names)
    fig, ax = plt.subplots(figsize=(max(10, n), max(8, n - 1)))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=names, yticklabels=names, ax=ax)
    ax.set_title("Random Forest - Confusion Matrix (Stratified Split)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Predicted", fontsize=11)
    ax.set_ylabel("Actual",    fontsize=11)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    path = REPORTS_DIR / "confusion_matrix.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    log.info(f"Saved -> {path}")


def write_comparison_csv(rows):
    df = pd.DataFrame(rows).sort_values("macro_f1", ascending=False)
    path = REPORTS_DIR / "model_comparison.csv"
    df.to_csv(path, index=False)
    log.info(f"Saved -> {path}")
    return df


def print_summary(rows, le):
    df  = pd.DataFrame(rows).sort_values("macro_f1", ascending=False)
    sep = "-" * 115
    print("\n" + "=" * 115)
    print("  ML MODEL VERIFICATION — CICIDS2017 (Stratified 80/20 Split)")
    print("  Sorted by Macro-F1 — the honest metric when attack classes are the target.")
    print("=" * 115)
    print(f"  Classes ({len(le.classes_)}): {', '.join(le.classes_)}")
    print(sep)
    print(
        f"  {'Model':<25} {'Accuracy':>10} {'Bal-Acc':>9} {'W-F1':>8} "
        f"{'Macro-F1':>10} {'MacroRec':>10} {'AtkDetect':>10} {'PredTime':>10}"
    )
    print(sep)
    for _, r in df.iterrows():
        star = " *" if r["model"] == "random_forest" else "  "
        print(
            f"{star}{r['model']:<23} "
            f"{r['accuracy']:>10.4f} "
            f"{r['balanced_accuracy']:>9.4f} "
            f"{r['f1_score']:>8.4f} "
            f"{r['macro_f1']:>10.4f} "
            f"{r['macro_recall']:>10.4f} "
            f"{r['attack_detection_rate']:>10.4f} "
            f"{r['pred_time_s']:>9.4f}s"
        )
    print("=" * 115)
    best = df.iloc[0]
    rf_rows = df[df.model == "random_forest"]
    if not rf_rows.empty:
        rf = rf_rows.iloc[0]
        print(
            f"\n  Best Macro-F1 : {best['model'].upper()} "
            f"(MacroF1={best['macro_f1']:.4f}, AtkDetect={best['attack_detection_rate']:.4f})"
        )
        print(
            f"  Primary model : RANDOM_FOREST "
            f"(MacroF1={rf['macro_f1']:.4f}, AtkDetect={rf['attack_detection_rate']:.4f})\n"
        )
    print(
        "  AtkDetect = macro recall over non-BENIGN classes only.\n"
        "  This is the key operational metric: what fraction of attacks does the model catch?\n"
    )


def main():
    log.info("=" * 60)
    log.info("Model Verification - Network Threat Detection")
    log.info("Split: all-days merge + stratified 80/20")
    log.info("=" * 60)

    # Rebuild the exact same train/test split used during training
    data = preprocess_pipeline(
        dataset_dir=DATASET_DIR,
        saved_models_dir=MODELS_DIR,
    )

    X_raw    = data["X_test"]
    X_scaled = data["X_test_scaled"]
    y_test   = data["y_test"]
    le       = data["label_encoder"]

    rows      = []
    rf_result = None

    for name in ALL_MODELS:
        log.info(f"\nEvaluating: {name.upper()}")
        res = evaluate_model(name, X_raw, X_scaled, y_test, le=le)
        if res is None:
            continue

        rows.append({
            "model":                 res["name"],
            "accuracy":              round(res["accuracy"],              4),
            "balanced_accuracy":     round(res["balanced_accuracy"],     4),
            "precision":             round(res["precision"],             4),
            "recall":                round(res["recall"],                4),
            "f1_score":              round(res["f1"],                    4),
            "macro_precision":       round(res["macro_precision"],       4),
            "macro_recall":          round(res["macro_recall"],          4),
            "macro_f1":              round(res["macro_f1"],              4),
            "attack_detection_rate": round(res["attack_detection_rate"], 4),
            "train_time_s":          0,
            "pred_time_s":           round(res["pred_time"],             6),
        })
        log.info(
            f"  Acc={res['accuracy']:.4f}  BalAcc={res['balanced_accuracy']:.4f}  "
            f"W-F1={res['f1']:.4f}  MacroF1={res['macro_f1']:.4f}  "
            f"AtkDetect={res['attack_detection_rate']:.4f}  "
            f"PredTime={res['pred_time']:.4f}s"
        )

        if name == "random_forest":
            rf_result = res

    if rf_result:
        log.info("\nGenerating reports (Random Forest)...")
        text, present, names = write_classification_report(y_test, rf_result["y_pred"], le)
        write_confusion_matrix(y_test, rf_result["y_pred"], present, names)
        print(f"\n{'-'*60}")
        print("RANDOM FOREST - Per-Class Classification Report")
        print(f"{'-'*60}")
        print(text)

    write_comparison_csv(rows)
    print_summary(rows, le)


if __name__ == "__main__":
    main()
