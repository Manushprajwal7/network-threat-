"""
Live packet capture using tshark subprocess directly.

Captures both IPv4 and IPv6 traffic from the selected interface.
Parses tshark -T fields output line-by-line; no PyShark / asyncio.
"""

import logging
import subprocess
import threading
import time
from typing import Callable, Optional

log = logging.getLogger(__name__)

# ── tshark field definitions ───────────────────────────────────────────────────
# FIELD ORDER MUST match TSHARK_FIELDS list exactly.

_F_TIME      = 0   # frame.time_epoch
_F_IP4_SRC   = 1   # ip.src
_F_IP4_DST   = 2   # ip.dst
_F_IP4_PROTO = 3   # ip.proto        (6=TCP, 17=UDP, 1=ICMP)
_F_IP6_SRC   = 4   # ipv6.src
_F_IP6_DST   = 5   # ipv6.dst
_F_IP6_NXT   = 6   # ipv6.nxt        (6=TCP, 17=UDP, 58=ICMPv6)
_F_TCP_SRCP  = 7   # tcp.srcport
_F_TCP_DSTP  = 8   # tcp.dstport
_F_UDP_SRCP  = 9   # udp.srcport
_F_UDP_DSTP  = 10  # udp.dstport
_F_FRAMELEN  = 11  # frame.len
_F_TCPFLAGS  = 12  # tcp.flags
_F_WINSIZE   = 13  # tcp.window_size
_F_TTL       = 14  # ip.ttl
_F_DATALEN   = 15  # data.len (application payload length)

TSHARK_FIELDS = [
    "frame.time_epoch",
    "ip.src",
    "ip.dst",
    "ip.proto",
    "ipv6.src",
    "ipv6.dst",
    "ipv6.nxt",
    "tcp.srcport",
    "tcp.dstport",
    "udp.srcport",
    "udp.dstport",
    "frame.len",
    "tcp.flags",
    "tcp.window_size",
    "ip.ttl",
    "data.len",
]


class PacketSniffer:
    """
    Captures live packets via tshark subprocess (IPv4 + IPv6).

    Usage (in a background thread):
        sniffer = PacketSniffer(interface="5", packet_callback=my_fn)
        sniffer.start()   # blocks until stop() is called
    """

    def __init__(
        self,
        interface: str,
        packet_callback: Optional[Callable[[dict], None]] = None,
    ):
        self._interface = interface
        self._callback = packet_callback
        self._running = False
        self._process: Optional[subprocess.Popen] = None
        self._error: Optional[str] = None
        self._packet_count = 0   # IP/IPv6 packets successfully parsed
        self._raw_count = 0      # all non-empty tshark output lines

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def packet_count(self) -> int:
        return self._packet_count

    @property
    def raw_count(self) -> int:
        return self._raw_count

    @property
    def error(self) -> Optional[str]:
        return self._error

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self):
        """
        Begin capture. Blocks until stop() is called or tshark exits.
        Must be run in a daemon thread.
        """
        from .interface_utils import get_tshark_path
        tshark_path = get_tshark_path()
        if not tshark_path:
            self._error = "tshark not found — install Wireshark"
            log.error(self._error)
            return

        cmd = _build_cmd(tshark_path, self._interface)
        log.info(f"Starting: {' '.join(cmd)}")
        self._running = True
        self._error = None

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            stderr_lines: list = []
            threading.Thread(
                target=_drain_stderr,
                args=(self._process.stderr, stderr_lines),
                daemon=True,
            ).start()

            for raw_line in self._process.stdout:
                if not self._running:
                    break
                line = raw_line.rstrip("\n\r")
                if not line.strip():
                    continue
                self._raw_count += 1
                packet_info = _parse_line(line)
                if packet_info is None:
                    continue
                self._packet_count += 1
                if self._callback:
                    try:
                        self._callback(packet_info)
                    except Exception as cb_err:
                        log.warning(f"Callback error: {cb_err}")

            # tshark finished — surface any error from stderr
            try:
                self._process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                pass

            rc = self._process.returncode
            if rc not in (0, None, -15) and stderr_lines:
                err = next(
                    (l for l in reversed(stderr_lines) if any(
                        kw in l for kw in ("rror", "annot", "No such", "ermission", "nvalid", "ailed")
                    )),
                    stderr_lines[-1],
                )
                self._error = err
                log.error(f"tshark exited {rc}: {err}")

        except FileNotFoundError:
            self._error = f"tshark not found at '{tshark_path}'"
            log.error(self._error)
        except Exception as exc:
            if self._running:
                self._error = str(exc)
                log.error(f"Capture error: {exc}")
        finally:
            self._running = False

    def stop(self):
        self._running = False
        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass


# ── Command builder ────────────────────────────────────────────────────────────

