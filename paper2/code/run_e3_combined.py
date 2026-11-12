import os
import sys
sys.path.insert(0, ".")
import json
import itertools
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

print("=== STARTING OBJECTIVE 3 COMBINED RUN: E3.3, E3.4, E3.5 ===")

# Cost matrix: costs[action][is_attack]
COSTS = {
    "Allow":      {0: 0,  1: 100},
    "Alert":      {0: 1,  1: -5},
    "Restrict":   {0: 3,  1: -10},
    "Quarantine": {0: 15, 1: -20},
    "Block":      {0: 50, 1: -50},
}
ACTION_NAMES = ["Allow", "Alert", "Restrict", "Quarantine", "Block"]
COST_TUPLES = [(0, 100), (1, -5), (3, -10), (15, -20), (50, -50)]

# Load class names
with open("audit/lofo/cache/class_names.json", "r") as f:
    class_names = json.load(f)

# Load data from generate_both_windows
from paper2.code.generate_both_windows import (
    levels_bal, levels_60k, y_bal, y_60k, trust_bal, trust_60k, tarp_bal, tarp_60k, get_family
)

# Flow-level level expansions (60,000 flows each)
sample_levels_bal = np.repeat(levels_bal, 100)
sample_levels_60k = np.repeat(levels_60k, 100)

is_atk_bal = (y_bal != 1).astype(int)
is_atk_60k = (y_60k != 1).astype(int)

n_atk_bal = int(np.sum(is_atk_bal == 1))
n_ben_bal = int(np.sum(is_atk_bal == 0))
n_atk_60k = int(np.sum(is_atk_60k == 1))
n_ben_60k = int(np.sum(is_atk_60k == 0))

print(f"Balanced window: {n_ben_bal} Benign, {n_atk_bal} Attack (Total {len(y_bal)})")
print(f"Attack-heavy window: {n_ben_60k} Benign, {n_atk_60k} Attack (Total {len(y_60k)})")

# Precompute counts per level (benign, attack)
bal_level_counts = []
atk_level_counts = []
for lvl in range(6):
    mask_b = (sample_levels_bal == lvl)
    b_ben = int(np.sum((mask_b) & (is_atk_bal == 0)))
    b_atk = int(np.sum((mask_b) & (is_atk_bal == 1)))
    bal_level_counts.append((b_ben, b_atk))
    
    mask_a = (sample_levels_60k == lvl)
    a_ben = int(np.sum((mask_a) & (is_atk_60k == 0)))
    a_atk = int(np.sum((mask_a) & (is_atk_60k == 1)))
    atk_level_counts.append((a_ben, a_atk))

print("\nLevel counts (Benign, Attack):")
for lvl in range(6):
    print(f"L{lvl}: Balanced={bal_level_counts[lvl]}, Attack-Heavy={atk_level_counts[lvl]}")


# ===================================================================
# EXPERIMENT E3.3: MAPPING OPTIMIZATION SWEEP UNDER MONOTONICITY
# ===================================================================
print("\n" + "="*60)
print("EXPERIMENT E3.3: LEVEL-TO-ACTION MAPPING OPTIMIZATION SWEEP")
print("="*60)

# Monotonic combinations with Allow at L0 and Block at L5
all_70 = [m for m in itertools.combinations_with_replacement(range(5), 6) if m[0] == 0 and m[5] == 4]
print(f"Total candidate monotonic mappings: {len(all_70)}")

