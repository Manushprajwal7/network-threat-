"""
Feature extractor: packet-level data → CICIDS2017-compatible feature vector.

NOTE: CICIDS2017 was built with CICFlowMeter, which computes flow-level statistics
(IAT, sub-flow, flags, etc.) over bidirectional traffic sessions. This module
approximates those features from individual packets as a practical demo/research
prototype. Each packet is treated as a single-packet "flow" in the forward direction.
For production deployments, replace with a live CICFlowMeter integration.

Feature names are loaded from the saved feature_columns.pkl so they always match
the trained model exactly; any feature not populated here defaults to 0.
"""

import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

_FEATURE_COLUMNS: Optional[list] = None


def _load_feature_columns() -> list:
    global _FEATURE_COLUMNS
    if _FEATURE_COLUMNS is None:
        try:
            import joblib

            cols_path = (
                Path(__file__).resolve().parent.parent
                / "ml_model"
                / "saved_models"
                / "feature_columns.pkl"
            )
            if cols_path.exists():
                _FEATURE_COLUMNS = joblib.load(cols_path)
                log.info(f"Loaded {len(_FEATURE_COLUMNS)} feature columns from pkl")
            else:
                log.warning("feature_columns.pkl not found — feature vector may be empty")
                _FEATURE_COLUMNS = []
        except Exception as e:
            log.error(f"Failed to load feature columns: {e}")
            _FEATURE_COLUMNS = []
    return _FEATURE_COLUMNS


def extract_features(packet_info: dict) -> dict:
    """
    Convert a parsed packet dict to a CICIDS2017 feature dict.

    Parameters
    ----------
    packet_info : dict
        Keys: timestamp, src_ip, dst_ip, src_port, dst_port, protocol,
              packet_length, ttl, tcp_flags, window_size, payload_length

    Returns
    -------
    dict — feature_name → numeric value, aligned with feature_columns.pkl.
            All CICIDS2017 columns not populated here are left at 0 and
            will be zero-padded by predict_threat().
    """
    _load_feature_columns()  # warm cache

    length: int = int(packet_info.get("packet_length") or 0)
    payload: int = int(packet_info.get("payload_length") or 0)
    dst_port: int = int(packet_info.get("dst_port") or 0)
    window: int = int(packet_info.get("window_size") or 0)
    protocol: str = str(packet_info.get("protocol") or "UNKNOWN").upper()

    # Approximate flow duration in microseconds from packet length (demo heuristic)
    flow_duration = max(1, length * 10)

    features: dict = {
        # ── Core discriminative features ──────────────────────────────────
        "Destination Port": dst_port,
        "Flow Duration": flow_duration,

        # ── Packet/byte counts (single-packet flow) ───────────────────────
        "Total Fwd Packets": 1,
        "Total Backward Packets": 0,
        "Total Length of Fwd Packets": length,
        "Total Length of Bwd Packets": 0,

        # ── Fwd packet length stats ───────────────────────────────────────
        "Fwd Packet Length Max": length,
        "Fwd Packet Length Min": length,
        "Fwd Packet Length Mean": float(length),
        "Fwd Packet Length Std": 0.0,

        # ── Bwd packet length stats ───────────────────────────────────────
        "Bwd Packet Length Max": 0,
        "Bwd Packet Length Min": 0,
        "Bwd Packet Length Mean": 0.0,
        "Bwd Packet Length Std": 0.0,

        # ── Flow-level rates ──────────────────────────────────────────────
        "Flow Bytes/s": float(length) / max(flow_duration / 1e6, 1e-9),
        "Flow Packets/s": 1.0 / max(flow_duration / 1e6, 1e-9),

        # ── Inter-arrival times (zero for single packet) ──────────────────
        "Flow IAT Mean": 0.0,
        "Flow IAT Std": 0.0,
        "Flow IAT Max": 0.0,
        "Flow IAT Min": 0.0,
        "Fwd IAT Total": 0.0,
        "Fwd IAT Mean": 0.0,
        "Fwd IAT Std": 0.0,
        "Fwd IAT Max": 0.0,
        "Fwd IAT Min": 0.0,
        "Bwd IAT Total": 0.0,
        "Bwd IAT Mean": 0.0,
        "Bwd IAT Std": 0.0,
        "Bwd IAT Max": 0.0,
        "Bwd IAT Min": 0.0,

        # ── TCP flags (filled in below if TCP) ────────────────────────────
        "Fwd PSH Flags": 0,
        "Bwd PSH Flags": 0,
        "Fwd URG Flags": 0,
        "Bwd URG Flags": 0,
        "FIN Flag Count": 0,
        "SYN Flag Count": 0,
        "RST Flag Count": 0,
        "PSH Flag Count": 0,
        "ACK Flag Count": 0,
        "URG Flag Count": 0,
        "CWE Flag Count": 0,
        "ECE Flag Count": 0,

        # ── Header lengths ────────────────────────────────────────────────
        "Fwd Header Length": 20 if protocol in ("TCP", "UDP") else 8,
        "Bwd Header Length": 0,
        "Fwd Header Length.1": 20 if protocol in ("TCP", "UDP") else 8,

        # ── Packet length aggregates ──────────────────────────────────────
        "Packet Length Max": length,
        "Packet Length Min": length,
        "Packet Length Mean": float(length),
        "Packet Length Std": 0.0,
        "Packet Length Variance": 0.0,
        "Average Packet Size": float(length),

        # ── Sub-flow (same as flow for single-packet view) ────────────────
        "Subflow Fwd Packets": 1,
        "Subflow Fwd Bytes": length,
        "Subflow Bwd Packets": 0,
        "Subflow Bwd Bytes": 0,

        # ── Window / segment sizing ───────────────────────────────────────
        "Init_Win_bytes_forward": window,
        "Init_Win_bytes_backward": 0,
        "act_data_pkt_fwd": 1 if payload > 0 else 0,
        "min_seg_size_forward": payload if payload > 0 else 0,

        # ── Active / idle (not applicable for single packet) ─────────────
        "Active Mean": 0.0,
        "Active Std": 0.0,
        "Active Max": 0.0,
        "Active Min": 0.0,
        "Idle Mean": 0.0,
        "Idle Std": 0.0,
        "Idle Max": 0.0,
        "Idle Min": 0.0,

        # ── Ratios ────────────────────────────────────────────────────────
        "Down/Up Ratio": 0.0,
    }

    # ── Parse TCP flags ────────────────────────────────────────────────────────
    tcp_flags_raw = packet_info.get("tcp_flags") or ""
    if tcp_flags_raw:
        flag_str = str(tcp_flags_raw).upper()
        if "SYN" in flag_str or flag_str == "S":
            features["SYN Flag Count"] = 1
        if "ACK" in flag_str or flag_str == "A":
            features["ACK Flag Count"] = 1
        if "FIN" in flag_str or flag_str == "F":
            features["FIN Flag Count"] = 1
        if "RST" in flag_str or flag_str == "R":
            features["RST Flag Count"] = 1
        if "PSH" in flag_str or flag_str == "P":
            features["PSH Flag Count"] = 1
            features["Fwd PSH Flags"] = 1
        if "URG" in flag_str or flag_str == "U":
            features["URG Flag Count"] = 1
            features["Fwd URG Flags"] = 1

    return features
