# experiments/E6_extended_cost_sensitivity.py
"""
E6: Extended cost sensitivity analysis.
Sweeps benign penalties and containment rewards over wide scaling ranges [0.2x, 10.0x].
Identifies exact mathematical boundaries where policy preferences shift.
"""
import os
import json
import pandas as pd
import numpy as np

from common import (
    CONFIG, load_dataset_references, train_clean_if, generate_windows,
    compute_signals, assign_levels, evaluate_policy_mapping
)

def run_e6():
    print("=== RUNNING E6: EXTENDED COST SENSITIVITY SWEEP ===")
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
    
    # 1. Block Penalty Multiplier sweep
    lambda_block_vals = [0.2, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 8.0, 10.0, 15.0, 20.0]
    results_block = []
    for lam in lambda_block_vals:
        cb = [0, 1, 3, 15, int(round(50 * lam))]
        ca = [0, -5, -10, -20, -50]
        
        p1 = evaluate_policy_mapping((0, 1, 2, 3, 3, 4), levels_bal, y_bin_bal, levels_atk, y_bin_atk, cost_benign=cb, cost_attack=ca)
        p2_tier = evaluate_policy_mapping((0, 1, 2, 3, 4, 4), levels_bal, y_bin_bal, levels_atk, y_bin_atk, cost_benign=cb, cost_attack=ca)
        p2 = evaluate_policy_mapping((0, 2, 3, 4, 4, 4), levels_bal, y_bin_bal, levels_atk, y_bin_atk, cost_benign=cb, cost_attack=ca)
        
        results_block.append({
            "Lambda_Block": lam,
            "Block Penalty (OCU)": cb[4],
            "P1 Comb Net (OCU)": p1["combined_net_benefit"],
            "P2-tier Comb Net (OCU)": p2_tier["combined_net_benefit"],
            "P2 Comb Net (OCU)": p2["combined_net_benefit"],
            "P2-tier Advantage vs P1": round(p2_tier["combined_net_benefit"] / (p1["combined_net_benefit"] + 1e-9), 2),
            "Winner": "P2-tier" if p2_tier["combined_net_benefit"] >= p1["combined_net_benefit"] else "P1"
        })
        
    df_block = pd.DataFrame(results_block)
    out_csv = "experiments/outputs/E6_extended_cost_sensitivity.csv"
    df_block.to_csv(out_csv, index=False)
    print(f"\nSaved E6 results to {out_csv}")
    print(df_block.to_string(index=False))

if __name__ == "__main__":
    run_e6()
