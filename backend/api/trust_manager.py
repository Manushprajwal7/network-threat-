"""
Trust Manager — computes a composite trust score for a network entity.

Formula:
    Trust Score = α(User Trust) + β(Device Trust) + γ(Behavior Trust)
    α = 0.3, β = 0.3, γ = 0.4

Trust levels:
    80–100 → High Trust
    50–79  → Medium Trust
    0–49   → Low Trust
"""

import time
from collections import defaultdict, deque

# ── Weights ────────────────────────────────────────────────────────────────────
ALPHA = 0.3   # user component weight
BETA  = 0.3   # device component weight
GAMMA = 0.4   # behavior component weight

# How many recent events to track per entity
HISTORY_WINDOW = 50

# Score penalty per severity level (applied to behavior component)
_SEVERITY_PENALTY = {
    "Low":      0,
    "Medium":   10,
    "High":     25,
    "Critical": 40,
}

# Trust level thresholds
def _trust_level(score: float) -> str:
    if score >= 80:
        return "High Trust"
    if score >= 50:
        return "Medium Trust"
    return "Low Trust"


class TrustManager:
    """
    Stateful trust manager that tracks per-entity history and updates scores.
    Entities are identified by a string key (e.g. IP address or session ID).
    """

    def __init__(self):
        # Per-entity deque of (timestamp, risk_level) tuples
        self._history: dict[str, deque] = defaultdict(lambda: deque(maxlen=HISTORY_WINDOW))
        # Cached base trust scores (could be loaded from a DB in production)
        self._user_trust: dict[str, float] = defaultdict(lambda: 100.0)
        self._device_trust: dict[str, float] = defaultdict(lambda: 100.0)

    def record_event(self, entity_id: str, risk_level: str):
        """Record a detection event for an entity."""
        self._history[entity_id].append((time.time(), risk_level))

    def _compute_behavior_trust(self, entity_id: str) -> float:
        """Derive behavior trust from recent event history."""
        history = self._history[entity_id]
        if not history:
            return 100.0

        score = 100.0
        for _ts, risk in history:
            score -= _SEVERITY_PENALTY.get(risk, 0) * 0.5  # rolling decay factor

        return max(0.0, min(100.0, score))

    def compute_trust(
        self,
        entity_id: str = "default",
        risk_level: str = "Low",
        record: bool = True,
    ) -> dict:
        """
        Compute and return full trust breakdown for an entity.

        Parameters
        ----------
        entity_id  : Identifier for the entity (IP, user-id, session, etc.)
        risk_level : Risk level of the current event (Low/Medium/High/Critical)
        record     : Whether to record this event in the entity's history
        """
        if record:
            self.record_event(entity_id, risk_level)

        penalty = _SEVERITY_PENALTY.get(risk_level, 0)

        user_trust   = max(0.0, self._user_trust[entity_id] - penalty * ALPHA)
        device_trust = max(0.0, self._device_trust[entity_id] - penalty * BETA)
        behavior_trust = self._compute_behavior_trust(entity_id)

        # Update cached values
        self._user_trust[entity_id]   = user_trust
        self._device_trust[entity_id] = device_trust

        final_score = (
            ALPHA * user_trust
            + BETA  * device_trust
            + GAMMA * behavior_trust
        )
        final_score = round(max(0.0, min(100.0, final_score)), 2)

        return {
            "entity_id":         entity_id,
            "user_trust":        round(user_trust, 2),
            "device_trust":      round(device_trust, 2),
            "behavior_trust":    round(behavior_trust, 2),
            "final_trust_score": final_score,
            "trust_level":       _trust_level(final_score),
        }

    def reset_entity(self, entity_id: str):
        """Reset all trust state for an entity (e.g. after manual review)."""
        self._history.pop(entity_id, None)
        self._user_trust.pop(entity_id, None)
        self._device_trust.pop(entity_id, None)


# Module-level singleton for use by Flask app
_manager = TrustManager()


def compute_trust(entity_id: str = "default", risk_level: str = "Low", record: bool = True) -> dict:
    """Convenience wrapper around the singleton TrustManager."""
    return _manager.compute_trust(entity_id=entity_id, risk_level=risk_level, record=record)


if __name__ == "__main__":
    mgr = TrustManager()
    for risk in ["Low", "Medium", "High", "Critical", "Critical"]:
        result = mgr.compute_trust(entity_id="192.168.1.10", risk_level=risk)
        print(
            f"[{risk:<8}] score={result['final_trust_score']:6.2f} "
            f"level='{result['trust_level']}' "
            f"behavior={result['behavior_trust']:.2f}"
        )
