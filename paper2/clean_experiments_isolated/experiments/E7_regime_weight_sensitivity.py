# experiments/E7_regime_weight_sensitivity.py
"""
E7: Evaluation regime mixture weight sensitivity.
Sweeps the relative weight of the Balanced vs Attack-Heavy windows (w_bal in [0.0, 1.0])
to evaluate how operational threat posture affects policy selection.
"""
import os
import json
import pandas as pd
import numpy as np

from common import (
    CONFIG, load_dataset_references, train_clean_if, generate_windows,
    compute_signals, assign_levels, evaluate_policy_mapping, enumerate_all_70_mappings
)

def run_e7():
    print("=== RUNNING E7: REGIME MIXTURE WEIGHT SENSITIVITY ===")
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
    
    levels_bal = assign_levels(s_bal, conf_bal, preds_bal, R_bal, trust_bal, benign_idx)
    levels_atk = assign_levels(s_atk, conf_atk, preds_atk, R_atk, trust_atk, benign_idx)
    
    weights = [
        (1.0, 0.0), (0.9, 0.1), (0.8, 0.2), (0.7, 0.3), (0.5, 0.5),
        (0.3, 0.7), (0.2, 0.8), (0.1, 0.9), (0.0, 1.0)
    ]
    
    all_70 = enumerate_all_70_mappings()
    
    results = []
    for w_bal, w_atk in weights:
        # Evaluate all 70 under this weighting to get rank
        sweep_scores = []
        for pi in all_70:
            res = evaluate_policy_mapping(pi, levels_bal, y_bin_bal, levels_atk, y_bin_atk, w_bal=w_bal, w_atk=w_atk)
            sweep_scores.append((pi, res["combined_net_benefit"]))
            
        sweep_scores.sort(key=lambda x: x[1], reverse=True)
        ranks = {item[0]: idx + 1 for idx, item in enumerate(sweep_scores)}
        
        p1_res = evaluate_policy_mapping((0, 1, 2, 3, 3, 4), levels_bal, y_bin_bal, levels_atk, y_bin_atk, w_bal=w_bal, w_atk=w_atk)
        p2_tier_res = evaluate_policy_mapping((0, 1, 2, 3, 4, 4), levels_bal, y_bin_bal, levels_atk, y_bin_atk, w_bal=w_bal, w_atk=w_atk)
        p2_res = evaluate_policy_mapping((0, 2, 3, 4, 4, 4), levels_bal, y_bin_bal, levels_atk, y_bin_atk, w_bal=w_bal, w_atk=w_atk)
        
        results.append({
            "w_bal": w_bal,
            "w_atk": w_atk,
            "P1 Net (OCU)": int(round(p1_res["combined_net_benefit"])),
            "P1 Rank": ranks[(0, 1, 2, 3, 3, 4)],
            "P2-tier Net (OCU)": int(round(p2_tier_res["combined_net_benefit"])),
            "P2-tier Rank": ranks[(0, 1, 2, 3, 4, 4)],
            "P2 Net (OCU)": int(round(p2_res["combined_net_benefit"])),
            "P2 Rank": ranks[(0, 2, 3, 4, 4, 4)],
        })
        
    df = pd.DataFrame(results)
    out_csv = "experiments/outputs/E7_regime_weight_sensitivity.csv"
    df.to_csv(out_csv, index=False)
    print(f"\nSaved E7 results to {out_csv}")
    print(df.to_string(index=False))

if __name__ == "__main__":
    run_e7()
