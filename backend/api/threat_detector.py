"""
Threat Detector — the single analysis entry point that combines:

    ENSEMBLE ML  →  UNKNOWN DETECTION  →  TRUST SCORE  →  SECURITY DECISION

`analyze_flow()` is the canonical per-flow pipeline used by the live
CaptureManager. `detect()` is a thin backward-compatible wrapper used by the
manual /api/predict endpoint and the simulation lab.
"""

import logging
import sys
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from ml_model.ensemble_detector import predict_ensemble
from ml_model.predict import list_available_models
from api.trust_manager import compute_trust
from api.decision_engine import make_decision

log = logging.getLogger(__name__)

_BENIGN = {"BENIGN", "BENIGNTRAFFIC", ""}


def analyze_flow(
    flow_features: dict,
    entity_id: str = "default",
    topology_risk: str = "Low",
) -> dict:
    """
    Full detection pipeline for one network flow.

    Parameters
    ----------
    flow_features : dict   CICIoT2023 feature name → value
    entity_id     : str    entity key for trust tracking (source IP)
    topology_risk : str    current topology risk of the source node (context)
    """
    # 1. Ensemble ML detection (+ unknown/zero-day analysis)
    ens = predict_ensemble(flow_features)
    predicted_label = ens["predicted_label"]
    is_attack = predicted_label.upper() not in _BENIGN

    # 2. Trust score (uses prediction, confidence, anomaly, history, topology)
    trust = compute_trust(
        entity_id=entity_id,
        predicted_label=predicted_label,
        risk_level=ens["risk_level"],
        confidence=ens["confidence_score"],
        anomaly_score=ens["anomaly_score"],
        is_attack=is_attack,
        topology_risk=topology_risk,
        record=True,
    )

    # 3. Security decision (uses every signal + topology criticality)
    decision = make_decision(
        predicted_label=predicted_label,
        risk_level=ens["risk_level"],
        trust_level=trust["trust_level"],
        confidence=ens["confidence_score"],
        anomaly_score=ens["anomaly_score"],
        known_or_unknown=ens["known_or_unknown"],
        topology_criticality=topology_risk,
        repeated_events=trust["repeated_attacks"],
        entity_id=entity_id,
    )

    return {
        # Prediction / ensemble
        "predicted_label":  predicted_label,
        "confidence_score": ens["confidence_score"],
        "risk_level":       ens["risk_level"],
        "model_used":       "+".join(ens["models_used"]) or "ensemble",
        "per_model":        ens["per_model"],
        "agreement":        ens["agreement"],
        "known_or_unknown": ens["known_or_unknown"],
        "anomaly_score":    ens["anomaly_score"],
        "entropy":          ens["entropy"],
        "is_attack":        is_attack,
        # Trust
        "user_trust":        trust["user_trust"],
        "device_trust":      trust["device_trust"],
        "behavior_trust":    trust["behavior_trust"],
        "trust_score":       trust["final_trust_score"],
        "trust_level":       trust["trust_level"],
        "repeated_attacks":  trust["repeated_attacks"],
        # Decision
        "action":            decision["action"],
        "reason":            decision["reason"],
        "policy_level":      decision["policy_level"],
    }


def detect(
    flow_features: dict,
    model_name: str = "ensemble",   # kept for signature compatibility; ensemble always used
    entity_id: str = "default",
) -> dict:
    """Backward-compatible single-flow detection (manual API / simulation)."""
    if not list_available_models():
        raise RuntimeError(
            "No trained models found. Run ml_model/train_ciciot2023_models.py first."
        )
    return analyze_flow(flow_features, entity_id=entity_id, topology_risk="Low")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample = {"flow_duration": 0.01, "Number": 12, "Rate": 1200.0,
              "Tot sum": 720, "Max": 60, "Min": 60, "AVG": 60.0,
              "syn_count": 12, "syn_flag_number": 1.0, "TCP": 1.0}
    for k, v in analyze_flow(sample, entity_id="192.168.0.100").items():
        print(f"  {k:<18}: {v}")
