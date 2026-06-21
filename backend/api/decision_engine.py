"""
Decision Engine — maps (risk_level, trust_level, history) → enforcement action.

Decision matrix:
    BENIGN  + High Trust        → Allow
    Medium Risk or Medium Trust → Restrict
    High Risk                   → Alert
    Critical Risk or Low Trust  → Quarantine
    Repeated Critical           → Block
"""

from collections import defaultdict

# Per-entity consecutive Critical event counter
_critical_streak: dict[str, int] = defaultdict(int)

# How many consecutive Critical events trigger a Block
BLOCK_THRESHOLD = 3

# ── Decision rules (evaluated top-to-bottom, first match wins) ─────────────────

def make_decision(
    predicted_label: str,
    risk_level: str,
    trust_level: str,
    entity_id: str = "default",
) -> dict:
    """
    Determine the enforcement action for a detected flow.

    Parameters
    ----------
    predicted_label : Attack class string (e.g. "BENIGN", "DoS", "Botnet")
    risk_level      : Low / Medium / High / Critical
    trust_level     : High Trust / Medium Trust / Low Trust
    entity_id       : Entity key for streak tracking

    Returns
    -------
    dict with keys:
        action       – Allow / Restrict / Alert / Quarantine / Block
        reason       – Human-readable explanation
        policy_level – INFO / WARNING / HIGH / CRITICAL / BLOCK
    """
    label_upper = predicted_label.upper()

    # Track consecutive critical events
    if risk_level == "Critical":
        _critical_streak[entity_id] += 1
    else:
        _critical_streak[entity_id] = 0

    streak = _critical_streak[entity_id]

    # Rule 1 — Repeated Critical → Block
    if streak >= BLOCK_THRESHOLD:
        return {
            "action":       "Block",
            "reason":       f"Repeated Critical threat detected ({streak} consecutive events from {entity_id}). Blocking entity.",
            "policy_level": "BLOCK",
        }

    # Rule 2 — Critical Risk or Low Trust → Quarantine
    if risk_level == "Critical" or trust_level == "Low Trust":
        return {
            "action":       "Quarantine",
            "reason":       f"Critical risk '{predicted_label}' detected or entity trust is Low. Quarantining traffic.",
            "policy_level": "CRITICAL",
        }

    # Rule 3 — High Risk → Alert
    if risk_level == "High":
        return {
            "action":       "Alert",
            "reason":       f"High-risk attack '{predicted_label}' detected. Security team alerted.",
            "policy_level": "HIGH",
        }

    # Rule 4 — Medium Risk or Medium Trust → Restrict
    if risk_level == "Medium" or trust_level == "Medium Trust":
        return {
            "action":       "Restrict",
            "reason":       f"Medium risk or medium trust level. Applying traffic restrictions.",
            "policy_level": "WARNING",
        }

    # Rule 5 — BENIGN + High Trust → Allow
    if label_upper == "BENIGN" and trust_level == "High Trust":
        return {
            "action":       "Allow",
            "reason":       "Traffic identified as BENIGN with high trust. Allowing connection.",
            "policy_level": "INFO",
        }

    # Fallback — any Low Risk with High Trust still allows
    if risk_level == "Low" and trust_level == "High Trust":
        return {
            "action":       "Allow",
            "reason":       f"Low risk '{predicted_label}' with high trust. Allowing connection.",
            "policy_level": "INFO",
        }

    # Default — restrict anything else
    return {
        "action":       "Restrict",
        "reason":       f"Unclassified risk/trust combination for '{predicted_label}'. Applying restrictions as precaution.",
        "policy_level": "WARNING",
    }


def reset_streak(entity_id: str):
    """Reset the critical event streak for an entity (e.g. after manual clearance)."""
    _critical_streak.pop(entity_id, None)


if __name__ == "__main__":
    test_cases = [
        ("BENIGN",          "Low",      "High Trust"),
        ("DoS",             "High",     "High Trust"),
        ("DDoS",            "High",     "Medium Trust"),
        ("Botnet",          "Critical", "Low Trust"),
        ("Web Attack",      "Critical", "Medium Trust"),
        ("PortScan",        "High",     "Low Trust"),
        ("Botnet",          "Critical", "Low Trust"),   # streak 2
        ("Botnet",          "Critical", "Low Trust"),   # streak 3 → Block
    ]
    entity = "10.0.0.5"
    for label, risk, trust in test_cases:
        d = make_decision(label, risk, trust, entity_id=entity)
        print(f"[{label:<15}] risk={risk:<8} trust={trust:<12} → {d['action']} ({d['policy_level']})")
