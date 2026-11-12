# experiments/E1_multiseed_stability.py
"""
E1: Multi-seed stability evaluation across seeds [13, 42, 99, 123, 2024].
Assesses variance in Clean IF AUC, Trust AUC, posture distributions, and policy net benefits.
"""
import os
import json
import time
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from common import (
    CONFIG, load_dataset_references, train_clean_if, generate_windows,
    compute_signals, assign_levels, evaluate_policy_mapping
)

def run_e1():
    print("=== RUNNING E1: MULTI-SEED STABILITY SUITE ===")
    seeds = CONFIG["seeds"]["multi_seed_suite"]
    class_names, benign_idx, X_train_scaled, y_train, X_test_scaled, y_test = load_dataset_references()
    
    results = []
    
    for seed in seeds:
        t0 = time.time()
        print(f"\n--- Running Seed {seed} ---")
        
        # 1. Train Clean IF
        if_model, p5, p95 = train_clean_if(X_train_scaled, y_train, benign_idx, seed=seed)
        
        # 2. Generate windows
        atk_indices, y_atk_raw, bal_indices, y_bal_raw = generate_windows(y_test, benign_idx, seed=seed)
        y_bin_atk = (y_atk_raw != benign_idx).astype(int)
        y_bin_bal = (y_bal_raw != benign_idx).astype(int)
        
        # 3. Compute signals on balanced window
        s_bal, conf_bal, preds_bal, R_bal, trust_bal = compute_signals(
            X_test_scaled, bal_indices, y_bal_raw, benign_idx, if_model, p5, p95, seed=seed
        )
        # Compute signals on attack window
        s_atk, conf_atk, preds_atk, R_atk, trust_atk = compute_signals(
            X_test_scaled, atk_indices, y_atk_raw, benign_idx, if_model, p5, p95, seed=seed
        )
        
        # 4. AUCs
        if_auc_bal = roc_auc_score(y_bin_bal, s_bal)
        trust_auc_bal = roc_auc_score(y_bin_bal, 100.0 - trust_bal)
        
        # 5. Assign levels
        levels_bal = assign_levels(s_bal, conf_bal, preds_bal, R_bal, trust_bal, benign_idx)
        levels_atk = assign_levels(s_atk, conf_atk, preds_atk, R_atk, trust_atk, benign_idx)
        
        # 6. Evaluate Policies
        # P1: (0, 1, 2, 3, 3, 4)
        p1_res = evaluate_policy_mapping((0, 1, 2, 3, 3, 4), levels_bal, y_bin_bal, levels_atk, y_bin_atk)
        # P2-tier: (0, 1, 2, 3, 4, 4)
        p2_tier_res = evaluate_policy_mapping((0, 1, 2, 3, 4, 4), levels_bal, y_bin_bal, levels_atk, y_bin_atk)
        # P2: (0, 2, 3, 4, 4, 4)
        p2_res = evaluate_policy_mapping((0, 2, 3, 4, 4, 4), levels_bal, y_bin_bal, levels_atk, y_bin_atk)
        
        row = {
            "seed": seed,
            "if_auc": round(if_auc_bal, 4),
            "trust_auc": round(trust_auc_bal, 4),
            "p1_net_bal": p1_res["bal"]["net_benefit"],
            "p1_net_atk": p1_res["atk"]["net_benefit"],
            "p1_comb_net": p1_res["combined_net_benefit"],
            "p1_block_fpr_bal": p1_res["bal"]["block_fpr"],
            "p1_block_fpr_atk": p1_res["atk"]["block_fpr"],
            "p2_tier_net_bal": p2_tier_res["bal"]["net_benefit"],
            "p2_tier_net_atk": p2_tier_res["atk"]["net_benefit"],
            "p2_tier_comb_net": p2_tier_res["combined_net_benefit"],
            "p2_tier_block_fpr_bal": p2_tier_res["bal"]["block_fpr"],
            "p2_tier_block_fpr_atk": p2_tier_res["atk"]["block_fpr"],
            "p2_net_bal": p2_res["bal"]["net_benefit"],
            "p2_net_atk": p2_res["atk"]["net_benefit"],
            "p2_comb_net": p2_res["combined_net_benefit"],
            "p2_block_fpr_bal": p2_res["bal"]["block_fpr"],
            "p2_block_fpr_atk": p2_res["atk"]["block_fpr"],
            "runtime_s": round(time.time() - t0, 2)
        }
        results.append(row)
        print(f"Seed {seed} finished in {row['runtime_s']}s: IF AUC={row['if_auc']}, Trust AUC={row['trust_auc']}, P2-tier Comb Net={row['p2_tier_comb_net']:,}")
        
    df = pd.DataFrame(results)
    out_csv = "experiments/outputs/E1_multiseed_stability.csv"
    df.to_csv(out_csv, index=False)
    print(f"\nSaved E1 results to {out_csv}")
    
    # Compute summary statistics
    numeric_cols = [c for c in df.columns if c not in ["seed"]]
    summary = []
    for col in numeric_cols:
        summary.append({
            "metric": col,
            "mean": df[col].mean(),
            "std": df[col].std(),
            "min": df[col].min(),
            "max": df[col].max()
        })
    df_summary = pd.DataFrame(summary)
    df_summary.to_csv("experiments/outputs/E1_multiseed_summary.csv", index=False)
    print("\n--- E1 Summary Statistics (Mean +- Std) ---")
    print(df_summary.to_string(index=False))

if __name__ == "__main__":
    run_e1()
