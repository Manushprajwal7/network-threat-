# scripts/run_phase1_ec_ed.py
"""
PHASE 1 - EXPERIMENTS E-C and E-D
E-C: Component ablation & baselines
  (i) XGBoost-alone per-flow policy (attack if conf>=0.9 -> Block else Allow)
  (ii) Per-flow hybrid: batch level for L0-L3, per-flow benign veto inside L4
  (iii) Full 2^4 = 16 ablation of {c_conf, c_anom, c_trust, c_topo}
  (iv) Pipeline with IF removed entirely
  (v) Pipeline with trust removed
  (vi) Learned meta-classifier (Logistic Regression, Decision Tree) on the 4 signals
E-D: Realistic streams + prevalence sweep
  Time-ordered continuous benign background with injected attack bursts of random durations.
  Sweep attack prevalence in {0.1, 0.5, 1, 2, 5, 10, 25, 50, 75, 97.6}%.
  Level occupancy, attack density per level with batch bootstrap CIs.
  Net benefit of P1, P2-tier, P_opt, and XGBoost-alone.
  Break-even prevalence between P1 and P2-tier.
"""
import os
import sys
import json
import itertools
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import roc_auc_score
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

from experiments.common import (
    load_dataset_references, train_clean_if, generate_windows,
    compute_signals, assign_levels, evaluate_policy_mapping,
    COST_BENIGN_DEFAULT, COST_ATTACK_DEFAULT, CONFIG
)

print("Loading dataset references for E-C and E-D...", flush=True)
class_names, benign_idx, X_train_scaled, y_train, X_test_scaled, y_test = load_dataset_references()
if_model, p5, p95 = train_clean_if(X_train_scaled, y_train, benign_idx, seed=42)

# Load evaluation streams
atk_indices, y_atk_raw, bal_indices, y_bal_raw = generate_windows(y_test, benign_idx, seed=42)
y_bin_bal = (y_bal_raw != benign_idx).astype(int)
y_bin_atk = (y_atk_raw != benign_idx).astype(int)

# Signals
s_bal, conf_bal, preds_bal, R_bal, trust_bal = compute_signals(
    X_test_scaled, bal_indices, y_bal_raw, benign_idx, if_model, p5, p95, seed=42
)
s_atk, conf_atk, preds_atk, R_atk, trust_atk = compute_signals(
    X_test_scaled, atk_indices, y_atk_raw, benign_idx, if_model, p5, p95, seed=42
)

# -----------------------------------------------------------------------------
# EXPERIMENT E-C: COMPONENT ABLATION & BASELINES
# -----------------------------------------------------------------------------
print("\n=== RUNNING EXPERIMENT E-C: COMPONENT ABLATION & BASELINES ===", flush=True)

# (i) Pure XGBoost Per-Flow Policy
# If predicted != benign and conf >= 0.90 -> Block (4), else Allow (0)
def eval_pure_xgb(preds, confs, y_bin):
    act = np.where((preds != benign_idx) & (confs >= 0.90), 4, 0)
    b_blk = np.sum((act == 4) & (y_bin == 0))
    tot_b = np.sum(y_bin == 0)
    tot_a = np.sum(y_bin == 1)
    
    ben_pen = b_blk * COST_BENIGN_DEFAULT[4]
    atk_rew = np.sum((act == 4) & (y_bin == 1)) * (-COST_ATTACK_DEFAULT[4])
    net_ben = atk_rew - ben_pen
    blk_fpr = (b_blk / tot_b * 100.0) if tot_b > 0 else 0.0
    return net_ben, blk_fpr, b_blk

xgb_net_bal, xgb_fpr_bal, xgb_blk_cnt_bal = eval_pure_xgb(preds_bal, conf_bal, y_bin_bal)
xgb_net_atk, xgb_fpr_atk, xgb_blk_cnt_atk = eval_pure_xgb(preds_atk, conf_atk, y_bin_atk)
xgb_comb = 0.5 * (xgb_net_bal + xgb_net_atk)
print(f"P_XGB: Combined Net = {xgb_comb:+,.0f} OCU, Balanced Block FPR = {xgb_fpr_bal:.2f}% ({xgb_blk_cnt_bal} flows blocked)", flush=True)

