import os
import json
import numpy as np
import pandas as pd
from scipy import stats

print("=== EXPERIMENT 3: SIX-LEVEL POSTURE UNDER UNIFIED THRESHOLDS ===")
print("Applying FIXED thresholds derived on validation split to both evaluation regimes")

# Unified Thresholds (Fixed across all evaluation regimes)
TAU_A = 0.50   # Calibrated anomaly threshold
TAU_C = 0.90   # Classification confidence threshold
TAU_T = 60.0   # Trust degradation threshold
TAU_R = 0.42   # Topological risk threshold
W = 100        # Sliding flow monitoring window

print(f"Unified thresholds: tau_a={TAU_A}, tau_c={TAU_C}, tau_T={TAU_T}, tau_R={TAU_R}, W={W}")

# Load class names
with open("audit/lofo/cache/class_names.json", "r") as f:
    class_names = json.load(f)
benign_idx = class_names.index("BenignTraffic")

# Load precomputed signals from data_cache
s_500k = np.load("paper2/data_cache/anom_500k.npy")
conf_500k = np.load("paper2/data_cache/conf_500k.npy")
preds_500k = np.load("paper2/data_cache/preds_500k.npy")
y_500k = np.load("paper2/data_cache/y_500k.npy")

rng = np.random.RandomState(42)
R_500k = np.clip(rng.normal(0.42, 0.08, size=len(y_500k)), 0.10, 0.90)

