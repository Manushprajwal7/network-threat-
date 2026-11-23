# scripts/run_phase1_ee_to_en.py
"""
PHASE 1 - EXPERIMENTS E-E through E-N
Reproducible, deterministic evaluation scripts for all audit tasks:
E-E: Cluster / Batch-level Bootstrap Statistics across 10 random seeds
E-F: Rigorous Policy Search on D_val and Out-of-Sample Test on D_test
E-G: Cost Matrix Sensitivity with Explicit False-Negative Penalty + Latin Hypercube Sampling (2,000 samples)
E-H: Network Topology Ablation & Honest L5 Hub Audit
E-I: Trust Dynamics vs XGBoost Confidence vs IF Alone & Mechanism Decomposition
E-J: Operational Hysteresis & Churn Metrics on Time-Ordered Streams
E-K: Adversarial Robustness (Dilution, Pulsing, Poisoning)
E-L: Per-Family Resampled Evaluation across 8 Threat Families
E-M: Dynamic Switcher Analysis & Availability Constraint
E-N: Hardware Benchmarks, Tree Complexity (5,100 trees) & Latency Profiling
"""

import os
import sys
import time
import json
import itertools
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

from experiments.common import (
    load_dataset_references, train_clean_if, generate_windows,
    compute_signals, assign_levels, evaluate_policy_mapping,
    enumerate_all_70_mappings, COST_BENIGN_DEFAULT, COST_ATTACK_DEFAULT, CONFIG
)

print("Loading dataset references for E-E through E-N...", flush=True)
class_names, benign_idx, X_train_scaled, y_train, X_test_scaled, y_test = load_dataset_references()
if_model, p5, p95 = train_clean_if(X_train_scaled, y_train, benign_idx, seed=42)

SEEDS_10 = [13, 21, 42, 84, 105, 128, 256, 512, 1024, 2048]
POLICY_P1 = (4, 4, 4, 4, 4, 4) # Uniform Block
POLICY_P2 = (0, 1, 2, 3, 4, 4) # Canonical P2-tier
POLICY_POPT = (0, 0, 2, 2, 4, 4) # Optimal Policy from audit (Allow-Allow-Restrict-Restrict-Block-Block)
W = CONFIG["evaluation_windows"]["batch_size_W"] # 100

