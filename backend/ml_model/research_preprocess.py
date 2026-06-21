"""
Research-grade preprocessing for CICIDS2017.

Implements four split strategies to prevent data leakage:

  A. Random Stratified   — baseline only (not used for publication metrics)
  B. File-based          — train on some CSV files, test on held-out files
  C. Temporal            — sort by Timestamp, train on earlier, test on later
  D. Attack-holdout      — hold out one attack family; test unknown detection

Configuration
-------------
RESEARCH_MODE            = True   → enable file-based / temporal split
MAX_SAMPLES_PER_CLASS    = 50_000 → cap per class to avoid RAM issues
BENIGN_UNDERSAMPLE_RATIO = 2.0    → keep at most 2× attack rows as BENIGN
FAST_MODE                = True   → use smaller caps for quick iteration

Usage
-----
from research_preprocess import research_pipeline

data = research_pipeline(
    dataset_dir   = Path("..."),
    saved_models_dir = Path("..."),
    split_mode    = "file",   # "random" | "file" | "temporal" | "attack_holdout"
)
"""

import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib

log = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────

RESEARCH_MODE            = True
MAX_SAMPLES_PER_CLASS    = 50_000
BENIGN_UNDERSAMPLE_RATIO = 2.0
FAST_MODE                = True
FAST_MAX_PER_CLASS       = 20_000
MIN_CLASS_SAMPLES        = 4        # must have at least this many to stratify

NON_FEATURE_COLS: frozenset[str] = frozenset({
    "flow id", "source ip", "source port", "destination ip",
    "destination port", "timestamp", "similarhttp",
})

DATASET_DIR = Path(
    os.environ.get(
        "CICIDS_DATASET_DIR",
        r"C:\Users\Manus\OneDrive\Desktop\L thirupathi\dataset\csv"
        r"\MachineLearningCSV\MachineLearningCVE",
    )
)

# File-based split: which files go to test?
# CICIDS2017 daily files — use Friday (DoS Hulk, PortScan, DDoS) for test.
# Adjust if your file naming differs.
TEST_FILES_KEYWORDS = ["friday", "Thursday", "thursday"]


# ── Internal helpers ───────────────────────────────────────────────────────────

def _find_label_col(df: pd.DataFrame) -> str:
    for cand in ["label", "Label", " Label"]:
        if cand in df.columns:
            return cand
    for c in df.columns:
        if "label" in c.lower():
            return c
    raise ValueError(f"Cannot find label column. Columns: {df.columns.tolist()}")


