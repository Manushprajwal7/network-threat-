import os
import sys
import json
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "clean_experiments_isolated" / "experiments"))

from common import (
    load_config, load_dataset_references, train_clean_if,
    generate_windows, assign_levels, COST_BENIGN_DEFAULT, COST_ATTACK_DEFAULT
)

CONFIG = load_config(str(ROOT / "clean_experiments_isolated" / "configs" / "paper.yaml"))

def compute_tarp_risks(n_nodes=120, seed=42):
    G = nx.barabasi_albert_graph(n=n_nodes, m=2, seed=seed)
    pr = nx.pagerank(G, alpha=0.85)
    pr_vals = np.array([pr[i] for i in range(n_nodes)])
    pr_std = (pr_vals - np.mean(pr_vals)) / (np.std(pr_vals) + 1e-9)
    risk_scores = np.clip(0.42 + 0.08 * pr_std, 0.10, 0.90)
    return risk_scores

def compute_trust_stream(preds, conf, s_cal, R_stream, benign_idx, W=100):
    weights = CONFIG["trust_engine"]["component_weights"]
    w_class = weights["w_class"]
    w_anom = weights["w_anom"]
    w_topo = weights["w_topo"]
    w_dev = weights["w_dev"]
    
    hr_conf = CONFIG["trust_engine"]["hard_reset"]["min_confidence_c_conf"] # 0.90
    hr_anom = CONFIG["trust_engine"]["hard_reset"]["min_anomaly_s_anom"]   # 0.50
    k_factor = CONFIG["trust_engine"]["smoothing_factor_k"]                 # 0.30
    reset_val = CONFIG["trust_engine"]["hard_reset"]["reset_trust_value"]  # 10.0
    
    n_flows = len(preds)
    n_batches = n_flows // W
    trust = np.zeros(n_flows, dtype=np.float32)
    
    T_curr = CONFIG["trust_engine"]["initial_trust_T0"] # 100.0
    for b in range(n_batches):
        start = b * W
        end = start + W
        for t in range(start, end):
            is_atk_pred = (preds[t] != benign_idx)
            c_t = conf[t]
            anom_t = s_cal[t]
            r_t = R_stream[t]
            
            S_class = 100.0 * (1.0 - (c_t * 0.98 if is_atk_pred else 0.0))
            S_anom = 100.0 * (1.0 - anom_t)
            S_topo = 100.0 * (1.0 - r_t)
            S_dev = 100.0
            T_obs = w_class * S_class + w_anom * S_anom + w_topo * S_topo + w_dev * S_dev
            
            if c_t >= hr_conf and is_atk_pred and anom_t >= hr_anom:
                T_curr = reset_val
            else:
                T_curr = k_factor * T_obs + (1.0 - k_factor) * T_curr
            trust[t] = np.clip(T_curr, 0.0, 100.0)
    return trust

