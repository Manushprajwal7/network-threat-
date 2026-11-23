import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.figure(figsize=(7, 4), dpi=300)
x = np.arange(2)
width = 0.35
val_nb = [786.6, 1909.8]
test_nb = [784.2, 1907.7]
plt.bar(x - width/2, val_nb, width, label="Validation Split (Seed 42)", color="#3b82f6")
plt.bar(x + width/2, test_nb, width, label="Held-Out Test (Seed 99)", color="#10b981")
plt.xticks(x, ["P1 (Default)", "P2-tier (Recommended)"], fontsize=10, fontweight="bold")
plt.ylabel("Combined Net Benefit (kOCU)", fontsize=10.5, fontweight="bold")
plt.title("Generalization Across Validation and Independent Held-Out Test Splits", fontsize=11.5, fontweight="bold", pad=12)
plt.legend(loc="upper left", fontsize=9.5)
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("experiments/E21_held_out_balanced/plot.png", dpi=300)
plt.close()
print("Saved experiments/E21_held_out_balanced/plot.png")
