"""
Dataset loading and preprocessing for CICIoT2023.

Strategy:
  1. Load train/, validation/, test/ folders separately (no random split).
  2. Auto-detect label column (case-insensitive search for 'label').
  3. Class-aware deduplication: drop exact duplicates in BENIGN, keep all attacks.
  4. Handle NaN/Infinity values.
  5. Encode labels and scale numeric features.
  6. Save feature_columns, scaler, label_encoder, clip bounds.

Expected workflow:
  - Train on train/, validate on validation/, test on test/ folders.
  - No undersampling (use class weights in training if needed).
  - Outlier clipping and scaling applied consistently.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

NON_FEATURE_COLS = {
    "flow id", "source ip", "source port", "destination ip",
    "destination port", "timestamp", "similarhttp",
    "flowid", "src", "dst", "protocol",  # Common variants
}

LABEL_CANDIDATES = ["label", "Label", " Label", "Attack", "class", "Category"]
MIN_CLASS_SAMPLES = 2


def find_label_col(df: pd.DataFrame) -> str:
    """Auto-detect label column name."""
    for c in LABEL_CANDIDATES:
        if c in df.columns:
            return c
    for c in df.columns:
        if "label" in c.lower() or "attack" in c.lower() or "class" in c.lower():
            return c
    raise ValueError("Cannot find label column. Columns: " + str(df.columns.tolist()))


def load_csvs_from_folder(folder_path: Path) -> pd.DataFrame:
    """Load all CSV files from a folder and merge them."""
    files = sorted(folder_path.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files in {folder_path}")

    log.info(f"Loading {len(files)} CSV files from {folder_path}")
    frames = []
    for f in files:
        try:
            df = pd.read_csv(f, low_memory=False)
            log.info(f"  {f.name}: {len(df):,} rows")
            frames.append(df)
        except Exception as e:
            log.warning(f"  Skipped {f.name}: {e}")

    if not frames:
        raise ValueError(f"No valid CSV files found in {folder_path}")

    merged = pd.concat(frames, ignore_index=True)
    log.info(f"Total: {len(merged):,} rows")
    return merged


def clean_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """
    Clean column names, find label, remove identifier columns,
    handle NaN/Infinity, deduplicate BENIGN, keep all attacks.
    """
    df = df.copy()
    df.columns = df.columns.str.strip()
    label_col = find_label_col(df)
    df[label_col] = df[label_col].astype(str).str.strip()

    # Drop identifier columns
    drop = [c for c in df.columns if c.lower() in NON_FEATURE_COLS]
    if drop:
        log.info(f"Dropping non-feature cols: {drop}")
        df.drop(columns=drop, inplace=True)

    # Inf -> NaN, then fill numeric NaN with median
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    num_cols = df.select_dtypes(include=[np.number]).columns
    df[num_cols] = df[num_cols].fillna(df[num_cols].median())
    df.dropna(inplace=True)

    # Class-aware deduplication
    before = len(df)
    is_benign = df[label_col].str.upper() == "BENIGN"
    benign_dedup = df[is_benign].drop_duplicates()
    attacks_kept = df[~is_benign]
    df = pd.concat([benign_dedup, attacks_kept], ignore_index=True)
    log.info(
        f"Class-aware dedup: removed {before - len(df):,} BENIGN duplicates "
        f"(kept {len(df):,} total)"
    )

    return df, label_col


def preprocess_ciciot2023(
    dataset_dir: Path,
    saved_models_dir: Path,
) -> dict:
    """
    Load and preprocess CICIoT2023 from separate train/validation/test folders.

    Returns dict with:
      X_train, y_train, X_val, y_val, X_test, y_test (scaled)
      scaler, label_encoder, feature_columns, class_names
      clip_lower, clip_upper
    """
    log.info("=" * 60)
    log.info("CICIoT2023 - Preprocessing (Train/Validation/Test Split)")
    log.info("=" * 60)

    train_dir = dataset_dir / "train"
    val_dir = dataset_dir / "validation"
    test_dir = dataset_dir / "test"

    if not train_dir.exists():
        raise FileNotFoundError(f"Train folder not found: {train_dir}")
    if not val_dir.exists():
        raise FileNotFoundError(f"Validation folder not found: {val_dir}")
    if not test_dir.exists():
        raise FileNotFoundError(f"Test folder not found: {test_dir}")

    # Load all three sets
    log.info("\nLoading train set...")
    df_train = load_csvs_from_folder(train_dir)

    log.info("\nLoading validation set...")
    df_val = load_csvs_from_folder(val_dir)

    log.info("\nLoading test set...")
    df_test = load_csvs_from_folder(test_dir)

    # Clean all three
    log.info("\nCleaning train set...")
    df_train, label_col = clean_dataset(df_train)

    log.info("\nCleaning validation set...")
    df_val, _ = clean_dataset(df_val)

    log.info("\nCleaning test set...")
    df_test, _ = clean_dataset(df_test)

    log.info("\nClass distribution — TRAIN:")
    for cls, cnt in df_train[label_col].value_counts().items():
        log.info(f"  {cls:<40} {cnt:>8,}")

    log.info("\nClass distribution — VALIDATION:")
    for cls, cnt in df_val[label_col].value_counts().items():
        log.info(f"  {cls:<40} {cnt:>8,}")

    log.info("\nClass distribution — TEST:")
    for cls, cnt in df_test[label_col].value_counts().items():
        log.info(f"  {cls:<40} {cnt:>8,}")

    # Extract features and labels from train (to fit encoders/scaler)
    y_train_series = df_train[label_col]
    X_train_df = df_train.drop(columns=[label_col]).select_dtypes(include=[np.number])
    feature_columns = list(X_train_df.columns)

    log.info(f"\nFeature matrix: {X_train_df.shape[0]:,} rows x {X_train_df.shape[1]} features")

    # Drop rare classes from train set before encoding
    counts = y_train_series.value_counts()
    rare = counts[counts < MIN_CLASS_SAMPLES].index.tolist()
    if rare:
        log.warning(f"Dropping rare classes from train: {rare}")
        mask = ~y_train_series.isin(rare)
        X_train_df = X_train_df[mask]
        y_train_series = y_train_series[mask]

    # Encode labels using train set encoder
    le = LabelEncoder()
    y_train_enc = le.fit_transform(y_train_series)
    log.info(f"Classes ({len(le.classes_)}): {list(le.classes_)}")

    # Align validation and test with same features and encoders
    X_val_df = df_val.drop(columns=[label_col]).select_dtypes(include=[np.number])
    X_test_df = df_test.drop(columns=[label_col]).select_dtypes(include=[np.number])

    # Ensure all have the same features (fill missing with 0)
    for df in [X_val_df, X_test_df]:
        for col in feature_columns:
            if col not in df.columns:
                df[col] = 0.0
        # Reorder to match training features
        df = df[feature_columns]

    # Encode validation and test labels (handle unknown classes)
    y_val_series = df_val[label_col]
    y_test_series = df_test[label_col]

    y_val_enc = np.array([
        le.transform([cls])[0] if cls in le.classes_ else 0
        for cls in y_val_series
    ])
    y_test_enc = np.array([
        le.transform([cls])[0] if cls in le.classes_ else 0
        for cls in y_test_series
    ])

    X_train = X_train_df.values
    X_val = X_val_df[feature_columns].values
    X_test = X_test_df[feature_columns].values

    log.info(f"\nDataset sizes:")
    log.info(f"  Train: {X_train.shape[0]:,} rows")
    log.info(f"  Val:   {X_val.shape[0]:,} rows")
    log.info(f"  Test:  {X_test.shape[0]:,} rows")

    # Outlier clipping (fit on train only)
    lower = np.percentile(X_train, 1, axis=0)
    upper = np.percentile(X_train, 99, axis=0)
    X_train = np.clip(X_train, lower, upper)
    X_val = np.clip(X_val, lower, upper)
    X_test = np.clip(X_test, lower, upper)

    # Scale (fit on train only)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    # Save artefacts
    saved_models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, saved_models_dir / "scaler.pkl")
    joblib.dump(le, saved_models_dir / "label_encoder.pkl")
    joblib.dump(feature_columns, saved_models_dir / "feature_columns.pkl")
    joblib.dump(lower, saved_models_dir / "clip_lower.pkl")
    joblib.dump(upper, saved_models_dir / "clip_upper.pkl")
    log.info(f"Saved artefacts -> {saved_models_dir}")

    return {
        "X_train": X_train,
        "X_val": X_val,
        "X_test": X_test,
        "X_train_scaled": X_train_scaled,
        "X_val_scaled": X_val_scaled,
        "X_test_scaled": X_test_scaled,
        "y_train": y_train_enc,
        "y_val": y_val_enc,
        "y_test": y_test_enc,
        "scaler": scaler,
        "label_encoder": le,
        "feature_columns": feature_columns,
        "class_names": list(le.classes_),
        "clip_lower": lower,
        "clip_upper": upper,
    }


if __name__ == "__main__":
    DATASET_DIR = Path(r"C:\Users\Manus\OneDrive\Desktop\L-thirupathi\dataset\archive (3)\CICIOT23")
    SAVED_MODELS_DIR = Path(__file__).parent / "saved_models"
    result = preprocess_ciciot2023(DATASET_DIR, SAVED_MODELS_DIR)
    print(f"Train: {result['X_train'].shape}")
    print(f"Val:   {result['X_val'].shape}")
    print(f"Test:  {result['X_test'].shape}")
    print(f"Classes: {result['class_names']}")
