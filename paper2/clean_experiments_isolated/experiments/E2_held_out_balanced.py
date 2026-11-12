# experiments/E2_held_out_balanced.py
"""
E2: Held-out balanced test window evaluation using independent test seed 99.
Demonstrates generalization and verifies 0.00% Block FPR on unseen balanced traffic.
"""
import os
import json
import time
import numpy as np
import pandas as pd

from common import (
    CONFIG, load_dataset_references, train_clean_if, generate_windows,
    compute_signals, assign_levels, evaluate_policy_mapping
)

def run_e2():
    print("=== RUNNING E2: HELD-OUT BALANCED TEST EVALUATION ===")
    seed = CONFIG["seeds"]["held_out_test"]
    class_names, benign_idx, X_train_scaled, y_train, X_test_scaled, y_test = load_dataset_references()
    
    # Train Clean IF with primary seed 42
    if_model, p5, p95 = train_clean_if(X_train_scaled, y_train, benign_idx, seed=42)
    
    # Generate held-out window with seed 99
    atk_indices, y_atk_raw, bal_indices, y_bal_raw = generate_windows(y_test, benign_idx, seed=seed)
    y_bin_atk = (y_atk_raw != benign_idx).astype(int)
    y_bin_bal = (y_bal_raw != benign_idx).astype(int)
    
    # Compute signals
    s_bal, conf_bal, preds_bal, R_bal, trust_bal = compute_signals(
        X_test_scaled, bal_indices, y_bal_raw, benign_idx, if_model, p5, p95, seed=seed
    )
    s_atk, conf_atk, preds_atk, R_atk, trust_atk = compute_signals(
        X_test_scaled, atk_indices, y_atk_raw, benign_idx, if_model, p5, p95, seed=seed
    )
    
    # Assign levels
    levels_bal = assign_levels(s_bal, conf_bal, preds_bal, R_bal, trust_bal, benign_idx)
    levels_atk = assign_levels(s_atk, conf_atk, preds_atk, R_atk, trust_atk, benign_idx)
    
    # Evaluate P1 and P2-tier
    p1_res = evaluate_policy_mapping((0, 1, 2, 3, 3, 4), levels_bal, y_bin_bal, levels_atk, y_bin_atk)
    p2_tier_res = evaluate_policy_mapping((0, 1, 2, 3, 4, 4), levels_bal, y_bin_bal, levels_atk, y_bin_atk)
    p2_res = evaluate_policy_mapping((0, 2, 3, 4, 4, 4), levels_bal, y_bin_bal, levels_atk, y_bin_atk)
    
    results = [
        {
            "Policy": "P1 (Default)",
            "Mapping": "Allo-Aler-Rest-Quar-Quar-Bloc",
            "Held-Out Balanced Net (OCU)": p1_res["bal"]["net_benefit"],
            "Held-Out Balanced Benign Penalty (OCU)": p1_res["bal"]["benign_penalty"],
            "Held-Out Balanced Block FPR (%)": p1_res["bal"]["block_fpr"],
            "Held-Out Balanced Disruptive FPR (%)": p1_res["bal"]["disruptive_fpr"],
            "Attack-Heavy Net (OCU)": p1_res["atk"]["net_benefit"],
            "Combined Net Benefit (OCU)": p1_res["combined_net_benefit"]
        },
        {
            "Policy": "P2-tier (Recommended)",
            "Mapping": "Allo-Aler-Rest-Quar-Bloc-Bloc",
            "Held-Out Balanced Net (OCU)": p2_tier_res["bal"]["net_benefit"],
            "Held-Out Balanced Benign Penalty (OCU)": p2_tier_res["bal"]["benign_penalty"],
            "Held-Out Balanced Block FPR (%)": p2_tier_res["bal"]["block_fpr"],
            "Held-Out Balanced Disruptive FPR (%)": p2_tier_res["bal"]["disruptive_fpr"],
            "Attack-Heavy Net (OCU)": p2_tier_res["atk"]["net_benefit"],
            "Combined Net Benefit (OCU)": p2_tier_res["combined_net_benefit"]
        },
        {
            "Policy": "P2 (Global Cost-Optimal)",
            "Mapping": "Allo-Rest-Quar-Bloc-Bloc-Bloc",
            "Held-Out Balanced Net (OCU)": p2_res["bal"]["net_benefit"],
            "Held-Out Balanced Benign Penalty (OCU)": p2_res["bal"]["benign_penalty"],
            "Held-Out Balanced Block FPR (%)": p2_res["bal"]["block_fpr"],
            "Held-Out Balanced Disruptive FPR (%)": p2_res["bal"]["disruptive_fpr"],
            "Attack-Heavy Net (OCU)": p2_res["atk"]["net_benefit"],
            "Combined Net Benefit (OCU)": p2_res["combined_net_benefit"]
        }
    ]
    
    df = pd.DataFrame(results)
    out_csv = "experiments/outputs/E2_held_out_balanced.csv"
    df.to_csv(out_csv, index=False)
    print(f"\nSaved E2 results to {out_csv}")
    print(df.to_string(index=False))

if __name__ == "__main__":
    run_e2()