sweep_results = []
for m in all_70:
    # Check safety constraint: Block on benign <= 5.0% on balanced window
    ben_blocked_bal = sum(bal_level_counts[lvl][0] for lvl in range(6) if m[lvl] == 4)
    block_fpr_bal = ben_blocked_bal / n_ben_bal * 100.0
    is_safe = (block_fpr_bal <= 5.0)
    
    # Compute costs
    c_bal = sum(bal_level_counts[lvl][0] * COST_TUPLES[m[lvl]][0] + bal_level_counts[lvl][1] * COST_TUPLES[m[lvl]][1] for lvl in range(6))
    c_atk = sum(atk_level_counts[lvl][0] * COST_TUPLES[m[lvl]][0] + atk_level_counts[lvl][1] * COST_TUPLES[m[lvl]][1] for lvl in range(6))
    c_comb = 0.5 * c_bal + 0.5 * c_atk
    
    net_ben_bal = -c_bal
    net_ben_atk = -c_atk
    comb_net_ben = -c_comb
    
    # Metrics on balanced window
    atk_acted = sum(bal_level_counts[lvl][1] for lvl in range(6) if m[lvl] > 0)
    atk_recall = atk_acted / n_atk_bal * 100.0
    
    ben_acted = sum(bal_level_counts[lvl][0] for lvl in range(6) if m[lvl] > 0)
    ben_fpr = ben_acted / n_ben_bal * 100.0
    
    ben_qb = sum(bal_level_counts[lvl][0] for lvl in range(6) if m[lvl] >= 3)
    ben_qb_rate = ben_qb / n_ben_bal * 100.0
    
    # Action precision monotonicity check
    # Compute precision per action present
    act_atk = {a: sum(bal_level_counts[lvl][1] for lvl in range(6) if m[lvl] == a) for a in range(5)}
    act_ben = {a: sum(bal_level_counts[lvl][0] for lvl in range(6) if m[lvl] == a) for a in range(5)}
    precisions = []
    for a in range(5):
        tot_a = act_atk[a] + act_ben[a]
        if tot_a > 0:
            precisions.append((a, act_atk[a] / tot_a * 100.0))
    
    is_prec_mono = True
    for i in range(len(precisions) - 1):
        if precisions[i][1] > precisions[i+1][1]:
            is_prec_mono = False
            break
            
    mapping_str = " -> ".join([f"L{lvl}:{ACTION_NAMES[m[lvl]]}" for lvl in range(6)])
    short_str = "-".join([ACTION_NAMES[m[lvl]] for lvl in range(6)])
    
    sweep_results.append({
        "mapping_tuple": str(m),
        "mapping_name": short_str,
        "mapping_detail": mapping_str,
        "is_safe_fpr_le_5pct": is_safe,
        "expected_cost_balanced": c_bal,
        "net_benefit_balanced": net_ben_bal,
        "expected_cost_attack_heavy": c_atk,
        "net_benefit_attack_heavy": net_ben_atk,
        "combined_cost": c_comb,
        "combined_net_benefit": comb_net_ben,
        "attack_recall_pct": atk_recall,
        "benign_fpr_pct": ben_fpr,
        "benign_quar_block_pct": ben_qb_rate,
        "benign_block_fpr_pct": block_fpr_bal,
        "action_precision_monotonic": is_prec_mono
    })

# Convert to DataFrame
df_sweep_all = pd.DataFrame(sweep_results)
df_sweep_safe = df_sweep_all[df_sweep_all["is_safe_fpr_le_5pct"]].copy()

# Sort safe mappings by combined net benefit descending (combined cost ascending)
df_sweep_safe = df_sweep_safe.sort_values(by="combined_net_benefit", ascending=False).reset_index(drop=True)
df_sweep_safe["rank_combined"] = df_sweep_safe.index + 1

# Also rank by balanced net benefit
df_sweep_safe["rank_balanced"] = df_sweep_safe["net_benefit_balanced"].rank(ascending=False, method="min").astype(int)
# Also rank by attack-heavy net benefit
df_sweep_safe["rank_attack_heavy"] = df_sweep_safe["net_benefit_attack_heavy"].rank(ascending=False, method="min").astype(int)

# Export full sweep (all 65 safe mappings, plus excluded 5 noted)
os.makedirs("paper2/tables", exist_ok=True)
sweep_csv_path = "paper2/tables/O3_E3_mapping_sweep.csv"
df_sweep_safe.to_csv(sweep_csv_path, index=False)
print(f"Exported full sweep ({len(df_sweep_safe)} safe mappings) to {sweep_csv_path}")

# Top 10 mappings
df_top10 = df_sweep_safe.head(10).copy()
top10_csv_path = "paper2/tables/O3_E3_top10_mappings.csv"
df_top10.to_csv(top10_csv_path, index=False)
print(f"Exported top 10 mappings to {top10_csv_path}")

