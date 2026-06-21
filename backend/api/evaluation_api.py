"""
Evaluation API Blueprint — serves all research metrics to the frontend.

Endpoints (all under /api/evaluation/...):
  GET /api/evaluation/summary           full model comparison + metadata
  GET /api/evaluation/per-class         per-attack-class metrics from RF report
  GET /api/evaluation/confusion-matrix  confusion matrix PNG as base64
  GET /api/evaluation/experiment-log    training experiment metadata log
  GET /api/evaluation/latency           prediction latency per model
  GET /api/evaluation/trust-trend       rolling trust score samples
  GET /api/evaluation/export/csv        download model_comparison.csv
"""

import re
import base64
import datetime
import logging
from pathlib import Path

from flask import Blueprint, jsonify, send_file, make_response

log = logging.getLogger(__name__)

evaluation_bp = Blueprint("evaluation", __name__)

_BASE        = Path(__file__).resolve().parent.parent          # backend/
_REPORTS_DIR = _BASE / "ml_model" / "reports"
_MODELS_DIR  = _BASE / "ml_model" / "saved_models"

# Rolling trust-score samples stored by capture_manager (shared list)
_trust_samples: list[dict] = []


def register_trust_sample(score: float, entity_id: str = "default"):
    """Called by capture_manager on each analysed event."""
    _trust_samples.append({
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
        "score": round(score, 2),
        "entity": entity_id,
    })
    if len(_trust_samples) > 500:
        _trust_samples.pop(0)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _read_comparison_csv() -> list[dict]:
    csv_path = _REPORTS_DIR / "model_comparison.csv"
    if not csv_path.exists():
        return []
    import csv
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            r = {k: _coerce(v) for k, v in row.items()}
            # Normalise: evaluate_models.py writes "model_name", verify writes "model"
            if "model_name" in r and "model" not in r:
                r["model"] = r.pop("model_name")
            rows.append(r)
    return rows


def _parse_classification_report() -> list[dict]:
    """Parse sklearn classification_report.txt into per-class dicts."""
    path = _REPORTS_DIR / "classification_report.txt"
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8", errors="replace")
    classes = []

    for line in text.splitlines():
        line = line.strip()
        # Skip headers, separators, summary rows
        if not line or line.startswith("=") or line.startswith("Classification"):
            continue
        if any(kw in line for kw in ["accuracy", "macro avg", "weighted avg"]):
            continue

        # Match: <class_name>   <prec>   <recall>   <f1>   <support>
        m = re.match(
            r"^(.+?)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)$",
            line,
        )
        if m:
            name = m.group(1).strip()
            # Normalise encoding artefacts from CICIDS2017 labels
            name = name.encode("ascii", "ignore").decode().strip()
            name = re.sub(r'\s+', ' ', name)
            classes.append({
                "class":     name,
                "precision": float(m.group(2)),
                "recall":    float(m.group(3)),
                "f1":        float(m.group(4)),
                "support":   int(m.group(5)),
            })

    return classes


def _confusion_matrix_b64() -> str | None:
    path = _REPORTS_DIR / "confusion_matrix.png"
    if not path.exists():
        return None
    data = path.read_bytes()
    return base64.b64encode(data).decode()


