"""
CaptureManager — orchestrates live packet capture, ML inference, and event storage.

Key fixes vs. original:
- Uses tshark subprocess (not PyShark) via the new packet_sniffer.py
- Resolves interface name → numeric index before passing to tshark (-i 1, -i 2, ...)
- ML pipeline imported at module level — import errors are visible immediately
- Errors in _on_packet logged at WARNING (not DEBUG) so they appear in the console
- Pre-warms Random Forest on start() so the first packet isn't slow
"""

import datetime
import logging
import sys
import threading
import time
import uuid
from collections import deque
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

MAX_EVENTS = 500
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

# Pre-import ML pipeline at module load so errors surface immediately
try:
    from api.threat_detector import detect as _detect_fn
    from packet_capture.feature_extractor import extract_features as _extract_fn
    _ML_READY = True
    log.info("ML pipeline imports OK")
except Exception as _imp_err:
    _detect_fn = None   # type: ignore
    _extract_fn = None  # type: ignore
    _ML_READY = False
    log.error(f"ML pipeline import failed: {_imp_err}")


def _resolve_interface(name: str) -> str:
    """
    Given a user-selected interface name or index, return the tshark
    interface index (e.g. "1") for the most reliable -i argument on Windows.

    Falls back to the original string if no match is found.
    """
    # If already a numeric index, use as-is
    if name.strip().isdigit():
        return name.strip()

    try:
        from packet_capture.interface_utils import list_interfaces
        ifaces = list_interfaces()
        for iface in ifaces:
            if iface.get("name") == name or iface.get("device") == name:
                idx = iface.get("index", "")
                if idx:
                    return idx
    except Exception as e:
        log.warning(f"Interface lookup failed: {e}")

    # Return the original — tshark may accept friendly names on some systems
    return name


class CaptureManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._sniffer = None
        self._interface: Optional[str] = None          # resolved (index)
        self._interface_friendly: Optional[str] = None  # original name for display

        self._events: deque = deque(maxlen=MAX_EVENTS)
        self._packets_captured = 0   # IP packets that ran through the ML pipeline
        self._events_analyzed = 0    # events successfully added to the queue
        self._packets_failed = 0     # packets where ML pipeline threw an exception
        self._start_time: Optional[float] = None
        self._error: Optional[str] = None
        self._last_error: Optional[str] = None

    # ── Control ───────────────────────────────────────────────────────────────

    def start(self, interface: str) -> dict:
        if not _ML_READY:
            return {"ok": False, "error": "ML pipeline not ready — check server logs"}

        resolved = _resolve_interface(interface)
        log.info(f"Interface '{interface}' resolved to '{resolved}'")

        with self._lock:
            if self._running:
                return {"ok": False, "error": "Capture already running"}
            self._interface = resolved
            self._interface_friendly = interface
            self._error = None
            self._last_error = None
            self._packets_captured = 0
            self._events_analyzed = 0
            self._packets_failed = 0
            self._running = True
            self._start_time = time.time()

        # Pre-warm the Random Forest so first real packet isn't slow
        threading.Thread(target=self._prewarm, daemon=True, name="model-prewarm").start()

        self._thread = threading.Thread(target=self._run, daemon=True, name="packet-capture")
        self._thread.start()
        log.info(f"Capture started on '{interface}' (index={resolved})")
        return {"ok": True, "interface": interface, "resolved": resolved}

    def stop(self) -> dict:
        with self._lock:
            if not self._running:
                return {"ok": False, "error": "No capture running"}
            self._running = False
            if self._sniffer:
                self._sniffer.stop()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=4)

        log.info("Capture stopped")
        return {"ok": True}

    # ── Status ────────────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        from packet_capture.interface_utils import check_tshark_installed
        tshark_ok, tshark_info = check_tshark_installed()
        with self._lock:
            raw = getattr(self._sniffer, "raw_count", 0) if self._sniffer else 0
            return {
                "is_running": self._running,
                "selected_interface": self._interface_friendly or self._interface,
                "resolved_interface": self._interface,
                "packets_captured": self._packets_captured,
                "events_analyzed": self._events_analyzed,
                "packets_failed": self._packets_failed,
                "raw_packets_seen": raw,
                "tshark_available": tshark_ok,
                "tshark_path": tshark_info if tshark_ok else None,
                "tshark_error": tshark_info if not tshark_ok else None,
                "ml_ready": _ML_READY,
                "error": self._error,
                "last_packet_error": self._last_error,
                "uptime_seconds": (
                    int(time.time() - self._start_time)
                    if self._start_time and self._running else 0
                ),
            }

    def get_debug_info(self) -> dict:
        with self._lock:
            sample = list(self._events)[-3:] if self._events else []
            raw = getattr(self._sniffer, "raw_count", 0) if self._sniffer else 0
        return {
            "ml_ready": _ML_READY,
            "events_in_queue": len(list(self._events)),
            "packets_captured": self._packets_captured,
            "events_analyzed": self._events_analyzed,
            "packets_failed": self._packets_failed,
            "raw_packets_seen": raw,
            "last_error": self._last_error,
            "sample_events": sample,
        }

    # ── Data getters ──────────────────────────────────────────────────────────

    def get_events(self, limit: int = 50) -> list:
        with self._lock:
            events = list(self._events)
        return list(reversed(events))[:limit]

    def get_dashboard_stats(self) -> dict:
        with self._lock:
            events = list(self._events)
            packets = self._packets_captured

        if not events:
            return {
                "total_packets": packets,
                "active_flows": 0,
                "threats_detected": 0,
                "average_trust_score": 0.0,
                "blocked_connections": 0,
                "model_confidence": 0.0,
                "benign_count": 0,
                "attack_count": 0,
                "critical_count": 0,
                "high_risk_count": 0,
                "source": "live",
            }

        threats   = [e for e in events if e.get("predicted_label", "").upper() != "BENIGN"]
        blocked   = [e for e in events if e.get("action") in ("Block", "Quarantine")]
        criticals = [e for e in events if e.get("risk_level") == "Critical"]
        high_risk = [e for e in events if e.get("risk_level") in ("High", "Critical")]
        trust_scores = [float(e.get("trust_score", 100.0)) for e in events]
        confidences  = [float(e.get("confidence", 0.0)) for e in events]
        unique_srcs  = set(e.get("source_ip") for e in events if e.get("source_ip"))

        avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0.0
        avg_conf  = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            "total_packets": packets,
            "active_flows": len(unique_srcs),
            "threats_detected": len(threats),
            "average_trust_score": round(avg_trust / 100.0, 3),
            "blocked_connections": len(blocked),
            "model_confidence": round(avg_conf, 4),
            "benign_count": len(events) - len(threats),
            "attack_count": len(threats),
            "critical_count": len(criticals),
            "high_risk_count": len(high_risk),
            "source": "live",
        }

    def get_threat_distribution(self) -> list:
        with self._lock:
            events = list(self._events)
        if not events:
            return []
        counts: dict = {}
        for e in events:
            label = e.get("predicted_label") or "Unknown"
            counts[label] = counts.get(label, 0) + 1
        total = sum(counts.values())
        _COLORS = {
            "BENIGN": "#00ff9d", "DoS": "#ff2d55", "DDoS": "#bf5fff",
            "PortScan": "#00d4ff", "Botnet": "#ff8c42", "Web Attack": "#f87171",
            "Brute Force": "#ec4899", "Infiltration": "#a78bfa", "Heartbleed": "#c0392b",
        }
        def _color(lbl):
            for k, v in _COLORS.items():
                if k.lower() in lbl.lower():
                    return v
            return "#6b7280"
        return [
            {"name": lbl, "count": cnt, "percentage": round(cnt / total * 100, 1), "color": _color(lbl)}
            for lbl, cnt in sorted(counts.items(), key=lambda x: -x[1])
        ]

    def get_trust_summary(self) -> dict:
        with self._lock:
            events = list(self._events)
        if not events:
            return {"average_trust_score": 0.0, "high_trust_entities": 0,
                    "medium_trust_entities": 0, "low_trust_entities": 0, "entity_list": []}
        entity_data: dict = {}
        for e in events:
            src = e.get("source_ip")
            if src:
                entity_data[src] = e
        entity_list, trust_scores, high, medium, low = [], [], 0, 0, 0
        for ip, e in entity_data.items():
            ts_raw = float(e.get("trust_score", 100.0))
            ts = ts_raw / 100.0
            trust_scores.append(ts)
            if ts_raw >= 80:
                high += 1; status = "online"
            elif ts_raw >= 50:
                medium += 1; status = "alerted" if e.get("action") in ("Alert", "Restrict") else "online"
            else:
                low += 1; status = _action_to_entity_status(e.get("action", "Allow"))
            entity_list.append({
                "id": f"E-{ip.replace('.', '-')}",
                "name": ip, "ip": ip,
                "userTrust": round(float(e.get("user_trust", 100.0)) / 100.0, 3),
                "deviceTrust": round(float(e.get("device_trust", 100.0)) / 100.0, 3),
                "behaviorTrust": round(float(e.get("behavior_trust", 100.0)) / 100.0, 3),
                "finalTrust": round(ts, 3),
                "riskLevel": e.get("risk_level", "Low"),
                "status": status,
            })
        avg = sum(trust_scores) / len(trust_scores) if trust_scores else 0.0
        entity_list.sort(key=lambda x: x["finalTrust"])
        return {
            "average_trust_score": round(avg, 3),
            "high_trust_entities": high, "medium_trust_entities": medium, "low_trust_entities": low,
            "entity_list": entity_list[:20],
        }

    def get_recent_alerts(self, limit: int = 20) -> list:
        with self._lock:
            events = list(self._events)
        alerts = [
            e for e in reversed(events)
            if e.get("risk_level") in ("High", "Critical")
            or e.get("action") in ("Block", "Quarantine", "Alert")
        ][:limit]
        return [
            {
                "id": e.get("id", ""),
                "severity": _risk_to_severity(e.get("risk_level", "Low")),
                "message": (
                    e.get("reason")
                    or f"{e.get('predicted_label','Unknown')} from {e.get('source_ip','?')}"
                ),
                "time": e.get("timestamp", ""),
                "acked": False,
            }
            for e in alerts
        ]

    def get_traffic_trend(self) -> list:
        with self._lock:
            events = list(self._events)
        now = time.time()
        buckets: dict = {}
        for e in events:
            ts = e.get("timestamp_unix", now)
            mins_ago = int((now - ts) / 60)
            if mins_ago > 11:
                continue
            slot = 11 - mins_ago
            if slot not in buckets:
                buckets[slot] = {"normal": 0, "threats": 0, "packets": 0}
            if e.get("predicted_label", "").upper() == "BENIGN":
                buckets[slot]["normal"] += 1
            else:
                buckets[slot]["threats"] += 1
            buckets[slot]["packets"] += 1
        result = []
        for i in range(12):
            b = buckets.get(i, {"normal": 0, "threats": 0, "packets": 0})
            mins_ago = 11 - i
            result.append({
                "time": f"-{mins_ago}m" if mins_ago > 0 else "now",
                "normal": b["normal"],
                "threats": b["threats"],
                "packets": b["packets"],
            })
        return result

    def get_network_flows(self, limit: int = 25) -> list:
        events = self.get_events(limit)
        return [
            {
                "id": e.get("id", f"F-{i:05d}"),
                "srcIP": e.get("source_ip") or "?",
                "dstIP": e.get("dest_ip") or "?",
                "protocol": e.get("protocol") or "?",
                "packetCount": 1,
                "flowDuration": "00:00:01",
                "bytes": f"{e.get('packet_length', 0)} B",
                "status": _action_to_status(e.get("action", "Allow")),
                "attackType": e.get("predicted_label") or "BENIGN",
            }
            for i, e in enumerate(events)
        ]

    def get_topology(self) -> dict:
        """Return network topology: nodes (IPs) and edges (connections) from captured events."""
        with self._lock:
            events = list(self._events)
        if not events:
            return {"nodes": [], "edges": [], "total_events": 0}

        _RANK = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
        _RISK = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}
        node_data: dict = {}
        edge_data: dict = {}

        def _ensure_node(ip: str):
            if ip not in node_data:
                node_data[ip] = {
                    "id": ip, "packet_count": 0, "threat_count": 0,
                    "trust_sum": 0.0, "trust_n": 0,
                    "risk_rank": 0, "protocols": set(), "actions": set(),
                }

        for e in events:
            src = e.get("source_ip")
            dst = e.get("dest_ip")
            proto = e.get("protocol") or "UNKNOWN"
            risk = e.get("risk_level", "Low")
            trust = float(e.get("trust_score", 100.0))
            pkt_len = int(e.get("packet_length") or 0)
            label = (e.get("predicted_label") or "BENIGN").upper()
            action = e.get("action", "Allow")
            is_threat = label not in ("BENIGN", "")

            if src:
                _ensure_node(src)
                nd = node_data[src]
                nd["packet_count"] += 1
                nd["trust_sum"] += trust
                nd["trust_n"] += 1
                nd["protocols"].add(proto)
                nd["actions"].add(action)
                if is_threat:
                    nd["threat_count"] += 1
                r = _RANK.get(risk, 0)
                if r > nd["risk_rank"]:
                    nd["risk_rank"] = r

            if dst:
                _ensure_node(dst)
                node_data[dst]["packet_count"] += 1
                node_data[dst]["protocols"].add(proto)

            if src and dst:
                key = f"{src}|{dst}"
                if key not in edge_data:
                    edge_data[key] = {
                        "source": src, "target": dst,
                        "count": 0, "protocols": set(),
                        "bytes": 0, "has_threat": False,
                    }
                ed = edge_data[key]
                ed["count"] += 1
                ed["protocols"].add(proto)
                ed["bytes"] += pkt_len
                if is_threat:
                    ed["has_threat"] = True

        nodes = []
        for ip, nd in node_data.items():
            avg_trust = nd["trust_sum"] / nd["trust_n"] if nd["trust_n"] > 0 else 100.0
            nodes.append({
                "id": ip,
                "packet_count": nd["packet_count"],
                "threat_count": nd["threat_count"],
                "trust_score": round(avg_trust, 1),
                "risk_level": _RISK[nd["risk_rank"]],
                "protocols": list(nd["protocols"])[:5],
                "actions": list(nd["actions"])[:3],
                "is_local": _is_private_ip(ip),
            })

        nodes.sort(key=lambda x: (-int(x["is_local"]), -x["packet_count"]))

        edges = [
            {
                "source": ed["source"], "target": ed["target"],
                "count": ed["count"],
                "protocols": list(ed["protocols"])[:3],
                "bytes": ed["bytes"],
                "has_threat": ed["has_threat"],
            }
            for ed in sorted(edge_data.values(), key=lambda x: -x["count"])
        ]

        return {
            "nodes": nodes[:60],
            "edges": edges[:120],
            "total_events": len(events),
        }

    def get_security_decisions(self) -> dict:
        with self._lock:
            events = list(self._events)
        counts = {"allow": 0, "restrict": 0, "alert": 0, "quarantine": 0, "block": 0}
        for e in events:
            action = (e.get("action") or "Allow").lower()
            if action in counts:
                counts[action] += 1
        total = sum(counts.values()) or 1
        return {
            key: {"count": val, "percentage": round(val / total * 100, 1)}
            for key, val in counts.items()
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _prewarm(self):
        """Load the Random Forest model into memory before capture starts."""
        try:
            from ml_model.predict import predict_threat
            predict_threat({"Destination Port": 80, "Total Fwd Packets": 1}, "random_forest")
            log.info("Random Forest model pre-warmed OK")
        except Exception as e:
            log.warning(f"Model pre-warm failed (will load on first packet): {e}")

    def _run(self):
        from packet_capture.packet_sniffer import PacketSniffer
        self._sniffer = PacketSniffer(
            interface=self._interface,
            packet_callback=self._on_packet,
        )
        self._sniffer.start()

        # Capture stopped — check if the sniffer recorded an error
        if self._sniffer.error:
            with self._lock:
                self._error = self._sniffer.error
                self._running = False
            log.error(f"Sniffer stopped with error: {self._sniffer.error}")
        else:
            with self._lock:
                self._running = False

    def _on_packet(self, packet_info: dict):
        """Process one captured IP packet through the full ML pipeline."""
        step = "init"
        try:
            if not _ML_READY:
                raise RuntimeError("ML pipeline not loaded")

            step = "feature_extraction"
            features = _extract_fn(packet_info)

            step = "ml_detection"
            result = _detect_fn(
                flow_features=features,
                model_name="random_forest",
                entity_id=str(packet_info.get("src_ip") or "unknown"),
            )

            step = "build_event"
            event = {
                "id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp_unix": float(packet_info.get("timestamp") or time.time()),
                "source_ip": packet_info.get("src_ip"),
                "dest_ip": packet_info.get("dst_ip"),
                "source_port": packet_info.get("src_port"),
                "dest_port": packet_info.get("dst_port"),
                "protocol": packet_info.get("protocol", "UNKNOWN"),
                "packet_length": int(packet_info.get("packet_length") or 0),
                "predicted_label": str(result.get("predicted_label", "Unknown")),
                "confidence": float(result.get("confidence_score", 0.0)),
                "risk_level": str(result.get("risk_level", "Low")),
                "trust_score": float(result.get("trust_score", 100.0)),
                "trust_level": str(result.get("trust_level", "High Trust")),
                "user_trust": float(result.get("user_trust", 100.0)),
                "device_trust": float(result.get("device_trust", 100.0)),
                "behavior_trust": float(result.get("behavior_trust", 100.0)),
                "action": str(result.get("action", "Allow")),
                "reason": str(result.get("reason", "")),
                "policy_level": str(result.get("policy_level", "INFO")),
                "severity": _risk_to_severity(str(result.get("risk_level", "Low"))),
            }

            step = "store"
            with self._lock:
                self._events.append(event)
                self._packets_captured += 1
                self._events_analyzed += 1

        except Exception as exc:
            with self._lock:
                self._packets_captured += 1
                self._packets_failed += 1
                self._last_error = f"[{step}] {type(exc).__name__}: {exc}"
            log.warning(f"Packet analysis failed at step '{step}': {exc}")


# ── Singleton ──────────────────────────────────────────────────────────────────

_manager = CaptureManager()


def get_manager() -> CaptureManager:
    return _manager


# ── Helpers ───────────────────────────────────────────────────────────────────

def _risk_to_severity(risk: str) -> str:
    return {"Low": "low", "Medium": "medium", "High": "high", "Critical": "critical"}.get(risk, "low")

def _action_to_status(action: str) -> str:
    return {"Allow": "allowed", "Restrict": "restricted", "Alert": "alerted",
            "Quarantine": "quarantined", "Block": "blocked"}.get(action, "allowed")

def _action_to_entity_status(action: str) -> str:
    return {"Allow": "online", "Restrict": "online", "Alert": "alerted",
            "Quarantine": "quarantined", "Block": "blocked"}.get(action, "online")

def _is_private_ip(ip: str) -> bool:
    import ipaddress
    try:
        clean = ip.split("%")[0]
        addr = ipaddress.ip_address(clean)
        return bool(addr.is_private or addr.is_link_local or addr.is_loopback)
    except ValueError:
        return False
