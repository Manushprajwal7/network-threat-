import numpy as np
import pandas as pd
from pathlib import Path
import json

ROOT = Path(".").resolve()
cache_dir = ROOT.parent / "audit" / "lofo" / "cache"
with open(cache_dir / "class_names.json", "r") as f:
    class_names = json.load(f)
benign_idx = class_names.index("BenignTraffic")

# Cost matrix
cb = [0, 1, 3, 15, 50]
ca = [0, -5, -10, -20, -50]

# Load D_test
d_val_dir = ROOT / "audit_v3" / "cache"
y_test = np.load(d_val_dir / "D_test_y.npy")
y_test_bin = (y_test != benign_idx).astype(int)

# Let's inspect test_levels_new from run_e7
# Recompute test_levels_new exactly as run_e7 did:
calib_df = pd.read_csv(ROOT / "audit_v3" / "E7_calibration_split" / "calibration_params.csv")
q05_new = float(calib_df.loc[calib_df["parameter"] == "q_0.05", "new_value_d_calib"].values[0])
q95_new = float(calib_df.loc[calib_df["parameter"] == "q_0.95", "new_value_d_calib"].values[0])

# We can load val_raw_anom / test_raw_anom or run compute_posture_levels
import joblib
sys_path = ROOT / "audit_v3" / "env"
import sys
sys.path.insert(0, str(sys_path))
from inference_helper import xgb_predict_batched, if_predict_batched

xgb_path = ROOT.parent / "backend" / "ml_model" / "saved_models" / "xgboost.pkl"
xgb_model = joblib.load(xgb_path)
if_path = ROOT.parent / "backend" / "ml_model" / "saved_models" / "isolation_forest_corrected.pkl"
if_model = joblib.load(if_path)

X_test_unscaled = np.load(d_val_dir / "D_test_X.npy")
X_test_scaled = np.load(d_val_dir / "D_test_X_scaled.npy")

test_probs = xgb_predict_batched(xgb_model, X_test_unscaled, batch_size=1024)
test_preds = np.argmax(test_probs, axis=1)
test_confs = np.max(test_probs, axis=1)
test_raw_anom = if_predict_batched(if_model, X_test_scaled, batch_size=2048)

n_flows = len(test_raw_anom)
W = 100
s_cal = np.clip((test_raw_anom - q05_new) / (q95_new - q05_new + 1e-9) * 0.80 + 0.10, 0.0, 1.0)
rng = np.random.RandomState(99)
R_stream = np.clip(rng.normal(0.42, 0.08, n_flows), 0.10, 0.90)

T_stream = np.zeros(n_flows, dtype=float)
t_curr = 100.0
for i in range(n_flows):
    pred = test_preds[i]
    conf = test_confs[i]
    s_anom = s_cal[i]
    R_node = R_stream[i]
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

c_anom = (s_cal >= 0.50).astype(int)
c_conf = (test_preds != benign_idx).astype(int) & (test_confs >= 0.90).astype(int)
c_trust = (T_stream <= 60.0).astype(int)
c_topo = (R_stream >= 0.42).astype(int)
S = c_anom + c_conf + c_trust + c_topo

levels = np.zeros(n_flows, dtype=int)
levels[S == 1] = 1
levels[S == 2] = 2
crit = (S >= 3)
t_crit = (T_stream <= 20.0)
is_hub = (R_stream >= 0.75)
levels[crit & (~t_crit)] = 3
levels[crit & t_crit & (~is_hub)] = 4
levels[crit & t_crit & is_hub] = 5

print("Level counts on D_test (seed 99):")
for l in range(6):
    b_l = np.sum((levels == l) & (y_test_bin == 0))
    a_l = np.sum((levels == l) & (y_test_bin == 1))
    print(f"L{l}: benign={b_l:,}, attack={a_l:,}, total={b_l+a_l:,}")

def eval_map(mp):
    cost = 0
    for l in range(6):
        act = mp[l]
        b_l = np.sum((levels == l) & (y_test_bin == 0))
        a_l = np.sum((levels == l) & (y_test_bin == 1))
        cost += b_l * cb[act] + a_l * ca[act]
    return -cost

print("\nOCU on D_test:")
print("(0,0,0,0,4,4) [Allow-Allow-Allow-Allow-Block-Block]:", eval_map([0, 0, 0, 0, 4, 4]))
print("(0,0,2,2,4,4) [Allow-Allow-Restrict-Restrict-Block-Block]:", eval_map([0, 0, 2, 2, 4, 4]))
print("(0,0,1,3,4,4) [Allow-Allow-Alert-Quarantine-Block-Block]:", eval_map([0, 0, 1, 3, 4, 4]))
print("(0,1,2,3,4,4) [Allow-Alert-Restrict-Quarantine-Block-Block]:", eval_map([0, 1, 2, 3, 4, 4]))
print("(0,1,2,3,3,4) [Allow-Alert-Restrict-Quarantine-Quarantine-Block]:", eval_map([0, 1, 2, 3, 3, 4]))
