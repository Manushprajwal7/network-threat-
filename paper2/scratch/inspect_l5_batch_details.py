import numpy as np
import pandas as pd
from pathlib import Path
import json
import joblib
import networkx as nx

ROOT = Path(".").resolve()
d_val_dir = ROOT / "audit_v3" / "cache"

# Load D_val arrays
y_val = np.load(d_val_dir / "D_val_y.npy")
cache_dir = ROOT.parent / "audit" / "lofo" / "cache"
with open(cache_dir / "class_names.json", "r") as f:
    class_names = json.load(f)
benign_idx = class_names.index("BenignTraffic")

# Models & inference
sys_path = ROOT / "audit_v3" / "env"
import sys
sys.path.insert(0, str(sys_path))
from inference_helper import xgb_predict_batched, if_predict_batched

xgb_path = ROOT.parent / "backend" / "ml_model" / "saved_models" / "xgboost.pkl"
xgb_model = joblib.load(xgb_path)
if_path = ROOT.parent / "backend" / "ml_model" / "saved_models" / "isolation_forest_corrected.pkl"
if_model = joblib.load(if_path)

X_val_unscaled = np.load(d_val_dir / "D_val_X.npy")
X_val_scaled = np.load(d_val_dir / "D_val_X_scaled.npy")

val_probs = xgb_predict_batched(xgb_model, X_val_unscaled, batch_size=1024)
val_preds = np.argmax(val_probs, axis=1)
val_confs = np.max(val_probs, axis=1)
val_raw_anom = if_predict_batched(if_model, X_val_scaled, batch_size=2048)

calib_df = pd.read_csv(ROOT / "audit_v3" / "E7_calibration_split" / "calibration_params.csv")
q05_new = float(calib_df.loc[calib_df["parameter"] == "q_0.05", "new_value_d_calib"].values[0])
q95_new = float(calib_df.loc[calib_df["parameter"] == "q_0.95", "new_value_d_calib"].values[0])

n_flows = len(val_raw_anom)
W = 100
n_batches = n_flows // W
s_cal = np.clip((val_raw_anom - q05_new) / (q95_new - q05_new + 1e-9) * 0.80 + 0.10, 0.0, 1.0)

# Graph
G = nx.barabasi_albert_graph(n=120, m=2, seed=42)
pr = nx.pagerank(G, alpha=0.85)
pr_vals = np.array([pr[i] for i in range(120)])
pr_std = (pr_vals - np.mean(pr_vals)) / (np.std(pr_vals) + 1e-9)
risk_scores_120 = np.clip(0.42 + 0.08 * pr_std, 0.10, 0.90)

obs_batch_nodes = np.array([b % 120 for b in range(n_batches)])
obs_R_batch = risk_scores_120[obs_batch_nodes]
obs_R_stream = np.repeat(obs_R_batch, W)

# Trust calculation
T_stream = np.zeros(n_flows, dtype=float)
t_curr = 100.0
for i in range(n_flows):
    pred = val_preds[i]
    conf = val_confs[i]
    s_anom = s_cal[i]
    R_node = obs_R_stream[i]
    s_c = 100.0 if pred == benign_idx else (1.0 - conf) * 100.0
    s_a = (1.0 - s_anom) * 100.0
    s_t = (1.0 - R_node) * 100.0
    s_d = 80.0
    t_obs = 0.40 * s_c + 0.35 * s_a + 0.15 * s_t + 0.10 * s_d
    if conf >= 0.90 and pred != benign_idx and s_anom >= 0.50:
        t_curr = 10.0
    else:
        t_curr = 0.30 * t_obs + 0.70 * t_curr
    T_stream[i] = t_curr

hub_nodes = [node for node in range(120) if risk_scores_120[node] >= 0.75]
hub_batches = [b for b in range(n_batches) if (b % 120) in hub_nodes]

print("\n--- Inspecting the 10 Hub Batches in Table 6 Stream ---")
for b in hub_batches:
    st = b * W
    en = st + W
    b_y = y_val[st:en]
    n_atk = np.sum(b_y != benign_idx)
    mean_s_cal = np.mean(s_cal[st:en])
    mean_conf = np.mean(val_confs[st:en])
    mean_T = np.mean(T_stream[st:en])
    R_b = obs_R_batch[b]
    node = obs_batch_nodes[b]
    
    c_anom = int(mean_s_cal >= 0.50)
    c_conf = int(np.mean((val_preds[st:en] != benign_idx) & (val_confs[st:en] >= 0.90)) >= 0.50)
    c_trust = int(mean_T <= 60.0)
    c_topo = int(R_b >= 0.42)
    S = c_anom + c_conf + c_trust + c_topo
    
    # Escalation condition for L5: S >= 3 and mean_T <= 20.0 and R >= 0.75
    l5_met = (S >= 3) and (mean_T <= 20.0) and (R_b >= 0.75)
    print(f"Batch {b:3d} (Node {node}, R={R_b:.4f}): Attacks={n_atk:3d}/100, S={S}, mean_T={mean_T:.2f}, L5_condition={l5_met}")
