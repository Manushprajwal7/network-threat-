import os
import sys
import time
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "clean_experiments_isolated" / "experiments"))

from common import (
    load_config, load_dataset_references, train_clean_if,
    generate_windows, assign_levels, COST_BENIGN_DEFAULT, COST_ATTACK_DEFAULT
)

CONFIG = load_config(str(ROOT / "configs" / "paper.yaml"))

def run_task4_hybrid_audit(seed=42):
    print("=== TASK 4: FORMALIZE P_HYBRID AND BENIGN VETO AUDIT ===")
    
    # 1. Load data & models
    class_names, benign_idx, X_train_scaled, y_train, X_test_scaled, y_test = load_dataset_references()
    X_test_unscaled = np.load(ROOT / "audit" / "lofo" / "cache" / "X_test.npy", mmap_mode="r")
    xgb_path = ROOT.parent / "backend" / "ml_model" / "saved_models" / "xgboost.pkl"
    if not xgb_path.exists():
        xgb_path = ROOT / "backend" / "ml_model" / "saved_models" / "xgboost.pkl"
    xgb_model = joblib.load(xgb_path)
    if_model, p5, p95 = train_clean_if(X_train_scaled, y_train, benign_idx, seed=seed)
    
    cb = COST_BENIGN_DEFAULT # [0, 1, 3, 15, 50]
    ca = COST_ATTACK_DEFAULT # [0, -5, -10, -20, -50]
    
    # Generate streams: Balanced, Attack-Heavy, Unstratified
    _, _, bal_indices, y_bal_raw = generate_windows(y_test, benign_idx, seed=seed)
    atk_indices, y_atk_raw, _, _ = generate_windows(y_test, benign_idx, seed=seed)
    
    rng = np.random.RandomState(seed)
    unstr_indices = np.copy(bal_indices)
    rng.shuffle(unstr_indices)
    y_unstr_raw = np.array(y_test[unstr_indices])
    
    streams = {
        "balanced": (bal_indices, y_bal_raw),
        "attack-heavy": (atk_indices, y_atk_raw),
        "unstratified": (unstr_indices, y_unstr_raw)
    }
    
    stream_results = []
    
    for s_name, (indices, y_raw) in streams.items():
        y_bin = (y_raw != benign_idx).astype(int)
        tot_benign = np.sum(y_bin == 0)
        tot_attack = np.sum(y_bin == 1)
        
        # Inference time measurement
        t0 = time.perf_counter()
        X_win_scaled = np.array(X_test_scaled[indices], dtype=np.float32)
        raw_anom = -if_model.score_samples(X_win_scaled)
        s_cal = np.clip((raw_anom - p5) / (p95 - p5 + 1e-9) * 0.80 + 0.10, 0.0, 1.0)
        
        X_win_unscaled = np.array(X_test_unscaled[indices], dtype=np.float32)
        probs = xgb_model.predict_proba(X_win_unscaled)
        preds = np.argmax(probs, axis=1)
        confs = np.max(probs, axis=1)
        
        node_risks = np.clip(rng.normal(0.42, 0.08, size=120), 0.10, 0.90)
        R_stream = np.repeat(node_risks[np.arange(600) % 120], 100)
        
        # ADTM trust
        trust = np.zeros(60000, dtype=np.float32)
        T_curr = 100.0
        for b in range(600):
            start = b * 100
            end = start + 100
            for t in range(start, end):
                is_atk_pred = (preds[t] != benign_idx)
                c_t = confs[t]
                anom_t = s_cal[t]
                r_t = R_stream[t]
                
                S_class = 100.0 * (1.0 - (c_t * 0.98 if is_atk_pred else 0.0))
                S_anom = 100.0 * (1.0 - anom_t)
                S_topo = 100.0 * (1.0 - r_t)
                T_obs = 0.40 * S_class + 0.35 * S_anom + 0.15 * S_topo + 0.10 * 100.0
                
                if c_t >= 0.90 and is_atk_pred and anom_t >= 0.50:
                    T_curr = 10.0
                else:
                    T_curr = 0.30 * T_obs + 0.70 * T_curr
                trust[t] = np.clip(T_curr, 0.0, 100.0)
                
        levels = assign_levels(s_cal, confs, preds, R_stream, trust, benign_idx)
        t_pipeline = time.perf_counter() - t0
        per_flow_latency_us = (t_pipeline / 60000.0) * 1e6
        
        # Policy Mappings:
        # P_XGB: Confidence-gated XGBoost (pure microscopic)
        # Block if attack with conf >= 0.90, else Allow
        acts_xgb = np.where((preds != benign_idx) & (confs >= 0.90), 4, 0)
        
        # P2-tier: Allow-Alert-Restrict-Quar-Block-Block [0, 1, 2, 3, 4, 4]
        acts_p2_tier = np.array([[0, 1, 2, 3, 4, 4][lvl] for lvl in levels])
        
        # P_hybrid: P2-tier + Benign Veto inside L4
        # If in L4 and predicted benign with conf >= 0.90, veto to Allow (0)
        acts_hybrid = np.copy(acts_p2_tier)
        # Notice: Uses RUNTIME classifier features ONLY (preds == benign_idx & confs >= 0.90)
        # Zero ground-truth label leakage!
        veto_mask = (levels == 4) & (preds == benign_idx) & (confs >= 0.90)
        acts_hybrid[veto_mask] = 0
        
        # Evaluate each policy
        for p_name, acts in [("P_XGB", acts_xgb), ("P2_tier", acts_p2_tier), ("P_hybrid", acts_hybrid)]:
            b_allow = int(np.sum((acts == 0) & (y_bin == 0)))
            b_alert = int(np.sum((acts == 1) & (y_bin == 0)))
            b_rest = int(np.sum((acts == 2) & (y_bin == 0)))
            b_quar = int(np.sum((acts == 3) & (y_bin == 0)))
            b_blk = int(np.sum((acts == 4) & (y_bin == 0)))
            
            a_allow = int(np.sum((acts == 0) & (y_bin == 1)))
            a_alert = int(np.sum((acts == 1) & (y_bin == 1)))
            a_rest = int(np.sum((acts == 2) & (y_bin == 1)))
            a_quar = int(np.sum((acts == 3) & (y_bin == 1)))
            a_blk = int(np.sum((acts == 4) & (y_bin == 1)))
            
            ben_cost = (b_allow * 0 + b_alert * 1 + b_rest * 3 + b_quar * 15 + b_blk * 50)
            atk_reward = (a_allow * 0 + a_alert * 5 + a_rest * 10 + a_quar * 20 + a_blk * 50)
            net_benefit = atk_reward - ben_cost
            
            blk_fpr = (b_blk / tot_benign * 100.0) if tot_benign > 0 else 0.0
            quar_fpr = (b_quar / tot_benign * 100.0) if tot_benign > 0 else 0.0
            
            # False Negatives: True attacks that escaped containment (assigned Allow or Alert)
            false_negatives = a_allow + a_alert
            
            # Count vetoed flows in P_hybrid
            vetoed_benign = int(np.sum(veto_mask & (y_bin == 0))) if p_name == "P_hybrid" else 0
            vetoed_attack_fn = int(np.sum(veto_mask & (y_bin == 1))) if p_name == "P_hybrid" else 0
            
            stream_results.append({
                "stream": s_name,
                "policy": p_name,
                "net_benefit_ocu": net_benefit,
                "block_fpr_pct": round(blk_fpr, 4),
                "quarantine_fpr_pct": round(quar_fpr, 4),
                "total_disruptive_fpr_pct": round(blk_fpr + quar_fpr, 4),
                "false_negatives_count": false_negatives,
                "vetoed_benign_flows": vetoed_benign,
                "vetoed_attack_false_negatives": vetoed_attack_fn,
                "per_flow_latency_us": round(per_flow_latency_us, 2)
            })
            
    df_res = pd.DataFrame(stream_results)
    out_csv = ROOT / "audit" / "outputs" / "task4_hybrid_audit.csv"
    df_res.to_csv(out_csv, index=False)
    print(f"\nSaved Task 4 Hybrid Audit to {out_csv}")
    print(df_res.to_string(index=False))
    
    # Combined 50/50 net benefit
    print("\n--- Combined Net Benefit (0.5*Balanced + 0.5*Attack-Heavy) ---")
    pols = ["P_XGB", "P_hybrid", "P2_tier"]
    for p in pols:
        b_net = df_res[(df_res["stream"] == "balanced") & (df_res["policy"] == p)]["net_benefit_ocu"].values[0]
        a_net = df_res[(df_res["stream"] == "attack-heavy") & (df_res["policy"] == p)]["net_benefit_ocu"].values[0]
        comb = 0.5 * (b_net + a_net)
        print(f"{p:10s} | Balanced: {b_net:>10,d} | Attack-Heavy: {a_net:>10,d} | Combined: {comb:>12,.1f} OCU")

if __name__ == "__main__":
    run_task4_hybrid_audit()