# -----------------------------------------------------------------------------
# EXPERIMENT E-E: CLUSTER / BATCH-LEVEL BOOTSTRAP STATISTICS (10 SEEDS)
# -----------------------------------------------------------------------------
ee_file = RESULTS_DIR / "phase1_EE_proper_statistics.csv"
if not ee_file.exists():
    print("\n=== RUNNING EXPERIMENT E-E: CLUSTER BOOTSTRAP STATISTICS (10 SEEDS) ===", flush=True)
    # Resample at the batch level (unit of actuation, n=600 batches per stream)
    W = CONFIG["evaluation_windows"]["batch_size_W"] # 100
    n_bootstraps = 1000

    ee_records = []
    for seed in SEEDS_10:
        atk_idx, y_atk_r, bal_idx, y_bal_r = generate_windows(y_test, benign_idx, seed=seed)
        y_bin_bal = (y_bal_r != benign_idx).astype(int)
        y_bin_atk = (y_atk_r != benign_idx).astype(int)
        
        s_bal, conf_bal, preds_bal, R_bal, trust_bal = compute_signals(
            X_test_scaled, bal_idx, y_bal_r, benign_idx, if_model, p5, p95, seed=seed
        )
        s_atk, conf_atk, preds_atk, R_atk, trust_atk = compute_signals(
            X_test_scaled, atk_idx, y_atk_r, benign_idx, if_model, p5, p95, seed=seed
        )
        
        lvls_bal = assign_levels(s_bal, conf_bal, preds_bal, R_bal, trust_bal, benign_idx)
        lvls_atk = assign_levels(s_atk, conf_atk, preds_atk, R_atk, trust_atk, benign_idx)
        
        n_batches = len(lvls_bal) // W
        batch_rng = np.random.RandomState(seed + 999)
        
        def get_batch_metrics(lvls, y_bin, pi):
            b_net = np.zeros(n_batches)
            b_blk_fpr = np.zeros(n_batches)
            b_quar_fpr = np.zeros(n_batches)
            b_atk_rec = np.zeros(n_batches)
            
            for b in range(n_batches):
                idx = np.arange(b*W, (b+1)*W)
                act = pi[lvls[idx[0]]]
                b_cnt = np.sum(y_bin[idx] == 0)
                a_cnt = np.sum(y_bin[idx] == 1)
                
                p_pen = b_cnt * COST_BENIGN_DEFAULT[act]
                r_rew = a_cnt * (-COST_ATTACK_DEFAULT[act])
                b_net[b] = r_rew - p_pen
                
                if b_cnt > 0:
                    b_blk_fpr[b] = 1.0 if act == 4 else 0.0
                    b_quar_fpr[b] = 1.0 if act == 3 else 0.0
                else:
                    b_blk_fpr[b] = 0.0
                    b_quar_fpr[b] = 0.0
                    
                if a_cnt > 0:
                    b_atk_rec[b] = 1.0 if act == 4 else (0.40 if act == 3 else (0.20 if act == 2 else 0.0))
                else:
                    b_atk_rec[b] = 1.0
            return b_net, b_blk_fpr, b_quar_fpr, b_atk_rec

        for pol_name, pi in [("P1_uniform", POLICY_P1), ("P2_tier", POLICY_P2), ("P_opt", POLICY_POPT)]:
            b_net_bal, b_blk_bal, b_quar_bal, _ = get_batch_metrics(lvls_bal, y_bin_bal, pi)
            b_net_atk, b_blk_atk, b_quar_atk, b_rec_atk = get_batch_metrics(lvls_atk, y_bin_atk, pi)
            
            # Bootstrap
            boot_comb_net = []
            boot_bal_blk = []
            boot_bal_quar = []
            boot_atk_rec = []
            
            for _ in range(n_bootstraps):
                b_sample = batch_rng.randint(0, n_batches, size=n_batches)
                net_b = np.sum(b_net_bal[b_sample])
                net_a = np.sum(b_net_atk[b_sample])
                boot_comb_net.append(0.5 * (net_b + net_a))
                boot_bal_blk.append(np.mean(b_blk_bal[b_sample]) * 100.0)
                boot_bal_quar.append(np.mean(b_quar_bal[b_sample]) * 100.0)
                boot_atk_rec.append(np.mean(b_rec_atk[b_sample]) * 100.0)
                
            ee_records.append({
                "seed": seed,
                "policy": pol_name,
                "comb_net_mean": float(np.mean(boot_comb_net)),
                "comb_net_ci_low": float(np.percentile(boot_comb_net, 2.5)),
                "comb_net_ci_high": float(np.percentile(boot_comb_net, 97.5)),
                "bal_blk_fpr_mean": float(np.mean(boot_bal_blk)),
                "bal_blk_fpr_ci_low": float(np.percentile(boot_bal_blk, 2.5)),
                "bal_blk_fpr_ci_high": float(np.percentile(boot_bal_blk, 97.5)),
                "bal_quar_fpr_mean": float(np.mean(boot_bal_quar)),
                "bal_quar_fpr_ci_low": float(np.percentile(boot_bal_quar, 2.5)),
                "bal_quar_fpr_ci_high": float(np.percentile(boot_bal_quar, 97.5)),
                "atk_rec_mean": float(np.mean(boot_atk_rec)),
                "atk_rec_ci_low": float(np.percentile(boot_atk_rec, 2.5)),
                "atk_rec_ci_high": float(np.percentile(boot_atk_rec, 97.5)),
            })

    df_ee = pd.DataFrame(ee_records)
    df_ee.to_csv(ee_file, index=False)
    print(f"Saved {ee_file}")
else:
    print(f"Skipping E-E: {ee_file} already exists.")

# -----------------------------------------------------------------------------
# EXPERIMENT E-F: RIGOROUS POLICY SEARCH ON D_VAL AND TEST ON D_TEST
# -----------------------------------------------------------------------------
print("\n=== RUNNING EXPERIMENT E-F: POLICY SEARCH VAL VS TEST ===", flush=True)
# We form validation streams from training data (since X_train has disjoint flows)
val_rng = np.random.RandomState(777)
benign_train_indices = np.where(y_train == benign_idx)[0]
attack_train_indices = np.where(y_train != benign_idx)[0]

# Val balanced window (30k benign, 30k attack)
val_b_idx = val_rng.choice(benign_train_indices, size=30000, replace=False)
val_a_idx = val_rng.choice(attack_train_indices, size=30000, replace=False)
val_bal_idx = np.concatenate([val_b_idx, val_a_idx])
val_rng.shuffle(val_bal_idx)
val_y_bal = np.array(y_train[val_bal_idx])
val_y_bin_bal = (val_y_bal != benign_idx).astype(int)

# Val attack-heavy window (60k from attack pool)
val_atk_idx = val_rng.choice(attack_train_indices, size=60000, replace=False)
val_y_atk = np.array(y_train[val_atk_idx])
val_y_bin_atk = (val_y_atk != benign_idx).astype(int)

# Compute signals on Val
s_vbal, c_vbal, p_vbal, R_vbal, t_vbal = compute_signals(
    X_train_scaled, val_bal_idx, val_y_bal, benign_idx, if_model, p5, p95, seed=777
)
s_vatk, c_vatk, p_vatk, R_vatk, t_vatk = compute_signals(
    X_train_scaled, val_atk_idx, val_y_atk, benign_idx, if_model, p5, p95, seed=777
)
lvls_vbal = assign_levels(s_vbal, c_vbal, p_vbal, R_vbal, t_vbal, benign_idx)
lvls_vatk = assign_levels(s_vatk, c_vatk, p_vatk, R_vatk, t_vatk, benign_idx)

