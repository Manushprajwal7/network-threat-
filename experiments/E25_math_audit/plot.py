import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.figure(figsize=(6, 3.5), dpi=300)
plt.bar(["Math Audit Issues"], [0], color="#16a34a", width=0.35, edgecolor="black")
plt.ylabel("Syntax Error Count", fontsize=10, fontweight="bold")
plt.title("LaTeX Math Delimiter and Syntax Audit Status", fontsize=11, fontweight="bold", pad=12)
plt.ylim(0, 5)
plt.text(0, 0.2, "0 Errors (100% Clean)", ha="center", fontweight="bold")
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("experiments/E25_latex_math_audit/plot.png", dpi=300)
plt.close()
print("Saved experiments/E25_latex_math_audit/plot.png")
