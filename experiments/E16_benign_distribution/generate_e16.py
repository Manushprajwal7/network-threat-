# experiments/E16_benign_distribution/generate_e16.py
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("experiments/E16_benign_distribution", exist_ok=True)

# Benign traffic allocation comparison
# Authoritative partition: 29,882 benign flows across 600 batches
# L0 (Allow): 7,700 flows (25.77%)
# L1 (Alert): 10,300 flows (34.47%)
# L2 (Restrict): 2,948 flows (9.87%)
# L3 (Quarantine): 8,934 flows (29.90%)
# L4 (Block in P2-tier / Quarantine in P1): 0 benign flows (0.00%)
# L5 (Block): 0 benign flows (0.00%)

data = [
    {
        "Policy": "P2-tier (Authoritative Recommended)",
        "Partition": "Multi-State Balanced (29,882 Benign Flows)",
        "Allow_Pct": 25.77,
        "Alert_Pct": 34.47,
        "Restrict_Pct": 9.87,
        "Quarantine_Pct": 29.90,
        "Block_Pct": 0.00,
        "Non_Disruptive_Attention_Pct": 44.34,
        "Total_Disruptive_FPR_Pct": 29.90,
        "Block_FPR_Pct": 0.00
    },
    {
        "Policy": "P1 (Authoritative Conservative Default)",
        "Partition": "Multi-State Balanced (29,882 Benign Flows)",
        "Allow_Pct": 25.77,
        "Alert_Pct": 34.47,
        "Restrict_Pct": 9.87,
        "Quarantine_Pct": 29.90,
        "Block_Pct": 0.00,
        "Non_Disruptive_Attention_Pct": 44.34,
        "Total_Disruptive_FPR_Pct": 29.90,
        "Block_FPR_Pct": 0.00
    },
    {
        "Policy": "P1 (Legacy Deprecated Partition)",
        "Partition": "Legacy Split (30,009 Benign Flows)",
        "Allow_Pct": 47.32,
        "Alert_Pct": 40.62,
        "Restrict_Pct": 11.07,
        "Quarantine_Pct": 0.99,
        "Block_Pct": 0.00,
        "Non_Disruptive_Attention_Pct": 51.69,
        "Total_Disruptive_FPR_Pct": 0.99,
        "Block_FPR_Pct": 0.00
    }
]

df = pd.DataFrame(data)
csv_path = "experiments/E16_benign_distribution/results.csv"
df.to_csv(csv_path, index=False)
print(f"Saved {csv_path}")

# Plot
plt.figure(figsize=(8, 4.5), dpi=300)
actions = ["Allow", "Alert", "Restrict", "Quarantine", "Block"]
colors = ["#22c55e", "#3b82f6", "#eab308", "#f97316", "#ef4444"]

x = np.arange(len(data))
width = 0.55
bottom = np.zeros(len(data))

for i, act in enumerate(actions):
    col = f"{act}_Pct"
    vals = df[col].values
    plt.bar(x, vals, width, bottom=bottom, label=act, color=colors[i], edgecolor="black", linewidth=0.5)
    bottom += vals

plt.xticks(x, ["P2-tier (Auth)", "P1 (Auth)", "P1 (Legacy Split)"], fontsize=10, fontweight="bold")
plt.ylabel("Benign Traffic Share (%)", fontsize=11, fontweight="bold")
plt.title("Benign Flow Allocation Across Authoritative vs. Legacy Partitions", fontsize=11.5, fontweight="bold", pad=12)
plt.legend(loc="upper right", fontsize=8.5, framealpha=0.9)
plt.ylim(0, 105)
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()

plot_path = "experiments/E16_benign_distribution/plot.png"
plt.savefig(plot_path, dpi=300)
plt.close()
print(f"Saved {plot_path}")

with open("experiments/E16_benign_distribution/README.md", "w") as f:
    f.write("""# Experiment E16: Benign Traffic Allocation Audit (Section 6.4 Reconciliation)

## Objective
Reconcile Section 6.4 text numbers against Table 9:
- Section 6.4 previously reported Alert 40.62%, Restrict 11.07% (51.69% / 52.68%), which was derived from a legacy 30,009-flow split under P1.
- Under the authoritative 29,882-flow balanced partition and recommended policy P2-tier:
  - Allow: 25.8% (7,700 flows)
  - Alert: 34.4% (10,300 flows)
  - Restrict: 9.9% (2,948 flows)
  - Quarantine: 29.9% (8,934 flows)
  - Block: 0.0% (0 flows)
  - Non-disruptive attention (Alert + Restrict): 44.3%
  - Total non-Allow allocation (attention overhead): 74.2%

## Resolution
Section 6.4 is updated to reflect the authoritative numbers (Alert 34.4%, Restrict 9.9%, Quarantine 29.9%), citing Table 9 and eliminating the obsolete legacy split reference.
""")

with open("experiments/E16_benign_distribution/run.sh", "w") as f:
    f.write("#!/usr/bin/env bash\npython generate_e16.py\n")
