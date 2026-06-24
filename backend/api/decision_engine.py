"""
Decision Engine — maps detection + trust + topology signals → enforcement action.

Pipeline stage: TRUST_SCORE → (this) → TOPOLOGY / DASHBOARD

Final action ∈ {Allow, Restrict, Alert, Quarantine, Block}, chosen from:
  - final prediction (attack class) and risk level
  - model confidence
  - trust score / level
  - anomaly score & known/unknown status
  - repeated suspicious events (per-entity streak + history)
  - topology criticality (position/role of the node in the graph)
"""

from collections import defaultdict

# Per-entity consecutive high-severity counter
_critical_streak: dict = defaultdict(int)

BLOCK_THRESHOLD = 3            # consecutive critical events → Block
LOW_CONF_ATTACK = 0.45        # attacks below this confidence are treated cautiously

_RISK_ORDER = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}


def make_decision(
    predicted_label: str,
    risk_level: str,
    trust_level: str,
    confidence: float = 0.0,
    anomaly_score: float = 0.0,
    known_or_unknown: str = "Known",
    topology_criticality: str = "Low",
    repeated_events: int = 0,
    entity_id: str = "default",
) -> dict:
    """Determine the enforcement action for a detected flow."""
    label_upper = (predicted_label or "").upper()
    is_benign = label_upper in ("BENIGN", "BENIGNTRAFFIC", "")
    is_attack = not is_benign
    topo_crit = _RISK_ORDER.get(topology_criticality, 0)

    # Track consecutive critical events
    if risk_level == "Critical" and is_attack:
        _critical_streak[entity_id] += 1
    elif is_benign:
        _critical_streak[entity_id] = 0
    streak = _critical_streak[entity_id]

    # Rule 1 — Repeated Critical (streak or long history) → Block
    if is_attack and (streak >= BLOCK_THRESHOLD or repeated_events >= 8) and trust_level == "Low Trust":
        return _d("Block", "BLOCK",
                  f"Repeated critical threat from {entity_id} "
                  f"(streak={streak}, history={repeated_events}). Blocking entity.")

    # Rule 2 — Unknown / zero-day with strong anomaly → Quarantine
    if known_or_unknown == "Unknown" and anomaly_score >= 0.6:
        return _d("Quarantine", "CRITICAL",
                  f"Unknown/zero-day pattern '{predicted_label}' "
                  f"(anomaly={anomaly_score:.2f}). Quarantining for analysis.")

    # Rule 3 — Critical risk, Low trust, or critical topology position → Quarantine
    if is_attack and (risk_level == "Critical" or trust_level == "Low Trust" or topo_crit >= 3):
        return _d("Quarantine", "CRITICAL",
                  f"Critical risk '{predicted_label}' / low trust / critical topology "
                  f"position. Quarantining traffic.")

    # Rule 4 — Low-confidence attack → Restrict (avoid over-blocking on uncertainty)
    if is_attack and confidence < LOW_CONF_ATTACK and anomaly_score < 0.5:
        return _d("Restrict", "WARNING",
                  f"Low-confidence detection of '{predicted_label}' "
                  f"({confidence:.2f}). Restricting pending more evidence.")

    # Rule 5 — High risk or unknown/suspicious → Alert
    if risk_level == "High" or known_or_unknown in ("Unknown", "Suspicious"):
        return _d("Alert", "HIGH",
                  f"High-risk / suspicious activity '{predicted_label}'. Security team alerted.")

    # Rule 6 — Medium risk or medium trust or elevated topology → Restrict
    if risk_level == "Medium" or trust_level == "Medium Trust" or topo_crit >= 2:
        return _d("Restrict", "WARNING",
                  "Medium risk / trust / topology exposure. Applying traffic restrictions.")

    # Rule 7 — Benign with high trust → Allow
    if is_benign and trust_level == "High Trust":
        return _d("Allow", "INFO",
                  "Traffic classified BENIGN with high trust. Allowing connection.")

    # Rule 8 — Low risk with high trust → Allow
    if risk_level == "Low" and trust_level == "High Trust":
        return _d("Allow", "INFO",
                  f"Low risk '{predicted_label}' with high trust. Allowing connection.")

    # Default — restrict as a precaution
    return _d("Restrict", "WARNING",
              f"Unclassified risk/trust combination for '{predicted_label}'. Restricting.")


def _d(action: str, policy: str, reason: str) -> dict:
    return {"action": action, "reason": reason, "policy_level": policy}


def reset_streak(entity_id: str):
    _critical_streak.pop(entity_id, None)


if __name__ == "__main__":
    cases = [
        ("BenignTraffic", "Low", "High Trust", 0.99, 0.0, "Known", "Low", 0),
        ("DDoS-SYN_Flood", "High", "Medium Trust", 0.95, 0.1, "Known", "Medium", 2),
        ("Mirai-udpplain", "Critical", "Low Trust", 0.9, 0.3, "Known", "High", 5),
        ("Unknown", "High", "Low Trust", 0.3, 0.8, "Unknown", "Critical", 9),
    ]
    for c in cases:
        d = make_decision(*c, entity_id="10.0.0.9")
        print(f"[{c[0]:<16}] risk={c[1]:<8} → {d['action']:<10} ({d['policy_level']})")