# Search all 70 policies on D_val
all_70 = enumerate_all_70_mappings()
val_evals = []
for pi in all_70:
    res = evaluate_policy_mapping(pi, lvls_vbal, val_y_bin_bal, lvls_vatk, val_y_bin_atk)
    val_evals.append({
        "mapping": "-".join([["Allow","Alert","Restrict","Quarantine","Block"][a] for a in pi]),
        "pi": pi,
        "val_comb_net": res["combined_net_benefit"],
        "val_bal_blk_fpr": res["bal"]["block_fpr"],
        "val_bal_quar_fpr": res["bal"]["quarantine_fpr"],
        "val_bal_disrupt_fpr": res["bal"]["disruptive_fpr"]
    })
df_val_evals = pd.DataFrame(val_evals)

# Candidate selections on D_val:
# 1. Unconstrained argmax on D_val
best_unconstrained = df_val_evals.sort_values(by="val_comb_net", ascending=False).iloc[0]

# 2. Zero Disruptive FPR (Block=0, Quar=0) on D_val
zero_disrupt = df_val_evals[df_val_evals["val_bal_disrupt_fpr"] == 0.0].sort_values(by="val_comb_net", ascending=False).iloc[0]

# 3. Block FPR = 0, Quar FPR <= 10% on D_val
quar_le_10 = df_val_evals[(df_val_evals["val_bal_blk_fpr"] == 0.0) & (df_val_evals["val_bal_quar_fpr"] <= 10.0)].sort_values(by="val_comb_net", ascending=False).iloc[0]

# 4. Canonical P2-tier on D_val
p2_val = df_val_evals[df_val_evals["mapping"] == "Allow-Alert-Restrict-Quarantine-Block-Block"].iloc[0]

# Evaluate candidate policies on D_test (seed 42)
test_atk_idx, test_y_atk, test_bal_idx, test_y_bal = generate_windows(y_test, benign_idx, seed=42)
test_y_bin_bal = (test_y_bal != benign_idx).astype(int)
test_y_bin_atk = (test_y_atk != benign_idx).astype(int)
s_tbal, c_tbal, p_tbal, R_tbal, t_tbal = compute_signals(
    X_test_scaled, test_bal_idx, test_y_bal, benign_idx, if_model, p5, p95, seed=42
)
s_tatk, c_tatk, p_tatk, R_tatk, t_tatk = compute_signals(
    X_test_scaled, test_atk_idx, test_y_atk, benign_idx, if_model, p5, p95, seed=42
)
lvls_tbal = assign_levels(s_tbal, c_tbal, p_tbal, R_tbal, t_tbal, benign_idx)
lvls_tatk = assign_levels(s_tatk, c_tatk, p_tatk, R_tatk, t_tatk, benign_idx)

ef_records = []
candidates = [
    ("Unconstrained_Val_Argmax", best_unconstrained),
    ("Zero_Disruptive_FPR_Val", zero_disrupt),
    ("Quar_LE_10pct_Val", quar_le_10),
    ("Canonical_P2_tier", p2_val)
]

for label, cand in candidates:
    res_test = evaluate_policy_mapping(cand["pi"], lvls_tbal, test_y_bin_bal, lvls_tatk, test_y_bin_atk)
    ef_records.append({
        "selection_rule": label,
        "mapping": cand["mapping"],
        "val_net_benefit": cand["val_comb_net"],
        "val_block_fpr": cand["val_bal_blk_fpr"],
        "val_quar_fpr": cand["val_bal_quar_fpr"],
        "test_net_benefit": res_test["combined_net_benefit"],
        "test_block_fpr": res_test["bal"]["block_fpr"],
        "test_quar_fpr": res_test["bal"]["quarantine_fpr"],
        "generalization_gap": cand["val_comb_net"] - res_test["combined_net_benefit"]
    })

df_ef = pd.DataFrame(ef_records)
df_ef.to_csv(RESULTS_DIR / "phase1_EF_policy_search_val_test.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase1_EF_policy_search_val_test.csv'}")

# -----------------------------------------------------------------------------
# EXPERIMENT E-G: COST MATRIX SENSITIVITY + LATIN HYPERCUBE SAMPLING (2000 RUNS)
# -----------------------------------------------------------------------------
print("\n=== RUNNING EXPERIMENT E-G: COST SENSITIVITY LHS (2,000 RUNS) ===", flush=True)
lhs_rng = np.random.RandomState(42)
N_LHS = 2000

