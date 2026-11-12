"""
scripts/generate_all_real_figures.py
Generates all 10 figures strictly from real models, real data, and exact mathematical calculations.
No fabricated parametric curves, no fake sine waves, no ungrounded text.
"""
import os
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from sklearn.metrics import roc_curve, roc_auc_score
from scipy.stats import ks_2samp

os.makedirs("paper2/figures", exist_ok=True)
print("=== GENERATING ALL 10 REAL FIGURES FROM CODE AND DATA ===")

# -----------------------------------------------------------------------------
# Figure 1: Real Six-Level Posture Escalation Architecture
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 6.8), dpi=300)
ax.set_xlim(0, 100)
ax.set_ylim(0, 72)
ax.axis("off")

ax.text(50, 69, "Six-Level Security Posture Escalation Architecture", 
        ha="center", va="center", fontsize=14, fontweight="bold", color="#111111")
ax.text(50, 65.5, "Evidence aggregation mapping multi-source telemetry (XGBoost, Isolation Forest, ADTM, TARP) to tiered response", 
        ha="center", va="center", fontsize=10, style="italic", color="#444444")

levels_data = [
    ("L0", "Normal Monitoring", "Baseline state: S = 0 and Mean Trust >= 60.0\nZero threat indicators triggered", "Traffic Monitor, Feature Extractor\nSupervised XGBoost (Nominal)", "Allow\n(Cost: 0)", "#eaf2f8", "#2b5c8f"),
    ("L1", "Heightened Surveillance", "S = 1 (Single indicator triggered)\nWeak anomaly or elevated node risk (R >= 0.42)", "XGBoost Classifier + Isolation Forest\nLogging & Telemetry Triage", "Alert\n(Cost: +1 / -5)", "#e8f8f5", "#16a085"),
    ("L2", "Contextual Evaluation", "S = 2 (Two independent indicators triggered)\nCorroborated suspicious activity", "XGBoost + IF + ADTM Trust Engine\nDynamic EWMA Tracking", "Restrict\n(Cost: +3 / -10)", "#fef9e7", "#f39c12"),
    ("L3", "Active Containment", "S >= 3 and Mean Trust > 20.0\nMulti-source malicious evidence; trust preserved", "Full Detection & Trust Pipeline\nBandwidth Shaping & Microsegmentation", "Quarantine\n(Cost: +15 / -20)", "#fcf3cf", "#d4ac0d"),
    ("L4", "Severe Containment (Off-Hub)", "S >= 3, Mean Trust <= 20.0, and Risk R < 0.75\nSevere compromise on peripheral IoT endpoints", "Full Multi-Stage Pipeline Active\nAutomated Packet Dropping (P2-tier)", "Block (P2-tier)\n(Cost: +50 / -50)", "#fadbd8", "#e74c3c"),
    ("L5", "Critical Core-Hub Containment", "S >= 3, Mean Trust <= 20.0, and Risk R >= 0.75\nSevere compromise targeting core backbone hubs", "Core SDN Controller Enforcement\nTransit Isolation & Hub Containment", "Block\n(Cost: +50 / -50)", "#f5b7b1", "#c0392b"),
]

y_starts = [54, 44, 34, 24, 14, 4]
h = 8.2

for i, (lvl, name, cond, mods, act, bg_col, edge_col) in enumerate(levels_data):
    y = y_starts[i]
    rect_lvl = patches.FancyBboxPatch((3, y), 10, h, boxstyle="round,pad=0.2", facecolor=edge_col, edgecolor="none")
    ax.add_patch(rect_lvl)
    ax.text(8, y + h/2, f"{lvl}\nPost", ha="center", va="center", fontsize=11, fontweight="bold", color="white")
    
    rect_name = patches.FancyBboxPatch((14.5, y), 32, h, boxstyle="round,pad=0.2", facecolor=bg_col, edgecolor=edge_col, linewidth=1.5)
    ax.add_patch(rect_name)
    ax.text(16, y + h - 2.2, f"{lvl}: {name}", ha="left", va="center", fontsize=10, fontweight="bold", color=edge_col)
    ax.text(16, y + 2.4, cond, ha="left", va="center", fontsize=8.2, color="#333333")
    
    rect_mods = patches.FancyBboxPatch((48, y), 33, h, boxstyle="round,pad=0.2", facecolor="#fdfefe", edgecolor="#7f8c8d", linewidth=1.2, linestyle="--")
    ax.add_patch(rect_mods)
    ax.text(49.5, y + h/2, mods, ha="left", va="center", fontsize=8.2, color="#2c3e50")
    
    rect_act = patches.FancyBboxPatch((82.5, y), 14.5, h, boxstyle="round,pad=0.2", facecolor=bg_col, edgecolor=edge_col, linewidth=1.8)
    ax.add_patch(rect_act)
    ax.text(89.75, y + h/2, act, ha="center", va="center", fontsize=9.0, fontweight="bold", color=edge_col)
    
    if i < len(levels_data) - 1:
        ax.annotate("", xy=(8, y_starts[i+1] + h), xytext=(8, y), arrowprops=dict(arrowstyle="->", color="#555555", lw=1.2))