# Default mapping stats
default_tuple_str = "(0, 1, 2, 3, 3, 4)"
default_row = df_sweep_safe[df_sweep_safe["mapping_tuple"] == default_tuple_str].iloc[0]
print(f"\nDefault Mapping P1 ({default_row['mapping_name']}):")
print(f"  Combined Rank: {default_row['rank_combined']} of {len(df_sweep_safe)}")
print(f"  Balanced Rank: {default_row['rank_balanced']} of {len(df_sweep_safe)}")
print(f"  Attack-Heavy Rank: {default_row['rank_attack_heavy']} of {len(df_sweep_safe)}")
print(f"  Balanced Net Benefit: {default_row['net_benefit_balanced']:,}")
print(f"  Attack-Heavy Net Benefit: {default_row['net_benefit_attack_heavy']:,}")
print(f"  Combined Net Benefit: {default_row['combined_net_benefit']:,}")

# Optimal mapping P2 stats (Rank 1 combined)
opt_row = df_sweep_safe.iloc[0]
print(f"\nOptimal Mapping P2 ({opt_row['mapping_name']}):")
print(f"  Combined Rank: {opt_row['rank_combined']} of {len(df_sweep_safe)}")
print(f"  Balanced Rank: {opt_row['rank_balanced']} of {len(df_sweep_safe)}")
print(f"  Attack-Heavy Rank: {opt_row['rank_attack_heavy']} of {len(df_sweep_safe)}")
print(f"  Balanced Net Benefit: {opt_row['net_benefit_balanced']:,}")
print(f"  Attack-Heavy Net Benefit: {opt_row['net_benefit_attack_heavy']:,}")
print(f"  Combined Net Benefit: {opt_row['combined_net_benefit']:,}")
print(f"  Block FPR: {opt_row['benign_block_fpr_pct']:.2f}%")

# Top tier-preserving mapping (where all 5 action tiers are populated: Allow, Alert, Restrict, Quarantine, Block)
tier_pres_row = df_sweep_safe[df_sweep_safe["mapping_name"] == "Allow-Alert-Restrict-Quarantine-Block-Block"].iloc[0]
print(f"\nTier-Preserving Optimal P2_tier ({tier_pres_row['mapping_name']}):")
print(f"  Combined Rank: {tier_pres_row['rank_combined']} of {len(df_sweep_safe)}")
print(f"  Balanced Rank: {tier_pres_row['rank_balanced']} of {len(df_sweep_safe)}")
print(f"  Balanced Net Benefit: {tier_pres_row['net_benefit_balanced']:,}")
print(f"  Attack-Heavy Net Benefit: {tier_pres_row['net_benefit_attack_heavy']:,}")
print(f"  Combined Net Benefit: {tier_pres_row['combined_net_benefit']:,}")
print(f"  Block FPR: {tier_pres_row['benign_block_fpr_pct']:.2f}%")


# ===================================================================
# EXPERIMENT E3.4: PER-FAMILY ACTION SPECIALIZATION
# ===================================================================
print("\n" + "="*60)
print("EXPERIMENT E3.4: PER-FAMILY ACTION SPECIALIZATION AUDIT")
print("="*60)

# Mappings to evaluate:
# P1: Allow, Alert, Restrict, Quarantine, Quarantine, Block
map_p1 = {0: "Allow", 1: "Alert", 2: "Restrict", 3: "Quarantine", 4: "Quarantine", 5: "Block"}
# P2: Allow, Restrict, Quarantine, Block, Block, Block
map_p2 = {0: "Allow", 1: "Restrict", 2: "Quarantine", 3: "Block", 4: "Block", 5: "Block"}
# P2_tier: Allow, Alert, Restrict, Quarantine, Block, Block
map_p2_tier = {0: "Allow", 1: "Alert", 2: "Restrict", 3: "Quarantine", 4: "Block", 5: "Block"}

actions_p1_bal = np.array([map_p1[lvl] for lvl in sample_levels_bal])
actions_p2_bal = np.array([map_p2[lvl] for lvl in sample_levels_bal])
actions_p2_tier_bal = np.array([map_p2_tier[lvl] for lvl in sample_levels_bal])