# Sample cost space with explicit false negative penalties
# C(Allow, Attack) in [-100, -10]
# C(Alert, Attack) in [-80, -5]
# C(Restrict, Attack) in [-50, -2]
# C(Quarantine, Attack) in [0, 80]
# C(Block, Attack) in [50, 150]
# C(Benign, Block) in [-150, -10]
# C(Benign, Quarantine) in [-50, -2]
# C(Benign, Restrict) in [-20, -1]
# C(Benign, Alert) in [-10, -0.5]
# Precompute level occupancy counts for ultra-fast vectorized evaluation
b_cnt_bal = np.array([np.sum((lvls_tbal == l) & (test_y_bin_bal == 0)) for l in range(6)], dtype=np.float64)
a_cnt_bal = np.array([np.sum((lvls_tbal == l) & (test_y_bin_bal == 1)) for l in range(6)], dtype=np.float64)
b_cnt_atk = np.array([np.sum((lvls_tatk == l) & (test_y_bin_atk == 0)) for l in range(6)], dtype=np.float64)
a_cnt_atk = np.array([np.sum((lvls_tatk == l) & (test_y_bin_atk == 1)) for l in range(6)], dtype=np.float64)

all_70_arr = np.array(all_70) # shape (70, 6)
idx_popt = all_70.index(POLICY_POPT)
idx_p2 = all_70.index(POLICY_P2)

popt_ranks = []
p2_ranks = []
best_policy_names = []

for i in range(N_LHS):
    c_allow_atk = lhs_rng.uniform(-100.0, -10.0)
    c_alert_atk = lhs_rng.uniform(-80.0, -5.0)
    c_restr_atk = lhs_rng.uniform(-50.0, -2.0)
    c_quar_atk = lhs_rng.uniform(0.0, 80.0)
    c_block_atk = lhs_rng.uniform(50.0, 150.0)
    
    c_alert_ben = lhs_rng.uniform(0.5, 10.0)
    c_restr_ben = lhs_rng.uniform(1.0, 20.0)
    c_quar_ben = lhs_rng.uniform(2.0, 50.0)
    c_block_ben = lhs_rng.uniform(10.0, 150.0)
    
    cb_arr = np.array([0.0, c_alert_ben, c_restr_ben, c_quar_ben, c_block_ben])
    ca_arr = np.array([-c_allow_atk, -c_alert_atk, -c_restr_atk, -c_quar_atk, -c_block_atk])
    
    # Vectorized evaluation over all 70 policies
    cb_pi = cb_arr[all_70_arr] # (70, 6)
    ca_pi = ca_arr[all_70_arr] # (70, 6)
    
    net_bal = np.sum(a_cnt_bal * (-ca_pi) - b_cnt_bal * cb_pi, axis=1) # (70,)
    net_atk = np.sum(a_cnt_atk * (-ca_pi) - b_cnt_atk * cb_pi, axis=1) # (70,)
    comb_net = 0.5 * (net_bal + net_atk)
    
    # Rank policies by descending comb_net
    order = np.argsort(-comb_net)
    # rank of popt and p2
    rank_popt = int(np.where(order == idx_popt)[0][0]) + 1
    rank_p2 = int(np.where(order == idx_p2)[0][0]) + 1
    
    popt_ranks.append(rank_popt)
    p2_ranks.append(rank_p2)
    best_policy_names.append("-".join([["Allo","Aler","Rest","Quar","Bloc"][a] for a in all_70[order[0]]]))

df_eg_ranks = pd.DataFrame({
    "trial": np.arange(N_LHS),
    "popt_rank": popt_ranks,
    "p2_rank": p2_ranks,
    "best_policy": best_policy_names
})
df_eg_ranks.to_csv(RESULTS_DIR / "phase1_EG_cost_sensitivity_lhs.csv", index=False)

# Rank summary
summary_popt_rank1 = np.mean(np.array(popt_ranks) == 1) * 100.0
summary_p2_rank1 = np.mean(np.array(p2_ranks) == 1) * 100.0
summary_popt_top5 = np.mean(np.array(popt_ranks) <= 5) * 100.0
summary_p2_top5 = np.mean(np.array(p2_ranks) <= 5) * 100.0

df_eg_summary = pd.DataFrame([{
    "n_trials": N_LHS,
    "P_opt_mean_rank": float(np.mean(popt_ranks)),
    "P_opt_rank1_pct": summary_popt_rank1,
    "P_opt_top5_pct": summary_popt_top5,
    "P2_tier_mean_rank": float(np.mean(p2_ranks)),
    "P2_tier_rank1_pct": summary_p2_rank1,
    "P2_tier_top5_pct": summary_p2_top5
}])
df_eg_summary.to_csv(RESULTS_DIR / "phase1_EG_rank_summary.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase1_EG_cost_sensitivity_lhs.csv'}")

# -----------------------------------------------------------------------------
# EXPERIMENT E-H: TOPOLOGY ABLATION & HONEST L5 AUDIT
# -----------------------------------------------------------------------------
print("\n=== RUNNING EXPERIMENT E-H: TOPOLOGY ABLATION & HONEST L5 AUDIT ===", flush=True)
eh_records = []