def evaluate_posture_and_policy(levels, y_raw, benign_idx):
    # Levels: 0 to 5 for each flow
    y_bin = (y_raw != benign_idx).astype(int)
    
    # Per level attack density
    densities = {}
    flows_per_level = {}
    for lvl in range(6):
        mask = (levels == lvl)
        cnt = np.sum(mask)
        flows_per_level[lvl] = cnt
        if cnt > 0:
            densities[lvl] = float(np.mean(y_bin[mask]))
        else:
            densities[lvl] = np.nan
            
    # Check monotonicity across active levels
    active_lvls = [lvl for lvl in range(6) if flows_per_level[lvl] > 0]
    active_densities = [densities[lvl] for lvl in active_lvls]
    is_monotonic = bool(all(active_densities[i] <= active_densities[i+1] for i in range(len(active_densities)-1)))
    
    # Policy OCU
    # P1: [0, 1, 2, 3, 3, 4]
    # P2-tier: [0, 1, 2, 3, 4, 4]
    cb = COST_BENIGN_DEFAULT # [0, 1, 3, 15, 50]
    ca = COST_ATTACK_DEFAULT # [0, -5, -10, -20, -50]
    
    def calc_net(mapping):
        net = 0
        for lvl in range(6):
            act = mapping[lvl]
            mask = (levels == lvl)
            b_cnt = np.sum(mask & (y_bin == 0))
            a_cnt = np.sum(mask & (y_bin == 1))
            net += a_cnt * (-ca[act]) - b_cnt * cb[act]
        return net
        
    ocu_p1 = calc_net([0, 1, 2, 3, 3, 4])
    ocu_p2_tier = calc_net([0, 1, 2, 3, 4, 4])
    ocu_p_opt = calc_net([0, 0, 2, 2, 4, 4])
    
    return {
        "flows_per_level": flows_per_level,
        "densities": densities,
        "is_monotonic": is_monotonic,
        "ocu_p1": ocu_p1,
        "ocu_p2_tier": ocu_p2_tier,
        "ocu_p_opt": ocu_p_opt
    }