fams_bal = np.array([get_family(y) for y in y_bal])
target_families = ["Benign", "DDoS", "DoS", "Mirai", "Recon", "Spoofing", "Web", "BruteForce"]

family_rows = []
for fam in target_families:
    mask = (fams_bal == fam)
    cnt = int(np.sum(mask))
    if cnt == 0:
        continue
    
    is_atk_sub = is_atk_bal[mask]
    t_sub = trust_bal[mask]
    tp_sub = tarp_bal[mask]
    
    # Under P1 Default
    acts_p1 = actions_p1_bal[mask]
    c_p1_allow = np.sum(acts_p1 == "Allow")
    c_p1_alert = np.sum(acts_p1 == "Alert")
    c_p1_restrict = np.sum(acts_p1 == "Restrict")
    c_p1_quarantine = np.sum(acts_p1 == "Quarantine")
    c_p1_block = np.sum(acts_p1 == "Block")
    
    dom_p1 = max(["Allow", "Alert", "Restrict", "Quarantine", "Block"], 
                 key=lambda a: np.sum(acts_p1 == a))
    
    cost_p1 = sum(COSTS[a][is_atk_sub[i]] for i, a in enumerate(acts_p1))
    mean_cost_p1 = cost_p1 / cnt
    
    # Under P2 Optimal
    acts_p2 = actions_p2_bal[mask]
    dom_p2 = max(["Allow", "Alert", "Restrict", "Quarantine", "Block"], 
                 key=lambda a: np.sum(acts_p2 == a))
    cost_p2 = sum(COSTS[a][is_atk_sub[i]] for i, a in enumerate(acts_p2))
    mean_cost_p2 = cost_p2 / cnt
    
    # Under P2_tier
    acts_p2_tier = actions_p2_tier_bal[mask]
    dom_p2_tier = max(["Allow", "Alert", "Restrict", "Quarantine", "Block"], 
                     key=lambda a: np.sum(acts_p2_tier == a))
    cost_p2_tier = sum(COSTS[a][is_atk_sub[i]] for i, a in enumerate(acts_p2_tier))
    mean_cost_p2_tier = cost_p2_tier / cnt
    
    family_rows.append({
        "family": fam,
        "flow_count": cnt,
        "share_pct": cnt / len(y_bal) * 100.0,
        "mean_trust": float(np.mean(t_sub)),
        "mean_tarp": float(np.mean(tp_sub)),
        # P1 metrics
        "p1_allow_pct": c_p1_allow / cnt * 100.0,
        "p1_alert_pct": c_p1_alert / cnt * 100.0,
        "p1_restrict_pct": c_p1_restrict / cnt * 100.0,
        "p1_quarantine_pct": c_p1_quarantine / cnt * 100.0,
        "p1_block_pct": c_p1_block / cnt * 100.0,
        "p1_dominant_action": dom_p1,
        "p1_total_cost": cost_p1,
        "p1_mean_cost": mean_cost_p1,
        # P2 metrics
        "p2_allow_pct": np.sum(acts_p2 == "Allow") / cnt * 100.0,
        "p2_alert_pct": np.sum(acts_p2 == "Alert") / cnt * 100.0,
        "p2_restrict_pct": np.sum(acts_p2 == "Restrict") / cnt * 100.0,
        "p2_quarantine_pct": np.sum(acts_p2 == "Quarantine") / cnt * 100.0,
        "p2_block_pct": np.sum(acts_p2 == "Block") / cnt * 100.0,
        "p2_dominant_action": dom_p2,
        "p2_total_cost": cost_p2,
        "p2_mean_cost": mean_cost_p2,
        # P2_tier metrics
        "p2_tier_dominant_action": dom_p2_tier,
        "p2_tier_total_cost": cost_p2_tier,
        "p2_tier_mean_cost": mean_cost_p2_tier,
    })

df_family = pd.DataFrame(family_rows)
family_csv_path = "paper2/tables/O3_E4_per_family_actions.csv"
df_family.to_csv(family_csv_path, index=False)
print(f"Exported per-family specialization analysis to {family_csv_path}")

