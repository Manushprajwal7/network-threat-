"""
Unknown Threat Detection — evaluation pipeline for the Topology-Aware
Multi-Level Protection Framework (CICIoT2023).

Produces a publication-ready package for the paper's Section 5.6 using ONLY
real model outputs (nothing is hardcoded or fabricated).

Two complementary evaluation strategies are run:

  A. Known-vs-Unknown Holdout  (primary, methodologically clean)
     - A fixed set of rare attack classes is treated as UNKNOWN.
     - An Isolation Forest is trained on KNOWN traffic only (these unknown
       classes are never seen during IF training).
     - On the test set, the IF flags each flow as normal (Known) or
       anomalous (Unknown). Detection is scored against the true known/unknown
       membership of each flow.

  B. Confidence + Anomaly        (supplementary)
     - XGBoost class confidence (max softmax prob) is combined with the IF.
     - A flow is flagged Unknown if confidence < 0.60 OR the IF marks it
       anomalous.

Artifacts written to backend/ml_model/reports/:
  - unknown_threat_results.csv      (all metrics, one row per strategy)
  - unknown_threat_summary.txt      (human-readable research summary)
  - anomaly_score_distribution.png  (known vs unknown anomaly scores)
  - known_vs_unknown_detection.png  (4-category detection bar chart)
  - unknown_confusion_matrix.png    (binary Known/Unknown confusion matrix)

The trained Isolation Forest is saved to saved_models/isolation_forest.pkl.

Run:
    cd backend
    python ml_model/evaluate_unknown_threats.py
    python ml_model/evaluate_unknown_threats.py --contamination 0.05 --max-train 200000
    python ml_model/evaluate_unknown_threats.py --prep-only   # build cache then exit
"""

import argparse
import csv
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import joblib

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Paths ───────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
SAVED_MODELS_DIR = BASE_DIR / "saved_models"
REPORTS_DIR = BASE_DIR / "reports"
CACHE_DIR = SAVED_MODELS_DIR / "_unknown_cache"
IF_MODEL_PATH = SAVED_MODELS_DIR / "isolation_forest.pkl"

import os
DATASET_DIR = Path(
    os.environ.get(
        "CICIOT_DATASET_DIR",
        r"C:\Users\Manus\OneDrive\Desktop\L-thirupathi\dataset\archive (3)\CICIOT23",
    )
)

# ── Unknown holdout classes (rare attack families treated as zero-day) ────────────
UNKNOWN_CLASSES = [
    "Backdoor_Malware",
    "BrowserHijacking",
    "CommandInjection",
    "SqlInjection",
    "XSS",
    "Uploading_Attack",
    "Recon-PingSweep",
]

CONFIDENCE_THRESHOLD = 0.60  # Strategy B: confidence below this → unknown


# ── Helpers ───────────────────────────────────────────────────────────────────────

def _fail(msg: str) -> None:
    log.error(msg)
    sys.exit(1)


def _normalized_anomaly(iforest, X: np.ndarray) -> np.ndarray:
    """0..1 anomaly score (1 = highly anomalous), matching the live detector's
    convention: clip(0.5 - score_samples, 0, 1)."""
    raw = iforest.score_samples(X)            # higher = more normal
    return np.clip(0.5 - raw, 0.0, 1.0)


# ── Stage 1: data preparation (cached) ─────────────────────────────────────────────