# (ii) Hybrid Posture + Benign Veto inside Level L4
# Batch posture escalation for L0-L3; in L4, if predicted == benign and conf >= 0.90 -> Allow (veto), else Block
levels_bal = assign_levels(s_bal, conf_bal, preds_bal, R_bal, trust_bal, benign_idx)
levels_atk = assign_levels(s_atk, conf_atk, preds_atk, R_atk, trust_atk, benign_idx)

def eval_hybrid(levels, preds, confs, y_bin):
    pi_p2_tier = [0, 1, 2, 3, 4, 4]
    acts = np.array([pi_p2_tier[lvl] for lvl in levels])
    
    # Apply benign veto in L4: if flow is predicted benign with conf >= 0.90, override Block -> Allow (0)
    veto_mask = (levels == 4) & (preds == benign_idx) & (confs >= 0.90)
    acts[veto_mask] = 0
    
    b_blk = np.sum((acts == 4) & (y_bin == 0))
    b_quar = np.sum((acts == 3) & (y_bin == 0))
    tot_b = np.sum(y_bin == 0)
    
    ben_pen = np.sum([np.sum((acts == a) & (y_bin == 0)) * COST_BENIGN_DEFAULT[a] for a in range(5)])
    atk_rew = np.sum([np.sum((acts == a) & (y_bin == 1)) * (-COST_ATTACK_DEFAULT[a]) for a in range(5)])
    net_ben = atk_rew - ben_pen
    blk_fpr = (b_blk / tot_b * 100.0) if tot_b > 0 else 0.0
    quar_fpr = (b_quar / tot_b * 100.0) if tot_b > 0 else 0.0
    return net_ben, blk_fpr, quar_fpr, np.sum(veto_mask)

hyb_net_bal, hyb_blk_bal, hyb_quar_bal, veto_cnt_bal = eval_hybrid(levels_bal, preds_bal, conf_bal, y_bin_bal)
hyb_net_atk, hyb_blk_atk, hyb_quar_atk, veto_cnt_atk = eval_hybrid(levels_atk, preds_atk, conf_atk, y_bin_atk)
hyb_comb = 0.5 * (hyb_net_bal + hyb_net_atk)
print(f"P_hybrid: Combined Net = {hyb_comb:+,.0f} OCU, Flood Block FPR = {hyb_blk_atk:.2f}% (Vetoed {veto_cnt_atk} flows)", flush=True)

# (iii) Full 2^4 = 16 Ablation of {c_conf, c_anom, c_trust, c_topo}
W = 100
n_b_bal = len(y_bin_bal) // W
n_b_atk = len(y_bin_atk) // W

c_conf_b_bal = np.array([np.mean((conf_bal[b*W:(b+1)*W] >= 0.90) & (preds_bal[b*W:(b+1)*W] != benign_idx)) >= 0.50 for b in range(n_b_bal)])
c_anom_b_bal = np.array([np.mean(s_bal[b*W:(b+1)*W] >= 0.50) >= 0.50 for b in range(n_b_bal)])
c_trust_b_bal = np.array([np.mean(trust_bal[b*W:(b+1)*W] <= 60.0) >= 0.50 for b in range(n_b_bal)])
c_topo_b_bal = np.array([np.mean(R_bal[b*W:(b+1)*W] >= 0.42) >= 0.50 for b in range(n_b_bal)])

c_conf_b_atk = np.array([np.mean((conf_atk[b*W:(b+1)*W] >= 0.90) & (preds_atk[b*W:(b+1)*W] != benign_idx)) >= 0.50 for b in range(n_b_atk)])
c_anom_b_atk = np.array([np.mean(s_atk[b*W:(b+1)*W] >= 0.50) >= 0.50 for b in range(n_b_atk)])
c_trust_b_atk = np.array([np.mean(trust_atk[b*W:(b+1)*W] <= 60.0) >= 0.50 for b in range(n_b_atk)])
c_topo_b_atk = np.array([np.mean(R_atk[b*W:(b+1)*W] >= 0.42) >= 0.50 for b in range(n_b_atk)])

signals_dict_bal = {'c_conf': c_conf_b_bal, 'c_anom': c_anom_b_bal, 'c_trust': c_trust_b_bal, 'c_topo': c_topo_b_bal}
signals_dict_atk = {'c_conf': c_conf_b_atk, 'c_anom': c_anom_b_atk, 'c_trust': c_trust_b_atk, 'c_topo': c_topo_b_atk}

