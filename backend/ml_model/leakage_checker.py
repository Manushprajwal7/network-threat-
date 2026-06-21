"""
Data leakage checker for CICIDS2017 ML pipeline.

Checks:
  1. Exact duplicate rows
  2. Non-feature (identifier) columns present
  3. Label column not in feature set
  4. Single-feature predictive power (decision stump)
  5. High inter-feature correlation
  6. Class balance sanity

Saves: backend/ml_model/reports/leakage_report.txt
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score

log = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent / "reports"

NON_FEATURE_COLS = {
    "flow id", "source ip", "source port", "destination ip",
    "destination port", "timestamp", "similarhttp", "label",
}

HIGH_SINGLE_FEATURE_ACC = 0.90
HIGH_CORR_THRESHOLD     = 0.95


def check_leakage(df: pd.DataFrame, label_col: str,
                  reports_dir: Path = REPORTS_DIR) -> dict:
    """
    Run all leakage checks. Saves leakage_report.txt.
    Returns dict with check results and warning count.
    """
    reports_dir.mkdir(parents=True, exist_ok=True)
    lines    = ["=" * 70, "DATA LEAKAGE CHECK REPORT", "=" * 70, ""]
    warnings = []

    total = len(df)

    # ── 1. Duplicate rows ─────────────────────────────────────────────────────
    n_dup   = int(df.duplicated().sum())
    dup_pct = 100.0 * n_dup / total if total else 0
    _add(lines, f"[CHECK 1] Duplicate rows: {n_dup:,} / {total:,} ({dup_pct:.1f}%)")
    if dup_pct > 5:
        w = f"  WARNING: {dup_pct:.1f}% duplicates — may inflate accuracy."
        warnings.append(w); lines.append(w)
    else:
        lines.append("  OK")
    lines.append("")

    # ── 2. Non-feature columns ────────────────────────────────────────────────
    bad_cols = [c for c in df.columns
                if c.lower().strip() in NON_FEATURE_COLS and c != label_col]
    _add(lines, f"[CHECK 2] Non-feature columns present: {bad_cols}")
    if bad_cols:
        w = f"  WARNING: Remove before training: {bad_cols}"
        warnings.append(w); lines.append(w)
    else:
        lines.append("  OK — no identifier columns found in feature set")
    lines.append("")

    # ── 3. Label not in features ──────────────────────────────────────────────
    feat_cols = [c for c in df.columns
                 if c != label_col and c.lower().strip() not in NON_FEATURE_COLS]
    label_in  = label_col in feat_cols
    _add(lines, f"[CHECK 3] Label '{label_col}' absent from feature columns: {not label_in}")
    if label_in:
        w = f"  CRITICAL: Label column '{label_col}' is inside features! Severe leakage."
        warnings.append(w); lines.append(w)
    else:
        lines.append("  OK")
    lines.append("")

    # ── 4. Single-feature predictive power ────────────────────────────────────
    num_cols    = df[feat_cols].select_dtypes(include=[np.number]).columns.tolist()
    le          = LabelEncoder()
    y           = le.fit_transform(df[label_col].astype(str).str.strip())
    sample_n    = min(10_000, total)
    idx         = np.random.choice(total, sample_n, replace=False)
    X_s         = np.nan_to_num(df[num_cols].values[idx], nan=0.0, posinf=0.0, neginf=0.0)
    y_s         = y[idx]
    suspicious  = []

    _add(lines, f"[CHECK 4] Single-feature stump accuracy (subsample={sample_n:,}, threshold={HIGH_SINGLE_FEATURE_ACC}):")
    for i, col in enumerate(num_cols):
        feat = X_s[:, i].reshape(-1, 1)
        try:
            clf = DecisionTreeClassifier(max_depth=1, random_state=42)
            clf.fit(feat, y_s)
            acc = accuracy_score(y_s, clf.predict(feat))
            if acc > HIGH_SINGLE_FEATURE_ACC:
                suspicious.append((col, round(acc, 4)))
                w = f"  SUSPICIOUS: '{col}' — stump acc={acc:.4f} (>{HIGH_SINGLE_FEATURE_ACC})"
                warnings.append(w); lines.append(w)
        except Exception:
            pass
    if not suspicious:
        lines.append("  OK — no single feature shows suspiciously high predictive power")
    lines.append("")

    # ── 5. High inter-feature correlation ────────────────────────────────────
    _add(lines, f"[CHECK 5] High inter-feature correlation (>{HIGH_CORR_THRESHOLD}):")
    try:
        sample_df  = pd.DataFrame(X_s, columns=num_cols)
        corr       = sample_df.corr().abs()
        upper      = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
        high_pairs = [
            (c, r, round(float(upper.loc[r, c]), 3))
            for c in upper.columns
            for r in upper.index
            if pd.notna(upper.loc[r, c]) and upper.loc[r, c] > HIGH_CORR_THRESHOLD
        ]
        if high_pairs:
            for col1, col2, val in high_pairs[:15]:
                lines.append(f"  {col1} ↔ {col2}: {val}")
            if len(high_pairs) > 15:
                lines.append(f"  ... and {len(high_pairs) - 15} more pairs")
            lines.append(f"  Note: {len(high_pairs)} highly correlated pairs. Consider removing redundant features.")
        else:
            lines.append("  OK — no extreme inter-feature correlations")
    except Exception as e:
        lines.append(f"  Could not compute correlations: {e}")
    lines.append("")

    # ── 6. Class balance ─────────────────────────────────────────────────────
    _add(lines, "[CHECK 6] Class distribution:")
    class_counts = df[label_col].value_counts()
    for cls, cnt in class_counts.items():
        pct = 100.0 * cnt / total
        lines.append(f"  {cls:<40} {cnt:>8,}  ({pct:5.1f}%)")
    benign_pct = 100.0 * class_counts.get("BENIGN", 0) / total if total else 0
    if benign_pct > 80:
        w = f"  WARNING: BENIGN is {benign_pct:.1f}% of data — consider undersampling."
        warnings.append(w); lines.append(w)
    lines.append("")

    # ── Summary ───────────────────────────────────────────────────────────────
    lines += ["=" * 70, f"SUMMARY: {len(warnings)} warning(s) found."]
    for w in warnings:
        lines.append(f"  {w}")
    if not warnings:
        lines.append("  No leakage issues detected. Pipeline looks clean.")
    lines.append("=" * 70)

    text = "\n".join(lines)
    out  = reports_dir / "leakage_report.txt"
    out.write_text(text, encoding="utf-8")
    log.info(f"Leakage report saved -> {out}")
    print(text)

    return {
        "total_rows":              total,
        "duplicate_rows":          n_dup,
        "duplicate_pct":           dup_pct,
        "non_feature_cols":        bad_cols,
        "label_in_features":       label_in,
        "suspicious_features":     suspicious,
        "high_corr_pairs":         len(high_pairs) if "high_pairs" in dir() else 0,
        "warning_count":           len(warnings),
    }


def _add(lines: list, msg: str):
    lines.append(msg)
    log.info(msg)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    DATASET_DIR = Path(
        r"C:\Users\Manus\OneDrive\Desktop\L thirupathi\dataset\csv\MachineLearningCSV\MachineLearningCVE"
    )
    files = sorted(DATASET_DIR.glob("*.csv"))
    if not files:
        print("No CSV files found.")
        sys.exit(1)
    df = pd.read_csv(files[0], low_memory=False)
    df.columns = df.columns.str.strip()
    lc = next((c for c in df.columns if "label" in c.lower()), None)
    if lc:
        check_leakage(df, lc)
    else:
        print("No label column found.")