def build_cache(max_train: int) -> None:
    """Preprocess CICIoT2023 once and cache the arrays needed for evaluation."""
    try:
        from preprocess_ciciot2023 import preprocess_ciciot2023
    except ImportError as e:
        _fail(f"Cannot import preprocess_ciciot2023: {e}")

    if not DATASET_DIR.exists():
        _fail(f"CICIoT2023 dataset not found: {DATASET_DIR}\n"
              f"Set CICIOT_DATASET_DIR or place the dataset there.")

    log.info("Preprocessing CICIoT2023 (this loads the full dataset, ~5 min)...")
    data = preprocess_ciciot2023(dataset_dir=DATASET_DIR, saved_models_dir=SAVED_MODELS_DIR)

    le = data["label_encoder"]
    class_names = list(le.classes_)

    present_unknown = [c for c in UNKNOWN_CLASSES if c in class_names]
    missing = [c for c in UNKNOWN_CLASSES if c not in class_names]
    if missing:
        log.warning(f"Unknown classes not present in label encoder (ignored): {missing}")
    if not present_unknown:
        _fail("None of the configured UNKNOWN_CLASSES exist in the dataset labels.")

    unknown_idx = set(int(le.transform([c])[0]) for c in present_unknown)

    # --- Training data for the Isolation Forest: KNOWN classes only ---
    y_train = data["y_train"]
    X_train_scaled = data["X_train_scaled"]
    known_train_mask = ~np.isin(y_train, list(unknown_idx))
    X_known = X_train_scaled[known_train_mask]
    if len(X_known) > max_train:
        idx = np.random.default_rng(42).choice(len(X_known), max_train, replace=False)
        X_known = X_known[idx]
    log.info(f"IF training pool (known-only): {len(X_known):,} samples "
             f"(subsampled to {max_train:,} cap)")

    # --- Test data: scaled (for IF) + unscaled clipped (for XGBoost) + labels ---
    y_test = data["y_test"]
    X_test_scaled = data["X_test_scaled"]
    X_test = data["X_test"]  # clipped, unscaled — XGBoost was trained on this

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    np.save(CACHE_DIR / "X_known_train.npy", X_known.astype(np.float32))
    np.save(CACHE_DIR / "X_test_scaled.npy", X_test_scaled.astype(np.float32))
    np.save(CACHE_DIR / "X_test.npy", X_test.astype(np.float32))
    np.save(CACHE_DIR / "y_test.npy", y_test.astype(np.int32))
    meta = {
        "class_names": class_names,
        "unknown_classes": present_unknown,
        "unknown_idx": sorted(unknown_idx),
    }
    (CACHE_DIR / "meta.json").write_text(json.dumps(meta, indent=2))
    log.info(f"Cached evaluation arrays -> {CACHE_DIR}")


def cache_ready() -> bool:
    need = ["X_known_train.npy", "X_test_scaled.npy", "X_test.npy",
            "y_test.npy", "meta.json"]
    return all((CACHE_DIR / f).exists() for f in need)


# ── Stage 2: Isolation Forest (train if missing) ──────────────────────────────────

def get_isolation_forest(contamination: float):
    if IF_MODEL_PATH.exists():
        log.info(f"Loading Isolation Forest -> {IF_MODEL_PATH}")
        return joblib.load(IF_MODEL_PATH)

    from sklearn.ensemble import IsolationForest
    X_known = np.load(CACHE_DIR / "X_known_train.npy")
    log.info(f"Training Isolation Forest on {len(X_known):,} known samples "
             f"(contamination={contamination})...")
    iforest = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    )
    iforest.fit(X_known)
    SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(iforest, IF_MODEL_PATH)
    log.info(f"Isolation Forest saved -> {IF_MODEL_PATH}")
    return iforest


# ── Metrics ────────────────────────────────────────────────────────────────────────

def binary_metrics(y_true_unknown: np.ndarray, y_pred_unknown: np.ndarray,
                   anomaly_norm: np.ndarray) -> dict:
    """All requested metrics. Positive class = Unknown."""
    tp = int(np.sum((y_true_unknown == 1) & (y_pred_unknown == 1)))
    fn = int(np.sum((y_true_unknown == 1) & (y_pred_unknown == 0)))
    fp = int(np.sum((y_true_unknown == 0) & (y_pred_unknown == 1)))
    tn = int(np.sum((y_true_unknown == 0) & (y_pred_unknown == 0)))

    n_unknown = tp + fn
    n_known = tn + fp
    total = tp + fn + fp + tn

    tpr = tp / n_unknown if n_unknown else 0.0          # recall on unknown
    fpr = fp / n_known if n_known else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tpr
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    tnr = tn / n_known if n_known else 0.0

    accuracy = (tp + tn) / total if total else 0.0
    balanced = (tpr + tnr) / 2.0                          # anomaly detection accuracy
    known_acc = tnr
    unknown_acc = tpr

    avg_known = float(np.mean(anomaly_norm[y_true_unknown == 0])) if n_known else 0.0
    avg_unknown = float(np.mean(anomaly_norm[y_true_unknown == 1])) if n_unknown else 0.0

    return {
        "TP": tp, "FP": fp, "TN": tn, "FN": fn,
        "n_known": n_known, "n_unknown": n_unknown,
        "UTDR": tpr,
        "precision": precision, "recall": recall, "f1": f1,
        "FPR": fpr, "TPR": tpr,
        "accuracy": accuracy,
        "anomaly_detection_accuracy": balanced,
        "known_traffic_accuracy": known_acc,
        "unknown_traffic_accuracy": unknown_acc,
        "avg_anomaly_known": avg_known,
        "avg_anomaly_unknown": avg_unknown,
    }


