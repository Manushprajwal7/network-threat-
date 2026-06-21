"""
Flask API — Network Threat Detection Backend

Endpoints:
    GET  /                        → Service status
    GET  /health                  → Health check with model availability
    POST /api/predict             → Predict threat for manual flow features
    GET  /api/model-comparison    → Model comparison CSV as JSON
    GET  /api/interfaces          → Available capture interfaces
    POST /api/capture/start       → Start live packet capture
    POST /api/capture/stop        → Stop live packet capture
    GET  /api/capture/status      → Capture status
    GET  /api/live-events         → Latest analysed packet events
    GET  /api/dashboard-stats     → Real-time KPI stats
    GET  /api/threat-distribution → Attack class distribution
    GET  /api/trust-summary       → Per-entity trust breakdown
    GET  /api/recent-alerts       → Recent high-risk alerts
    GET  /api/traffic-trend       → Rolling 12-minute traffic trend
    GET  /api/network-flows       → Latest flows for Network Monitor panel
    GET  /api/security-decisions  → Decision engine action counts
"""

import logging
import datetime
import warnings
import sys
from pathlib import Path

# Suppress sklearn's internal joblib/parallel compatibility warning that fires
# during Random Forest inference — it is an sklearn-internal issue, not ours.
warnings.filterwarnings(
    "ignore",
    message=r".*sklearn\.utils\.parallel\.delayed.*",
    category=UserWarning,
    module=r"sklearn\.utils\.parallel",
)

from flask import Flask, jsonify, request
from flask_cors import CORS

# ── Path bootstrap ────────────────────────────────────────────────────────────
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from ml_model.predict import list_available_models
from api.threat_detector import detect
from api.evaluation_api import evaluation_bp
from api.blocking_manager import get_blocking_manager
from api.simulation_manager import get_simulation_manager, SIM_TYPES
from api.research_api import research_bp
from packet_capture.capture_manager import get_manager
from packet_capture.interface_utils import list_interfaces, check_tshark_installed, get_default_interface_index

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)
app.register_blueprint(evaluation_bp)
app.register_blueprint(research_bp)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

REPORTS_DIR = _backend_dir / "ml_model" / "reports"


# ── Status / Health ───────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "Network Threat Detection — ML Backend",
        "version": "2.0.0",
        "status":  "running",
    })


@app.route("/health", methods=["GET"])
def health():
    available = list_available_models()
    tshark_ok, tshark_info = check_tshark_installed()
    return jsonify({
        "backend":          "running",
        "models_loaded":    len(available) > 0,
        "available_models": available,
        "primary_model":    "random_forest" if "random_forest" in available else (available[0] if available else None),
        "tshark_available": tshark_ok,
        "tshark_info":      tshark_info,
        "timestamp":        _now(),
    })


# ── Manual prediction (kept for direct API use) ───────────────────────────────

@app.route("/api/predict", methods=["POST"])
def predict():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be JSON"}), 400

    features   = body.get("features", {})
    model_name = body.get("model", "random_forest")
    entity_id  = body.get("entity_id", "default")

    if not features:
        return jsonify({"error": "No features provided"}), 400

    try:
        result = detect(flow_features=features, model_name=model_name, entity_id=entity_id)
        return jsonify({
            "prediction":   result["predicted_label"],
            "confidence":   result["confidence_score"],
            "risk_level":   result["risk_level"],
            "trust_score":  result["trust_score"],
            "trust_level":  result["trust_level"],
            "action":       result["action"],
            "reason":       result["reason"],
            "policy_level": result["policy_level"],
            "model_used":   result["model_used"],
            "timestamp":    _now(),
        })
    except RuntimeError as e:
        return jsonify({"error": str(e), "hint": "Run python ml_model/train_models.py first"}), 503
    except Exception as e:
        log.exception("Prediction error")
        return jsonify({"error": str(e)}), 500


@app.route("/api/model-comparison", methods=["GET"])
def model_comparison():
    import csv
    csv_path = REPORTS_DIR / "model_comparison.csv"
    if not csv_path.exists():
        return jsonify({
            "error": "model_comparison.csv not found",
            "hint":  "Run python ml_model/train_models.py to generate it",
        }), 404
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append({k: _coerce_numeric(v) for k, v in row.items()})
    return jsonify({"models": rows, "count": len(rows), "timestamp": _now()})


