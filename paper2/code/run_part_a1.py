import os
import json
import joblib
import numpy as np
from sklearn.metrics import roc_auc_score

print("=== PART A.1: VERIFY CONTAMINATION ===")

# 1. Read backend/ml_model/unknown_attack_detector.py lines 60-80
detector_path = "backend/ml_model/unknown_attack_detector.py"
with open(detector_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print("\n--- backend/ml_model/unknown_attack_detector.py Lines 60-80 ---")
for i in range(59, min(80, len(lines))):
    print(f"Line {i+1:2d}: {lines[i].rstrip()}")

# Exact line checking for 'BENIGN' and fallback
print("\n--- Extracted Lines ---")
line_check = lines[66].strip()  # benign_idx = ...
line_fallback = lines[74].strip() # X_benign = X_train
print(f"Check line (Line 67): {line_check}")
print(f"Fallback line (Line 75): {line_fallback}")

# 2. Load 10,000 random attack samples and 10,000 random benign samples from audit/lofo/cache/X_test_scaled.npy using y_test
print("\n--- Loading test set and labels ---")
X_test = np.load("audit/lofo/cache/X_test_scaled.npy")
y_test = np.load("audit/lofo/cache/y_test.npy")

with open("audit/lofo/cache/class_names.json", "r") as f:
    class_names = json.load(f)

benign_idx = class_names.index("BenignTraffic")
print(f"Benign class: 'BenignTraffic' at index {benign_idx}")

attack_indices_all = np.where(y_test != benign_idx)[0]
benign_indices_all = np.where(y_test == benign_idx)[0]

print(f"Total test samples: {len(y_test):,}")
print(f"Total attack samples: {len(attack_indices_all):,}")
print(f"Total benign samples: {len(benign_indices_all):,}")

np.random.seed(42)
sampled_attack_idx = np.random.choice(attack_indices_all, size=10000, replace=False)
# Note: benign in test might be fewer or more than 10,000, let's check:
if len(benign_indices_all) < 10000:
    print(f"Warning: Only {len(benign_indices_all)} benign samples in test set! Using replacement=True or all available.")
    sampled_benign_idx = np.random.choice(benign_indices_all, size=10000, replace=True)
else:
    sampled_benign_idx = np.random.choice(benign_indices_all, size=10000, replace=False)

eval_idx = np.concatenate([sampled_attack_idx, sampled_benign_idx])
y_eval = np.concatenate([np.ones(10000, dtype=int), np.zeros(10000, dtype=int)]) # 1 = attack, 0 = benign

X_eval = X_test[eval_idx]

# 3. Score both with backend/ml_model/saved_models/isolation_forest.pkl
print("\n--- Scoring with published (contaminated) Isolation Forest ---")
if_model = joblib.load("backend/ml_model/saved_models/isolation_forest.pkl")
raw_scores = if_model.score_samples(X_eval)
anomaly_scores = np.clip(0.5 - raw_scores, 0, 1)

anom_attack = anomaly_scores[:10000]
anom_benign = anomaly_scores[10000:]

mean_attack = float(np.mean(anom_attack))
mean_benign = float(np.mean(anom_benign))

auc_attack = float(roc_auc_score(y_eval, anomaly_scores))
auc_benign = float(roc_auc_score(1 - y_eval, anomaly_scores))

pct_attack_above_90 = float(np.mean(anom_attack >= 0.90) * 100)
pct_benign_above_90 = float(np.mean(anom_benign >= 0.90) * 100)

print(f"Mean anomaly score (Attack): {mean_attack:.4f}")
print(f"Mean anomaly score (Benign): {mean_benign:.4f}")
print(f"AUC (Attack as anomaly, positive=1): {auc_attack:.4f}")
print(f"AUC (Benign as positive=1): {auc_benign:.4f}")
print(f"% Attack above tau=0.90: {pct_attack_above_90:.2f}%")
print(f"% Benign above tau=0.90: {pct_benign_above_90:.2f}%")

if auc_attack >= 0.5:
    print("\n[STOP TRIGGER] AUC >= 0.5. The bug is not inverted as expected.")
else:
    print(f"\n[CONFIRMED] Contamination verified! benign_mean ({mean_benign:.4f}) > attack_mean ({mean_attack:.4f}), AUC = {auc_attack:.4f} (< 0.5).")