# ── Plots ──────────────────────────────────────────────────────────────────────────

def plot_anomaly_distribution(anomaly_norm, y_true_unknown, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 9})

    known = anomaly_norm[y_true_unknown == 0]
    unknown = anomaly_norm[y_true_unknown == 1]

    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    bins = np.linspace(0, 1, 41)
    ax.hist(known, bins=bins, density=True, alpha=0.6, color="#0284c7",
            label=f"Known (n={len(known):,})")
    ax.hist(unknown, bins=bins, density=True, alpha=0.6, color="#d97706",
            label=f"Unknown (n={len(unknown):,})")
    ax.axvline(float(np.mean(known)), color="#0284c7", ls="--", lw=1.2)
    ax.axvline(float(np.mean(unknown)), color="#d97706", ls="--", lw=1.2)
    ax.set_xlabel("Isolation Forest anomaly score (0 = normal, 1 = anomalous)")
    ax.set_ylabel("Density")
    ax.set_title("Anomaly Score Distribution: Known vs Unknown Traffic")
    ax.legend(frameon=False, fontsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(pad=0.4)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    log.info(f"  wrote {path}")


def plot_detection_bars(m, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 9})

    labels = ["Known\nCorrectly\nClassified", "Known\nMisclassified\nas Unknown",
              "Unknown\nCorrectly\nDetected", "Unknown\nMissed"]
    values = [m["TN"], m["FP"], m["TP"], m["FN"]]
    colors = ["#0284c7", "#94a3b8", "#059669", "#dc2626"]

    fig, ax = plt.subplots(figsize=(5.6, 3.6))
    bars = ax.bar(labels, values, color=colors)
    ax.set_ylabel("Number of flows")
    ax.set_title("Known vs Unknown Detection Breakdown")
    ax.set_yscale("log")
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,}",
                ha="center", va="bottom", fontsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.margins(y=0.18)
    fig.tight_layout(pad=0.4)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    log.info(f"  wrote {path}")


