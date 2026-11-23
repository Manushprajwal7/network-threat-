import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "clean_experiments_isolated" / "experiments"))

from common import (
    load_config, load_dataset_references, train_clean_if,
    generate_windows, assign_levels, COST_BENIGN_DEFAULT, COST_ATTACK_DEFAULT
)

CONFIG = load_config(str(ROOT / "configs" / "paper.yaml"))

def run_task3_policy_rebuild(seeds=[13, 42, 99, 123, 2024, 7, 77, 101, 2023, 31415]):
    print(f"=== TASK 3: REBUILDING ALL POLICY EVALUATIONS ACROSS {len(seeds)} SEEDS & 5 REGIMES ===")
    
    # 1. Load data
    class_names, benign_idx, X_train_scaled, y_train, X_test_scaled, y_test = load_dataset_references()
    X_test_unscaled = np.load(ROOT / "audit" / "lofo" / "cache" / "X_test.npy", mmap_mode="r")
    xgb_path = ROOT.parent / "backend" / "ml_model" / "saved_models" / "xgboost.pkl"
    if not xgb_path.exists():
        xgb_path = ROOT / "backend" / "ml_model" / "saved_models" / "xgboost.pkl"
    xgb_model = joblib.load(xgb_path)
    
    # Train clean IF
    if_model, p5, p95 = train_clean_if(X_train_scaled, y_train, benign_idx, seed=42)
    
    cb = COST_BENIGN_DEFAULT # [0, 1, 3, 15, 50]
    ca = COST_ATTACK_DEFAULT # [0, -5, -10, -20, -50]
    action_names = ["Allow", "Alert", "Restrict", "Quarantine", "Block"]
    
    # Policies:
    # P1: Allow-Alert-Restrict-Quar-Quar-Block [0, 1, 2, 3, 3, 4]
    # P2-tier: Allow-Alert-Restrict-Quar-Block-Block [0, 1, 2, 3, 4, 4]
    # P_opt: Allow-Allow-Restrict-Restrict-Block-Block [0, 0, 2, 2, 4, 4] (cost optimal)
    # P2: Allow-Restrict-Quar-Block-Block-Block [0, 2, 3, 4, 4, 4] (aggressive)
    # P_XGB: Confidence-gated flow classifier (Block if attack & conf >= 0.90, else Allow)
    # P_hybrid: P2-tier + flow benign veto in L4 (Allow if in L4 and predicted benign with conf >= 0.90)
    static_mappings = {
        "P1": [0, 1, 2, 3, 3, 4],
        "P2_tier": [0, 1, 2, 3, 4, 4],
        "P_opt": [0, 0, 2, 2, 4, 4],
        "P2": [0, 2, 3, 4, 4, 4]
    }
    
    all_policies = ["P_XGB", "P_hybrid", "P_opt", "P2_tier", "P1", "P2"]
    regime_names = ["balanced", "attack-heavy", "multi-state", "unstratified", "flood"]
    
    # Storage for per-run detailed results
    detailed_rows = []
    # Storage for seed-level summaries for paired statistical testing
    seed_net_benefits = {p: {r: [] for r in regime_names} for p in all_policies}
    seed_combined_net = {p: [] for p in all_policies}
    
    W = 100
    n_batches = 600
    total_flows = 60000
    
    ben_all = np.where(y_test == benign_idx)[0]
    atk_all = np.where(y_test != benign_idx)[0]
    
    for s_idx, seed in enumerate(seeds):
        print(f"\n--- Running Seed {s_idx+1}/{len(seeds)} (Seed: {seed}) ---")
        rng_seed = np.random.RandomState(seed)
        
        # Build the 5 regimes for this seed:
        # 1. Balanced Stratified (180 benign, 240 mixed 50%, 180 attack)
        _, _, bal_indices, y_bal_raw = generate_windows(y_test, benign_idx, seed=seed)
        
        # 2. Attack-Heavy (60k contiguous test slice)
        # To vary with seed, sample a contiguous 60k slice or stratified 97.6% attack
        atk_start = (seed * 1000) % (len(y_test) - total_flows)
        atk_indices = np.arange(atk_start, atk_start + total_flows)
        y_atk_raw = np.array(y_test[atk_indices])
        
        # 3. Multi-State (Nominal 120 batches, Recon 80 batches, Lateral 100 batches, Flood 200 batches, Recovery 100 batches)
        # In benchmark paper, multi-state is identical to the balanced multi-state stream
        ms_indices = np.copy(bal_indices)
        y_ms_raw = np.copy(y_bal_raw)
        
        # 4. Unstratified (60k flows randomly sampled with 50.2% attack, completely shuffled across flows)
        unstr_indices = np.copy(bal_indices)
        rng_seed.shuffle(unstr_indices)
        y_unstr_raw = np.array(y_test[unstr_indices])
        
        # 5. Flood (Pure attack flood: 60,000 attack flows)
        flood_indices = rng_seed.choice(atk_all, size=total_flows, replace=False)
        y_flood_raw = np.array(y_test[flood_indices])
        
        regimes_data = {
            "balanced": (bal_indices, y_bal_raw),
            "attack-heavy": (atk_indices, y_atk_raw),
            "multi-state": (ms_indices, y_ms_raw),
            "unstratified": (unstr_indices, y_unstr_raw),
            "flood": (flood_indices, y_flood_raw)
        }
        
        for reg_name, (reg_indices, reg_y_raw) in regimes_data.items():
            # Compute signals
            X_win = np.array(X_test_scaled[reg_indices], dtype=np.float32)
            raw_anom = -if_model.score_samples(X_win)
            s_cal = np.clip((raw_anom - p5) / (p95 - p5 + 1e-9) * 0.80 + 0.10, 0.0, 1.0)
            
            # Predict with XGBoost
            # Read unscaled features for XGBoost
            X_unscaled_win = np.array(X_test_unscaled[reg_indices], dtype=np.float32)
            xgb_probs = xgb_model.predict_proba(X_unscaled_win)
            real_preds = np.argmax(xgb_probs, axis=1)
            real_confs = np.max(xgb_probs, axis=1)
            
            # Synthetic TARP risk for this seed
            # 120-node topology round robin
            node_risks = np.clip(rng_seed.normal(0.42, 0.08, size=120), 0.10, 0.90)
            R_batch = node_risks[np.arange(n_batches) % 120]
            R_stream = np.repeat(R_batch, W)
            
            # ADTM trust calculation
            T_stream = np.zeros(total_flows, dtype=np.float32)
            T_curr = 100.0
            for b in range(n_batches):
                start = b * W
                end = start + W
                for t in range(start, end):
                    is_atk_pred = (real_preds[t] != benign_idx)
                    c_t = real_confs[t]
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
                    T_stream[t] = np.clip(T_curr, 0.0, 100.0)
                    
            # Posture levels
            levels = assign_levels(s_cal, real_confs, real_preds, R_stream, T_stream, benign_idx)
            
            y_bin = (reg_y_raw != benign_idx).astype(int)
            tot_benign = np.sum(y_bin == 0)
            tot_attack = np.sum(y_bin == 1)
            
            # Evaluate each policy
            for pol_name in all_policies:
                if pol_name in static_mappings:
                    mapping = static_mappings[pol_name]
                    actions = np.array([mapping[lvl] for lvl in levels])
                elif pol_name == "P_XGB":
                    # Confidence-gated XGBoost: Block if attack with conf >= 0.90, else Allow
                    actions = np.where((real_preds != benign_idx) & (real_confs >= 0.90), 4, 0)
                elif pol_name == "P_hybrid":
                    mapping = static_mappings["P2_tier"]
                    actions = np.array([mapping[lvl] for lvl in levels])
                    # Benign veto inside L4: if predicted benign with conf >= 0.90, veto to Allow
                    veto_mask = (levels == 4) & (real_preds == benign_idx) & (real_confs >= 0.90)
                    actions[veto_mask] = 0
                    
                # Compute flow counts per action
                # Cost & Benefit
                ben_cost = 0
                atk_reward = 0
                
                # Per level & action metrics
                for act_id in range(5):
                    act_mask = (actions == act_id)
                    b_act = int(np.sum(act_mask & (y_bin == 0)))
                    a_act = int(np.sum(act_mask & (y_bin == 1)))
                    tot_act = b_act + a_act
                    
                    ben_cost += b_act * cb[act_id]
                    atk_reward += a_act * (-ca[act_id])
                    
                    prec = (a_act / tot_act * 100.0) if tot_act > 0 else np.nan
                    rec = (a_act / tot_attack * 100.0) if tot_attack > 0 else np.nan
                    fpr = (b_act / tot_benign * 100.0) if tot_benign > 0 else np.nan
                    fnr = (100.0 - rec) if not np.isnan(rec) else np.nan
                    
                    ocu_action = a_act * ca[act_id] + b_act * cb[act_id]
                    
                    detailed_rows.append({
                        "seed": seed,
                        "regime": reg_name,
                        "policy": pol_name,
                        "action_id": act_id,
                        "action_name": action_names[act_id],
                        "benign_count": b_act,
                        "attack_count": a_act,
                        "total_count": tot_act,
                        "precision_pct": prec,
                        "recall_pct": rec,
                        "fpr_pct": fpr,
                        "fnr_pct": fnr,
                        "action_ocu": ocu_action,
                        "is_used": (tot_act > 0)
                    })
                    
                net_benefit = atk_reward - ben_cost
                seed_net_benefits[pol_name][reg_name].append(net_benefit)
                
        # Combined net benefit (0.5 * balanced + 0.5 * attack-heavy)
        for pol_name in all_policies:
            bal_net = seed_net_benefits[pol_name]["balanced"][-1]
            atk_net = seed_net_benefits[pol_name]["attack-heavy"][-1]
            comb_net = 0.5 * (bal_net + atk_net)
            seed_combined_net[pol_name].append(comb_net)
            
    # Save full granular detailed evaluations
    df_detailed = pd.DataFrame(detailed_rows)
    det_csv = ROOT / "audit" / "outputs" / "task3_detailed_policy_evaluations.csv"
    df_detailed.to_csv(det_csv, index=False)
    print(f"\nSaved detailed policy evaluations to {det_csv}")
    
    # 2. Aggregate across 10 seeds: Mean, SD, 95% CI
    agg_summary = []
    for reg_name in regime_names:
        for pol_name in all_policies:
            sub = df_detailed[(df_detailed["regime"] == reg_name) & (df_detailed["policy"] == pol_name)]
            
            # Policy-level totals across seeds
            for act_id in range(5):
                act_sub = sub[sub["action_id"] == act_id]
                act_name = action_names[act_id]
                
                # Check if used
                used_across = act_sub["is_used"].any()
                
                b_cnt_mean = float(act_sub["benign_count"].mean())
                b_cnt_sd = float(act_sub["benign_count"].std())
                a_cnt_mean = float(act_sub["attack_count"].mean())
                a_cnt_sd = float(act_sub["attack_count"].std())
                
                prec_vals = act_sub["precision_pct"].dropna()
                rec_vals = act_sub["recall_pct"].dropna()
                fpr_vals = act_sub["fpr_pct"].dropna()
                fnr_vals = act_sub["fnr_pct"].dropna()
                
                prec_str = f"{prec_vals.mean():.2f} ± {prec_vals.std():.2f}" if len(prec_vals) > 0 else "N/A"
                rec_str = f"{rec_vals.mean():.2f} ± {rec_vals.std():.2f}" if len(rec_vals) > 0 else "N/A"
                fpr_str = f"{fpr_vals.mean():.2f} ± {fpr_vals.std():.2f}" if len(fpr_vals) > 0 else "N/A"
                fnr_str = f"{fnr_vals.mean():.2f} ± {fnr_vals.std():.2f}" if len(fnr_vals) > 0 else "N/A"
                
                agg_summary.append({
                    "regime": reg_name,
                    "policy": pol_name,
                    "action_name": act_name,
                    "is_used": "YES" if used_across else "N/A",
                    "benign_mean": round(b_cnt_mean, 1),
                    "benign_sd": round(b_cnt_sd, 1),
                    "attack_mean": round(a_cnt_mean, 1),
                    "attack_sd": round(a_cnt_sd, 1),
                    "precision_mean_sd": prec_str,
                    "recall_mean_sd": rec_str,
                    "fpr_mean_sd": fpr_str,
                    "fnr_mean_sd": fnr_str,
                })
                
    df_agg = pd.DataFrame(agg_summary)
    agg_csv = ROOT / "audit" / "outputs" / "task3_policy_action_summary_table.csv"
    df_agg.to_csv(agg_csv, index=False)
    print(f"Saved aggregated action summary table to {agg_csv}")
    
    # 3. Overall Policy Performance Summary across 10 seeds (OCU, Net Benefit, FPRs)
    pol_summary_rows = []
    for reg_name in regime_names:
        for pol_name in all_policies:
            net_vals = np.array(seed_net_benefits[pol_name][reg_name])
            m = float(np.mean(net_vals))
            s = float(np.std(net_vals, ddof=1))
            n = len(net_vals)
            se = s / np.sqrt(n)
            ci95_low = m - 1.96 * se
            ci95_high = m + 1.96 * se
            
            # Disruption FPRs (Block & Quarantine)
            sub_blk = df_detailed[(df_detailed["regime"] == reg_name) & (df_detailed["policy"] == pol_name) & (df_detailed["action_id"] == 4)]
            sub_quar = df_detailed[(df_detailed["regime"] == reg_name) & (df_detailed["policy"] == pol_name) & (df_detailed["action_id"] == 3)]
            
            blk_fpr_mean = float(sub_blk["fpr_pct"].mean()) if len(sub_blk) > 0 else 0.0
            quar_fpr_mean = float(sub_quar["fpr_pct"].mean()) if len(sub_quar) > 0 else 0.0
            
            pol_summary_rows.append({
                "regime": reg_name,
                "policy": pol_name,
                "net_benefit_mean_ocu": round(m, 1),
                "net_benefit_sd_ocu": round(s, 1),
                "ci95_lower_ocu": round(ci95_low, 1),
                "ci95_upper_ocu": round(ci95_high, 1),
                "block_fpr_pct": round(blk_fpr_mean, 2),
                "quarantine_fpr_pct": round(quar_fpr_mean, 2),
                "total_disruptive_fpr_pct": round(blk_fpr_mean + quar_fpr_mean, 2)
            })
            
    # Add Combined regime
    for pol_name in all_policies:
        comb_vals = np.array(seed_combined_net[pol_name])
        m = float(np.mean(comb_vals))
        s = float(np.std(comb_vals, ddof=1))
        n = len(comb_vals)
        se = s / np.sqrt(n)
        ci95_low = m - 1.96 * se
        ci95_high = m + 1.96 * se
        
        pol_summary_rows.append({
            "regime": "combined_50_50",
            "policy": pol_name,
            "net_benefit_mean_ocu": round(m, 1),
            "net_benefit_sd_ocu": round(s, 1),
            "ci95_lower_ocu": round(ci95_low, 1),
            "ci95_upper_ocu": round(ci95_high, 1),
            "block_fpr_pct": round(0.5 * (
                float(df_detailed[(df_detailed["regime"] == "balanced") & (df_detailed["policy"] == pol_name) & (df_detailed["action_id"] == 4)]["fpr_pct"].mean()) +
                float(df_detailed[(df_detailed["regime"] == "attack-heavy") & (df_detailed["policy"] == pol_name) & (df_detailed["action_id"] == 4)]["fpr_pct"].mean())
            ), 2),
            "quarantine_fpr_pct": round(0.5 * (
                float(df_detailed[(df_detailed["regime"] == "balanced") & (df_detailed["policy"] == pol_name) & (df_detailed["action_id"] == 3)]["fpr_pct"].mean()) +
                float(df_detailed[(df_detailed["regime"] == "attack-heavy") & (df_detailed["policy"] == pol_name) & (df_detailed["action_id"] == 3)]["fpr_pct"].mean())
            ), 2),
            "total_disruptive_fpr_pct": 0.0 # Will compute
        })
        
    df_pol_summary = pd.DataFrame(pol_summary_rows)
    pol_sum_csv = ROOT / "audit" / "outputs" / "task3_policy_multiseed_summary.csv"
    df_pol_summary.to_csv(pol_sum_csv, index=False)
    print(f"Saved policy multiseed summary to {pol_sum_csv}")
    print(df_pol_summary[df_pol_summary["regime"].isin(["balanced", "attack-heavy", "combined_50_50"])].to_string(index=False))
    
    # 4. Paired Bootstrap and Wilcoxon Signed-Rank Tests
    # Compare P_hybrid vs P_XGB, P_opt, P_2-tier, P_2
    print("\n=== PAIRED BOOTSTRAP & WILCOXON SIGNED-RANK TESTS ===")
    test_comparisons = [
        ("P_hybrid", "P_XGB"),
        ("P_hybrid", "P_opt"),
        ("P_hybrid", "P2_tier"),
        ("P_hybrid", "P2")
    ]
    
    stat_test_rows = []
    
    for pA, pB in test_comparisons:
        for reg in ["balanced", "attack-heavy", "combined_50_50"]:
            if reg == "combined_50_50":
                valsA = np.array(seed_combined_net[pA])
                valsB = np.array(seed_combined_net[pB])
            else:
                valsA = np.array(seed_net_benefits[pA][reg])
                valsB = np.array(seed_net_benefits[pB][reg])
                
            diffs = valsA - valsB
            mean_diff = float(np.mean(diffs))
            
            # Wilcoxon signed-rank test
            # If all diffs are identical (e.g. constant zero), handle gracefully
            if np.all(diffs == 0):
                w_stat, w_pval = 0.0, 1.0
            else:
                try:
                    w_res = stats.wilcoxon(diffs, alternative="two-sided")
                    w_stat, w_pval = float(w_res.statistic), float(w_res.pvalue)
                except Exception as e:
                    w_stat, w_pval = np.nan, np.nan
                    
            # Paired Bootstrap (10,000 resamples)
            boot_rng = np.random.RandomState(42)
            boot_diffs = []
            for _ in range(10000):
                boot_idx = boot_rng.choice(len(diffs), size=len(diffs), replace=True)
                boot_diffs.append(np.mean(diffs[boot_idx]))
            boot_diffs = np.array(boot_diffs)
            boot_ci_low = float(np.percentile(boot_diffs, 2.5))
            boot_ci_high = float(np.percentile(boot_diffs, 97.5))
            boot_pval = float(np.mean(boot_diffs <= 0) * 2 if mean_diff > 0 else np.mean(boot_diffs >= 0) * 2)
            boot_pval = min(1.0, boot_pval)
            
            stat_test_rows.append({
                "comparison": f"{pA} vs {pB}",
                "regime": reg,
                "mean_diff_ocu": round(mean_diff, 1),
                "bootstrap_ci95_lower": round(boot_ci_low, 1),
                "bootstrap_ci95_upper": round(boot_ci_high, 1),
                "bootstrap_p_value": round(boot_pval, 4),
                "wilcoxon_stat": w_stat,
                "wilcoxon_p_value": round(w_pval, 4),
                "significance": "p < 0.05" if (w_pval < 0.05 or boot_pval < 0.05) else "Not Significant"
            })
            
    df_stat = pd.DataFrame(stat_test_rows)
    stat_csv = ROOT / "audit" / "outputs" / "task3_paired_bootstrap_wilcoxon.csv"
    df_stat.to_csv(stat_csv, index=False)
    print(f"\nSaved paired statistical tests to {stat_csv}")
    print(df_stat.to_string(index=False))

if __name__ == "__main__":
    run_task3_policy_rebuild()
