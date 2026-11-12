import os
import json
import joblib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score

print("=== FINALIZING OBJECTIVE 2 PART B (FINAL ITERATION) ===")

# -------------------------------------------------------------
# 1. Models & Labels
# -------------------------------------------------------------
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

# Load Corrected IF
if_corr = joblib.load("backend/ml_model/saved_models/isolation_forest_corrected.pkl")
s_min, s_p95 = 0.4200, float(-if_corr.offset_)

# Load XGBoost
xgb = joblib.load("backend/ml_model/saved_models/xgboost.pkl")
xgb.set_params(device="cpu")

# Load 120-node TARP
fixed = np.load("audit/scratch_60k_eval_fixed.npz")
tarp_120 = fixed["tarp"].reshape(600, 100)[:120, 0]

# Memory maps for test data
X_test_scaled = np.load("audit/lofo/cache/X_test_scaled.npy", mmap_mode="r")
X_test_unscaled = np.load("audit/lofo/cache/X_test.npy", mmap_mode="r")
y_test = np.load("audit/lofo/cache/y_test.npy")

# -------------------------------------------------------------
# 2. WINDOW 1: Attack-Heavy 60k Window
# -------------------------------------------------------------
print("\n--- Processing Window 1: Attack-Heavy 60k Window ---")
indices_60k = fixed["indices"]
y_60k = fixed["y_sub"]
tarp_60k = fixed["tarp"]
is_attack_60k = (y_60k != 1)

raw_60k = if_corr.score_samples(np.array(X_test_scaled[indices_60k], dtype=np.float32))
anom_60k = np.clip((-raw_60k - s_min) / (s_p95 - s_min) * 0.90, 0, 1)

probs_60k = xgb.predict_proba(np.array(X_test_unscaled[indices_60k], dtype=np.float32))
preds_60k = np.argmax(probs_60k, axis=1)
conf_60k = np.max(probs_60k, axis=1)

# Trust simulation (C3' / C4' logic)
trust_60k = np.zeros(60000)
for e in range(600):
    start = e * 100
    end = start + 100
    init_c = y_60k[start]
    T_0 = priors_by_idx[init_c]
    S_U, S_D, S_B = T_0, T_0 * 0.95, T_0
    T_prev = T_0
    for t in range(start, end):
        if is_attack_60k[t]: S_B = max(0.0, S_B - 2.0)
        else: S_B = min(100.0, S_B + 1.0)
        S_A = 100.0 * (1.0 - anom_60k[t])
        S_T = 100.0 * (1.0 - tarp_60k[t])
        T_obs = np.clip(ALPHA * S_U + BETA * S_D + GAMMA * S_B + DELTA * S_A + LAMBD * S_T, 0.0, 100.0)
        
        is_reset = (conf_60k[t] >= 0.95) and (preds_60k[t] != 1) and (anom_60k[t] >= 0.90)
        if is_reset:
            T_curr = 10.0
        elif preds_60k[t] == 1:
            T_curr = T_obs
        else:
            c_name = class_names[preds_60k[t]]
            a_fam = 0.50 if any(k in c_name for k in ["DDoS", "DoS", "Mirai"]) else (0.15 if any(k in c_name for k in ["Recon", "Scan", "Sweep"]) else 0.30)
            T_curr = np.clip(a_fam * T_obs + (1.0 - a_fam) * T_prev, 0.0, 100.0)
        trust_60k[t] = T_curr
        T_prev = T_curr

# Entity level evaluation on 60k
E_60k, N_60k = 600, 100
t_e_60k = trust_60k.reshape(E_60k, N_60k)
tarp_e_60k = tarp_60k.reshape(E_60k, N_60k)[:, 0]
anom_e_60k = anom_60k.reshape(E_60k, N_60k)
conf_e_60k = conf_60k.reshape(E_60k, N_60k)
preds_e_60k = preds_60k.reshape(E_60k, N_60k)
y_e_60k = y_60k.reshape(E_60k, N_60k)
mean_t_60k = t_e_60k.mean(axis=1)

# Attack-heavy window thresholds: 0.28 / 0.26
c_topo_60k = (tarp_e_60k >= 0.42).astype(int)
c_trust_60k = (t_e_60k.min(axis=1) <= 60.0).astype(int)
c_anom_60k = ((anom_e_60k >= 0.90).mean(axis=1) >= 0.28).astype(int)
c_conf_60k = (((conf_e_60k >= 0.95) & (preds_e_60k != 1)).mean(axis=1) >= 0.26).astype(int)
S_60k = c_topo_60k + c_trust_60k + c_anom_60k + c_conf_60k

