import os
import json
import numpy as np
import pandas as pd

print("=== EXPERIMENT 7: PER-FAMILY ACTION AUDIT (NEUTRAL PRIORS) ===")

with open("audit/lofo/cache/class_names.json", "r") as f:
    class_names = json.load(f)
benign_idx = class_names.index("BenignTraffic")

# Map 34 classes to 7 broad families + Benign
def get_family_name(c_idx):
    if c_idx == benign_idx:
        return "Benign"
    name = class_names[c_idx]
    if "DDoS" in name: return "DDoS"
    if "DoS" in name: return "DoS"
    if "Mirai" in name: return "Mirai"
    if "Recon" in name or "Vulnerability" in name: return "Recon"
    if "Spoofing" in name: return "Spoofing"
    if "Web" in name or "SqlInjection" in name or "XSS" in name or "CommandInjection" in name: return "Web"
    if "BruteForce" in name or "Dictionary" in name: return "BruteForce"
    return "Other"

# Load balanced window data and assigned levels from Experiment 3
# To get exact per-family flow counts, let's load balanced_indices and y_test
y_test = np.load("audit/lofo/cache/y_test.npy", mmap_mode="r")

# Re-read or compute from run_full_clean_pipeline
from paper2.new_experiments.run_full_clean_pipeline import balanced_indices, levels_bal, trust_bal

# Under P2-tier mapping: L0=Allow, L1=Alert, L2=Restrict, L3=Quarantine, L4=Block, L5=Block
P2_TIER = [0, 1, 2, 3, 4, 4]
ACTION_NAMES = ["Allow", "Alert", "Restrict", "Quarantine", "Block"]

y_bal = y_test[balanced_indices]
actions_bal = np.array([P2_TIER[lvl] for lvl in levels_bal])

families = [get_family_name(c) for c in y_bal]
unique_fams = ["Benign", "DDoS", "DoS", "Mirai", "Recon", "Spoofing", "Web", "BruteForce"]

fam_rows = []
for fam in unique_fams:
    mask = np.array([f == fam for f in families])
    tot = np.sum(mask)
    if tot == 0:
        continue
    
    mean_t = np.mean(trust_bal[mask])
    share_pct = (tot / len(y_bal)) * 100.0
    
    # Action counts
    act_counts = [np.sum(actions_bal[mask] == a) for a in range(5)]
    dom_act_idx = np.argmax(act_counts)
    dom_act = ACTION_NAMES[dom_act_idx]
    
    quar_pct = (act_counts[3] / tot) * 100.0
    block_pct = (act_counts[4] / tot) * 100.0
    allow_pct = (act_counts[0] / tot) * 100.0
    alert_pct = (act_counts[1] / tot) * 100.0
    rest_pct = (act_counts[2] / tot) * 100.0
    
    fam_rows.append({
        "Threat Family": fam,
        "Total Flows": f"{tot:,}",
        "Share (%)": f"{share_pct:.2f}%",
        "Mean Trust": f"{mean_t:.2f}",
        "Allow (%)": f"{allow_pct:.1f}%",
        "Alert (%)": f"{alert_pct:.1f}%",
        "Restrict (%)": f"{rest_pct:.1f}%",
        "Quarantine (%)": f"{quar_pct:.1f}%",
        "Block (%)": f"{block_pct:.1f}%",
        "Dominant Action": dom_act
    })

df_fam = pd.DataFrame(fam_rows)
out_csv = "paper2/new_experiments/tables/tab9_per_family_actions.csv"
df_fam.to_csv(out_csv, index=False)
print("\n=== PER-FAMILY ACTION AUDIT UNDER NEUTRAL PRIORS (tab9_per_family_actions.csv) ===")
print(df_fam.to_string(index=False))
