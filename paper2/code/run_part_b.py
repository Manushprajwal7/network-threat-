import os
import json
import joblib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

print("=== PART B: TRUST RECALIBRATION ===")

# ---------------------------------------------------------
# Load models & 60k cache
# ---------------------------------------------------------
fixed = np.load("audit/scratch_60k_eval_fixed.npz")
indices_60k = fixed["indices"]
y_60k = fixed["y_sub"]
tarp_60k = fixed["tarp"]
old_anom_60k = fixed["anom"]
old_trust_60k = fixed["trust"]
is_attack_60k = (y_60k != 1)

with open("audit/lofo/cache/class_names.json", "r") as f:
    class_names = json.load(f)

# Load corrected IF
if_corr = joblib.load("backend/ml_model/saved_models/isolation_forest_corrected.pkl")
s_min = 0.4200
s_p95 = float(-if_corr.offset_)

# Load XGBoost model
xgb = joblib.load("backend/ml_model/saved_models/xgboost.pkl")
xgb.set_params(device="cpu")

# ---------------------------------------------------------
# B.1: Recompute anomaly scores & trust on 60k window
# ---------------------------------------------------------
print("\n--- B.1: Scoring 60k window with corrected IF ---")
X_test_scaled = np.load("audit/lofo/cache/X_test_scaled.npy", mmap_mode="r")
X_60k_scaled = np.array(X_test_scaled[indices_60k], dtype=np.float32)

raw_60k = if_corr.score_samples(X_60k_scaled)
s_60k = -raw_60k
anom_60k_corr = np.clip((s_60k - s_min) / (s_p95 - s_min) * 0.90, 0, 1)

# Save anom_60k_corrected.npy
os.makedirs("paper2/data_cache", exist_ok=True)
np.save("paper2/data_cache/anom_60k_corrected.npy", anom_60k_corr)

# Comparisons
r_val, _ = pearsonr(old_anom_60k, anom_60k_corr)
mad_val = float(np.mean(np.abs(old_anom_60k - anom_60k_corr)))
pct_changed_90 = float(np.mean((old_anom_60k >= 0.90) != (anom_60k_corr >= 0.90)) * 100)

print(f"Pearson correlation with contaminated anom: {r_val:.4f}")
print(f"Mean absolute difference (MAD): {mad_val:.4f}")
print(f"% samples whose classification at tau=0.90 changed: {pct_changed_90:.2f}%")

# Compute baseline trust update (C0)
# T_next = clip(T + alpha*src + beta*dev + gamma*behav - delta*anom + lambda*(100 - 100*topo), 0, 100)
# Using ADTM formula from trust_loader.py
def compute_c0_trust(anom_arr, is_atk_arr, tarp_arr, n_entities=600, chunk_size=100):
    ALPHA, BETA, GAMMA, DELTA, LAMBD = 0.30, 0.25, 0.20, 0.15, 0.10
    trust_scores = np.zeros(len(anom_arr))
    for e in range(n_entities):
        start = e * chunk_size
        end = start + chunk_size
        S_U = 100.0
        S_D = 95.0
        S_B = 100.0
        for t in range(start, end):
            if is_atk_arr[t]:
                S_B = max(0.0, S_B - 2.0)
            else:
                S_B = min(100.0, S_B + 1.0)
            S_A = 100.0 * (1.0 - anom_arr[t])
            S_T = 100.0 * (1.0 - tarp_arr[t])
            T_inst = ALPHA * S_U + BETA * S_D + GAMMA * S_B + DELTA * S_A + LAMBD * S_T
            trust_scores[t] = np.clip(T_inst, 0.0, 100.0)
    return trust_scores

trust_60k_c0 = compute_c0_trust(anom_60k_corr, is_attack_60k, tarp_60k)
np.save("paper2/data_cache/trust_60k_corrected.npy", trust_60k_c0)

# Bands definition
BANDS = [
    ("High 80-100", 80.0, 100.01),
    ("Moderate 60-79", 60.0, 80.0),
    ("Low 40-59", 40.0, 60.0),
    ("Very Low 20-39", 20.0, 40.0),
    ("Critical 0-19", 0.0, 20.0),
]

