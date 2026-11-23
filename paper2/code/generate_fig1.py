import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

os.makedirs("paper2/figures", exist_ok=True)
fig_path = "paper2/figures/fig1_posture_architecture.png"

fig, ax = plt.subplots(figsize=(12, 6.5))
ax.set_xlim(0, 100)
ax.set_ylim(0, 70)
ax.axis("off")

# Title
ax.text(50, 67, "Six-Level Security Posture Escalation Architecture", 
        ha="center", va="center", fontsize=14, fontweight="bold", color="#111111")
ax.text(50, 63.5, "Operational hierarchy mapping multi-stage component signals (Detection, Anomaly, Trust, Topology) to tiered response actions", 
        ha="center", va="center", fontsize=10, style="italic", color="#444444")

# Levels data: (Level, Name, Evidence / Conditions, Active Component Modules, Operational Action, Color, EdgeColor)
levels_data = [
    ("L0", "Normal Monitoring", "Baseline traffic; S = 0\nTrust > 80, Anomaly < 0.90", "Flow Monitor, Feature Extractor\nXGBoost Multiclass (Nominal)", "Allow\n(Cost: 0)", "#eaf2f8", "#2b5c8f"),
    ("L1", "Heightened Surveillance", "S >= 1 (Single anomaly indicator)\nConf >= 0.95 or Anomaly >= 0.90", "XGBoost Classifier + Isolation Forest\nTelemetry Logging Active", "Alert\n(Cost: +1 / -5)", "#e8f8f5", "#16a085"),
    ("L2", "Contextual Evaluation", "S >= 2 (Suspicious behavior)\nTrust <= 60, Anomaly elevated", "XGBoost + IF + ADTM Trust Engine\nAdaptive EWMA Tracking", "Restrict\n(Cost: +3 / -10)", "#fef9e7", "#f39c12"),
    ("L3", "Active Containment", "S >= 3 (Confirmed intrusion)\nTrust <= 40, Multi-vector presence", "XGBoost + IF + ADTM + TARP Graph\nEntity Streak & Anomaly Correlator", "Quarantine\n(Cost: +15 / -20)", "#fcf3cf", "#d4ac0d"),
    ("L4", "Topology Hub Isolation", "S >= 3, Trust <= 20, Families >= 2\nTARP hub isolation (100% attack)", "Full Multi-Stage Pipeline Active\nUpstream Graph Dependency Pruning", "Block (P2-tier)\n(Cost: +50 / -50)", "#fadbd8", "#e74c3c"),
    ("L5", "Adaptive Lockdown", "S >= 3, Trust <= 20, Families >= 3\nTARP >= 0.75 (Critical core hub)", "Emergency Lockdown Controller\nDistributed Blacklist Coordinator", "Block\n(Cost: +50 / -50)", "#f5b7b1", "#c0392b"),
]

y_starts = [52, 42, 32, 22, 12, 2]
h = 8.2

for i, (lvl, name, cond, mods, act, bg_col, edge_col) in enumerate(levels_data):
    y = y_starts[i]
    
    # Level Badge Box
    rect_lvl = patches.FancyBboxPatch((3, y), 10, h, boxstyle="round,pad=0.2",
                                      facecolor=edge_col, edgecolor="none")
    ax.add_patch(rect_lvl)
    ax.text(8, y + h/2, f"{lvl}\nPost", ha="center", va="center", fontsize=11, fontweight="bold", color="white")
    
    # Level Name & Conditions Box
    rect_name = patches.FancyBboxPatch((14.5, y), 31, h, boxstyle="round,pad=0.2",
                                       facecolor=bg_col, edgecolor=edge_col, linewidth=1.5)
    ax.add_patch(rect_name)
    ax.text(16, y + h - 2.2, f"{lvl}: {name}", ha="left", va="center", fontsize=10.5, fontweight="bold", color=edge_col)
    ax.text(16, y + 2.4, cond, ha="left", va="center", fontsize=8.5, color="#333333")
    
    # Active Modules Box
    rect_mods = patches.FancyBboxPatch((47, y), 34, h, boxstyle="round,pad=0.2",
                                       facecolor="#fdfefe", edgecolor="#7f8c8d", linewidth=1.2, linestyle="--")
    ax.add_patch(rect_mods)
    ax.text(48.5, y + h/2, mods, ha="left", va="center", fontsize=8.5, color="#2c3e50")
    
    # Enforcement Action Box
    rect_act = patches.FancyBboxPatch((82.5, y), 14.5, h, boxstyle="round,pad=0.2",
                                      facecolor=bg_col, edgecolor=edge_col, linewidth=1.8)
    ax.add_patch(rect_act)
    ax.text(89.75, y + h/2, act, ha="center", va="center", fontsize=9.5, fontweight="bold", color=edge_col)
    
    # Connecting arrows downward
    if i < len(levels_data) - 1:
        ax.annotate("", xy=(8, y_starts[i+1] + h), xytext=(8, y),
                    arrowprops=dict(arrowstyle="->", color="#555555", lw=1.2))

# Header labels
ax.text(8, 61, "Posture", ha="center", va="center", fontsize=9.5, fontweight="bold", color="#333333")
ax.text(30, 61, "Level Definition & Trigger Conditions", ha="center", va="center", fontsize=9.5, fontweight="bold", color="#333333")
ax.text(64, 61, "Active Pipeline Components", ha="center", va="center", fontsize=9.5, fontweight="bold", color="#333333")
ax.text(90, 61, "Enforcement Tier", ha="center", va="center", fontsize=9.5, fontweight="bold", color="#333333")

plt.tight_layout()
plt.savefig(fig_path, dpi=300)
plt.close()
print(f"Generated {fig_path} successfully ({os.path.getsize(fig_path):,} bytes)")
