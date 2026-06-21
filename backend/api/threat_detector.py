"""
Threat Detector — high-level wrapper that combines prediction, trust scoring,
and decision making into a single callable.
"""

import logging
import sys
from pathlib import Path

# Allow importing from sibling ml_model package regardless of run location
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from ml_model.predict import predict_threat, list_available_models
from api.trust_manager import compute_trust
from api.decision_engine import make_decision

log = logging.getLogger(__name__)


def detect(
    flow_features: dict,
    model_name: str = "random_forest",
    entity_id: str = "default",
) -> dict:
    """
    Full detection pipeline for one network flow.

    Parameters
    ----------
    flow_features : dict — feature name → value
    model_name    : which ML model to use (default: random_forest)
    entity_id     : entity identifier for trust tracking (e.g. source IP)

    Returns
    -------
    dict with keys from predict, trust, and decision modules combined.
    """
    available = list_available_models()
    if not available:
        raise RuntimeError(
            "No trained models found. Run `python ml_model/train_models.py` first."
        )
    if model_name not in available:
        log.warning(f"Model '{model_name}' not found; falling back to '{available[0]}'")
        model_name = available[0]

    # 1. Predict
    prediction = predict_threat(flow_features, model_name=model_name)

    # 2. Trust score
    trust = compute_trust(
        entity_id=entity_id,
        risk_level=prediction["risk_level"],
        record=True,
    )

    # 3. Decision
    decision = make_decision(
        predicted_label=prediction["predicted_label"],
        risk_level=prediction["risk_level"],
        trust_level=trust["trust_level"],
        entity_id=entity_id,
    )

    return {
        # Prediction
        "predicted_label":   prediction["predicted_label"],
        "confidence_score":  prediction["confidence_score"],
        "risk_level":        prediction["risk_level"],
        "model_used":        prediction["model_used"],
        # Trust
        "user_trust":        trust["user_trust"],
        "device_trust":      trust["device_trust"],
        "behavior_trust":    trust["behavior_trust"],
        "trust_score":       trust["final_trust_score"],
        "trust_level":       trust["trust_level"],
        # Decision
        "action":            decision["action"],
        "reason":            decision["reason"],
        "policy_level":      decision["policy_level"],
    }


if __name__ == "__main__":
    sample_flow = {
        "Flow Duration":         100000,
        "Total Fwd Packets":     5,
        "Total Backward Packets": 3,
        "Flow Bytes/s":          2500.0,
        "Flow Packets/s":        80.0,
    }
    result = detect(sample_flow, entity_id="192.168.0.100")
    for k, v in result.items():
        print(f"  {k:<22}: {v}")
