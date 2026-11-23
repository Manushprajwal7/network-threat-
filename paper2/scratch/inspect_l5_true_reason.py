import numpy as np
import pandas as pd
from pathlib import Path
import json

ROOT = Path(".").resolve()
d_val_dir = ROOT / "audit_v3" / "cache"

# Load D_val arrays
y_val = np.load(d_val_dir / "D_val_y.npy")
cache_dir = ROOT.parent / "audit" / "lofo" / "cache"
with open(cache_dir / "class_names.json", "r") as f:
    class_names = json.load(f)
benign_idx = class_names.index("BenignTraffic")

# Let's inspect run_e4_permutation_v2.py or run_e8_cost_and_policy.py for how Table 6 levels were computed
import joblib
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

# Check round-robin node assignment vs random normal
# In run_e3_topology.py or task2:
# What was the node assignment for Table 6?
# In task2: obs_batch_nodes = np.array([b % 120 for b in range(n_batches)])
# In run_e7 / run_e8: R_stream = np.clip(rng.normal(0.42, 0.08, n_flows), 0.10, 0.90) with seed 42!
rng_42 = np.random.RandomState(42)
R_stream_normal = np.clip(rng_42.normal(0.42, 0.08, n_flows), 0.10, 0.90)

print(f"Max R in R_stream_normal: {np.max(R_stream_normal):.4f}")
print(f"Number of flows with R >= 0.75 in normal draw: {np.sum(R_stream_normal >= 0.75)}")

# What about round-robin on 120-node graph?
import networkx as nx
G = nx.barabasi_albert_graph(n=120, m=2, seed=42)
pr = nx.pagerank(G, alpha=0.85)
pr_vals = np.array([pr[i] for i in range(120)])
pr_std = (pr_vals - np.mean(pr_vals)) / (np.std(pr_vals) + 1e-9)
risk_scores_120 = np.clip(0.42 + 0.08 * pr_std, 0.10, 0.90)

print("Nodes with risk >= 0.75 in 120-node graph:")
for node in range(120):
    if risk_scores_120[node] >= 0.75:
        print(f"  Node {node}: R = {risk_scores_120[node]:.4f}")

# Under round robin b % 120:
# batches that map to hub nodes:
hub_nodes = [node for node in range(120) if risk_scores_120[node] >= 0.75]
hub_batches = [b for b in range(n_batches) if (b % 120) in hub_nodes]
print(f"Batches mapping to hub nodes under round-robin: {hub_batches}")