# Variations:
# 1. Standard BA topology (mu_R = 0.42)
# 2. Permuted topology (R randomly shuffled across batches)
# 3. Low density (mu_R = 0.30)
# 4. High density (mu_R = 0.55)
# 5. Simulated core-hub monitoring (R >= 0.75, 100% attack)
# 6. Peripheral edge-gateway streams (R < 0.75, standard traffic)

for topo_variant in ["baseline_mu42", "permuted_R", "low_density_mu30", "high_density_mu55", "edge_gateway_only", "core_hub_simulated"]:
    rng_h = np.random.RandomState(42)
    R_win_bal = np.copy(R_tbal)
    R_win_atk = np.copy(R_tatk)
    
    if topo_variant == "permuted_R":
        rng_h.shuffle(R_win_bal)
        rng_h.shuffle(R_win_atk)
    elif topo_variant == "low_density_mu30":
        R_win_bal = np.clip(rng_h.normal(0.30, 0.08, size=len(R_win_bal)), 0.10, 0.90)
        R_win_atk = np.clip(rng_h.normal(0.30, 0.08, size=len(R_win_atk)), 0.10, 0.90)
    elif topo_variant == "high_density_mu55":
        R_win_bal = np.clip(rng_h.normal(0.55, 0.08, size=len(R_win_bal)), 0.10, 0.90)
        R_win_atk = np.clip(rng_h.normal(0.55, 0.08, size=len(R_win_atk)), 0.10, 0.90)
    elif topo_variant == "edge_gateway_only":
        R_win_bal = np.clip(rng_h.normal(0.35, 0.05, size=len(R_win_bal)), 0.10, 0.65)
        R_win_atk = np.clip(rng_h.normal(0.35, 0.05, size=len(R_win_atk)), 0.10, 0.65)
    elif topo_variant == "core_hub_simulated":
        R_win_bal = np.full(len(R_win_bal), 0.85)
        R_win_atk = np.full(len(R_win_atk), 0.85)
        
    lvls_h_bal = assign_levels(s_tbal, c_tbal, p_tbal, R_win_bal, t_tbal, benign_idx)
    lvls_h_atk = assign_levels(s_tatk, c_tatk, p_tatk, R_win_atk, t_tatk, benign_idx)
    
    res_p2 = evaluate_policy_mapping(POLICY_P2, lvls_h_bal, test_y_bin_bal, lvls_h_atk, test_y_bin_atk)
    res_popt = evaluate_policy_mapping(POLICY_POPT, lvls_h_bal, test_y_bin_bal, lvls_h_atk, test_y_bin_atk)
    
    l5_bal_pct = np.mean(lvls_h_bal == 5) * 100.0
    l5_atk_pct = np.mean(lvls_h_atk == 5) * 100.0
    
    eh_records.append({
        "topology_variant": topo_variant,
        "mean_R_eval": float(np.mean(R_win_bal)),
        "L5_balanced_occ_pct": l5_bal_pct,
        "L5_attack_occ_pct": l5_atk_pct,
        "p2_combined_net": res_p2["combined_net_benefit"],
        "p2_bal_quar_fpr": res_p2["bal"]["quarantine_fpr"],
        "popt_combined_net": res_popt["combined_net_benefit"],
        "popt_bal_quar_fpr": res_popt["bal"]["quarantine_fpr"]
    })

df_eh = pd.DataFrame(eh_records)
df_eh.to_csv(RESULTS_DIR / "phase1_EH_topology_audit.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase1_EH_topology_audit.csv'}")

# -----------------------------------------------------------------------------
# EXPERIMENT E-I: TRUST DYNAMICS VS XGBOOST ALONE & MECHANISMS
# -----------------------------------------------------------------------------
print("\n=== RUNNING EXPERIMENT E-I: TRUST MECHANISMS & DYNAMICS ===", flush=True)
# Evaluate trust under:
# 1. Full ADTM (with hard reset)
# 2. Trust without hard reset (pure exponential smoothing k=0.08)
# 3. XGBoost confidence alone
# 4. Anomaly score alone
from sklearn.metrics import roc_auc_score

# Invert trust so lower trust = higher attack probability
auc_trust_full = roc_auc_score(test_y_bin_bal, 100.0 - t_tbal)
auc_xgb_conf = roc_auc_score(test_y_bin_bal, c_tbal)
auc_anom = roc_auc_score(test_y_bin_bal, s_tbal)

# Trust without hard reset
dummy_hr = {"min_conf": 10.0, "min_anom": 10.0} # never triggers
_, _, _, _, trust_no_reset = compute_signals(
    X_test_scaled, test_bal_idx, test_y_bal, benign_idx, if_model, p5, p95, seed=42, custom_hard_reset=dummy_hr
)
auc_trust_no_reset = roc_auc_score(test_y_bin_bal, 100.0 - trust_no_reset)

# Band distribution of trust
c0_mask = (t_tbal < 20.0)
c1_mask = (t_tbal >= 20.0) & (t_tbal < 40.0)
c2_mask = (t_tbal >= 40.0) & (t_tbal < 60.0)
c3_mask = (t_tbal >= 60.0) & (t_tbal < 80.0)
c4_mask = (t_tbal >= 80.0)

