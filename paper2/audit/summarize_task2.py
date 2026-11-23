import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
perms_csv = ROOT / "audit" / "outputs" / "task2_topology_confound_permutations.csv"
df_perms = pd.read_csv(perms_csv)

# Observed values from task2:
# Flows per level: {0: 13400, 1: 4600, 2: 8500, 3: 15400, 4: 17700, 5: 400}
# Attack densities: {0: 0.0, 1: 0.0, 2: 0.466, 3: 0.525584, 4: 0.997910, 5: 1.0}
# Monotonic: True
# P1 OCU: 446388
# P2-tier OCU: 974983
# P_opt OCU: 986315

obs_values = {
    "is_monotonic": 1.0,
    "ocu_p1": 446388.0,
    "ocu_p2_tier": 974983.0,
    "ocu_p_opt": 986315.0,
    "l0_flows": 13400.0,
    "l1_flows": 4600.0,
    "l2_flows": 8500.0,
    "l3_flows": 15400.0,
    "l4_flows": 17700.0,
    "l5_flows": 400.0,
    "l0_density": 0.0,
    "l1_density": 0.0,
    "l2_density": 0.4660,
    "l3_density": 0.5256,
    "l4_density": 0.9979,
    "l5_density": 1.0
}

metrics = [
    ("Monotonicity Rate", "is_monotonic"),
    ("P1 Net OCU", "ocu_p1"),
    ("P2-tier Net OCU", "ocu_p2_tier"),
    ("P_opt Net OCU", "ocu_p_opt"),
    ("L0 Flow Count", "l0_flows"),
    ("L1 Flow Count", "l1_flows"),
    ("L2 Flow Count", "l2_flows"),
    ("L3 Flow Count", "l3_flows"),
    ("L4 Flow Count", "l4_flows"),
    ("L5 Flow Count", "l5_flows"),
    ("L0 Attack Density", "l0_density"),
    ("L1 Attack Density", "l1_density"),
    ("L2 Attack Density", "l2_density"),
    ("L3 Attack Density", "l3_density"),
    ("L4 Attack Density", "l4_density"),
    ("L5 Attack Density", "l5_density"),
]

summary_rows = []
for label, col in metrics:
    obs_val = obs_values[col]
    vals = df_perms[col].dropna().astype(float)
    p_mean = float(np.mean(vals))
    p_std = float(np.std(vals))
    ci_lower = float(np.percentile(vals, 2.5))
    ci_upper = float(np.percentile(vals, 97.5))
    
    # Empirical two-sided p-value
    if p_std > 1e-12:
        p_val = float(np.mean(np.abs(vals - p_mean) >= np.abs(obs_val - p_mean)))
    else:
        p_val = 1.0 if np.isclose(obs_val, p_mean) else 0.0
        
    summary_rows.append({
        "metric": label,
        "observed_round_robin": round(obs_val, 4),
        "perm_mean": round(p_mean, 4),
        "perm_std": round(p_std, 4),
        "perm_ci95_lower": round(ci_lower, 4),
        "perm_ci95_upper": round(ci_upper, 4),
        "p_value": round(float(p_val), 4),
        "robust_status": "ROBUST" if (ci_lower <= obs_val <= ci_upper) or (p_val > 0.05) else "SENSITIVE_TO_CONFOUND"
    })

df_summary = pd.DataFrame(summary_rows)
out_csv = ROOT / "audit" / "outputs" / "task2_topology_confound_summary.csv"
df_summary.to_csv(out_csv, index=False)
print(f"Saved Task 2 Summary to {out_csv}")
print(df_summary.to_string(index=False))

# Key findings
l1_densities = df_perms["l1_density"].dropna().astype(float)
l1_zero_pct = float(np.mean(l1_densities == 0.0) * 100)
l5_pop_pct = float(np.mean(df_perms["l5_flows"] > 0) * 100)
mono_pct = float(np.mean(df_perms["is_monotonic"].astype(float)) * 100)

print("\n" + "="*70)
print("TASK 2 KEY FINDINGS & AUDIT VERDICT:")
print("="*70)
print(f"1. L1 Attack Density == 0%: {l1_zero_pct:.2f}% of permutations")
print(f"   Permutation Mean: {np.mean(l1_densities)*100:.3f}% (95% CI: [{np.percentile(l1_densities, 2.5)*100:.3f}%, {np.percentile(l1_densities, 97.5)*100:.3f}%])")
print(f"2. L5 Flow Population: {l5_pop_pct:.2f}% of permutations populated (mean flows: {np.mean(df_perms['l5_flows']):.1f})")
print(f"3. Strict Monotonicity: {mono_pct:.2f}% of permutations")
print(f"4. P2-tier Net Benefit OCU: Observed {obs_values['ocu_p2_tier']:,.0f} vs Permutation Mean {np.mean(df_perms['ocu_p2_tier']):,.1f} (CI: [{np.percentile(df_perms['ocu_p2_tier'], 2.5):,.0f}, {np.percentile(df_perms['ocu_p2_tier'], 97.5):,.0f}])")
print("="*70)