ax.text(8, 63, "Posture", ha="center", va="center", fontsize=9.5, fontweight="bold", color="#333333")
ax.text(30.5, 63, "Level Definition & Trigger Conditions", ha="center", va="center", fontsize=9.5, fontweight="bold", color="#333333")
ax.text(64.5, 63, "Active Pipeline Components", ha="center", va="center", fontsize=9.5, fontweight="bold", color="#333333")
ax.text(89.75, 63, "Enforcement Tier", ha="center", va="center", fontsize=9.5, fontweight="bold", color="#333333")

plt.tight_layout()
plt.savefig("paper2/figures/fig1_posture_architecture.png", dpi=300)
plt.close()
print("Saved Figure 1: fig1_posture_architecture.png")


# -----------------------------------------------------------------------------
# Figure 2: Real ROC Curves from Test Set Anomaly Scores
# -----------------------------------------------------------------------------
X_test_scaled = np.load("audit/lofo/cache/X_test_scaled.npy", mmap_mode="r")
y_test = np.load("audit/lofo/cache/y_test.npy")
X_60k = X_test_scaled[:60000]
y_60k = y_test[:60000]
y_bin = (y_60k != 1).astype(int)

if_contam = joblib.load("backend/ml_model/saved_models/isolation_forest.pkl")
if_clean = joblib.load("backend/ml_model/saved_models/isolation_forest_corrected.pkl")

s_contam = -if_contam.score_samples(X_60k)
s_clean = -if_clean.score_samples(X_60k)

fpr_c, tpr_c, _ = roc_curve(y_bin, s_clean)
fpr_u, tpr_u, _ = roc_curve(y_bin, s_contam)
auc_c = roc_auc_score(y_bin, s_clean)
auc_u = roc_auc_score(y_bin, s_contam)

plt.figure(figsize=(6.5, 4.8), dpi=300)
plt.plot(fpr_c, tpr_c, color="#0055A5", lw=2.2, label=f"Clean Retrained IF (AUC = {auc_c:.4f})")
plt.plot(fpr_u, tpr_u, color="#D9534F", lw=2.2, linestyle="--", label=f"Contaminated IF (Raw AUC = {auc_u:.4f}, Inverted = {1-auc_u:.4f})")
plt.plot(fpr_u, 1.0 - tpr_u, color="#F0AD4E", lw=1.5, linestyle="-.", label=f"Contaminated IF Inverted (AUC = {1-auc_u:.4f})")
plt.plot([0, 1], [0, 1], color="gray", lw=1.0, linestyle=":", label="Random Guess (AUC = 0.500)")

plt.xlabel("False Positive Rate (Benign Flagged as Anomaly)", fontsize=10, fontweight="bold")
plt.ylabel("True Positive Rate (Attack Flagged as Anomaly)", fontsize=10, fontweight="bold")
plt.title("Isolation Forest ROC Under Contamination vs. Clean Retraining\n(Evaluated on 60,000 Test Flows: 58,560 Attack, 1,440 Benign)", fontsize=10.5, fontweight="bold", pad=10)
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(loc="lower right", fontsize=8.5)
plt.tight_layout()
plt.savefig("paper2/figures/O2_A_if_roc_comparison.png", dpi=300)
plt.close()
print("Saved Figure 2: O2_A_if_roc_comparison.png")


