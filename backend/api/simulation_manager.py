"""
Attack Simulation Manager — controlled local-only simulation.

SAFETY RULES (enforced in code, not just documentation):
  - All targets are 127.0.0.1 or loopback only
  - No real network scanning of external IPs
  - No real credentials tested
  - Port range limited to safe localhost ports (8000–8020)
  - Rate-limited; cannot generate real DDoS traffic
  - All events are SYNTHETIC; no real exploit payloads
  - Clearly labelled as "SIMULATION" in all output

Supported simulation types:
  dos        — repeated synthetic requests to localhost test endpoint
  portscan   — TCP connect probes to 127.0.0.1:8000–8020 only
  bruteforce — repeated failed-auth events against mock endpoint
  botnet     — synthetic beacon events to dummy local addresses
  unknown    — anomalous feature vectors outside training distribution
"""

import logging
import threading
import time
import datetime
import uuid
import random
import socket
from typing import Optional
from collections import deque

log = logging.getLogger(__name__)

# ── Safety constants ────────────────────────────────────────────────────────────
SAFE_TARGET        = "127.0.0.1"
SAFE_PORT_RANGE    = range(8000, 8021)
MAX_DURATION_SEC   = 60          # maximum allowed simulation duration
RATE_LIMIT_DELAY   = 0.05        # seconds between synthetic events (20 events/s max)
MAX_EVENT_QUEUE    = 500

# ── Simulation type metadata ────────────────────────────────────────────────────
SIM_TYPES = {
    "dos": {
        "label":       "DoS Simulation",
        "description": "Synthetic repeated request events to localhost test endpoint",
        "attack_type": "DoS",
        "risk_level":  "High",
    },
    "portscan": {
        "label":       "PortScan Simulation",
        "description": "TCP connect probes to 127.0.0.1 ports 8000–8020 only",
        "attack_type": "PortScan",
        "risk_level":  "High",
    },
    "bruteforce": {
        "label":       "Brute Force Simulation",
        "description": "Repeated failed-login events against mock local endpoint",
        "attack_type": "Brute Force",
        "risk_level":  "Critical",
    },
    "botnet": {
        "label":       "Botnet Behavior Simulation",
        "description": "Synthetic periodic beacon events to dummy local addresses",
        "attack_type": "Botnet",
        "risk_level":  "Critical",
    },
    "unknown": {
        "label":       "Unknown Threat Simulation",
        "description": "Anomalous synthetic flow features outside training distribution",
        "attack_type": "Unknown",
        "risk_level":  "Critical",
    },
}


# ── Synthetic actors (RFC-5737 doc ranges for "external" attackers; ───────────────
#    RFC-1918 private ranges for "internal" victims). These are labels only —
#    no real packets are sent to them. They give the dashboard/topology a
#    realistic attacker→victim picture.
_ATTACKER = {
    "dos":        "203.0.113.66",
    "portscan":   "198.51.100.40",
    "bruteforce": "203.0.113.7",
    "botnet":     "10.0.0.66",      # internal infected host beaconing out
    "unknown":    "198.51.100.13",
}
_VICTIM = {
    "dos":        "10.0.0.10",
    "bruteforce": "10.0.0.22",
    "botnet":     "192.0.2.99",     # external C2
    "unknown":    "10.0.0.5",
}


def _ciciot_features(*, number: int, pkt_size: float, duration: float,
                     proto_num: int, dst_port: int, flags: set) -> dict:
    """Build a CICIoT2023 feature dict for a synthetic attack flow."""
    dur = duration if duration > 1e-6 else 1e-3
    f = {
        "flow_duration": dur,
        "Header_Length": 40.0 * number,
        "Protocol Type": float(proto_num),
        "Duration": 64.0,
        "Rate": number / dur,
        "Srate": number / dur,
        "Drate": 0.0,
        "TCP": 1.0 if proto_num == 6 else 0.0,
        "UDP": 1.0 if proto_num == 17 else 0.0,
        "ICMP": 1.0 if proto_num == 1 else 0.0,
        "IPv": 1.0,
        "HTTP": 1.0 if dst_port in (80, 8080) else 0.0,
        "HTTPS": 1.0 if dst_port == 443 else 0.0,
        "SSH": 1.0 if dst_port == 22 else 0.0,
        "Telnet": 1.0 if dst_port == 23 else 0.0,
        "Tot sum": pkt_size * number,
        "Min": pkt_size, "Max": pkt_size, "AVG": pkt_size, "Tot size": pkt_size, "Std": 0.0,
        "Number": float(number),
        "IAT": dur / max(1, number),
        "Magnitue": (2 * pkt_size) ** 0.5,
        "Radius": 0.0, "Covariance": 0.0, "Variance": 0.0,
        "Weight": float(number),
    }
    for name in ("fin", "syn", "rst", "psh", "ack", "ece", "cwr"):
        f[f"{name}_flag_number"] = 1.0 if name in flags else 0.0
    for name in ("ack", "syn", "fin", "urg", "rst"):
        f[f"{name}_count"] = float(number if name in flags else 0)
    return f


