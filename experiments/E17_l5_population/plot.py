import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("experiments/E17_l5_population/results.csv")

plt.figure(figsize=(7, 4), dpi=300)
labels = ["Attack Flooding (97.6% Atk)", "Nominal Benign (0% Atk)"]
l5_rates = [100.0, 0.0]
plt.bar(labels, l5_rates, color=["#dc2626", "#16a34a"], width=0.45, edgecolor="black")
plt.ylabel("Level L5 Escalation Rate (%)", fontsize=10.5, fontweight="bold")
plt.title("Level L5 Engagement Under Core Hub SDN Monitoring (R >= 0.75)", fontsize=11.5, fontweight="bold", pad=12)
plt.ylim(0, 115)
for i, v in enumerate(l5_rates):
    plt.text(i, v + 3, f"{v:.1f}% ({'1,000/1,000 batches' if v==100 else '0/1,000 batches'})", ha="center", fontweight="bold")
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("experiments/E17_l5_population/plot.png", dpi=300)
plt.close()
print("Saved experiments/E17_l5_population/plot.png")
