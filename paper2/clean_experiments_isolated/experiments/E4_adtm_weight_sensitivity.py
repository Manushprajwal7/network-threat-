# experiments/E4_adtm_weight_sensitivity.py
"""
E4: ADTM component weight sensitivity analysis.
Evaluates trust discrimination (AUC), posture distribution, and policy benefits
under various weight allocations (Class-heavy, Anomaly-heavy, Topo-heavy, Uniform, Extreme).
"""
import os
import json
import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score

from common import (
    CONFIG, load_dataset_references, train_clean_if, generate_windows,
    compute_signals, assign_levels, evaluate_policy_mapping
)

def run_e4():
    print("=== RUNNING E4: ADTM COMPONENT WEIGHT SENSITIVITY ===")
    class_names, benign_idx, X_train_scaled, y_train, X_test_scaled, y_test = load_dataset_references()
    
    if_model, p5, p95 = train_clean_if(X_train_scaled, y_train, benign_idx, seed=42)
    atk_indices, y_atk_raw, bal_indices, y_bal_raw = generate_windows(y_test, benign_idx, seed=42)
    y_bin_atk = (y_atk_raw != benign_idx).astype(int)
    y_bin_bal = (y_bal_raw != benign_idx).astype(int)
    
    weight_configs = [
        {"name": "Baseline (Paper)", "weights": {"w_class": 0.40, "w_anom": 0.35, "w_topo": 0.15, "w_dev": 0.10}},
        {"name": "Class-Heavy", "weights": {"w_class": 0.60, "w_anom": 0.20, "w_topo": 0.10, "w_dev": 0.10}},
        {"name": "Anomaly-Heavy", "weights": {"w_class": 0.20, "w_anom": 0.60, "w_topo": 0.10, "w_dev": 0.10}},
        {"name": "Topo-Heavy", "weights": {"w_class": 0.25, "w_anom": 0.25, "w_topo": 0.40, "w_dev": 0.10}},
        {"name": "Uniform", "weights": {"w_class": 0.25, "w_anom": 0.25, "w_topo": 0.25, "w_dev": 0.25}},
        {"name": "Extreme-Class", "weights": {"w_class": 0.70, "w_anom": 0.10, "w_topo": 0.10, "w_dev": 0.10}},
        {"name": "Extreme-Anomaly", "weights": {"w_class": 0.10, "w_anom": 0.70, "w_topo": 0.10, "w_dev": 0.10}},
    ]
    
    results = []
    for cfg in weight_configs:
        w = cfg["weights"]
        s_bal, conf_bal, preds_bal, R_bal, trust_bal = compute_signals(
            X_test_scaled, bal_indices, y_bal_raw, benign_idx, if_model, p5, p95, seed=42,
            custom_weights=w
        )
        s_atk, conf_atk, preds_atk, R_atk, trust_atk = compute_signals(
            X_test_scaled, atk_indices, y_atk_raw, benign_idx, if_model, p5, p95, seed=42,
            custom_weights=w
        )
        
        trust_auc = roc_auc_score(y_bin_bal, 100.0 - trust_bal)
        levels_bal = assign_levels(s_bal, conf_bal, preds_bal, R_bal, trust_bal, benign_idx)
        levels_atk = assign_levels(s_atk, conf_atk, preds_atk, R_atk, trust_atk, benign_idx)
        
        p1_res = evaluate_policy_mapping((0, 1, 2, 3, 3, 4), levels_bal, y_bin_bal, levels_atk, y_bin_atk)
        p2_tier_res = evaluate_policy_mapping((0, 1, 2, 3, 4, 4), levels_bal, y_bin_bal, levels_atk, y_bin_atk)
        
        results.append({
            "Configuration": cfg["name"],
            "w_class": w["w_class"],
            "w_anom": w["w_anom"],
            "w_topo": w["w_topo"],
            "w_dev": w["w_dev"],
            "Trust AUC": round(trust_auc, 4),
            "P1 Comb Net (OCU)": p1_res["combined_net_benefit"],
            "P2-tier Comb Net (OCU)": p2_tier_res["combined_net_benefit"],
            "P2-tier Bal Block FPR (%)": p2_tier_res["bal"]["block_fpr"],
            "P2-tier Atk Block FPR (%)": p2_tier_res["atk"]["block_fpr"],
        })
        
    df = pd.DataFrame(results)
    out_csv = "experiments/outputs/E4_adtm_weight_sensitivity.csv"
    df.to_csv(out_csv, index=False)
    print(f"\nSaved E4 results to {out_csv}")
    print(df.to_string(index=False))

if __name__ == "__main__":
    run_e4()
