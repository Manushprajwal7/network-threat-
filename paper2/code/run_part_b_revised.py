import os
import json
import joblib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score

print("=== PART B REVISED: TRUST RECALIBRATION WITH THREE BUG FIXES ===")

# -------------------------------------------------------------------
# 1. Load Data
# -------------------------------------------------------------------
# 60k evaluation window
fixed = np.load("audit/scratch_60k_eval_fixed.npz")
indices_60k = fixed["indices"]
y_60k = fixed["y_sub"]
tarp_60k = fixed["tarp"]
is_attack_60k = (y_60k != 1)

# Corrected IF model
if_corr = joblib.load("backend/ml_model/saved_models/isolation_forest_corrected.pkl")
s_min, s_p95 = 0.4200, float(-if_corr.offset_)

# Score 60k with corrected IF
X_test_scaled = np.load("audit/lofo/cache/X_test_scaled.npy", mmap_mode="r")
raw_60k = if_corr.score_samples(np.array(X_test_scaled[indices_60k], dtype=np.float32))
anom_60k = np.clip((-raw_60k - s_min) / (s_p95 - s_min) * 0.90, 0, 1)

# XGBoost on 60k unscaled
xgb = joblib.load("backend/ml_model/saved_models/xgboost.pkl")
xgb.set_params(device="cpu")
X_test_unscaled = np.load("audit/lofo/cache/X_test.npy", mmap_mode="r")
probs_60k = xgb.predict_proba(np.array(X_test_unscaled[indices_60k], dtype=np.float32))
preds_60k = np.argmax(probs_60k, axis=1)
conf_60k = np.max(probs_60k, axis=1)

# 500k evaluation window (precomputed cache)
y_500k = np.load("paper2/data_cache/y_500k.npy")
anom_500k = np.load("paper2/data_cache/anom_500k.npy")
preds_500k = np.load("paper2/data_cache/preds_500k.npy")
conf_500k = np.load("paper2/data_cache/conf_500k.npy")
is_attack_500k = (y_500k != 1)
tarp_500k = np.tile(tarp_60k, int(np.ceil(500000 / len(tarp_60k))))[:500000]

with open("audit/lofo/cache/class_names.json", "r") as f:
    class_names = json.load(f)

def get_family(cls):
    if cls == 1: return "Benign"
    if cls in [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]: return "DDoS"
    if cls in [18, 19, 20, 21]: return "DoS"
    if cls in [23, 24, 25]: return "Mirai"
    if cls in [26, 27, 28, 29, 32]: return "Recon"
    if cls in [0, 2, 3, 30, 31, 33]: return "Web"
    if cls in [16, 22]: return "Spoofing"
    if cls in [17]: return "BruteForce"
    return "Other"

# Family-aware initial priors
p_benign_map = {
    "BenignTraffic": 100.0, "Recon-PingSweep": 74.8, "SqlInjection": 70.1,
    "BrowserHijacking": 57.6, "DictionaryBruteForce": 56.9, "DNS_Spoofing": 55.5,
    "CommandInjection": 53.7, "Uploading_Attack": 53.1, "MITM-ArpSpoofing": 53.0,
    "Backdoor_Malware": 52.0, "XSS": 51.6, "Recon-OSScan": 48.0,
    "Recon-PortScan": 43.5, "Recon-HostDiscovery": 41.4,
}
priors_by_idx = np.full(len(class_names), 45.0)
priors_by_idx[1] = 100.0
for c_name, val in p_benign_map.items():
    if c_name in class_names:
        priors_by_idx[class_names.index(c_name)] = val

ALPHA, BETA, GAMMA, DELTA, LAMBD = 0.30, 0.25, 0.20, 0.15, 0.10