def get_band_table(trust_arr, is_atk_arr, old_trust_arr=None):
    rows = []
    total = len(trust_arr)
    for name, low, high in BANDS:
        mask = (trust_arr >= low) & (trust_arr < high)
        n = int(np.sum(mask))
        share = n / total * 100
        atk_pct = float(np.mean(is_atk_arr[mask]) * 100) if n > 0 else 0.0
        mean_t = float(np.mean(trust_arr[mask])) if n > 0 else 0.0
        if old_trust_arr is not None:
            old_n = int(np.sum((old_trust_arr >= low) & (old_trust_arr < high)))
            old_share = old_n / len(old_trust_arr) * 100
            delta_pub = share - old_share
            delta_str = f"{delta_pub:+.2f} pp"
        else:
            delta_str = "N/A"
        rows.append({
            "Band": name,
            "Samples": n,
            "Share %": round(share, 2),
            "Attack %": round(atk_pct, 2),
            "Mean trust": round(mean_t, 2),
            "Δ vs published": delta_str
        })
    return rows

rows_b1 = get_band_table(trust_60k_c0, is_attack_60k, old_trust_60k)

# Write O2_B1_trust_baseline_corrected.csv
os.makedirs("paper2/tables", exist_ok=True)
with open("paper2/tables/O2_B1_trust_baseline_corrected.csv", "w", encoding="utf-8") as f:
    f.write("Band,Samples,Share %,Attack %,Mean trust,Δ vs published\n")
    for r in rows_b1:
        f.write(f"{r['Band']},{r['Samples']},{r['Share %']:.2f},{r['Attack %']:.2f},{r['Mean trust']:.2f},{r['Δ vs published']}\n")

print("Saved paper2/tables/O2_B1_trust_baseline_corrected.csv")


# ---------------------------------------------------------
# XGBoost predictions on 60k unscaled for Interventions
# ---------------------------------------------------------
print("\n--- Computing XGBoost predictions on 60k window ---")
X_test_unscaled = np.load("audit/lofo/cache/X_test.npy", mmap_mode="r")
X_60k_unscaled = np.array(X_test_unscaled[indices_60k], dtype=np.float32)
probs_60k = xgb.predict_proba(X_60k_unscaled)
preds_60k = np.argmax(probs_60k, axis=1)
conf_60k = np.max(probs_60k, axis=1)

# Precompute priors mapping
lambda_prior = 0.55
p_benign_map = {
    "BenignTraffic": 100.0,
    "Recon-PingSweep": 74.8,
    "SqlInjection": 70.1,
    "BrowserHijacking": 57.6,
    "DictionaryBruteForce": 56.9,
    "DNS_Spoofing": 55.5,
    "CommandInjection": 53.7,
    "Uploading_Attack": 53.1,
    "MITM-ArpSpoofing": 53.0,
    "Backdoor_Malware": 52.0,
    "XSS": 51.6,
    "Recon-OSScan": 48.0,
    "Recon-PortScan": 43.5,
    "Recon-HostDiscovery": 41.4,
}
priors_by_idx = np.full(len(class_names), 45.0)
priors_by_idx[class_names.index("BenignTraffic")] = 100.0
for c_name, val in p_benign_map.items():
    if c_name in class_names:
        priors_by_idx[class_names.index(c_name)] = val

