import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

os.makedirs("paper2/figures", exist_ok=True)
fig_path = "paper2/figures/fig4_two_window_distribution.png"

df_atk = pd.read_csv("paper2/tables/O2_B6_attack_60k.csv")
df_bal = pd.read_csv("paper2/tables/O2_B6_balanced_flowlevel.csv")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

x = np.arange(6)
width = 0.38
levels = ["L0", "L1", "L2", "L3", "L4", "L5"]

# --- Panel (a): Attack-Heavy Window (97.5% Attack Base Rate) ---
bars1 = ax1.bar(x - width/2, df_atk["share%"], width, label="Entity Share (%)", color="#2b5c8f", edgecolor="black")
bars2 = ax1.bar(x + width/2, df_atk["attack%"], width, label="Attack Traffic (%)", color="#d95f02", edgecolor="black")

ax1.set_xlabel("Security Posture Level", fontsize=11, fontweight="bold")
ax1.set_ylabel("Percentage (%)", fontsize=11, fontweight="bold")
ax1.set_title("(a) Attack-Heavy 60k Window (97.5% Base Rate)\nUpper containment tiers active under sustained siege", fontsize=12, fontweight="bold", pad=12)
ax1.set_xticks(x)
ax1.set_xticklabels(levels, fontsize=10, fontweight="bold")
ax1.set_ylim(0, 115)
ax1.grid(axis="y", linestyle="--", alpha=0.5)
ax1.legend(loc="upper left", frameon=True, fontsize=10)

# Values on bars
for bar in bars1:
    h = bar.get_height()
    if h > 0:
        ax1.text(bar.get_x() + bar.get_width()/2., h + 1.5, f"{h:.1f}%", ha="center", va="bottom", fontsize=8.5, fontweight="bold")
    else:
        ax1.text(bar.get_x() + bar.get_width()/2., 1.5, "0%", ha="center", va="bottom", fontsize=8.5, color="#888888")

for bar in bars2:
    h = bar.get_height()
    if h > 0:
        ax1.text(bar.get_x() + bar.get_width()/2., h + 1.5, f"{h:.1f}%", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#d95f02")

ax1.annotate("L0-L2 Empty\n(No Benign Entities)", xy=(1, 5), xytext=(0.5, 35),
             arrowprops=dict(arrowstyle="->", color="#555555", lw=1.2),
             ha="center", fontsize=9.5, fontweight="bold", bbox=dict(boxstyle="round,pad=0.4", facecolor="#f2f2f2", edgecolor="#888888"))


# --- Panel (b): Stratified Balanced Window (30/40/30) ---
bars3 = ax2.bar(x - width/2, df_bal["share%"], width, label="Entity Share (%)", color="#2b5c8f", edgecolor="black")
bars4 = ax2.bar(x + width/2, df_bal["attack%"], width, label="Attack Traffic (%)", color="#d95f02", edgecolor="black")

ax2.set_xlabel("Security Posture Level", fontsize=11, fontweight="bold")
ax2.set_ylabel("Percentage (%)", fontsize=11, fontweight="bold")
ax2.set_title("(b) Stratified Balanced Window (30/40/30)\nFull monotonic escalation across all six posture tiers", fontsize=12, fontweight="bold", pad=12)
ax2.set_xticks(x)
ax2.set_xticklabels(levels, fontsize=10, fontweight="bold")
ax2.set_ylim(0, 115)
ax2.grid(axis="y", linestyle="--", alpha=0.5)
ax2.legend(loc="upper left", frameon=True, fontsize=10)

# Values on bars
for bar in bars3:
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., h + 1.5, f"{h:.1f}%", ha="center", va="bottom", fontsize=8.5, fontweight="bold")

for bar in bars4:
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., h + 1.5, f"{h:.1f}%", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#d95f02")

# Monotonicity annotation
ax2.annotate("Strictly Monotonic Attack% Escalation:\n0.0% -> 39.7% -> 57.4% -> 57.6% -> 100.0% -> 100.0%",
             xy=(3, 75), xytext=(2.8, 95),
             ha="center", fontsize=9.5, fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.5", facecolor="#eef3f8", edgecolor="#2b5c8f"))

plt.tight_layout()
plt.savefig(fig_path, dpi=300)
plt.close()
print(f"Generated {fig_path} successfully ({os.path.getsize(fig_path):,} bytes)")
