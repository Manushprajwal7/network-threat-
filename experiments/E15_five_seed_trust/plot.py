import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("experiments/E15_five_seed_trust/results.csv")
configs = df["Config"].unique()

plt.figure(figsize=(8, 4.5), dpi=300)
for cfg in configs:
    sub = df[df["Config"] == cfg]
    plt.plot([str(s) for s in sub["seed"]], sub["AUC"], marker="o", label=f"{cfg} (Mean: {sub['AUC'].mean():.4f})")
plt.xlabel("Random Seed", fontsize=11, fontweight="bold")
plt.ylabel("Trust AUC", fontsize=11, fontweight="bold")
plt.title("Dynamic Trust AUC Stability Across 5 Seeds for Configurations C0* - C4*", fontsize=12, fontweight="bold", pad=12)
plt.legend(loc="center right", fontsize=8.5)
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("experiments/E15_five_seed_trust/plot.png", dpi=300)
plt.close()
print("Saved experiments/E15_five_seed_trust/plot.png")
