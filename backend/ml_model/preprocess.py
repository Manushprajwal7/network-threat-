"""
Dataset loading and preprocessing for CICIDS2017.

Strategy (matches peer-reviewed CICIDS2017 literature):
  1. Load all 8 CSVs and merge.
  2. Class-aware deduplication — BENIGN rows are exact-deduped (traffic is
     naturally diverse), but attack-class rows are KEPT AS-IS.  Deduping
     attacks is wrong because DoS / port-scan traffic is inherently repetitive;
     naive drop_duplicates() collapses an entire attack class to a handful of
     rows, which then falls below MIN_CLASS_SAMPLES and vanishes entirely from
     both train and test, leaving models with nothing but BENIGN to learn.
  3. BENIGN undersampling     — BENIGN is 83 % of the raw data; capping it at
                                1x the total attack count produces a balanced
                                50/50 split for honest per-class evaluation.
  4. Stratified 80/20 split  — ensures every attack class appears in both train
                                and test sets.
  5. Outlier clipping         — per-feature 1st/99th percentile on train only.
  6. StandardScaler           — fit on train, applied to both.

Expected weighted F1 after these steps:
  Random Forest  88-93 %   Decision Tree  85-90 %   Gradient Boost 86-91 %
  KNN            83-88 %   Logistic Reg   75-83 %   SVM            76-83 %
  Naive Bayes    60-72 %
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

NON_FEATURE_COLS = {
    "flow id", "source ip", "source port", "destination ip",
    "destination port", "timestamp", "similarhttp",
}
LABEL_CANDIDATES = ["label", "Label", " Label"]

# BENIGN cap: keep at most this multiple of total attack rows.
# 1.0 = balanced (50 % BENIGN / 50 % attacks) which gives the most honest
# per-class evaluation.  Higher values skew toward BENIGN and produce
# misleadingly high weighted-F1 scores while hiding poor attack recall.
BENIGN_CAP_RATIO = 1.0
# Minimum samples per class to keep.  Must be >= 2 so stratified split works.
# Lower than the old value of 10 so that small attack classes (e.g., Heartbleed
# with ~11 rows) survive the filter.
MIN_CLASS_SAMPLES = 2


def find_label_col(df: pd.DataFrame) -> str:
    for c in LABEL_CANDIDATES:
        if c in df.columns:
            return c
    for c in df.columns:
        if "label" in c.lower():
            return c
    raise ValueError("Cannot find label column. Columns: " + str(df.columns.tolist()))


def load_all_csvs(dataset_dir: Path) -> pd.DataFrame:
    files = sorted(dataset_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files in {dataset_dir}")
    log.info(f"Loading {len(files)} CSV files from {dataset_dir}")
    frames = []
    for f in files:
        try:
            df = pd.read_csv(f, low_memory=False)
            log.info(f"  {f.name}: {len(df):,} rows")
            frames.append(df)
        except Exception as e:
            log.warning(f"  Skipped {f.name}: {e}")
    merged = pd.concat(frames, ignore_index=True)
    log.info(f"Total after merge: {len(merged):,} rows")
    return merged


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    df = df.copy()
    df.columns = df.columns.str.strip()
    label_col = find_label_col(df)
    df[label_col] = df[label_col].astype(str).str.strip()

    # Drop identifier columns
    drop = [c for c in df.columns if c.lower() in NON_FEATURE_COLS]
    if drop:
        log.info(f"  Dropping non-feature cols: {drop}")
        df.drop(columns=drop, inplace=True)

    # Inf -> NaN, then fill numeric NaN with median
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    num_cols = df.select_dtypes(include=[np.number]).columns
    df[num_cols] = df[num_cols].fillna(df[num_cols].median())
    df.dropna(inplace=True)

    # Class-aware deduplication:
    #   BENIGN traffic is naturally diverse → dedup is safe and saves memory.
    #   Attack traffic is inherently repetitive (DoS floods, port scans send
    #   identical packets).  Global drop_duplicates() collapses entire attack
    #   classes to single-digit row counts, which then fail MIN_CLASS_SAMPLES
    #   and disappear from both train and test — leaving only BENIGN.
    before = len(df)
    is_benign = df[label_col].str.upper() == "BENIGN"
    benign_dedup  = df[is_benign].drop_duplicates()
    attacks_kept  = df[~is_benign]          # keep ALL attack rows
    df = pd.concat([benign_dedup, attacks_kept], ignore_index=True)
    log.info(
        f"  Class-aware dedup: removed {before - len(df):,} BENIGN duplicates "
        f"(attack rows preserved); kept {len(df):,} total"
    )

    return df, label_col


def undersample_benign(df: pd.DataFrame, label_col: str, cap_ratio: float) -> pd.DataFrame:
    """Cap BENIGN at cap_ratio × (total non-BENIGN rows)."""
    is_benign = df[label_col].str.upper() == "BENIGN"
    attack_df  = df[~is_benign]
    benign_df  = df[is_benign]

    n_attack = len(attack_df)
    cap      = int(n_attack * cap_ratio)

    if len(benign_df) > cap:
        benign_df = benign_df.sample(n=cap, random_state=42)
        log.info(f"  BENIGN undersampled: {is_benign.sum():,} -> {cap:,} "
                 f"(cap_ratio={cap_ratio}x, attacks={n_attack:,})")

    result = pd.concat([benign_df, attack_df], ignore_index=True)
    log.info(f"  After undersampling: {len(result):,} rows")
    return result


def drop_rare_classes(X: np.ndarray, y: np.ndarray, le: LabelEncoder, min_count: int) -> tuple[np.ndarray, np.ndarray]:
    """Remove classes with fewer than min_count samples (can't generalise)."""
    counts = pd.Series(y).value_counts()
    rare   = counts[counts < min_count].index.tolist()
    if rare:
        rare_names = [le.classes_[i] for i in rare if i < len(le.classes_)]
        log.warning(f"  Dropping {len(rare)} rare class(es) (<{min_count} samples): {rare_names}")
        mask = ~pd.Series(y).isin(rare).values
        X, y = X[mask], y[mask]
    return X, y


def clip_outliers(X: np.ndarray, lower=None, upper=None):
    if lower is None:
        lower = np.percentile(X, 1,  axis=0)
        upper = np.percentile(X, 99, axis=0)
    return np.clip(X, lower, upper), lower, upper


def preprocess_pipeline(
    dataset_dir: Path,
    saved_models_dir: Path,
    test_size: float = 0.2,
    benign_cap_ratio: float = BENIGN_CAP_RATIO,
    random_state: int = 42,
) -> dict:
    """
    Full preprocessing pipeline.

    Steps:
      load -> clean -> dedup -> benign undersample -> stratified split
      -> outlier clip -> scale -> save artefacts
    """
    log.info("=" * 60)
    log.info("Preprocessing — All-days merge + stratified split")
    log.info("=" * 60)

    df_raw = load_all_csvs(dataset_dir)

    log.info("\nCleaning and deduplicating...")
    df, label_col = clean(df_raw)

    log.info("\nClass distribution before undersampling:")
    for cls, cnt in df[label_col].value_counts().items():
        log.info(f"  {cls:<40} {cnt:>8,}")

    log.info("\nUndersampling BENIGN...")
    df = undersample_benign(df, label_col, cap_ratio=benign_cap_ratio)

    # Features / labels
    y_series = df[label_col]
    X_df     = df.drop(columns=[label_col]).select_dtypes(include=[np.number])

    log.info(f"\nFeature matrix: {X_df.shape[0]:,} rows x {X_df.shape[1]} features")
    feature_columns = list(X_df.columns)

    # Drop classes below minimum before encoding
    counts = y_series.value_counts()
    rare   = counts[counts < MIN_CLASS_SAMPLES].index.tolist()
    if rare:
        log.warning(f"Dropping pre-split rare classes: {rare}")
        mask     = ~y_series.isin(rare)
        X_df     = X_df[mask]
        y_series = y_series[mask]

    # Encode labels
    le    = LabelEncoder()
    y_enc = le.fit_transform(y_series)
    log.info(f"Classes ({len(le.classes_)}): {list(le.classes_)}")

    # Stratified split
    X_train, X_test, y_train, y_test = train_test_split(
        X_df.values, y_enc,
        test_size=test_size,
        random_state=random_state,
        stratify=y_enc,
    )
    log.info(f"\nTrain: {X_train.shape[0]:,}  |  Test: {X_test.shape[0]:,}")

    # Post-split sanity check — confirm attack classes appear in the test set
    test_classes  = set(np.unique(y_test))
    train_classes = set(np.unique(y_train))
    all_classes   = set(range(len(le.classes_)))
    missing_test  = all_classes - test_classes
    if missing_test:
        missing_names = [le.classes_[i] for i in sorted(missing_test)]
        log.warning(f"  Classes absent from test set: {missing_names}")
    benign_idx = list(le.classes_).index("BENIGN") if "BENIGN" in le.classes_ else -1
    attack_test_count = int(np.sum(y_test != benign_idx)) if benign_idx >= 0 else len(y_test)
    log.info(f"  Test BENIGN: {int(np.sum(y_test == benign_idx)):,}  |  Attack: {attack_test_count:,}")
    if attack_test_count == 0:
        log.error(
            "TEST SET HAS ZERO ATTACK SAMPLES — models will only learn BENIGN. "
            "Check that attack CSVs loaded correctly and MIN_CLASS_SAMPLES is not too high."
        )

    # Outlier clipping (fit on train only)
    X_train, lower, upper = clip_outliers(X_train)
    X_test,  _,     _     = clip_outliers(X_test, lower, upper)

    # Scale
    scaler         = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    # Save artefacts
    saved_models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler,          saved_models_dir / "scaler.pkl")
    joblib.dump(le,              saved_models_dir / "label_encoder.pkl")
    joblib.dump(feature_columns, saved_models_dir / "feature_columns.pkl")
    joblib.dump(lower,           saved_models_dir / "clip_lower.pkl")
    joblib.dump(upper,           saved_models_dir / "clip_upper.pkl")
    log.info(f"Saved artefacts -> {saved_models_dir}")

    return {
        "X_train":         X_train,
        "X_test":          X_test,
        "X_train_scaled":  X_train_scaled,
        "X_test_scaled":   X_test_scaled,
        "y_train":         y_train,
        "y_test":          y_test,
        "scaler":          scaler,
        "label_encoder":   le,
        "feature_columns": feature_columns,
        "class_names":     list(le.classes_),
        "clip_lower":      lower,
        "clip_upper":      upper,
    }


if __name__ == "__main__":
    DATASET_DIR     = Path(r"C:\Users\Manus\OneDrive\Desktop\L thirupathi\dataset\csv\MachineLearningCSV\MachineLearningCVE")
    SAVED_MODELS_DIR = Path(__file__).parent / "saved_models"
    result = preprocess_pipeline(DATASET_DIR, SAVED_MODELS_DIR)
    print("Train:", result["X_train"].shape)
    print("Test :", result["X_test"].shape)
    print("Classes:", result["class_names"])
