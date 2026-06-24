"""
Feature Extractor — flow statistics → CICIoT2023 feature vector.

Pipeline stage: FLOW_AGGREGATION → (this) → ML_DETECTION

The models in saved_models/ are trained on the **CICIoT2023** schema
(46 numeric features). This module converts a real aggregated flow record
(produced by flow_aggregator.FlowAggregator) into that exact 46-feature
vector, aligned to feature_columns.pkl.

CICIoT2023 features are window/flow statistics. Where a feature has no direct
live equivalent it is approximated from real packet statistics (documented per
line) — never faked. Any column present in feature_columns.pkl but not produced
here is zero-filled downstream by the predictor, satisfying the
"fill missing trained features with 0" requirement.
"""

import logging
import math
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

_FEATURE_COLUMNS: Optional[list] = None

# Application-protocol presence columns expected by CICIoT2023
_APP_PROTO_COLS = ("HTTP", "HTTPS", "DNS", "Telnet", "SMTP", "SSH", "IRC", "DHCP")


def _load_feature_columns() -> list:
    global _FEATURE_COLUMNS
    if _FEATURE_COLUMNS is None:
        try:
            import joblib
            cols_path = (
                Path(__file__).resolve().parent.parent
                / "ml_model" / "saved_models" / "feature_columns.pkl"
            )
            if cols_path.exists():
                _FEATURE_COLUMNS = list(joblib.load(cols_path))
                log.info(f"[FEATURE_EXTRACTION] Loaded {len(_FEATURE_COLUMNS)} CICIoT2023 feature columns")
            else:
                log.warning("[FEATURE_EXTRACTION] feature_columns.pkl not found")
                _FEATURE_COLUMNS = []
        except Exception as e:
            log.error(f"[FEATURE_EXTRACTION] Failed to load feature columns: {e}")
            _FEATURE_COLUMNS = []
    return _FEATURE_COLUMNS


def _mean(xs) -> float:
    return float(sum(xs) / len(xs)) if xs else 0.0


def _variance(xs) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return float(sum((x - m) ** 2 for x in xs) / len(xs))


def _std(xs) -> float:
    return math.sqrt(_variance(xs))


def _covariance(a, b) -> float:
    """Covariance of incoming/outgoing size sequences (paired up to min length)."""
    n = min(len(a), len(b))
    if n < 2:
        return 0.0
    am, bm = _mean(a[:n]), _mean(b[:n])
    return float(sum((a[i] - am) * (b[i] - bm) for i in range(n)) / n)


