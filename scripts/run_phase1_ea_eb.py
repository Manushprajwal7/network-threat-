# scripts/run_phase1_ea_eb.py
"""
PHASE 1 - EXPERIMENTS E-A and E-B
E-A: Sign-flip control (Contaminated vs Clean IF, M=100,200 across 10 seeds; raw AUC, negated AUC, KS D, per-family AUC; baselines: OCSVM, LOF, ECOD/Mahalanobis, Autoencoder).
E-B: Contamination dose-response curve (10 contamination levels x 10 seeds; raw AUC, negated AUC with 95% CIs; inversion point).
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_auc_score
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from sklearn.decomposition import PCA
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

from experiments.common import load_dataset_references, CONFIG

print("Loading dataset references...")
class_names, benign_idx, X_train_scaled, y_train, X_test_scaled, y_test = load_dataset_references()

# Family mapping
family_mapping = {
    'DDoS': ['DDoS-ACK_Fragmentation', 'DDoS-HTTP_Flood', 'DDoS-ICMP_Flood', 'DDoS-ICMP_Fragmentation',
             'DDoS-PSHACK_Flood', 'DDoS-RSTFINFlood', 'DDoS-SYN_Flood', 'DDoS-SlowLoris',
             'DDoS-SynonymousIP_Flood', 'DDoS-TCP_Flood', 'DDoS-UDP_Flood', 'DDoS-UDP_Fragmentation'],
    'DoS': ['DoS-HTTP_Flood', 'DoS-SYN_Flood', 'DoS-TCP_Flood', 'DoS-UDP_Flood'],
    'Mirai': ['Mirai-greeth_flood', 'Mirai-greip_flood', 'Mirai-udpplain'],
    'Spoofing': ['DNS_Spoofing', 'MITM-ArpSpoofing'],
    'Recon': ['Recon-HostDiscovery', 'Recon-OSScan', 'Recon-PingSweep', 'Recon-PortScan', 'VulnerabilityScan'],
    'Web': ['CommandInjection', 'SqlInjection', 'Uploading_Attack', 'XSS', 'BrowserHijacking'],
    'BruteForce': ['DictionaryBruteForce'],
    'Malware': ['Backdoor_Malware'],
    'Benign': ['BenignTraffic']
}
class_to_family = {}
for fam, clist in family_mapping.items():
    for c in clist:
        class_to_family[c] = fam

# 1. Prepare evaluation slice from test set (60,000 flows: representative test slice)
rng_eval = np.random.RandomState(42)
test_indices = np.arange(len(y_test))
eval_indices = rng_eval.choice(test_indices, size=60000, replace=False)
X_eval = np.array(X_test_scaled[eval_indices], dtype=np.float32)
y_eval = np.array(y_test[eval_indices])
y_bin_eval = (y_eval != benign_idx).astype(int)

# Pre-compute benign training indices and full training pool
benign_train_indices = np.where(y_train == benign_idx)[0]
full_train_indices = np.arange(len(y_train))

# -----------------------------------------------------------------------------
# EXPERIMENT E-A: SIGN-FLIP CONTROL & BASELINES
# -----------------------------------------------------------------------------
print("\n=== RUNNING EXPERIMENT E-A: SIGN-FLIP CONTROL ===")
seeds = [42, 43, 44, 45, 46, 47, 48, 49, 50, 51]
ea_rows = []

for m_trees in [100, 200]:
    for model_type in ["Contaminated", "Clean"]:
        raw_aucs = []
        neg_aucs = []
        ks_stats = []
        family_aucs = {fam: [] for fam in ['DDoS', 'DoS', 'Mirai', 'Spoofing', 'Recon', 'Web', 'BruteForce']}
        
        for s in seeds:
            rng_s = np.random.RandomState(s)
            if model_type == "Clean":
                sub_idx = rng_s.choice(benign_train_indices, size=20000, replace=False)
            else: # Contaminated (train on raw training split: 97.64% attack)
                sub_idx = rng_s.choice(full_train_indices, size=20000, replace=False)
                
            X_sub = np.array(X_train_scaled[sub_idx], dtype=np.float32)
            clf = IsolationForest(n_estimators=m_trees, random_state=s, n_jobs=-1, contamination=0.05)
            clf.fit(X_sub)
            
            # Score samples: in scikit-learn, score_samples is negative for anomalies
            scores = clf.score_samples(X_eval)
            raw_anom = -scores  # conventional negated score: higher = more anomalous
            # scikit-learn raw score: higher = more nominal (inlier)
            
            # Raw ROC AUC (using scikit-learn raw score as anomaly predictor)
            # If raw score is used as anomaly predictor:
            auc_raw = roc_auc_score(y_bin_eval, scores)
            # If negated score (-score) is used:
            auc_neg = roc_auc_score(y_bin_eval, raw_anom)
            
            # KS statistic between benign and attack score distributions
            b_scores = raw_anom[y_bin_eval == 0]
            a_scores = raw_anom[y_bin_eval == 1]
            ks_res = stats.ks_2samp(b_scores, a_scores)
            
            raw_aucs.append(auc_raw)
            neg_aucs.append(auc_neg)
            ks_stats.append(ks_res.statistic)
            
            # Per-family AUCs (each family vs benign)
            for fam in family_aucs.keys():
                fam_classes = [class_names.index(c) for c in family_mapping[fam] if c in class_names]
                fam_mask = np.isin(y_eval, fam_classes)
                if np.sum(fam_mask) >= 5:
                    eval_mask = (y_bin_eval == 0) | fam_mask
                    y_sub = (y_eval[eval_mask] != benign_idx).astype(int)
                    sc_sub = raw_anom[eval_mask]
                    family_aucs[fam].append(roc_auc_score(y_sub, sc_sub))
                    
        row = {
            'model_type': model_type,
            'trees_M': m_trees,
            'mean_raw_auc': round(float(np.mean(raw_aucs)), 4),
            'std_raw_auc': round(float(np.std(raw_aucs)), 4),
            'mean_negated_auc': round(float(np.mean(neg_aucs)), 4),
            'std_negated_auc': round(float(np.std(neg_aucs)), 4),
            'mean_ks_D': round(float(np.mean(ks_stats)), 4),
            'std_ks_D': round(float(np.std(ks_stats)), 4)
        }
        for fam, f_list in family_aucs.items():
            row[f'{fam}_auc'] = round(float(np.mean(f_list)), 4) if len(f_list) > 0 else np.nan
        ea_rows.append(row)
        print(f"E-A {model_type} M={m_trees}: Raw AUC={row['mean_raw_auc']}, Negated AUC={row['mean_negated_auc']}, KS D={row['mean_ks_D']}")

df_ea = pd.DataFrame(ea_rows)
df_ea.to_csv(RESULTS_DIR / "phase1_EA_sign_flip_control.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase1_EA_sign_flip_control.csv'}")

# --- BASELINES ON CLEAN BENIGN TRAFFIC (OCSVM, LOF, PCA/Mahalanobis, Autoencoder) ---
print("\n--- Running Anomaly Detection Baselines on Clean Benign Set ---")
baseline_rows = []

# Fit on clean benign subset
rng_base = np.random.RandomState(42)
b_idx_5k = rng_base.choice(benign_train_indices, size=5000, replace=False)
b_idx_20k = rng_base.choice(benign_train_indices, size=20000, replace=False)
X_b_5k = np.array(X_train_scaled[b_idx_5k], dtype=np.float32)
X_b_20k = np.array(X_train_scaled[b_idx_20k], dtype=np.float32)

# 1. One-Class SVM (nu=0.05, rbf)
print("Evaluating One-Class SVM (5k benign fit)...")
ocsvm = OneClassSVM(kernel='rbf', gamma='scale', nu=0.05)
ocsvm.fit(X_b_5k)
ocsvm_scores = -ocsvm.decision_function(X_eval) # higher = more anomalous
auc_ocsvm = roc_auc_score(y_bin_eval, ocsvm_scores)
ks_ocsvm = stats.ks_2samp(ocsvm_scores[y_bin_eval == 0], ocsvm_scores[y_bin_eval == 1]).statistic
baseline_rows.append({
    'detector': 'One-Class SVM (RBF, nu=0.05)',
    'training_data': 'Clean Benign (5k)',
    'roc_auc': round(float(auc_ocsvm), 4),
    'ks_D': round(float(ks_ocsvm), 4),
    'status': 'Baseline Anomaly Detector'
})

# 2. Local Outlier Factor (novelty=True)
print("Evaluating Local Outlier Factor (5k benign fit)...")
lof = LocalOutlierFactor(n_neighbors=20, novelty=True, contamination=0.05, n_jobs=-1)
lof.fit(X_b_5k)
lof_scores = -lof.decision_function(X_eval)
auc_lof = roc_auc_score(y_bin_eval, lof_scores)
ks_lof = stats.ks_2samp(lof_scores[y_bin_eval == 0], lof_scores[y_bin_eval == 1]).statistic
baseline_rows.append({
    'detector': 'Local Outlier Factor (k=20)',
    'training_data': 'Clean Benign (5k)',
    'roc_auc': round(float(auc_lof), 4),
    'ks_D': round(float(ks_lof), 4),
    'status': 'Baseline Anomaly Detector'
})

# 3. PCA Reconstruction / Diagonal Mahalanobis Distance (ECOD surrogate)
print("Evaluating PCA Reconstruction Error (20k benign fit)...")
pca = PCA(n_components=10, random_state=42)
pca.fit(X_b_20k)
X_recon = pca.inverse_transform(pca.transform(X_eval))
recon_err = np.sum((X_eval - X_recon)**2, axis=1)
auc_pca = roc_auc_score(y_bin_eval, recon_err)
ks_pca = stats.ks_2samp(recon_err[y_bin_eval == 0], recon_err[y_bin_eval == 1]).statistic
baseline_rows.append({
    'detector': 'PCA Reconstruction Error (n_comp=10)',
    'training_data': 'Clean Benign (20k)',
    'roc_auc': round(float(auc_pca), 4),
    'ks_D': round(float(ks_pca), 4),
    'status': 'Baseline Anomaly Detector'
})

# 4. Diagonal Mahalanobis Distance
mu = np.mean(X_b_20k, axis=0)
std = np.std(X_b_20k, axis=0) + 1e-6
mahal = np.sqrt(np.sum(((X_eval - mu) / std)**2, axis=1))
auc_mahal = roc_auc_score(y_bin_eval, mahal)
ks_mahal = stats.ks_2samp(mahal[y_bin_eval == 0], mahal[y_bin_eval == 1]).statistic
baseline_rows.append({
    'detector': 'Diagonal Mahalanobis Distance',
    'training_data': 'Clean Benign (20k)',
    'roc_auc': round(float(auc_mahal), 4),
    'ks_D': round(float(ks_mahal), 4),
    'status': 'Baseline Anomaly Detector'
})

df_base = pd.DataFrame(baseline_rows)
df_base.to_csv(RESULTS_DIR / "phase1_EA_baselines.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase1_EA_baselines.csv'}")
print(df_base.to_string())

# -----------------------------------------------------------------------------
# EXPERIMENT E-B: CONTAMINATION DOSE-RESPONSE CURVE
# -----------------------------------------------------------------------------
print("\n=== RUNNING EXPERIMENT E-B: CONTAMINATION DOSE-RESPONSE ===")
fractions = [0.0, 0.001, 0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.9764]
attack_train_indices = np.where(y_train != benign_idx)[0]

dose_rows = []
total_train_samples = 20000

for frac in fractions:
    n_atk = int(round(total_train_samples * frac))
    n_ben = total_train_samples - n_atk
    
    raw_aucs = []
    neg_aucs = []
    ks_stats = []
    
    for s in seeds:
        rng_s = np.random.RandomState(s)
        idx_b = rng_s.choice(benign_train_indices, size=n_ben, replace=False) if n_ben > 0 else np.array([], dtype=int)
        idx_a = rng_s.choice(attack_train_indices, size=n_atk, replace=False) if n_atk > 0 else np.array([], dtype=int)
        sub_idx = np.concatenate([idx_b, idx_a])
        rng_s.shuffle(sub_idx)
        
        X_sub = np.array(X_train_scaled[sub_idx], dtype=np.float32)
        clf = IsolationForest(n_estimators=100, random_state=s, n_jobs=-1, contamination=0.05)
        clf.fit(X_sub)
        
        scores = clf.score_samples(X_eval)
        raw_anom = -scores
        
        auc_r = roc_auc_score(y_bin_eval, scores)   # raw scikit-learn inlier score as attack predictor
        auc_n = roc_auc_score(y_bin_eval, raw_anom) # negated score (-scores) as attack predictor
        ks_d = stats.ks_2samp(raw_anom[y_bin_eval == 0], raw_anom[y_bin_eval == 1]).statistic
        
        raw_aucs.append(auc_r)
        neg_aucs.append(auc_n)
        ks_stats.append(ks_d)
        
    mean_neg = float(np.mean(neg_aucs))
    std_neg = float(np.std(neg_aucs))
    ci95_low = mean_neg - 1.96 * std_neg / np.sqrt(len(seeds))
    ci95_high = mean_neg + 1.96 * std_neg / np.sqrt(len(seeds))
    
    dose_rows.append({
        'contamination_fraction': frac,
        'contamination_pct': round(frac * 100, 2),
        'mean_negated_auc': round(mean_neg, 4),
        'std_negated_auc': round(std_neg, 4),
        'ci95_lower': round(ci95_low, 4),
        'ci95_upper': round(ci95_high, 4),
        'mean_raw_auc': round(float(np.mean(raw_aucs)), 4),
        'mean_ks_D': round(float(np.mean(ks_stats)), 4)
    })
    print(f"Contamination {frac*100:5.2f}%: Negated AUC = {mean_neg:.4f} [ {ci95_low:.4f}, {ci95_high:.4f} ], Raw AUC = {np.mean(raw_aucs):.4f}")

df_dose = pd.DataFrame(dose_rows)
df_dose.to_csv(RESULTS_DIR / "phase1_EB_dose_response.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase1_EB_dose_response.csv'}")

# Find inversion point (where negated AUC crosses 0.50)
inversion_pt = df_dose[df_dose['mean_negated_auc'] < 0.50].iloc[0]['contamination_pct']
print(f"Empirical Inversion Point: between {df_dose[df_dose['mean_negated_auc'] >= 0.50].iloc[-1]['contamination_pct']}% and {inversion_pt}% contamination")
print("=== EXPERIMENTS E-A AND E-B COMPLETE ===")