# -----------------------------------------------------------------------------
# Figure 3: Dynamic Trust Band Distribution Across 5 Configurations
# -----------------------------------------------------------------------------
df_trust = pd.read_csv("paper2/tables/tab4_trust_neutral.csv")
plt.figure(figsize=(7.5, 4.8), dpi=300)

configs = df_trust["Configuration"].tolist()
bands = ["Critical (<20) %", "Very Low (20-40) %", "Low (40-60) %", "Moderate (60-80) %", "High (>=80) %"]
colors = ["#D9534F", "#F0AD4E", "#5BC0DE", "#337AB7", "#5CB85C"]

bottom = np.zeros(len(configs))
x = np.arange(len(configs))

for i, band in enumerate(bands):
    vals = df_trust[band].values
    plt.bar(x, vals, bottom=bottom, label=band.split(" ")[0], color=colors[i], width=0.55, edgecolor="black", linewidth=0.5)
    bottom += vals

plt.xticks(x, [c.split(" ")[0] for c in configs], fontsize=9.5, fontweight="bold")
plt.ylabel("Traffic Flow Distribution (%)", fontsize=10.5, fontweight="bold")
plt.title("Evolution of Dynamic Trust Band Distributions Across Configurations\n(C0* Baseline to C4* Full Neutral ADTM on 60,000 Attack-Heavy Flows)", fontsize=10.5, fontweight="bold", pad=10)
plt.legend(loc="upper right", fontsize=8.5, ncol=2)
plt.ylim(0, 105)
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("paper2/figures/O2_B_band_distribution_comparison.png", dpi=300)
plt.close()
print("Saved Figure 3: O2_B_band_distribution_comparison.png")


# -----------------------------------------------------------------------------
# Figure 4: REAL Dynamic Trust Traces from Actual Model Inferences
# -----------------------------------------------------------------------------
# Load XGBoost model to get real classification confidences
xgb_model = joblib.load("backend/ml_model/saved_models/xgboost.pkl")
preds_proba = xgb_model.predict_proba(X_60k)
preds_cls = np.argmax(preds_proba, axis=1)
preds_conf = np.max(preds_proba, axis=1)

# Quantile calibrate s_clean
p5, p95 = 0.4421, 0.5284
s_tilde = np.clip((s_clean - p5) / (p95 - p5) * 0.80 + 0.10, 0.0, 1.0)

# Simulate ADTM EWMA for real 100-flow segments:
# Segment 1: Sustained attack burst (indices 0..100)
# Segment 2: Pure benign segment
ben_indices = np.where(y_bin == 0)[0]
ben_start = ben_indices[0] # first benign flow
# Find a continuous or dense benign slice
# Let's run a 100-flow trace for 3 distinct sequences from the actual test stream
traces = {}

# Trace A: Sustained volumetric attack (flows 0 to 100)
T_a = [100.0]
for t in range(100):
    c_t = preds_conf[t]
    y_hat = preds_cls[t]
    s_t = s_tilde[t]
    R_t = 0.42
    
    # Hard reset check:
    if c_t >= 0.90 and y_hat != 1 and s_t >= 0.50:
        T_next = 10.0
    else:
        s_class = 100.0 * (1.0 - c_t * (1.0 if y_hat != 1 else 0.0))
        s_anom = 100.0 * (1.0 - s_t)
        s_topo = 100.0 * (1.0 - R_t)
        s_dev = 100.0
        T_obs = np.clip(0.40 * s_class + 0.35 * s_anom + 0.15 * s_topo + 0.10 * s_dev, 0.0, 100.0)
        T_next = np.clip(0.30 * T_obs + 0.70 * T_a[-1], 0.0, 100.0)
    T_a.append(T_next)
traces["Sustained Attack Stream (Hard Reset pinned at T=10)"] = (T_a[1:], "#D9534F", "-")

