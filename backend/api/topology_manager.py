"""
Topology Manager — live, stateful network graph built from analysed flows.

Pipeline stage: SECURITY_DECISION → (this) → DASHBOARD

Maintains a persistent graph for the whole capture session (not rebuilt per
request). Each analysed flow updates node/edge statistics. Topology risk logic:

  - repeated attacker node               → elevated risk
  - node fanning out to many destinations → possible scan
  - low-trust node touching a critical    → quarantine/block recommendation
  - high-centrality node under attack     → critical alert

Exposes graph + risky-node intelligence to the dashboard API.
"""

import ipaddress
import logging
import threading
import time

log = logging.getLogger(__name__)

_RANK = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
_NAME = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}

# Risk-logic thresholds
REPEAT_ATTACK_THRESH = 3     # threat flows from a node → repeated attacker
FANOUT_SCAN_THRESH   = 15    # distinct destinations → possible scan
CENTRALITY_HIGH      = 20    # node degree considered high-centrality
MAX_NODES            = 400
MAX_EDGES            = 800


def _is_private(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip.split("%")[0])
        return bool(addr.is_private or addr.is_link_local or addr.is_loopback)
    except ValueError:
        return False


class TopologyManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._nodes: dict = {}
        self._edges: dict = {}
        self._total_flows = 0

    # ── Update ──────────────────────────────────────────────────────────────────

    def _node(self, ip: str) -> dict:
        nd = self._nodes.get(ip)
        if nd is None:
            nd = {
                "id": ip,
                "packets_sent": 0,
                "packets_received": 0,
                "threat_count": 0,
                "protocols": set(),
                "attacks": set(),
                "actions": set(),
                "dst_set": set(),
                "src_set": set(),
                "trust_score": 100.0,
                "risk_rank": 0,
                "last_seen": time.time(),
            }
            self._nodes[ip] = nd
        return nd

    def update_flow(self, event: dict):
        """Update the graph from one analysed flow event."""
        src = event.get("source_ip")
        dst = event.get("dest_ip")
        proto = event.get("protocol") or "UNKNOWN"
        pkts = int(event.get("flow_packets") or 1)
        nbytes = int(event.get("flow_bytes") or event.get("packet_length") or 0)
        label = (event.get("predicted_label") or "BENIGN")
        is_threat = bool(event.get("is_threat"))
        risk = event.get("risk_level", "Low")
        trust = float(event.get("trust_score", 100.0))
        action = event.get("action", "Allow")

        with self._lock:
            self._total_flows += 1

            if src:
                n = self._node(src)
                n["packets_sent"] += pkts
                n["protocols"].add(proto)
                n["actions"].add(action)
                n["trust_score"] = min(n["trust_score"], trust)
                n["last_seen"] = time.time()
                if dst:
                    n["dst_set"].add(dst)
                if is_threat:
                    n["threat_count"] += 1
                    n["attacks"].add(label)
                    n["risk_rank"] = max(n["risk_rank"], _RANK.get(risk, 0))

            if dst:
                n = self._node(dst)
                n["packets_received"] += pkts
                n["protocols"].add(proto)
                n["last_seen"] = time.time()
                if src:
                    n["src_set"].add(src)

            if src and dst:
                key = f"{src}|{dst}"
                ed = self._edges.get(key)
                if ed is None:
                    ed = {
                        "source": src, "target": dst,
                        "packet_count": 0, "flow_count": 0, "bytes": 0,
                        "protocols": set(), "attacks": set(),
                        "has_threat": False, "risk_rank": 0,
                        "last_seen": time.time(),
                    }
                    self._edges[key] = ed
                ed["packet_count"] += pkts
                ed["flow_count"] += 1
                ed["bytes"] += nbytes
                ed["protocols"].add(proto)
                ed["last_seen"] = time.time()
                if is_threat:
                    ed["has_threat"] = True
                    ed["attacks"].add(label)
                    ed["risk_rank"] = max(ed["risk_rank"], _RANK.get(risk, 0))

            self._evict_if_needed()

    def _evict_if_needed(self):
        if len(self._nodes) > MAX_NODES:
            for ip, _ in sorted(self._nodes.items(), key=lambda kv: kv[1]["last_seen"])[:len(self._nodes) - MAX_NODES]:
                self._nodes.pop(ip, None)
        if len(self._edges) > MAX_EDGES:
            for k, _ in sorted(self._edges.items(), key=lambda kv: kv[1]["last_seen"])[:len(self._edges) - MAX_EDGES]:
                self._edges.pop(k, None)

    # ── Risk analysis ───────────────────────────────────────────────────────────

    def _node_status(self, actions: set) -> str:
        if "Block" in actions:
            return "blocked"
        if "Quarantine" in actions:
            return "quarantined"
        if "Alert" in actions:
            return "alerted"
        if "Restrict" in actions:
            return "restricted"
        return "active"

    def _analyse_node(self, nd: dict, critical_ids: set) -> dict:
        """Compute effective risk + reasons for one node."""
        reasons = []
        rank = nd["risk_rank"]
        degree = len(nd["dst_set"]) + len(nd["src_set"])
        fanout = len(nd["dst_set"])

        if nd["threat_count"] >= REPEAT_ATTACK_THRESH:
            rank = max(rank, _RANK["High"])
            reasons.append(f"repeated attacker ({nd['threat_count']} threat flows)")

        if fanout >= FANOUT_SCAN_THRESH:
            rank = max(rank, _RANK["High"])
            reasons.append(f"possible scan (fan-out to {fanout} hosts)")

        if nd["trust_score"] < 50 and (nd["dst_set"] & critical_ids):
            rank = max(rank, _RANK["Critical"])
            reasons.append("low-trust node communicating with a critical node")

        if degree >= CENTRALITY_HIGH and nd["threat_count"] > 0:
            rank = max(rank, _RANK["Critical"])
            reasons.append(f"high-centrality node under attack (degree {degree})")

        return {"risk_rank": rank, "reasons": reasons, "degree": degree, "fanout": fanout}

    def _critical_ids(self) -> set:
        """Nodes considered critical: high packet volume hubs."""
        if not self._nodes:
            return set()
        vols = sorted(
            ((ip, nd["packets_sent"] + nd["packets_received"]) for ip, nd in self._nodes.items()),
            key=lambda kv: -kv[1],
        )
        top = vols[: max(1, len(vols) // 10)]   # top 10% by volume
        return {ip for ip, _ in top}

    # ── Output ──────────────────────────────────────────────────────────────────

    def get_topology(self) -> dict:
        with self._lock:
            if not self._nodes:
                return {"nodes": [], "edges": [], "total_events": 0}
            critical_ids = self._critical_ids()

            nodes = []
            for ip, nd in self._nodes.items():
                analysis = self._analyse_node(nd, critical_ids)
                pkt_total = nd["packets_sent"] + nd["packets_received"]
                nodes.append({
                    "id": ip,
                    "packet_count": pkt_total,
                    "packets_sent": nd["packets_sent"],
                    "packets_received": nd["packets_received"],
                    "threat_count": nd["threat_count"],
                    "trust_score": round(nd["trust_score"], 1),
                    "risk_level": _NAME[analysis["risk_rank"]],
                    "protocols": list(nd["protocols"])[:6],
                    "attacks": list(nd["attacks"])[:6],
                    "actions": list(nd["actions"])[:4],
                    "status": self._node_status(nd["actions"]),
                    "degree": analysis["degree"],
                    "fanout": analysis["fanout"],
                    "risk_reasons": analysis["reasons"],
                    "is_local": _is_private(ip),
                })
            nodes.sort(key=lambda x: (-int(x["is_local"]), -x["packet_count"]))

            edges = [
                {
                    "source": ed["source"], "target": ed["target"],
                    "count": ed["packet_count"],
                    "flow_count": ed["flow_count"],
                    "protocols": list(ed["protocols"])[:3],
                    "attacks": list(ed["attacks"])[:4],
                    "bytes": ed["bytes"],
                    "has_threat": ed["has_threat"],
                    "risk_level": _NAME[ed["risk_rank"]],
                }
                for ed in sorted(self._edges.values(), key=lambda x: -x["packet_count"])
            ]

            return {
                "nodes": nodes[:120],
                "edges": edges[:200],
                "total_events": self._total_flows,
            }

    def get_risky_nodes(self) -> dict:
        with self._lock:
            if not self._nodes:
                return {"risky_nodes": [], "count": 0}
            critical_ids = self._critical_ids()
            risky = []
            for ip, nd in self._nodes.items():
                analysis = self._analyse_node(nd, critical_ids)
                rank = analysis["risk_rank"]
                if rank >= _RANK["Medium"] or nd["threat_count"] > 0:
                    risky.append({
                        "id": ip,
                        "risk_level": _NAME[rank],
                        "risk_rank": rank,
                        "threat_count": nd["threat_count"],
                        "trust_score": round(nd["trust_score"], 1),
                        "packets_sent": nd["packets_sent"],
                        "packets_received": nd["packets_received"],
                        "fanout": analysis["fanout"],
                        "degree": analysis["degree"],
                        "attacks": list(nd["attacks"])[:6],
                        "status": self._node_status(nd["actions"]),
                        "reasons": analysis["reasons"] or ["threat flows observed"],
                        "is_local": _is_private(ip),
                    })
            risky.sort(key=lambda x: (-x["risk_rank"], -x["threat_count"]))
            return {"risky_nodes": risky[:50], "count": len(risky)}

    def risk_index(self) -> dict:
        """Snapshot of {node_ip: risk_level} for fast per-flow context lookups."""
        with self._lock:
            if not self._nodes:
                return {}
            critical_ids = self._critical_ids()
            return {
                ip: _NAME[self._analyse_node(nd, critical_ids)["risk_rank"]]
                for ip, nd in self._nodes.items()
            }

    def reset(self):
        with self._lock:
            self._nodes.clear()
            self._edges.clear()
            self._total_flows = 0


_manager = TopologyManager()


def get_topology_manager() -> TopologyManager:
    return _manager