def _make_dos_event(seq: int) -> dict:
    n = random.randint(180, 320)
    return _base_event("dos", seq, _ATTACKER["dos"], _VICTIM["dos"], 80, "TCP", {
        "description":   "High-rate SYN flood — short duration, high packet rate",
        "_features":     _ciciot_features(number=n, pkt_size=60, duration=random.uniform(0.01, 0.03),
                                          proto_num=6, dst_port=80, flags={"syn"}),
        "_packets":      n,
        "_bytes":        n * 60,
    })


def _make_portscan_event(seq: int) -> dict:
    # Fan out across many internal hosts → triggers topology scan detection
    victim = f"10.0.0.{(seq % 24) + 1}"
    port = random.randint(1, 1024)
    return _base_event("portscan", seq, _ATTACKER["portscan"], victim, port, "TCP", {
        "description":   f"SYN/RST probe to {victim}:{port}",
        "_features":     _ciciot_features(number=2, pkt_size=60, duration=random.uniform(0.0005, 0.003),
                                          proto_num=6, dst_port=port, flags={"syn", "rst"}),
        "_packets":      2,
        "_bytes":        120,
    })


def _make_bruteforce_event(seq: int) -> dict:
    n = random.randint(6, 14)
    return _base_event("bruteforce", seq, _ATTACKER["bruteforce"], _VICTIM["bruteforce"], 22, "TCP", {
        "description":   "Repeated failed-auth attempts against SSH (mock)",
        "auth_result":   "FAILED",
        "_features":     _ciciot_features(number=n, pkt_size=100, duration=random.uniform(0.1, 0.5),
                                          proto_num=6, dst_port=22, flags={"syn", "ack", "psh"}),
        "_packets":      n,
        "_bytes":        n * 100,
    })


def _make_botnet_event(seq: int) -> dict:
    interval = random.uniform(20, 60)
    n = random.randint(2, 5)
    return _base_event("botnet", seq, _ATTACKER["botnet"], _VICTIM["botnet"], 8443, "UDP", {
        "description":      f"Periodic C2 beacon (interval ~{interval:.0f}s)",
        "beacon_interval_s": round(interval, 1),
        "_features":         _ciciot_features(number=n, pkt_size=120, duration=random.uniform(0.05, 0.2),
                                              proto_num=17, dst_port=8443, flags=set()),
        "_packets":          n,
        "_bytes":            n * 120,
    })


def _make_unknown_event(seq: int) -> dict:
    # Extreme, out-of-distribution features → low confidence / high entropy → Unknown
    feats = _ciciot_features(number=1, pkt_size=65000, duration=0.00005,
                             proto_num=6, dst_port=31337, flags={"syn", "fin", "rst", "psh", "urg"})
    feats["Rate"] = 5_000_000.0
    feats["Tot sum"] = 5_000_000.0
    return _base_event("unknown", seq, _ATTACKER["unknown"], _VICTIM["unknown"], 31337, "TCP", {
        "description":   "Anomalous flow far outside training distribution",
        "anomaly":       True,
        "_features":     feats,
        "_packets":      1,
        "_bytes":        65000,
    })


def _base_event(sim_type: str, seq: int, src_ip: str, dst_ip: str,
                dst_port: int, protocol: str, extras: dict) -> dict:
    meta = SIM_TYPES[sim_type]
    return {
        "id":             str(uuid.uuid4()),
        "sequence":       seq,
        "timestamp":      _now(),
        "simulation":     True,
        "sim_type":       sim_type,
        "attack_type":    meta["attack_type"],
        "risk_level":     meta["risk_level"],
        "source_ip":      src_ip,
        "dest_ip":        dst_ip,
        "source_port":    random.randint(49152, 65535),
        "dest_port":      dst_port,
        "protocol":       protocol,
        "safety_label":   "SYNTHETIC SIMULATION — no real packets sent",
        **extras,
    }


# ── Portscan — only touches localhost safe ports ────────────────────────────────

def _probe_localhost_ports(results: list) -> None:
    """Actually probe localhost:8000–8020 (non-destructive TCP connect check)."""
    for port in SAFE_PORT_RANGE:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.05)
            result = s.connect_ex((SAFE_TARGET, port))
            results.append({"port": port, "open": result == 0})
            s.close()
        except Exception:
            results.append({"port": port, "open": False})


# ── Simulation state ──────────────────────────────────────────────────────────

