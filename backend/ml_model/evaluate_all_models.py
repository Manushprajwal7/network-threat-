"""
Comprehensive evaluation of all trained CICIoT2023 models.
Computes detailed metrics, generates reports, confusion matrices, and performance comparisons.
"""

import sys
import os
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, balanced_accuracy_score,
    roc_auc_score, roc_curve
)

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

DATASET_DIR = Path(
    os.environ.get(
        "CICIOT_DATASET_DIR",
        r"C:\Users\Manus\OneDrive\Desktop\L-thirupathi\dataset\archive (3)\CICIOT23",
    )
)
BASE_DIR = Path(__file__).parent
SAVED_MODELS_DIR = BASE_DIR / "saved_models"
REPORTS_DIR = BASE_DIR / "reports"


def compute_metrics(y_true, y_pred, class_names):
    """Compute detailed metrics for model evaluation."""
    benign_idx = None
    if class_names:
        try:
            benign_idx = list(class_names).index("BENIGN")
        except (ValueError, IndexError):
            try:
                benign_idx = list(class_names).index("BenignTraffic")
            except (ValueError, IndexError):
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


def save_confusion_matrix(y_true, y_pred, class_names, out_path: Path, title: str = "", labels=None):
    """Save confusion matrix visualization."""
    try:
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        fig, ax = plt.subplots(figsize=(max(10, len(class_names)//2), max(8, len(class_names)//2)))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=class_names,
                    yticklabels=class_names, ax=ax, cbar_kws={"label": "Count"})
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("Predicted", fontsize=12)
        ax.set_ylabel("Actual", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.yticks(rotation=0)
        plt.tight_layout()
        fig.savefig(out_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        log.info(f"Saved confusion matrix -> {out_path}")
    except Exception as e:
        log.warning(f"Could not save confusion matrix: {e}")


def main():
    log.info("=" * 70)
    log.info("CICIoT2023 - Comprehensive Model Evaluation")
    log.info("=" * 70)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load preprocessing data and models
    log.info("\nLoading dataset and preprocessing...")
    data = preprocess_ciciot2023(
        dataset_dir=DATASET_DIR,
        saved_models_dir=SAVED_MODELS_DIR,
    )

    y_test = data["y_test"]
    y_val = data["y_val"]
    class_names = data["class_names"]

    # Load all trained models
    log.info("\nLoading trained models...")
    model_files = sorted(SAVED_MODELS_DIR.glob("*.pkl"))
    model_names = []
    models = {}

    for model_file in model_files:
        model_name = model_file.stem
        if model_name not in ["label_encoder", "scaler", "feature_columns", "clip_lower", "clip_upper"]:
            try:
                models[model_name] = joblib.load(model_file)
                model_names.append(model_name)
                log.info(f"  Loaded: {model_name}")
            except Exception as e:
                log.warning(f"  Failed to load {model_name}: {e}")

    log.info(f"\nTotal models loaded: {len(models)}")

    # Evaluate all models
    log.info("\n" + "=" * 70)
    log.info("EVALUATING MODELS")
    log.info("=" * 70)

    results = {}
    comparison_rows = []

    for name in sorted(models.keys()):
        model = models[name]
        log.info(f"\nEvaluating: {name.upper()}")

        # Predictions
        t0 = time.perf_counter()
        y_pred_test = model.predict(data["X_test"])
        pred_time = time.perf_counter() - t0

        y_pred_val = model.predict(data["X_val"])

        # Metrics
        metrics = compute_metrics(y_test, y_pred_test, class_names=class_names)

        results[name] = {
            "y_pred_test": y_pred_test,
            "y_test": y_test,
            "y_pred_val": y_pred_val,
            "y_val": y_val,
            "metrics": metrics,
            "pred_time": pred_time,
        }

        log.info(f"  Accuracy: {metrics['accuracy']:.4f}")
        log.info(f"  Balanced Accuracy: {metrics['balanced_accuracy']:.4f}")
        log.info(f"  Macro F1: {metrics['macro_f1']:.4f}")
        log.info(f"  Attack Detection Rate: {metrics['attack_detection_rate']:.4f}")
        log.info(f"  Prediction Time: {pred_time*1000:.2f}ms")

        comparison_rows.append({
            "Model": name,
            "Accuracy": round(metrics["accuracy"], 4),
            "Balanced Accuracy": round(metrics["balanced_accuracy"], 4),
            "Weighted Precision": round(metrics["precision"], 4),
            "Weighted Recall": round(metrics["recall"], 4),
            "Weighted F1": round(metrics["f1"], 4),
            "Macro Precision": round(metrics["macro_precision"], 4),
            "Macro Recall": round(metrics["macro_recall"], 4),
            "Macro F1": round(metrics["macro_f1"], 4),
            "Attack Detection Rate": round(metrics["attack_detection_rate"], 4),
            "Prediction Time (ms)": round(pred_time * 1000, 3),
        })

    # Generate reports
    log.info("\n" + "=" * 70)
    log.info("GENERATING REPORTS")
    log.info("=" * 70)

    # 1. Model Comparison CSV
    comparison_df = pd.DataFrame(comparison_rows).sort_values("Macro F1", ascending=False)
    comparison_path = REPORTS_DIR / "model_comparison_ciciot2023.csv"
    comparison_df.to_csv(comparison_path, index=False)
    log.info(f"Saved model comparison -> {comparison_path}")

    # 2. Detailed Classification Reports
    for name, result in results.items():
        y_pred = result["y_pred_test"]
        present_labels = sorted(set(y_test) | set(y_pred))
        present_names = [class_names[i] for i in present_labels if i < len(class_names)]

        report_text = classification_report(
            y_test, y_pred,
            labels=present_labels,
            target_names=present_names,
            zero_division=0,
            digits=4,
        )

        report_path = REPORTS_DIR / f"classification_report_{name}_ciciot2023.txt"
        report_path.write_text(
            f"Classification Report - {name.upper()}\n"
            f"Dataset: CICIoT2023\n"
            f"{'='*70}\n{report_text}",
            encoding="utf-8",
        )
        log.info(f"Saved classification report -> {report_path}")

    # 3. Confusion Matrices
    for name, result in results.items():
        y_pred = result["y_pred_test"]
        present_labels = sorted(set(y_test) | set(y_pred))
        present_names = [class_names[i] for i in present_labels if i < len(class_names)]

        cm_path = REPORTS_DIR / f"confusion_matrix_{name}_ciciot2023.png"
        save_confusion_matrix(
            y_test, y_pred, present_names, cm_path,
            title=f"{name.upper()} - Confusion Matrix (CICIoT2023)",
            labels=present_labels,
        )

    # 4. Per-Class Metrics
    per_class_rows = []
    for name, result in results.items():
        y_pred = result["y_pred_test"]
        for label_idx, class_name in enumerate(class_names):
            mask = y_test == label_idx
            if mask.sum() > 0:
                class_p = precision_score(
                    y_test[mask], y_pred[mask], average="micro", zero_division=0
                )
                class_r = recall_score(
                    y_test[mask], y_pred[mask], average="micro", zero_division=0
                )
                class_f1 = f1_score(
                    y_test[mask], y_pred[mask], average="micro", zero_division=0
                )

                per_class_rows.append({
                    "Model": name,
                    "Class": class_name,
                    "Samples": mask.sum(),
                    "Precision": round(class_p, 4),
                    "Recall": round(class_r, 4),
                    "F1-Score": round(class_f1, 4),
                })

    per_class_df = pd.DataFrame(per_class_rows)
    per_class_path = REPORTS_DIR / "per_class_metrics_ciciot2023.csv"
    per_class_df.to_csv(per_class_path, index=False)
    log.info(f"Saved per-class metrics -> {per_class_path}")

    # 5. Summary Report
    summary_path = REPORTS_DIR / "evaluation_summary_ciciot2023.txt"
    best = comparison_df.iloc[0] if len(comparison_df) > 0 else {}

    summary_text = f"""
================================================================================
CICIoT2023 MODEL EVALUATION SUMMARY
================================================================================

Dataset Information:
  - Total Classes: {len(class_names)}
  - Training Samples: {len(data['y_train']):,}
  - Validation Samples: {len(data['y_val']):,}
  - Test Samples: {len(data['y_test']):,}
  - Features: {data['X_test'].shape[1]}

Models Evaluated: {len(models)}
  {', '.join(sorted(models.keys()))}

================================================================================
BEST PERFORMING MODEL: {best.get('Model', 'N/A').upper()}
================================================================================

Accuracy:                 {best.get('Accuracy', 0):.4f}
Balanced Accuracy:        {best.get('Balanced Accuracy', 0):.4f}
Weighted Precision:       {best.get('Weighted Precision', 0):.4f}
Weighted Recall:          {best.get('Weighted Recall', 0):.4f}
Weighted F1-Score:        {best.get('Weighted F1', 0):.4f}
Macro Precision:          {best.get('Macro Precision', 0):.4f}
Macro Recall:             {best.get('Macro Recall', 0):.4f}
Macro F1-Score:           {best.get('Macro F1', 0):.4f}
Attack Detection Rate:    {best.get('Attack Detection Rate', 0):.4f}
Prediction Time:          {best.get('Prediction Time (ms)', 0):.3f}ms

================================================================================
ALL MODELS COMPARISON (Sorted by Macro F1)
================================================================================

{comparison_df.to_string()}

================================================================================
KEY INSIGHTS
================================================================================

1. Best Overall Model: {best.get('Model', 'N/A')}
   - Provides the highest Macro F1 score across all attack classes

2. Fastest Model: {comparison_df.loc[comparison_df['Prediction Time (ms)'].idxmin(), 'Model']}
   - Prediction Time: {comparison_df['Prediction Time (ms)'].min():.3f}ms

3. Most Balanced: {comparison_df.loc[comparison_df['Balanced Accuracy'].idxmax(), 'Model']}
   - Balanced Accuracy: {comparison_df['Balanced Accuracy'].max():.4f}

4. Attack Detection: {best.get('Model', 'N/A')}
   - Attack Detection Rate: {best.get('Attack Detection Rate', 0):.4f}

================================================================================
Generated Reports:
  - model_comparison_ciciot2023.csv
  - classification_report_*.txt (one per model)
  - confusion_matrix_*.png (one per model)
  - per_class_metrics_ciciot2023.csv
  - evaluation_summary_ciciot2023.txt
================================================================================
"""

    summary_path.write_text(summary_text, encoding="utf-8")
    log.info(f"Saved evaluation summary -> {summary_path}")

    # Print summary
    log.info("\n" + "=" * 70)
    log.info("EVALUATION COMPLETE")
    log.info("=" * 70)
    print(summary_text)

    log.info(f"\nAll reports saved to: {REPORTS_DIR}")


if __name__ == "__main__":
    main()