# -------------------------------------------------------------------
# 2. ADTM Trust Simulator with Three Bug Fixes
# -------------------------------------------------------------------
# Bug 1: Hard reset applies per-flow only (NO LOCK)
# Bug 2: Hard reset target is T = 10 (populates Critical [0, 19])
def run_adtm_sim(anom_arr, preds_arr, conf_arr, tarp_arr, y_arr, is_atk_arr,
                 use_priors=False, use_hard_reset=False, use_ewma=False, n_ent=600):
    total = n_ent * 100
    trust = np.zeros(total)
    
    for e in range(n_ent):
        start = e * 100
        end = start + 100
        init_c = y_arr[start]
        T_0 = priors_by_idx[init_c] if use_priors else 100.0
        
        S_U = T_0 if use_priors else 100.0
        S_D = (T_0 * 0.95) if use_priors else 95.0
        S_B = T_0 if use_priors else 100.0
        T_prev = T_0
        
        for t in range(start, end):
            # Stateful behavioral update
            if is_atk_arr[t]:
                S_B = max(0.0, S_B - 2.0)
            else:
                S_B = min(100.0, S_B + 1.0)
                
            S_A = 100.0 * (1.0 - anom_arr[t])
            S_T = 100.0 * (1.0 - tarp_arr[t])
            T_obs = np.clip(ALPHA * S_U + BETA * S_D + GAMMA * S_B + DELTA * S_A + LAMBD * S_T, 0.0, 100.0)
            
            # Bug 1 & 2: Per-flow hard reset to T=10, NO LOCK
            is_reset = False
            if use_hard_reset and (conf_arr[t] >= 0.95) and (preds_arr[t] != 1) and (anom_arr[t] >= 0.90):
                is_reset = True
                
            if is_reset:
                T_curr = 10.0  # Bug 2: sets trust to 10 for this flow only
            elif use_ewma:
                # Next benign flow recovers naturally
                if preds_arr[t] == 1:
                    T_curr = T_obs
                else:
                    c_name = class_names[preds_arr[t]]
                    if any(k in c_name for k in ["DDoS", "DoS", "Mirai"]):
                        a_fam = 0.50
                    elif any(k in c_name for k in ["Recon", "Scan", "Sweep"]):
                        a_fam = 0.15
                    else:
                        a_fam = 0.30
                    T_curr = np.clip(a_fam * T_obs + (1.0 - a_fam) * T_prev, 0.0, 100.0)
            else:
                T_curr = T_obs
                
            trust[t] = T_curr
            T_prev = T_curr
            
    return trust

print("Simulating C0' through C4'...")
t_c0 = run_adtm_sim(anom_60k, preds_60k, conf_60k, tarp_60k, y_60k, is_attack_60k, False, False, False, 600)
t_c1 = run_adtm_sim(anom_60k, preds_60k, conf_60k, tarp_60k, y_60k, is_attack_60k, True, False, False, 600)
t_c2 = run_adtm_sim(anom_60k, preds_60k, conf_60k, tarp_60k, y_60k, is_attack_60k, True, True, False, 600)
t_c3 = run_adtm_sim(anom_60k, preds_60k, conf_60k, tarp_60k, y_60k, is_attack_60k, True, True, True, 600)
t_c4 = run_adtm_sim(anom_500k, preds_500k, conf_500k, tarp_500k, y_500k, is_attack_500k, True, True, True, 5000)

# Save corrected caches
np.save("paper2/data_cache/trust_60k_corrected.npy", t_c0)
np.save("paper2/data_cache/trust_500k_c4.npy", t_c4)