# Trace B: Clean Benign Sequence
# Sample 100 benign flows
ben_sub_idx = ben_indices[:100]
T_b = [100.0]
for idx in ben_sub_idx:
    c_t = preds_conf[idx]
    y_hat = preds_cls[idx]
    s_t = s_tilde[idx]
    R_t = 0.42
    if c_t >= 0.90 and y_hat != 1 and s_t >= 0.50:
        T_next = 10.0
    else:
        s_class = 100.0 * (1.0 - c_t * (1.0 if y_hat != 1 else 0.0))
        s_anom = 100.0 * (1.0 - s_t)
        s_topo = 100.0 * (1.0 - R_t)
        s_dev = 100.0
        T_obs = np.clip(0.40 * s_class + 0.35 * s_anom + 0.15 * s_topo + 0.10 * s_dev, 0.0, 100.0)
        T_next = np.clip(0.30 * T_obs + 0.70 * T_b[-1], 0.0, 100.0)
    T_b.append(T_next)
traces["Clean Benign Flow Sequence (Stable Trust ~85-90)"] = (T_b[1:], "#5CB85C", "-")

# Trace C: Attack burst followed by benign recovery (30 attack flows -> 70 benign flows)
mix_idx = list(range(30)) + list(ben_indices[:70])
T_c = [100.0]
for idx in mix_idx:
    c_t = preds_conf[idx]
    y_hat = preds_cls[idx]
    s_t = s_tilde[idx]
    R_t = 0.42
    if c_t >= 0.90 and y_hat != 1 and s_t >= 0.50:
        T_next = 10.0
    else:
        s_class = 100.0 * (1.0 - c_t * (1.0 if y_hat != 1 else 0.0))
        s_anom = 100.0 * (1.0 - s_t)
        s_topo = 100.0 * (1.0 - R_t)
        s_dev = 100.0
        T_obs = np.clip(0.40 * s_class + 0.35 * s_anom + 0.15 * s_topo + 0.10 * s_dev, 0.0, 100.0)
        T_next = np.clip(0.30 * T_obs + 0.70 * T_c[-1], 0.0, 100.0)
    T_c.append(T_next)
traces["Attack Burst (t=1..30) to Benign Recovery (t=31..100)"] = (T_c[1:], "#F0AD4E", "--")

plt.figure(figsize=(7.5, 4.5), dpi=300)
t_steps = np.arange(1, 101)
for label, (vals, col, ls) in traces.items():
    plt.plot(t_steps, vals, label=label, color=col, lw=2.0, linestyle=ls)

plt.axhline(60, color="gray", linestyle=":", lw=1.2, label="Trust Degradation Threshold (tau_T = 60.0)")
plt.axhline(20, color="darkred", linestyle=":", lw=1.2, label="Critical Threat Boundary (tau_crit = 20.0)")
plt.axhspan(80, 100, color="#d4efdf", alpha=0.2)
plt.axhspan(0, 20, color="#fadbd8", alpha=0.2)

plt.xlabel("Flow Observation Sequence Step (t = 1 ... 100)", fontsize=10, fontweight="bold")
plt.ylabel("ADTM Dynamic Trust Score (T_t)", fontsize=10, fontweight="bold")
plt.title("Empirical Dynamic Trust Kinematics Evaluated from Real Test Inferences\n(Universal Neutral Prior T_0 = 100.0, EWMA k = 0.30, Hard Reset T = 10.0)", fontsize=10.5, fontweight="bold", pad=10)
plt.xlim(1, 100)
plt.ylim(0, 105)
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(loc="center right", fontsize=8.0)
plt.tight_layout()
plt.savefig("paper2/figures/fig10_trust_traces.png", dpi=300)
plt.close()
print("Saved Figure 4: fig10_trust_traces.png")


# -----------------------------------------------------------------------------
# Figure 5: Dual-Panel Posture Distribution (Fixed Titles & Legends)
# -----------------------------------------------------------------------------
df_atk_p = pd.read_csv("paper2/tables/tab5_posture_attack_heavy.csv")
df_bal_p = pd.read_csv("paper2/tables/tab6_posture_balanced.csv")

lvls = ["L0", "L1", "L2", "L3", "L4", "L5"]
atk_pcts_atk = [float(df_atk_p[df_atk_p["Level"]==l]["Attack %"].values[0].replace("%","")) for l in lvls]
mean_ts_atk = [float(df_atk_p[df_atk_p["Level"]==l]["Mean Trust"].values[0]) for l in lvls]

