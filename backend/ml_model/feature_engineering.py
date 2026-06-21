"""
Feature engineering for CICIDS2017.

Defines three feature categories:
  A. Packet features   — length stats, size averages
  B. Flow features     — duration, bytes/s, packet rates
  C. Behavioral        — TCP flags, window sizes, active/idle times

All lists use the exact CICIDS2017 column names.
Missing columns are skipped gracefully.
"""

import numpy as np
import pandas as pd

# ── Feature category definitions ──────────────────────────────────────────────

PACKET_FEATURES: list[str] = [
    "Packet Length Mean",
    "Packet Length Std",
    "Min Packet Length",
    "Max Packet Length",
    "Average Packet Size",
    "Packet Length Variance",
]

FLOW_FEATURES: list[str] = [
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Fwd Packets/s",
    "Bwd Packets/s",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
]

BEHAVIORAL_FEATURES: list[str] = [
    "SYN Flag Count",
    "ACK Flag Count",
    "RST Flag Count",
    "PSH Flag Count",
    "FIN Flag Count",
    "Down/Up Ratio",
    "Active Mean",
    "Idle Mean",
    "Init_Win_bytes_forward",
    "Init_Win_bytes_backward",
]

NON_FEATURE_COLS: frozenset[str] = frozenset({
    "flow id", "source ip", "source port", "destination ip",
    "destination port", "timestamp", "similarhttp",
})

ALL_RESEARCH_FEATURES: list[str] = PACKET_FEATURES + FLOW_FEATURES + BEHAVIORAL_FEATURES


# ── Helpers ────────────────────────────────────────────────────────────────────

def _col_map(df: pd.DataFrame) -> dict[str, str]:
    """Build lowercase → actual-column-name mapping."""
    return {c.lower().strip(): c for c in df.columns}


def get_available_features(df: pd.DataFrame, feature_list: list[str]) -> list[str]:
    """Return feature names (original case) that actually exist in df."""
    cmap = _col_map(df)
    return [cmap[f.lower().strip()] for f in feature_list if f.lower().strip() in cmap]


def extract_research_features(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Extract packet + flow + behavioral features from df.

    Returns
    -------
    feature_df   : DataFrame with selected columns only
    feature_groups : dict mapping category → list of column names
    """
    pkt  = get_available_features(df, PACKET_FEATURES)
    flow = get_available_features(df, FLOW_FEATURES)
    beh  = get_available_features(df, BEHAVIORAL_FEATURES)

    seen: set[str] = set()
    ordered: list[str] = []
    for c in pkt + flow + beh:
        if c not in seen:
            seen.add(c)
            ordered.append(c)

    groups = {
        "packet_features":     pkt,
        "flow_features":       flow,
        "behavioral_features": beh,
        "total_selected":      ordered,
    }
    return df[ordered].copy(), groups


def get_all_numeric_features(df: pd.DataFrame, label_col: str) -> list[str]:
    """
    Return ALL usable numeric feature columns (full CICIDS2017 feature set).
    Excludes label and identifier columns.
    """
    return [
        c for c in df.columns
        if c != label_col
        and c.lower().strip() not in NON_FEATURE_COLS
        and pd.api.types.is_numeric_dtype(df[c])
    ]


def describe_features(df: pd.DataFrame, label_col: str) -> None:
    """Print a summary of available research features."""
    pkt  = get_available_features(df, PACKET_FEATURES)
    flow = get_available_features(df, FLOW_FEATURES)
    beh  = get_available_features(df, BEHAVIORAL_FEATURES)
    all_ = get_all_numeric_features(df, label_col)

    print(f"\n{'='*60}")
    print("FEATURE ENGINEERING SUMMARY")
    print(f"{'='*60}")
    print(f"  Packet features     : {len(pkt):>3}  {pkt}")
    print(f"  Flow features       : {len(flow):>3}  {flow}")
    print(f"  Behavioral features : {len(beh):>3}  {beh}")
    print(f"  Total research feat : {len(set(pkt+flow+beh)):>3}")
    print(f"  Total numeric feat  : {len(all_):>3}  (full set)")
    print(f"{'='*60}\n")