def _build_cmd(tshark_path: str, interface: str) -> list:
    cmd = [tshark_path, "-i", interface]
    for field in TSHARK_FIELDS:
        cmd += ["-e", field]
    cmd += [
        "-T", "fields",
        "-E", "separator=\t",
        "-E", "occurrence=f",
        "-l",   # line-buffered
        "-q",   # suppress packet-count summary to stdout
    ]
    return cmd


# ── Line parser ────────────────────────────────────────────────────────────────

def _parse_line(line: str) -> Optional[dict]:
    """
    Parse one tab-delimited tshark fields line into a packet dict.
    Returns None for non-IP / non-IPv6 frames or parse failures.
    """
    try:
        parts = line.split("\t")
        while len(parts) < len(TSHARK_FIELDS):
            parts.append("")

        # ── IP layer (IPv4 takes priority; fall back to IPv6) ─────────────
        src_ip = parts[_F_IP4_SRC].strip() or parts[_F_IP6_SRC].strip() or None
        dst_ip = parts[_F_IP4_DST].strip() or parts[_F_IP6_DST].strip() or None

        if not src_ip and not dst_ip:
            return None   # ARP, STP, 802.11 management — skip

        # Protocol number (IPv4 or IPv6 next-header)
        proto_raw = parts[_F_IP4_PROTO].strip() or parts[_F_IP6_NXT].strip()
        proto_num = _safe_int(proto_raw)

        # ── Transport ports ───────────────────────────────────────────────
        tcp_src = _safe_int(parts[_F_TCP_SRCP])
        tcp_dst = _safe_int(parts[_F_TCP_DSTP])
        udp_src = _safe_int(parts[_F_UDP_SRCP])
        udp_dst = _safe_int(parts[_F_UDP_DSTP])

        src_port = tcp_src if tcp_src is not None else udp_src
        dst_port = tcp_dst if tcp_dst is not None else udp_dst

        # ── Protocol name ─────────────────────────────────────────────────
        if proto_num == 6 or tcp_src is not None or tcp_dst is not None:
            protocol = "TCP"
        elif proto_num == 17 or udp_src is not None or udp_dst is not None:
            protocol = "UDP"
        elif proto_num in (1, 58):
            protocol = "ICMP"
        elif proto_num is not None:
            protocol = f"IP-{proto_num}"
        else:
            protocol = "UNKNOWN"

        # Application-layer overrides based on well-known ports
        if dst_port == 53 or src_port == 53:
            protocol = "DNS"
        elif dst_port in (80, 8080):
            protocol = "HTTP"
        elif dst_port == 443:
            protocol = "HTTPS"

        flags_raw = parts[_F_TCPFLAGS].strip()

        return {
            "timestamp":     _safe_float(parts[_F_TIME]) or time.time(),
            "src_ip":        src_ip,
            "dst_ip":        dst_ip,
            "src_port":      src_port,
            "dst_port":      dst_port,
            "protocol":      protocol,
            "proto_num":     proto_num,
            "packet_length": _safe_int(parts[_F_FRAMELEN]) or 0,
            "ttl":           _safe_int(parts[_F_TTL]),
            "tcp_flags":     _decode_tcp_flags(flags_raw) if flags_raw else None,
            "window_size":   _safe_int(parts[_F_WINSIZE]),
            "payload_length": _safe_int(parts[_F_DATALEN]) or 0,
        }
    except Exception as exc:
        log.debug(f"Line parse error: {exc} | {line!r}")
        return None


# ── stderr reader ──────────────────────────────────────────────────────────────

def _drain_stderr(stderr, lines: list):
    try:
        for line in stderr:
            s = line.strip()
            if not s:
                continue
            lines.append(s)
            if any(kw in s for kw in ("rror", "annot", "No such", "ermission", "nvalid", "ailed")):
                log.warning(f"tshark: {s}")
            else:
                log.debug(f"tshark: {s}")
    except Exception:
        pass


# ── Helpers ────────────────────────────────────────────────────────────────────

def _safe_int(val) -> Optional[int]:
    if val is None or val == "":
        return None
    try:
        return int(str(val).strip())
    except (TypeError, ValueError):
        return None


def _safe_float(val) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        return float(str(val).strip())
    except (TypeError, ValueError):
        return None


def _decode_tcp_flags(flags_str: str) -> str:
    try:
        val = int(flags_str, 16)
        parts = []
        if val & 0x01: parts.append("FIN")
        if val & 0x02: parts.append("SYN")
        if val & 0x04: parts.append("RST")
        if val & 0x08: parts.append("PSH")
        if val & 0x10: parts.append("ACK")
        if val & 0x20: parts.append("URG")
        return "|".join(parts) if parts else flags_str
    except (ValueError, TypeError):
        return str(flags_str)