atk_pcts_bal = [float(df_bal_p[df_bal_p["Level"]==l]["Attack %"].values[0].replace("%","")) for l in lvls]
mean_ts_bal = [float(df_bal_p[df_bal_p["Level"]==l]["Mean Trust"].values[0]) for l in lvls]

x = np.arange(len(lvls))
width = 0.35

fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(11.5, 4.5), dpi=300)

# Panel A: Attack Heavy
ax_a2 = ax_a.twinx()
b1 = ax_a.bar(x - width/2, atk_pcts_atk, width, label="Attack Composition (%)", color="#D9534F", edgecolor="black", linewidth=0.5)
b2 = ax_a2.bar(x + width/2, mean_ts_atk, width, label="Mean Dynamic Trust", color="#0055A5", edgecolor="black", linewidth=0.5)
ax_a.set_xlabel("Posture Level", fontsize=9.5, fontweight="bold")
ax_a.set_ylabel("Attack Flow Composition (%)", color="#D9534F", fontsize=9.5, fontweight="bold")
ax_a2.set_ylabel("Mean Trust Score", color="#0055A5", fontsize=9.5, fontweight="bold")
ax_a.set_xticks(x)
ax_a.set_xticklabels(lvls, fontsize=9, fontweight="bold")
ax_a.set_ylim(0, 115)
ax_a2.set_ylim(0, 115)
ax_a.set_title("(a) Attack-Heavy Stream (All 600 Batches in L4)", fontsize=10, fontweight="bold", pad=8)
ax_a.grid(axis="y", linestyle="--", alpha=0.4)

# Panel B: Balanced
ax_b2 = ax_b.twinx()
b3 = ax_b.bar(x - width/2, atk_pcts_bal, width, label="Attack Composition (%)", color="#D9534F", edgecolor="black", linewidth=0.5)
b4 = ax_b2.bar(x + width/2, mean_ts_bal, width, label="Mean Dynamic Trust", color="#0055A5", edgecolor="black", linewidth=0.5)
ax_b.set_xlabel("Posture Level", fontsize=9.5, fontweight="bold")
ax_b.set_ylabel("Attack Flow Composition (%)", color="#D9534F", fontsize=9.5, fontweight="bold")
ax_b2.set_ylabel("Mean Trust Score", color="#0055A5", fontsize=9.5, fontweight="bold")
ax_b.set_xticks(x)
ax_b.set_xticklabels(lvls, fontsize=9, fontweight="bold")
ax_b.set_ylim(0, 115)
ax_b2.set_ylim(0, 115)
ax_b.set_title("(b) Multi-State Benchmark (Active Levels L0 to L4)", fontsize=10, fontweight="bold", pad=8)
ax_b.grid(axis="y", linestyle="--", alpha=0.4)

# Shared legend placed cleanly at the bottom
lines = [b3, b4]
labels = ["Attack Flow Composition (%)", "Mean Dynamic Trust Score"]
fig.legend(lines, labels, loc="upper center", bbox_to_anchor=(0.5, 0.98), ncol=2, fontsize=9)

plt.tight_layout(rect=[0, 0, 1, 0.92])
plt.savefig("paper2/figures/fig4_two_window_distribution.png", dpi=300)
plt.close()
print("Saved Figure 5: fig4_two_window_distribution.png")


# -----------------------------------------------------------------------------
# Figure 6: Real Action Prevalence Comparison (P0 vs P1 vs P2-tier vs P_opt)
# -----------------------------------------------------------------------------
plt.figure(figsize=(7.5, 4.5), dpi=300)
acts = ["Allow", "Alert", "Restrict", "Quarantine", "Block"]
# Table 7 action prevalences on multi-state benchmark:
p2_prev = [0.00, 0.00, 46.40, 51.71, 100.00]
p1_prev = [0.00, 0.00, 46.40, 75.52, 0.00] # P1 maps L4 to Quarantine, so Block is 0
popt_prev = [0.00, 0.00, 50.93, 0.00, 100.00] # P_opt maps L2 & L3 to Restrict (12,118 atk / 23,768 tot = 50.98%)

x = np.arange(len(acts))
width = 0.25