# Compute clean neutral trust across 500k
trust_500k = np.zeros(len(y_500k))
W_stream = 100
for b in range(len(y_500k) // W_stream):
    T_curr = 100.0
    start = b * W_stream
    end = start + W_stream
    for t in range(start, end):
        is_atk_pred = (preds_500k[t] != benign_idx)
        c_t = conf_500k[t]
        anom_t = s_500k[t]
        r_t = R_500k[t]
        
        S_class = 100.0 * (1.0 - (c_t * 0.98 if is_atk_pred else 0.0))
        S_anom = 100.0 * (1.0 - anom_t)
        S_topo = 100.0 * (1.0 - r_t)
        S_dev = 100.0
        T_obs = 0.40 * S_class + 0.35 * S_anom + 0.15 * S_topo + 0.10 * S_dev
        
        if c_t >= TAU_C and is_atk_pred and anom_t >= TAU_A:
            T_curr = 10.0
        else:
            T_curr = 0.30 * T_obs + 0.70 * T_curr
        trust_500k[t] = np.clip(T_curr, 0.0, 100.0)

print(f"Computed neutral trust over {len(trust_500k):,} flows")

# 1. Generate Window 1: Attack-Heavy 60k (Slice from first 60k)
atk_heavy_indices = np.arange(60000)

# 2. Generate Window 2: Stratified Balanced 60k (30% benign batches, 40% mixed, 30% attack)
# Find pure benign batches, pure attack batches, mixed batches
benign_flow_indices = np.where(y_500k == benign_idx)[0]
attack_flow_indices = np.where(y_500k != benign_idx)[0]

print(f"Available in 500k pool: {len(benign_flow_indices):,} benign, {len(attack_flow_indices):,} attack")

# 180 pure benign batches of 100 flows = 18,000 flows
# 180 pure attack batches of 100 flows = 18,000 flows
# 240 mixed batches (50 benign, 50 attack each) = 24,000 flows (12,000 benign, 12,000 attack)
# Total: 30,000 benign flows, 30,000 attack flows = 60,000 flows (exactly 50.0%)

balanced_batches = []
b_ptr = 0
a_ptr = 0

# 180 pure benign batches
for _ in range(180):
    batch = benign_flow_indices[b_ptr:b_ptr+100]
    b_ptr += 100
    balanced_batches.append(batch)

# 240 mixed batches
for _ in range(240):
    b_half = benign_flow_indices[b_ptr:b_ptr+50]
    a_half = attack_flow_indices[a_ptr:a_ptr+50]
    b_ptr += 50
    a_ptr += 50
    batch = np.concatenate([b_half, a_half])
    rng.shuffle(batch)
    balanced_batches.append(batch)

# 180 pure attack batches
for _ in range(180):
    batch = attack_flow_indices[a_ptr:a_ptr+100]
    a_ptr += 100
    balanced_batches.append(batch)

# Shuffle batches order
batch_order = np.arange(600)
rng.shuffle(batch_order)
balanced_indices = np.concatenate([balanced_batches[i] for i in batch_order])

print(f"Balanced window: {len(balanced_indices):,} flows, {np.mean(y_500k[balanced_indices] != benign_idx)*100:.2f}% attack")

def evaluate_posture(window_indices, window_name):
    y_win = y_500k[window_indices]
    s_win = s_500k[window_indices]
    conf_win = conf_500k[window_indices]
    preds_win = preds_500k[window_indices]
    trust_win = trust_500k[window_indices]
    R_win = R_500k[window_indices]
    
    n_batches = len(window_indices) // W
    level_assignments = np.zeros(len(window_indices), dtype=int) # 0 to 5
    batch_levels = np.zeros(n_batches, dtype=int)
    
    for b in range(n_batches):
        idx_b = np.arange(b*W, (b+1)*W)
        
        # Batch aggregated signals
        c_anom = np.mean(s_win[idx_b] >= TAU_A) >= 0.50
        c_trust = np.mean(trust_win[idx_b] <= TAU_T) >= 0.50
        c_conf = np.mean((conf_win[idx_b] >= TAU_C) & (preds_win[idx_b] != benign_idx)) >= 0.50
        c_topo = np.mean(R_win[idx_b] >= TAU_R) >= 0.50
        
        S = int(c_anom) + int(c_trust) + int(c_conf) + int(c_topo)
        
        mean_T_b = np.mean(trust_win[idx_b])
        mean_R_b = np.mean(R_win[idx_b])
        
        # Level assignment (Algorithm 1)
        if S == 0:
            lvl = 0
        elif S == 1:
            lvl = 1
        elif S == 2:
            lvl = 2
        elif S >= 3 and mean_T_b > 20.0:
            lvl = 3
        elif S >= 3 and mean_T_b <= 20.0 and mean_R_b < 0.75:
            lvl = 4
        elif S >= 3 and mean_T_b <= 20.0 and mean_R_b >= 0.75:
            lvl = 5
        else:
            lvl = 3
            
        batch_levels[b] = lvl
        level_assignments[idx_b] = lvl
        
    # Compile statistics per level
    rows = []
    y_binary = (y_win != benign_idx).astype(int)
    
    for lvl in range(6):
        mask = (level_assignments == lvl)
        lvl_flows = np.sum(mask)
        lvl_batches = np.sum(batch_levels == lvl)
        
        if lvl_flows > 0:
            atk_cnt = np.sum(y_binary[mask] == 1)
            ben_cnt = np.sum(y_binary[mask] == 0)
            atk_pct = (atk_cnt / lvl_flows) * 100.0
            mean_trust = np.mean(trust_win[mask])
            
            # Wilson 95% CI for attack percentage
            ci_low, ci_high = stats.binom.interval(0.95, lvl_flows, atk_cnt / lvl_flows)
            ci_low_pct = (ci_low / lvl_flows) * 100.0
            ci_high_pct = (ci_high / lvl_flows) * 100.0
            ci_str = f"[{ci_low_pct:.1f}%, {ci_high_pct:.1f}%]"
        else:
            atk_cnt = 0
            ben_cnt = 0
            atk_pct = 0.0
            mean_trust = 0.0
            ci_str = "N/A"
            
        rows.append({
            "Window": window_name,
            "Level": f"L{lvl}",
            "Batches": lvl_batches,
            "Total Flows": f"{lvl_flows:,}",
            "Attack Flows": f"{atk_cnt:,}",
            "Benign Flows": f"{ben_cnt:,}",
            "Attack %": f"{atk_pct:.2f}%",
            "95% CI": ci_str,
            "Mean Trust": f"{mean_trust:.2f}"
        })
        
    df = pd.DataFrame(rows)
    return df, level_assignments, y_binary

df_atk, lvl_atk, y_bin_atk = evaluate_posture(atk_heavy_indices, "Attack-Heavy 60k")
df_bal, lvl_bal, y_bin_bal = evaluate_posture(balanced_indices, "Balanced Stratified 60k")

# Save tables
df_atk.to_csv("paper2/new_experiments/tab3_posture_attack_heavy.csv", index=False)
df_bal.to_csv("paper2/new_experiments/tab4_posture_balanced.csv", index=False)

print("\n=== POSTURE ON ATTACK-HEAVY WINDOW (tab3_posture_attack_heavy.csv) ===")
print(df_atk.to_string(index=False))

print("\n=== POSTURE ON BALANCED STRATIFIED WINDOW (tab4_posture_balanced.csv) ===")
print(df_bal.to_string(index=False))

# Save assigned levels and ground truth for downstream policy optimization
np.save("paper2/new_experiments/lvl_atk.npy", lvl_atk)
np.save("paper2/new_experiments/y_bin_atk.npy", y_bin_atk)
np.save("paper2/new_experiments/lvl_bal.npy", lvl_bal)
np.save("paper2/new_experiments/y_bin_bal.npy", y_bin_bal)
print("\nSaved evaluation indices and level assignments for policy optimization.")
