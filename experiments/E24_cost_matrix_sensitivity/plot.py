import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("experiments/E24_cost_matrix_sensitivity/results.csv")
ratios = df["P2_tier_Advantage_Ratio"]

plt.figure(figsize=(8, 4.5), dpi=300)
plt.hist(ratios, bins=15, color="#0284c7", edgecolor="black", alpha=0.7)
plt.axvline(1.0, color="red", linestyle="--", linewidth=2, label="Parity Threshold (Ratio = 1.0)")
plt.xlabel("P2-tier vs. P1 Net Benefit Advantage Ratio", fontsize=10.5, fontweight="bold")
plt.ylabel("Number of Parameter Configurations", fontsize=10.5, fontweight="bold")
plt.title("P2-tier Benefit Advantage Across 27 Cost Matrix Scaling Regimes", fontsize=11.5, fontweight="bold", pad=12)
plt.legend(loc="upper right", fontsize=9.5)
plt.grid(True, linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig("experiments/E24_cost_matrix_sensitivity/plot.png", dpi=300)
plt.close()
print("Saved experiments/E24_cost_matrix_sensitivity/plot.png")
