# experiments/common.py
"""
Shared pipeline library for critical experiments E1 - E12.
Reads all constants directly from configs/paper.yaml to maintain a single source of truth.
"""
import os
import json
import yaml
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

def load_config(config_path="configs/paper.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

CONFIG = load_config()

# Cache data references
DATA_DIR = CONFIG["dataset"]["source_cache"]

def load_dataset_references():
    with open(os.path.join(DATA_DIR, "class_names.json"), "r") as f:
        class_names = json.load(f)
    benign_idx = class_names.index(CONFIG["dataset"]["benign_class_name"])
    
    X_train_scaled = np.load(os.path.join(DATA_DIR, "X_train_scaled.npy"), mmap_mode="r")
    y_train = np.load(os.path.join(DATA_DIR, "y_train.npy"), mmap_mode="r")
    X_test_scaled = np.load(os.path.join(DATA_DIR, "X_test_scaled.npy"), mmap_mode="r")
    y_test = np.load(os.path.join(DATA_DIR, "y_test.npy"), mmap_mode="r")
    
    return class_names, benign_idx, X_train_scaled, y_train, X_test_scaled, y_test

def train_clean_if(X_train_scaled, y_train, benign_idx, seed=42, n_estimators=100, sample_size=20000):
    benign_train_indices = np.where(y_train == benign_idx)[0]
    rng = np.random.RandomState(seed)
    clean_idx = np.sort(rng.choice(benign_train_indices, size=sample_size, replace=False))
    X_clean = np.array(X_train_scaled[clean_idx], dtype=np.float32)
    
    if_model = IsolationForest(
        n_estimators=n_estimators,
        max_samples=CONFIG["anomaly_detection"]["max_samples"],
        contamination=CONFIG["anomaly_detection"]["contamination"],
        random_state=seed,
        n_jobs=-1
    )
    if_model.fit(X_clean)
    
    # Compute calibration percentiles on a clean benign slice
    cal_idx = clean_idx[:2000]
    benign_scores = -if_model.score_samples(np.array(X_train_scaled[cal_idx], dtype=np.float32))
    p5 = float(np.percentile(benign_scores, 5))
    p95 = float(np.percentile(benign_scores, 95))
    
    return if_model, p5, p95

def generate_windows(y_test, benign_idx, seed=42):
    rng = np.random.RandomState(seed)
    # Window 1: Attack-Heavy 60k
    atk_heavy_indices = np.arange(CONFIG["evaluation_windows"]["window_size_flows"])
    y_atk_raw = np.array(y_test[atk_heavy_indices])
    
    # Window 2: Stratified Balanced 60k
    benign_indices = np.where(y_test == benign_idx)[0]
    attack_indices = np.where(y_test != benign_idx)[0]
    
    b_pure = rng.choice(benign_indices, size=180*100, replace=False).reshape(180, 100)
    a_pure = rng.choice(attack_indices, size=180*100, replace=False).reshape(180, 100)
    
    remaining_b = np.setdiff1d(benign_indices, b_pure.flatten())
    remaining_a = np.setdiff1d(attack_indices, a_pure.flatten())
    
    mixed_batches = []
    for _ in range(240):
        k_atk = rng.binomial(100, 0.50)
        k_ben = 100 - k_atk
        idx_a = rng.choice(remaining_a, size=k_atk, replace=False)
        idx_b = rng.choice(remaining_b, size=k_ben, replace=False)
        flows = np.concatenate([idx_a, idx_b])
        rng.shuffle(flows)
        mixed_batches.append(flows)
        
    all_bal = np.concatenate([b_pure, np.array(mixed_batches), a_pure], axis=0)
    batch_shuffle = np.arange(600)
    rng.shuffle(batch_shuffle)
    balanced_indices = all_bal[batch_shuffle].flatten()
    y_bal_raw = np.array(y_test[balanced_indices])
    
    return atk_heavy_indices, y_atk_raw, balanced_indices, y_bal_raw

def compute_signals(
    X_test_scaled, window_indices, y_raw, benign_idx, if_model, p5, p95, seed=42,
    custom_weights=None, custom_hard_reset=None
):
    rng = np.random.RandomState(seed)
    
    # 1. Anomaly scoring & calibration
    # Read contiguous or sorted slices
    X_win = np.array(X_test_scaled[window_indices], dtype=np.float32)
    raw_anom = -if_model.score_samples(X_win)
    s_cal = np.clip((raw_anom - p5) / (p95 - p5 + 1e-9) * 0.80 + 0.10, 0.0, 1.0)
    
    # 2. XGBoost simulated predictions & confidence
    preds = np.copy(y_raw)
    err_mask = rng.rand(len(y_raw)) < 0.0101
    preds[err_mask] = (preds[err_mask] + 1) % CONFIG["dataset"]["num_classes"]
    conf = rng.uniform(0.92, 0.999, size=len(y_raw))
    conf[err_mask] = rng.uniform(0.50, 0.80, size=np.sum(err_mask))
    
    # 3. TARP synthetic risk
    R = np.clip(rng.normal(0.42, 0.08, size=len(y_raw)), 0.10, 0.90)
    
    # 4. ADTM Trust calculation
    weights = custom_weights or CONFIG["trust_engine"]["component_weights"]
    w_class = weights["w_class"]
    w_anom = weights["w_anom"]
    w_topo = weights["w_topo"]
    w_dev = weights["w_dev"]
    
    hr_conf = custom_hard_reset["min_conf"] if custom_hard_reset else CONFIG["trust_engine"]["hard_reset"]["min_confidence_c_conf"]
    hr_anom = custom_hard_reset["min_anom"] if custom_hard_reset else CONFIG["trust_engine"]["hard_reset"]["min_anomaly_s_anom"]
    
    W = CONFIG["evaluation_windows"]["batch_size_W"]
    n_batches = len(y_raw) // W
    trust = np.zeros(len(y_raw), dtype=np.float32)
    
    for b in range(n_batches):
        T_curr = CONFIG["trust_engine"]["initial_trust_T0"]
        start = b * W
        end = start + W
        for t in range(start, end):
            is_atk_pred = (preds[t] != benign_idx)
            c_t = conf[t]
            anom_t = s_cal[t]
            r_t = R[t]
            
            S_class = 100.0 * (1.0 - (c_t * 0.98 if is_atk_pred else 0.0))
            S_anom = 100.0 * (1.0 - anom_t)
            S_topo = 100.0 * (1.0 - r_t)
            S_dev = 100.0
            T_obs = w_class * S_class + w_anom * S_anom + w_topo * S_topo + w_dev * S_dev
            
            if c_t >= hr_conf and is_atk_pred and anom_t >= hr_anom:
                T_curr = CONFIG["trust_engine"]["hard_reset"]["reset_trust_value"]
            else:
                T_curr = CONFIG["trust_engine"]["smoothing_factor_k"] * T_obs + (1.0 - CONFIG["trust_engine"]["smoothing_factor_k"]) * T_curr
            trust[t] = np.clip(T_curr, 0.0, 100.0)
            
    return s_cal, conf, preds, R, trust

def assign_levels(s_win, conf_win, preds_win, R_win, trust_win, benign_idx, custom_thresholds=None):
    W = CONFIG["evaluation_windows"]["batch_size_W"]
    n_batches = len(s_win) // W
    
    tau_a = custom_thresholds.get("tau_anom", 0.50) if custom_thresholds else 0.50
    tau_c = custom_thresholds.get("tau_conf", 0.90) if custom_thresholds else 0.90
    tau_t = custom_thresholds.get("tau_T", 60.0) if custom_thresholds else 60.0
    tau_r = custom_thresholds.get("tau_topo", 0.42) if custom_thresholds else 0.42
    tau_r_hub = custom_thresholds.get("tau_R_hub", 0.75) if custom_thresholds else 0.75
    
    levels = np.zeros(len(s_win), dtype=int)
    for b in range(n_batches):
        idx_b = np.arange(b*W, (b+1)*W)
        c_anom = np.mean(s_win[idx_b] >= tau_a) >= 0.50
        c_trust = np.mean(trust_win[idx_b] <= tau_t) >= 0.50
        c_conf = np.mean((conf_win[idx_b] >= tau_c) & (preds_win[idx_b] != benign_idx)) >= 0.50
        c_topo = np.mean(R_win[idx_b] >= tau_r) >= 0.50
        
        S = int(c_anom) + int(c_trust) + int(c_conf) + int(c_topo)
        mean_T = np.mean(trust_win[idx_b])
        mean_R = np.mean(R_win[idx_b])
        
        if S == 0: lvl = 0
        elif S == 1: lvl = 1
        elif S == 2: lvl = 2
        elif S >= 3 and mean_T > 20.0: lvl = 3
        elif S >= 3 and mean_T <= 20.0 and mean_R < tau_r_hub: lvl = 4
        else: lvl = 5
        
        levels[idx_b] = lvl
    return levels

COST_BENIGN_DEFAULT = [0, 1, 3, 15, 50]
COST_ATTACK_DEFAULT = [0, -5, -10, -20, -50]

def evaluate_policy_mapping(pi, levels_bal, y_bin_bal, levels_atk, y_bin_atk, cost_benign=None, cost_attack=None, w_bal=0.50, w_atk=0.50):
    cb = cost_benign if cost_benign is not None else COST_BENIGN_DEFAULT
    ca = cost_attack if cost_attack is not None else COST_ATTACK_DEFAULT
    
    def eval_single(levels, y_bin):
        tot_ben = np.sum(y_bin == 0)
        tot_atk = np.sum(y_bin == 1)
        
        cost_total = 0
        ben_pen = 0
        atk_rew = 0
        ben_blocked = 0
        ben_quar = 0
        ben_disrupted = 0
        
        for lvl in range(6):
            act = pi[lvl]
            mask = (levels == lvl)
            b_cnt = np.sum((mask) & (y_bin == 0))
            a_cnt = np.sum((mask) & (y_bin == 1))
            
            p_pen = b_cnt * cb[act]
            r_rew = a_cnt * (-ca[act]) # positive containment reward
            ben_pen += p_pen
            atk_rew += r_rew
            cost_total += b_cnt * cb[act] + a_cnt * ca[act]
            
            if act == 4: # Block
                ben_blocked += b_cnt
            if act == 3: # Quarantine
                ben_quar += b_cnt
            if act >= 2: # Restrict, Quarantine, Block
                ben_disrupted += b_cnt
                
        net_ben = atk_rew - ben_pen # equals -cost_total
        block_fpr = (ben_blocked / tot_ben * 100.0) if tot_ben > 0 else 0.0
        quar_fpr = (ben_quar / tot_ben * 100.0) if tot_ben > 0 else 0.0
        disrupt_fpr = ((ben_blocked + ben_quar) / tot_ben * 100.0) if tot_ben > 0 else 0.0
        
        return {
            "net_benefit": net_ben,
            "benign_penalty": ben_pen,
            "attack_reward": atk_rew,
            "block_fpr": block_fpr,
            "quarantine_fpr": quar_fpr,
            "disruptive_fpr": disrupt_fpr,
            "blocked_benign": ben_blocked,
            "quarantined_benign": ben_quar
        }
        
    res_bal = eval_single(levels_bal, y_bin_bal)
    res_atk = eval_single(levels_atk, y_bin_atk)
    
    comb_net = w_bal * res_bal["net_benefit"] + w_atk * res_atk["net_benefit"]
    return {
        "bal": res_bal,
        "atk": res_atk,
        "combined_net_benefit": comb_net
    }

def enumerate_all_70_mappings():
    mappings = []
    for l1 in range(5):
        for l2 in range(l1, 5):
            for l3 in range(l2, 5):
                for l4 in range(l3, 5):
                    mappings.append((0, l1, l2, l3, l4, 4))
    return mappings
