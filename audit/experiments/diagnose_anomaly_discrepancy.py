import numpy as np
import joblib
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent

# 1. Load Isolation Forest model
if_path = ROOT / "backend" / "ml_model" / "saved_models" / "isolation_forest.pkl"
iforest = joblib.load(if_path)

# Source code function:
source_code = """
# From backend/ml_model/unknown_attack_detector.py lines 137-139:
raw_score = float(iforest.score_samples(row_2d)[0])
anomaly_score = float(np.clip(0.5 - raw_score, 0, 1))
"""

# 2. Validation Set
X_val_scaled = np.load(ROOT / "audit" / "lofo" / "cache" / "X_val_scaled.npy", mmap_mode="r")
y_val = np.load(ROOT / "audit" / "lofo" / "cache" / "y_val.npy")
n_val = len(y_val)

# Random 100k sample from validation for exact evaluation
rng = np.random.default_rng(42)
idx_val = rng.choice(n_val, size=100000, replace=False)
raw_val = iforest.score_samples(X_val_scaled[idx_val])
anom_val = np.clip(0.5 - raw_val, 0, 1)

is_atk_val = (y_val[idx_val] != 1)
is_ben_val = (y_val[idx_val] == 1)
n_atk_val = int(is_atk_val.sum())
n_ben_val = int(is_ben_val.sum())

# 3. Restored 60k Evaluation Window
fixed = np.load(ROOT / "audit" / "scratch_60k_eval_fixed.npz")
anom_60k = fixed["anom"]
y_60k = fixed["y_sub"]
is_atk_60k = (y_60k != 1)
is_ben_60k = (y_60k == 1)
n_atk_60k = int(is_atk_60k.sum())
n_ben_60k = int(is_ben_60k.sum())

thresholds = [0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 0.99]

# Compute Table 1: Full Validation ROC/PR Table
rows_val = []
for tau in thresholds:
    pred_atk = (anom_val >= tau)
    cnt_above = int(pred_atk.sum())
    
    tp = int((pred_atk & is_atk_val).sum())
    fp = int((pred_atk & is_ben_val).sum())
    fn = int(((~pred_atk) & is_atk_val).sum())
    tn = int(((~pred_atk) & is_ben_val).sum())
    
    recall = tp / n_atk_val * 100.0 if n_atk_val > 0 else 0.0
    precision = tp / (tp + fp) * 100.0 if (tp + fp) > 0 else 0.0
    fpr = fp / n_ben_val * 100.0 if n_ben_val > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) / 100.0 if (precision + recall) > 0 else 0.0
    
    pct_atk_above = (anom_val[is_atk_val] >= tau).mean() * 100.0
    pct_ben_above = (anom_val[is_ben_val] >= tau).mean() * 100.0
    
    rows_val.append({
        "Threshold (tau)": tau,
        "Samples Above": cnt_above,
        "% Above (Total)": round(cnt_above / len(anom_val) * 100.0, 2),
        "Recall % (Attack)": round(recall, 2),
        "Precision %": round(precision, 2),
        "FPR % (Benign)": round(fpr, 2),
        "F1 Score": round(f1, 4),
        "% Atk Above": round(pct_atk_above, 2),
        "% Ben Above": round(pct_ben_above, 2)
    })

df_val = pd.DataFrame(rows_val)

# Compute Table 2: Restored 60k Window Statistics
rows_60k = []
for tau in thresholds:
    pred_atk = (anom_60k >= tau)
    cnt_above = int(pred_atk.sum())
    
    tp = int((pred_atk & is_atk_60k).sum())
    fp = int((pred_atk & is_ben_60k).sum())
    fn = int(((~pred_atk) & is_atk_60k).sum())
    tn = int(((~pred_atk) & is_ben_60k).sum())
    
    recall = tp / n_atk_60k * 100.0 if n_atk_60k > 0 else 0.0
    precision = tp / (tp + fp) * 100.0 if (tp + fp) > 0 else 0.0
    fpr = fp / n_ben_60k * 100.0 if n_ben_60k > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) / 100.0 if (precision + recall) > 0 else 0.0
    
    pct_atk_above = (anom_60k[is_atk_60k] >= tau).mean() * 100.0
    pct_ben_above = (anom_60k[is_ben_60k] >= tau).mean() * 100.0
    
    rows_60k.append({
        "Threshold (tau)": tau,
        "Samples Above": cnt_above,
        "% Above (Total)": round(cnt_above / len(anom_60k) * 100.0, 2),
        "Recall % (Attack)": round(recall, 2),
        "Precision %": round(precision, 2),
        "FPR % (Benign)": round(fpr, 2),
        "F1 Score": round(f1, 4),
        "% Atk Above": round(pct_atk_above, 2),
        "% Ben Above": round(pct_ben_above, 2)
    })

df_60k = pd.DataFrame(rows_60k)

print("=" * 90)
print("  SOURCE CODE LINE THAT COMPUTES THE ANOMALY SCORE:")
print("=" * 90)
print(source_code.strip())
print("=" * 90)

print("\n--- TABLE 1: VALIDATION SET ROC/PR TABLE (100k samples, 97.64% attack, 2.36% benign) ---")
print(df_val.to_string(index=False))

print("\n--- TABLE 2: RESTORED 60k EVALUATION WINDOW (60,000 samples, 97.53% attack, 2.47% benign) ---")
print(df_60k.to_string(index=False))

# Update the CSV table in paper2/tables/
out_val_csv = ROOT / "paper2" / "tables" / "E1_1_anomaly_threshold_justification.csv"
df_val_export = df_val[["Threshold (tau)", "Precision %", "Recall % (Attack)", "FPR % (Benign)", "F1 Score"]].copy()
df_val_export.columns = ["Threshold", "Precision_Pct", "Recall_Pct", "FPR_Pct", "F1_Score"]
df_val_export["Selected"] = ["No", "No", "No", "No", "Yes (Evaluated tau=0.90)", "No", "No"]
df_val_export.to_csv(out_val_csv, index=False)
print(f"\nUpdated {out_val_csv} with true empirical values!")