sig_names = ['c_conf', 'c_anom', 'c_trust', 'c_topo']
ablation_rows = []

for r in range(5):
    for subset in itertools.combinations(sig_names, r):
        sub_name = '+'.join(subset) if len(subset) > 0 else 'None'
        
        # Build S
        S_bal_b = np.sum([signals_dict_bal[k] for k in subset], axis=0) if len(subset) > 0 else np.zeros(n_b_bal, dtype=int)
        S_atk_b = np.sum([signals_dict_atk[k] for k in subset], axis=0) if len(subset) > 0 else np.zeros(n_b_atk, dtype=int)
        
        # Assign levels
        def S_to_levels(S_b, trust_w, R_w, y_bin):
            n_b = len(S_b)
            lvls = np.zeros(len(y_bin), dtype=int)
            for b in range(n_b):
                idx = np.arange(b*W, (b+1)*W)
                mT = np.mean(trust_w[idx])
                mR = np.mean(R_w[idx])
                s_val = S_b[b]
                if s_val == 0: l = 0
                elif s_val == 1: l = 1
                elif s_val == 2: l = 2
                elif s_val >= 3 and mT > 20.0: l = 3
                elif s_val >= 3 and mT <= 20.0 and mR < 0.75: l = 4
                else: l = 5
                lvls[idx] = l
            return lvls
            
        lvls_bal_sub = S_to_levels(S_bal_b, trust_bal, R_bal, y_bin_bal)
        lvls_atk_sub = S_to_levels(S_atk_b, trust_atk, R_atk, y_bin_atk)
        
        pi_p2 = [0, 1, 2, 3, 4, 4]
        res_p2 = evaluate_policy_mapping(pi_p2, lvls_bal_sub, y_bin_bal, lvls_atk_sub, y_bin_atk)
        
        ablation_rows.append({
            'active_components': sub_name,
            'num_components': len(subset),
            'has_conf': ('c_conf' in subset),
            'has_anom': ('c_anom' in subset),
            'has_trust': ('c_trust' in subset),
            'has_topo': ('c_topo' in subset),
            'balanced_net_ocu': res_p2['bal']['net_benefit'],
            'attack_heavy_net_ocu': res_p2['atk']['net_benefit'],
            'combined_net_ocu': res_p2['combined_net_benefit'],
            'balanced_block_fpr': res_p2['bal']['block_fpr'],
            'balanced_quar_fpr': res_p2['bal']['quarantine_fpr'],
            'attack_heavy_block_fpr': res_p2['atk']['block_fpr']
        })

df_abl = pd.DataFrame(ablation_rows).sort_values('combined_net_ocu', ascending=False).reset_index(drop=True)
df_abl.to_csv(RESULTS_DIR / "phase1_EC_component_ablation.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase1_EC_component_ablation.csv'}", flush=True)

# (vi) Learned Meta-Classifier (Logistic Regression & Small Decision Tree)
print("Evaluating Learned Meta-Classifier on 4 components...", flush=True)
# Feature matrix for 600 batches on balanced: [c_conf, c_anom, c_trust, c_topo]
X_meta_bal = np.column_stack([c_conf_b_bal, c_anom_b_bal, c_trust_b_bal, c_topo_b_bal])
# Ground truth batch attack label: 1 if batch attack share >= 0.50 else 0
y_batch_atk_bal = np.array([np.mean(y_bin_bal[b*W:(b+1)*W]) >= 0.50 for b in range(n_b_bal)]).astype(int)

# Logistic regression
lr_meta = LogisticRegression(random_state=42)
lr_meta.fit(X_meta_bal, y_batch_atk_bal)
lr_probs = lr_meta.predict_proba(X_meta_bal)[:, 1]
lr_auc = roc_auc_score(y_batch_atk_bal, lr_probs)

# Decision Tree
dt_meta = DecisionTreeClassifier(max_depth=3, random_state=42)
dt_meta.fit(X_meta_bal, y_batch_atk_bal)
dt_probs = dt_meta.predict_proba(X_meta_bal)[:, 1]
dt_auc = roc_auc_score(y_batch_atk_bal, dt_probs)

