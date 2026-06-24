"""
Trust Manager — composite trust score for a network entity (source IP/device).

Pipeline stage: ML_DETECTION → (this) → SECURITY_DECISION

    Trust Score = α·UserTrust + β·DeviceTrust + γ·BehaviorTrust
    α = 0.3, β = 0.3, γ = 0.4

Trust now reflects ALL detection signals, not just risk level:
  - predicted attack type / risk level
  - model confidence (confident attacks hurt trust more)
  - anomaly score (device behaving abnormally → device trust drops)
  - repeated suspicious behavior (escalating behavior-trust penalty)
  - source-device history
  - topology risk position (risky graph position lowers trust)

Trust levels:  ≥80 High · ≥50 Medium · <50 Low
"""

import time
from collections import defaultdict, deque

ALPHA = 0.3   # user component weight
BETA  = 0.3   # device component weight
GAMMA = 0.4   # behavior component weight

HISTORY_WINDOW = 100

# Base penalty per severity (scaled by the various signals below)
_SEVERITY_PENALTY = {"Low": 0, "Medium": 12, "High": 26, "Critical": 42}
_TOPO_PENALTY     = {"Low": 0, "Medium": 5, "High": 12, "Critical": 20}


def _trust_level(score: float) -> str:
    if score >= 80:
        return "High Trust"
    if score >= 50:
        return "Medium Trust"
    return "Low Trust"


class TrustManager:
    """Stateful per-entity trust tracker."""

    def __init__(self):
        # entity → deque of event dicts {ts, risk, is_attack, anomaly, confidence}
        self._history: dict = defaultdict(lambda: deque(maxlen=HISTORY_WINDOW))
        self._user_trust: dict = defaultdict(lambda: 100.0)
        self._device_trust: dict = defaultdict(lambda: 100.0)

    def record_event(self, entity_id: str, risk_level: str, is_attack: bool,
                     anomaly_score: float, confidence: float):
        self._history[entity_id].append({
            "ts": time.time(),
            "risk": risk_level,
            "is_attack": is_attack,
            "anomaly": anomaly_score,
            "confidence": confidence,
        })

    def repeated_attacks(self, entity_id: str) -> int:
        """Number of attack events currently held in the entity's history."""
        return sum(1 for e in self._history[entity_id] if e["is_attack"])

    def _behavior_trust(self, entity_id: str) -> float:
        """Behavior trust from recent history — escalates with repeated attacks."""
        history = self._history[entity_id]
        if not history:
            return 100.0
        score = 100.0
        consecutive = 0
        for e in history:
            base = _SEVERITY_PENALTY.get(e["risk"], 0)
            if e["is_attack"]:
                consecutive += 1
                # Escalating penalty for repeated suspicious behavior
                score -= base * 0.5 * (1 + 0.15 * consecutive)
                score -= e["anomaly"] * 10.0
            else:
                consecutive = max(0, consecutive - 1)
                score += 1.0   # slow recovery on benign traffic
        return max(0.0, min(100.0, score))

    def compute_trust(
        self,
        entity_id: str = "default",
        predicted_label: str = "BENIGN",
        risk_level: str = "Low",
        confidence: float = 0.0,
        anomaly_score: float = 0.0,
        is_attack: bool = False,
        topology_risk: str = "Low",
        record: bool = True,
    ) -> dict:
        if record:
            self.record_event(entity_id, risk_level, is_attack, anomaly_score, confidence)

        sev = _SEVERITY_PENALTY.get(risk_level, 0)
        topo = _TOPO_PENALTY.get(topology_risk, 0)

        # User trust: drops with confident attacks
        if is_attack:
            self._user_trust[entity_id] = max(
                0.0, self._user_trust[entity_id] - sev * ALPHA * (0.5 + confidence)
            )
        user_trust = self._user_trust[entity_id]

        # Device trust: drops with anomaly + topology risk
        self._device_trust[entity_id] = max(
            0.0, self._device_trust[entity_id] - (anomaly_score * 15.0) - (topo * BETA)
        )
        device_trust = self._device_trust[entity_id]

        # Behavior trust: derived from rolling history
        behavior_trust = self._behavior_trust(entity_id)

        final = ALPHA * user_trust + BETA * device_trust + GAMMA * behavior_trust
        final = round(max(0.0, min(100.0, final)), 2)

        return {
            "entity_id":         entity_id,
            "user_trust":        round(user_trust, 2),
            "device_trust":      round(device_trust, 2),
            "behavior_trust":    round(behavior_trust, 2),
            "final_trust_score": final,
            "trust_level":       _trust_level(final),
            "repeated_attacks":  self.repeated_attacks(entity_id),
        }

    def reset_entity(self, entity_id: str):
        self._history.pop(entity_id, None)
        self._user_trust.pop(entity_id, None)
        self._device_trust.pop(entity_id, None)


_manager = TrustManager()


def compute_trust(entity_id: str = "default", predicted_label: str = "BENIGN",
                  risk_level: str = "Low", confidence: float = 0.0,
                  anomaly_score: float = 0.0, is_attack: bool = False,
                  topology_risk: str = "Low", record: bool = True) -> dict:
    """Convenience wrapper around the singleton TrustManager."""
    return _manager.compute_trust(
        entity_id=entity_id, predicted_label=predicted_label, risk_level=risk_level,
        confidence=confidence, anomaly_score=anomaly_score, is_attack=is_attack,
        topology_risk=topology_risk, record=record,
    )


def get_trust_manager() -> TrustManager:
    return _manager


if __name__ == "__main__":
    mgr = TrustManager()
    for risk, atk in [("Low", False), ("High", True), ("Critical", True), ("Critical", True)]:
        r = mgr.compute_trust("10.0.0.5", risk_level=risk, is_attack=atk,
                              confidence=0.9, anomaly_score=0.3 if atk else 0.0)
        print(f"[{risk:<8} atk={atk}] final={r['final_trust_score']:6.2f} "
              f"level={r['trust_level']:<12} behaviour={r['behavior_trust']:.1f} "
              f"repeats={r['repeated_attacks']}")
