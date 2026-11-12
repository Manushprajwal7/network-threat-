# experiments/E13_table4_figure3/plot.py
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("experiments/E13_table4_figure3/results.csv")

fig, ax = plt.subplots(figsize=(7.5, 4.5), dpi=300)

configs = [c.split(" ")[0] for c in df["Config"]]
bands = ["Critical", "Very Low", "Low", "Moderate", "High"]
labels = ["Critical (<20)", "Very Low (20-40)", "Low (40-60)", "Moderate (60-80)", "High (>=80)"]
colors = ["#D9534F", "#F0AD4E", "#5BC0DE", "#337AB7", "#5CB85C"]

bottom = np.zeros(len(configs))
x = np.arange(len(configs))
width = 0.55

for i, band in enumerate(bands):
    vals = df[band].values
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
plt.savefig("experiments/E13_table4_figure3/plot.png", dpi=300)
plt.savefig("paper2/figures/O2_B_band_distribution_comparison.png", dpi=300)
plt.close()
print("Saved experiments/E13_table4_figure3/plot.png")
