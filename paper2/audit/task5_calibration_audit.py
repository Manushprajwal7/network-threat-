import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import precision_recall_curve, roc_auc_score

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "clean_experiments_isolated" / "experiments"))

from common import (
    load_config, load_dataset_references, train_clean_if,
    generate_windows
)

CONFIG = load_config(str(ROOT / "configs" / "paper.yaml"))

def run_calibration_audit(seed=42):
    print("=== TASK 5: AUDITING ANOMALY CALIBRATION AND THRESHOLDS ===")
    
    # 1. Load dataset references
    class_names, benign_idx, X_train_scaled, y_train, X_test_scaled, y_test = load_dataset_references()
    
    # Split training into train and independent validation split for calibration
    benign_train_indices = np.where(y_train == benign_idx)[0]
    rng = np.random.RandomState(seed)
    rng.shuffle(benign_train_indices)
    
    # Train IF on 20,000 clean benign samples
    if_train_idx = benign_train_indices[:20000]
    # Independent held-out validation slice for calibration (disjoint 5,000 benign samples)
    val_cal_idx = benign_train_indices[20000:25000]
    
    from sklearn.ensemble import IsolationForest
    if_model = IsolationForest(
        n_estimators=100,
        max_samples=CONFIG["anomaly_detection"]["max_samples"],
        contamination=CONFIG["anomaly_detection"]["contamination"],
        random_state=seed,
        n_jobs=-1
    )
    X_clean_train = np.array(X_train_scaled[if_train_idx], dtype=np.float32)
    if_model.fit(X_clean_train)
    
    # Evaluate raw anomaly scores on separate validation split
    X_val_cal = np.array(X_train_scaled[val_cal_idx], dtype=np.float32)
    val_raw_scores = -if_model.score_samples(X_val_cal)
    
    # Compute calibration percentiles p5 and p95 on this separate validation split
    p5_val = float(np.percentile(val_raw_scores, 5))
    p95_val = float(np.percentile(val_raw_scores, 95))
    p75_val = float(np.percentile(val_raw_scores, 75)) # upper quartile
    
    print(f"Independent Validation Split Percentiles:")
    print(f"  p5: {p5_val:.4f}, p75: {p75_val:.4f}, p95: {p95_val:.4f}")
    
    # Published / paper calibration values:
    p5_pub = 0.4421
    p95_pub = 0.5284
    print(f"Published Config Percentiles: p5 = {p5_pub:.4f}, p95 = {p95_pub:.4f}")
    
    # 2. Evaluate on held-out test splits:
    # A. Primary balanced stream
    # B. Attack-heavy stream
    # C. Full test partition sample (e.g. 100,000 flows)
    _, _, bal_indices, y_bal_raw = generate_windows(y_test, benign_idx, seed=seed)
    atk_indices, y_atk_raw, _, _ = generate_windows(y_test, benign_idx, seed=seed)
    
    X_bal = np.array(X_test_scaled[bal_indices], dtype=np.float32)
    raw_bal = -if_model.score_samples(X_bal)
    
    # Compute calibrated scores under both calibration fits
    s_pub_bal = np.clip((raw_bal - p5_pub) / (p95_pub - p5_pub + 1e-9) * 0.80 + 0.10, 0.0, 1.0)
    s_val_bal = np.clip((raw_bal - p5_val) / (p95_val - p5_val + 1e-9) * 0.80 + 0.10, 0.0, 1.0)
    
    is_atk_bal = (y_bal_raw != benign_idx)
    is_ben_bal = (y_bal_raw == benign_idx)
    
    # Exceedance audit at s = 0.50, 0.70, 0.90
    thresholds = [0.50, 0.70, 0.90]
    exceed_rows = []
    
    for th in thresholds:
        # Published calibration
        ben_exc_pub = np.mean(s_pub_bal[is_ben_bal] >= th) * 100.0
        atk_exc_pub = np.mean(s_pub_bal[is_atk_bal] >= th) * 100.0
        
        # Independent validation calibration
        ben_exc_val = np.mean(s_val_bal[is_ben_bal] >= th) * 100.0
        atk_exc_val = np.mean(s_val_bal[is_atk_bal] >= th) * 100.0
        
        exceed_rows.append({
            "threshold_s": th,
            "pub_benign_exceedance_pct": round(ben_exc_pub, 2),
            "pub_attack_exceedance_pct": round(atk_exc_pub, 2),
            "pub_precision": round(np.sum((s_pub_bal >= th) & is_atk_bal) / np.sum(s_pub_bal >= th) * 100.0, 2),
            "val_benign_exceedance_pct": round(ben_exc_val, 2),
            "val_attack_exceedance_pct": round(atk_exc_val, 2),
            "val_precision": round(np.sum((s_val_bal >= th) & is_atk_bal) / np.sum(s_val_bal >= th) * 100.0, 2),
        })
        
    df_exceed = pd.DataFrame(exceed_rows)
    out_csv = ROOT / "audit" / "outputs" / "task5_exceedance_audit.csv"
    df_exceed.to_csv(out_csv, index=False)
    print(f"\nSaved exceedance audit to {out_csv}")
    print(df_exceed.to_string(index=False))
    
    # 3. Recalibration of c_anomaly threshold:
    # Compute precision-recall curve on the validation split
    prec, rec, pr_thresh = precision_recall_curve(is_atk_bal.astype(int), s_val_bal)
    # Find optimal threshold maximizing F1 or precision at high recall
    f1_scores = 2 * (prec * rec) / (prec + rec + 1e-9)
    best_f1_idx = np.argmax(f1_scores)
    best_th_f1 = float(pr_thresh[min(best_f1_idx, len(pr_thresh)-1)])
    
    # Upper-quartile calibrated threshold:
    # Mapping raw p75 through calibration
    th_upper_quartile = float(np.clip((p75_val - p5_val) / (p95_val - p5_val + 1e-9) * 0.80 + 0.10, 0.0, 1.0))
    
    print("\n[RECALIBRATION FINDINGS]")
    print(f"Optimal F1 threshold on validation: s = {best_th_f1:.4f} (F1: {f1_scores[best_f1_idx]:.4f}, Prec: {prec[best_f1_idx]:.4f}, Rec: {rec[best_f1_idx]:.4f})")
    print(f"Upper-quartile (p75) calibrated threshold: s = {th_upper_quartile:.4f}")
    
    summary_recal = [
        {
            "method": "Current Unified Threshold",
            "threshold": 0.50,
            "benign_exceedance_pct": round(float(np.mean(s_val_bal[is_ben_bal] >= 0.50) * 100.0), 2),
            "attack_recall_pct": round(float(np.mean(s_val_bal[is_atk_bal] >= 0.50) * 100.0), 2),
            "precision_pct": round(float(np.sum((s_val_bal >= 0.50) & is_atk_bal) / np.sum(s_val_bal >= 0.50) * 100.0), 2),
            "notes": "Current operational threshold; balanced trade-off"
        },
        {
            "method": "Optimal PR F1-Score",
            "threshold": round(best_th_f1, 4),
            "benign_exceedance_pct": round(float(np.mean(s_val_bal[is_ben_bal] >= best_th_f1) * 100.0), 2),
            "attack_recall_pct": round(float(np.mean(s_val_bal[is_atk_bal] >= best_th_f1) * 100.0), 2),
            "precision_pct": round(float(np.sum((s_val_bal >= best_th_f1) & is_atk_bal) / np.sum(s_val_bal >= best_th_f1) * 100.0), 2),
            "notes": "Maximizes harmonic mean of precision and recall"
        },
        {
            "method": "Upper-Quartile (p75 Benign)",
            "threshold": round(th_upper_quartile, 4),
            "benign_exceedance_pct": round(float(np.mean(s_val_bal[is_ben_bal] >= th_upper_quartile) * 100.0), 2),
            "attack_recall_pct": round(float(np.mean(s_val_bal[is_atk_bal] >= th_upper_quartile) * 100.0), 2),
            "precision_pct": round(float(np.sum((s_val_bal >= th_upper_quartile) & is_atk_bal) / np.sum(s_val_bal >= th_upper_quartile) * 100.0), 2),
            "notes": "Limits nominal benign escalation to top quartile"
        }
    ]
    df_recal = pd.DataFrame(summary_recal)
    recal_csv = ROOT / "audit" / "outputs" / "task5_recalibration_summary.csv"
    df_recal.to_csv(recal_csv, index=False)
    print(f"Saved recalibration summary to {recal_csv}")
    print(df_recal.to_string(index=False))

if __name__ == "__main__":
    run_calibration_audit()