def plot_confusion_matrix(m, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 9})

    # rows = actual [Known, Unknown], cols = predicted [Known, Unknown]
    cm = np.array([[m["TN"], m["FP"]],
                   [m["FN"], m["TP"]]], dtype=float)
    fig, ax = plt.subplots(figsize=(3.8, 3.4))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["Known", "Unknown"])
    ax.set_yticklabels(["Known", "Unknown"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Unknown Threat Detection\nConfusion Matrix")
    vmax = cm.max()
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{int(cm[i, j]):,}", ha="center", va="center",
                    color="white" if cm[i, j] > vmax * 0.5 else "#1e293b",
                    fontsize=11, fontweight="bold")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout(pad=0.4)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    log.info(f"  wrote {path}")


# ── Reports ────────────────────────────────────────────────────────────────────────

def write_csv(rows, path):
    cols = ["approach", "contamination", "n_known", "n_unknown",
            "TP", "FP", "TN", "FN",
            "UTDR", "precision", "recall", "f1", "FPR", "TPR",
            "accuracy", "anomaly_detection_accuracy",
            "known_traffic_accuracy", "unknown_traffic_accuracy",
            "avg_anomaly_known", "avg_anomaly_unknown"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    log.info(f"  wrote {path}")


def write_summary(mA, mB, contamination, unknown_classes, path):
    def pct(v): return f"{v * 100:.2f}%"
    lines = []
    lines.append("=" * 60)
    lines.append("UNKNOWN THREAT DETECTION SUMMARY")
    lines.append("=" * 60)
    lines.append("Dataset: CICIoT2023")
    lines.append("Evaluation: Known-vs-Unknown Holdout")
    lines.append(f"Isolation Forest contamination rate: {contamination}")
    lines.append("")
    lines.append("Unknown Classes:")
    for c in unknown_classes:
        lines.append(f"  * {c}")
    lines.append("")
    lines.append("-" * 60)
    lines.append("Strategy A — Isolation Forest Holdout (primary)")
    lines.append("-" * 60)
    lines.append(f"  UTDR:                       {pct(mA['UTDR'])}")
    lines.append(f"  Precision:                  {pct(mA['precision'])}")
    lines.append(f"  Recall:                     {pct(mA['recall'])}")
    lines.append(f"  F1-Score:                   {pct(mA['f1'])}")
    lines.append(f"  FPR:                        {pct(mA['FPR'])}")
    lines.append(f"  TPR:                        {pct(mA['TPR'])}")
    lines.append(f"  Accuracy:                   {pct(mA['accuracy'])}")
    lines.append(f"  Anomaly Detection Accuracy: {pct(mA['anomaly_detection_accuracy'])}")
    lines.append(f"  Known Traffic Accuracy:     {pct(mA['known_traffic_accuracy'])}")
    lines.append(f"  Unknown Traffic Accuracy:   {pct(mA['unknown_traffic_accuracy'])}")
    lines.append(f"  Known Samples:              {mA['n_known']:,}")
    lines.append(f"  Unknown Samples:            {mA['n_unknown']:,}")
    lines.append(f"  Average Known Anomaly Score:   {mA['avg_anomaly_known']:.4f}")
    lines.append(f"  Average Unknown Anomaly Score: {mA['avg_anomaly_unknown']:.4f}")
    lines.append("")
    lines.append("-" * 60)
    lines.append("Strategy B — XGBoost Confidence (<0.60) OR IF Anomaly")
    lines.append("-" * 60)
    lines.append(f"  UTDR:                       {pct(mB['UTDR'])}")
    lines.append(f"  Precision:                  {pct(mB['precision'])}")
    lines.append(f"  Recall:                     {pct(mB['recall'])}")
    lines.append(f"  F1-Score:                   {pct(mB['f1'])}")
    lines.append(f"  FPR:                        {pct(mB['FPR'])}")
    lines.append(f"  TPR:                        {pct(mB['TPR'])}")
    lines.append(f"  Accuracy:                   {pct(mB['accuracy'])}")
    lines.append(f"  Anomaly Detection Accuracy: {pct(mB['anomaly_detection_accuracy'])}")
    lines.append("")
    lines.append("Note: Isolation Forest trained on KNOWN traffic only; the 7")
    lines.append("unknown classes were never seen during IF training. XGBoost")
    lines.append("confidence is from the full 34-class model. All values are")
    lines.append("computed from real model outputs on the CICIoT2023 test set.")
    lines.append("=" * 60)
    text = "\n".join(lines)
    path.write_text(text, encoding="utf-8")
    log.info(f"  wrote {path}")
    return text


def print_terminal_summary(mA, unknown_classes):
    def pct(v): return f"{v * 100:.2f}%"
    print("\n" + "=" * 50)
    print("UNKNOWN THREAT DETECTION SUMMARY")
    print("Dataset: CICIoT2023")
    print("Evaluation: Known-vs-Unknown Holdout")
    print("Unknown Classes:")
    for c in unknown_classes:
        print(f"  * {c}")
    print("\nMetrics:")
    print(f"  UTDR:                        {pct(mA['UTDR'])}")
    print(f"  Precision:                   {pct(mA['precision'])}")
    print(f"  Recall:                      {pct(mA['recall'])}")
    print(f"  F1-Score:                    {pct(mA['f1'])}")
    print(f"  FPR:                         {pct(mA['FPR'])}")
    print(f"  TPR:                         {pct(mA['TPR'])}")
    print(f"  Accuracy:                    {pct(mA['accuracy'])}")
    print(f"  Known Samples:               {mA['n_known']:,}")
    print(f"  Unknown Samples:             {mA['n_unknown']:,}")
    print(f"  Average Known Anomaly Score:   {mA['avg_anomaly_known']:.4f}")
    print(f"  Average Unknown Anomaly Score: {mA['avg_anomaly_unknown']:.4f}")
    print("=" * 50 + "\n")


# ── Main ─────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Unknown Threat Detection evaluation (CICIoT2023)")
    parser.add_argument("--contamination", type=float, default=0.05,
                        help="Isolation Forest contamination rate (default 0.05)")
    parser.add_argument("--max-train", type=int, default=200_000,
                        help="Max known samples for IF training (default 200k)")
    parser.add_argument("--prep-only", action="store_true",
                        help="Only build the preprocessing cache, then exit")
    parser.add_argument("--rebuild-cache", action="store_true",
                        help="Force rebuild of the preprocessing cache")
    args = parser.parse_args()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Stage 1: cache
    if args.rebuild_cache or not cache_ready():
        build_cache(args.max_train)
    else:
        log.info("Using existing preprocessing cache.")
    if args.prep_only:
        log.info("Prep-only: cache built, exiting.")
        return

    meta = json.loads((CACHE_DIR / "meta.json").read_text())
    class_names = meta["class_names"]
    unknown_classes = meta["unknown_classes"]
    unknown_idx = set(meta["unknown_idx"])

    X_test_scaled = np.load(CACHE_DIR / "X_test_scaled.npy")
    X_test = np.load(CACHE_DIR / "X_test.npy")
    y_test = np.load(CACHE_DIR / "y_test.npy")

    y_true_unknown = np.isin(y_test, list(unknown_idx)).astype(int)
    log.info(f"Test set: {len(y_test):,} flows | "
             f"known={int(np.sum(y_true_unknown == 0)):,} | "
             f"unknown={int(np.sum(y_true_unknown == 1)):,}")

    # Stage 2: Isolation Forest
    iforest = get_isolation_forest(args.contamination)

    # Stage 3: scores
    log.info("Scoring test set with Isolation Forest...")
    t0 = time.perf_counter()
    if_pred = iforest.predict(X_test_scaled)              # -1 anomaly, 1 normal
    anomaly_norm = _normalized_anomaly(iforest, X_test_scaled)
    log.info(f"  IF scoring done in {time.perf_counter() - t0:.1f}s")
    pred_unknown_A = (if_pred == -1).astype(int)

    # XGBoost confidence (Strategy B)
    xgb_path = SAVED_MODELS_DIR / "xgboost.pkl"
    if not xgb_path.exists():
        _fail(f"XGBoost model not found: {xgb_path}\n"
              f"Run: python ml_model/train_ciciot2023_models.py")
    log.info("Computing XGBoost confidence (predict_proba)...")
    xgb = joblib.load(xgb_path)
    t1 = time.perf_counter()
    proba = xgb.predict_proba(X_test)                    # trained on UNSCALED clipped data
    confidence = proba.max(axis=1)
    log.info(f"  XGBoost proba done in {time.perf_counter() - t1:.1f}s")
    pred_unknown_B = ((confidence < CONFIDENCE_THRESHOLD) | (if_pred == -1)).astype(int)

    # Stage 4: metrics
    mA = binary_metrics(y_true_unknown, pred_unknown_A, anomaly_norm)
    mB = binary_metrics(y_true_unknown, pred_unknown_B, anomaly_norm)
    mA["approach"] = "A_isolation_forest_holdout"
    mB["approach"] = "B_confidence_or_anomaly"
    mA["contamination"] = args.contamination
    mB["contamination"] = args.contamination

    # Stage 5: outputs
    write_csv([mA, mB], REPORTS_DIR / "unknown_threat_results.csv")
    write_summary(mA, mB, args.contamination, unknown_classes,
                  REPORTS_DIR / "unknown_threat_summary.txt")
    plot_anomaly_distribution(anomaly_norm, y_true_unknown,
                              REPORTS_DIR / "anomaly_score_distribution.png")
    plot_detection_bars(mA, REPORTS_DIR / "known_vs_unknown_detection.png")
    plot_confusion_matrix(mA, REPORTS_DIR / "unknown_confusion_matrix.png")

    print_terminal_summary(mA, unknown_classes)
    log.info("Unknown Threat Detection package complete.")
    log.info(f"Reports: {REPORTS_DIR}")


if __name__ == "__main__":
    main()
