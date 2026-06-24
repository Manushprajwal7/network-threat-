"""
Research-grade evaluation module.

Generates:
  - Per-model classification reports (text)
  - Per-model confusion matrices (PNG)
  - Model comparison CSV with full metrics
  - Per-class metrics CSV
  - Latency report CSV
  - Accuracy trustworthiness warnings
  - research_summary.txt

All outputs go to backend/ml_model/reports/
"""

import logging
import time
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings(
    "ignore",
    message=r".*sklearn\.utils\.parallel\.delayed.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r".*make it possible to propagate the scikit-learn configuration.*",
    category=UserWarning,
)
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)

log = logging.getLogger(__name__)

ACCURACY_WARNING_THRESHOLD = 0.95


# ── Core metrics ───────────────────────────────────────────────────────────────

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray,
                    class_names: list | None = None,
                    predict_proba: np.ndarray | None = None) -> dict:
    """
    Compute full research metrics for one model.
    Includes weighted, macro, per-class, ROC-AUC, FPR, FNR, ADR.
    """
    benign_idx = None
    if class_names:
        try:
            benign_idx = list(class_names).index("BENIGN")
        except ValueError:
            pass

    acc         = accuracy_score(y_true, y_pred)
    bal_acc     = balanced_accuracy_score(y_true, y_pred)
    w_prec      = precision_score(y_true, y_pred, average="weighted",  zero_division=0)
    w_rec       = recall_score(   y_true, y_pred, average="weighted",  zero_division=0)
    w_f1        = f1_score(       y_true, y_pred, average="weighted",  zero_division=0)
    mac_prec    = precision_score(y_true, y_pred, average="macro",     zero_division=0)
    mac_rec     = recall_score(   y_true, y_pred, average="macro",     zero_division=0)
    mac_f1      = f1_score(       y_true, y_pred, average="macro",     zero_division=0)

    attack_lbls = [l for l in np.unique(y_true) if l != benign_idx]
    adr = recall_score(y_true, y_pred, labels=attack_lbls, average="macro", zero_division=0) \
        if attack_lbls else 0.0

    # False Positive / Negative rates (binary: BENIGN vs attack)
    fpr = fnr = 0.0
    if benign_idx is not None:
        y_bin_true = (y_true != benign_idx).astype(int)
        y_bin_pred = (y_pred != benign_idx).astype(int)
        tn = int(np.sum((y_bin_true == 0) & (y_bin_pred == 0)))
        fp = int(np.sum((y_bin_true == 0) & (y_bin_pred == 1)))
        fn = int(np.sum((y_bin_true == 1) & (y_bin_pred == 0)))
        tp = int(np.sum((y_bin_true == 1) & (y_bin_pred == 1)))
        fpr = fp / (fp + tn + 1e-9)
        fnr = fn / (fn + tp + 1e-9)

    # ROC-AUC (macro OvR, only if probas available)
    roc_auc = None
    if predict_proba is not None:
        try:
            unique_classes = np.unique(y_true)
            if len(unique_classes) > 1:
                roc_auc = roc_auc_score(
                    y_true, predict_proba,
                    multi_class="ovr", average="macro",
                    labels=list(range(len(class_names))) if class_names else None,
                )
        except Exception:
            pass

    return {
        "accuracy":              round(acc,      4),
        "balanced_accuracy":     round(bal_acc,  4),
        "precision":             round(w_prec,   4),
        "recall":                round(w_rec,    4),
        "f1_score":              round(w_f1,     4),
        "macro_precision":       round(mac_prec, 4),
        "macro_recall":          round(mac_rec,  4),
        "macro_f1":              round(mac_f1,   4),
        "attack_detection_rate": round(adr,      4),
        "false_positive_rate":   round(fpr,      4),
        "false_negative_rate":   round(fnr,      4),
        "roc_auc":               round(roc_auc, 4) if roc_auc is not None else None,
    }


def _check_accuracy_warning(name: str, accuracy: float, split_mode: str) -> str | None:
    if accuracy > ACCURACY_WARNING_THRESHOLD:
        msg = (
            f"WARNING: {name} accuracy = {accuracy:.4f} > {ACCURACY_WARNING_THRESHOLD}. "
            f"This may indicate data leakage, duplicate samples, or unrealistic evaluation. "
            f"Split mode used: '{split_mode}'. "
            f"Check leakage_report.txt and prefer file-based or temporal split."
        )
        log.warning(msg)
        return msg
    return None


# ── Confusion matrix ───────────────────────────────────────────────────────────

