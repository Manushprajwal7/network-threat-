"""
Network Configuration Manager — Define and manage network segments.

Allows segmentation of topology by network/subnet for multi-network environments.
Stores network metadata and filtering rules.
"""

import ipaddress
import threading
from typing import List, Dict, Optional

# Default networks — adjust to your environment
DEFAULT_NETWORKS = [
    {
        "name": "LAN - Main Office",
        "id": "lan-main",
        "subnet": "192.168.1.0/24",
        "description": "Main office local network",
        "type": "internal",
    },
    {
        "name": "DMZ - Web Servers",
        "id": "dmz-web",
        "subnet": "192.168.10.0/24",
        "description": "DMZ with web-facing servers",
        "type": "dmz",
    },
    {
        "name": "LAN - Branch Office",
        "id": "lan-branch",
        "subnet": "10.0.1.0/24",
        "description": "Branch office local network",
        "type": "internal",
    },
    {
        "name": "Internal - Database",
        "id": "internal-db",
        "subnet": "10.0.10.0/24",
        "description": "Database servers network",
        "type": "internal",
    },
]


class NetworkConfig:
    def __init__(self):
        self._lock = threading.RLock()
        self.networks = []
        self._load_defaults()

    def _load_defaults(self):
        """Load default networks."""
        with self._lock:
            self.networks = DEFAULT_NETWORKS.copy()

    def get_networks(self) -> List[Dict]:
        """Return all configured networks."""
        with self._lock:
            return [
                {
                    "id": n["id"],
                    "name": n["name"],
                    "subnet": n["subnet"],
                    "description": n.get("description", ""),
                    "type": n.get("type", "internal"),
                }
                for n in self.networks
            ]

    def get_network(self, network_id: str) -> Optional[Dict]:
        """Get a specific network by ID."""
        with self._lock:
            for n in self.networks:
                if n["id"] == network_id:
                    return n
            return None

    def add_network(self, name: str, subnet: str, network_id: str = None, **kwargs) -> Dict:
        """Add a new network configuration."""
        if not network_id:
            network_id = name.lower().replace(" ", "-")

        with self._lock:
            net = {
                "id": network_id,
                "name": name,
                "subnet": subnet,
                "description": kwargs.get("description", ""),
                "type": kwargs.get("type", "internal"),
            }
            self.networks.append(net)
            return net

    def ip_in_network(self, ip: str, network_id: str) -> bool:
        """Check if an IP belongs to a network."""
        try:
            net = self.get_network(network_id)
            if not net:
                return False
            ip_obj = ipaddress.ip_address(ip.split("%")[0])
            subnet = ipaddress.ip_network(net["subnet"], strict=False)
            return ip_obj in subnet
        except ValueError:
            return False

    def get_network_for_ip(self, ip: str) -> Optional[Dict]:
        """Find which network an IP belongs to (if any)."""
        with self._lock:
            for n in self.networks:
                if self.ip_in_network(ip, n["id"]):
                    return n
            return None

    def filter_nodes_by_network(self, nodes: List[Dict], network_id: str) -> List[Dict]:
        """Filter nodes that belong to a specific network."""
        net = self.get_network(network_id)
        if not net:
            return nodes

        filtered = []
        try:
            subnet = ipaddress.ip_network(net["subnet"], strict=False)
            for node in nodes:
                try:
                    ip_obj = ipaddress.ip_address(node["id"].split("%")[0])
                    if ip_obj in subnet:
                        filtered.append(node)
                except ValueError:
                    pass
        except ValueError:
            return nodes

        return filtered

    def get_network_layout(self, network_id: str) -> Dict:
        """Get layout parameters for a network (for deterministic positioning)."""
        net = self.get_network(network_id)
        if not net:
            return {"network_id": network_id, "positions": {}}

        return {
            "network_id": network_id,
            "network_name": net["name"],
            "subnet": net["subnet"],
            "type": net.get("type", "internal"),
        }


# Global singleton
_config = NetworkConfig()


def get_network_config() -> NetworkConfig:
    return _config