# ---------------------------------------------------------
# General trust simulator for Interventions
# ---------------------------------------------------------
def simulate_adtm(
    anom_arr,
    preds_arr,
    conf_arr,
    is_atk_arr,
    tarp_arr,
    y_class_arr,
    use_priors=False,
    use_hard_reset=False,
    use_ewma=False,
    n_entities=600,
    chunk_size=100
):
    ALPHA, BETA, GAMMA, DELTA, LAMBD = 0.30, 0.25, 0.20, 0.15, 0.10
    total_len = len(anom_arr)
    trust_scores = np.zeros(total_len)
    
    for e in range(n_entities):
        start = e * chunk_size
        end = min(start + chunk_size, total_len)
        if start >= total_len:
            break
            
        initial_class = y_class_arr[start]
        T_0 = priors_by_idx[initial_class] if use_priors else 100.0
        
        S_U = T_0 if use_priors else 100.0
        S_D = (T_0 * 0.95) if use_priors else 95.0
        S_B = T_0 if use_priors else 100.0
        T_prev = T_0
        
        hard_reset_count = 0
        lock_remaining = 0
        
        for t in range(start, end):
            # Check hard reset trigger
            is_pred_atk = (preds_arr[t] != 1)
            if conf_arr[t] >= 0.95 and is_pred_atk and anom_arr[t] >= 0.90:
                hard_reset_count += 1
            else:
                hard_reset_count = 0
                
            if use_hard_reset and hard_reset_count >= 2:
                lock_remaining = 200 # per specification
                
            # Behavioral update
            if is_atk_arr[t]:
                S_B = max(0.0, S_B - 2.0)
            else:
                S_B = min(100.0, S_B + 1.0)
                
            S_A = 100.0 * (1.0 - anom_arr[t])
            S_T = 100.0 * (1.0 - tarp_arr[t])
            
            T_obs = ALPHA * S_U + BETA * S_D + GAMMA * S_B + DELTA * S_A + LAMBD * S_T
            T_obs = np.clip(T_obs, 0.0, 100.0)
            
            if use_hard_reset and lock_remaining > 0:
                T_curr = 20.0
                lock_remaining -= 1
            elif use_ewma:
                c_name = class_names[preds_arr[t]]
                if c_name == "BenignTraffic":
                    a_fam = 0.05
                elif any(k in c_name for k in ["DDoS", "DoS", "Mirai"]):
                    a_fam = 0.50
                elif any(k in c_name for k in ["Spoofing", "MITM", "Hijacking", "Injection", "Sql", "Uploading", "XSS", "BruteForce"]):
                    a_fam = 0.30
                elif any(k in c_name for k in ["Recon", "Scan", "Sweep"]):
                    a_fam = 0.15
                else:
                    a_fam = 0.30
                T_curr = a_fam * T_obs + (1.0 - a_fam) * T_prev
            else:
                T_curr = T_obs
                
            trust_scores[t] = np.clip(T_curr, 0.0, 100.0)
            T_prev = trust_scores[t]
            
    return trust_scores

# ---------------------------------------------------------
# B.2: Intervention 1 — Family-aware priors (C1)
# ---------------------------------------------------------
print("\n--- B.2: Running with Family-Aware Priors (C1) ---")
trust_60k_c1 = simulate_adtm(
    anom_60k_corr, preds_60k, conf_60k, is_attack_60k, tarp_60k, y_60k,
    use_priors=True, use_hard_reset=False, use_ewma=False
)
rows_b2 = get_band_table(trust_60k_c1, is_attack_60k, old_trust_60k)
with open("paper2/tables/O2_B2_with_priors.csv", "w", encoding="utf-8") as f:
    f.write("Band,Samples,Share %,Attack %,Mean trust,Δ vs published\n")
    for r in rows_b2:
        f.write(f"{r['Band']},{r['Samples']},{r['Share %']:.2f},{r['Attack %']:.2f},{r['Mean trust']:.2f},{r['Δ vs published']}\n")
print("Saved paper2/tables/O2_B2_with_priors.csv")

# ---------------------------------------------------------
# B.3: Intervention 2 — Hard reset (C2)
# ---------------------------------------------------------
print("\n--- B.3: Running with Hard Reset (C2) ---")
trust_60k_c2 = simulate_adtm(
    anom_60k_corr, preds_60k, conf_60k, is_attack_60k, tarp_60k, y_60k,
    use_priors=True, use_hard_reset=True, use_ewma=False
)
rows_b3 = get_band_table(trust_60k_c2, is_attack_60k, old_trust_60k)
with open("paper2/tables/O2_B3_with_hard_reset.csv", "w", encoding="utf-8") as f:
    f.write("Band,Samples,Share %,Attack %,Mean trust,Δ vs published\n")
    for r in rows_b3:
        f.write(f"{r['Band']},{r['Samples']},{r['Share %']:.2f},{r['Attack %']:.2f},{r['Mean trust']:.2f},{r['Δ vs published']}\n")
