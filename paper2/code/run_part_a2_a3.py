import os
import time
import json
import joblib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_curve, roc_auc_score

print("=== PART A.2 & A.3: ISOLATION FOREST REPAIR AND VERIFICATION ===")

# 1. Load class names and verify benign match
with open("audit/lofo/cache/class_names.json", "r") as f:
    class_names = json.load(f)

candidates = ["BenignTraffic", "Benign_Traffic", "BENIGN", "Benign"]
matched_benign_label = None
matched_benign_idx = -1
for cand in candidates:
    if cand in class_names:
        matched_benign_label = cand
        matched_benign_idx = class_names.index(cand)
        break

print(f"Matched benign label: '{matched_benign_label}' at index {matched_benign_idx}")

# 2. Check/load model
corrected_model_path = "backend/ml_model/saved_models/isolation_forest_corrected.pkl"
if os.path.exists(corrected_model_path):
    print("Loading existing corrected IF model...")
    if_corrected = joblib.load(corrected_model_path)
else:
    raise FileNotFoundError("Corrected model not found!")

# 3. Load test data and sample 10,000 attack and 10,000 benign
print("Loading X_test_scaled.npy and y_test.npy...")
X_test = np.load("audit/lofo/cache/X_test_scaled.npy", mmap_mode="r")
y_test = np.load("audit/lofo/cache/y_test.npy")

attack_indices_all = np.where(y_test != matched_benign_idx)[0]
benign_indices_all = np.where(y_test == matched_benign_idx)[0]

np.random.seed(42)
sampled_attack_idx = np.random.choice(attack_indices_all, size=10000, replace=False)
sampled_benign_idx = np.random.choice(benign_indices_all, size=10000, replace=False)

eval_idx = np.concatenate([sampled_attack_idx, sampled_benign_idx])
y_eval = np.concatenate([np.ones(10000, dtype=int), np.zeros(10000, dtype=int)]) # 1 = attack, 0 = benign

X_eval = np.array(X_test[eval_idx], dtype=np.float32)

# 4. Score with contaminated model (using published code: clip(0.5 - raw, 0, 1))
if_contaminated = joblib.load("backend/ml_model/saved_models/isolation_forest.pkl")
raw_contam = if_contaminated.score_samples(X_eval)
anom_contam = np.clip(0.5 - raw_contam, 0, 1)

mean_attack_contam = float(np.mean(anom_contam[:10000]))
mean_benign_contam = float(np.mean(anom_contam[10000:]))
auc_contam = float(roc_auc_score(y_eval, anom_contam))
pct_attack_90_contam = float(np.mean(anom_contam[:10000] >= 0.90) * 100)
pct_benign_90_contam = float(np.mean(anom_contam[10000:] >= 0.90) * 100)

# 5. Score with corrected model (Liu et al. anomaly score calibrated to benign 95th percentile = 0.90)
raw_corr = if_corrected.score_samples(X_eval)
s_corr = -raw_corr  # Liu et al. anomaly score
s_min = 0.4200
s_p95 = float(-if_corrected.offset_)  # exactly 0.55865

# Calibrated anomaly score
anom_corr = np.clip((s_corr - s_min) / (s_p95 - s_min) * 0.90, 0, 1)

mean_attack_corr = float(np.mean(anom_corr[:10000]))
mean_benign_corr = float(np.mean(anom_corr[10000:]))
auc_corr = float(roc_auc_score(y_eval, anom_corr))
pct_attack_90_corr = float(np.mean(anom_corr[:10000] >= 0.90) * 100)
pct_benign_90_corr = float(np.mean(anom_corr[10000:] >= 0.90) * 100)

print("\n--- RESULTS COMPARISON ---")
print(f"Contaminated: benign_mean={mean_benign_contam:.4f}, attack_mean={mean_attack_contam:.4f}, AUC={auc_contam:.4f}, benign>=0.90={pct_benign_90_contam:.2f}%, attack>=0.90={pct_attack_90_contam:.2f}%")
print(f"Corrected:    benign_mean={mean_benign_corr:.4f}, attack_mean={mean_attack_corr:.4f}, AUC={auc_corr:.4f}, benign>=0.90={pct_benign_90_corr:.2f}%, attack>=0.90={pct_attack_90_corr:.2f}%")
print(f"Anomaly gap (attack - benign): {mean_attack_corr - mean_benign_corr:.4f} (Target: >= 0.30)")

# Write CSV table
os.makedirs("paper2/tables", exist_ok=True)
csv_path = "paper2/tables/O2_A_if_comparison.csv"
with open(csv_path, "w", encoding="utf-8") as f:
    f.write("IF model,benign_mean,attack_mean,AUC(benign vs attack),% benign above 0.90,% attack above 0.90\n")
    f.write(f"Contaminated (published),{mean_benign_contam:.4f},{mean_attack_contam:.4f},{auc_contam:.4f},{pct_benign_90_contam:.2f}%,{pct_attack_90_contam:.2f}%\n")
    f.write(f"Corrected (benign-only),{mean_benign_corr:.4f},{mean_attack_corr:.4f},{auc_corr:.4f},{pct_benign_90_corr:.2f}%,{pct_attack_90_corr:.2f}%\n")

print(f"Saved comparison table to {csv_path}")

# Generate ROC comparison figure
os.makedirs("paper2/figures", exist_ok=True)
fig_path = "paper2/figures/O2_A_if_roc_comparison.png"

fpr_contam, tpr_contam, _ = roc_curve(y_eval, anom_contam)
fpr_corr, tpr_corr, _ = roc_curve(y_eval, anom_corr)

plt.figure(figsize=(7, 6))
plt.plot(fpr_contam, tpr_contam, color="#dc2626", lw=2, linestyle="--", label=f"Contaminated IF (AUC = {auc_contam:.4f})")
plt.plot(fpr_corr, tpr_corr, color="#16a34a", lw=2.5, label=f"Corrected IF (AUC = {auc_corr:.4f})")
plt.plot([0, 1], [0, 1], color="#94a3b8", lw=1, linestyle=":", label="Random Guess (AUC = 0.5000)")
plt.xlabel("False Positive Rate (Benign misclassified as anomalous)", fontsize=11)
plt.ylabel("True Positive Rate (Attacks correctly flagged anomalous)", fontsize=11)
plt.title("Isolation Forest ROC Curve: Contaminated vs. Corrected", fontsize=12, fontweight="bold")
plt.legend(loc="lower right", fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(fig_path, dpi=300)
plt.close()
print(f"Saved ROC comparison plot to {fig_path}")
