import os
import json
import time
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_auc_score, roc_curve

print("=== EXPERIMENT 1: CONTROLLED ISOLATION FOREST COMPARISON ===")
print("Evaluating Contaminated vs Clean models at equal tree counts (M=100, M=200)")

# 1. Load class names
with open("audit/lofo/cache/class_names.json", "r") as f:
    class_names = json.load(f)

benign_idx = class_names.index("BenignTraffic")
print(f"Benign class: 'BenignTraffic' at index {benign_idx}")

# 2. Load training data (mmap)
X_train_scaled = np.load("audit/lofo/cache/X_train_scaled.npy", mmap_mode="r")
y_train = np.load("audit/lofo/cache/y_train.npy", mmap_mode="r")
print(f"Loaded X_train_scaled: {X_train_scaled.shape}, y_train: {y_train.shape}")

# Find benign indices in train
benign_train_indices = np.where(y_train == benign_idx)[0]
print(f"Total benign training flows available: {len(benign_train_indices):,} ({len(benign_train_indices)/len(y_train)*100:.2f}%)")

# Sample 20,000 clean benign samples (seed 42)
rng = np.random.RandomState(42)
clean_sample_idx = rng.choice(benign_train_indices, size=20000, replace=False)
X_train_clean = np.array(X_train_scaled[clean_sample_idx])

# Sample 20,000 contaminated samples (simulating fallback random slice from train, 97.5% attack)
contam_sample_idx = rng.choice(len(y_train), size=20000, replace=False)
X_train_contam = np.array(X_train_scaled[contam_sample_idx])
contam_attack_pct = np.mean(y_train[contam_sample_idx] != benign_idx) * 100
print(f"Contaminated training slice attack percentage: {contam_attack_pct:.2f}% (simulating published bug)")

# 3. Load test data
X_test_scaled = np.load("audit/lofo/cache/X_test_scaled.npy", mmap_mode="r")
y_test = np.load("audit/lofo/cache/y_test.npy", mmap_mode="r")

# Take the standard 60,000 evaluation window from test set
eval_idx = rng.choice(len(y_test), size=60000, replace=False)
X_eval = np.array(X_test_scaled[eval_idx])
y_eval = np.array(y_test[eval_idx])
y_eval_binary = (y_eval != benign_idx).astype(int)

n_eval_benign = np.sum(y_eval_binary == 0)
n_eval_attack = np.sum(y_eval_binary == 1)
print(f"Evaluation window: {len(y_eval):,} flows ({n_eval_attack:,} attack, {n_eval_benign:,} benign, {n_eval_attack/len(y_eval)*100:.2f}% attack)")

# 4. Train and evaluate 4 models:
# (1) Contaminated M=100
# (2) Contaminated M=200
# (3) Clean M=100
# (4) Clean M=200

models_to_test = [
    ("Contaminated (M=100)", X_train_contam, 100, 0.05),
    ("Contaminated (M=200)", X_train_contam, 200, 0.05),
    ("Repaired Clean (M=100)", X_train_clean, 100, 0.05),
    ("Repaired Clean (M=200)", X_train_clean, 200, 0.05),
]

results = []

for name, X_tr, n_est, contam in models_to_test:
    t0 = time.time()
    model = IsolationForest(
        n_estimators=n_est,
        max_samples=256,
        contamination=contam,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_tr)
    fit_time = time.time() - t0
    
    # Anomaly scores on eval: -score_samples gives higher value for more anomalous
    raw_scores = -model.score_samples(X_eval)
    
    # AUC: higher score should predict attack (1)
    auc = roc_auc_score(y_eval_binary, raw_scores)
    
    # Scores by class
    scores_benign = raw_scores[y_eval_binary == 0]
    scores_attack = raw_scores[y_eval_binary == 1]
    
    # Kolmogorov-Smirnov 2-sample test
    ks_res = stats.ks_2samp(scores_benign, scores_attack)
    ks_stat = ks_res.statistic
    ks_pval = ks_res.pvalue
    
    # Anomaly gap
    mean_benign = np.mean(scores_benign)
    mean_attack = np.mean(scores_attack)
    anomaly_gap = mean_attack - mean_benign
    
    # Correlation with binary label
    pearson_r, _ = stats.pearsonr(raw_scores, y_eval_binary)
    spearman_rho, _ = stats.spearmanr(raw_scores, y_eval_binary)
    
    # Linear quantile calibration: map benign 95th percentile to 0.90, benign min to 0.10
    p5_benign = np.percentile(scores_benign, 5)
    p95_benign = np.percentile(scores_benign, 95)
    
    # Scale scores: min-max calibrated
    cal_scores = np.clip((raw_scores - p5_benign) / (p95_benign - p5_benign + 1e-9) * 0.80 + 0.10, 0.0, 1.0)
    cal_benign_tail = np.mean(cal_scores[y_eval_binary == 0] >= 0.90) * 100.0
    cal_attack_tail = np.mean(cal_scores[y_eval_binary == 1] >= 0.90) * 100.0
    
    results.append({
        "Model": name,
        "Trees (M)": n_est,
        "Training Telemetry": "97.5% Contaminated" if "Contam" in name else "100% Clean Benign",
        "ROC AUC": round(auc, 4),
        "KS Statistic (D)": round(ks_stat, 4),
        "KS p-value": f"{ks_pval:.2e}",
        "Anomaly Gap": round(anomaly_gap, 4),
        "Benign Score Mean": round(mean_benign, 4),
        "Attack Score Mean": round(mean_attack, 4),
        "Benign Tail >= 0.90 (%)": round(cal_benign_tail, 2),
        "Attack Tail >= 0.90 (%)": round(cal_attack_tail, 2),
        "Pearson r": round(pearson_r, 4),
        "Spearman rho": round(spearman_rho, 4),
        "Fit Time (s)": round(fit_time, 2)
    })
    print(f"Done {name}: AUC={auc:.4f}, KS-D={ks_stat:.4f}, Gap={anomaly_gap:.4f}, Benign>=0.90={cal_benign_tail:.2f}%")

df_results = pd.DataFrame(results)
out_csv = "paper2/new_experiments/tab1_if_controlled.csv"
df_results.to_csv(out_csv, index=False)
print(f"\nSaved clean controlled IF comparison to {out_csv}")
print(df_results.to_string(index=False))