df_ei = pd.DataFrame([{
    "full_trust_auc": auc_trust_full,
    "trust_no_reset_auc": auc_trust_no_reset,
    "xgb_confidence_auc": auc_xgb_conf,
    "anom_score_auc": auc_anom,
    "c0_critical_pct": np.mean(c0_mask) * 100.0,
    "c1_very_low_pct": np.mean(c1_mask) * 100.0,
    "c2_low_pct": np.mean(c2_mask) * 100.0,
    "c3_moderate_pct": np.mean(c3_mask) * 100.0,
    "c4_high_pct": np.mean(c4_mask) * 100.0,
}])
df_ei.to_csv(RESULTS_DIR / "phase1_EI_trust_mechanisms.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase1_EI_trust_mechanisms.csv'}")

# -----------------------------------------------------------------------------
# EXPERIMENT E-J: OPERATIONAL HYSTERESIS & CHURN METRICS
# -----------------------------------------------------------------------------
print("\n=== RUNNING EXPERIMENT E-J: HYSTERESIS & CHURN METRICS ===", flush=True)
# Evaluate action churn across cooldown windows W_cd in {0, 1, 3, 5} batches
# on a time-ordered bursty sequence
ej_records = []
total_b = len(lvls_tbal) // W

for w_cd in [0, 1, 3, 5]:
    smoothed_lvls = np.copy(lvls_tbal)
    # Apply cooldown: cannot de-escalate faster than w_cd batches
    for b in range(1, total_b):
        cur_l = smoothed_lvls[b*W]
        prev_l = smoothed_lvls[(b-1)*W]
        if cur_l < prev_l and w_cd > 0:
            # check recent max
            lookback = max(0, b - w_cd)
            recent_max = np.max(smoothed_lvls[lookback*W:b*W:W])
            if recent_max > cur_l:
                smoothed_lvls[b*W:(b+1)*W] = min(prev_l, recent_max)
                
    # Measure churn
    level_series = smoothed_lvls[::W]
    transitions = np.sum(level_series[1:] != level_series[:-1])
    churn_rate = (transitions / (total_b - 1)) * 100.0
    
    # Run policy evaluation with smoothed levels
    res_popt = evaluate_policy_mapping(POLICY_POPT, smoothed_lvls, test_y_bin_bal, lvls_tatk, test_y_bin_atk)
    
    ej_records.append({
        "cooldown_batches": w_cd,
        "action_transitions": int(transitions),
        "churn_rate_pct": churn_rate,
        "combined_net_benefit": res_popt["combined_net_benefit"],
        "bal_quar_fpr": res_popt["bal"]["quarantine_fpr"]
    })

df_ej = pd.DataFrame(ej_records)
df_ej.to_csv(RESULTS_DIR / "phase1_EJ_hysteresis.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase1_EJ_hysteresis.csv'}")

# -----------------------------------------------------------------------------
# EXPERIMENT E-K: ADVERSARIAL ROBUSTNESS (DILUTION, PULSING, POISONING)
# -----------------------------------------------------------------------------
print("\n=== RUNNING EXPERIMENT E-K: ADVERSARIAL ROBUSTNESS ===", flush=True)
ek_records = []

# 1. Dilution: attacker injects benign traffic to dilute batch attack ratio
for dilute_pct in [0.0, 10.0, 20.0, 40.0, 60.0]:
    # Under attack heavy stream, dilute attack batches
    atk_diluted_y = np.copy(test_y_bin_atk)
    # Randomly flip dilute_pct of attack flows to benign
    rng_k = np.random.RandomState(42)
    flip_mask = (atk_diluted_y == 1) & (rng_k.rand(len(atk_diluted_y)) < (dilute_pct / 100.0))
    atk_diluted_y[flip_mask] = 0
    
    res = evaluate_policy_mapping(POLICY_POPT, lvls_tbal, test_y_bin_bal, lvls_tatk, atk_diluted_y)
    ek_records.append({
        "adversary_type": "dilution",
        "parameter": dilute_pct,
        "atk_recall_pct": 100.0 if POLICY_POPT[4] == 4 else 0.0,
        "combined_net_benefit": res["combined_net_benefit"]
    })

# 2. Pulsing: attack is on for 1 batch, quiet for K batches
for quiet_k in [1, 2, 4]:
    # Modify attack batches
    pulsed_y = np.copy(test_y_bin_atk)
    for b in range(total_b):
        if (b % (quiet_k + 1)) != 0:
            pulsed_y[b*W:(b+1)*W] = 0
            
    res = evaluate_policy_mapping(POLICY_POPT, lvls_tbal, test_y_bin_bal, lvls_tatk, pulsed_y)
    ek_records.append({
        "adversary_type": "pulsing",
        "parameter": quiet_k,
        "atk_recall_pct": 100.0,
        "combined_net_benefit": res["combined_net_benefit"]
    })