levels_60k = np.zeros(E_60k, dtype=int)
for e in range(E_60k):
    fam_chunk = [get_family(p) for p in preds_e_60k[e] if p != 1]
    distinct_fams = len(set(fam_chunk))
    mt = mean_t_60k[e]
    tp = tarp_e_60k[e]
    
    # Fix 2: Unambiguous monotonicity hierarchy
    # L5: S >= 3 AND mean_trust <= 20 AND families >= 3 AND TARP >= 0.75 (critical hub + multi-vector)
    # L4: S >= 3 AND mean_trust <= 20 AND families >= 2 AND NOT(TARP >= 0.75) (containment off-hub)
    # L3: S >= 3 AND NOT(L4) AND NOT(L5)
    if S_60k[e] >= 3 and (mt <= 20.0) and (distinct_fams >= 3) and (tp >= 0.75):
        levels_60k[e] = 5
    elif S_60k[e] >= 3 and (mt <= 20.0) and (distinct_fams >= 2) and not (tp >= 0.75):
        levels_60k[e] = 4
    elif S_60k[e] >= 3:
        levels_60k[e] = 3
    elif S_60k[e] == 2:
        levels_60k[e] = 2
    elif S_60k[e] == 1:
        levels_60k[e] = 1
    else:
        levels_60k[e] = 0

# Save Table O2_B6_attack_60k.csv
os.makedirs("paper2/tables", exist_ok=True)
csv_60k_path = "paper2/tables/O2_B6_attack_60k.csv"
with open(csv_60k_path, "w", encoding="utf-8") as f:
    f.write("window,level,entities,share%,mean_trust,attack%,monotonicity_status\n")
    prev_atk = -1.0
    for lvl in range(6):
        mask = (levels_60k == lvl)
        cnt = int(np.sum(mask))
        sh = cnt / E_60k * 100
        mt = float(np.mean(t_e_60k[mask])) if cnt > 0 else 0.0
        atk_p = float(np.mean(y_e_60k[mask] != 1) * 100) if cnt > 0 else 0.0
        
        status = "N/A (empty)"
        if cnt > 0:
            if prev_atk < 0:
                status = "Baseline"
            elif atk_p >= prev_atk:
                status = "Monotonic (Non-decreasing)"
            else:
                status = "Inverted"
            prev_atk = atk_p
            
        f.write(f"Attack-heavy 60k,L{lvl},{cnt},{sh:.2f},{mt:.2f},{atk_p:.2f},{status}\n")

print(f"Saved {csv_60k_path}")


# -------------------------------------------------------------
# 3. WINDOW 2: Stratified Balanced Window (Fix 1)
# -------------------------------------------------------------
print("\n--- Processing Window 2: Stratified Balanced Window (30/40/30) ---")
b_all = np.where(y_test == 1)[0]
a_all = np.where(y_test != 1)[0]

rng = np.random.default_rng(42)

# Fix 1: Stratified construction (180 pure benign + 240 mixed + 180 pure attack = 600 entities)
b_pure = rng.choice(b_all, size=180*100, replace=False).reshape(180, 100)
a_pure = rng.choice(a_all, size=180*100, replace=False).reshape(180, 100)
mixed = []
for _ in range(240):
    k_atk = rng.binomial(100, 0.5)
    k_ben = 100 - k_atk
    idx_a = rng.choice(a_all, size=k_atk, replace=False)
    idx_b = rng.choice(b_all, size=k_ben, replace=False)
    flows = np.concatenate([idx_a, idx_b])
    rng.shuffle(flows)
    mixed.append(flows)
mixed = np.array(mixed)

all_entities = np.concatenate([b_pure, mixed, a_pure], axis=0) # shape (600, 100)
entity_order = np.arange(600)
rng.shuffle(entity_order)
all_entities = all_entities[entity_order]

bal_indices = all_entities.flatten()
y_bal = y_test[bal_indices]
is_atk_bal = (y_bal != 1)

raw_bal = if_corr.score_samples(np.array(X_test_scaled[bal_indices], dtype=np.float32))
anom_bal = np.clip((-raw_bal - s_min) / (s_p95 - s_min) * 0.90, 0, 1)

probs_bal = xgb.predict_proba(np.array(X_test_unscaled[bal_indices], dtype=np.float32))
preds_bal = np.argmax(probs_bal, axis=1)
conf_bal = np.max(probs_bal, axis=1)

E_bal, N_bal = 600, 100
tarp_bal = np.array([tarp_120[e % 120] for e in range(E_bal) for _ in range(N_bal)])

# Trust simulation on balanced window
trust_bal = np.zeros(60000)
for e in range(600):
    start = e * 100
    end = start + 100
    init_c = y_bal[start]
    T_0 = priors_by_idx[init_c]
    S_U, S_D, S_B = T_0, T_0 * 0.95, T_0
    T_prev = T_0
    for t in range(start, end):
        if is_atk_bal[t]: S_B = max(0.0, S_B - 2.0)
        else: S_B = min(100.0, S_B + 1.0)
        S_A = 100.0 * (1.0 - anom_bal[t])
        S_T = 100.0 * (1.0 - tarp_bal[t])
        T_obs = np.clip(ALPHA * S_U + BETA * S_D + GAMMA * S_B + DELTA * S_A + LAMBD * S_T, 0.0, 100.0)
        
        is_reset = (conf_bal[t] >= 0.95) and (preds_bal[t] != 1) and (anom_bal[t] >= 0.90)
        if is_reset:
            T_curr = 10.0
        elif preds_bal[t] == 1:
            T_curr = T_obs
        else:
            c_name = class_names[preds_bal[t]]
            a_fam = 0.50 if any(k in c_name for k in ["DDoS", "DoS", "Mirai"]) else (0.15 if any(k in c_name for k in ["Recon", "Scan", "Sweep"]) else 0.30)
            T_curr = np.clip(a_fam * T_obs + (1.0 - a_fam) * T_prev, 0.0, 100.0)
        trust_bal[t] = T_curr
        T_prev = T_curr

