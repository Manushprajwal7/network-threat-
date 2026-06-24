"""
Unknown / Zero-Day Attack Detector.

Uses three complementary signals:
  1. Prediction confidence threshold     — low confidence → unknown
  2. Isolation Forest anomaly score      — high anomaly → unknown
  3. Entropy of class probability vector — high entropy → uncertain

Supports:
  - Training an Isolation Forest on BENIGN traffic
  - Detecting whether a flow is "known" or "unknown/suspicious"
  - Returning structured detection results for the live pipeline

Saved model: saved_models/isolation_forest.pkl
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import joblib

log = logging.getLogger(__name__)

BASE_DIR         = Path(__file__).parent
SAVED_MODELS_DIR = BASE_DIR / "saved_models"
IF_MODEL_PATH    = SAVED_MODELS_DIR / "isolation_forest.pkl"

# ── Thresholds ─────────────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD  = 0.50   # below → unknown
ANOMALY_THRESHOLD     = 0.55   # IF decision_function > this → normal; else → anomaly
# CICIoT2023 has 34 classes (max entropy ln(34)≈3.53); set a high-uncertainty
# threshold appropriate for that class count to avoid over-flagging.
ENTROPY_THRESHOLD     = 2.70   # above → high uncertainty (nats)

_cache: dict = {}


def _load(name: str):
    if name not in _cache:
        path = SAVED_MODELS_DIR / f"{name}.pkl"
        if not path.exists():
            raise FileNotFoundError(f"Artefact not found: {path}")
        _cache[name] = joblib.load(path)
    return _cache[name]


# ── Training ───────────────────────────────────────────────────────────────────

def train_isolation_forest(
    X_train: np.ndarray,
    y_train: np.ndarray,
    label_encoder,
    contamination: float = 0.05,
) -> None:
    """
    Train an Isolation Forest on BENIGN samples only.
    The IF learns the normal traffic distribution; deviations → anomaly.
    """
    try:
        from sklearn.ensemble import IsolationForest
    except ImportError:
        log.error("scikit-learn not available. Cannot train Isolation Forest.")
        return

    benign_idx = list(label_encoder.classes_).index("BENIGN") \
        if "BENIGN" in label_encoder.classes_ else -1

    if benign_idx >= 0:
        benign_mask = y_train == benign_idx
        X_benign    = X_train[benign_mask]
        log.info(f"Training Isolation Forest on {len(X_benign):,} BENIGN samples")
    else:
        X_benign = X_train
        log.warning("BENIGN class not found — training IF on all training samples")

    iforest = IsolationForest(
        n_estimators  = 200,
        contamination = contamination,
        random_state  = 42,
        n_jobs        = -1,
    )
    iforest.fit(X_benign)

    SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(iforest, IF_MODEL_PATH)
    log.info(f"Isolation Forest saved → {IF_MODEL_PATH}")


# ── Inference ──────────────────────────────────────────────────────────────────

def _shannon_entropy(proba: np.ndarray) -> float:
    """Shannon entropy of a probability vector (nats)."""
    eps = 1e-12
    p   = proba + eps
    return float(-np.sum(p * np.log(p)))


def detect_unknown(
    feature_row: np.ndarray,
    predict_proba: Optional[np.ndarray] = None,
    predicted_label: str = "BENIGN",
    use_isolation_forest: bool = True,
) -> dict:
    """
    Determine whether a flow is a known attack, unknown threat, or benign.

    Parameters
    ----------
    feature_row     : 1D numpy array of scaled features (same as model input)
    predict_proba   : Probability vector from classifier (optional)
    predicted_label : The classifier's predicted class label
    use_isolation_forest : Whether to run the IF anomaly check

    Returns
    -------
    dict with:
        known_or_unknown  — "Known" | "Unknown" | "Suspicious"
        confidence        — top-class probability (0–1)
        anomaly_score     — normalised IF score (0–1, high = anomalous)
        entropy           — class probability entropy (higher = more uncertain)
        unknown_risk_level— "Low" | "Medium" | "High" | "Critical"
        flags             — list of triggered warning conditions
    """
    confidence    = float(np.max(predict_proba)) if predict_proba is not None else 1.0
    entropy       = _shannon_entropy(predict_proba) if predict_proba is not None else 0.0
    anomaly_score = 0.0
    flags: list[str] = []

    # Isolation Forest anomaly score
    if use_isolation_forest and IF_MODEL_PATH.exists():
        try:
            iforest = _load("isolation_forest")
            row_2d  = feature_row.reshape(1, -1)
            # score_samples: more negative = more anomalous
            raw_score    = float(iforest.score_samples(row_2d)[0])
            # Normalise to [0, 1] where 1 = highly anomalous
            anomaly_score = float(np.clip(0.5 - raw_score, 0, 1))
        except Exception as e:
            log.debug(f"IF scoring error: {e}")

    # Flag conditions
    if confidence < CONFIDENCE_THRESHOLD:
        flags.append(f"low_confidence ({confidence:.3f} < {CONFIDENCE_THRESHOLD})")

    if anomaly_score > (1 - ANOMALY_THRESHOLD):
        flags.append(f"high_anomaly_score ({anomaly_score:.3f})")

    if entropy > ENTROPY_THRESHOLD:
        flags.append(f"high_entropy ({entropy:.3f})")

    if predicted_label.upper() == "BENIGN" and anomaly_score > 0.6:
        flags.append("predicted_benign_but_anomalous")

    # Determine known_or_unknown
    is_unknown = len(flags) >= 2
    is_suspicious = len(flags) == 1

    if is_unknown:
        known_or_unknown = "Unknown"
    elif is_suspicious:
        known_or_unknown = "Suspicious"
    else:
        known_or_unknown = "Known"

    # Unknown risk level
    if known_or_unknown == "Unknown":
        if anomaly_score > 0.75 or confidence < 0.40:
            unknown_risk = "Critical"
        elif anomaly_score > 0.55 or confidence < 0.50:
            unknown_risk = "High"
        else:
            unknown_risk = "Medium"
    elif known_or_unknown == "Suspicious":
        unknown_risk = "Medium"
    else:
        unknown_risk = "Low"

    return {
        "known_or_unknown":   known_or_unknown,
        "confidence":         round(confidence, 4),
        "anomaly_score":      round(anomaly_score, 4),
        "entropy":            round(entropy, 4),
        "unknown_risk_level": unknown_risk,
        "flags":              flags,
    }


def generate_synthetic_unknown(n_features: int, n_samples: int = 1) -> np.ndarray:
    """
    Generate synthetic feature vectors that do NOT match training distribution.
    Used by the Attack Simulation Lab for unknown threat simulation.
    """
    rng    = np.random.default_rng(seed=None)
    # Very large values + noise outside normal traffic ranges
    base   = rng.uniform(low=1e6, high=1e8, size=(n_samples, n_features))
    noise  = rng.standard_normal((n_samples, n_features)) * 1e5
    return (base + noise).astype(float)