def save_confusion_matrix(
    y_true: np.ndarray, y_pred: np.ndarray,
    class_names: list, out_path: Path, title: str = ""
) -> None:
    labels       = sorted(np.unique(np.concatenate([y_true, y_pred])))
    present_names = [class_names[i] for i in labels if i < len(class_names)]
    cm            = confusion_matrix(y_true, y_pred, labels=labels)
    sz            = max(8, len(present_names))
    fig, ax       = plt.subplots(figsize=(sz, sz - 1))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=present_names, yticklabels=present_names, ax=ax,
    )
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel("Predicted", fontsize=11)
    ax.set_ylabel("Actual", fontsize=11)
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    log.info(f"Saved confusion matrix → {out_path}")


# ── Per-class metrics ──────────────────────────────────────────────────────────

def compute_per_class(y_true: np.ndarray, y_pred: np.ndarray,
                       class_names: list) -> pd.DataFrame:
    labels = sorted(np.unique(np.concatenate([y_true, y_pred])))
    names  = [class_names[i] for i in labels if i < len(class_names)]
    prec   = precision_score(y_true, y_pred, labels=labels, average=None, zero_division=0)
    rec    = recall_score(   y_true, y_pred, labels=labels, average=None, zero_division=0)
    f1     = f1_score(       y_true, y_pred, labels=labels, average=None, zero_division=0)
    sup    = np.array([int(np.sum(y_true == l)) for l in labels])

    return pd.DataFrame({
        "class":     names,
        "precision": np.round(prec, 4),
        "recall":    np.round(rec,  4),
        "f1":        np.round(f1,   4),
        "support":   sup,
    })


# ── Main evaluation entry point ────────────────────────────────────────────────

def evaluate_and_report(
    results:     dict,           # {model_name: {model, y_pred, y_test, train_time, pred_time}}
    data:        dict,           # from research_pipeline / preprocess_pipeline
    reports_dir: Path,
    split_mode:  str = "file",
) -> pd.DataFrame:
    """
    Generate all research-grade reports for all trained models.

    Writes:
      model_comparison_research.csv
      classification_report_<model>.txt   (per model)
      confusion_matrix_<model>.png        (per model)
      per_class_metrics.csv
      latency_report.csv
      research_summary.txt
    """
    reports_dir.mkdir(parents=True, exist_ok=True)
    y_test      = data["y_test"]
    class_names = data["class_names"]
    rows        = []
    pc_rows     = []
    lat_rows    = []
    warnings    = []
    per_class_primary = None

    for name, res in results.items():
        y_pred     = res["y_pred"]
        proba      = res.get("y_proba")
        train_time = res.get("train_time", 0.0)
        pred_time  = res.get("pred_time",  0.0)

        m = compute_metrics(y_test, y_pred, class_names, proba)
        w = _check_accuracy_warning(name, m["accuracy"], split_mode)
        if w:
            warnings.append(w)

        row = {
            "model_name":            name,
            "split_mode":            split_mode,
            "accuracy":              m["accuracy"],
            "balanced_accuracy":     m["balanced_accuracy"],
            "precision":             m["precision"],
            "recall":                m["recall"],
            "f1_score":              m["f1_score"],
            "macro_precision":       m["macro_precision"],
            "macro_recall":          m["macro_recall"],
            "macro_f1":              m["macro_f1"],
            "attack_detection_rate": m["attack_detection_rate"],
            "false_positive_rate":   m["false_positive_rate"],
            "false_negative_rate":   m["false_negative_rate"],
            "roc_auc":               m["roc_auc"],
            "train_time_s":          round(train_time, 3),
            "pred_time_s":           round(pred_time,  6),
        }
        rows.append(row)

        # Classification report
        labels        = sorted(set(y_test) | set(y_pred))
        present_names = [class_names[i] for i in labels if i < len(class_names)]
        clf_report    = classification_report(
            y_test, y_pred, labels=labels,
            target_names=present_names, zero_division=0
        )
        rpt_path = reports_dir / f"classification_report_{name}.txt"
        rpt_path.write_text(
            f"Classification Report — {name.upper()}\n"
            f"Split mode: {split_mode}\n"
            f"{'='*60}\n{clf_report}",
            encoding="utf-8"
        )
        log.info(f"Saved classification report → {rpt_path}")

        # Confusion matrix
        cm_path = reports_dir / f"confusion_matrix_{name}.png"
        save_confusion_matrix(
            y_test, y_pred, class_names, cm_path,
            title=f"{name.replace('_', ' ').title()} — Confusion Matrix ({split_mode})"
        )

        # Per-class metrics (save for all, track primary separately)
        pc_df = compute_per_class(y_test, y_pred, class_names)
        pc_df.insert(0, "model", name)
        pc_rows.append(pc_df)
        if name in ("random_forest_research", "random_forest"):
            per_class_primary = pc_df

        # Latency
        lat_rows.append({
            "model":        name,
            "train_time_s": round(train_time, 3),
            "pred_time_s":  round(pred_time,  6),
            "pred_time_ms": round(pred_time * 1000, 3),
            "realtime_ok":  pred_time < 0.01,
        })

    # Model comparison CSV
    comp_df = pd.DataFrame(rows).sort_values("macro_f1", ascending=False)
    comp_path = reports_dir / "model_comparison_research.csv"
    comp_df.to_csv(comp_path, index=False)
    log.info(f"Saved model comparison → {comp_path}")

    # Per-class CSV
    if pc_rows:
        pc_all = pd.concat(pc_rows, ignore_index=True)
        pc_path = reports_dir / "per_class_metrics.csv"
        pc_all.to_csv(pc_path, index=False)
        log.info(f"Saved per-class metrics → {pc_path}")

    # Latency CSV
    lat_df   = pd.DataFrame(lat_rows)
    lat_path = reports_dir / "latency_report.csv"
    lat_df.to_csv(lat_path, index=False)
    log.info(f"Saved latency report → {lat_path}")

    # Research summary
    _write_research_summary(comp_df, warnings, split_mode, data, reports_dir)

    # Terminal output
    _print_summary(comp_df)

    return comp_df