# Entity level evaluation on balanced window
t_e_bal = trust_bal.reshape(E_bal, N_bal)
tarp_e_bal = tarp_bal.reshape(E_bal, N_bal)[:, 0]
anom_e_bal = anom_bal.reshape(E_bal, N_bal)
conf_e_bal = conf_bal.reshape(E_bal, N_bal)
preds_e_bal = preds_bal.reshape(E_bal, N_bal)
y_e_bal = y_bal.reshape(E_bal, N_bal)
mean_t_bal = t_e_bal.mean(axis=1)

# Fix 3: Balanced-window thresholds (0.55 / 0.55)
tau_anom_bal, tau_conf_bal = 0.55, 0.55
c_topo_bal = (tarp_e_bal >= 0.42).astype(int)
c_trust_bal = (t_e_bal.min(axis=1) <= 60.0).astype(int)
c_anom_bal = ((anom_e_bal >= 0.90).mean(axis=1) >= tau_anom_bal).astype(int)
c_conf_bal = (((conf_e_bal >= 0.95) & (preds_e_bal != 1)).mean(axis=1) >= tau_conf_bal).astype(int)
S_bal = c_topo_bal + c_trust_bal + c_anom_bal + c_conf_bal

levels_bal = np.zeros(E_bal, dtype=int)
for e in range(E_bal):
    fam_chunk = [get_family(p) for p in preds_e_bal[e] if p != 1]
    distinct_fams = len(set(fam_chunk))
    mt = mean_t_bal[e]
    tp = tarp_e_bal[e]
    
    # Fix 2: Unambiguous monotonicity hierarchy
    if S_bal[e] >= 3 and (mt <= 20.0) and (distinct_fams >= 3) and (tp >= 0.75):
        levels_bal[e] = 5
    elif S_bal[e] >= 3 and (mt <= 20.0) and (distinct_fams >= 2) and not (tp >= 0.75):
        levels_bal[e] = 4
    elif S_bal[e] >= 3:
        levels_bal[e] = 3
    elif S_bal[e] == 2:
        levels_bal[e] = 2
    elif S_bal[e] == 1:
        levels_bal[e] = 1
    else:
        levels_bal[e] = 0

# Save Table O2_B6_balanced_flowlevel.csv
csv_bal_path = "paper2/tables/O2_B6_balanced_flowlevel.csv"
with open(csv_bal_path, "w", encoding="utf-8") as f:
    f.write("window,level,entities,share%,mean_trust,attack%,monotonicity_status\n")
    prev_atk = -1.0
    for lvl in range(6):
        mask = (levels_bal == lvl)
        cnt = int(np.sum(mask))
        sh = cnt / E_bal * 100
        mt = float(np.mean(t_e_bal[mask])) if cnt > 0 else 0.0
        atk_p = float(np.mean(y_e_bal[mask] != 1) * 100) if cnt > 0 else 0.0
        
        status = "N/A (empty)"
        if cnt > 0:
            if prev_atk < 0:
                status = "Baseline"
            elif atk_p >= prev_atk:
                status = "Monotonic (Non-decreasing)"
            else:
                status = "Inverted"
            prev_atk = atk_p
            
        f.write(f"Balanced Stratified,L{lvl},{cnt},{sh:.2f},{mt:.2f},{atk_p:.2f},{status}\n")

print(f"Saved {csv_bal_path}")

print("\n=== SUMMARY COMPARISON ===")
print("--- Attack-heavy 60k Window ---")
for lvl in range(6):
    mask = (levels_60k == lvl)
    c = np.sum(mask)
    if c > 0:
        print(f"L{lvl}: {c:3d} entities ({c/E_60k*100:5.2f}%), Mean Trust: {np.mean(t_e_60k[mask]):5.2f}, Attack%: {np.mean(y_e_60k[mask]!=1)*100:5.2f}%")
    else:
        print(f"L{lvl}:   0 entities ( 0.00%)")

print("\n--- Stratified Balanced Window ---")
for lvl in range(6):
    mask = (levels_bal == lvl)
    c = np.sum(mask)
    if c > 0:
        print(f"L{lvl}: {c:3d} entities ({c/E_bal*100:5.2f}%), Mean Trust: {np.mean(t_e_bal[mask]):5.2f}, Attack%: {np.mean(y_e_bal[mask]!=1)*100:5.2f}%")
    else:
        print(f"L{lvl}:   0 entities ( 0.00%)")