def extract_features(flow: dict) -> dict:
    """
    Convert an aggregated flow record into a CICIoT2023 feature dict.

    Parameters
    ----------
    flow : dict
        Flow record from FlowAggregator.snapshot() with keys:
        protocol, proto_num, duration, packet_count, fwd_count, bwd_count,
        fwd_sizes, bwd_sizes, all_sizes, header_bytes, ttl_mean, iats,
        app_protocols, flags{...}

    Returns
    -------
    dict — feature_name → numeric value, keyed by the CICIoT2023 schema.
    """
    _load_feature_columns()

    sizes      = flow.get("all_sizes") or []
    fwd_sizes  = flow.get("fwd_sizes") or []
    bwd_sizes  = flow.get("bwd_sizes") or []
    iats       = flow.get("iats") or []
    flags      = flow.get("flags") or {}
    duration   = float(flow.get("duration") or 0.0)
    n_pkts     = int(flow.get("packet_count") or 0)
    fwd_n      = int(flow.get("fwd_count") or 0)
    bwd_n      = int(flow.get("bwd_count") or 0)
    proto_num  = int(flow.get("proto_num") or 0)
    app_protos = flow.get("app_protocols") or set()

    # Rates (guard against zero-duration single-packet windows)
    dur_safe = duration if duration > 1e-6 else 1e-6
    rate  = n_pkts / dur_safe
    srate = fwd_n / dur_safe
    drate = bwd_n / dur_safe

    tot_sum = float(sum(sizes))
    s_min   = float(min(sizes)) if sizes else 0.0
    s_max   = float(max(sizes)) if sizes else 0.0
    s_avg   = _mean(sizes)
    s_std   = _std(sizes)

    mean_fwd, mean_bwd = _mean(fwd_sizes), _mean(bwd_sizes)
    var_fwd,  var_bwd  = _variance(fwd_sizes), _variance(bwd_sizes)

    # CICIoT2023 derived statistics
    magnitude  = math.sqrt(max(0.0, mean_fwd + mean_bwd))
    radius     = math.sqrt(max(0.0, var_fwd + var_bwd))
    covariance = _covariance(fwd_sizes, bwd_sizes)
    variance   = _variance(sizes)
    weight     = float(fwd_n * bwd_n)

    # Transport / network protocol presence
    is_tcp  = 1.0 if (proto_num == 6) else 0.0
    is_udp  = 1.0 if (proto_num == 17) else 0.0
    is_icmp = 1.0 if (proto_num in (1, 58)) else 0.0

    features = {
        # ── Timing / size ──────────────────────────────────────────────
        "flow_duration": duration,
        "Header_Length": float(flow.get("header_bytes") or 0),
        "Protocol Type": float(proto_num),
        "Duration":      float(flow.get("ttl_mean") or 0.0),   # CICIoT "Duration" = IP TTL
        "Rate":          rate,
        "Srate":         srate,
        "Drate":         drate,

        # ── TCP flag presence (0/1) ────────────────────────────────────
        "fin_flag_number": 1.0 if flags.get("fin") else 0.0,
        "syn_flag_number": 1.0 if flags.get("syn") else 0.0,
        "rst_flag_number": 1.0 if flags.get("rst") else 0.0,
        "psh_flag_number": 1.0 if flags.get("psh") else 0.0,
        "ack_flag_number": 1.0 if flags.get("ack") else 0.0,
        "ece_flag_number": 1.0 if flags.get("ece") else 0.0,
        "cwr_flag_number": 1.0 if flags.get("cwr") else 0.0,

        # ── TCP flag counts ────────────────────────────────────────────
        "ack_count": float(flags.get("ack") or 0),
        "syn_count": float(flags.get("syn") or 0),
        "fin_count": float(flags.get("fin") or 0),
        "urg_count": float(flags.get("urg") or 0),
        "rst_count": float(flags.get("rst") or 0),

        # ── Application protocol presence (0/1) ─────────────────────────
        "HTTP":   1.0 if "HTTP"   in app_protos else 0.0,
        "HTTPS":  1.0 if "HTTPS"  in app_protos else 0.0,
        "DNS":    1.0 if "DNS"    in app_protos else 0.0,
        "Telnet": 1.0 if "Telnet" in app_protos else 0.0,
        "SMTP":   1.0 if "SMTP"   in app_protos else 0.0,
        "SSH":    1.0 if "SSH"    in app_protos else 0.0,
        "IRC":    1.0 if "IRC"    in app_protos else 0.0,

        # ── Transport / network layer presence (0/1) ────────────────────
        "TCP":  is_tcp,
        "UDP":  is_udp,
        "DHCP": 1.0 if "DHCP" in app_protos else 0.0,
        "ARP":  0.0,            # ARP frames are non-IP and filtered upstream
        "ICMP": is_icmp,
        "IPv":  1.0,            # all captured packets are IP
        "LLC":  0.0,            # link-layer LLC not captured

        # ── Packet-size statistics ──────────────────────────────────────
        "Tot sum":  tot_sum,
        "Min":      s_min,
        "Max":      s_max,
        "AVG":      s_avg,
        "Std":      s_std,
        "Tot size": s_avg,      # representative packet size for the window
        "IAT":      _mean(iats),
        "Number":   float(n_pkts),
        "Magnitue": magnitude,  # (sic) dataset spelling
        "Radius":   radius,
        "Covariance": covariance,
        "Variance": variance,
        "Weight":   weight,
    }

    return features