def _experiment_metadata() -> dict:
    """Derive training metadata from saved artefact timestamps."""
    import joblib
    scaler_path = _MODELS_DIR / "scaler.pkl"
    trained_at  = None
    if scaler_path.exists():
        ts = scaler_path.stat().st_mtime
        trained_at = datetime.datetime.fromtimestamp(ts).isoformat()

    models_found = [
        m.stem for m in _MODELS_DIR.glob("*.pkl")
        if m.stem not in {"scaler", "label_encoder", "feature_columns", "clip_lower", "clip_upper"}
    ]

    feature_columns = []
    fc_path = _MODELS_DIR / "feature_columns.pkl"
    if fc_path.exists():
        feature_columns = joblib.load(fc_path)

    le_classes: list[str] = []
    le_path = _MODELS_DIR / "label_encoder.pkl"
    if le_path.exists():
        le = joblib.load(le_path)
        le_classes = list(le.classes_)

    return {
        "dataset":          "CICIDS2017",
        "split_strategy":   "Temporal (Mon-Thu train / Fri test)",
        "deduplication":    "Near-duplicate removal (3 sig. fig. rounding)",
        "outlier_clipping": "Per-feature 1st/99th percentile clip",
        "num_features":     len(feature_columns),
        "num_classes":      len(le_classes),
        "attack_classes":   le_classes,
        "models_trained":   models_found,
        "primary_model":    "random_forest",
        "trained_at":       trained_at,
        "framework":        "scikit-learn 1.9",
        "python_version":   "3.12",
        "evaluation_metric": "Weighted F1-score",
        "reference_paper":  "Developing a Multi-Level Protection Framework in Network Topologies",
    }


def _coerce(v: str):
    try: return int(v)
    except ValueError: pass
    try: return float(v)
    except ValueError: return v


# ── Routes ─────────────────────────────────────────────────────────────────────

@evaluation_bp.route("/api/evaluation/summary", methods=["GET"])
def evaluation_summary():
    rows = _read_comparison_csv()
    meta = _experiment_metadata()

    # Rank by macro_f1 (honest per-class metric) if available, else f1_score
    if rows and "macro_f1" in rows[0]:
        best = max(rows, key=lambda r: float(r.get("macro_f1", 0)))
    else:
        best = max(rows, key=lambda r: float(r.get("f1_score", 0))) if rows else None

    return jsonify({
        "models":               rows,
        "count":                len(rows),
        "best_model":           best["model"] if best else None,
        "best_f1":              best.get("f1_score") if best else None,
        "best_macro_f1":        best.get("macro_f1") if best else None,
        "best_attack_detect":   best.get("attack_detection_rate") if best else None,
        "best_accuracy":        best.get("accuracy") if best else None,
        "experiment":           meta,
        "reports_available": {
            "model_comparison":      (_REPORTS_DIR / "model_comparison.csv").exists(),
            "classification_report": (_REPORTS_DIR / "classification_report.txt").exists(),
            "confusion_matrix":      (_REPORTS_DIR / "confusion_matrix.png").exists(),
        },
        "metric_note": (
            "macro_f1 and attack_detection_rate are the primary correctness metrics. "
            "f1_score (weighted) inflates when BENIGN dominates the test set."
        ),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    })


@evaluation_bp.route("/api/evaluation/per-class", methods=["GET"])
def per_class_metrics():
    classes = _parse_classification_report()
    if not classes:
        return jsonify({
            "error": "classification_report.txt not found",
            "hint":  "Run python ml_model/train_models.py or python ml_model/verify_models.py",
            "classes": [],
        }), 404

    # Sort: attacks first (non-BENIGN), then BENIGN
    attacks = [c for c in classes if c["class"].upper() != "BENIGN"]
    benign  = [c for c in classes if c["class"].upper() == "BENIGN"]
    sorted_classes = sorted(attacks, key=lambda x: x["f1"], reverse=True) + benign

    attack_classes = [c for c in classes if c["class"].upper() != "BENIGN"]
    attack_detect_rate = (
        round(sum(c["recall"] for c in attack_classes) / len(attack_classes), 4)
        if attack_classes else 0
    )

    return jsonify({
        "primary_model":        "random_forest",
        "classes":              sorted_classes,
        "total_support":        sum(c["support"] for c in classes),
        "macro_f1":             round(sum(c["f1"] for c in classes) / len(classes), 4) if classes else 0,
        "attack_detection_rate": attack_detect_rate,
        "note": (
            "attack_detection_rate = mean recall over attack classes only. "
            "A model that predicts BENIGN for everything gets 0.0 here."
        ),
        "timestamp":            datetime.datetime.utcnow().isoformat() + "Z",
    })


