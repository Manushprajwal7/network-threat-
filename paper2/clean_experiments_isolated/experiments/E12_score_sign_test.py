# experiments/E12_score_sign_test.py
"""
E12: Fast unit test for Isolation Forest score_samples sign convention and anomaly monotonicity.
Verifies that scikit-learn's score_samples is correctly negated and positively correlates with attack labels.
"""
import os
import json
import time
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import roc_auc_score
from sklearn.ensemble import IsolationForest

from common import CONFIG, load_dataset_references

def run_e12():
    print("=== RUNNING E12: FAST UNIT TEST FOR SCORE_SAMPLES SIGN CONVENTION ===")
    t0 = time.time()
    
    class_names, benign_idx, X_train_scaled, y_train, X_test_scaled, y_test = load_dataset_references()
    
    # 1. Take a small training sample of clean benign data (5,000 flows)
    benign_train_indices = np.where(y_train == benign_idx)[0]
    rng = np.random.RandomState(42)
    clean_idx = np.sort(rng.choice(benign_train_indices, size=5000, replace=False))
    X_train_clean = np.array(X_train_scaled[clean_idx], dtype=np.float32)
    
    # Fit IF
    if_model = IsolationForest(n_estimators=100, max_samples=256, contamination=0.05, random_state=42, n_jobs=-1)
    if_model.fit(X_train_clean)
    
    # 2. Sample 2,000 benign and 2,000 attack test flows
    test_benign_idx = np.where(y_test == benign_idx)[0]
    test_attack_idx = np.where(y_test != benign_idx)[0]
    
    sample_b = np.sort(rng.choice(test_benign_idx, size=2000, replace=False))
    sample_a = np.sort(rng.choice(test_attack_idx, size=2000, replace=False))
    
    test_idx = np.concatenate([sample_b, sample_a])
    X_test_sample = np.array(X_test_scaled[test_idx], dtype=np.float32)
    y_test_sample = np.array(y_test[test_idx])
    y_bin = (y_test_sample != benign_idx).astype(int)
    
    # 3. Evaluate raw score_samples vs negated score_samples
    raw_scores = if_model.score_samples(X_test_sample)
    neg_scores = -raw_scores # Our anomaly score
    
    mean_raw_benign = np.mean(raw_scores[y_bin == 0])
    mean_raw_attack = np.mean(raw_scores[y_bin == 1])
    
    mean_neg_benign = np.mean(neg_scores[y_bin == 0])
    mean_neg_attack = np.mean(neg_scores[y_bin == 1])
    
    corr_raw, _ = stats.pearsonr(raw_scores, y_bin)
    corr_neg, _ = stats.pearsonr(neg_scores, y_bin)
    
    auc_raw = roc_auc_score(y_bin, raw_scores)
    auc_neg = roc_auc_score(y_bin, neg_scores)
    
    print(f"Scikit-learn raw score_samples: Benign Mean = {mean_raw_benign:.4f}, Attack Mean = {mean_raw_attack:.4f}")
    print(f"Negated anomaly score (-score_samples): Benign Mean = {mean_neg_benign:.4f}, Attack Mean = {mean_neg_attack:.4f}")
    print(f"Pearson Correlation with Attack Label: Raw = {corr_raw:.4f}, Negated = {corr_neg:.4f}")
    print(f"ROC AUC: Raw = {auc_raw:.4f}, Negated = {auc_neg:.4f}")
    
    # Assertions
    assert mean_raw_benign > mean_raw_attack, "FATAL: In raw scikit-learn, benign must have higher score than attack"
    assert mean_neg_attack > mean_neg_benign, "FATAL: In negated anomaly score, attack must have higher score than benign"
    assert corr_neg > 0.0, f"FATAL: Negated score correlation must be positive, got {corr_neg}"
    assert auc_neg > 0.80, f"FATAL: Negated score AUC must be > 0.80, got {auc_neg}"
    
    results = {
        "status": "PASSED",
        "mean_raw_benign": float(mean_raw_benign),
        "mean_raw_attack": float(mean_raw_attack),
        "mean_neg_benign": float(mean_neg_benign),
        "mean_neg_attack": float(mean_neg_attack),
        "pearson_corr_negated": float(corr_neg),
        "roc_auc_negated": float(auc_neg),
        "elapsed_s": round(time.time() - t0, 2)
    }
    
    out_json = "experiments/outputs/E12_score_sign_test.json"
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"\nUNIT TEST PASSED in {results['elapsed_s']}s! Saved to {out_json}")

if __name__ == "__main__":
    run_e12()