# ── Interface discovery ───────────────────────────────────────────────────────

@app.route("/api/interfaces", methods=["GET"])
def interfaces():
    """Return available network interfaces detected by tshark."""
    tshark_ok, tshark_info = check_tshark_installed()
    if not tshark_ok:
        return jsonify({
            "interfaces": [],
            "tshark_available": False,
            "error": tshark_info,
        })
    ifaces = list_interfaces()
    default_idx = get_default_interface_index()
    return jsonify({
        "interfaces": ifaces,
        "tshark_available": True,
        "tshark_path": tshark_info,
        "default_index": default_idx,
        "count": len(ifaces),
    })


# ── Capture control ───────────────────────────────────────────────────────────

@app.route("/api/capture/start", methods=["POST"])
def capture_start():
    """
    Start live packet capture on a given interface.
    Body: { "interface": "Wi-Fi" }
    """
    body = request.get_json(silent=True) or {}
    interface = body.get("interface", "").strip()
    if not interface:
        return jsonify({"error": "interface name is required"}), 400

    result = get_manager().start(interface)
    if not result["ok"]:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/capture/stop", methods=["POST"])
def capture_stop():
    """Stop live packet capture."""
    result = get_manager().stop()
    if not result["ok"]:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/capture/status", methods=["GET"])
def capture_status():
    """Return current capture status and counters."""
    return jsonify(get_manager().get_status())


# ── Live data feeds ───────────────────────────────────────────────────────────

@app.route("/api/live-events", methods=["GET"])
def live_events():
    """Return the most recent analysed packet events (default: last 50)."""
    limit = min(int(request.args.get("limit", 50)), 200)
    events = get_manager().get_events(limit)
    return jsonify({
        "events": events,
        "count": len(events),
        "timestamp": _now(),
    })


@app.route("/api/dashboard-stats", methods=["GET"])
def dashboard_stats():
    """Return real-time aggregate KPI stats from analysed events."""
    stats = get_manager().get_dashboard_stats()
    stats["timestamp"] = _now()
    return jsonify(stats)


@app.route("/api/threat-distribution", methods=["GET"])
def threat_distribution():
    """Return attack-class distribution across all analysed events."""
    dist = get_manager().get_threat_distribution()
    return jsonify({
        "distribution": dist,
        "total_events": sum(d["count"] for d in dist),
        "timestamp": _now(),
    })


@app.route("/api/trust-summary", methods=["GET"])
def trust_summary():
    """Return per-entity trust scores and aggregate trust stats."""
    summary = get_manager().get_trust_summary()
    summary["timestamp"] = _now()
    return jsonify(summary)


@app.route("/api/recent-alerts", methods=["GET"])
def recent_alerts():
    """Return recent high-risk or blocked events as alerts."""
    limit = min(int(request.args.get("limit", 20)), 50)
    alerts = get_manager().get_recent_alerts(limit)
    return jsonify({
        "alerts": alerts,
        "count": len(alerts),
        "timestamp": _now(),
    })


@app.route("/api/traffic-trend", methods=["GET"])
def traffic_trend():
    """Return rolling 12-minute traffic trend data for the area chart."""
    trend = get_manager().get_traffic_trend()
    return jsonify({
        "trend": trend,
        "timestamp": _now(),
    })


@app.route("/api/network-flows", methods=["GET"])
def network_flows():
    """Return recent events formatted as network flows for the flow monitor."""
    limit = min(int(request.args.get("limit", 25)), 100)
    flows = get_manager().get_network_flows(limit)
    return jsonify({
        "flows": flows,
        "count": len(flows),
        "timestamp": _now(),
    })


@app.route("/api/security-decisions", methods=["GET"])
def security_decisions():
    """Return decision engine action counts."""
    decisions = get_manager().get_security_decisions()
    return jsonify({
        "decisions": decisions,
        "timestamp": _now(),
    })


@app.route("/api/topology", methods=["GET"])
def topology():
    """Return network topology (nodes + edges) derived from captured events."""
    data = get_manager().get_topology()
    data["timestamp"] = _now()
    return jsonify(data)