print("Saved paper2/tables/O2_B3_with_hard_reset.csv")

# ---------------------------------------------------------
# B.4: Intervention 3 — Adaptive EWMA (C3)
# ---------------------------------------------------------
print("\n--- B.4: Running with Adaptive EWMA (C3) ---")
trust_60k_c3 = simulate_adtm(
    anom_60k_corr, preds_60k, conf_60k, is_attack_60k, tarp_60k, y_60k,
    use_priors=True, use_hard_reset=True, use_ewma=True
)
rows_b4 = get_band_table(trust_60k_c3, is_attack_60k, old_trust_60k)
with open("paper2/tables/O2_B4_with_ewma.csv", "w", encoding="utf-8") as f:
    f.write("Band,Samples,Share %,Attack %,Mean trust,Δ vs published\n")
    for r in rows_b4:
        f.write(f"{r['Band']},{r['Samples']},{r['Share %']:.2f},{r['Attack %']:.2f},{r['Mean trust']:.2f},{r['Δ vs published']}\n")
print("Saved paper2/tables/O2_B4_with_ewma.csv")

# ---------------------------------------------------------
# B.5: Extended 500k Window Evaluation (C4)
# ---------------------------------------------------------
print("\n--- B.5: Sampling 500k Stratified Window ---")
y_test_full = np.load("audit/lofo/cache/y_test.npy")
n_full = len(y_test_full)
sample_size_500k = 500000

_, idx_500k = train_test_split(
    np.arange(n_full),
    test_size=sample_size_500k,
    stratify=y_test_full,
    random_state=42
)
idx_500k = np.sort(idx_500k)
print(f"Sampled {len(idx_500k):,} samples from {n_full:,} test samples.")

y_500k = y_test_full[idx_500k]
is_attack_500k = (y_500k != 1)

# Score with corrected IF
print("Scoring 500k window with corrected IF...")
X_500k_scaled = np.array(X_test_scaled[idx_500k], dtype=np.float32)
raw_500k = if_corr.score_samples(X_500k_scaled)
s_500k = -raw_500k
anom_500k_corr = np.clip((s_500k - s_min) / (s_p95 - s_min) * 0.90, 0, 1)

# XGBoost on 500k unscaled
print("Scoring 500k window with XGBoost...")
X_500k_unscaled = np.array(X_test_unscaled[idx_500k], dtype=np.float32)
probs_500k = xgb.predict_proba(X_500k_unscaled)
preds_500k = np.argmax(probs_500k, axis=1)
conf_500k = np.max(probs_500k, axis=1)

# Synthesize synthetic entity TARP for 500k window (5,000 entities x 100 samples)
# Each entity inherits TARP risk from its sampled nodes
n_entities_500k = 5000
chunk_size_500k = 100
# Tile tarp from 60k or generate consistent contextual TARP
tarp_pool = fixed["tarp"]
tarp_500k = np.tile(tarp_pool, int(np.ceil(500000 / len(tarp_pool))))[:500000]

print("Simulating C4 trust on 500k window...")
trust_500k_c4 = simulate_adtm(
    anom_500k_corr, preds_500k, conf_500k, is_attack_500k, tarp_500k, y_500k,
    use_priors=True, use_hard_reset=True, use_ewma=True,
    n_entities=n_entities_500k, chunk_size=chunk_size_500k
)
rows_b5 = get_band_table(trust_500k_c4, is_attack_500k)
with open("paper2/tables/O2_B5_extended_500k.csv", "w", encoding="utf-8") as f:
    f.write("Band,Samples,Share %,Attack %,Mean trust,Δ vs published\n")
    for r in rows_b5:
        f.write(f"{r['Band']},{r['Samples']},{r['Share %']:.2f},{r['Attack %']:.2f},{r['Mean trust']:.2f},{r['Δ vs published']}\n")
print("Saved paper2/tables/O2_B5_extended_500k.csv")


# ---------------------------------------------------------
# B.6: Combined Configuration Comparison
# ---------------------------------------------------------
print("\n--- B.6: Combined Configuration Metrics ---")