@evaluation_bp.route("/api/evaluation/confusion-matrix", methods=["GET"])
def confusion_matrix_image():
    b64 = _confusion_matrix_b64()
    if b64 is None:
        return jsonify({
            "available": False,
            "hint": "Run python ml_model/verify_models.py to generate confusion_matrix.png",
        }), 404
    return jsonify({
        "available":    True,
        "image_base64": b64,
        "format":       "png",
        "model":        "random_forest",
        "timestamp":    datetime.datetime.utcnow().isoformat() + "Z",
    })


@evaluation_bp.route("/api/evaluation/latency", methods=["GET"])
def latency_breakdown():
    rows = _read_comparison_csv()
    data = []
    for r in rows:
        pred_ms = round(float(r.get("pred_time_s", 0)) * 1000, 3)
        data.append({
            "model":         r.get("model", ""),
            "pred_time_ms":  pred_ms,
            "pred_time_s":   r.get("pred_time_s", 0),
            "train_time_s":  r.get("train_time_s", 0),
            "realtime_ok":   pred_ms < 100,
        })
    data.sort(key=lambda x: x["pred_time_ms"])
    return jsonify({
        "latency": data,
        "fastest": data[0]["model"] if data else None,
        "slowest": data[-1]["model"] if data else None,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    })


@evaluation_bp.route("/api/evaluation/trust-trend", methods=["GET"])
def trust_trend():
    import math, random
    random.seed(0)
    if _trust_samples:
        return jsonify({"samples": _trust_samples[-120:], "source": "live"})

    # Deterministic demo trend — simulates trust erosion during an attack
    samples = []
    base = 91.0
    t = datetime.datetime.utcnow() - datetime.timedelta(minutes=60)
    for i in range(60):
        noise  = random.gauss(0, 2.5)
        attack = 25 * math.exp(-0.5 * ((i - 30) / 6) ** 2)
        score  = max(30, min(100, base + noise - attack))
        samples.append({
            "ts":     (t + datetime.timedelta(minutes=i)).isoformat() + "Z",
            "score":  round(score, 2),
            "entity": "demo",
        })
    return jsonify({"samples": samples, "source": "demo"})


@evaluation_bp.route("/api/evaluation/experiment-log", methods=["GET"])
def experiment_log():
    meta = _experiment_metadata()
    rows = _read_comparison_csv()

    entries = []
    for i, r in enumerate(sorted(rows, key=lambda x: float(x.get("f1_score", 0)), reverse=True)):
        entries.append({
            "run_id":       f"EXP-{i+1:03d}",
            "model":        r.get("model", ""),
            "split":        "Temporal Mon-Thu/Fri",
            "dedup":        "Yes (3 s.f.)",
            "clipping":     "1st/99th pct",
            "accuracy":     r.get("accuracy", 0),
            "precision":    r.get("precision", 0),
            "recall":       r.get("recall", 0),
            "f1_score":     r.get("f1_score", 0),
            "train_time_s": r.get("train_time_s", 0),
            "pred_time_ms": round(float(r.get("pred_time_s", 0)) * 1000, 2),
            "status":       "COMPLETED",
            "trained_at":   meta.get("trained_at", "—"),
        })

    return jsonify({
        "experiment_name": "Multi-Level Network Threat Detection",
        "paper_title":     meta["reference_paper"],
        "dataset":         "CICIDS2017 (CIC-IDS-2017)",
        "entries":         entries,
        "total":           len(entries),
        "timestamp":       datetime.datetime.utcnow().isoformat() + "Z",
    })


@evaluation_bp.route("/api/evaluation/export/csv", methods=["GET"])
def export_csv():
    csv_path = _REPORTS_DIR / "model_comparison.csv"
    if not csv_path.exists():
        return jsonify({"error": "CSV not found"}), 404
    response = make_response(csv_path.read_text(encoding="utf-8"))
    response.headers["Content-Type"]        = "text/csv"
    response.headers["Content-Disposition"] = "attachment; filename=model_comparison_cicids2017.csv"
    return response
