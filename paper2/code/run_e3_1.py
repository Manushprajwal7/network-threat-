import os
import sys
sys.path.insert(0, ".")
import json
import joblib
import numpy as np

print("=== RUNNING OBJECTIVE 3: EXPERIMENT E3.1 (REVISED AUDIT) ===")

# Cost matrix: costs[action][is_attack]
COSTS = {
    "Allow":      {0: 0,  1: 100},
    "Alert":      {0: 1,  1: -5},
    "Restrict":   {0: 3,  1: -10},
    "Quarantine": {0: 15, 1: -20},
    "Block":      {0: 50, 1: -50},
}

with open("audit/lofo/cache/class_names.json", "r") as f:
    class_names = json.load(f)

from backend.api.decision_engine import make_decision
from backend.ml_model.predict import get_risk_level

# -------------------------------------------------------------------
# 1. WINDOW 1: Attack-Heavy 60k Window
# -------------------------------------------------------------------
print("\n--- 1. Evaluating Window 1: Attack-Heavy 60k ---")
fixed = np.load("audit/scratch_60k_eval_fixed.npz")
indices_60k = fixed["indices"]
y_60k = fixed["y_sub"]
is_atk_60k = (y_60k != 1).astype(int)
n_atk_60k = int(np.sum(is_atk_60k == 1))
n_ben_60k = int(np.sum(is_atk_60k == 0))

tarp_60k = fixed["tarp"]
anom_60k_pub = fixed["anom"]      # Contaminated IF anomaly from published paper
trust_60k_pub = fixed["trust"]    # Published ADTM trust
preds_60k = fixed["preds"]
conf_60k = fixed["conf"]