print("\nPer-Family Specialization Summary (P1 Default Policy):")
for r in family_rows:
    print(f"  {r['family']:12s} (N={r['flow_count']:5d}): "
          f"Allow={r['p1_allow_pct']:5.1f}% Alert={r['p1_alert_pct']:5.1f}% "
          f"Res={r['p1_restrict_pct']:5.1f}% Qua={r['p1_quarantine_pct']:5.1f}% "
          f"Blo={r['p1_block_pct']:5.1f}% | Dominant={r['p1_dominant_action']:10s} | "
          f"MeanTrust={r['mean_trust']:5.1f} | MeanCost={r['p1_mean_cost']:6.2f}")


# Generate Heatmap for E3.4
os.makedirs("paper2/figures", exist_ok=True)
fig_family_path = "paper2/figures/O3_per_family_heatmap.png"

plt.figure(figsize=(14, 6))

# Panel 1: P1 Default Heatmap
plt.subplot(1, 2, 1)
p1_matrix = df_family[["p1_allow_pct", "p1_alert_pct", "p1_restrict_pct", "p1_quarantine_pct", "p1_block_pct"]].values
sns.heatmap(p1_matrix, annot=True, fmt=".1f", cmap="Blues", cbar=True,
            xticklabels=["Allow", "Alert", "Restrict", "Quarantine", "Block"],
            yticklabels=df_family["family"])
plt.title("(a) Default Policy P1 Enforcement Distribution (%)", fontsize=12, fontweight="bold", pad=10)
plt.xlabel("Enforcement Action", fontsize=11, fontweight="bold")
plt.ylabel("Traffic Family", fontsize=11, fontweight="bold")

# Panel 2: P2 Optimal Heatmap
plt.subplot(1, 2, 2)
p2_matrix = df_family[["p2_allow_pct", "p2_alert_pct", "p2_restrict_pct", "p2_quarantine_pct", "p2_block_pct"]].values
sns.heatmap(p2_matrix, annot=True, fmt=".1f", cmap="Blues", cbar=True,
            xticklabels=["Allow", "Alert", "Restrict", "Quarantine", "Block"],
            yticklabels=df_family["family"])
plt.title("(b) Optimal Policy P2 Enforcement Distribution (%)", fontsize=12, fontweight="bold", pad=10)
plt.xlabel("Enforcement Action", fontsize=11, fontweight="bold")
plt.ylabel("Traffic Family", fontsize=11, fontweight="bold")

plt.tight_layout()
plt.savefig(fig_family_path, dpi=300)
plt.close()
print(f"Saved family specialization heatmap to {fig_family_path}")


# ===================================================================
# EXPERIMENT E3.5: HEADLINE COMPARISON TABLE & FIGURES
# ===================================================================
print("\n" + "="*60)
print("EXPERIMENT E3.5: HEADLINE COMPARISON & PAPER SUMMARY")
print("="*60)

# Load existing P0 numbers from O3_E1_baseline_costs.csv
df_e1 = pd.read_csv("paper2/tables/O3_E1_baseline_costs.csv")
# Attack-Heavy:
p0_pub_atk = df_e1[(df_e1["window"] == "Attack-heavy 60k") & (df_e1["policy"].str.contains("Published"))].iloc[0]
p0_rec_atk = df_e1[(df_e1["window"] == "Attack-heavy 60k") & (df_e1["policy"].str.contains("Recomputed"))].iloc[0]
p1_atk     = df_e1[(df_e1["window"] == "Attack-heavy 60k") & (df_e1["policy"].str.contains("P1"))].iloc[0]

# Balanced:
p0_rec_bal = df_e1[(df_e1["window"] == "Balanced Stratified 60k") & (df_e1["policy"].str.contains("Recomputed"))].iloc[0]
p1_bal     = df_e1[(df_e1["window"] == "Balanced Stratified 60k") & (df_e1["policy"].str.contains("P1"))].iloc[0]

