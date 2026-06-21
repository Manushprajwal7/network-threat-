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


# ── Event generators (purely synthetic) ────────────────────────────────────────

def _make_dos_event(seq: int) -> dict:
    return _base_event("dos", seq, {
        "flow_duration":          random.uniform(0.001, 0.02),
        "total_fwd_packets":      random.randint(500, 2000),
        "flow_bytes_s":           random.uniform(1e6, 5e6),
        "packet_length_mean":     random.uniform(40, 80),
        "syn_flag_count":         random.randint(1, 5),
        "description":            "High packet rate / short duration DoS-like flow",
    })


def _make_portscan_event(seq: int) -> dict:
    port = random.choice(list(SAFE_PORT_RANGE))
    return _base_event("portscan", seq, {
        "dest_port":              port,
        "flow_duration":          random.uniform(0.0001, 0.002),
        "total_fwd_packets":      1,
        "total_backward_packets": 0,
        "syn_flag_count":         1,
        "rst_flag_count":         1,
        "description":            f"SYN probe to localhost:{port}",
    })


def _make_bruteforce_event(seq: int) -> dict:
    return _base_event("bruteforce", seq, {
        "flow_duration":          random.uniform(0.1, 0.5),
        "total_fwd_packets":      random.randint(3, 10),
        "fin_flag_count":         1,
        "ack_flag_count":         random.randint(2, 8),
        "description":            "Repeated failed-auth attempt (mock endpoint)",
        "auth_result":            "FAILED",
    })


def _make_botnet_event(seq: int) -> dict:
    interval = random.uniform(20, 60)
    return _base_event("botnet", seq, {
        "flow_duration":          random.uniform(0.05, 0.2),
        "total_fwd_packets":      random.randint(1, 4),
        "total_backward_packets": random.randint(1, 3),
        "flow_bytes_s":           random.uniform(100, 800),
        "beacon_interval_s":      round(interval, 1),
        "description":            f"Periodic synthetic beacon (interval ~{interval:.0f}s)",
    })


def _make_unknown_event(seq: int, n_features: int = 78) -> dict:
    features = {f"feat_{i}": random.uniform(1e6, 1e9) * (1 + random.gauss(0, 0.5))
                for i in range(min(n_features, 20))}
    return _base_event("unknown", seq, {
        "description": "Anomalous features outside training distribution",
        "anomaly":     True,
        **features,
    })


def _base_event(sim_type: str, seq: int, extras: dict) -> dict:
    meta = SIM_TYPES[sim_type]
    return {
        "id":             str(uuid.uuid4()),
        "sequence":       seq,
        "timestamp":      _now(),
        "simulation":     True,
        "sim_type":       sim_type,
        "attack_type":    meta["attack_type"],
        "risk_level":     meta["risk_level"],
        "source_ip":      SAFE_TARGET,
        "dest_ip":        SAFE_TARGET,
        "source_port":    random.randint(49152, 65535),
        "dest_port":      random.choice(list(SAFE_PORT_RANGE)),
        "protocol":       "TCP",
        "safety_label":   "LOCAL CONTROLLED SIMULATION ONLY",
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
        end_t  = time.time() + duration
        seq    = 0

        # For portscan, do a real (safe) localhost probe once at start
        if sim_type == "portscan":
            probe_results: list = []
            _probe_localhost_ports(probe_results)

        while time.time() < end_t:
            with self._lock:
                if not self._running:
                    break

            evt = gen(seq)
            seq += 1

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
