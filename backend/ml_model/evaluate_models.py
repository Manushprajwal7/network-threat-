"""
Evaluation utilities — metrics, reports, confusion matrix, terminal summary.
Called by train_models.py after training, but also importable standalone.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for server environments
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    balanced_accuracy_score,
)

log = logging.getLogger(__name__)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, class_names: list | None = None) -> dict:
    """
    Compute both weighted (overall accuracy proxy) and macro (per-class
    fairness) metrics.  For network threat detection, macro recall / macro F1
    matter most: a model that predicts BENIGN for everything scores 1.0 on
    weighted metrics but 0.0 on macro recall for attack classes.

    Also computes attack_detection_rate = macro recall over NON-BENIGN classes
    only, which is the primary operational metric for a security system.
    """
    benign_idx = None
    if class_names:
        try:
            benign_idx = list(class_names).index("BENIGN")
        except ValueError:
            pass

    weighted_p  = precision_score(y_true, y_pred, average="weighted",  zero_division=0)
    weighted_r  = recall_score(   y_true, y_pred, average="weighted",  zero_division=0)
    weighted_f1 = f1_score(       y_true, y_pred, average="weighted",  zero_division=0)
    macro_p     = precision_score(y_true, y_pred, average="macro",     zero_division=0)
    macro_r     = recall_score(   y_true, y_pred, average="macro",     zero_division=0)
    macro_f1    = f1_score(       y_true, y_pred, average="macro",     zero_division=0)

    # Attack detection rate: macro recall excluding BENIGN
    attack_labels = [lbl for lbl in np.unique(y_true) if lbl != benign_idx]
    if attack_labels:
        attack_recall = recall_score(
            y_true, y_pred, labels=attack_labels, average="macro", zero_division=0
        )
    else:
        attack_recall = 0.0

    return {
        "accuracy":              accuracy_score(y_true, y_pred),
        "balanced_accuracy":     balanced_accuracy_score(y_true, y_pred),
        "precision":             weighted_p,
        "recall":                weighted_r,
        "f1":                    weighted_f1,
        "macro_precision":       macro_p,
        "macro_recall":          macro_r,
        "macro_f1":              macro_f1,
        "attack_detection_rate": attack_recall,
    }


def evaluate_and_report(results: dict, data: dict, reports_dir: Path) -> pd.DataFrame:
    """
    Compute metrics for every trained model, write comparison CSV,
    classification report text, confusion matrix image (Random Forest),
    and print a terminal summary table.
    """
    reports_dir.mkdir(parents=True, exist_ok=True)

    y_test = data["y_test"]
    class_names = data["class_names"]
    rows = []

    for name, res in results.items():
        y_pred = res["y_pred"]
        m = compute_metrics(y_test, y_pred, class_names=class_names)
        rows.append({
            "model_name":            name,
            "accuracy":              round(m["accuracy"],              4),
            "balanced_accuracy":     round(m["balanced_accuracy"],     4),
            "precision":             round(m["precision"],             4),
            "recall":                round(m["recall"],                4),
            "f1_score":              round(m["f1"],                    4),
            "macro_precision":       round(m["macro_precision"],       4),
            "macro_recall":          round(m["macro_recall"],          4),
            "macro_f1":              round(m["macro_f1"],              4),
            "attack_detection_rate": round(m["attack_detection_rate"], 4),
            "train_time_s":          round(res["train_time"], 3),
            "pred_time_s":           round(res["pred_time"],  6),
        })

    comparison_df = pd.DataFrame(rows).sort_values("macro_f1", ascending=False)
    comparison_path = reports_dir / "model_comparison.csv"
    comparison_df.to_csv(comparison_path, index=False)
    log.info(f"Saved model comparison -> {comparison_path}")

    # ── Classification report (Random Forest as primary) ──
    primary = "random_forest"
    if primary in results:
        # Only include labels that actually appear in the test set
        present_labels = sorted(set(y_test) | set(results[primary]["y_pred"]))
        present_names = [class_names[i] for i in present_labels if i < len(class_names)]
        report_text = classification_report(
            y_test,
            results[primary]["y_pred"],
            labels=present_labels,
            target_names=present_names,
            zero_division=0,
        )
        report_path = reports_dir / "classification_report.txt"
        report_path.write_text(
            f"Classification Report — Random Forest (Primary Model)\n"
            f"{'='*60}\n{report_text}",
            encoding="utf-8",
        )
        log.info(f"Saved classification report -> {report_path}")

    # ── Confusion matrix (Random Forest) ──
    if primary in results:
        present_labels = sorted(set(y_test) | set(results[primary]["y_pred"]))
        present_names = [class_names[i] for i in present_labels if i < len(class_names)]
        _save_confusion_matrix(
            y_test,
            results[primary]["y_pred"],
            present_names,
            reports_dir / "confusion_matrix.png",
            title="Random Forest — Confusion Matrix",
            labels=present_labels,
        )

    # ── Terminal summary ──
    _print_summary(comparison_df)

    return comparison_df


def _save_confusion_matrix(y_true, y_pred, class_names, out_path: Path, title: str = "", labels=None):
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    fig, ax = plt.subplots(figsize=(max(8, len(class_names)), max(6, len(class_names) - 1)))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        ax=ax,
    )
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel("Predicted", fontsize=11)
    ax.set_ylabel("Actual", fontsize=11)
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    log.info(f"Saved confusion matrix -> {out_path}")


def _print_summary(df: pd.DataFrame):
    sep = "-" * 110
    print("\n" + "=" * 110)
    print("  MODEL COMPARISON SUMMARY  (sorted by Macro-F1 — the honest multi-class metric)")
    print("=" * 110)
    # model column may be 'model_name' (train pipeline) or 'model' (verify pipeline)
    model_col = "model_name" if "model_name" in df.columns else "model"
    has_macro   = "macro_f1" in df.columns
    has_adr     = "attack_detection_rate" in df.columns

    if has_macro and has_adr:
        header = (
            f"{'Model':<25} {'Accuracy':>10} {'W-F1':>8} "
            f"{'Macro-F1':>10} {'MacroRec':>10} {'AtkDetect':>10} {'Train(s)':>10}"
        )
    else:
        header = (
            f"{'Model':<25} {'Accuracy':>10} {'Precision':>10} "
            f"{'Recall':>10} {'F1-Score':>10} {'Train(s)':>10}"
        )
    print(header)
    print(sep)
    for _, row in df.iterrows():
        if has_macro and has_adr:
            print(
                f"{row[model_col]:<25} "
                f"{row['accuracy']:>10.4f} "
                f"{row['f1_score']:>8.4f} "
                f"{row['macro_f1']:>10.4f} "
                f"{row['macro_recall']:>10.4f} "
                f"{row['attack_detection_rate']:>10.4f} "
                f"{row['train_time_s']:>10.3f}"
            )
        else:
            print(
                f"{row[model_col]:<25} "
                f"{row['accuracy']:>10.4f} "
                f"{row['precision']:>10.4f} "
                f"{row['recall']:>10.4f} "
                f"{row['f1_score']:>10.4f} "
                f"{row['train_time_s']:>10.3f}"
            )
    print("=" * 110)
    print(
        "\n  W-F1=Weighted F1 (high when BENIGN dominates).  "
        "Macro-F1 / AtkDetect = true per-class performance.\n"
    )


if __name__ == "__main__":
    # Standalone usage: print the saved comparison CSV
    import sys
    reports_dir = Path(__file__).parent / "reports"
    csv_path = reports_dir / "model_comparison.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        _print_summary(df)
    else:
        print(f"No comparison CSV found at {csv_path}. Run train_models.py first.")
        sys.exit(1)
