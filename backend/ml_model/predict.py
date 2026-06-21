"""
Prediction module — load saved models and predict threat class for new traffic flows.

Usage:
    from ml_model.predict import predict_threat

    result = predict_threat(
        input_features={"Flow Duration": 12345, "Total Fwd Packets": 10, ...},
        model_name="random_forest"
    )
"""

import logging
from pathlib import Path
from typing import Union

import numpy as np
import joblib

log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
SAVED_MODELS_DIR = BASE_DIR / "saved_models"

# Risk level mapping by attack class (case-insensitive substring match)
_RISK_MAP = {
    "benign":      "Low",
    "dos":         "High",
    "ddos":        "High",
    "portscan":    "High",
    "botnet":      "Critical",
    "infiltration": "Critical",
    "web attack":  "Critical",
    "brute force": "Critical",
}

# Cache for loaded artefacts (avoids re-loading on every call)
_cache: dict = {}


def _load(name: str):
    if name not in _cache:
        path = SAVED_MODELS_DIR / f"{name}.pkl"
        if not path.exists():
            raise FileNotFoundError(f"Saved artefact not found: {path}")
        _cache[name] = joblib.load(path)
    return _cache[name]


def _get_risk_level(label: str) -> str:
    label_lower = label.lower()
    for keyword, risk in _RISK_MAP.items():
        if keyword in label_lower:
            return risk
    return "Medium"


def predict_threat(
    input_features: dict,
    model_name: str = "random_forest",
) -> dict:
    """
    Predict the threat class for a single traffic flow.

    Parameters
    ----------
    input_features : dict
        Feature name → value mapping (any subset of trained features is fine).
    model_name : str
        One of: random_forest, decision_tree, logistic_regression, svm,
                knn, gradient_boosting, naive_bayes

    Returns
    -------
    dict with keys:
        predicted_label   – human-readable attack class
        confidence_score  – probability of top class (0–1)
        risk_level        – Low / Medium / High / Critical
        model_used        – model name used for prediction
    """
    model = _load(model_name)
    scaler = _load("scaler")
    le = _load("label_encoder")
    feature_columns: list = _load("feature_columns")

    # Build a row aligned with training feature columns; fill missing cols with 0
    row = np.zeros(len(feature_columns), dtype=float)
    for i, col in enumerate(feature_columns):
        if col in input_features:
            try:
                row[i] = float(input_features[col])
            except (TypeError, ValueError):
                row[i] = 0.0

    # Apply same outlier clipping used during training (if artefacts exist)
    clip_lower_path = SAVED_MODELS_DIR / "clip_lower.pkl"
    clip_upper_path = SAVED_MODELS_DIR / "clip_upper.pkl"
    if clip_lower_path.exists() and clip_upper_path.exists():
        row = np.clip(row, _load("clip_lower"), _load("clip_upper"))

    # Models that need scaling
    needs_scaling = {"logistic_regression", "svm", "knn"}
    if model_name in needs_scaling:
        row = scaler.transform(row.reshape(1, -1))
    else:
        row = row.reshape(1, -1)

    # Predict
    y_pred = model.predict(row)[0]
    predicted_label = le.inverse_transform([y_pred])[0]

    # Confidence
    confidence_score = 0.0
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(row)[0]
        confidence_score = float(np.max(proba))
    elif hasattr(model, "decision_function"):
        # SVM without probability=True fallback
        df_val = model.decision_function(row)[0]
        if isinstance(df_val, np.ndarray):
            confidence_score = float(np.max(np.abs(df_val))) / (float(np.sum(np.abs(df_val))) + 1e-9)
        else:
            confidence_score = min(abs(float(df_val)), 1.0)

    risk_level = _get_risk_level(predicted_label)

    return {
        "predicted_label":  predicted_label,
        "confidence_score": round(confidence_score, 4),
        "risk_level":       risk_level,
        "model_used":       model_name,
    }


def list_available_models() -> list[str]:
    """Return names of models that have a saved .pkl file."""
    known = [
        "random_forest", "decision_tree", "logistic_regression",
        "svm", "knn", "gradient_boosting", "naive_bayes",
    ]
    return [m for m in known if (SAVED_MODELS_DIR / f"{m}.pkl").exists()]


if __name__ == "__main__":
    # Quick smoke-test with dummy features
    available = list_available_models()
    if not available:
        print("No saved models found. Run train_models.py first.")
    else:
        sample = {"Flow Duration": 100000, "Total Fwd Packets": 5, "Total Backward Packets": 3}
        for m in available:
            try:
                r = predict_threat(sample, model_name=m)
                print(f"[{m}] → {r['predicted_label']} (conf={r['confidence_score']:.3f}, risk={r['risk_level']})")
            except Exception as e:
                print(f"[{m}] ERROR: {e}")