class SimulationManager:
    def __init__(self):
        self._lock        = threading.Lock()
        self._running     = False
        self._thread: Optional[threading.Thread] = None
        self._sim_type    = None
        self._events      = deque(maxlen=MAX_EVENT_QUEUE)
        self._start_time  = None
        self._end_time    = None
        self._event_count = 0
        self._duration    = 30

    def start(self, sim_type: str, duration_seconds: int = 30) -> dict:
        with self._lock:
            if self._running:
                return {"ok": False, "error": "Simulation already running"}
            if sim_type not in SIM_TYPES:
                return {"ok": False, "error": f"Unknown simulation type: {sim_type}"}

            duration          = min(int(duration_seconds), MAX_DURATION_SEC)
            self._sim_type    = sim_type
            self._duration    = duration
            self._running     = True
            self._start_time  = time.time()
            self._events.clear()
            self._event_count = 0

            self._thread = threading.Thread(
                target=self._run_simulation,
                args=(sim_type, duration),
                daemon=True,
            )
            self._thread.start()

        log.info(f"[SIM] Started '{sim_type}' simulation for {duration}s")
        return {
            "ok":         True,
            "sim_type":   sim_type,
            "duration":   duration,
            "safety":     "LOCAL CONTROLLED SIMULATION ONLY",
            "target":     SAFE_TARGET,
        }

    def stop(self) -> dict:
        with self._lock:
            if not self._running:
                return {"ok": False, "error": "No simulation is running"}
            self._running  = False
            self._end_time = time.time()
        log.info(f"[SIM] Stopped '{self._sim_type}' simulation")
        return {"ok": True, "events_generated": self._event_count}

    def get_status(self) -> dict:
        elapsed = (time.time() - self._start_time) if self._start_time else 0
        return {
            "running":          self._running,
            "sim_type":         self._sim_type,
            "duration":         self._duration,
            "elapsed_seconds":  round(elapsed, 1),
            "remaining_seconds":max(0, round(self._duration - elapsed, 1)),
            "events_generated": self._event_count,
        }

    def get_events(self, limit: int = 50) -> list:
        with self._lock:
            events = list(self._events)
        return events[-limit:]

    def _run_simulation(self, sim_type: str, duration: int) -> None:
        generators = {
            "dos":        _make_dos_event,
            "portscan":   _make_portscan_event,
            "bruteforce": _make_bruteforce_event,
            "botnet":     _make_botnet_event,
            "unknown":    _make_unknown_event,
        }
        gen    = generators[sim_type]
        seq    = 0

        # For portscan, do a real (safe) localhost probe once at start
        if sim_type == "portscan":
            probe_results: list = []
            _probe_localhost_ports(probe_results)

        # Inject simulated flows into the live detection pipeline so they have a
        # visible effect across the dashboard / topology / trust / decisions.
        try:
            from packet_capture.capture_manager import get_manager
            capture = get_manager()
        except Exception as e:
            capture = None
            log.warning(f"[SIM] capture manager unavailable for injection: {e}")

        # Pre-warm the ensemble so the first injection doesn't eat the run window
        # (the Random Forest model is large and slow to load on first use).
        try:
            from ml_model.ensemble_detector import get_ensemble_members
            from ml_model.predict import build_feature_row, predict_proba_full
            warm_row = build_feature_row({"Number": 1, "Rate": 1.0})
            for m in get_ensemble_members():
                predict_proba_full(m, warm_row)
        except Exception as e:
            log.debug(f"[SIM] prewarm skipped: {e}")

        # Start the clock AFTER prewarm so the full duration is spent generating.
        end_t = time.time() + duration

        while time.time() < end_t:
            with self._lock:
                if not self._running:
                    break

            evt = gen(seq)
            seq += 1

            # Run through the real pipeline and merge the detection result back
            if capture is not None:
                enriched = capture.inject_simulated_flow(
                    src_ip=evt["source_ip"], dst_ip=evt["dest_ip"],
                    src_port=evt["source_port"], dst_port=evt["dest_port"],
                    protocol=evt["protocol"], features=evt.pop("_features", {}),
                    packet_count=evt.pop("_packets", 1), byte_count=evt.pop("_bytes", 0),
                    sim_type=sim_type,
                )
                if enriched:
                    evt["predicted_attack"] = enriched.get("predicted_label")
                    evt["confidence"]       = enriched.get("confidence")
                    evt["risk_level"]       = enriched.get("risk_level", evt["risk_level"])
                    evt["trust_score"]      = enriched.get("trust_score")
                    evt["trust_level"]      = enriched.get("trust_level")
                    evt["security_action"]  = enriched.get("action")
                    evt["anomaly_score"]    = enriched.get("anomaly_score")
                    evt["known_or_unknown"] = enriched.get("known_or_unknown", "Known")
                    evt["event_id"]         = enriched.get("id")
            else:
                evt.pop("_features", None); evt.pop("_packets", None); evt.pop("_bytes", None)

            with self._lock:
                self._events.append(evt)
                self._event_count += 1

            time.sleep(RATE_LIMIT_DELAY)

        with self._lock:
            self._running  = False
            self._end_time = time.time()
        log.info(f"[SIM] '{sim_type}' finished after {seq} events")


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"


# ── Singleton ─────────────────────────────────────────────────────────────────

_sim: Optional[SimulationManager] = None


def get_simulation_manager() -> SimulationManager:
    global _sim
    if _sim is None:
        _sim = SimulationManager()
    return _sim