# Note: P0 Published on balanced window was not evaluated in published work, but if Table 19A actions are applied or if recomputed:
# We document both fairly.
# Compute Benign Penalty and Attack Containment for each policy on balanced window:
# P0 Recomputed Balanced:
# From E3.1: Allow=11609 (11607 ben), Alert=27287 (1423 ben), Restrict=17083 (16785 ben), Quarantine=4021 (194 ben), Block=0
# Benign penalty: 11607*0 + 1423*1 + 16785*3 + 194*15 + 0*50 = 1423 + 50355 + 2910 = 54,688
# Attack containment benefit: 2*(-100) + 25864*(-5) + 298*(-10) + 3827*(-20) + 0*(-50) = -200 - 129320 - 2980 - 76540 = -209,040
# Net benefit = -(54688 - 209040) = +154,352 (Wait, let's verify exact cost: 54688 - 208640 = -153,952 => Net Benefit = +153,952)
cost_ben_p0_rec_bal = 1423 * 1 + 16785 * 3 + 194 * 15
cost_atk_p0_rec_bal = 2 * 100 + 25864 * (-5) + 298 * (-10) + 3827 * (-20)
# Net benefit: - (54688 - 208640) = +153,952

# P1 Default Balanced:
# Allow=14200 (14200 ben), Alert=20200 (12191 ben, 8009 atk), Restrict=7800 (3321 ben, 4479 atk), Quarantine=16300 (297 ben, 16003 atk), Block=1500 (0 ben, 1500 atk)
# Benign penalty: 14200*0 + 12191*1 + 3321*3 + 297*15 + 0*50 = 12191 + 9963 + 4455 = 26,609
# Attack containment benefit: 0*100 + 8009*(-5) + 4479*(-10) + 16003*(-20) + 1500*(-50) = -40045 - 44790 - 320060 - 75000 = -479,895
# Net benefit = -(26609 - 479895) = +453,286
cost_ben_p1_bal = 12191 * 1 + 3321 * 3 + 297 * 15
cost_atk_p1_bal = 8009 * (-5) + 4479 * (-10) + 16003 * (-20) + 1500 * (-50)

# P2 Optimal Balanced:
# Allow (14200 ben), Restrict (12191 ben, 8009 atk), Quarantine (3321 ben, 4479 atk), Block (297 ben, 17503 atk)
# Benign penalty: 14200*0 + 12191*3 + 3321*15 + 297*50 = 36573 + 49815 + 14850 = 101,238
# Attack containment: 8009*(-10) + 4479*(-20) + 17503*(-50) = -80090 - 89580 - 875150 = -1,044,820
# Net benefit = -(101238 - 1044820) = +943,582
cost_ben_p2_bal = 12191 * 3 + 3321 * 15 + 297 * 50
cost_atk_p2_bal = 8009 * (-10) + 4479 * (-20) + 17503 * (-50)

# P2 Tier-Preserving Balanced:
# Allow (14200 ben), Alert (12191 ben, 8009 atk), Restrict (3321 ben, 4479 atk), Quarantine (297 ben, 403 atk), Block (0 ben, 17100 atk)
# Benign penalty: 14200*0 + 12191*1 + 3321*3 + 297*15 + 0*50 = 26,609
# Attack containment: 8009*(-5) + 4479*(-10) + 403*(-20) + 17100*(-50) = -40045 - 44790 - 8060 - 855000 = -947,895
# Net benefit = -(26609 - 947895) = +921,286
cost_ben_p2_tier_bal = 12191 * 1 + 3321 * 3 + 297 * 15
cost_atk_p2_tier_bal = 8009 * (-5) + 4479 * (-10) + 403 * (-20) + 17100 * (-50)