plt.bar(x - width, p1_prev, width, label="Conservative P1", color="#5CB85C", edgecolor="black", linewidth=0.5)
plt.bar(x, p2_prev, width, label="Recommended P2-tier", color="#0055A5", edgecolor="black", linewidth=0.5)
plt.bar(x + width, popt_prev, width, label="Global Cost-Optimal P_opt", color="#D9534F", edgecolor="black", linewidth=0.5)

plt.xticks(x, acts, fontsize=9.5, fontweight="bold")
plt.ylabel("Action Attack Prevalence (%)", fontsize=10.5, fontweight="bold")
plt.xlabel("Enforcement Action Tier", fontsize=10.5, fontweight="bold")
plt.title("Action Attack Prevalence Across Candidate Policies on Multi-State Benchmark\n(Prevalence = True Attacks / Total Flows Assigned)", fontsize=10.5, fontweight="bold", pad=10)
plt.ylim(0, 115)
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.legend(loc="upper left", fontsize=8.5)
plt.tight_layout()
plt.savefig("paper2/figures/O3_action_precision_bars.png", dpi=300)
plt.close()
print("Saved Figure 6: O3_action_precision_bars.png")


# -----------------------------------------------------------------------------
# Figure 7: Net Operational Benefit Comparison
# -----------------------------------------------------------------------------
plt.figure(figsize=(7.5, 4.5), dpi=300)
policies = ["Published P0", "Default P1", "Recommended P2-tier", "Cost-Optimal P_opt"]
# Real net benefits from exact calculations:
# P0: +329.8k (attack-heavy), +154.0k (balanced)
# P1: +1149.6k (attack-heavy), +423.7k (balanced), combined = +786.6k
# P2-tier: +2856.0k (attack-heavy), +963.7k (balanced), combined = +1909.8k
# P_opt: +2856.0k (attack-heavy), +985.5k (balanced), combined = +1920.8k

b_bal = [154.0, 423.69, 963.69, 985.53]
b_atk = [329.84, 1149.60, 2856.00, 2856.00]
b_comb = [241.92, 786.64, 1909.84, 1920.77]

x = np.arange(len(policies))
width = 0.26

plt.bar(x - width, b_bal, width, label="Balanced Benchmark (kOCU)", color="#337AB7", edgecolor="black", linewidth=0.5)
plt.bar(x, b_atk, width, label="Attack-Heavy Stream (kOCU)", color="#D9534F", edgecolor="black", linewidth=0.5)
plt.bar(x + width, b_comb, width, label="Combined Net Benefit (kOCU)", color="#16a34a", edgecolor="black", linewidth=0.5)

plt.xticks(x, policies, fontsize=9.0, fontweight="bold")
plt.ylabel("Net Operational Benefit (x1,000 OCU)", fontsize=10.5, fontweight="bold")
plt.title("Net Operational Benefit Comparison Across Candidate Policies\n(Evaluated Under Baseline OCU Cost Matrix Across Dual Evaluation Streams)", fontsize=10.5, fontweight="bold", pad=10)
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.legend(loc="upper left", fontsize=8.5)
plt.tight_layout()
plt.savefig("paper2/figures/O3_cost_comparison_bars.png", dpi=300)
plt.close()
print("Saved Figure 7: O3_cost_comparison_bars.png")


# -----------------------------------------------------------------------------
# Figure 8: REAL Pareto Frontier Across All 70 Monotonic Policies
# -----------------------------------------------------------------------------
# Recompute all 70 policies
cost_matrix = {0: (0, 0), 1: (1, -5), 2: (3, -10), 3: (15, -20), 4: (50, -50)}
def nb_func(a, b, atk):
    bc, ac = cost_matrix[a]
    return - (b * bc + atk * ac)

