import pandas as pd

df6 = pd.read_csv('tables/tab6_posture_balanced.csv')

costs = {
    0: (0, 0),       # Allow: benign cost 0, attack reward 0
    1: (-1, 5),      # Alert: benign cost -1, attack reward +5
    2: (-3, 10),     # Restrict: benign cost -3, attack reward +10
    3: (-15, 20),    # Quarantine: benign cost -15, attack reward +20
    4: (-50, 50)     # Block: benign cost -50, attack reward +50
}

def clean_int(val):
    if pd.isna(val):
        return 0
    return int(str(val).replace(',', '').strip())

def calc_ocu_tab6(mapping):
    total_ocu = 0
    for idx, r in df6.iterrows():
        lvl = int(str(r['Level']).replace('L_', '').replace('L', ''))
        act = mapping[lvl]
        b_cnt = clean_int(r['Benign Flows'])
        a_cnt = clean_int(r['Attack Flows'])
        b_val, a_val = costs[act]
        total_ocu += b_cnt * b_val + a_cnt * a_val
    return total_ocu

print("=== Recomputed OCU directly from Table 6 counts ===")
p_opt_000044 = calc_ocu_tab6([0, 0, 0, 0, 4, 4])
p_opt_002244 = calc_ocu_tab6([0, 0, 2, 2, 4, 4])
p2tier_012344 = calc_ocu_tab6([0, 1, 2, 3, 4, 4])
p2tier_001344 = calc_ocu_tab6([0, 0, 1, 3, 4, 4])
p1_012334 = calc_ocu_tab6([0, 1, 2, 3, 3, 4])
p2_023444 = calc_ocu_tab6([0, 2, 3, 4, 4, 4])

print(f"P(0,0,0,0,4,4) [Allow-Allow-Allow-Allow-Block-Block]: {p_opt_000044:,}")
print(f"P(0,0,2,2,4,4) [Allow-Allow-Restrict-Restrict-Block-Block]: {p_opt_002244:,}")
print(f"P(0,1,2,3,4,4) [Allow-Alert-Restrict-Quarantine-Block-Block]: {p2tier_012344:,}")
print(f"P(0,0,1,3,4,4) [Allow-Allow-Alert-Quarantine-Block-Block]: {p2tier_001344:,}")
print(f"P(0,1,2,3,3,4) [Allow-Alert-Restrict-Quarantine-Quarantine-Block]: {p1_012334:,}")
print(f"P(0,2,3,4,4,4) [Allow-Restrict-Quarantine-Block-Block-Block]: {p2_023444:,}")

# Achievable OCU:
# Total attack flows in Table 6:
total_attack = sum(clean_int(r['Attack Flows']) for _, r in df6.iterrows())
max_achievable = total_attack * 50
print(f"\nTotal attack flows in Table 6: {total_attack:,}")
print(f"Max achievable attack reward (x50): {max_achievable:,}")
print(f"P2-tier (0,1,2,3,4,4) captures: {p2tier_012344 / max_achievable * 100:.2f}% of achievable OCU ({p2tier_012344:,} / {max_achievable:,})")
print(f"P_opt (0,0,2,2,4,4) captures: {p_opt_002244 / max_achievable * 100:.2f}% of achievable OCU ({p_opt_002244:,} / {max_achievable:,})")