def _clean(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    df = df.copy()
    df.columns = df.columns.str.strip()
    lc = _find_label_col(df)
    df[lc] = df[lc].astype(str).str.strip()

    drop = [c for c in df.columns if c.lower().strip() in NON_FEATURE_COLS]
    if drop:
        df.drop(columns=drop, inplace=True)
        log.info(f"  Dropped identifier columns: {drop}")

    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    num = df.select_dtypes(include=[np.number]).columns
    df[num] = df[num].fillna(df[num].median())
    df.dropna(inplace=True)
    return df, lc


def _class_aware_dedup(df: pd.DataFrame, lc: str) -> pd.DataFrame:
    """Dedup BENIGN only; keep all attack rows (repetitive by nature)."""
    before  = len(df)
    benign  = df[df[lc].str.upper() == "BENIGN"].drop_duplicates()
    attacks = df[df[lc].str.upper() != "BENIGN"]
    df      = pd.concat([benign, attacks], ignore_index=True)
    log.info(f"  Class-aware dedup: removed {before - len(df):,} BENIGN duplicates")
    return df


def _cap_classes(df: pd.DataFrame, lc: str, max_per_class: int) -> pd.DataFrame:
    """Cap each class to max_per_class rows."""
    parts = []
    for cls, grp in df.groupby(lc):
        if len(grp) > max_per_class:
            grp = grp.sample(max_per_class, random_state=42)
            log.info(f"  Capped '{cls}' to {max_per_class:,} rows")
        parts.append(grp)
    return pd.concat(parts, ignore_index=True)


def _undersample_benign(df: pd.DataFrame, lc: str, ratio: float) -> pd.DataFrame:
    """Keep at most ratio × (total attack rows) BENIGN rows."""
    is_b   = df[lc].str.upper() == "BENIGN"
    atk    = df[~is_b]
    ben    = df[is_b]
    cap    = int(len(atk) * ratio)
    if len(ben) > cap:
        ben = ben.sample(cap, random_state=42)
        log.info(f"  BENIGN undersampled {is_b.sum():,} → {cap:,}")
    return pd.concat([ben, atk], ignore_index=True)


def _clip_outliers(X: np.ndarray, lower=None, upper=None):
    if lower is None:
        lower = np.percentile(X, 1,  axis=0)
        upper = np.percentile(X, 99, axis=0)
    return np.clip(X, lower, upper), lower, upper


def _encode_and_split(X_tr_df, X_te_df, y_tr_s, y_te_s):
    """Encode labels, clip, scale, return full data dict."""
    le          = LabelEncoder()
    y_all       = pd.concat([y_tr_s, y_te_s])
    le.fit(y_all.astype(str).str.strip())
    y_train     = le.transform(y_tr_s.astype(str).str.strip())
    y_test      = le.transform(y_te_s.astype(str).str.strip())

    feature_columns = list(X_tr_df.columns)
    X_train = X_tr_df.values.astype(float)
    X_test  = X_te_df.values.astype(float)

    X_train, lower, upper = _clip_outliers(X_train)
    X_test,  _,     _     = _clip_outliers(X_test, lower, upper)

    scaler         = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    log.info(f"  Train: {X_train.shape[0]:,}  |  Test: {X_test.shape[0]:,}")
    log.info(f"  Classes ({len(le.classes_)}): {list(le.classes_)}")

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


def _save_artefacts(data: dict, saved_models_dir: Path) -> None:
    saved_models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(data["scaler"],          saved_models_dir / "scaler.pkl")
    joblib.dump(data["label_encoder"],   saved_models_dir / "label_encoder.pkl")
    joblib.dump(data["feature_columns"], saved_models_dir / "feature_columns.pkl")
    joblib.dump(data["clip_lower"],      saved_models_dir / "clip_lower.pkl")
    joblib.dump(data["clip_upper"],      saved_models_dir / "clip_upper.pkl")
    log.info(f"  Saved preprocessing artefacts → {saved_models_dir}")


# ── Split strategies ───────────────────────────────────────────────────────────

def _split_random(df: pd.DataFrame, lc: str, test_size: float = 0.2):
    """Stratified random split (baseline only)."""
    log.info("[SPLIT] Random stratified 80/20 split")
    feat = df.drop(columns=[lc]).select_dtypes(include=[np.number])
    y    = df[lc]
    return feat, feat, y, y, train_test_split(
        feat, y, test_size=test_size, random_state=42, stratify=y
    )


def _split_file_based(files_train: list[Path], files_test: list[Path],
                      max_per_class: int, benign_ratio: float):
    """
    Train on files_train, test on files_test.
    Returns (train_df, test_df), both cleaned and capped.
    """
    log.info(f"[SPLIT] File-based — train files: {[f.name for f in files_train]}")
    log.info(f"        test  files: {[f.name for f in files_test]}")

    def _load(paths):
        parts = []
        for p in paths:
            try:
                df = pd.read_csv(p, low_memory=False)
                log.info(f"  Loaded {p.name}: {len(df):,} rows")
                parts.append(df)
            except Exception as e:
                log.warning(f"  Skipped {p.name}: {e}")
        return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()

    train_raw = _load(files_train)
    test_raw  = _load(files_test)

    if train_raw.empty or test_raw.empty:
        raise ValueError("File-based split: train or test set is empty.")

    train_df, lc = _clean(train_raw)
    test_df,  _  = _clean(test_raw)

    train_df = _class_aware_dedup(train_df, lc)
    train_df = _undersample_benign(train_df, lc, benign_ratio)
    train_df = _cap_classes(train_df, lc, max_per_class)

    test_df  = _cap_classes(test_df, lc, max_per_class // 2)

    return train_df, test_df, lc


def _split_temporal(df: pd.DataFrame, lc: str, timestamp_col: str,
                    train_ratio: float = 0.75):
    """Sort by timestamp; use first train_ratio% as train, rest as test."""
    log.info(f"[SPLIT] Temporal — column='{timestamp_col}', train_ratio={train_ratio}")
    df     = df.sort_values(timestamp_col).reset_index(drop=True)
    n      = len(df)
    cutoff = int(n * train_ratio)
    return df.iloc[:cutoff], df.iloc[cutoff:], lc


def _split_attack_holdout(df: pd.DataFrame, lc: str, holdout_attack: str):
    """
    Hold out all rows of holdout_attack from training.
    Test set contains both held-out attack and a BENIGN sample.
    """
    log.info(f"[SPLIT] Attack holdout — held out: '{holdout_attack}'")
    mask_holdout = df[lc].str.contains(holdout_attack, case=False, na=False)
    train_df     = df[~mask_holdout]
    holdout_df   = df[mask_holdout]
    n_holdout    = len(holdout_df)
    benign_test  = df[df[lc].str.upper() == "BENIGN"].sample(
        min(n_holdout * 2, int(df[lc].str.upper().eq("BENIGN").sum())), random_state=42
    )
    test_df = pd.concat([holdout_df, benign_test], ignore_index=True)
    log.info(f"  Holdout rows: {n_holdout:,}  |  Test size: {len(test_df):,}")
    return train_df, test_df, lc


# ── Public pipeline ────────────────────────────────────────────────────────────

def research_pipeline(
    dataset_dir:      Path,
    saved_models_dir: Path,
    split_mode:       str  = "file",      # random | file | temporal | attack_holdout
    holdout_attack:   str  = "PortScan",  # used when split_mode="attack_holdout"
    fast_mode:        bool = FAST_MODE,
) -> dict:
    """
    Research-grade preprocessing pipeline.

    Parameters
    ----------
    dataset_dir      : Path to directory containing CICIDS2017 CSV files
    saved_models_dir : Where to save scaler/encoder/feature artefacts
    split_mode       : "random" | "file" | "temporal" | "attack_holdout"
    holdout_attack   : Attack family to hold out (attack_holdout mode)
    fast_mode        : Cap samples for faster iteration

    Returns
    -------
    dict with X_train, X_test, y_train, y_test, scaled versions,
    scaler, label_encoder, feature_columns, class_names, clip bounds,
    and split_mode metadata.
    """
    max_per_class = FAST_MAX_PER_CLASS if fast_mode else MAX_SAMPLES_PER_CLASS
    log.info("=" * 60)
    log.info(f"Research Pipeline — split_mode={split_mode}  fast={fast_mode}")
    log.info(f"Max per class: {max_per_class:,}")
    log.info("=" * 60)

    files = sorted(dataset_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files in {dataset_dir}")
    log.info(f"Found {len(files)} CSV file(s)")

    # ── File-based split ──────────────────────────────────────────────────────
    if split_mode == "file":
        test_kw    = TEST_FILES_KEYWORDS
        test_files = [f for f in files if any(kw.lower() in f.name.lower() for kw in test_kw)]
        train_files= [f for f in files if f not in test_files]

        if not test_files:
            log.warning("No test files matched keywords — falling back to last file as test.")
            test_files  = files[-1:]
            train_files = files[:-1]

        if not train_files:
            log.warning("Only 1 CSV found — using random split instead.")
            split_mode = "random"
        else:
            train_df, test_df, lc = _split_file_based(
                train_files, test_files, max_per_class,
                BENIGN_UNDERSAMPLE_RATIO
            )
            X_tr_df = train_df.drop(columns=[lc]).select_dtypes(include=[np.number])
            X_te_df = test_df.drop(columns=[lc]).select_dtypes(include=[np.number])
            # Align columns
            common  = [c for c in X_tr_df.columns if c in X_te_df.columns]
            X_tr_df = X_tr_df[common]
            X_te_df = X_te_df[common]
            y_tr_s  = train_df[lc]
            y_te_s  = test_df[lc]

            # Drop rare classes
            for df_, y_ in [(None, y_tr_s), (None, y_te_s)]:
                pass
            all_classes = set(y_tr_s.unique()) & set(y_te_s.unique())
            mask_tr = y_tr_s.isin(all_classes)
            mask_te = y_te_s.isin(all_classes)
            X_tr_df = X_tr_df[mask_tr.values]
            y_tr_s  = y_tr_s[mask_tr]
            X_te_df = X_te_df[mask_te.values]
            y_te_s  = y_te_s[mask_te]

            data = _encode_and_split(X_tr_df, X_te_df, y_tr_s, y_te_s)
            data["split_mode"] = "file"
            _save_artefacts(data, saved_models_dir)
            return data

    # ── Load all CSVs (for random / temporal / attack_holdout) ────────────────
    frames = []
    for f in files:
        try:
            df = pd.read_csv(f, low_memory=False)
            log.info(f"  {f.name}: {len(df):,} rows")
            frames.append(df)
        except Exception as e:
            log.warning(f"  Skipped {f.name}: {e}")
    merged = pd.concat(frames, ignore_index=True)
    log.info(f"Total: {len(merged):,} rows")

    df, lc = _clean(merged)
    df = _class_aware_dedup(df, lc)
    df = _undersample_benign(df, lc, BENIGN_UNDERSAMPLE_RATIO)
    df = _cap_classes(df, lc, max_per_class)

    # ── Temporal split ────────────────────────────────────────────────────────
    if split_mode == "temporal":
        ts_col = next(
            (c for c in merged.columns if "timestamp" in c.lower()), None
        )
        if ts_col is None:
            log.warning("No Timestamp column found — falling back to random split.")
            split_mode = "random"
        else:
            # Re-clean with timestamp kept for sorting, then drop
            df_ts, _ = _clean(pd.concat(frames, ignore_index=True))
            # Restore timestamp from original merged df
            orig_ts_col = next(c for c in merged.columns if "timestamp" in c.lower())
            df_ts["__ts__"] = pd.to_datetime(
                merged[orig_ts_col].astype(str), errors="coerce"
            ).values[:len(df_ts)]
            df_ts = df_ts.sort_values("__ts__").reset_index(drop=True)
            df_ts.drop(columns=["__ts__"], inplace=True)
            df    = _class_aware_dedup(df_ts, lc)
            df    = _undersample_benign(df, lc, BENIGN_UNDERSAMPLE_RATIO)
            df    = _cap_classes(df, lc, max_per_class)
            n     = len(df)
            cut   = int(n * 0.75)
            train_df, test_df = df.iloc[:cut], df.iloc[cut:]
            X_tr_df = train_df.drop(columns=[lc]).select_dtypes(include=[np.number])
            X_te_df = test_df.drop(columns=[lc]).select_dtypes(include=[np.number])
            common  = [c for c in X_tr_df.columns if c in X_te_df.columns]
            data    = _encode_and_split(
                X_tr_df[common], X_te_df[common],
                train_df[lc], test_df[lc]
            )
            data["split_mode"] = "temporal"
            _save_artefacts(data, saved_models_dir)
            return data

    # ── Attack-holdout split ──────────────────────────────────────────────────
    if split_mode == "attack_holdout":
        train_df, test_df, _ = _split_attack_holdout(df, lc, holdout_attack)
        X_tr_df = train_df.drop(columns=[lc]).select_dtypes(include=[np.number])
        X_te_df = test_df.drop(columns=[lc]).select_dtypes(include=[np.number])
        common  = [c for c in X_tr_df.columns if c in X_te_df.columns]
        data    = _encode_and_split(
            X_tr_df[common], X_te_df[common],
            train_df[lc], test_df[lc]
        )
        data["split_mode"]     = "attack_holdout"
        data["holdout_attack"] = holdout_attack
        _save_artefacts(data, saved_models_dir)
        return data

    # ── Random stratified split (fallback / baseline) ─────────────────────────
    log.info("[SPLIT] Random stratified 80/20 (baseline)")
    feat    = df.drop(columns=[lc]).select_dtypes(include=[np.number])
    y       = df[lc]
    X_tr_df, X_te_df, y_tr_s, y_te_s = train_test_split(
        feat, y, test_size=0.2, random_state=42, stratify=y
    )
    data = _encode_and_split(X_tr_df, X_te_df, y_tr_s, y_te_s)
    data["split_mode"] = "random"
    _save_artefacts(data, saved_models_dir)
    return data


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    BASE = Path(__file__).parent
    result = research_pipeline(
        dataset_dir      = DATASET_DIR,
        saved_models_dir = BASE / "saved_models_research",
        split_mode       = "file",
        fast_mode        = True,
    )
    print(f"\nTrain: {result['X_train'].shape}")
    print(f"Test : {result['X_test'].shape}")
    print(f"Classes: {result['class_names']}")
    print(f"Split mode: {result['split_mode']}")