# XGBoost alone confidence AUC on batches
xgb_batch_conf = np.array([np.mean(conf_bal[b*W:(b+1)*W] * (preds_bal[b*W:(b+1)*W] != benign_idx)) for b in range(n_b_bal)])
xgb_batch_auc = roc_auc_score(y_batch_atk_bal, xgb_batch_conf)

meta_rows = [
    {'model': 'XGBoost Alone (Batch Mean Confidence)', 'batch_auc': round(float(xgb_batch_auc), 4), 'weights': '1.0 c_conf'},
    {'model': 'Logistic Regression Meta-Classifier', 'batch_auc': round(float(lr_auc), 4), 'weights': str([round(w, 3) for w in lr_meta.coef_[0]])},
    {'model': 'Decision Tree Meta-Classifier (depth=3)', 'batch_auc': round(float(dt_auc), 4), 'weights': 'Tree rules'},
    {'model': 'Heuristic Linear Posture Sum (S = sum c_k)', 'batch_auc': round(float(roc_auc_score(y_batch_atk_bal, np.sum(X_meta_bal, axis=1))), 4), 'weights': '[1, 1, 1, 1]'}
]
df_meta = pd.DataFrame(meta_rows)
df_meta.to_csv(RESULTS_DIR / "phase1_EC_meta_classifier.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase1_EC_meta_classifier.csv'}", flush=True)
print(df_meta.to_string(), flush=True)

# -----------------------------------------------------------------------------
# EXPERIMENT E-D: REALISTIC STREAMS + PREVALENCE SWEEP
# -----------------------------------------------------------------------------
print("\n=== RUNNING EXPERIMENT E-D: REALISTIC STREAMS & PREVALENCE SWEEP ===", flush=True)
prevalences = [0.001, 0.005, 0.01, 0.02, 0.05, 0.10, 0.25, 0.50, 0.75, 0.976]
benign_test_indices = np.where(y_test == benign_idx)[0]
attack_test_indices = np.where(y_test != benign_idx)[0]

total_stream_flows = 60000
rng_d = np.random.RandomState(42)

ed_rows = []

