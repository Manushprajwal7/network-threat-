# experiments/E5_threshold_sensitivity.py
"""
E5: Posture threshold sensitivity analysis.
Sweeps tau_anom, tau_T, tau_conf, and tau_topo around their baseline values
to verify posture stability, level monotonicity, and policy robustness.
"""
import os
import json
import pandas as pd
import numpy as np

from common import (
    CONFIG, load_dataset_references, train_clean_if, generate_windows,
    compute_signals, assign_levels, evaluate_policy_mapping
)

def run_e5():
    print("=== RUNNING E5: POSTURE THRESHOLD SENSITIVITY ===")
    class_names, benign_idx, X_train_scaled, y_train, X_test_scaled, y_test = load_dataset_references()
    
    if_model, p5, p95 = train_clean_if(X_train_scaled, y_train, benign_idx, seed=42)
    atk_indices, y_atk_raw, bal_indices, y_bal_raw = generate_windows(y_test, benign_idx, seed=42)
    y_bin_atk = (y_atk_raw != benign_idx).astype(int)
    y_bin_bal = (y_bal_raw != benign_idx).astype(int)
    
    s_bal, conf_bal, preds_bal, R_bal, trust_bal = compute_signals(
        X_test_scaled, bal_indices, y_bal_raw, benign_idx, if_model, p5, p95, seed=42
    )
    s_atk, conf_atk, preds_atk, R_atk, trust_atk = compute_signals(
        X_test_scaled, atk_indices, y_atk_raw, benign_idx, if_model, p5, p95, seed=42
    )
    
    tau_anom_list = [0.40, 0.45, 0.50, 0.55, 0.60]
    tau_t_list = [50.0, 55.0, 60.0, 65.0, 70.0]
    tau_conf_list = [0.85, 0.90, 0.95]
    tau_topo_list = [0.35, 0.42, 0.50]
    
    results = []
    
    # 1. Sweep Anomaly Threshold (others default)
    for ta in tau_anom_list:
        th = {"tau_anom": ta, "tau_conf": 0.90, "tau_T": 60.0, "tau_topo": 0.42}
        lvl_bal = assign_levels(s_bal, conf_bal, preds_bal, R_bal, trust_bal, benign_idx, custom_thresholds=th)
        lvl_atk = assign_levels(s_atk, conf_atk, preds_atk, R_atk, trust_atk, benign_idx, custom_thresholds=th)
        p2_tier = evaluate_policy_mapping((0, 1, 2, 3, 4, 4), lvl_bal, y_bin_bal, lvl_atk, y_bin_atk)
        results.append({
            "Parameter Swept": "tau_anom",
            "Value": ta,
            "L4 Batches Bal": int(np.sum(lvl_bal == 4) // 100),
            "L4 Batches Atk": int(np.sum(lvl_atk == 4) // 100),
            "P2-tier Comb Net (OCU)": p2_tier["combined_net_benefit"],
            "Bal Block FPR (%)": p2_tier["bal"]["block_fpr"]
        })
        
    # 2. Sweep Trust Threshold (others default)
    for tt in tau_t_list:
        th = {"tau_anom": 0.50, "tau_conf": 0.90, "tau_T": tt, "tau_topo": 0.42}
        lvl_bal = assign_levels(s_bal, conf_bal, preds_bal, R_bal, trust_bal, benign_idx, custom_thresholds=th)
        lvl_atk = assign_levels(s_atk, conf_atk, preds_atk, R_atk, trust_atk, benign_idx, custom_thresholds=th)
        p2_tier = evaluate_policy_mapping((0, 1, 2, 3, 4, 4), lvl_bal, y_bin_bal, lvl_atk, y_bin_atk)
        results.append({
            "Parameter Swept": "tau_T",
            "Value": tt,
            "L4 Batches Bal": int(np.sum(lvl_bal == 4) // 100),
            "L4 Batches Atk": int(np.sum(lvl_atk == 4) // 100),
            "P2-tier Comb Net (OCU)": p2_tier["combined_net_benefit"],
            "Bal Block FPR (%)": p2_tier["bal"]["block_fpr"]
        })
        
    # 3. Sweep Conf Threshold (others default)
    for tc in tau_conf_list:
        th = {"tau_anom": 0.50, "tau_conf": tc, "tau_T": 60.0, "tau_topo": 0.42}
        lvl_bal = assign_levels(s_bal, conf_bal, preds_bal, R_bal, trust_bal, benign_idx, custom_thresholds=th)
        lvl_atk = assign_levels(s_atk, conf_atk, preds_atk, R_atk, trust_atk, benign_idx, custom_thresholds=th)
        p2_tier = evaluate_policy_mapping((0, 1, 2, 3, 4, 4), lvl_bal, y_bin_bal, lvl_atk, y_bin_atk)
        results.append({
            "Parameter Swept": "tau_conf",
            "Value": tc,
            "L4 Batches Bal": int(np.sum(lvl_bal == 4) // 100),
            "L4 Batches Atk": int(np.sum(lvl_atk == 4) // 100),
            "P2-tier Comb Net (OCU)": p2_tier["combined_net_benefit"],
            "Bal Block FPR (%)": p2_tier["bal"]["block_fpr"]
        })
        
    # 4. Sweep Topo Threshold (others default)
    for tr in tau_topo_list:
        th = {"tau_anom": 0.50, "tau_conf": 0.90, "tau_T": 60.0, "tau_topo": tr}
        lvl_bal = assign_levels(s_bal, conf_bal, preds_bal, R_bal, trust_bal, benign_idx, custom_thresholds=th)
        lvl_atk = assign_levels(s_atk, conf_atk, preds_atk, R_atk, trust_atk, benign_idx, custom_thresholds=th)
        p2_tier = evaluate_policy_mapping((0, 1, 2, 3, 4, 4), lvl_bal, y_bin_bal, lvl_atk, y_bin_atk)
        results.append({
            "Parameter Swept": "tau_topo",
            "Value": tr,
            "L4 Batches Bal": int(np.sum(lvl_bal == 4) // 100),
            "L4 Batches Atk": int(np.sum(lvl_atk == 4) // 100),
            "P2-tier Comb Net (OCU)": p2_tier["combined_net_benefit"],
            "Bal Block FPR (%)": p2_tier["bal"]["block_fpr"]
        })
        
    df = pd.DataFrame(results)
    out_csv = "experiments/outputs/E5_threshold_sensitivity.csv"
    df.to_csv(out_csv, index=False)
    print(f"\nSaved E5 results to {out_csv}")
    print(df.to_string(index=False))

if __name__ == "__main__":
    run_e5()
