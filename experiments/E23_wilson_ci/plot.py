import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("experiments/E23_wilson_ci/results.csv")

plt.figure(figsize=(7.5, 4), dpi=300)
x = np.arange(len(df))
means = [float(r["Attack Density (%)"].replace("%", "")) for _, r in df.iterrows()]
yerr_low = [means[i] - df.iloc[i]["CI Lower (Exact)"] for i in range(len(means))]
yerr_high = [df.iloc[i]["CI Upper (Exact)"] - means[i] for i in range(len(means))]
plt.errorbar(x, means, yerr=[yerr_low, yerr_high], fmt="o", color="#2563eb", ecolor="#dc2626", elinewidth=2, capsize=5, capthick=1.5)
plt.xticks(x, [f"{r['Regime'].split()[0]} {r['Level']}" for _, r in df.iterrows()], fontsize=9, fontweight="bold")
plt.ylabel("Attack Density (%)", fontsize=10.5, fontweight="bold")
plt.title("Exact Non-Degenerate Wilson 95% Confidence Intervals", fontsize=11.5, fontweight="bold", pad=12)
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("experiments/E23_wilson_ci/plot.png", dpi=300)
plt.close()
print("Saved experiments/E23_wilson_ci/plot.png")
