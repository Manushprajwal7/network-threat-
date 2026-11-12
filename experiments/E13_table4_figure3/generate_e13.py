# experiments/E13_table4_figure3/generate_e13.py
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("experiments/E13_table4_figure3", exist_ok=True)

# Authoritative data for configurations C0* to C4*
data = [
    {"Config": "C0* (Published Baseline)", "Trust AUC": 0.0441, "Trust Gap": -7.35, "Benign Mean": 86.01, "Attack Mean": 93.36, "Critical": 0.00, "Very Low": 0.00, "Low": 0.00, "Moderate": 0.03, "High": 99.97},
    {"Config": "C1* (+ Clean IF)", "Trust AUC": 0.9492, "Trust Gap": 7.23, "Benign Mean": 87.96, "Attack Mean": 80.74, "Critical": 0.00, "Very Low": 0.00, "Low": 0.00, "Moderate": 35.18, "High": 64.82},
    {"Config": "C2* (+ Clean IF + Dynamic Weights)", "Trust AUC": 0.9964, "Trust Gap": 54.13, "Benign Mean": 76.68, "Attack Mean": 22.55, "Critical": 28.68, "Very Low": 68.00, "Low": 0.81, "Moderate": 1.37, "High": 1.14},
    {"Config": "C3* (+ Clean IF + Hard Reset)", "Trust AUC": 0.9682, "Trust Gap": 50.55, "Benign Mean": 87.96, "Attack Mean": 37.42, "Critical": 60.55, "Very Low": 0.00, "Low": 0.00, "Moderate": 1.19, "High": 38.27},
    {"Config": "C4* (Full Neutral ADTM)", "Trust AUC": 0.9858, "Trust Gap": 19.98, "Benign Mean": 32.96, "Attack Mean": 12.98, "Critical": 91.34, "Very Low": 7.89, "Low": 0.24, "Moderate": 0.49, "High": 0.04},
]

df = pd.DataFrame(data)
csv_path = "experiments/E13_table4_figure3/results.csv"
df.to_csv(csv_path, index=False)
print(f"Saved {csv_path}")

# Also update authoritative paper2/tables/tab4_trust_neutral.csv
tab4_csv = "paper2/tables/tab4_trust_neutral.csv"
df_tab4 = df.rename(columns={
    "Config": "Configuration",
    "Trust AUC": "Trust AUC",
    "Trust Gap": "Trust Gap",
    "Benign Mean": "Benign Trust Mean",
    "Attack Mean": "Attack Trust Mean",
    "Critical": "Critical (<20) %",
    "Very Low": "Very Low (20-40) %",
    "Low": "Low (40-60) %",
    "Moderate": "Moderate (60-80) %",
    "High": "High (>=80) %"
})
df_tab4.to_csv(tab4_csv, index=False)
print(f"Saved {tab4_csv}")

# Generate synchronized Figure 3 plot
fig, ax = plt.subplots(figsize=(7.5, 4.5), dpi=300)

configs = [d["Config"].split(" ")[0] for d in data]
bands = ["Critical", "Very Low", "Low", "Moderate", "High"]
labels = ["Critical (<20)", "Very Low (20-40)", "Low (40-60)", "Moderate (60-80)", "High (>=80)"]
colors = ["#D9534F", "#F0AD4E", "#5BC0DE", "#337AB7", "#5CB85C"]

bottom = np.zeros(len(configs))
x = np.arange(len(configs))
width = 0.55

for i, band in enumerate(bands):
    vals = np.array([d[band] for d in data])
    ax.bar(x, vals, bottom=bottom, label=labels[i], color=colors[i], width=width, edgecolor="black", linewidth=0.5)
    bottom += vals

ax.set_xticks(x)
ax.set_xticklabels(configs, fontsize=10, fontweight="bold")
ax.set_ylabel("Traffic Flow Distribution (%)", fontsize=11, fontweight="bold")
ax.set_title("Evolution of Dynamic Trust Band Distributions Across Configurations", fontsize=12, fontweight="bold", pad=12)
ax.legend(loc="upper right", fontsize=8.5, framealpha=0.9, ncol=2)
ax.set_ylim(0, 105)
ax.grid(axis="y", linestyle="--", alpha=0.5)

plt.tight_layout()
fig_out = "experiments/E13_table4_figure3/plot.png"
fig_paper = "paper2/figures/O2_B_band_distribution_comparison.png"
plt.savefig(fig_out, dpi=300)
plt.savefig(fig_paper, dpi=300)
plt.close()
print(f"Saved {fig_out} and {fig_paper}")

# Write README.md and run.sh
with open("experiments/E13_table4_figure3/README.md", "w") as f:
    f.write("""# Experiment E13: Table 4 vs. Figure 3 Trust Band Reconciliation

## Objective
Reconcile the critical discrepancy between Table 4 and Figure 3 caption for configuration C4*.
Figure 3 caption previously reported intermediate configuration C3* values (60.55% Critical).
This experiment regenerates both Table 4 and Figure 3 from a single authoritative source of truth.

## Authoritative C4* Distribution
- Critical (<20): 91.34%
- Very Low (20–40): 7.89%
- Low (40–60): 0.24%
- Moderate (60–80): 0.49%
- High (≥80): 0.04%

## Artifacts
- `results.csv`: Table 4 data for C0*–C4*
- `plot.png`: Exact matching stacked bar chart
""")

with open("experiments/E13_table4_figure3/run.sh", "w") as f:
    f.write("#!/usr/bin/env bash\npython generate_e13.py\n")
