import numpy as np

lvl_bal = np.load("paper2/new_experiments/lvl_bal.npy")
y_bal = np.load("paper2/new_experiments/y_bin_bal.npy")

lvl_atk = np.load("paper2/new_experiments/lvl_atk.npy")
y_atk = np.load("paper2/new_experiments/y_bin_atk.npy")

# Cost matrix:
# a in [0: Allow, 1: Alert, 2: Restrict, 3: Quarantine, 4: Block]
# y=0 (benign): Allow=0, Alert=1, Restrict=3, Quarantine=15, Block=50
# y=1 (attack): Allow=0, Alert=-5, Restrict=-10, Quarantine=-20, Block=-50
c_ben = np.array([0, 1, 3, 15, 50])
c_atk = np.array([0, -5, -10, -20, -50])

policies = {
    "P1 (Default)": [0, 1, 2, 3, 3, 4],
    "P2-tier (Recommended)": [0, 1, 2, 3, 4, 4],
    "P2 (Global Cost-Optimal)": [0, 2, 3, 4, 4, 4],
}

for name, mapping in policies.items():
    map_arr = np.array(mapping)
    
    # Balanced
    act_bal = map_arr[lvl_bal]
    ben_mask_bal = (y_bal == 0)
    atk_mask_bal = (y_bal == 1)
    
    pen_ben_bal = np.sum(c_ben[act_bal[ben_mask_bal]])
    ben_atk_bal = np.sum(-c_atk[act_bal[atk_mask_bal]])
    net_bal = ben_atk_bal - pen_ben_bal
    block_fpr_bal = np.mean(act_bal[ben_mask_bal] == 4) * 100
    
    # Attack-Heavy
    act_atk = map_arr[lvl_atk]
    ben_mask_atk = (y_atk == 0)
    atk_mask_atk = (y_atk == 1)
    
    pen_ben_atk = np.sum(c_ben[act_atk[ben_mask_atk]])
    ben_atk_atk = np.sum(-c_atk[act_atk[atk_mask_atk]])
    net_atk = ben_atk_atk - pen_ben_atk
    block_fpr_atk = np.mean(act_atk[ben_mask_atk] == 4) * 100
    
    comb_net = 0.5 * (net_bal + net_atk)
    
    print(f"=== {name} ===")
    print(f"  Balanced: Benign Penalty = {pen_ben_bal:,} OCU, Attack Benefit = {ben_atk_bal:,} OCU, Net Benefit = {net_bal:,} OCU, Block FPR = {block_fpr_bal:.2f}%")
    print(f"  Atk-Heavy: Benign Penalty = {pen_ben_atk:,} OCU, Attack Benefit = {ben_atk_atk:,} OCU, Net Benefit = {net_atk:,} OCU, Block FPR = {block_fpr_atk:.2f}%")
    print(f"  Combined Net Benefit = {comb_net:,} OCU")