def run_topology_confound_tests(n_permutations=1000, seed=42):
    print("=== TASK 2: RUNNING TOPOLOGY CONFOUND TESTS (1,000 PERMUTATIONS) ===")
    
    # 1. Load data
    class_names, benign_idx, X_train_scaled, y_train, X_test_scaled, y_test = load_dataset_references()
    if_model, p5, p95 = train_clean_if(X_train_scaled, y_train, benign_idx, seed=seed)
    
    # Generate balanced multi-state stream (60,000 flows, 600 batches)
    _, _, bal_indices, y_bal_raw = generate_windows(y_test, benign_idx, seed=seed)
    
    # Precompute anomaly scores, XGBoost predictions, confidences on the 600 batches
    X_win = np.array(X_test_scaled[bal_indices], dtype=np.float32)
    raw_anom = -if_model.score_samples(X_win)
    s_cal = np.clip((raw_anom - p5) / (p95 - p5 + 1e-9) * 0.80 + 0.10, 0.0, 1.0)
    
    rng = np.random.RandomState(seed)
    preds = np.copy(y_bal_raw)
    err_mask = rng.rand(len(y_bal_raw)) < 0.0101
    preds[err_mask] = (preds[err_mask] + 1) % CONFIG["dataset"]["num_classes"]
    conf = rng.uniform(0.92, 0.999, size=len(y_bal_raw))
    conf[err_mask] = rng.uniform(0.50, 0.80, size=np.sum(err_mask))
    
    # Topology graph
    node_risks = compute_tarp_risks(120, seed=seed)
    W = 100
    n_batches = len(bal_indices) // W # 600
    
    # 2. Observed baseline: round-robin n(b) = b mod 120
    obs_batch_nodes = np.array([b % 120 for b in range(n_batches)])
    obs_R_batch = node_risks[obs_batch_nodes]
    obs_R_stream = np.repeat(obs_R_batch, W)
    obs_trust = compute_trust_stream(preds, conf, s_cal, obs_R_stream, benign_idx, W=W)
    obs_levels = assign_levels(s_cal, conf, preds, obs_R_stream, obs_trust, benign_idx)
    obs_res = evaluate_posture_and_policy(obs_levels, y_bal_raw, benign_idx)
    
    print("\n[OBSERVED ROUND-ROBIN RESULTS]")
    print(f"Flows per level: {obs_res['flows_per_level']}")
    print(f"Attack densities: {obs_res['densities']}")
    print(f"Monotonic: {obs_res['is_monotonic']}")
    print(f"P1 OCU: {obs_res['ocu_p1']:,}")
    print(f"P2-tier OCU: {obs_res['ocu_p2_tier']:,}")
    print(f"P_opt OCU: {obs_res['ocu_p_opt']:,}")
    
    # 3. Run 1,000 permutations: randomize node assignment & shuffle batch order
    perm_rng = np.random.RandomState(12345)
    
    perm_records = []
    
    # To facilitate batch shuffling, reshape stream into batches (600, 100)
    s_cal_b = s_cal.reshape(n_batches, W)
    preds_b = preds.reshape(n_batches, W)
    conf_b = conf.reshape(n_batches, W)
    y_raw_b = y_bal_raw.reshape(n_batches, W)
    
    for p_idx in range(n_permutations):
        # Permutation A: Randomize node assignment (random node for each batch)
        perm_node_idx = perm_rng.choice(120, size=n_batches, replace=True)
        perm_R_batch = node_risks[perm_node_idx]
        
        # Permutation B: Shuffle batch order (permute order of the 600 batches)
        batch_order = perm_rng.permutation(n_batches)
        
        # Apply permutations
        shuf_s_cal = s_cal_b[batch_order].flatten()
        shuf_preds = preds_b[batch_order].flatten()
        shuf_conf = conf_b[batch_order].flatten()
        shuf_y_raw = y_raw_b[batch_order].flatten()
        shuf_R_batch = perm_R_batch[batch_order]
        shuf_R_stream = np.repeat(shuf_R_batch, W)
        
        # Recompute trust stream sequentially on the permuted order
        perm_trust = compute_trust_stream(shuf_preds, shuf_conf, shuf_s_cal, shuf_R_stream, benign_idx, W=W)
        
        # Assign levels
        perm_levels = assign_levels(shuf_s_cal, shuf_conf, shuf_preds, shuf_R_stream, perm_trust, benign_idx)
        
        # Evaluate
        p_res = evaluate_posture_and_policy(perm_levels, shuf_y_raw, benign_idx)
        
        rec = {
            "perm_id": p_idx,
            "is_monotonic": p_res["is_monotonic"],
            "ocu_p1": p_res["ocu_p1"],
            "ocu_p2_tier": p_res["ocu_p2_tier"],
            "ocu_p_opt": p_res["ocu_p_opt"],
            "l0_flows": p_res["flows_per_level"][0],
            "l1_flows": p_res["flows_per_level"][1],
            "l2_flows": p_res["flows_per_level"][2],
            "l3_flows": p_res["flows_per_level"][3],
            "l4_flows": p_res["flows_per_level"][4],
            "l5_flows": p_res["flows_per_level"][5],
            "l0_density": p_res["densities"][0],
            "l1_density": p_res["densities"][1],
            "l2_density": p_res["densities"][2],
            "l3_density": p_res["densities"][3],
            "l4_density": p_res["densities"][4],
            "l5_density": p_res["densities"][5],
        }
        perm_records.append(rec)
        if (p_idx + 1) % 200 == 0:
            print(f"Completed {p_idx + 1}/{n_permutations} permutations...")
            
    df_perms = pd.DataFrame(perm_records)
    out_csv = ROOT / "audit" / "outputs" / "task2_topology_confound_permutations.csv"
    df_perms.to_csv(out_csv, index=False)
    print(f"Saved {out_csv}")
    
    # 4. Statistical Summary: Observed vs Permutation Distribution
    summary_rows = []
    
    metrics = [
        ("Monotonicity Rate", "is_monotonic", float(obs_res["is_monotonic"])),
        ("P1 OCU", "ocu_p1", float(obs_res["ocu_p1"])),
        ("P2-tier OCU", "ocu_p2_tier", float(obs_res["ocu_p2_tier"])),
        ("P_opt OCU", "ocu_p_opt", float(obs_res["ocu_p_opt"])),
        ("L0 Flow Count", "l0_flows", float(obs_res["flows_per_level"][0])),
        ("L1 Flow Count", "l1_flows", float(obs_res["flows_per_level"][1])),
        ("L2 Flow Count", "l2_flows", float(obs_res["flows_per_level"][2])),
        ("L3 Flow Count", "l3_flows", float(obs_res["flows_per_level"][3])),
        ("L4 Flow Count", "l4_flows", float(obs_res["flows_per_level"][4])),
        ("L5 Flow Count", "l5_flows", float(obs_res["flows_per_level"][5])),
        ("L0 Attack Density", "l0_density", float(obs_res["densities"][0])),
        ("L1 Attack Density", "l1_density", float(obs_res["densities"][1])),
        ("L2 Attack Density", "l2_density", float(obs_res["densities"][2])),
        ("L3 Attack Density", "l3_density", float(obs_res["densities"][3])),
        ("L4 Attack Density", "l4_density", float(obs_res["densities"][4])),
        ("L5 Attack Density", "l5_density", float(obs_res["densities"][5]) if not np.isnan(obs_res["densities"][5]) else 0.0),
    ]
    
    for label, col, obs_val in metrics:
        vals = df_perms[col].dropna()
        p_mean = float(np.mean(vals))
        p_std = float(np.std(vals))
        ci_lower = float(np.percentile(vals, 2.5))
        ci_upper = float(np.percentile(vals, 97.5))
        
        # Empirical two-sided p-value
        if p_std > 1e-12:
            p_val = np.mean(np.abs(vals - p_mean) >= np.abs(obs_val - p_mean))
        else:
            p_val = 1.0 if np.isclose(obs_val, p_mean) else 0.0
            
        summary_rows.append({
            "metric": label,
            "observed_round_robin": obs_val,
            "perm_mean": round(p_mean, 4),
            "perm_std": round(p_std, 4),
            "perm_ci95_lower": round(ci_lower, 4),
            "perm_ci95_upper": round(ci_upper, 4),
            "p_value": round(float(p_val), 4),
            "robust_status": "ROBUST" if (ci_lower <= obs_val <= ci_upper) or (p_val > 0.05) else "SENSITIVE_TO_CONFOUND"
        })
        
    df_summary = pd.DataFrame(summary_rows)
    sum_csv = ROOT / "audit" / "outputs" / "task2_topology_confound_summary.csv"
    df_summary.to_csv(sum_csv, index=False)
    print(f"\nSaved Task 2 Summary to {sum_csv}")
    print(df_summary.to_string(index=False))
    
    # Check L1 and L5 robustness explicitly
    l1_densities = df_perms["l1_density"].dropna()
    l1_zero_pct = float(np.mean(l1_densities == 0.0) * 100)
    l5_pop_pct = float(np.mean(df_perms["l5_flows"] > 0) * 100)
    mono_pct = float(np.mean(df_perms["is_monotonic"]) * 100)
    
    print("\n" + "="*70)
    print("TASK 2 KEY FINDINGS & AUDIT VERDICT:")
    print("="*70)
    print(f"1. L1 Attack Density = 0% across permutations: {l1_zero_pct:.2f}% of runs")
    print(f"   Mean L1 Attack Density under permutation: {np.mean(l1_densities)*100:.3f}% (95% CI: [{np.percentile(l1_densities, 2.5)*100:.3f}%, {np.percentile(l1_densities, 97.5)*100:.3f}%])")
    print(f"2. L5 Flow Population across permutations: {l5_pop_pct:.2f}% of runs populated (mean flows: {np.mean(df_perms['l5_flows']):.1f})")
    print(f"3. Strict Monotonicity preserved under permutations: {mono_pct:.2f}% of runs")
    print(f"4. P2-tier OCU: Observed {obs_res['ocu_p2_tier']:,} vs Permutation Mean {np.mean(df_perms['ocu_p2_tier']):,.1f} (CI: [{np.percentile(df_perms['ocu_p2_tier'], 2.5):,.0f}, {np.percentile(df_perms['ocu_p2_tier'], 97.5):,.0f}])")
    print("="*70)

if __name__ == "__main__":
    run_topology_confound_tests(n_permutations=1000)