# Build E3.5 Table
final_comparison_rows = [
    {
        "policy": "P0 (Published Table 19A)",
        "pipeline_description": "Contaminated IF + Original Decision Engine",
        "expected_cost_bal": "N/A (untested)",
        "net_benefit_bal": "N/A (untested)",
        "expected_cost_atk": -329835,
        "net_benefit_atk": 329835,
        "combined_net_benefit": "N/A",
        "benign_penalty_bal": "N/A",
        "attack_containment_bal": "N/A",
        "monotonic_precision": "NO (Inverted)",
        "inversion_count": 1,
        "block_fpr_bal%": 0.00,
        "attack_recall_bal%": "N/A"
    },
    {
        "policy": "P0 (Freshly Recomputed)",
        "pipeline_description": "Contaminated IF + Original Engine (Fair Eval)",
        "expected_cost_bal": -153952,
        "net_benefit_bal": 153952,
        "expected_cost_atk": -395769,
        "net_benefit_atk": 395769,
        "combined_net_benefit": 274860.5,
        "benign_penalty_bal": cost_ben_p0_rec_bal,
        "attack_containment_bal": cost_atk_p0_rec_bal,
        "monotonic_precision": "NO (Inverted)",
        "inversion_count": 1,
        "block_fpr_bal%": 0.00,
        "attack_recall_bal%": 99.99
    },
    {
        "policy": "P1 (New Default)",
        "pipeline_description": "Corrected IF + Recalibrated Trust + Default Mapping",
        "expected_cost_bal": -453286,
        "net_benefit_bal": 453286,
        "expected_cost_atk": -1259475,
        "net_benefit_atk": 1259475,
        "combined_net_benefit": 856380.5,
        "benign_penalty_bal": cost_ben_p1_bal,
        "attack_containment_bal": cost_atk_p1_bal,
        "monotonic_precision": "YES (Strictly Monotonic)",
        "inversion_count": 0,
        "block_fpr_bal%": 0.00,
        "attack_recall_bal%": 100.00
    },
    {
        "policy": "P2 (Global Cost-Optimal)",
        "pipeline_description": "Corrected Pipeline + Sweep-Optimal Mapping (Allow-Res-Qua-Blo-Blo-Blo)",
        "expected_cost_bal": -943582,
        "net_benefit_bal": 943582,
        "expected_cost_atk": -2851800,
        "net_benefit_atk": 2851800,
        "combined_net_benefit": 1897691.0,
        "benign_penalty_bal": cost_ben_p2_bal,
        "attack_containment_bal": cost_atk_p2_bal,
        "monotonic_precision": "YES (Strictly Monotonic)",
        "inversion_count": 0,
        "block_fpr_bal%": 0.99,
        "attack_recall_bal%": 100.00
    },
    {
        "policy": "P2_tier (Tier-Preserving Optimal)",
        "pipeline_description": "Corrected Pipeline + 5-Tier Optimal Mapping (Allow-Ale-Res-Qua-Blo-Blo)",
        "expected_cost_bal": -921286,
        "net_benefit_bal": 921286,
        "expected_cost_atk": -2802480,
        "net_benefit_atk": 2802480,
        "combined_net_benefit": 1861883.0,
        "benign_penalty_bal": cost_ben_p2_tier_bal,
        "attack_containment_bal": cost_atk_p2_tier_bal,
        "monotonic_precision": "YES (Strictly Monotonic)",
        "inversion_count": 0,
        "block_fpr_bal%": 0.00,
        "attack_recall_bal%": 100.00
    }
]

df_final_comparison = pd.DataFrame(final_comparison_rows)
final_csv_path = "paper2/tables/O3_E5_final_comparison.csv"
df_final_comparison.to_csv(final_csv_path, index=False)
print(f"Exported final headline comparison table to {final_csv_path}")


# -------------------------------------------------------------
# Generate Figures for E3.5
# -------------------------------------------------------------
# Figure 1: Net Benefit Comparison Bars across Policies
fig_cost_path = "paper2/figures/O3_cost_comparison_bars.png"

policies_for_plot = ["P0 (Recomputed)", "P1 (New Default)", "P2 (Global Optimal)", "P2_tier (Tier-Preserving)"]
net_ben_bal_vals = [153952, 453286, 943582, 921286]
net_ben_atk_vals = [395769, 1259475, 2851800, 2802480]

x = np.arange(len(policies_for_plot))
width = 0.35

plt.figure(figsize=(10, 6))
bars1 = plt.bar(x - width/2, [v/1e3 for v in net_ben_bal_vals], width, label="Balanced Stratified Window (30/40/30)", color="#2b5c8f")
bars2 = plt.bar(x + width/2, [v/1e3 for v in net_ben_atk_vals], width, label="Attack-Heavy 60k Window (97.5% Atk)", color="#d95f02")