for prev in prevalences:
    n_atk = int(round(total_stream_flows * prev))
    n_ben = total_stream_flows - n_atk
    
    # Construct continuous time-ordered realistic stream:
    # Benign traffic is continuous background; attack flows arrive in bursts of random length 50-500
    b_replace = (n_ben > len(benign_test_indices))
    a_replace = (n_atk > len(attack_test_indices))
    b_pool = rng_d.choice(benign_test_indices, size=n_ben, replace=b_replace)
    a_pool = rng_d.choice(attack_test_indices, size=n_atk, replace=a_replace)
    
    # Segment attack into burst episodes
    atk_ptr = 0
    bursts = []
    while atk_ptr < n_atk:
        burst_len = rng_d.randint(50, 501)
        actual_len = min(burst_len, n_atk - atk_ptr)
        bursts.append(a_pool[atk_ptr : atk_ptr + actual_len])
        atk_ptr += actual_len
        
    # Interleave bursts into benign background at random start positions
    stream_flows = np.zeros(total_stream_flows, dtype=int)
    is_atk_stream = np.zeros(total_stream_flows, dtype=int)
    
    # Pick insertion points for bursts
    n_bursts = len(bursts)
    if n_bursts > 0:
        insert_points = np.sort(rng_d.choice(total_stream_flows - 500, size=n_bursts, replace=False))
        occupied = np.zeros(total_stream_flows, dtype=bool)
        for ip, burst in zip(insert_points, bursts):
            blen = len(burst)
            # Find next free slot
            start = ip
            while start + blen <= total_stream_flows and np.any(occupied[start:start+blen]):
                start += 1
            if start + blen <= total_stream_flows:
                stream_flows[start:start+blen] = burst
                is_atk_stream[start:start+blen] = 1
                occupied[start:start+blen] = True
                
        # Fill remaining slots with benign traffic
        free_slots = np.where(~occupied)[0]
        n_free = len(free_slots)
        b_replace_free = (n_free > len(benign_test_indices))
        stream_flows[free_slots] = rng_d.choice(benign_test_indices, size=n_free, replace=b_replace_free)
    else:
        stream_flows = rng_d.choice(benign_test_indices, size=total_stream_flows, replace=(total_stream_flows > len(benign_test_indices)))
        
    y_stream = np.array(y_test[stream_flows])
    y_bin_stream = is_atk_stream
    
    # Run pipeline on this realistic stream
    s_str, conf_str, preds_str, R_str, trust_str = compute_signals(
        X_test_scaled, stream_flows, y_stream, benign_idx, if_model, p5, p95, seed=42
    )
    lvls_str = assign_levels(s_str, conf_str, preds_str, R_str, trust_str, benign_idx)
    
    # Level occupancy and attack density
    n_b = total_stream_flows // W
    densities_per_lvl = []
    occupancies = []
    for l in range(6):
        mask_l = (lvls_str == l)
        tot_l = np.sum(mask_l)
        atk_l = np.sum(mask_l & (y_bin_stream == 1))
        dens = (atk_l / tot_l * 100.0) if tot_l > 0 else 0.0
        occ = (tot_l / total_stream_flows * 100.0)
        densities_per_lvl.append(dens)
        occupancies.append(occ)
        
    # Evaluate P1 and P2-tier
    def eval_stream_policy(pi, lvls, y_bin):
        acts = np.array([pi[l] for l in lvls])
        ben_pen = np.sum([np.sum((acts == a) & (y_bin == 0)) * COST_BENIGN_DEFAULT[a] for a in range(5)])
        atk_rew = np.sum([np.sum((acts == a) & (y_bin == 1)) * (-COST_ATTACK_DEFAULT[a]) for a in range(5)])
        b_blk = np.sum((acts == 4) & (y_bin == 0))
        tot_b = np.sum(y_bin == 0)
        return atk_rew - ben_pen, (b_blk / tot_b * 100.0) if tot_b > 0 else 0.0
        
    pi_p1 = [0, 1, 2, 3, 3, 4]
    pi_p2_tier = [0, 1, 2, 3, 4, 4]
    pi_p_opt = [0, 0, 2, 2, 4, 4]
    
    nb_p1, blk_p1 = eval_stream_policy(pi_p1, lvls_str, y_bin_stream)
    nb_p2_tier, blk_p2_tier = eval_stream_policy(pi_p2_tier, lvls_str, y_bin_stream)
    nb_p_opt, blk_p_opt = eval_stream_policy(pi_p_opt, lvls_str, y_bin_stream)
    nb_xgb, blk_xgb, _ = eval_pure_xgb(preds_str, conf_str, y_bin_stream)
    
    row_ed = {
        'attack_prevalence_pct': round(prev * 100, 2),
        'P1_net_benefit': nb_p1,
        'P2_tier_net_benefit': nb_p2_tier,
        'P_opt_net_benefit': nb_p_opt,
        'P_XGB_net_benefit': nb_xgb,
        'P1_block_fpr': round(blk_p1, 3),
        'P2_tier_block_fpr': round(blk_p2_tier, 3),
        'P_XGB_block_fpr': round(blk_xgb, 3),
        'L0_occ_pct': round(occupancies[0], 2),
        'L1_occ_pct': round(occupancies[1], 2),
        'L2_occ_pct': round(occupancies[2], 2),
        'L3_occ_pct': round(occupancies[3], 2),
        'L4_occ_pct': round(occupancies[4], 2),
        'L5_occ_pct': round(occupancies[5], 2),
        'L0_atk_density': round(densities_per_lvl[0], 2),
        'L1_atk_density': round(densities_per_lvl[1], 2),
        'L2_atk_density': round(densities_per_lvl[2], 2),
        'L3_atk_density': round(densities_per_lvl[3], 2),
        'L4_atk_density': round(densities_per_lvl[4], 2),
        'p2_tier_beats_p1': (nb_p2_tier > nb_p1)
    }
    ed_rows.append(row_ed)
    print(f"Prevalence {prev*100:5.2f}%: P2-tier NB={nb_p2_tier:+d}, P1 NB={nb_p1:+d}, P_opt NB={nb_p_opt:+d}, P_XGB NB={nb_xgb:+d} (P2-tier beats P1: {nb_p2_tier > nb_p1})", flush=True)

df_ed = pd.DataFrame(ed_rows)
df_ed.to_csv(RESULTS_DIR / "phase1_ED_realistic_prevalence_sweep.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase1_ED_realistic_prevalence_sweep.csv'}", flush=True)
print("=== EXPERIMENTS E-C AND E-D COMPLETE ===", flush=True)