# -------------------------------------------------------------------
# 3. Bug 3 Fix: Reordered Level Assignment (L4 evaluated before L5)
# -------------------------------------------------------------------
def evaluate_levels(trust_arr, anom_arr, conf_arr, preds_arr, tarp_arr, n_ent):
    total = n_ent * 100
    t_e = trust_arr.reshape(n_ent, 100)
    a_e = anom_arr.reshape(n_ent, 100)
    c_e = conf_arr.reshape(n_ent, 100)
    p_e = preds_arr.reshape(n_ent, 100)
    tp_e = tarp_arr.reshape(n_ent, 100)[:, 0]
    
    c_topo = (tp_e >= 0.42).astype(int)
    c_trust = (t_e.min(axis=1) <= 60.0).astype(int)
    c_anom = ((a_e >= 0.90).mean(axis=1) >= 0.28).astype(int)
    c_conf = (((c_e >= 0.95) & (p_e != 1)).mean(axis=1) >= 0.26).astype(int)
    S = c_topo + c_trust + c_anom + c_conf
    
    levels = np.zeros(n_ent, dtype=int)
    for e in range(n_ent):
        fam_chunk = [get_family(p) for p in p_e[e] if p != 1]
        distinct_fams = len(set(fam_chunk))
        
        # Bug 3 fix: L4 checked first (specific topology risk hub), then L5
        if S[e] >= 3 and (t_e[e].min() <= 20.0) and (tp_e[e] >= 0.75):
            levels[e] = 4
        elif S[e] >= 3 and (t_e[e].min() <= 20.0) and (distinct_fams >= 2):
            levels[e] = 5
        elif S[e] >= 3:
            levels[e] = 3
        elif S[e] == 2:
            levels[e] = 2
        elif S[e] == 1:
            levels[e] = 1
        else:
            levels[e] = 0
            
    return levels

# -------------------------------------------------------------------
# 4. Generate Tables and Metrics
# -------------------------------------------------------------------
BANDS = [
    ("High 80-100", 80.0, 100.01),
    ("Moderate 60-79", 60.0, 80.0),
    ("Low 40-59", 40.0, 60.0),
    ("Very Low 20-39", 20.0, 40.0),
    ("Critical 0-19", 0.0, 20.0),
]

def make_band_csv(trust_arr, is_atk_arr, filepath):
    rows = []
    tot = len(trust_arr)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("Band,Samples,Share %,Attack %,Mean trust\n")
        for name, lo, hi in BANDS:
            mask = (trust_arr >= lo) & (trust_arr < hi)
            n = int(np.sum(mask))
            sh = n / tot * 100
            atk_p = float(np.mean(is_atk_arr[mask]) * 100) if n > 0 else 0.0
            mt = float(np.mean(trust_arr[mask])) if n > 0 else 0.0
            f.write(f"{name},{n},{sh:.2f},{atk_p:.2f},{mt:.2f}\n")

make_band_csv(t_c0, is_attack_60k, "paper2/tables/O2_B1_trust_baseline_corrected.csv")
make_band_csv(t_c1, is_attack_60k, "paper2/tables/O2_B2_with_priors.csv")
make_band_csv(t_c2, is_attack_60k, "paper2/tables/O2_B3_with_hard_reset.csv")
make_band_csv(t_c3, is_attack_60k, "paper2/tables/O2_B4_with_ewma.csv")
make_band_csv(t_c4, is_attack_500k, "paper2/tables/O2_B5_extended_500k.csv")

# Combined Table O2_B6
configs_meta = [
    ("C0'", t_c0, is_attack_60k, anom_60k, conf_60k, preds_60k, tarp_60k, 600),
    ("C1'", t_c1, is_attack_60k, anom_60k, conf_60k, preds_60k, tarp_60k, 600),
    ("C2'", t_c2, is_attack_60k, anom_60k, conf_60k, preds_60k, tarp_60k, 600),
    ("C3'", t_c3, is_attack_60k, anom_60k, conf_60k, preds_60k, tarp_60k, 600),
    ("C4'", t_c4, is_attack_500k, anom_500k, conf_500k, preds_500k, tarp_500k, 5000),
]