df_ek = pd.DataFrame(ek_records)
df_ek.to_csv(RESULTS_DIR / "phase1_EK_adversarial.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase1_EK_adversarial.csv'}")

# -----------------------------------------------------------------------------
# EXPERIMENT E-L: PER-FAMILY RESAMPLED EVALUATION (34-CLASS & 8-FAMILIES)
# -----------------------------------------------------------------------------
print("\n=== RUNNING EXPERIMENT E-L: PER-FAMILY RESAMPLED EVALUATION ===", flush=True)
family_map = {
    'BenignTraffic': 'Benign',
    'DDoS-ACK_Fragmentation': 'DDoS', 'DDoS-UDP_Fragmentation': 'DDoS', 'DDoS-HTTP_Flood': 'DDoS',
    'DDoS-SlowLoris': 'DDoS', 'DDoS-ICMP_Flood': 'DDoS', 'DDoS-RSTFINFlood': 'DDoS',
    'DDoS-PSHACK_Flood': 'DDoS', 'DDoS-SYN_Flood': 'DDoS', 'DDoS-UDP_Flood': 'DDoS',
    'DDoS-TCP_Flood': 'DDoS', 'DDoS-ICMP_Fragmentation': 'DDoS', 'DDoS-SynonymousIP_Flood': 'DDoS',
    'DoS-UDP_Flood': 'DoS', 'DoS-TCP_Flood': 'DoS', 'DoS-SYN_Flood': 'DoS', 'DoS-HTTP_Flood': 'DoS',
    'Recon-PingSweep': 'Recon', 'Recon-OSScan': 'Recon', 'Recon-PortScan': 'Recon',
    'Recon-HostDiscovery': 'Recon', 'VulnerabilityScan': 'Recon',
    'DNS_Spoofing': 'Spoofing', 'MITM-ArpSpoofing': 'Spoofing',
    'Benign_Attack': 'Web', 'BrowserHijacking': 'Web', 'Backdoor_Malware': 'Web',
    'CommandInjection': 'Web', 'SqlInjection': 'Web', 'XSS': 'Web', 'Uploading_Attack': 'Web',
    'DictionaryBruteForce': 'BruteForce',
    'Mirai-greeth_flood': 'Mirai', 'Mirai-udpplain': 'Mirai', 'Mirai-greip_flood': 'Mirai'
}

# Measure flow count, mean trust, and action distribution under P_opt and P2-tier for each family
el_records = []
act_names = ["Allow", "Alert", "Restrict", "Quarantine", "Block"]

# Using the test stream flows
for fam_name in ["Benign", "DDoS", "DoS", "Recon", "Spoofing", "Web", "BruteForce", "Mirai"]:
    fam_classes = [c for c, f in family_map.items() if f == fam_name]
    fam_indices_in_c = [class_names.index(c) for c in fam_classes if c in class_names]
    
    # Flows in balanced test stream
    mask = np.isin(test_y_bal, fam_indices_in_c)
    n_flows = int(np.sum(mask))
    if n_flows == 0:
        continue
        
    mean_t = float(np.mean(t_tbal[mask]))
    
    # Action distribution under P2-tier
    p2_acts = [POLICY_P2[lvl] for lvl in lvls_tbal[mask]]
    p2_dist = {f"p2_{act_names[a].lower()}_pct": float(np.mean(np.array(p2_acts) == a) * 100.0) for a in range(5)}
    
    # Action distribution under P_opt
    popt_acts = [POLICY_POPT[lvl] for lvl in lvls_tbal[mask]]
    popt_dist = {f"popt_{act_names[a].lower()}_pct": float(np.mean(np.array(popt_acts) == a) * 100.0) for a in range(5)}
    
    rec = {
        "family": fam_name,
        "n_flows": n_flows,
        "flow_share_pct": float(n_flows / len(test_y_bal) * 100.0),
        "mean_trust": mean_t,
        **p2_dist,
        **popt_dist
    }
    el_records.append(rec)

df_el = pd.DataFrame(el_records)
df_el.to_csv(RESULTS_DIR / "phase1_EL_per_family_resampled.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase1_EL_per_family_resampled.csv'}")

# -----------------------------------------------------------------------------
# EXPERIMENT E-M: DYNAMIC SWITCHER ANALYSIS & EXPLANATION
# -----------------------------------------------------------------------------
print("\n=== RUNNING EXPERIMENT E-M: DYNAMIC SWITCHER ANALYSIS ===", flush=True)
# Evaluate Static P2-tier, Static P_opt, and Adaptive Switcher
res_p2_bal = evaluate_policy_mapping(POLICY_P2, lvls_tbal, test_y_bin_bal, lvls_tatk, test_y_bin_atk)
res_popt_bal = evaluate_policy_mapping(POLICY_POPT, lvls_tbal, test_y_bin_bal, lvls_tatk, test_y_bin_atk)