@app.route("/api/debug", methods=["GET"])
def debug():
    """Return capture manager internal state for diagnosing data pipeline issues."""
    info = get_manager().get_debug_info()
    info["timestamp"] = _now()
    return jsonify(info)


# ── Simulation endpoints ──────────────────────────────────────────────────────

@app.route("/api/simulation/start", methods=["POST"])
def simulation_start():
    """
    Start a controlled local attack simulation.
    Body: { "type": "dos"|"portscan"|"bruteforce"|"botnet"|"unknown",
            "duration_seconds": 30 }
    """
    body        = request.get_json(silent=True) or {}
    sim_type    = body.get("type", "").strip()
    duration    = int(body.get("duration_seconds", 30))

    if not sim_type:
        return jsonify({"error": "simulation type required"}), 400

    result = get_simulation_manager().start(sim_type, duration)
    if not result["ok"]:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/simulation/stop", methods=["POST"])
def simulation_stop():
    """Stop the currently running simulation."""
    result = get_simulation_manager().stop()
    if not result["ok"]:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/simulation/status", methods=["GET"])
def simulation_status():
    """Return current simulation status."""
    return jsonify({**get_simulation_manager().get_status(), "timestamp": _now()})


@app.route("/api/simulation/events", methods=["GET"])
def simulation_events():
    """Return recent simulation-generated events."""
    limit  = min(int(request.args.get("limit", 50)), 200)
    events = get_simulation_manager().get_events(limit)

    # Run each event through the ML pipeline if models are loaded
    enriched = []
    for evt in events:
        enriched_evt = dict(evt)
        try:
            if evt.get("sim_type") == "unknown":
                enriched_evt["known_or_unknown"]  = "Unknown"
                enriched_evt["predicted_attack"]  = "Unknown/Suspicious"
                enriched_evt["confidence"]        = round(0.2 + 0.2 * __import__("random").random(), 3)
                enriched_evt["anomaly_score"]     = round(0.75 + 0.2 * __import__("random").random(), 3)
                enriched_evt["trust_score"]       = int(20 + 20 * __import__("random").random())
                enriched_evt["security_action"]   = "Quarantine"
            else:
                feat   = _sim_event_to_features(evt)
                result = detect(flow_features=feat,
                                model_name="random_forest",
                                entity_id=evt.get("source_ip", SAFE_TARGET_PLACEHOLDER))
                enriched_evt["predicted_attack"]  = result["predicted_label"]
                enriched_evt["confidence"]        = result["confidence_score"]
                enriched_evt["risk_level"]        = result["risk_level"]
                enriched_evt["trust_score"]       = result["trust_score"]
                enriched_evt["trust_level"]       = result["trust_level"]
                enriched_evt["security_action"]   = result["action"]
                enriched_evt["known_or_unknown"]  = "Known"
                enriched_evt["anomaly_score"]     = 0.0
        except Exception as e:
            log.debug(f"Sim event enrichment skipped: {e}")
        enriched.append(enriched_evt)

    return jsonify({"events": enriched, "count": len(enriched), "timestamp": _now()})


SAFE_TARGET_PLACEHOLDER = "127.0.0.1"


def _sim_event_to_features(evt: dict) -> dict:
    """Convert a simulation event dict to a feature dict for ML prediction."""
    return {
        "Flow Duration":              evt.get("flow_duration", 1000),
        "Total Fwd Packets":          evt.get("total_fwd_packets", 5),
        "Total Backward Packets":     evt.get("total_backward_packets", 2),
        "Flow Bytes/s":               evt.get("flow_bytes_s", 1000.0),
        "Flow Packets/s":             evt.get("flow_packets_s", 5.0),
        "SYN Flag Count":             evt.get("syn_flag_count", 0),
        "ACK Flag Count":             evt.get("ack_flag_count", 0),
        "RST Flag Count":             evt.get("rst_flag_count", 0),
        "FIN Flag Count":             evt.get("fin_flag_count", 0),
        "PSH Flag Count":             evt.get("psh_flag_count", 0),
        "Packet Length Mean":         evt.get("packet_length_mean", 60.0),
        "Average Packet Size":        evt.get("packet_length_mean", 60.0),
    }


# ── Blocking endpoints ────────────────────────────────────────────────────────

