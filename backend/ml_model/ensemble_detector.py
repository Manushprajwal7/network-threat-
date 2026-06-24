"""
Ensemble Detector — combines all available trained models into one decision.

Pipeline stage: FEATURE_EXTRACTION → (this) → TRUST_SCORE

Strategy
--------
1. Run the flow feature vector through every available ensemble member.
   Preferred members: Random Forest, XGBoost, CNN, LSTM. Only members whose
   model artefact exists on disk are used (CNN/LSTM are included automatically
   if/when their .pkl files are added). The ensemble never fabricates a model.
2. Combine member predictions with a confidence-weighted majority vote.
3. Average class-probability vectors for entropy / anomaly analysis.
4. Run unknown / zero-day detection (Isolation Forest + confidence + entropy).

Models are loaded once and cached in ml_model.predict.
"""

import logging
from collections import defaultdict
from typing import Optional

import numpy as np

from ml_model.predict import (
    load_artifact, list_available_models, build_feature_row,
    predict_proba_full, get_risk_level,
)
from ml_model.unknown_attack_detector import detect_unknown

log = logging.getLogger(__name__)

# Preferred ensemble members in priority order. Only those present are used.
ENSEMBLE_PREFERENCE = ["random_forest", "xgboost", "cnn", "lstm"]

_ensemble_members: Optional[list] = None


def get_ensemble_members() -> list:
    """Resolve the ensemble member list to models that actually exist."""
    global _ensemble_members
    if _ensemble_members is None:
        available = set(list_available_models())
        members = [m for m in ENSEMBLE_PREFERENCE if m in available]
        if not members:
            # Fall back to whatever classifier(s) exist so the pipeline still runs.
            members = list(available)
        _ensemble_members = members
        log.info(f"[ML_DETECTION] Ensemble members: {members}")
    return _ensemble_members


def predict_ensemble(features: dict) -> dict:
    """
    Run the full ensemble on one flow feature dict.

    Returns
    -------
    dict with:
        predicted_label    – final ensemble class
        confidence_score   – confidence-weighted agreement (0–1)
        risk_level         – Low / Medium / High / Critical
        per_model          – [{model, prediction, confidence}, ...]
        agreement          – fraction of members agreeing with final label
        known_or_unknown   – Known / Suspicious / Unknown
        anomaly_score      – Isolation Forest anomaly (0–1)
        entropy            – class-probability entropy
        unknown_flags      – triggered unknown-detection conditions
        models_used        – list of member names
    """
    members = get_ensemble_members()
    if not members:
        raise RuntimeError("No trained models available for ensemble.")

    row = build_feature_row(features)

    per_model = []
    vote_weight: dict = defaultdict(float)
    proba_sum: Optional[np.ndarray] = None
    proba_n = 0

    for name in members:
        try:
            label, confidence, proba = predict_proba_full(name, row)
        except Exception as e:
            log.warning(f"[ML_DETECTION] member '{name}' failed: {e}")
            continue

        per_model.append({
            "model": name,
            "prediction": label,
            "confidence": confidence,
        })
        # Confidence-weighted vote (floor weight so 0-confidence still counts)
        vote_weight[label] += confidence if confidence > 0 else 0.5

        if proba is not None:
            proba_sum = proba.copy() if proba_sum is None else proba_sum + proba
            proba_n += 1

    if not per_model:
        raise RuntimeError("All ensemble members failed to predict.")

    # Final label = highest confidence-weighted vote
    final_label = max(vote_weight.items(), key=lambda kv: kv[1])[0]

    members_agreeing = [m for m in per_model if m["prediction"] == final_label]
    agreement = len(members_agreeing) / len(per_model)
    final_conf = (
        sum(m["confidence"] for m in members_agreeing) / len(members_agreeing)
        if members_agreeing else 0.0
    )

    avg_proba = (proba_sum / proba_n) if (proba_sum is not None and proba_n) else None

    # Unknown / zero-day detection
    unknown = detect_unknown(
        feature_row=row,
        predict_proba=avg_proba,
        predicted_label=final_label,
        use_isolation_forest=True,
    )

    # Risk level — escalate when the flow is flagged unknown
    risk_level = get_risk_level(final_label)
    if unknown["known_or_unknown"] == "Unknown":
        risk_level = _max_risk(risk_level, unknown["unknown_risk_level"])

    return {
        "predicted_label":  final_label,
        "confidence_score": round(final_conf, 4),
        "risk_level":       risk_level,
        "per_model":        per_model,
        "agreement":        round(agreement, 3),
        "known_or_unknown": unknown["known_or_unknown"],
        "anomaly_score":    unknown["anomaly_score"],
        "entropy":          unknown["entropy"],
        "unknown_flags":    unknown["flags"],
        "models_used":      [m["model"] for m in per_model],
    }


_RISK_ORDER = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
_RISK_NAME = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}


def _max_risk(a: str, b: str) -> str:
    return _RISK_NAME[max(_RISK_ORDER.get(a, 1), _RISK_ORDER.get(b, 1))]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample = {"flow_duration": 0.02, "Number": 8, "Rate": 400.0,
              "Tot sum": 480, "Max": 60, "Min": 60, "AVG": 60.0,
              "syn_count": 8, "syn_flag_number": 1.0, "TCP": 1.0}
    out = predict_ensemble(sample)
    for k, v in out.items():
        print(f"  {k:<18}: {v}")