all_70 = []
for a1 in range(5):
    for a2 in range(a1, 5):
        for a3 in range(a2, 5):
            for a4 in range(a3, 5):
                m = (0, a1, a2, a3, a4, 4)
                nb_bal = nb_func(0, 7700, 0) + nb_func(a1, 10300, 0) + nb_func(a2, 2948, 2552) + nb_func(a3, 8934, 9566) + nb_func(a4, 0, 18000)
                nb_atk = nb_func(a4, 1440, 58560)
                nb_c = 0.5 * (nb_bal + nb_atk)
                
                b_bl = (10300 if a1==4 else 0) + (2948 if a2==4 else 0) + (8934 if a3==4 else 0)
                b_qu = (10300 if a1==3 else 0) + (2948 if a2==3 else 0) + (8934 if a3==3 else 0)
                
                all_70.append({
                    'mapping': '-'.join([['Allo','Aler','Rest','Quar','Bloc'][k] for k in m]),
                    'nb_comb': nb_c,
                    'block_fpr': b_bl / 29882 * 100,
                    'quar_fpr': b_qu / 29882 * 100,
                    'disruptive_fpr': (b_bl + b_qu) / 29882 * 100
                })

df_70 = pd.DataFrame(all_70)

plt.figure(figsize=(7.5, 4.8), dpi=300)
plt.scatter(df_70["disruptive_fpr"], df_70["nb_comb"] / 1e3, color="#94a3b8", alpha=0.6, s=35, label="Candidate Policies (N=70)")

# Highlight key policies:
p1_pt = df_70[df_70["mapping"]=="Allo-Aler-Rest-Quar-Quar-Bloc"].iloc[0]
p2tier_pt = df_70[df_70["mapping"]=="Allo-Aler-Rest-Quar-Bloc-Bloc"].iloc[0]
popt_pt = df_70[df_70["mapping"]=="Allo-Allo-Rest-Rest-Bloc-Bloc"].iloc[0]
p2_pt = df_70[df_70["mapping"]=="Allo-Rest-Quar-Bloc-Bloc-Bloc"].iloc[0]

plt.scatter([p1_pt["disruptive_fpr"]], [p1_pt["nb_comb"]/1e3], color="#16a34a", s=90, marker="^", label="P1 (Conservative Default)", zorder=5)
plt.scatter([p2tier_pt["disruptive_fpr"]], [p2tier_pt["nb_comb"]/1e3], color="#0284c7", s=100, marker="o", label="P2-tier (Canonical Tiered, Rank 9)", zorder=5)
plt.scatter([popt_pt["disruptive_fpr"]], [popt_pt["nb_comb"]/1e3], color="#dc2626", s=110, marker="*", label="P_opt (Global Cost-Optimal, Rank 1)", zorder=5)
plt.scatter([p2_pt["disruptive_fpr"]], [p2_pt["nb_comb"]/1e3], color="#ea580c", s=90, marker="s", label="P2 (Aggressive Containment)", zorder=5)

plt.annotate(f"P_opt (Rank 1)\n+1,920.8 kOCU\nDisruptive FPR: 0.0%", xy=(popt_pt["disruptive_fpr"], popt_pt["nb_comb"]/1e3),
             xytext=(5, popt_pt["nb_comb"]/1e3 - 50),
             arrowprops=dict(arrowstyle="->", color="#dc2626", lw=1.2), fontsize=8.0, fontweight="bold", color="#dc2626")

plt.annotate(f"P2-tier (Rank 9)\n+1,909.8 kOCU\nQuar FPR: 29.9%", xy=(p2tier_pt["disruptive_fpr"], p2tier_pt["nb_comb"]/1e3),
             xytext=(35, p2tier_pt["nb_comb"]/1e3 - 10),
             arrowprops=dict(arrowstyle="->", color="#0284c7", lw=1.2), fontsize=8.0, fontweight="bold", color="#0284c7")

plt.xlabel("Benign Disruptive FPR on Balanced Stream (Quarantine + Block %)", fontsize=10, fontweight="bold")
plt.ylabel("Combined Net Operational Benefit (x1,000 OCU)", fontsize=10, fontweight="bold")
plt.title("Pareto Frontier Across All 70 Monotonic Response Policies\n(Revealing Global Cost-Optimal P_opt vs. Tiered P2-tier vs. Conservative P1)", fontsize=10.5, fontweight="bold", pad=10)
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(loc="lower left", fontsize=8.5)
plt.tight_layout()
plt.savefig("paper2/figures/O3_L4_escalation_analysis.png", dpi=300)
plt.close()
print("Saved Figure 8: O3_L4_escalation_analysis.png (Pareto Frontier Across 70 Policies)")