b6_records = []
for name, t_arr, atk_arr, a_arr, c_arr, p_arr, tp_arr, n_ent in configs_meta:
    tot = len(t_arr)
    high_p = np.mean((t_arr >= 80.0) & (t_arr <= 100.01)) * 100
    mod_p = np.mean((t_arr >= 60.0) & (t_arr < 80.0)) * 100
    low_p = np.mean((t_arr >= 40.0) & (t_arr < 60.0)) * 100
    vlow_p = np.mean((t_arr >= 20.0) & (t_arr < 40.0)) * 100
    crit_p = np.mean((t_arr >= 0.0) & (t_arr < 20.0)) * 100
    auc = roc_auc_score(atk_arr, -t_arr)
    
    # Sample-level trust gap
    t_atk_sample = float(np.mean(t_arr[atk_arr]))
    t_ben_sample = float(np.mean(t_arr[~atk_arr]))
    sample_gap = t_ben_sample - t_atk_sample
    
    # Entity-level trust gap: entity mean trust of benign flows vs attack flows
    t_e = t_arr.reshape(n_ent, 100)
    atk_e = atk_arr.reshape(n_ent, 100)
    # Average entity trust for benign flows vs attack flows
    ent_ben_means = [t_e[e][~atk_e[e]].mean() for e in range(n_ent) if np.sum(~atk_e[e]) > 0]
    ent_atk_means = [t_e[e][atk_e[e]].mean() for e in range(n_ent) if np.sum(atk_e[e]) > 0]
    t_ben_entity = float(np.mean(ent_ben_means)) if ent_ben_means else t_ben_sample
    t_atk_entity = float(np.mean(ent_atk_means)) if ent_atk_means else t_atk_sample
    entity_gap = t_ben_entity - t_atk_entity
    
    # Level evaluation with Bug 3 fix
    levels = evaluate_levels(t_arr, a_arr, c_arr, p_arr, tp_arr, n_ent)
    l4_pct = float(np.mean(levels == 4) * 100)
    l5_pct = float(np.mean(levels == 5) * 100)
    
    b6_records.append({
        "config": name,
        "High%": round(high_p, 2),
        "Moderate%": round(mod_p, 2),
        "Low%": round(low_p, 2),
        "VeryLow%": round(vlow_p, 2),
        "Critical%": round(crit_p, 2),
        "AUC(trust,attack)": round(auc, 4),
        "L4_entities%": round(l4_pct, 2),
        "L5_entities%": round(l5_pct, 2),
        "mean_trust_attack": round(t_atk_sample, 2),
        "mean_trust_benign": round(t_ben_sample, 2),
        "sample_trust_gap": round(sample_gap, 2),
        "entity_trust_gap": round(entity_gap, 2),
    })

# Write revised O2_B6_combined_configs.csv
csv_path = "paper2/tables/O2_B6_combined_configs.csv"
with open(csv_path, "w", encoding="utf-8") as f:
    f.write("config,High%,Moderate%,Low%,VeryLow%,Critical%,AUC(trust,attack),L4_entities%,L5_entities%,mean_trust_attack,mean_trust_benign,sample_trust_gap,entity_trust_gap\n")
    for r in b6_records:
        f.write(f"{r['config']},{r['High%']:.2f},{r['Moderate%']:.2f},{r['Low%']:.2f},{r['VeryLow%']:.2f},{r['Critical%']:.2f},{r['AUC(trust,attack)']:.4f},{r['L4_entities%']:.2f},{r['L5_entities%']:.2f},{r['mean_trust_attack']:.2f},{r['mean_trust_benign']:.2f},{r['sample_trust_gap']:.2f},{r['entity_trust_gap']:.2f}\n")
print(f"Saved revised {csv_path}")

# Print summary table
print("\n" + "="*95)
print(f"{'Config':6s} | {'High%':6s} | {'Mod%':6s} | {'Low%':6s} | {'VLow%':6s} | {'Crit%':6s} | {'AUC':6s} | {'L4%':6s} | {'L5%':6s} | {'SampGap':8s} | {'EntGap':8s}")
print("="*95)
for r in b6_records:
    print(f"{r['config']:6s} | {r['High%']:6.2f} | {r['Moderate%']:6.2f} | {r['Low%']:6.2f} | {r['VeryLow%']:6.2f} | {r['Critical%']:6.2f} | {r['AUC(trust,attack)']:6.4f} | {r['L4_entities%']:6.2f} | {r['L5_entities%']:6.2f} | {r['sample_trust_gap']:8.2f} | {r['entity_trust_gap']:8.2f}")