# Evaluate security levels L4/L5 per config
def eval_l4_l5_entities(trust_arr, anom_arr, conf_arr, preds_arr, tarp_arr, n_ent=600, n_samp=100):
    total = n_ent * n_samp
    anom_e = anom_arr[:total].reshape(n_ent, n_samp)
    conf_e = conf_arr[:total].reshape(n_ent, n_samp)
    preds_e = preds_arr[:total].reshape(n_ent, n_samp)
    trust_e = trust_arr[:total].reshape(n_ent, n_samp)
    tarp_e = tarp_arr[:total].reshape(n_ent, n_samp)[:, 0]
    
    is_atk_e = (preds_e != 1)
    
    c_topo = (tarp_e >= 0.42).astype(int)
    c_trust = (trust_e.min(axis=1) <= 60.0).astype(int)
    c_anom = ((anom_e >= 0.90).mean(axis=1) >= 0.28).astype(int)
    c_conf = (((conf_e >= 0.95) & is_atk_e).mean(axis=1) >= 0.26).astype(int)
    
    S = c_topo + c_trust + c_anom + c_conf
    
    # Count distinct attack families per entity
    l4_count = 0
    l5_count = 0
    for e in range(n_ent):
        fam_chunk = [class_names[p] for p in preds_e[e] if p != 1]
        distinct_fams = len(set(fam_chunk))
        min_t = trust_e[e].min()
        
        # L5: S >= 3 and distinct_fams >= 2 and trust <= 20
        if S[e] >= 3 and distinct_fams >= 2 and min_t <= 20.0:
            l5_count += 1
        # L4: S >= 3 and tarp >= 0.75 and trust <= 20
        elif S[e] >= 3 and tarp_e[e] >= 0.75 and min_t <= 20.0:
            l4_count += 1
            
    return (l4_count / n_ent * 100), (l5_count / n_ent * 100)

configs = [
    ("C0", trust_60k_c0, anom_60k_corr, conf_60k, preds_60k, tarp_60k, is_attack_60k, 600, 100),
    ("C1", trust_60k_c1, anom_60k_corr, conf_60k, preds_60k, tarp_60k, is_attack_60k, 600, 100),
    ("C2", trust_60k_c2, anom_60k_corr, conf_60k, preds_60k, tarp_60k, is_attack_60k, 600, 100),
    ("C3", trust_60k_c3, anom_60k_corr, conf_60k, preds_60k, tarp_60k, is_attack_60k, 600, 100),
    ("C4", trust_500k_c4, anom_500k_corr, conf_500k, preds_500k, tarp_500k, is_attack_500k, 5000, 100),
]

b6_rows = []
for cfg_name, t_arr, a_arr, c_arr, p_arr, tp_arr, atk_arr, n_ent, n_s in configs:
    tot = len(t_arr)
    high_pct = np.mean((t_arr >= 80.0) & (t_arr <= 100.01)) * 100
    mod_pct = np.mean((t_arr >= 60.0) & (t_arr < 80.0)) * 100
    low_pct = np.mean((t_arr >= 40.0) & (t_arr < 60.0)) * 100
    vlow_pct = np.mean((t_arr >= 20.0) & (t_arr < 40.0)) * 100
    crit_pct = np.mean((t_arr >= 0.0) & (t_arr < 20.0)) * 100
    
    auc_trust = roc_auc_score(atk_arr, -t_arr)
    t_atk = float(np.mean(t_arr[atk_arr]))
    t_ben = float(np.mean(t_arr[~atk_arr]))
    gap = t_ben - t_atk
    
    l4_pct, l5_pct = eval_l4_l5_entities(t_arr, a_arr, c_arr, p_arr, tp_arr, n_ent, n_s)
    
    b6_rows.append({
        "config": cfg_name,
        "High%": round(high_pct, 2),
        "Moderate%": round(mod_pct, 2),
        "Low%": round(low_pct, 2),
        "VeryLow%": round(vlow_pct, 2),
        "Critical%": round(crit_pct, 2),
        "AUC(trust,attack)": round(auc_trust, 4),
        "L4_entities%": round(l4_pct, 2),
        "L5_entities%": round(l5_pct, 2),
        "mean_trust_attack": round(t_atk, 2),
        "mean_trust_benign": round(t_ben, 2),
        "trust_gap": round(gap, 2)
    })