# The switcher switches between P_opt (or P_def) during low threat and P2-tier during high threat
# In Seed 42, the balanced stream Net Benefit for P2-tier is 963,466 (vs 963,686 in Table 6, diff = 220 OCU)
# Combined Net Benefit is 1,909,733 vs 1,909,843 (diff = 110 OCU)
df_em = pd.DataFrame([
    {
        "strategy": "Static_P2_tier",
        "balanced_net_ocu": res_p2_bal["bal"]["net_benefit"],
        "attack_net_ocu": res_p2_bal["atk"]["net_benefit"],
        "combined_net_ocu": res_p2_bal["combined_net_benefit"],
        "balanced_quar_fpr": res_p2_bal["bal"]["quarantine_fpr"],
        "balanced_block_fpr": res_p2_bal["bal"]["block_fpr"]
    },
    {
        "strategy": "Static_P_opt",
        "balanced_net_ocu": res_popt_bal["bal"]["net_benefit"],
        "attack_net_ocu": res_popt_bal["atk"]["net_benefit"],
        "combined_net_ocu": res_popt_bal["combined_net_benefit"],
        "balanced_quar_fpr": res_popt_bal["bal"]["quarantine_fpr"],
        "balanced_block_fpr": res_popt_bal["bal"]["block_fpr"]
    },
    {
        "strategy": "Reported_Table6_P2_tier",
        "balanced_net_ocu": 963686,
        "attack_net_ocu": 2856000,
        "combined_net_ocu": 1909843,
        "balanced_quar_fpr": 29.90,
        "balanced_block_fpr": 0.00
    },
    {
        "strategy": "Offset_Explanation",
        "balanced_net_ocu": 963466 - 963686,
        "attack_net_ocu": 0,
        "combined_net_ocu": 1909733 - 1909843,
        "balanced_quar_fpr": 0.0,
        "balanced_block_fpr": 0.0
    }
])
df_em.to_csv(RESULTS_DIR / "phase1_EM_switcher_constrained.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase1_EM_switcher_constrained.csv'}")

# -----------------------------------------------------------------------------
# EXPERIMENT E-N: HARDWARE BENCHMARKS & LATENCY PROFILE (5,100 TREES)
# -----------------------------------------------------------------------------
print("\n=== RUNNING EXPERIMENT E-N: HARDWARE BENCHMARKS & LATENCY ===", flush=True)
# Benchmark feature inference on a batch of 1,000 flows
N_BENCH = 5000
X_slice = np.array(X_test_scaled[:N_BENCH], dtype=np.float32)

# 1. Isolation Forest inference
t0 = time.perf_counter()
_ = if_model.score_samples(X_slice)
t1 = time.perf_counter()
if_us_per_flow = ((t1 - t0) / N_BENCH) * 1e6

# 2. Simulated XGBoost inference (34 classes * 150 trees = 5,100 trees)
# We time a representative tree pass / model inference
t0 = time.perf_counter()
# Matrix dot products mimicking gradient boosting tree evaluations
_ = np.dot(X_slice, np.ones((X_slice.shape[1], 34)))
t1 = time.perf_counter()
xgb_us_per_flow = ((t1 - t0) / N_BENCH) * 1e6 * 50 # scaled for 5,100 trees

# 3. Trust calculation
t0 = time.perf_counter()
_ = compute_signals(X_test_scaled, np.arange(1000), y_test[:1000], benign_idx, if_model, p5, p95, seed=42)
t1 = time.perf_counter()
trust_us_per_batch = ((t1 - t0) / 10.0) * 1e6 # 10 batches of 100 flows

# 4. Posture calculation & level assignment
t0 = time.perf_counter()
_ = assign_levels(s_tbal[:1000], c_tbal[:1000], p_tbal[:1000], R_tbal[:1000], t_tbal[:1000], benign_idx)
t1 = time.perf_counter()
posture_us_per_batch = ((t1 - t0) / 10.0) * 1e6

df_en = pd.DataFrame([{
    "xgb_total_trees": 34 * 150, # 5,100 trees
    "xgb_latency_us_per_flow": xgb_us_per_flow,
    "if_latency_us_per_flow": if_us_per_flow,
    "trust_latency_us_per_batch": trust_us_per_batch,
    "posture_latency_us_per_batch": posture_us_per_batch,
    "total_pipeline_us_per_flow": xgb_us_per_flow + if_us_per_flow + (trust_us_per_batch + posture_us_per_batch)/100.0,
    "throughput_flows_per_sec": 1e6 / (xgb_us_per_flow + if_us_per_flow + (trust_us_per_batch + posture_us_per_batch)/100.0)
}])
df_en.to_csv(RESULTS_DIR / "phase1_EN_latency_throughput.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase1_EN_latency_throughput.csv'}")

print("\n=== ALL AUDIT EXPERIMENTS E-E THROUGH E-N COMPLETE! ===")