print("="*95)

# C4' per-level entity distribution
levels_c4 = evaluate_levels(t_c4, anom_500k, conf_500k, preds_500k, tarp_500k, 5000)
unique_c4, counts_c4 = np.unique(levels_c4, return_counts=True)
print("\n=== C4' Per-Level Entity Distribution (5,000 entities) ===")
for u, c in zip(unique_c4, counts_c4):
    print(f"L{u}: {c:5d} entities ({c/5000*100:6.2f}%)")

# -------------------------------------------------------------------
# 5. Figures
# -------------------------------------------------------------------
# Stacked Bar Chart
fig_bar_path = "paper2/figures/O2_B_band_distribution_comparison.png"
cfg_labels = [r["config"] for r in b6_records]
highs = [r["High%"] for r in b6_records]
mods = [r["Moderate%"] for r in b6_records]
lows = [r["Low%"] for r in b6_records]
vlows = [r["VeryLow%"] for r in b6_records]
crits = [r["Critical%"] for r in b6_records]

x = np.arange(len(cfg_labels))
width = 0.55

plt.figure(figsize=(9, 5))
plt.bar(x, highs, width, label="High (80-100)", color="#16a34a")
plt.bar(x, mods, width, bottom=highs, label="Moderate (60-79)", color="#0284c7")
plt.bar(x, lows, width, bottom=np.array(highs)+np.array(mods), label="Low (40-59)", color="#f59e0b")
plt.bar(x, vlows, width, bottom=np.array(highs)+np.array(mods)+np.array(lows), label="Very Low (20-39)", color="#ea580c")
plt.bar(x, crits, width, bottom=np.array(highs)+np.array(mods)+np.array(lows)+np.array(vlows), label="Critical (0-19)", color="#dc2626")

plt.xticks(x, cfg_labels, fontsize=11, fontweight="bold")
plt.ylabel("Population Share (%)", fontsize=11)
plt.title("ADTM Trust Band Distribution Across Recalibrated Configurations (C0'–C4')", fontsize=12, fontweight="bold")
plt.legend(loc="upper right", framealpha=0.9, fontsize=9)
plt.ylim(0, 100)
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(fig_bar_path, dpi=300)
plt.close()
print(f"Saved {fig_bar_path}")

# Heatmap
fig_heat_path = "paper2/figures/O2_B6_config_heatmap.png"
metrics_mat = np.array([
    [r["AUC(trust,attack)"], r["L4_entities%"], r["L5_entities%"], r["sample_trust_gap"]]
    for r in b6_records
])
m_names = ["AUC(trust, atk)", "L4 Entities (%)", "L5 Entities (%)", "Sample Gap (pts)"]

fig, ax = plt.subplots(figsize=(8, 5))
cax = ax.matshow(metrics_mat, cmap="YlGnBu", aspect="auto")
for i in range(len(b6_records)):
    for j in range(len(m_names)):
        v = metrics_mat[i, j]
        fmt = f"{v:.4f}" if j == 0 else f"{v:.2f}"
        ax.text(j, i, fmt, ha="center", va="center", color="black" if v < metrics_mat.max()*0.7 else "white", fontweight="bold")

ax.set_xticks(range(len(m_names)))
ax.set_xticklabels(m_names, fontsize=10, fontweight="bold")
ax.set_yticks(range(len(cfg_labels)))
ax.set_yticklabels(cfg_labels, fontsize=10, fontweight="bold")
plt.title("Recalibration Performance Heatmap (Revised Config × Metric)", fontsize=12, fontweight="bold", pad=20)
fig.colorbar(cax)
plt.tight_layout()
plt.savefig(fig_heat_path, dpi=300)
plt.close()
print(f"Saved {fig_heat_path}")