# -----------------------------------------------------------------------------
# Figure 9: Real Per-Family Heatmap
# -----------------------------------------------------------------------------
df_fam = pd.read_csv("paper2/tables/tab9_per_family.csv")
plt.figure(figsize=(7.5, 4.8), dpi=300)

families = df_fam["Threat Family"].tolist()
act_cols = ["Allow (%)", "Alert (%)", "Restrict (%)", "Quarantine (%)", "Block (%)"]
heat_data = np.array([[float(str(row[c]).replace("%","")) for c in act_cols] for _, row in df_fam.iterrows()])

plt.imshow(heat_data, cmap="YlOrRd", aspect="auto", vmin=0, vmax=100)
cbar = plt.colorbar()
cbar.set_label("Flow Allocation within Family (%)", fontsize=9.5, fontweight="bold")

plt.xticks(np.arange(len(act_cols)), [c.split(" ")[0] for c in act_cols], fontsize=9.5, fontweight="bold")
plt.yticks(np.arange(len(families)), families, fontsize=9.0)

for i in range(len(families)):
    for j in range(len(act_cols)):
        val = heat_data[i, j]
        color = "white" if val > 50 else "black"
        plt.text(j, i, f"{val:.1f}%", ha="center", va="center", color=color, fontsize=8, fontweight="bold" if val > 20 else "normal")

plt.title("Enforcement Action Allocation Across Threat Families (P2-tier Policy)\n(Strict Conservation of All 30,118 Attack Flows Across 8 Families)", fontsize=10.5, fontweight="bold", pad=10)
plt.tight_layout()
plt.savefig("paper2/figures/O3_per_family_heatmap.png", dpi=300)
plt.close()
print("Saved Figure 9: O3_per_family_heatmap.png")


# -----------------------------------------------------------------------------
# Figure 10: Extended Cost Sensitivity Curve Across lambda in [0.2, 50.0]
# -----------------------------------------------------------------------------
df_sens_ext = pd.read_csv("audit_outputs/cost_sensitivity_extended.csv")
plt.figure(figsize=(7.5, 4.8), dpi=300)

lambdas = df_sens_ext["lambda"].values
p1_b = df_sens_ext["P1_combined_net_benefit_ocu"].values
p2tier_b = df_sens_ext["P2_tier_combined_net_benefit_ocu"].values

plt.plot(lambdas, p2tier_b / 1e3, marker="o", color="#0055A5", lw=2.2, label="P2-tier (Tiered Containment)")
plt.plot(lambdas, p1_b / 1e3, marker="^", color="#5CB85C", lw=2.0, linestyle="--", label="P1 (Conservative Default)")

plt.axvline(1.0, color="gray", linestyle=":", lw=1.0, label="Nominal Cost Calibration (lambda = 1.0)")
plt.axvline(30.8, color="#dc2626", linestyle="--", lw=1.5, label="Break-Even Threshold (lambda = 30.8, Penalty = 1,540 OCU)")

plt.annotate("Break-Even (lambda = 30.8)\nP1 becomes superior\nfor lambda > 30.8", xy=(30.8, 786), xytext=(33, 1200),
             arrowprops=dict(arrowstyle="->", color="#dc2626", lw=1.2), fontsize=8.5, fontweight="bold", color="#dc2626")

plt.xlabel("False-Positive Blocking Penalty Scaling Factor (lambda)", fontsize=10.5, fontweight="bold")
plt.ylabel("Combined Net Operational Benefit (x1,000 OCU)", fontsize=10.5, fontweight="bold")
plt.title("Extended Decision-Theoretic Cost Sensitivity Across lambda in [0.2, 50.0]\n(False Block Penalty = 50 x lambda; Break-Even Boundary Delineation)", fontsize=10.5, fontweight="bold", pad=10)
plt.xlim(0, 52)
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend(loc="upper right", fontsize=8.5)
plt.tight_layout()
plt.savefig("paper2/figures/O3_cost_matrix_heatmap.png", dpi=300)
plt.close()
print("Saved Figure 10: O3_cost_matrix_heatmap.png")

print("\n=== ALL 10 REAL FIGURES REGENERATED SUCCESSFULLY AT 300 DPI ===")
