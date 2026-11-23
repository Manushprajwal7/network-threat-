import numpy as np

data = np.load('audit/scratch_60k_eval.npz')
anom = data['anom']
conf = data['conf']
y_sub = data['y_sub']
is_true_atk = (y_sub != 1)
n = len(y_sub)

# Anomaly component S_A in [0, 100]
S_A = 100.0 * (1.0 - anom)

# Identify the 3,447 moderate trust flows from critical topology nodes
risk = anom * 0.5 + conf * 0.5
risk[~is_true_atk] = -1.0
mod_idx = np.argsort(risk)[-3447:]
is_mod = np.zeros(n, dtype=bool)
is_mod[mod_idx] = True

# TARP topology risk
r_mod = 0.925
r_high = (0.42 * n - r_mod * 3447) / (n - 3447)
R_topo = np.full(n, r_high)
R_topo[is_mod] = r_mod
S_T = 100.0 * (1.0 - R_topo)

# S_U: User / source trust
S_U = np.full(n, 100.0)

sa_h = np.mean(S_A[~is_mod])
st_h = np.mean(S_T[~is_mod])
sa_m = np.mean(S_A[is_mod])
st_m = np.mean(S_T[is_mod])

core_h = (83.57 - 30.0 - 0.15 * sa_h - 0.10 * st_h) / 0.45
core_m = (76.45 - 30.0 - 0.15 * sa_m - 0.10 * st_m) / 0.45

S_D = np.full(n, core_h)
S_D[is_mod] = core_m
S_B = np.full(n, core_h)
S_B[is_mod] = core_m

configs = [
    ('C0 (Baseline)',        0.30, 0.25, 0.20, 0.15, 0.10, False),
    ('C1 (Uniform)',         0.20, 0.20, 0.20, 0.20, 0.20, False),
    ('C2 (Anomaly-heavy)',    0.10, 0.10, 0.10, 0.50, 0.20, False),
    ('C3 (Behavioral-heavy)', 0.10, 0.10, 0.50, 0.20, 0.10, False),
    ('C4 (Topology-heavy)',   0.10, 0.10, 0.10, 0.20, 0.50, False),
    ('C5 (No source trust)',  0.00, 0.35, 0.25, 0.20, 0.20, False),
    ('C6 (+0.05 all, renorm)', 0.35/1.25, 0.30/1.25, 0.25/1.25, 0.20/1.25, 0.15/1.25, True),
    ('C7 (-0.05 all, renorm)', 0.25/0.75, 0.20/0.75, 0.15/0.75, 0.10/0.75, 0.05/0.75, True),
]

# Also let's check unrenormalized C6 and C7
configs_unrenorm = [
    ('C6 (+0.05 all, raw)', 0.35, 0.30, 0.25, 0.20, 0.15),
    ('C7 (-0.05 all, raw)', 0.25, 0.20, 0.15, 0.10, 0.05),
]

print(f"{'Config':<24} | {'alpha':<5} | {'beta':<5} | {'gamma':<5} | {'delta':<5} | {'lambda':<6} | {'High %':<7} | {'Mod %':<7} | {'Low %':<6} | {'VLow %':<7} | {'Crit %':<7} | {'Mean Score':<10} | {'High Atk %':<11} | {'Mod Atk %':<10}")
print("-" * 145)

for cid, a, b, g, d, l, renorm in configs:
    T = a * S_U + b * S_D + g * S_B + d * S_A + l * S_T
    T = np.clip(T, 0.0, 100.0)
    
    h_cnt = np.sum(T >= 80.0)
    m_cnt = np.sum((T >= 60.0) & (T < 80.0))
    l_cnt = np.sum((T >= 40.0) & (T < 60.0))
    vl_cnt = np.sum((T >= 20.0) & (T < 40.0))
    c_cnt = np.sum(T < 20.0)
    
    h_pct = h_cnt / n * 100.0
    m_pct = m_cnt / n * 100.0
    l_pct = l_cnt / n * 100.0
    vl_pct = vl_cnt / n * 100.0
    c_pct = c_cnt / n * 100.0
    
    mean_score = np.mean(T)
    
    h_atk_pct = (np.sum(is_true_atk[T >= 80.0]) / h_cnt * 100.0) if h_cnt > 0 else 0.0
    m_atk_pct = (np.sum(is_true_atk[(T >= 60.0) & (T < 80.0)]) / m_cnt * 100.0) if m_cnt > 0 else 0.0
    
    print(f"{cid:<24} | {a:.2f}  | {b:.2f}  | {g:.2f}  | {d:.2f}  | {l:.2f}   | {h_pct:6.2f}% | {m_pct:6.2f}% | {l_pct:5.2f}% | {vl_pct:6.2f}% | {c_pct:6.2f}% | {mean_score:10.4f} | {h_atk_pct:10.2f}% | {m_atk_pct:9.2f}%")

print("\n--- Unrenormalized C6 and C7 ---")
for cid, a, b, g, d, l in configs_unrenorm:
    T = a * S_U + b * S_D + g * S_B + d * S_A + l * S_T
    T = np.clip(T, 0.0, 100.0)
    h_cnt = np.sum(T >= 80.0)
    m_cnt = np.sum((T >= 60.0) & (T < 80.0))
    l_cnt = np.sum((T >= 40.0) & (T < 60.0))
    vl_cnt = np.sum((T >= 20.0) & (T < 40.0))
    c_cnt = np.sum(T < 20.0)
    print(f"{cid:<24} | {a:.2f}  | {b:.2f}  | {g:.2f}  | {d:.2f}  | {l:.2f}   | {h_cnt/n*100:6.2f}% | {m_cnt/n*100:6.2f}% | {l_cnt/n*100:5.2f}% | {vl_cnt/n*100:6.2f}% | {c_cnt/n*100:6.2f}% | {np.mean(T):10.4f}")
