"""
Utilities for detecting tshark installation and listing available network interfaces.

Supports Windows tshark installed with Wireshark, PATH-accessible tshark,
and the TSHARK_PATH environment variable override.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# Common tshark paths on Windows
_TSHARK_WINDOWS_PATHS = [
    r"C:\Program Files\Wireshark\tshark.exe",
    r"C:\Program Files (x86)\Wireshark\tshark.exe",
]


def get_tshark_path() -> Optional[str]:
    """Return the path to a working tshark executable, or None if not found."""
    # 1. Environment variable override
    env_path = os.environ.get("TSHARK_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    # 2. Check if tshark is on the system PATH
    try:
        result = subprocess.run(
            ["tshark", "--version"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0:
            return "tshark"
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
        pass

    # 3. Common Windows install locations
    if sys.platform == "win32":
        for path in _TSHARK_WINDOWS_PATHS:
            if Path(path).exists():
                return path

    return None


def check_tshark_installed() -> tuple[bool, str]:
    """
    Check whether tshark is available.

    Returns
    -------
    (True, path)   – tshark found at `path`
    (False, error) – tshark not found; `error` is a human-readable message
    """
    path = get_tshark_path()
    if path:
        return True, path
    return (
        False,
        "tshark not found. Install Wireshark from https://www.wireshark.org/ "
        "or set the TSHARK_PATH environment variable.",
    )


def list_interfaces() -> list[dict]:
    """
    Return available network interfaces reported by tshark -D.

    Each entry has:
        index  – positional index string ("1", "2", …)
        name   – friendly name (e.g. "Wi-Fi", "Ethernet")
        device – underlying device string
    """
    tshark = get_tshark_path()
    if not tshark:
        return []

    try:
        result = subprocess.run(
            [tshark, "-D"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        interfaces = []
        for line in result.stdout.strip().splitlines():
            # Format: "1. \Device\NPF_{GUID} (Wi-Fi)"  or  "1. eth0"
            parts = line.strip().split(". ", 1)
            if len(parts) != 2:
                continue
            idx, rest = parts
            # Extract friendly name from trailing parentheses if present
            if "(" in rest and rest.rstrip().endswith(")"):
                last_open = rest.rfind("(")
                name = rest[last_open + 1 : rest.rfind(")")]
                device = rest[:last_open].strip()
            else:
                name = rest.strip()
                device = rest.strip()
            interfaces.append(
                {
                    "index": idx.strip(),
                    "name": name or device,
                    "device": device,
                }
            )
        return interfaces
    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError) as e:
        log.warning(f"list_interfaces failed: {e}")
        return []


def get_default_interface() -> Optional[str]:
    """Return the friendly name of the preferred default interface."""
    iface = get_default_interface_info()
    return iface["name"] if iface else None


def get_default_interface_index() -> Optional[str]:
    """Return the numeric index of the preferred default interface for tshark -i."""
    iface = get_default_interface_info()
    return iface["index"] if iface else None


def get_default_interface_info() -> Optional[dict]:
    """Return the full info dict for the best default capture interface."""
    interfaces = list_interfaces()
    if not interfaces:
        return None

    _SKIP = ("loopback", "bluetooth", "local area connection", "etw")

    def _is_virtual(name: str) -> bool:
        nl = name.lower()
        return any(k in nl for k in _SKIP)

    # Prefer Wi-Fi / wireless
    for iface in interfaces:
        nl = iface["name"].lower()
        if any(k in nl for k in ("wi-fi", "wifi", "wireless", "wlan")) and not _is_virtual(iface["name"]):
            return iface

    # Then Ethernet
    for iface in interfaces:
        nl = iface["name"].lower()
        if "ethernet" in nl and not _is_virtual(iface["name"]):
            return iface

    # First non-virtual adapter
    for iface in interfaces:
        if not _is_virtual(iface["name"]):
            return iface

    return interfaces[0]
