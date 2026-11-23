import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("experiments/E20_posture_threshold_sensitivity/results.csv")

plt.figure(figsize=(8, 4.5), dpi=300)
colors_mono = ["#16a34a" if "YES" in m else "#dc2626" for m in df["Monotonic Attack Density"]]
plt.bar(range(len(df)), df["P2-tier Net (OCU)"]/1e3, color=colors_mono, edgecolor="black", width=0.55)
plt.xticks(range(len(df)), [f"{r['Parameter']}={r['Value']}" for _, r in df.iterrows()], rotation=45, ha="right", fontsize=8)
plt.ylabel("P2-tier Combined Benefit (kOCU)", fontsize=10.5, fontweight="bold")
plt.title("Posture Threshold Sensitivity: Monotonicity Boundaries & Operational Benefit", fontsize=11.5, fontweight="bold", pad=12)
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("experiments/E20_posture_threshold_sensitivity/plot.png", dpi=300)
plt.close()
print("Saved experiments/E20_posture_threshold_sensitivity/plot.png")
