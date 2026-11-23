"""
trust_loader.py — Dynamic Trust Engine for 60,000-sample Evaluation (CICIoT2023)
Implements the Adaptive Dynamic Trust Model (ADTM) from Section 3.7 & Table 11.

ADTM formula per sample t:
    T(t) = α · S_U(t) + β · S_D(t) + γ · S_B(t) + δ · S_A(t) + λ · S_T(t)
with:
    α = 0.30 (User / Source Trust)
    β = 0.25 (Device Trust)
    γ = 0.20 (Behavioral Trust — stateful per entity, decays on attack, recovers on benign)
    δ = 0.15 (Anomaly Penalty component = 100 * (1 - anomaly_score))
    λ = 0.10 (Topology-derived Trust = 100 * (1 - tarp_risk))
"""

from pathlib import Path
import numpy as np

ALPHA = 0.30   # User / source trust
BETA  = 0.25   # Device trust
GAMMA = 0.20   # Behavioral trust
DELTA = 0.15   # Anomaly penalty
LAMBD = 0.10   # Topology penalty

BENIGN_CLASS_IDX = 1


def compute_dynamic_trust_all(anom, is_attack, tarp_risks, n_entities=600, chunk_size=100):
    """
    Computes dynamic trust scores across all 60,000 samples (600 entities x 100 samples).
    Behavioral trust S_B updates dynamically per entity:
      - Starts at 100.0 at t=0
      - On attack: drops by 2.0 (stateful penalty)
      - On benign: recovers by 1.0 (stateful recovery)
    Returns:
        trust_scores: (60000,) ndarray
        component_records: list of dicts with component contributions
    """
    n_samples = len(anom)
    trust_scores = np.zeros(n_samples, dtype=float)
    component_records = []

    for e in range(n_entities):
        start = e * chunk_size
        end = start + chunk_size
        
        # Initial states for entity e
        S_U = 100.0
        S_D = 95.0
        S_B = 100.0

        for t in range(start, end):
            # Stateful behavioral update
            if is_attack[t]:
                S_B = max(0.0, S_B - 2.0)
            else:
                S_B = min(100.0, S_B + 1.0)

            # Anomaly component
            S_A = 100.0 * (1.0 - anom[t])
            # Topology component
            S_T = 100.0 * (1.0 - tarp_risks[t])

            # Five non-zero terms
            term_src   = ALPHA * S_U
            term_dev   = BETA  * S_D
            term_behav = GAMMA * S_B
            term_anom  = DELTA * S_A
            term_topo  = LAMBD * S_T

            T_inst = term_src + term_dev + term_behav + term_anom + term_topo
            trust_scores[t] = np.clip(T_inst, 0.0, 100.0)

            if e < 10:  # store trace for diagnostic
                component_records.append({
                    "entity": e,
                    "t": t - start,
                    "T": trust_scores[t],
                    "term_src": term_src,
                    "term_dev": term_dev,
                    "term_behav": term_behav,
                    "term_anom": term_anom,
                    "term_topo": term_topo,
                })

    return trust_scores, component_records


def load_reconstructed_trust():
    """Compatibility loader returning trust scores and 60k evaluation cache."""
    root = Path(__file__).resolve().parent
    data = np.load(root / "scratch_60k_eval.npz")
    anom = data["anom"]
    conf = data["conf"]
    y_sub = data["y_sub"]
    is_attack = (y_sub != BENIGN_CLASS_IDX)

    import sys
    sys.path.insert(0, str(root))
    from topology_loader import load_tarp_risks
    tarp_risks, _ = load_tarp_risks()

    trust_scores, comp_records = compute_dynamic_trust_all(anom, is_attack, tarp_risks)

    return {
        "trust": trust_scores,
        "anom": anom,
        "conf": conf,
        "y_true": y_sub,
        "is_attack": is_attack,
        "tarp_risks": tarp_risks,
        "comp_records": comp_records,
    }


if __name__ == "__main__":
    res = load_reconstructed_trust()
    t = res["trust"]
    print("Dynamic Trust Summary:")
    print(f"  Count:          {len(t):,}")
    print(f"  Mean:           {np.mean(t):.2f}")
    print(f"  Min:            {np.min(t):.2f}")
    print(f"  Max:            {np.max(t):.2f}")
    print(f"  High (>=80):    {np.sum(t >= 80):,} ({np.mean(t >= 80)*100:.2f}%)")
    print(f"  Mod  (60-79):   {np.sum((t >= 60) & (t < 80)):,} ({np.mean((t >= 60) & (t < 80))*100:.2f}%)")
    print(f"  Low  (40-59):   {np.sum((t >= 40) & (t < 60)):,} ({np.mean((t >= 40) & (t < 60))*100:.2f}%)")
    print(f"  VLow (20-39):   {np.sum((t >= 20) & (t < 40)):,} ({np.mean((t >= 20) & (t < 40))*100:.2f}%)")
    print(f"  Crit (<20):     {np.sum(t < 20):,} ({np.mean(t < 20)*100:.2f}%)")