plt.ylabel("Net Operational Benefit ($k = -\\mathrm{Cost}/1000$)", fontsize=12, fontweight="bold")
plt.title("Net Operational Benefit Across Policy Configurations\n(Higher is Better; Benefit = -Cost)", fontsize=13, fontweight="bold", pad=12)
plt.xticks(x, policies_for_plot, fontsize=10, fontweight="bold")
plt.legend(frameon=True, fontsize=10)
plt.grid(axis="y", linestyle="--", alpha=0.5)

# Add values above bars
for bar in bars1:
    h = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., h + 20, f"+${h:.0f}k", ha="center", va="bottom", fontsize=9, fontweight="bold")
for bar in bars2:
    h = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., h + 50, f"+${h:.0f}k", ha="center", va="bottom", fontsize=9, fontweight="bold")

plt.ylim(0, 3200)
plt.tight_layout()
plt.savefig(fig_cost_path, dpi=300)
plt.close()
print(f"Saved net benefit comparison chart to {fig_cost_path}")


# Figure 2: Benign Penalty Breakdown (Stacked Bars)
fig_penalty_path = "paper2/figures/O3_benign_penalty_breakdown.png"

# Actions that impose cost on benign: Alert (cost 1), Restrict (cost 3), Quarantine (cost 15), Block (cost 50)
# P0 Recomputed:
# Alert ben: 1423 flows * 1 = $1,423
# Restrict ben: 16785 flows * 3 = $50,355
# Quarantine ben: 194 flows * 15 = $2,910
# Block ben: 0 flows * 50 = $0
# Total: $54,688

# P1 Default:
# Alert ben: 12191 flows * 1 = $12,191
# Restrict ben: 3321 flows * 3 = $9,963
# Quarantine ben: 297 flows * 15 = $4,455
# Block ben: 0 flows * 50 = $0
# Total: $26,609 (51.3% reduction!)

# P2 Tier-Preserving:
# Alert ben: 12191 * 1 = $12,191
# Restrict ben: 3321 * 3 = $9,963
# Quarantine ben: 297 * 15 = $4,455
# Block ben: 0 * 50 = $0
# Total: $26,609

# P2 Global Optimal:
# Alert ben: 0 * 1 = $0
# Restrict ben: 12191 * 3 = $36,573
# Quarantine ben: 3321 * 15 = $49,815
# Block ben: 297 * 50 = $14,850
# Total: $101,238

policies_pen = ["P0 (Recomputed)", "P1 (New Default)", "P2_tier (Tier-Preserving)", "P2 (Global Optimal)"]
c_alert = np.array([1423, 12191, 12191, 0])
c_restrict = np.array([50355, 9963, 9963, 36573])
c_quarantine = np.array([2910, 4455, 4455, 49815])
c_block = np.array([0, 0, 0, 14850])

plt.figure(figsize=(9, 6))
p_al = plt.bar(policies_pen, c_alert, label="Alert ($1/flow)", color="#7570b3")
p_re = plt.bar(policies_pen, c_restrict, bottom=c_alert, label="Restrict ($3/flow)", color="#e7298a")
p_qu = plt.bar(policies_pen, c_quarantine, bottom=c_alert+c_restrict, label="Quarantine ($15/flow)", color="#e6ab02")
p_bl = plt.bar(policies_pen, c_block, bottom=c_alert+c_restrict+c_quarantine, label="Block ($50/flow)", color="#d95f02")

totals = c_alert + c_restrict + c_quarantine + c_block
for i, tot in enumerate(totals):
    plt.text(i, tot + 1500, f"${tot:,}", ha="center", va="bottom", fontsize=10, fontweight="bold")

plt.ylabel("Benign Operational Cost Penalty ($)", fontsize=12, fontweight="bold")
plt.title("Benign Traffic Cost Penalty Breakdown by Enforcement Action\n(Balanced Window: P1 reduces benign penalty by 51.3% vs P0)", fontsize=12, fontweight="bold", pad=12)
plt.legend(frameon=True, fontsize=10)
plt.ylim(0, 125000)
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig(fig_penalty_path, dpi=300)
plt.close()
print(f"Saved benign penalty breakdown chart to {fig_penalty_path}")

print("\n=== ALL OBJECTIVE 3 EXPERIMENTS (E3.3, E3.4, E3.5) COMPLETED SUCCESSFULLY ===")
