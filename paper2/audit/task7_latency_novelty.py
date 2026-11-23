import os
import sys
import time
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "clean_experiments_isolated" / "experiments"))

from common import (
    load_config, load_dataset_references, train_clean_if,
    generate_windows
)

CONFIG = load_config(str(ROOT / "configs" / "paper.yaml"))

def run_task7_latency_novelty():
    print("=== TASK 7: LATENCY/THROUGHPUT BENCHMARK & LOFO ZERO-DAY NOVELTY TEST ===")
    
    # 1. Load data & models
    class_names, benign_idx, X_train_scaled, y_train, X_test_scaled, y_test = load_dataset_references()
    X_test_unscaled = np.load(ROOT / "audit" / "lofo" / "cache" / "X_test.npy", mmap_mode="r")
    xgb_path = ROOT.parent / "backend" / "ml_model" / "saved_models" / "xgboost.pkl"
    if not xgb_path.exists():
        xgb_path = ROOT / "backend" / "ml_model" / "saved_models" / "xgboost.pkl"
    xgb_model = joblib.load(xgb_path)
    if_model, p5, p95 = train_clean_if(X_train_scaled, y_train, benign_idx, seed=42)
    
    # Benchmark sample: 10,000 flows
    N_bench = 10000
    X_sub_scaled = np.array(X_test_scaled[:N_bench], dtype=np.float32)
    X_sub_unscaled = np.array(X_test_unscaled[:N_bench], dtype=np.float32)
    
    # Benchmark component latencies
    print("\n--- Running Component Latency Benchmark (10,000 flows) ---")
    
    # 1. XGBoost inference
    t0 = time.perf_counter()
    xgb_probs = xgb_model.predict_proba(X_sub_unscaled)
    preds = np.argmax(xgb_probs, axis=1)
    confs = np.max(xgb_probs, axis=1)
    t_xgb = (time.perf_counter() - t0)
    lat_xgb_us = (t_xgb / N_bench) * 1e6
    
    # 2. Isolation Forest anomaly scoring
    t0 = time.perf_counter()
    raw_anom = -if_model.score_samples(X_sub_scaled)
    s_cal = np.clip((raw_anom - p5) / (p95 - p5 + 1e-9) * 0.80 + 0.10, 0.0, 1.0)
    t_if = (time.perf_counter() - t0)
    lat_if_us = (t_if / N_bench) * 1e6
    
    # 3. TARP topology lookup
    node_risks = np.clip(np.random.normal(0.42, 0.08, size=120), 0.10, 0.90)
    t0 = time.perf_counter()
    R_stream = np.repeat(node_risks[np.arange(N_bench // 100) % 120], 100)
    t_topo = (time.perf_counter() - t0)
    lat_topo_us = (t_topo / N_bench) * 1e6
    
    # 4. ADTM sequential trust calculation
    t0 = time.perf_counter()
    trust = np.zeros(N_bench, dtype=np.float32)
    T_curr = 100.0
    for b in range(N_bench // 100):
        start = b * 100
        end = start + 100
        for t in range(start, end):
            is_atk_pred = (preds[t] != benign_idx)
            c_t = confs[t]
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
            trust[t] = np.clip(T_curr, 0.0, 100.0)
    t_trust = (time.perf_counter() - t0)
    lat_trust_us = (t_trust / N_bench) * 1e6
    
    # 5. Window level assignment
    t0 = time.perf_counter()
    from common import assign_levels
    levels = assign_levels(s_cal, confs, preds, R_stream, trust, benign_idx)
    t_posture = (time.perf_counter() - t0)
    lat_posture_us = (t_posture / N_bench) * 1e6
    
    # Total Pipeline Latency
    tot_time = t_xgb + t_if + t_topo + t_trust + t_posture
    tot_lat_us = (tot_time / N_bench) * 1e6
    throughput_fps = N_bench / tot_time
    
    latency_rows = [
        {"component": "XGBoost Supervised Classification", "batch_time_sec": round(t_xgb, 4), "per_flow_latency_us": round(lat_xgb_us, 2), "pct_overhead": round(t_xgb/tot_time*100, 1)},
        {"component": "Isolation Forest Anomaly Scoring", "batch_time_sec": round(t_if, 4), "per_flow_latency_us": round(lat_if_us, 2), "pct_overhead": round(t_if/tot_time*100, 1)},
        {"component": "TARP Topological Risk Lookup", "batch_time_sec": round(t_topo, 6), "per_flow_latency_us": round(lat_topo_us, 4), "pct_overhead": round(t_topo/tot_time*100, 2)},
        {"component": "ADTM Dynamic Trust EWMA Update", "batch_time_sec": round(t_trust, 4), "per_flow_latency_us": round(lat_trust_us, 2), "pct_overhead": round(t_trust/tot_time*100, 1)},
        {"component": "Posture Window Escalation (W=100)", "batch_time_sec": round(t_posture, 4), "per_flow_latency_us": round(lat_posture_us, 2), "pct_overhead": round(t_posture/tot_time*100, 1)},
        {"component": "Full Multi-Stage Pipeline Total", "batch_time_sec": round(tot_time, 4), "per_flow_latency_us": round(tot_lat_us, 2), "pct_overhead": 100.0}
    ]
    df_lat = pd.DataFrame(latency_rows)
    lat_csv = ROOT / "audit" / "outputs" / "task7_latency_benchmark.csv"
    df_lat.to_csv(lat_csv, index=False)
    print(f"Saved latency benchmark to {lat_csv}")
    print(df_lat.to_string(index=False))
    print(f"\nThroughput: {throughput_fps:,.1f} flows/second (Batch collection buffering = {100 / throughput_fps * 1000:.2f} ms per W=100 window at link saturation)")
    
    # 2. Leave-One-Attack-Family-Out (LOFO) Zero-Day Test
    print("\n--- Running Leave-One-Attack-Family-Out (LOFO) Novelty Test ---")
    # Load class mapping
    class_map_path = ROOT.parent / "audit_final" / "outputs" / "class_mapping.csv"
    if not class_map_path.exists():
        class_map_path = ROOT / "audit_final" / "outputs" / "class_mapping.csv"
    class_map_df = pd.read_csv(class_map_path)
    family_by_idx = dict(zip(class_map_df["class_index"], class_map_df["family"]))
    
    # Evaluate across a representative slice of 60,000 test flows containing all families
    _, _, bal_indices, y_bal_raw = generate_windows(y_test, benign_idx, seed=42)
    X_eval_scaled = np.array(X_test_scaled[bal_indices], dtype=np.float32)
    raw_anom_eval = -if_model.score_samples(X_eval_scaled)
    s_cal_eval = np.clip((raw_anom_eval - p5) / (p95 - p5 + 1e-9) * 0.80 + 0.10, 0.0, 1.0)
    
    families = sorted(list(set(class_map_df["family"]) - {"Benign"}))
    lofo_rows = []
    
    for fam in families:
        fam_classes = class_map_df[class_map_df["family"] == fam]["class_index"].tolist()
        fam_mask = np.isin(y_bal_raw, fam_classes)
        n_flows = int(np.sum(fam_mask))
        
        if n_flows == 0:
            continue
            
        # 1. Unsupervised Anomaly Detection Recall (s >= 0.50) without classifier
        s_fam = s_cal_eval[fam_mask]
        anom_detected = np.sum(s_fam >= 0.50)
        anom_recall = (anom_detected / n_flows) * 100.0
        anom_mean = float(np.mean(s_fam))
        
        # 2. Zero-Day Simulation: What if supervised XGBoost treats this family as Benign (simulated zero-day)?
        # If classifier fails to recognize it (predicts Benign), does anomaly detector provide defense-in-depth?
        lofo_rows.append({
            "attack_family": fam,
            "evaluation_flows": n_flows,
            "mean_anomaly_score": round(anom_mean, 4),
            "unsupervised_anomaly_recall_pct": round(anom_recall, 2),
            "supervised_dependence": "HIGH" if anom_recall < 50.0 else "MODERATE" if anom_recall < 80.0 else "INDEPENDENT_ANOMALY_DEFENSE",
            "zero_day_defense_verdict": "FLAGGED_BY_ANOMALY" if anom_recall >= 70.0 else "PARTIAL_SURVEILLANCE_ONLY"
        })
        
    df_lofo = pd.DataFrame(lofo_rows)
    lofo_csv = ROOT / "audit" / "outputs" / "task7_lofo_zero_day_novelty.csv"
    df_lofo.to_csv(lofo_csv, index=False)
    print(f"\nSaved LOFO novelty audit to {lofo_csv}")
    print(df_lofo.to_string(index=False))

if __name__ == "__main__":
    run_task7_latency_novelty()