def _write_research_summary(
    comp_df: pd.DataFrame,
    warnings: list,
    split_mode: str,
    data: dict,
    reports_dir: Path,
) -> None:
    best      = comp_df.iloc[0] if not comp_df.empty else None
    n_cls     = len(data.get("class_names", []))
    n_feat    = len(data.get("feature_columns", []))

    lines = [
        "=" * 70,
        "RESEARCH SUMMARY — Topology-Aware Multi-Level Protection Framework",
        "=" * 70,
        f"Dataset        : CICIDS2017",
        f"Split strategy : {split_mode}",
        f"Num features   : {n_feat}",
        f"Num classes    : {n_cls}",
        f"Classes        : {data.get('class_names', [])}",
        "",
        "── Model Rankings (by Macro-F1) ─────────────────────────────────",
    ]
    for _, row in comp_df.iterrows():
        lines.append(
            f"  {row['model_name']:<30} "
            f"Acc={row['accuracy']:.4f}  "
            f"MacroF1={row['macro_f1']:.4f}  "
            f"ADR={row['attack_detection_rate']:.4f}  "
            f"FPR={row['false_positive_rate']:.4f}"
        )
    if best is not None:
        lines += [
            "",
            f"Best model     : {best['model_name']}",
            f"Best Macro-F1  : {best['macro_f1']:.4f}",
            f"Best ADR       : {best['attack_detection_rate']:.4f}",
        ]
    if warnings:
        lines += ["", "── Accuracy Warnings ────────────────────────────────────────────"]
        for w in warnings:
            lines.append(f"  {w}")
    else:
        lines += ["", "── No accuracy warnings. Evaluation appears clean. ──────────────"]

    lines += [
        "",
        "── Evaluation Integrity Note ────────────────────────────────────",
        "  Results generated with research-grade pipeline:",
        "  * Class-aware deduplication (BENIGN deduped, attacks preserved)",
        "  * BENIGN undersampling (2x attack ratio)",
        f"  * Split mode: {split_mode}",
        "  * Outlier clipping (1st/99th percentile, fit on train only)",
        "  * StandardScaler (fit on train only)",
        "  * Regularised model hyperparameters to prevent overfitting",
        "=" * 70,
    ]

    text = "\n".join(lines)
    (reports_dir / "research_summary.txt").write_text(text, encoding="utf-8")
    log.info(f"Saved research summary → {reports_dir / 'research_summary.txt'}")
    print("\n" + text)


def _print_summary(df: pd.DataFrame) -> None:
    print("\n" + "=" * 110)
    print("  MODEL COMPARISON — sorted by Macro-F1")
    print("=" * 110)
    mcol = "model_name" if "model_name" in df.columns else "model"
    print(f"{'Model':<30} {'Accuracy':>10} {'W-F1':>8} {'MacroF1':>9} {'ADR':>8} {'FPR':>8} {'FNR':>8} {'Train(s)':>9}")
    print("-" * 110)
    for _, row in df.iterrows():
        print(
            f"{row[mcol]:<30} "
            f"{row['accuracy']:>10.4f} "
            f"{row['f1_score']:>8.4f} "
            f"{row['macro_f1']:>9.4f} "
            f"{row['attack_detection_rate']:>8.4f} "
            f"{row['false_positive_rate']:>8.4f} "
            f"{row['false_negative_rate']:>8.4f} "
            f"{row['train_time_s']:>9.3f}"
        )
    print("=" * 110)
    print("  ADR=Attack Detection Rate  FPR=False Positive Rate  FNR=False Negative Rate\n")
