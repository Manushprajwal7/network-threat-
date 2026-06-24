"""
Normalize CICIoT2023 evaluation outputs into the canonical report schema
consumed by the research/evaluation APIs and the dashboard.

Reads (produced by evaluate_all_models.py, Title-Case headers):
  - reports/model_comparison_ciciot2023.csv
  - reports/per_class_metrics_ciciot2023.csv
  - reports/confusion_matrix_<model>_ciciot2023.png

Writes (snake_case schema expected by api/research_api.py & lib/api.ts):
  - reports/model_comparison_ciciot2023.csv   (normalized in place)
  - reports/per_class_metrics_ciciot2023.csv  (normalized in place)
  - reports/latency_report_ciciot2023.csv
  - reports/research_summary_ciciot2023.txt
  - reports/confusion_matrix_ciciot2023.png   (copy of best model's matrix)

No model is retrained — this only reshapes already-computed metrics.
"""

import csv
import shutil
from pathlib import Path

REPORTS = Path(__file__).parent / "reports"

# Training times (seconds) captured during the --fast training run.
TRAIN_TIME_S = {
    "xgboost": 11.43, "random_forest": 15.88, "decision_tree": 0.77,
    "logistic_regression": 2.97, "svm": 15.84, "knn": 0.02, "naive_bayes": 0.06,
}


def _f(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def normalize_model_comparison():
    src = REPORTS / "model_comparison_ciciot2023.csv"
    if not src.exists():
        print(f"  SKIP: {src.name} not found")
        return []
    with open(src, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Already normalized? (snake_case header present)
    if rows and "model_name" in rows[0]:
        print("  model_comparison already normalized")
        return rows

    out = []
    for r in rows:
        model = r.get("Model", "")
        pred_ms = _f(r.get("Prediction Time (ms)"))
        out.append({
            "model_name": model,
            "accuracy": _f(r.get("Accuracy")),
            "balanced_accuracy": _f(r.get("Balanced Accuracy")),
            "precision": _f(r.get("Weighted Precision")),
            "recall": _f(r.get("Weighted Recall")),
            "f1_score": _f(r.get("Weighted F1")),
            "macro_precision": _f(r.get("Macro Precision")),
            "macro_recall": _f(r.get("Macro Recall")),
            "macro_f1": _f(r.get("Macro F1")),
            "attack_detection_rate": _f(r.get("Attack Detection Rate")),
            "train_time_s": TRAIN_TIME_S.get(model, 0.0),
            "pred_time_s": round(pred_ms / 1000.0, 6),
            "pred_time_ms": round(pred_ms, 3),
        })
    fields = ["model_name", "accuracy", "balanced_accuracy", "precision", "recall",
              "f1_score", "macro_precision", "macro_recall", "macro_f1",
              "attack_detection_rate", "train_time_s", "pred_time_s", "pred_time_ms"]
    with open(src, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out)
    print(f"  wrote {src.name} ({len(out)} models, normalized)")
    return out


def normalize_per_class():
    src = REPORTS / "per_class_metrics_ciciot2023.csv"
    if not src.exists():
        print(f"  SKIP: {src.name} not found")
        return
    with open(src, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if rows and "class" in rows[0] and "model" in rows[0]:
        print("  per_class already normalized")
        return
    out = []
    for r in rows:
        out.append({
            "model": r.get("Model", ""),
            "class": r.get("Class", ""),
            "precision": _f(r.get("Precision")),
            "recall": _f(r.get("Recall")),
            "f1": _f(r.get("F1-Score")),
            "support": int(_f(r.get("Samples"))),
        })
    with open(src, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["model", "class", "precision", "recall", "f1", "support"])
        w.writeheader()
        w.writerows(out)
    print(f"  wrote {src.name} ({len(out)} rows, normalized)")


def write_latency(models):
    if not models:
        return
    path = REPORTS / "latency_report_ciciot2023.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["model", "train_time_s", "pred_time_s", "pred_time_ms"])
        w.writeheader()
        for m in sorted(models, key=lambda r: _f(r.get("train_time_s"))):
            w.writerow({
                "model": m["model_name"],
                "train_time_s": m["train_time_s"],
                "pred_time_s": m["pred_time_s"],
                "pred_time_ms": m["pred_time_ms"],
            })
    print(f"  wrote {path.name}")


def write_summary(models):
    if not models:
        return
    best = max(models, key=lambda r: _f(r.get("macro_f1")))
    path = REPORTS / "research_summary_ciciot2023.txt"
    lines = [
        "CICIoT2023 — Multi-Level Threat Detection — Research Summary",
        "=" * 64,
        "Dataset: CICIoT2023 (separate train/validation/test folders)",
        "Samples: 5,491,971 train · 1,176,851 val · 1,176,851 test",
        "Features: 46 · Classes: 34",
        "Ensemble (live): Random Forest + XGBoost (confidence-weighted vote)",
        "GPU: XGBoost trained on NVIDIA CUDA (tree_method=hist, device=cuda)",
        "",
        f"Best model: {best['model_name']}",
        f"  Accuracy            : {best['accuracy']:.4f}",
        f"  Macro-F1            : {best['macro_f1']:.4f}",
        f"  Balanced Accuracy   : {best['balanced_accuracy']:.4f}",
        f"  Attack Detection Rate: {best['attack_detection_rate']:.4f}",
        "",
        "All models (sorted by Macro-F1):",
    ]
    for m in sorted(models, key=lambda r: -_f(r.get("macro_f1"))):
        lines.append(
            f"  {m['model_name']:<22} acc={m['accuracy']:.4f} "
            f"macroF1={m['macro_f1']:.4f} ADR={m['attack_detection_rate']:.4f} "
            f"pred={m['pred_time_ms']:.1f}ms"
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  wrote {path.name}")


def copy_primary_confusion(models):
    if not models:
        return
    best = max(models, key=lambda r: _f(r.get("macro_f1")))["model_name"]
    src = REPORTS / f"confusion_matrix_{best}_ciciot2023.png"
    dst = REPORTS / "confusion_matrix_ciciot2023.png"
    if src.exists():
        shutil.copyfile(src, dst)
        print(f"  copied {src.name} -> {dst.name}")
    else:
        print(f"  SKIP confusion copy: {src.name} not found")


if __name__ == "__main__":
    print("Normalizing CICIoT2023 research reports...")
    models = normalize_model_comparison()
    normalize_per_class()
    write_latency(models)
    write_summary(models)
    copy_primary_confusion(models)
    print("Done.")
