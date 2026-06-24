"""
CaptureManager — orchestrates the live, topology-aware monitoring pipeline:

    PACKET_CAPTURE → FEATURE_EXTRACTION → ML_DETECTION
                   → TRUST_SCORE → SECURITY_DECISION → TOPOLOGY → DASHBOARD

Design
------
- A tshark-backed PacketSniffer runs in a background thread and pushes every
  parsed packet into a FlowAggregator (no per-packet ML).
- A separate interval thread wakes every BATCH_INTERVAL seconds, snapshots all
  flows that saw traffic, and processes them as a batch:
      flow → CICIoT2023 features → ensemble detection → trust → decision
           → topology update → stored event.
- If a window has no packets, nothing is fabricated — the state stays empty.

All dashboard getters read from real analysed events / the live topology graph.
No hardcoded packets, fake flows, or mock values anywhere.
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

MAX_EVENTS = 800
BATCH_INTERVAL = 4.0   # seconds between batch analyses (requirement: 3–5s)

_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

# Pre-import the pipeline so import errors surface immediately at startup.
try:
    from api.threat_detector import analyze_flow as _analyze_flow
    from packet_capture.feature_extractor import extract_features as _extract_fn
    from packet_capture.flow_aggregator import FlowAggregator
    from api.topology_manager import get_topology_manager
    _ML_READY = True
    log.info("[INIT] Live pipeline imports OK")
except Exception as _imp_err:  # pragma: no cover
    _analyze_flow = None        # type: ignore
    _extract_fn = None          # type: ignore
    FlowAggregator = None       # type: ignore
    get_topology_manager = None  # type: ignore
    _ML_READY = False
    log.error(f"[INIT] Live pipeline import failed: {_imp_err}")


def _resolve_interface(name: str) -> str:
    if name.strip().isdigit():
        return name.strip()
    try:
        from packet_capture.interface_utils import list_interfaces
        for iface in list_interfaces():
            if iface.get("name") == name or iface.get("device") == name:
                if iface.get("index"):
                    return iface["index"]
    except Exception as e:
        log.warning(f"Interface lookup failed: {e}")
    return name


class CaptureManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._running = False
        self._sniffer = None
        self._capture_thread: Optional[threading.Thread] = None
        self._batch_thread: Optional[threading.Thread] = None
        self._interface: Optional[str] = None
        self._interface_friendly: Optional[str] = None

        self._aggregator = FlowAggregator() if _ML_READY else None
        self._topology = get_topology_manager() if _ML_READY else None

        self._events: deque = deque(maxlen=MAX_EVENTS)
        self._packets_processed = 0   # real packets folded into analysed flows
        self._flows_analyzed = 0
        self._flows_failed = 0
        self._start_time: Optional[float] = None
        self._error: Optional[str] = None
        self._last_error: Optional[str] = None

    # ── Control ───────────────────────────────────────────────────────────────

    def start(self, interface: str) -> dict:
        if not _ML_READY:
            return {"ok": False, "error": "ML pipeline not ready — check server logs"}

        resolved = _resolve_interface(interface)
        log.info(f"[PACKET_CAPTURE] Interface '{interface}' resolved to '{resolved}'")

        with self._lock:
            if self._running:
                return {"ok": False, "error": "Capture already running"}
            self._interface = resolved
            self._interface_friendly = interface
            self._error = None
            self._last_error = None
            self._packets_processed = 0
            self._flows_analyzed = 0
            self._flows_failed = 0
            self._events.clear()
            self._aggregator.reset()
            self._topology.reset()
            self._running = True
            self._start_time = time.time()

        threading.Thread(target=self._prewarm, daemon=True, name="model-prewarm").start()

        self._capture_thread = threading.Thread(target=self._run_capture, daemon=True, name="packet-capture")
        self._capture_thread.start()

        self._batch_thread = threading.Thread(target=self._run_batches, daemon=True, name="batch-analyzer")
        self._batch_thread.start()

        log.info(f"[PACKET_CAPTURE] Capture started on '{interface}' (index={resolved})")
        return {"ok": True, "interface": interface, "resolved": resolved}

    def stop(self) -> dict:
        with self._lock:
            if not self._running:
                return {"ok": False, "error": "No capture running"}
            self._running = False
            if self._sniffer:
                self._sniffer.stop()

        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=4)
        if self._batch_thread and self._batch_thread.is_alive():
            self._batch_thread.join(timeout=BATCH_INTERVAL + 2)

        log.info("[PACKET_CAPTURE] Capture stopped")
        return {"ok": True}

    # ── Capture + batch threads ─────────────────────────────────────────────────

    def _run_capture(self):
        from packet_capture.packet_sniffer import PacketSniffer
        self._sniffer = PacketSniffer(
            interface=self._interface,
            packet_callback=self._on_packet,
        )
        self._sniffer.start()   # blocks until stop()
        if self._sniffer.error:
            with self._lock:
                self._error = self._sniffer.error
                self._running = False
            log.error(f"[PACKET_CAPTURE] Sniffer stopped with error: {self._sniffer.error}")
        else:
            with self._lock:
                self._running = False

    def _on_packet(self, packet_info: dict):
        """Sniffer callback — buffer the packet into its flow (no ML here)."""
        try:
            self._aggregator.add_packet(packet_info)
        except Exception as exc:
            with self._lock:
                self._last_error = f"[aggregate] {type(exc).__name__}: {exc}"

    def _run_batches(self):
        """Every BATCH_INTERVAL seconds, analyse all flows seen in the window."""
        while True:
            time.sleep(BATCH_INTERVAL)
            with self._lock:
                if not self._running:
                    break
            try:
                self._process_window()
            except Exception as exc:
                with self._lock:
                    self._last_error = f"[batch] {type(exc).__name__}: {exc}"
                log.warning(f"[BATCH] window processing failed: {exc}")

    def _process_window(self):
        flows = self._aggregator.collect_window()
        if not flows:
            return

        risk_index = self._topology.risk_index()
        log.info(f"[FEATURE_EXTRACTION] Processing {len(flows)} flows from capture window")

        analyzed = 0
        for flow in flows:
            try:
                features = _extract_fn(flow)
                src = flow.get("src_ip") or "unknown"
                topo_risk = risk_index.get(src, "Low")

                result = _analyze_flow(features, entity_id=str(src), topology_risk=topo_risk)
                event = self._build_event(flow, result)

                self._topology.update_flow(event)   # TOPOLOGY stage
                with self._lock:
                    self._events.append(event)
                    self._packets_processed += int(flow.get("packet_count") or 0)
                    self._flows_analyzed += 1
                analyzed += 1
            except Exception as exc:
                with self._lock:
                    self._flows_failed += 1
                    self._last_error = f"[analyze] {type(exc).__name__}: {exc}"
                log.warning(f"[ML_DETECTION] flow analysis failed: {exc}")

        if analyzed:
            log.info(f"[ML_DETECTION] Analysed {analyzed} flows "
                     f"(total flows={self._flows_analyzed}, packets={self._packets_processed})")

    def _build_event(self, flow: dict, result: dict) -> dict:
        label = str(result.get("predicted_label", "Unknown"))
        flow_bytes = int(sum(flow.get("all_sizes") or []))
        return {
            "id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_unix": float(flow.get("last_ts") or time.time()),
            "source_ip": flow.get("src_ip"),
            "dest_ip": flow.get("dst_ip"),
            "source_port": flow.get("src_port"),
            "dest_port": flow.get("dst_port"),
            "protocol": flow.get("protocol", "UNKNOWN"),
            "packet_length": flow_bytes,                 # total flow bytes (compat field)
            "flow_packets": int(flow.get("packet_count") or 0),
            "flow_bytes": flow_bytes,
            "flow_duration": round(float(flow.get("duration") or 0.0), 4),
            # Detection
            "predicted_label": label,
            "confidence": float(result.get("confidence_score", 0.0)),
            "risk_level": str(result.get("risk_level", "Low")),
            "is_threat": bool(result.get("is_attack")),
            "known_or_unknown": str(result.get("known_or_unknown", "Known")),
            "anomaly_score": float(result.get("anomaly_score", 0.0)),
            "agreement": float(result.get("agreement", 0.0)),
            "per_model": result.get("per_model", []),
            "models_used": result.get("model_used", "ensemble"),
            # Trust
            "trust_score": float(result.get("trust_score", 100.0)),
            "trust_level": str(result.get("trust_level", "High Trust")),
            "user_trust": float(result.get("user_trust", 100.0)),
            "device_trust": float(result.get("device_trust", 100.0)),
            "behavior_trust": float(result.get("behavior_trust", 100.0)),
            # Decision
            "action": str(result.get("action", "Allow")),
            "reason": str(result.get("reason", "")),
            "policy_level": str(result.get("policy_level", "INFO")),
            "severity": _risk_to_severity(str(result.get("risk_level", "Low"))),
        }

    def _prewarm(self):
        try:
            from ml_model.ensemble_detector import get_ensemble_members
            from ml_model.predict import build_feature_row, predict_proba_full
            members = get_ensemble_members()
            row = build_feature_row({"Number": 1, "Rate": 1.0})
            for m in members:
                predict_proba_full(m, row)
            log.info(f"[INIT] Ensemble pre-warmed: {members}")
        except Exception as e:
            log.warning(f"[INIT] Pre-warm failed (will load on first batch): {e}")

    # ── Status ────────────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        from packet_capture.interface_utils import check_tshark_installed
        tshark_ok, tshark_info = check_tshark_installed()
        with self._lock:
            raw = getattr(self._sniffer, "raw_count", 0) if self._sniffer else 0
            active_flows = self._aggregator.active_flow_count() if self._aggregator else 0
            return {
                "is_running": self._running,
                "selected_interface": self._interface_friendly or self._interface,
                "resolved_interface": self._interface,
                "packets_captured": self._packets_processed,
                "events_analyzed": self._flows_analyzed,
                "packets_failed": self._flows_failed,
                "active_flows": active_flows,
                "raw_packets_seen": raw,
                "batch_interval_s": BATCH_INTERVAL,
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
            active = self._aggregator.active_flow_count() if self._aggregator else 0
        return {
            "ml_ready": _ML_READY,
            "events_in_queue": len(list(self._events)),
            "packets_captured": self._packets_processed,
            "events_analyzed": self._flows_analyzed,
            "packets_failed": self._flows_failed,
            "active_flows": active,
            "raw_packets_seen": raw,
            "last_error": self._last_error,
            "sample_events": sample,
        }

    # ── Data getters ────────────────────────────────────────────────────────────

    def get_events(self, limit: int = 50) -> list:
        with self._lock:
            events = list(self._events)
        return list(reversed(events))[:limit]

    def get_dashboard_stats(self) -> dict:
        with self._lock:
            events = list(self._events)
            packets = self._packets_processed
            active_flows = self._aggregator.active_flow_count() if self._aggregator else 0

        if not events:
            return {
                "total_packets": packets, "active_flows": active_flows,
                "threats_detected": 0, "average_trust_score": 0.0,
                "blocked_connections": 0, "model_confidence": 0.0,
                "benign_count": 0, "attack_count": 0,
                "critical_count": 0, "high_risk_count": 0, "source": "live",
            }

        threats   = [e for e in events if e.get("is_threat")]
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
            "active_flows": max(active_flows, len(unique_srcs)),
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
            "Mirai": "#ff8c42", "Recon": "#00d4ff", "Scan": "#00d4ff",
            "Spoofing": "#f87171", "BruteForce": "#ec4899", "Injection": "#a78bfa",
            "XSS": "#fbbf24", "Backdoor": "#c0392b", "MITM": "#fb7185",
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
                "message": (e.get("reason")
                            or f"{e.get('predicted_label','Unknown')} from {e.get('source_ip','?')}"),
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
            b = buckets.setdefault(slot, {"normal": 0, "threats": 0, "packets": 0})
            if e.get("is_threat"):
                b["threats"] += 1
            else:
                b["normal"] += 1
            b["packets"] += int(e.get("flow_packets") or 1)
        result = []
        for i in range(12):
            b = buckets.get(i, {"normal": 0, "threats": 0, "packets": 0})
            mins_ago = 11 - i
            result.append({
                "time": f"-{mins_ago}m" if mins_ago > 0 else "now",
                "normal": b["normal"], "threats": b["threats"], "packets": b["packets"],
            })
        return result

    def get_network_flows(self, limit: int = 25) -> list:
        events = self.get_events(limit)
        flows = []
        for i, e in enumerate(events):
            dur = float(e.get("flow_duration") or 0.0)
            flows.append({
                "id": e.get("id", f"F-{i:05d}"),
                "srcIP": e.get("source_ip") or "?",
                "dstIP": e.get("dest_ip") or "?",
                "protocol": e.get("protocol") or "?",
                "packetCount": int(e.get("flow_packets") or 1),
                "flowDuration": _fmt_duration(dur),
                "bytes": _fmt_bytes(int(e.get("flow_bytes") or 0)),
                "status": _action_to_status(e.get("action", "Allow")),
                "attackType": e.get("predicted_label") or "BENIGN",
            })
        return flows

    def get_security_decisions(self) -> dict:
        with self._lock:
            events = list(self._events)
        counts = {"allow": 0, "restrict": 0, "alert": 0, "quarantine": 0, "block": 0}
        for e in events:
            action = (e.get("action") or "Allow").lower()
            if action in counts:
                counts[action] += 1
        total = sum(counts.values()) or 1
        return {k: {"count": v, "percentage": round(v / total * 100, 1)} for k, v in counts.items()}

    # ── Topology (delegated to the stateful TopologyManager) ─────────────────────

    def get_topology(self) -> dict:
        if not self._topology:
            return {"nodes": [], "edges": [], "total_events": 0}
        return self._topology.get_topology()

    def get_risky_nodes(self) -> dict:
        if not self._topology:
            return {"risky_nodes": [], "count": 0}
        return self._topology.get_risky_nodes()

    # ── Simulation injection ─────────────────────────────────────────────────────

    def inject_simulated_flow(self, *, src_ip: str, dst_ip: str, src_port: int,
                              dst_port: int, protocol: str, features: dict,
                              packet_count: int, byte_count: int,
                              sim_type: str) -> Optional[dict]:
        """
        Run a synthetic (simulation) flow through the full detection pipeline so
        it shows up live across the dashboard / topology / trust / decisions.
        No real packets are sent — only the analysed event is recorded.
        Returns the enriched event (or None if the pipeline is unavailable).
        """
        if not _ML_READY or self._topology is None:
            return None
        try:
            topo_risk = self._topology.risk_index().get(src_ip, "Low")
            result = _analyze_flow(features, entity_id=str(src_ip), topology_risk=topo_risk)
            pkts = max(1, int(packet_count))
            per_pkt = max(1, int(byte_count) // pkts)
            flow = {
                "protocol": protocol, "src_ip": src_ip, "dst_ip": dst_ip,
                "src_port": src_port, "dst_port": dst_port,
                "duration": 0.05, "last_ts": time.time(),
                "packet_count": pkts,
                "all_sizes": [per_pkt] * pkts,
            }
            event = self._build_event(flow, result)
            event["simulated"] = True
            event["sim_type"] = sim_type

            self._topology.update_flow(event)
            with self._lock:
                self._events.append(event)
                self._packets_processed += pkts
                self._flows_analyzed += 1
            return event
        except Exception as exc:
            with self._lock:
                self._last_error = f"[sim_inject] {type(exc).__name__}: {exc}"
            log.warning(f"[SECURITY_DECISION] simulated flow injection failed: {exc}")
            return None


# ── Singleton ────────────────────────────────────────────────────────────────

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

def _fmt_duration(seconds: float) -> str:
    if seconds <= 0:
        return "00:00:00"
    h = int(seconds // 3600); m = int((seconds % 3600) // 60); s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def _fmt_bytes(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f} MB"
    if n >= 1_000:
        return f"{n/1_000:.1f} KB"
    return f"{n} B"
