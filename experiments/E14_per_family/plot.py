# experiments/E14_per_family/plot.py
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("experiments/E14_per_family/results.csv")

plt.figure(figsize=(10, 6), dpi=300)
heat_matrix = df[["Allow (%)", "Alert (%)", "Restrict (%)", "Quarantine (%)", "Block (%)"]].applymap(lambda s: float(str(s).replace("%", ""))).values
sns.heatmap(heat_matrix, annot=True, fmt=".1f", cmap="YlOrRd", cbar=True,
            xticklabels=["Allow", "Alert", "Restrict", "Quarantine", "Block"],
            yticklabels=df["Threat Family"])
plt.title("Enforcement Action Allocation Across Threat Families Under P2-tier", fontsize=12, fontweight="bold", pad=12)
plt.xlabel("Enforcement Action", fontsize=11, fontweight="bold")
plt.ylabel("Threat Family", fontsize=11, fontweight="bold")
plt.tight_layout()

plt.savefig("experiments/E14_per_family/plot.png", dpi=300)
plt.savefig("paper2/figures/O3_per_family_heatmap.png", dpi=300)
plt.close()
print("Saved experiments/E14_per_family/plot.png")