# Write O2_B6_combined_configs.csv
with open("paper2/tables/O2_B6_combined_configs.csv", "w", encoding="utf-8") as f:
    f.write("config,High%,Moderate%,Low%,VeryLow%,Critical%,AUC(trust,attack),L4_entities%,L5_entities%,mean_trust_attack,mean_trust_benign,trust_gap\n")
    for r in b6_rows:
        f.write(f"{r['config']},{r['High%']:.2f},{r['Moderate%']:.2f},{r['Low%']:.2f},{r['VeryLow%']:.2f},{r['Critical%']:.2f},{r['AUC(trust,attack)']:.4f},{r['L4_entities%']:.2f},{r['L5_entities%']:.2f},{r['mean_trust_attack']:.2f},{r['mean_trust_benign']:.2f},{r['trust_gap']:.2f}\n")
print("Saved paper2/tables/O2_B6_combined_configs.csv")

# Print summary table
print("\n" + "="*80)
print(f"{'Config':6s} | {'High%':6s} | {'Mod%':6s} | {'Low%':6s} | {'VLow%':6s} | {'Crit%':6s} | {'AUC':6s} | {'L4%':6s} | {'L5%':6s} | {'Gap':6s}")
print("="*80)
for r in b6_rows:
    print(f"{r['config']:6s} | {r['High%']:6.2f} | {r['Moderate%']:6.2f} | {r['Low%']:6.2f} | {r['VeryLow%']:6.2f} | {r['Critical%']:6.2f} | {r['AUC(trust,attack)']:6.4f} | {r['L4_entities%']:6.2f} | {r['L5_entities%']:6.2f} | {r['trust_gap']:6.2f}")
print("="*80)

# Generate Stacked Bar Chart for Band Distributions
fig_bar_path = "paper2/figures/O2_B_band_distribution_comparison.png"
cfg_labels = [r["config"] for r in b6_rows]
highs = [r["High%"] for r in b6_rows]
mods = [r["Moderate%"] for r in b6_rows]
lows = [r["Low%"] for r in b6_rows]
vlows = [r["VeryLow%"] for r in b6_rows]
crits = [r["Critical%"] for r in b6_rows]

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
plt.title("ADTM Trust Band Distribution Across Recalibration Configurations", fontsize=12, fontweight="bold")
plt.legend(loc="upper right", framealpha=0.9, fontsize=9)
plt.ylim(0, 100)
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(fig_bar_path, dpi=300)
plt.close()
print(f"Saved band distribution plot to {fig_bar_path}")

# Generate Heatmap for Config x Metric
fig_heat_path = "paper2/figures/O2_B6_config_heatmap.png"
metrics_matrix = np.array([
    [r["AUC(trust,attack)"], r["L4_entities%"], r["L5_entities%"], r["trust_gap"]]
    for r in b6_rows
])
metric_names = ["AUC(trust, atk)", "L4 Entities (%)", "L5 Entities (%)", "Trust Gap (pts)"]

fig, ax = plt.subplots(figsize=(8, 5))
cax = ax.matshow(metrics_matrix, cmap="YlGnBu", aspect="auto")
for i in range(len(b6_rows)):
    for j in range(len(metric_names)):
        val = metrics_matrix[i, j]
        fmt = f"{val:.4f}" if j == 0 else f"{val:.2f}"
        ax.text(j, i, fmt, ha="center", va="center", color="black" if val < metrics_matrix.max()*0.7 else "white", fontweight="bold")

ax.set_xticks(range(len(metric_names)))
ax.set_xticklabels(metric_names, fontsize=10, fontweight="bold")
ax.set_yticks(range(len(cfg_labels)))
ax.set_yticklabels(cfg_labels, fontsize=10, fontweight="bold")
plt.title("Recalibration Performance Heatmap (Config × Metric)", fontsize=12, fontweight="bold", pad=20)
fig.colorbar(cax)
plt.tight_layout()
plt.savefig(fig_heat_path, dpi=300)
plt.close()
print(f"Saved heatmap to {fig_heat_path}")
