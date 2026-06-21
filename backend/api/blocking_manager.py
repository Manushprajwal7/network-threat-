"""
Blocking Manager — controlled simulation of network entity blocking.

SIMULATION_MODE = True by default.
In simulation mode: NO real firewall rules are modified.
Blocked IPs are stored in memory + a local JSON file.

Real firewall mode is opt-in, disabled by default, and restricted to
private/local IP ranges only. Public IPs are never blocked automatically.

Private ranges:
  127.x.x.x
  10.x.x.x
  172.16–31.x.x
  192.168.x.x
"""

import ipaddress
import json
import logging
import datetime
from pathlib import Path
from threading import Lock
from typing import Optional

log = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────

SIMULATION_MODE   = True
REAL_FIREWALL_MODE= False   # Never auto-enabled; requires explicit code change

STATE_FILE = Path(__file__).parent.parent / "data" / "blocked_entities.json"

PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]


def _is_private_or_local(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return any(addr in net for net in PRIVATE_NETWORKS) or addr.is_loopback
    except ValueError:
        return False


# ── State ──────────────────────────────────────────────────────────────────────

class BlockingManager:
    """
    Thread-safe manager for tracking blocked IPs/entities.
    Persists state to a local JSON file.
    """

    def __init__(self):
        self._lock    = Lock()
        self._blocked: dict[str, dict] = {}   # ip → {reason, timestamp, action, count}
        self._history: list[dict]      = []   # audit log of all block/unblock actions
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._load_state()

    # ── Block / Unblock ────────────────────────────────────────────────────────

    def block(self, ip: str, reason: str = "Manual block",
              action: str = "Block", require_local: bool = True) -> dict:
        """
        Block an IP address (simulation or real, depending on config).

        In SIMULATION_MODE: records in memory only.
        In REAL_FIREWALL_MODE: applies Windows netsh rule (local IPs only).
        """
        if require_local and not _is_private_or_local(ip):
            return {
                "ok":    False,
                "error": f"Refusing to block public IP {ip}. "
                         "Only private/local IPs are allowed.",
            }

        with self._lock:
            existing = self._blocked.get(ip, {})
            count    = existing.get("count", 0) + 1
            entry    = {
                "ip":        ip,
                "reason":    reason,
                "action":    action,
                "count":     count,
                "timestamp": _now(),
                "mode":      "simulation" if SIMULATION_MODE else "real",
            }
            self._blocked[ip] = entry
            self._history.append({"event": "block", **entry})
            self._save_state()

        if not SIMULATION_MODE and REAL_FIREWALL_MODE:
            self._apply_firewall_block(ip, reason)

        log.info(f"[BLOCK] {ip} — {reason} (mode={'sim' if SIMULATION_MODE else 'real'})")
        return {"ok": True, "ip": ip, "action": action, "mode": entry["mode"]}

    def unblock(self, ip: str) -> dict:
        with self._lock:
            if ip not in self._blocked:
                return {"ok": False, "error": f"IP {ip} is not currently blocked"}
            removed = self._blocked.pop(ip)
            self._history.append({
                "event":     "unblock",
                "ip":        ip,
                "reason":    "Manual unblock",
                "timestamp": _now(),
            })
            self._save_state()

        if not SIMULATION_MODE and REAL_FIREWALL_MODE:
            self._remove_firewall_block(ip)

        log.info(f"[UNBLOCK] {ip}")
        return {"ok": True, "ip": ip, "previous": removed}

    def is_blocked(self, ip: str) -> bool:
        return ip in self._blocked

    def get_blocked_list(self) -> list[dict]:
        with self._lock:
            return list(self._blocked.values())

    def get_history(self, limit: int = 50) -> list[dict]:
        with self._lock:
            return self._history[-limit:]

    def auto_block_decision(
        self,
        ip: str,
        risk_level: str,
        trust_level: str,
        consecutive_critical: int,
        predicted_label: str,
    ) -> Optional[dict]:
        """
        Auto-block logic based on risk / trust / repeat offenses.
        Returns block result if triggered, else None.
        """
        reason = None
        if consecutive_critical >= 3:
            reason = f"Auto-block: {consecutive_critical} consecutive Critical events"
        elif risk_level == "Critical" and trust_level == "Low Trust":
            reason = f"Auto-block: Critical risk + Low Trust ({predicted_label})"

        if reason:
            return self.block(ip, reason=reason, action="Block")
        return None

    # ── Persistence ────────────────────────────────────────────────────────────

    def _save_state(self):
        try:
            state = {"blocked": self._blocked, "history": self._history[-200:]}
            STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
        except Exception as e:
            log.warning(f"Could not save block state: {e}")

    def _load_state(self):
        if STATE_FILE.exists():
            try:
                state          = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                self._blocked  = state.get("blocked", {})
                self._history  = state.get("history", [])
                log.info(f"Loaded {len(self._blocked)} blocked entities from state file")
            except Exception as e:
                log.warning(f"Could not load block state: {e}")

    # ── Real firewall (opt-in, Windows only) ───────────────────────────────────

    def _apply_firewall_block(self, ip: str, reason: str) -> None:
        import subprocess
        if not _is_private_or_local(ip):
            log.error(f"Refusing real firewall block for public IP {ip}")
            return
        rule = f"NetShield-Block-{ip.replace('.', '-')}"
        cmd  = ["netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule}", "dir=in", "action=block",
                f"remoteip={ip}", "protocol=any"]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            log.info(f"Firewall rule added: {rule}")
        except Exception as e:
            log.error(f"Failed to add firewall rule: {e}")

    def _remove_firewall_block(self, ip: str) -> None:
        import subprocess
        rule = f"NetShield-Block-{ip.replace('.', '-')}"
        cmd  = ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={rule}"]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            log.info(f"Firewall rule removed: {rule}")
        except Exception as e:
            log.error(f"Failed to remove firewall rule: {e}")


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"


# ── Singleton ─────────────────────────────────────────────────────────────────

_manager: Optional[BlockingManager] = None


def get_blocking_manager() -> BlockingManager:
    global _manager
    if _manager is None:
        _manager = BlockingManager()
    return _manager
