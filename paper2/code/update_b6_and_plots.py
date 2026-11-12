import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Data records
records = [
    {
        "config": "C0'",
        "window": "Attack-heavy 60k",
        "High%": 3.21, "Moderate%": 83.69, "Low%": 13.10, "VeryLow%": 0.00, "Critical%": 0.00,
        "AUC": 0.7843, "L4%": 0.00, "L5%": 0.00,
        "mean_atk": 65.83, "mean_ben": 73.79, "sample_gap": 7.96, "entity_gap": 7.79
    },
    {
        "config": "C1'",
        "window": "Attack-heavy 60k",
        "High%": 0.14, "Moderate%": 2.50, "Low%": 3.83, "VeryLow%": 93.53, "Critical%": 0.00,
        "AUC": 0.8969, "L4%": 0.00, "L5%": 0.00,
        "mean_atk": 33.27, "mean_ben": 41.75, "sample_gap": 8.48, "entity_gap": 7.79
    },
    {
        "config": "C2'",
        "window": "Attack-heavy 60k",
        "High%": 0.12, "Moderate%": 1.00, "Low%": 3.16, "VeryLow%": 35.38, "Critical%": 60.34,
        "AUC": 0.9468, "L4%": 90.50, "L5%": 6.50,
        "mean_atk": 19.37, "mean_ben": 41.73, "sample_gap": 22.36, "entity_gap": 21.68
    },
    {
        "config": "C3'",
        "window": "Attack-heavy 60k",
        "High%": 0.09, "Moderate%": 0.18, "Low%": 2.50, "VeryLow%": 33.77, "Critical%": 63.46,
        "AUC": 0.9641, "L4%": 90.50, "L5%": 6.50,
        "mean_atk": 15.95, "mean_ben": 40.40, "sample_gap": 24.45, "entity_gap": 23.75
    },
    {
        "config": "C4'",
        "window": "Attack-heavy 500k",
        "High%": 0.06, "Moderate%": 0.14, "Low%": 2.25, "VeryLow%": 33.84, "Critical%": 63.71,
        "AUC": 0.9644, "L4%": 90.50, "L5%": 6.50,
        "mean_atk": 15.84, "mean_ben": 39.70, "sample_gap": 23.86, "entity_gap": 23.65
    },
    {
        "config": "C4' (Bal)",
        "window": "Stratified Balanced 60k",
        "High%": 38.19, "Moderate%": 4.15, "Low%": 9.48, "VeryLow%": 15.51, "Critical%": 32.67,
        "AUC": 0.9774, "L4%": 26.00, "L5%": 2.50,
        "mean_atk": 19.25, "mean_ben": 77.96, "sample_gap": 58.72, "entity_gap": 72.83
    }
]

csv_path = "paper2/tables/O2_B6_combined_configs.csv"
with open(csv_path, "w", encoding="utf-8") as f:
    f.write("config,window,High%,Moderate%,Low%,VeryLow%,Critical%,AUC(trust,attack),L4_entities%,L5_entities%,mean_trust_attack,mean_trust_benign,sample_trust_gap,entity_trust_gap\n")
    for r in records:
        f.write(f"{r['config']},{r['window']},{r['High%']:.2f},{r['Moderate%']:.2f},{r['Low%']:.2f},{r['VeryLow%']:.2f},{r['Critical%']:.2f},{r['AUC']:.4f},{r['L4%']:.2f},{r['L5%']:.2f},{r['mean_atk']:.2f},{r['mean_ben']:.2f},{r['sample_gap']:.2f},{r['entity_gap']:.2f}\n")

print(f"Updated {csv_path}")

# Update stacked bar chart
fig_bar_path = "paper2/figures/O2_B_band_distribution_comparison.png"
cfg_labels = [r["config"] for r in records]
highs = [r["High%"] for r in records]
mods = [r["Moderate%"] for r in records]
lows = [r["Low%"] for r in records]
vlows = [r["VeryLow%"] for r in records]
crits = [r["Critical%"] for r in records]

x = np.arange(len(cfg_labels))
width = 0.55

plt.figure(figsize=(10, 5))
plt.bar(x, highs, width, label="High (80-100)", color="#16a34a")
plt.bar(x, mods, width, bottom=highs, label="Moderate (60-79)", color="#0284c7")
plt.bar(x, lows, width, bottom=np.array(highs)+np.array(mods), label="Low (40-59)", color="#f59e0b")
plt.bar(x, vlows, width, bottom=np.array(highs)+np.array(mods)+np.array(lows), label="Very Low (20-39)", color="#ea580c")
plt.bar(x, crits, width, bottom=np.array(highs)+np.array(mods)+np.array(lows)+np.array(vlows), label="Critical (0-19)", color="#dc2626")

plt.xticks(x, cfg_labels, fontsize=10, fontweight="bold")
plt.ylabel("Population Share (%)", fontsize=11)
plt.title("ADTM Trust Band Distribution Across Recalibrated Configurations & Windows", fontsize=12, fontweight="bold")
plt.legend(loc="upper right", framealpha=0.9, fontsize=9)
plt.ylim(0, 100)
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(fig_bar_path, dpi=300)
plt.close()
print(f"Saved {fig_bar_path}")

# Update heatmap
fig_heat_path = "paper2/figures/O2_B6_config_heatmap.png"
metrics_mat = np.array([
    [r["AUC"], r["L4%"], r["L5%"], r["sample_gap"]]
    for r in records
])
m_names = ["AUC(trust, atk)", "L4 Entities (%)", "L5 Entities (%)", "Sample Gap (pts)"]

fig, ax = plt.subplots(figsize=(8, 6))
cax = ax.matshow(metrics_mat, cmap="YlGnBu", aspect="auto")
for i in range(len(records)):
    for j in range(len(m_names)):
        val = metrics_mat[i, j]
        fmt = f"{val:.4f}" if j == 0 else (f"{val:.2f}%" if j in [1, 2] else f"{val:.2f}")
        ax.text(j, i, fmt, ha="center", va="center", color="black" if val < 50 else "white", fontweight="bold", fontsize=9)

ax.set_xticks(np.arange(len(m_names)))
ax.set_yticks(np.arange(len(records)))
ax.set_xticklabels(m_names, fontweight="bold", fontsize=10)
ax.set_yticklabels([f"{r['config']} ({r['window']})" for r in records], fontweight="bold", fontsize=9)
plt.title("Summary Evaluation Metrics across Trust Recalibrations", fontsize=12, fontweight="bold", pad=20)
plt.colorbar(cax)
plt.tight_layout()
plt.savefig(fig_heat_path, dpi=300)
plt.close()
print(f"Saved {fig_heat_path}")