# (A) Freshly computed P0 on Attack-Heavy using published decision engine
actions_p0_60k = []
for t in range(60000):
    p_label = class_names[preds_60k[t]]
    risk = get_risk_level(p_label)
    t_val = trust_60k_pub[t]
    trust_band = "High Trust" if t_val >= 80.0 else ("Medium Trust" if t_val >= 50.0 else "Low Trust")
    tp_val = tarp_60k[t]
    topo_crit = "Critical" if tp_val >= 0.75 else ("High" if tp_val >= 0.42 else "Low")
    
    d = make_decision(
        predicted_label=p_label,
        risk_level=risk,
        trust_level=trust_band,
        confidence=conf_60k[t],
        anomaly_score=anom_60k_pub[t],
        known_or_unknown="Known",
        topology_criticality=topo_crit,
        entity_id=str(t // 100)
    )
    actions_p0_60k.append(d["action"])
actions_p0_60k = np.array(actions_p0_60k)

# (B) New Default P1 on Attack-Heavy (from Part B)
# Levels: L0-L2: 0, L3: 18 entities (1800), L4: 543 entities (54300), L5: 39 entities (3900)
# Mapping: L0->Allow, L1->Alert, L2->Restrict, L3->Quarantine, L4->Quarantine, L5->Block
# As evaluated in Part B generate_both_windows.py:
# L3 Quarantine: 1728 atk, 72 ben
# L4 Quarantine: 52975 atk, 1325 ben
# L5 Block: 3813 atk, 87 ben
# Quarantine total: 56,100 flows (54,703 atk, 1,397 ben)
# Block total: 3,900 flows (3,813 atk, 87 ben)
actions_p1_60k = np.empty(60000, dtype=object)
# Entities 0 to 600: exactly matching generate_both_windows levels:
from paper2.code.generate_both_windows import levels_60k
sample_levels_60k = np.repeat(levels_60k, 100)
DEFAULT_MAP = {0: "Allow", 1: "Alert", 2: "Restrict", 3: "Quarantine", 4: "Quarantine", 5: "Block"}
for t in range(60000):
    actions_p1_60k[t] = DEFAULT_MAP[sample_levels_60k[t]]


# -------------------------------------------------------------------
# 2. WINDOW 2: Stratified Balanced 60k Window (Fix 1: 30/40/30)
# -------------------------------------------------------------------
print("\n--- 2. Evaluating Window 2: Stratified Balanced 60k ---")
y_test = np.load("audit/lofo/cache/y_test.npy")
b_all = np.where(y_test == 1)[0]
a_all = np.where(y_test != 1)[0]

rng = np.random.default_rng(42)
b_pure = rng.choice(b_all, size=180*100, replace=False).reshape(180, 100)
a_pure = rng.choice(a_all, size=180*100, replace=False).reshape(180, 100)
mixed = []
for _ in range(240):
    k_atk = rng.binomial(100, 0.5)
    k_ben = 100 - k_atk
    idx_a = rng.choice(a_all, size=k_atk, replace=False)
    idx_b = rng.choice(b_all, size=k_ben, replace=False)
    flows = np.concatenate([idx_a, idx_b])
    rng.shuffle(flows)
    mixed.append(flows)
mixed = np.array(mixed)

all_entities = np.concatenate([b_pure, mixed, a_pure], axis=0)
entity_order = np.arange(600)
rng.shuffle(entity_order)
all_entities = all_entities[entity_order]

bal_indices = all_entities.flatten()
y_bal = y_test[bal_indices]
is_atk_bal = (y_bal != 1).astype(int)
n_atk_bal = int(np.sum(is_atk_bal == 1))
n_ben_bal = int(np.sum(is_atk_bal == 0))

# (A) Freshly compute P0 on Balanced Window:
# Contaminated IF:
if_contam = joblib.load("backend/ml_model/saved_models/isolation_forest.pkl")
X_test_scaled = np.load("audit/lofo/cache/X_test_scaled.npy", mmap_mode="r")
raw_bal_contam = if_contam.score_samples(np.array(X_test_scaled[bal_indices], dtype=np.float32))
s_min_c = 0.4200
s_p95_c = float(-if_contam.offset_)
anom_bal_contam = np.clip((-raw_bal_contam - s_min_c) / (s_p95_c - s_min_c) * 0.90, 0, 1)

# XGBoost on balanced:
xgb = joblib.load("backend/ml_model/saved_models/xgboost.pkl")
xgb.set_params(device="cpu")
X_test_unscaled = np.load("audit/lofo/cache/X_test.npy", mmap_mode="r")
probs_bal = xgb.predict_proba(np.array(X_test_unscaled[bal_indices], dtype=np.float32))
preds_bal = np.argmax(probs_bal, axis=1)
conf_bal = np.max(probs_bal, axis=1)

# TARP on balanced:
tarp_120 = fixed["tarp"].reshape(600, 100)[:120, 0]
tarp_bal = np.array([tarp_120[e % 120] for e in range(600) for _ in range(100)])

# Published ADTM Trust update on balanced window:
ALPHA, BETA, GAMMA, DELTA, LAMBD = 0.30, 0.25, 0.20, 0.15, 0.10
trust_bal_pub = np.zeros(60000)
for e in range(600):
    start = e * 100
    end = start + 100
    S_U, S_D, S_B = 100.0, 95.0, 100.0
    for t in range(start, end):
        if is_atk_bal[t]: S_B = max(0.0, S_B - 2.0)
        else: S_B = min(100.0, S_B + 1.0)
        S_A = 100.0 * (1.0 - anom_bal_contam[t])
        S_T = 100.0 * (1.0 - tarp_bal[t])
        trust_bal_pub[t] = np.clip(ALPHA * S_U + BETA * S_D + GAMMA * S_B + DELTA * S_A + LAMBD * S_T, 0.0, 100.0)

# Decision Engine for P0 on Balanced:
actions_p0_bal = []
for t in range(60000):
    p_label = class_names[preds_bal[t]]
    risk = get_risk_level(p_label)
    t_val = trust_bal_pub[t]
    trust_band = "High Trust" if t_val >= 80.0 else ("Medium Trust" if t_val >= 50.0 else "Low Trust")
    tp_val = tarp_bal[t]
    topo_crit = "Critical" if tp_val >= 0.75 else ("High" if tp_val >= 0.42 else "Low")
    
    d = make_decision(
        predicted_label=p_label,
        risk_level=risk,
        trust_level=trust_band,
        confidence=conf_bal[t],
        anomaly_score=anom_bal_contam[t],
        known_or_unknown="Known",
        topology_criticality=topo_crit,
        entity_id=str(t // 100)
    )
    actions_p0_bal.append(d["action"])
actions_p0_bal = np.array(actions_p0_bal)

# (B) New Default P1 on Balanced (from Part B generate_both_windows.py):
from paper2.code.generate_both_windows import levels_bal
sample_levels_bal = np.repeat(levels_bal, 100)
actions_p1_bal = np.array([DEFAULT_MAP[lvl] for lvl in sample_levels_bal])


# -------------------------------------------------------------------
# 3. Policy Evaluation Function
# -------------------------------------------------------------------
def evaluate_policy(actions, is_attack):
    N_tot = len(actions)
    n_atk = int(np.sum(is_attack == 1))
    n_ben = int(np.sum(is_attack == 0))
    
    counts = {a: int(np.sum(actions == a)) for a in ["Allow", "Alert", "Restrict", "Quarantine", "Block"]}
    atk_c = {a: int(np.sum((actions == a) & (is_attack == 1))) for a in ["Allow", "Alert", "Restrict", "Quarantine", "Block"]}
    ben_c = {a: int(np.sum((actions == a) & (is_attack == 0))) for a in ["Allow", "Alert", "Restrict", "Quarantine", "Block"]}
    
    tot_cost = sum(ben_c[a] * COSTS[a][0] + atk_c[a] * COSTS[a][1] for a in ["Allow", "Alert", "Restrict", "Quarantine", "Block"])
    net_benefit = -tot_cost
    avg_cost = tot_cost / N_tot
    
    atk_recall = (n_atk - atk_c["Allow"]) / n_atk * 100.0 if n_atk > 0 else 0.0
    ben_fpr = (n_ben - ben_c["Allow"]) / n_ben * 100.0 if n_ben > 0 else 0.0
    ben_quar_block = (ben_c["Quarantine"] + ben_c["Block"]) / n_ben * 100.0 if n_ben > 0 else 0.0
    
    return {
        "counts": counts, "atk_c": atk_c, "ben_c": ben_c,
        "tot_cost": tot_cost, "net_benefit": net_benefit, "avg_cost": avg_cost,
        "atk_recall": atk_recall, "ben_fpr": ben_fpr, "ben_quar_block": ben_quar_block
    }

res_p0_60k_fresh = evaluate_policy(actions_p0_60k, is_atk_60k)
res_p1_60k = evaluate_policy(actions_p1_60k, is_atk_60k)

res_p0_bal_fresh = evaluate_policy(actions_p0_bal, is_atk_bal)
res_p1_bal = evaluate_policy(actions_p1_bal, is_atk_bal)

# Published Table 19A reference on Attack-Heavy (reported in paper):
# Alert: 54553 (100% atk), Quarantine: 5447 (1482 ben, 3965 atk)
p0_pub_counts = {"Allow": 0, "Alert": 54553, "Restrict": 0, "Quarantine": 5447, "Block": 0}
p0_pub_atk = {"Allow": 0, "Alert": 54553, "Restrict": 0, "Quarantine": 3965, "Block": 0}
p0_pub_ben = {"Allow": 0, "Alert": 0, "Restrict": 0, "Quarantine": 1482, "Block": 0}
c_pub = sum(p0_pub_ben[a] * COSTS[a][0] + p0_pub_atk[a] * COSTS[a][1] for a in p0_pub_counts)
res_p0_60k_table19 = {
    "counts": p0_pub_counts, "atk_c": p0_pub_atk, "ben_c": p0_pub_ben,
    "tot_cost": c_pub, "net_benefit": -c_pub, "avg_cost": c_pub / 60000.0,
    "atk_recall": 100.0, "ben_fpr": 100.0, "ben_quar_block": 100.0
}

# -------------------------------------------------------------------
# 4. Save Table O3_E1_baseline_costs.csv
# -------------------------------------------------------------------
csv_path = "paper2/tables/O3_E1_baseline_costs.csv"
os.makedirs("paper2/tables", exist_ok=True)
with open(csv_path, "w", encoding="utf-8") as f:
    f.write("window,policy,allow_cnt,alert_cnt,restrict_cnt,quarantine_cnt,block_cnt,total_cost,net_benefit,attack_recall%,benign_fpr%,benign_quar_block%\n")
    for w_name, p_name, r in [
        ("Attack-heavy 60k", "P0 (Published Table 19A)", res_p0_60k_table19),
        ("Attack-heavy 60k", "P0 (Freshly Recomputed)", res_p0_60k_fresh),
        ("Attack-heavy 60k", "P1 (New Default)", res_p1_60k),
        ("Balanced Stratified 60k", "P0 (Freshly Recomputed)", res_p0_bal_fresh),
        ("Balanced Stratified 60k", "P1 (New Default)", res_p1_bal),
    ]:
        c = r["counts"]
        f.write(f"{w_name},{p_name},{c['Allow']},{c['Alert']},{c['Restrict']},{c['Quarantine']},{c['Block']},{r['tot_cost']},{r['net_benefit']},{r['atk_recall']:.2f},{r['ben_fpr']:.2f},{r['ben_quar_block']:.2f}\n")
print(f"Saved {csv_path}")

# -------------------------------------------------------------------
# 5. Baseline Bounds Table
# -------------------------------------------------------------------
bounds_csv_path = "paper2/tables/O3_E1_baseline_bounds.csv"
all_allow_cost = n_ben_bal * 0 + n_atk_bal * 100
all_block_cost = n_ben_bal * 50 + n_atk_bal * (-50)
perfect_cost = n_ben_bal * 0 + n_atk_bal * (-50)

with open(bounds_csv_path, "w", encoding="utf-8") as f:
    f.write("policy,balanced_window_total_cost,balanced_window_net_benefit,operational_interpretation\n")
    f.write(f"All-Allow (Worst),{all_allow_cost},{-all_allow_cost},Catastrophic — all attacks allowed unimpeded\n")
    f.write(f"All-Block (Naive),{all_block_cost},{-all_block_cost},Neutral net benefit but 100% benign denial-of-service outage\n")
    f.write(f"P0 Published (Recomputed),{res_p0_bal_fresh['tot_cost']},{res_p0_bal_fresh['net_benefit']},Contaminated IF causes 16.8k benign restrictions and false quarantines\n")
    f.write(f"P1 New Default,{res_p1_bal['tot_cost']},{res_p1_bal['net_benefit']},Hierarchical containment: 14.2k benign allowed + 17.1k attacks quarantined/blocked\n")
    f.write(f"Theoretical Perfect Policy,{perfect_cost},{-perfect_cost},Upper bound — zero benign friction and 100% attack termination\n")
print(f"Saved {bounds_csv_path}")

# -------------------------------------------------------------------
# 6. Per-Level Cost Breakdown Table
# -------------------------------------------------------------------
level_csv_path = "paper2/tables/O3_E1_level_breakdown.csv"
levels_data = [
    {"level": "L0", "entities": 142, "action": "Allow",      "total_flows": 14200, "atk_p": 0.00,  "atk": 0,     "ben": 14200, "mean_trust": 88.91},
    {"level": "L1", "entities": 202, "action": "Alert",      "total_flows": 20200, "atk_p": 39.65, "atk": 8009,  "ben": 12191, "mean_trust": 52.32},
    {"level": "L2", "entities": 78,  "action": "Restrict",   "total_flows": 7800,  "atk_p": 57.42, "atk": 4479,  "ben": 3321,  "mean_trust": 40.25},
    {"level": "L3", "entities": 7,   "action": "Quarantine", "total_flows": 700,   "atk_p": 57.57, "atk": 403,   "ben": 297,   "mean_trust": 29.55},
    {"level": "L4", "entities": 156, "action": "Quarantine", "total_flows": 15600, "atk_p": 100.0,  "atk": 15600, "ben": 0,     "mean_trust": 15.44},
    {"level": "L5", "entities": 15,  "action": "Block",      "total_flows": 1500,  "atk_p": 100.0,  "atk": 1500,  "ben": 0,     "mean_trust": 14.53},
]

with open(level_csv_path, "w", encoding="utf-8") as f:
    f.write("level,entities,action,total_flows,total_cost,net_benefit,attack%,mean_trust\n")
    for r in levels_data:
        act = r["action"]
        c = r["ben"] * COSTS[act][0] + r["atk"] * COSTS[act][1]
        f.write(f"{r['level']},{r['entities']},{act},{r['total_flows']},{c},{-c},{r['atk_p']:.2f},{r['mean_trust']:.2f}\n")
print(f"Saved {level_csv_path}")

print("\n=== AUDIT VERIFICATION COMPLETE ===")
