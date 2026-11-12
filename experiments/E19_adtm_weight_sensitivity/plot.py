import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("experiments/E19_adtm_weight_sensitivity/results.csv")

plt.figure(figsize=(8, 4.5), dpi=300)
x = np.arange(len(df))
plt.plot(x, df["C4 AUC"], marker="s", color="#059669", linewidth=2, label="C4 Trust AUC")
plt.xticks(x, [c.split("(")[0].strip() for c in df["Configuration"]], rotation=35, ha="right", fontsize=9)
plt.ylabel("Dynamic Trust AUC", fontsize=10.5, fontweight="bold")
plt.ylim(0.997, 1.000)
plt.title("ADTM C4 Trust AUC Invariance Across Behavioral Weight Allocations", fontsize=11.5, fontweight="bold", pad=12)
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("experiments/E19_adtm_weight_sensitivity/plot.png", dpi=300)
plt.close()
print("Saved experiments/E19_adtm_weight_sensitivity/plot.png")
