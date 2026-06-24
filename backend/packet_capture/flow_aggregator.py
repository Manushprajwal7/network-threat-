"""
Flow Aggregator — groups captured packets into bidirectional flows.

Pipeline stage: PACKET_CAPTURE → (this) → FEATURE_EXTRACTION

Packets arriving from the sniffer are buffered into flows keyed by the
canonical 5-tuple:

    (protocol, {src_ip:src_port, dst_ip:dst_port})

The endpoint set is order-independent so that A→B and B→A map to the same
flow. The first packet seen for a flow defines the *initiator* (forward
direction); subsequent packets are tagged forward/backward accordingly.

Each interval the CaptureManager calls `collect_window()` which returns one
flow-record dict per flow that saw traffic in the window, then clears the
per-window accumulators. Flows idle beyond FLOW_TIMEOUT are evicted.

This module performs NO machine learning — it only accumulates real packet
statistics needed by the CICIoT2023 feature extractor.
"""

import logging
import math
import threading
import time
from typing import Optional

log = logging.getLogger(__name__)

# A flow with no packets for this many seconds is evicted.
FLOW_TIMEOUT = 30.0
# Hard cap on per-window packet samples retained per flow (memory guard).
MAX_SAMPLES_PER_FLOW = 20_000
# Hard cap on number of concurrently tracked flows (memory guard).
MAX_FLOWS = 4_000

# Well-known port → application protocol presence flags
_PORT_PROTO = {
    80: "HTTP", 8080: "HTTP", 8000: "HTTP",
    443: "HTTPS", 8443: "HTTPS",
    53: "DNS",
    23: "Telnet",
    25: "SMTP", 587: "SMTP", 465: "SMTP",
    22: "SSH",
    6667: "IRC", 6697: "IRC",
    67: "DHCP", 68: "DHCP",
}


def _flag_set(flags_str: Optional[str]) -> set:
    """Decode a 'SYN|ACK' style flag string into a set of flag names."""
    if not flags_str:
        return set()
    return {f.strip().upper() for f in str(flags_str).split("|") if f.strip()}


class _Flow:
    """Accumulates per-window statistics for one bidirectional flow."""

    __slots__ = (
        "protocol", "proto_num",
        "init_ip", "init_port", "resp_ip", "resp_port",
        "created", "last_seen",
        "w_first_ts", "w_last_ts", "w_prev_ts",
        "fwd_sizes", "bwd_sizes", "all_sizes",
        "header_bytes", "ttl_sum", "ttl_n",
        "iats", "app_protocols",
        "fin", "syn", "rst", "psh", "ack", "urg", "ece", "cwr",
        "window_packets",
    )

    def __init__(self, packet: dict):
        self.protocol: str = packet.get("protocol") or "UNKNOWN"
        self.proto_num: int = int(packet.get("proto_num") or _guess_proto_num(self.protocol))
        self.init_ip: str = packet.get("src_ip") or "0.0.0.0"
        self.init_port: int = int(packet.get("src_port") or 0)
        self.resp_ip: str = packet.get("dst_ip") or "0.0.0.0"
        self.resp_port: int = int(packet.get("dst_port") or 0)
        self.created: float = time.time()
        self.last_seen: float = self.created
        self._reset_window()

    def _reset_window(self):
        self.w_first_ts: Optional[float] = None
        self.w_last_ts: Optional[float] = None
        self.w_prev_ts: Optional[float] = None
        self.fwd_sizes: list = []
        self.bwd_sizes: list = []
        self.all_sizes: list = []
        self.header_bytes: int = 0
        self.ttl_sum: float = 0.0
        self.ttl_n: int = 0
        self.iats: list = []
        self.app_protocols: set = set()
        self.fin = self.syn = self.rst = self.psh = 0
        self.ack = self.urg = self.ece = self.cwr = 0
        self.window_packets: int = 0

    def add(self, packet: dict):
        ts = float(packet.get("timestamp") or time.time())
        size = int(packet.get("packet_length") or 0)
        self.last_seen = time.time()

        if self.window_packets >= MAX_SAMPLES_PER_FLOW:
            # Still update timing/counters but stop growing sample lists.
            self.w_last_ts = ts
            self.window_packets += 1
            return

        # Direction relative to initiator
        is_forward = (
            (packet.get("src_ip") == self.init_ip)
            and (int(packet.get("src_port") or 0) == self.init_port)
        )

        if size > 0:
            self.all_sizes.append(size)
            (self.fwd_sizes if is_forward else self.bwd_sizes).append(size)

        # Inter-arrival time within the window
        if self.w_prev_ts is not None:
            dt = ts - self.w_prev_ts
            if dt >= 0:
                self.iats.append(dt)
        self.w_prev_ts = ts
        if self.w_first_ts is None:
            self.w_first_ts = ts
        self.w_last_ts = ts

        # Header length approximation: TCP=20, UDP=8, ICMP=8, else 20 + IP(20)
        proto = (packet.get("protocol") or "").upper()
        if proto == "TCP" or self.proto_num == 6:
            self.header_bytes += 40
        elif proto == "UDP" or self.proto_num == 17:
            self.header_bytes += 28
        else:
            self.header_bytes += 28

        ttl = packet.get("ttl")
        if ttl is not None:
            self.ttl_sum += float(ttl)
            self.ttl_n += 1

        # Application protocol presence (from ports)
        for p in (int(packet.get("src_port") or 0), int(packet.get("dst_port") or 0)):
            app = _PORT_PROTO.get(p)
            if app:
                self.app_protocols.add(app)

        # TCP flags
        flags = _flag_set(packet.get("tcp_flags"))
        if "FIN" in flags: self.fin += 1
        if "SYN" in flags: self.syn += 1
        if "RST" in flags: self.rst += 1
        if "PSH" in flags: self.psh += 1
        if "ACK" in flags: self.ack += 1
        if "URG" in flags: self.urg += 1
        if "ECE" in flags: self.ece += 1
        if "CWR" in flags: self.cwr += 1

        self.window_packets += 1

    def has_window_traffic(self) -> bool:
        return self.window_packets > 0

    def snapshot(self) -> dict:
        """Produce a flow-record dict for feature extraction, then reset window."""
        duration = 0.0
        if self.w_first_ts is not None and self.w_last_ts is not None:
            duration = max(0.0, self.w_last_ts - self.w_first_ts)

        rec = {
            "protocol": self.protocol,
            "proto_num": self.proto_num,
            "src_ip": self.init_ip,
            "src_port": self.init_port,
            "dst_ip": self.resp_ip,
            "dst_port": self.resp_port,
            "duration": duration,
            "last_ts": self.w_last_ts or self.last_seen,
            "packet_count": self.window_packets,
            "fwd_count": len(self.fwd_sizes),
            "bwd_count": len(self.bwd_sizes),
            "fwd_sizes": list(self.fwd_sizes),
            "bwd_sizes": list(self.bwd_sizes),
            "all_sizes": list(self.all_sizes),
            "header_bytes": self.header_bytes,
            "ttl_mean": (self.ttl_sum / self.ttl_n) if self.ttl_n else 0.0,
            "iats": list(self.iats),
            "app_protocols": set(self.app_protocols),
            "flags": {
                "fin": self.fin, "syn": self.syn, "rst": self.rst,
                "psh": self.psh, "ack": self.ack, "urg": self.urg,
                "ece": self.ece, "cwr": self.cwr,
            },
        }
        self._reset_window()
        return rec


