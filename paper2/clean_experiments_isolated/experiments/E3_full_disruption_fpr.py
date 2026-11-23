# experiments/E3_full_disruption_fpr.py
"""
E3: Full disruptive FPR audit across all 70 monotonic policies.
Reports Quarantine FPR, Block FPR, and Total Disruptive FPR (Quarantine + Block)
for both Balanced Stratified and Attack-Heavy evaluation regimes.
"""
import os
import json
import pandas as pd
import numpy as np

from common import (
    CONFIG, load_dataset_references, train_clean_if, generate_windows,
    compute_signals, assign_levels, evaluate_policy_mapping, enumerate_all_70_mappings
)

def run_e3():
    print("=== RUNNING E3: FULL DISRUPTIVE FPR AUDIT (ALL 70 POLICIES) ===")
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
    
    all_70 = enumerate_all_70_mappings()
    action_names = ["Allo", "Aler", "Rest", "Quar", "Bloc"]
    
    rows = []
    for pi in all_70:
        res = evaluate_policy_mapping(pi, levels_bal, y_bin_bal, levels_atk, y_bin_atk)
        mapping_str = "-".join([action_names[a] for a in pi])
        
        rows.append({
            "mapping_tuple": str(pi),
            "mapping": mapping_str,
            "comb_net_benefit": res["combined_net_benefit"],
            "bal_net_benefit": res["bal"]["net_benefit"],
            "atk_net_benefit": res["atk"]["net_benefit"],
            "bal_block_fpr": round(res["bal"]["block_fpr"], 2),
            "bal_quar_fpr": round(res["bal"]["quarantine_fpr"], 2),
            "bal_total_disruptive_fpr": round(res["bal"]["disruptive_fpr"], 2),
            "atk_block_fpr": round(res["atk"]["block_fpr"], 2),
            "atk_quar_fpr": round(res["atk"]["quarantine_fpr"], 2),
            "atk_total_disruptive_fpr": round(res["atk"]["disruptive_fpr"], 2)
        })
        
    df = pd.DataFrame(rows)
    df = df.sort_values(by="comb_net_benefit", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    
    out_csv = "experiments/outputs/E3_full_disruption_audit.csv"
    df.to_csv(out_csv, index=False)
    print(f"\nSaved E3 full disruption audit to {out_csv}")
    
    # Highlight P1, P2-tier, P2
    p1 = df[df["mapping"] == "Allo-Aler-Rest-Quar-Quar-Bloc"].iloc[0]
    p2_tier = df[df["mapping"] == "Allo-Aler-Rest-Quar-Bloc-Bloc"].iloc[0]
    p2 = df[df["mapping"] == "Allo-Rest-Quar-Bloc-Bloc-Bloc"].iloc[0]
    
    summary_df = pd.DataFrame([p1, p2_tier, p2])
    print("\n--- Summary of Focal Policies ---")
    print(summary_df[["rank", "mapping", "comb_net_benefit", "bal_block_fpr", "bal_quar_fpr", "bal_total_disruptive_fpr", "atk_block_fpr", "atk_quar_fpr"]].to_string(index=False))

if __name__ == "__main__":
    run_e3()
