import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.figure(figsize=(6.5, 4), dpi=300)
corr_vals = [-0.7794, -0.7794, 0.7794]
colors_sign = ["#dc2626", "#dc2626", "#16a34a"]
plt.bar(["score_samples", "decision_function", "-score_samples"], corr_vals, color=colors_sign, width=0.45, edgecolor="black")
plt.axhline(0, color="black", linewidth=1)
plt.ylabel("Pearson Correlation r with Attack Label", fontsize=10.5, fontweight="bold")
plt.title("Isolation Forest Score Negation Verification (Convention Validation)", fontsize=11, fontweight="bold", pad=12)
plt.ylim(-1.0, 1.0)
for i, v in enumerate(corr_vals):
    plt.text(i, v + (0.05 if v > 0 else -0.12), f"r = {v:+.4f}", ha="center", fontweight="bold")
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("experiments/E22_score_sign/plot.png", dpi=300)
plt.close()
print("Saved experiments/E22_score_sign/plot.png")