def _guess_proto_num(protocol: str) -> int:
    p = (protocol or "").upper()
    if p in ("TCP", "HTTP", "HTTPS", "SSH", "SMTP", "TELNET", "IRC"):
        return 6
    if p in ("UDP", "DNS", "DHCP"):
        return 17
    if p == "ICMP":
        return 1
    return 0


def _flow_key(packet: dict):
    """Order-independent 5-tuple key (bidirectional)."""
    proto = (packet.get("protocol") or "UNKNOWN").upper()
    # Collapse app-layer names to transport class for stable keying
    if proto in ("HTTP", "HTTPS", "SSH", "SMTP", "TELNET", "IRC"):
        proto = "TCP"
    elif proto in ("DNS", "DHCP"):
        proto = "UDP"
    a = (packet.get("src_ip") or "0.0.0.0", int(packet.get("src_port") or 0))
    b = (packet.get("dst_ip") or "0.0.0.0", int(packet.get("dst_port") or 0))
    lo, hi = (a, b) if a <= b else (b, a)
    return (proto, lo, hi)


class FlowAggregator:
    """Thread-safe accumulator of packets into bidirectional flows."""

    def __init__(self):
        self._lock = threading.RLock()
        self._flows: dict = {}
        self._dropped = 0

    def add_packet(self, packet: dict):
        """Called once per captured packet (from the sniffer callback)."""
        try:
            key = _flow_key(packet)
            with self._lock:
                flow = self._flows.get(key)
                if flow is None:
                    if len(self._flows) >= MAX_FLOWS:
                        self._dropped += 1
                        return
                    flow = _Flow(packet)
                    self._flows[key] = flow
                flow.add(packet)
        except Exception as e:
            log.debug(f"[FLOW_AGGREGATOR] add_packet error: {e}")

    def collect_window(self) -> list:
        """
        Return one flow-record per flow that saw traffic this window,
        reset window accumulators, and evict idle flows.
        """
        now = time.time()
        records = []
        with self._lock:
            for key, flow in list(self._flows.items()):
                if flow.has_window_traffic():
                    records.append(flow.snapshot())
                # Evict flows idle beyond timeout
                if now - flow.last_seen > FLOW_TIMEOUT:
                    self._flows.pop(key, None)
        return records

    def active_flow_count(self) -> int:
        with self._lock:
            return len(self._flows)

    def reset(self):
        with self._lock:
            self._flows.clear()
            self._dropped = 0
