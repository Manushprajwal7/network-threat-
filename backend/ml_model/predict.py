"""
Prediction module — load saved CICIoT2023 models and score traffic flows.

Provides:
  - load_artifact(name)        : cached joblib loader (XGBoost forced to CPU)
  - list_available_models()    : models that actually have a .pkl on disk
  - build_feature_row(features): align a feature dict to feature_columns + clip
  - predict_proba_full(...)    : full class-probability vector for one model
  - predict_threat(...)        : single-model convenience prediction

The ensemble (ml_model.ensemble_detector) builds on these primitives so that
models and artefacts are loaded exactly once and shared across the pipeline.
"""

import logging
import warnings
from pathlib import Path

import numpy as np
import joblib

warnings.filterwarnings(
    "ignore",
    message=r".*sklearn\.utils\.parallel\.delayed.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r".*make it possible to propagate the scikit-learn configuration.*",
    category=UserWarning,
)

log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
SAVED_MODELS_DIR = BASE_DIR / "saved_models"

# All classifier model files we know how to load via joblib.
KNOWN_MODELS = [
    "random_forest", "decision_tree", "logistic_regression",
    "svm", "knn", "xgboost", "naive_bayes",
]

# Models trained on StandardScaler-transformed features.
NEEDS_SCALING = {"logistic_regression", "svm", "knn"}

# Risk level by CICIoT2023 attack-class keyword (checked in order, first match wins)
_RISK_KEYWORDS = [
    ("benign", "Low"),
    ("mirai", "Critical"),
    ("backdoor", "Critical"),
    ("malware", "Critical"),
    ("bruteforce", "Critical"),
    ("brute", "Critical"),
    ("dictionary", "Critical"),
    ("sqlinjection", "Critical"),
    ("sql", "Critical"),
    ("xss", "Critical"),
    ("commandinjection", "Critical"),
    ("command", "Critical"),
    ("injection", "Critical"),
    ("hijack", "Critical"),
    ("uploading", "Critical"),
    ("ddos", "High"),
    ("dos", "High"),
    ("flood", "High"),
    ("fragmentation", "High"),
    ("spoofing", "High"),
    ("mitm", "High"),
    ("vulnerability", "High"),
    ("recon", "Medium"),
    ("scan", "Medium"),
    ("sweep", "Medium"),
    ("discovery", "Medium"),
    ("portscan", "Medium"),
]

_cache: dict = {}


def load_artifact(name: str):
    """Cached joblib loader. XGBoost is forced onto CPU for robust inference."""
    if name not in _cache:
        path = SAVED_MODELS_DIR / f"{name}.pkl"
        if not path.exists():
            raise FileNotFoundError(f"Saved artefact not found: {path}")
        obj = joblib.load(path)
        if name == "xgboost":
            # Model was trained with device='cuda'; force CPU so inference works
            # on any machine and avoids device-mismatch warnings on each call.
            try:
                obj.set_params(device="cpu")
                if hasattr(obj, "get_booster"):
                    obj.get_booster().set_param({"device": "cpu"})
            except Exception as e:
                log.debug(f"Could not force XGBoost to CPU: {e}")
        _cache[name] = obj
    return _cache[name]


# Backwards-compatible private alias used by some callers
_load = load_artifact


def get_risk_level(label: str) -> str:
    low = (label or "").lower()
    for keyword, risk in _RISK_KEYWORDS:
        if keyword in low:
            return risk
    return "Medium"


def list_available_models() -> list:
    """Return names of classifier models that have a saved .pkl file."""
    return [m for m in KNOWN_MODELS if (SAVED_MODELS_DIR / f"{m}.pkl").exists()]


def build_feature_row(input_features: dict) -> np.ndarray:
    """
    Align a feature dict to the trained feature columns, fill missing with 0,
    and apply the same outlier clipping used during training.

    Returns a 1-D float array (unscaled).
    """
    feature_columns = load_artifact("feature_columns")
    row = np.zeros(len(feature_columns), dtype=float)
    for i, col in enumerate(feature_columns):
        if col in input_features:
            try:
                row[i] = float(input_features[col])
            except (TypeError, ValueError):
                row[i] = 0.0

    clip_lower_path = SAVED_MODELS_DIR / "clip_lower.pkl"
    clip_upper_path = SAVED_MODELS_DIR / "clip_upper.pkl"
    if clip_lower_path.exists() and clip_upper_path.exists():
        row = np.clip(row, load_artifact("clip_lower"), load_artifact("clip_upper"))
    return row


def _prepare_input(model_name: str, row: np.ndarray) -> np.ndarray:
    """Scale (if required) and reshape a clipped row for a given model."""
    if model_name in NEEDS_SCALING:
        scaler = load_artifact("scaler")
        return scaler.transform(row.reshape(1, -1))
    return row.reshape(1, -1)


def predict_proba_full(model_name: str, row: np.ndarray) -> tuple:
    """
    Predict with one model and return (label, confidence, full_proba_vector).

    full_proba_vector is aligned to label_encoder.classes_ (length = n_classes),
    or None if the model exposes no probabilities.
    """
    model = load_artifact(model_name)
    le = load_artifact("label_encoder")
    X = _prepare_input(model_name, row)

    y_pred = int(model.predict(X)[0])
    label = le.inverse_transform([y_pred])[0]

    full = None
    confidence = 0.0
    if hasattr(model, "predict_proba"):
        try:
            proba = model.predict_proba(X)[0]
            classes = getattr(model, "classes_", np.arange(len(proba)))
            full = np.zeros(len(le.classes_), dtype=float)
            for cls_idx, p in zip(classes, proba):
                ci = int(cls_idx)
                if 0 <= ci < len(full):
                    full[ci] = float(p)
            confidence = float(np.max(proba))
        except Exception as e:
            log.debug(f"predict_proba failed for {model_name}: {e}")

    if confidence == 0.0 and hasattr(model, "decision_function"):
        try:
            df_val = model.decision_function(X)[0]
            if isinstance(df_val, np.ndarray):
                confidence = float(np.max(np.abs(df_val))) / (float(np.sum(np.abs(df_val))) + 1e-9)
            else:
                confidence = min(abs(float(df_val)), 1.0)
        except Exception:
            pass

    return label, round(confidence, 4), full


def predict_threat(input_features: dict, model_name: str = "random_forest") -> dict:
    """Single-model convenience prediction (used by /api/predict and prewarm)."""
    row = build_feature_row(input_features)
    label, confidence, _ = predict_proba_full(model_name, row)
    return {
        "predicted_label":  label,
        "confidence_score": confidence,
        "risk_level":       get_risk_level(label),
        "model_used":       model_name,
    }


if __name__ == "__main__":
    available = list_available_models()
    if not available:
        print("No saved models found. Run training first.")
    else:
        sample = {"flow_duration": 0.01, "Number": 5, "Rate": 500.0, "Tot sum": 300}
        for m in available:
            try:
                r = predict_threat(sample, model_name=m)
                print(f"[{m}] -> {r['predicted_label']} (conf={r['confidence_score']:.3f}, risk={r['risk_level']})")
            except Exception as e:
                print(f"[{m}] ERROR: {e}")
