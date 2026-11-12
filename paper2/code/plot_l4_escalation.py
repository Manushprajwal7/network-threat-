import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

os.makedirs("paper2/figures", exist_ok=True)
fig_path = "paper2/figures/O3_L4_escalation_analysis.png"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

# --- Panel 1: L4 Traffic Composition (0 Benign vs 15,600 Attack) ---
categories = ["Benign Traffic", "Attack Traffic"]
counts = [0, 15600]
colors = ["#2b5c8f", "#d95f02"]

bars1 = ax1.bar(categories, counts, color=colors, width=0.45, edgecolor="black", linewidth=1.2)
ax1.set_ylabel("Number of Flows in $L_4$", fontsize=12, fontweight="bold")
ax1.set_title("(a) $L_4$ Security Level Traffic Composition\n(Balanced Stratified Window)", fontsize=12, fontweight="bold", pad=12)
ax1.set_ylim(0, 18000)
ax1.grid(axis="y", linestyle="--", alpha=0.5)

# Value annotations
ax1.text(0, 300, "0 flows\n(0.00% FPR)", ha="center", va="bottom", fontsize=11, fontweight="bold", color="#2b5c8f")
ax1.text(1, 15600 + 300, "15,600 flows\n(100.00% Attack)", ha="center", va="bottom", fontsize=11, fontweight="bold", color="#d95f02")

# Highlighting zero false positives
ax1.annotate("Zero Benign Contamination!\nSafe for Maximum Escalation",
             xy=(0, 50), xytext=(0.4, 8000),
             arrowprops=dict(facecolor="#2b5c8f", shrink=0.08, width=1.5, headwidth=8),
             fontsize=10, fontweight="bold", bbox=dict(boxstyle="round,pad=0.5", facecolor="#eef3f8", edgecolor="#2b5c8f"))


# --- Panel 2: Operational Containment Cost at L4 (Quarantine vs Block) ---
# Quarantine: 15,600 attacks * (-20) = -$312,000 (Benefit = +$312k)
# Block: 15,600 attacks * (-50) = -$780,000 (Benefit = +$780k)
# Difference Delta = +$468,000
actions = ["Quarantine (P1 Default)", "Block (P2-tier Recommended)"]
benefits = [312, 780] # In thousands
colors_action = ["#e6ab02", "#e41a1c"]

bars2 = ax2.bar(actions, benefits, color=colors_action, width=0.45, edgecolor="black", linewidth=1.2)
ax2.set_ylabel("Net Containment Benefit ($k = -\\mathrm{Cost}/1000$)", fontsize=12, fontweight="bold")
ax2.set_title("(b) Operational Containment Value at $L_4$\n(Higher Benefit = Superior Containment)", fontsize=12, fontweight="bold", pad=12)
ax2.set_ylim(0, 950)
ax2.grid(axis="y", linestyle="--", alpha=0.5)

# Annotations
ax2.text(0, 312 + 15, "+$312,000\n(−$20/attack)", ha="center", va="bottom", fontsize=11, fontweight="bold")
ax2.text(1, 780 + 15, "+$780,000\n(−$50/attack)", ha="center", va="bottom", fontsize=11, fontweight="bold")

# Delta bracket and text
ax2.annotate("", xy=(1, 780), xytext=(0, 312),
             arrowprops=dict(arrowstyle="->", color="black", lw=2, ls="--"))
ax2.text(0.5, 570, "Free Improvement:\n+$468,000 Net Benefit\n(with 0% Block FPR)",
         ha="center", va="center", fontsize=11, fontweight="bold",
         bbox=dict(boxstyle="round,pad=0.6", facecolor="#fff2cc", edgecolor="#d6b656"))

# Master footnote
fig.suptitle("$L_4$ Block Escalation: $L_4$ has 0% Benign Traffic $\\rightarrow$ Block Strictly Dominates Quarantine",
             fontsize=13, fontweight="bold", y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig(fig_path, dpi=300)
plt.close()
print(f"Generated {fig_path} successfully ({os.path.getsize(fig_path):,} bytes)")