@app.route("/api/blocked-entities", methods=["GET"])
def blocked_entities():
    """Return list of currently blocked IPs/entities."""
    entities = get_blocking_manager().get_blocked_list()
    return jsonify({
        "entities":    entities,
        "count":       len(entities),
        "mode":        "simulation",
        "timestamp":   _now(),
    })


@app.route("/api/block", methods=["POST"])
def block_entity():
    """
    Block an IP address (simulation mode by default).
    Body: { "ip": "127.0.0.1", "reason": "..." }
    """
    body   = request.get_json(silent=True) or {}
    ip     = body.get("ip", "").strip()
    reason = body.get("reason", "Manual block via API")

    if not ip:
        return jsonify({"error": "ip is required"}), 400

    result = get_blocking_manager().block(ip, reason=reason)
    if not result["ok"]:
        return jsonify(result), 400
    result["timestamp"] = _now()
    return jsonify(result)


@app.route("/api/unblock", methods=["POST"])
def unblock_entity():
    """
    Unblock an IP address.
    Body: { "ip": "127.0.0.1" }
    """
    body = request.get_json(silent=True) or {}
    ip   = body.get("ip", "").strip()

    if not ip:
        return jsonify({"error": "ip is required"}), 400

    result = get_blocking_manager().unblock(ip)
    if not result["ok"]:
        return jsonify(result), 400
    result["timestamp"] = _now()
    return jsonify(result)


@app.route("/api/block-history", methods=["GET"])
def block_history():
    """Return audit log of block/unblock actions."""
    limit   = min(int(request.args.get("limit", 50)), 200)
    history = get_blocking_manager().get_history(limit)
    return jsonify({"history": history, "count": len(history), "timestamp": _now()})


# ── Research report export ────────────────────────────────────────────────────

@app.route("/api/research-report", methods=["GET"])
def research_report():
    """
    Return a comprehensive research report combining:
    - Model comparison metrics
    - Per-class detection performance
    - Simulation summary
    - Trust score behavior
    - Blocking action summary
    """
    import csv
    report = {
        "title":   "Topology-Aware Multi-Level Protection Framework — Research Report",
        "dataset": "CICIDS2017",
        "timestamp": _now(),
    }

    # Model metrics
    for csv_name in ["model_comparison_research.csv", "model_comparison.csv"]:
        csv_path = REPORTS_DIR / csv_name
        if csv_path.exists():
            rows = []
            with open(csv_path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    rows.append({k: _coerce_numeric(v) for k, v in row.items()})
            report["model_comparison"] = rows
            break

    # Per-class metrics
    pc_path = REPORTS_DIR / "per_class_metrics.csv"
    if pc_path.exists():
        rows = []
        with open(pc_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rows.append({k: _coerce_numeric(v) for k, v in row.items()})
        report["per_class_metrics"] = rows

    # Research summary text
    summary_path = REPORTS_DIR / "research_summary.txt"
    if summary_path.exists():
        report["research_summary"] = summary_path.read_text(encoding="utf-8")

    # Leakage report
    leakage_path = REPORTS_DIR / "leakage_report.txt"
    if leakage_path.exists():
        report["leakage_report"] = leakage_path.read_text(encoding="utf-8")

    # Simulation summary
    sim_status = get_simulation_manager().get_status()
    report["simulation"] = sim_status

    # Blocking summary
    blocked = get_blocking_manager().get_blocked_list()
    report["blocking"] = {
        "total_blocked": len(blocked),
        "mode": "simulation",
        "entities": blocked,
    }

    # Trust summary from live capture
    report["trust_summary"] = get_manager().get_trust_summary()

    return jsonify(report)


@app.route("/api/research-report/csv", methods=["GET"])
def research_report_csv():
    """Return model comparison as CSV download."""
    from flask import Response
    for csv_name in ["model_comparison_research.csv", "model_comparison.csv"]:
        csv_path = REPORTS_DIR / csv_name
        if csv_path.exists():
            return Response(
                csv_path.read_text(encoding="utf-8"),
                mimetype="text/csv",
                headers={"Content-Disposition": f"attachment; filename={csv_name}"},
            )
    return jsonify({"error": "No model comparison CSV found. Run training first."}), 404


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"


def _coerce_numeric(value: str):
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("Starting Network Threat Detection API on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
