import itertools
import numpy as np

# Balanced window level stats:
# L0: 14200 ben, 0 atk
# L1: 12191 ben, 8009 atk
# L2: 3321 ben, 4479 atk
# L3: 297 ben, 403 atk
# L4: 0 ben, 15600 atk
# L5: 0 ben, 1500 atk
bal_flows = [
    (14200, 0),
    (12191, 8009),
    (3321, 4479),
    (297, 403),
    (0, 15600),
    (0, 1500)
]

# Attack-heavy window level stats:
# L0: 0 ben, 0 atk
# L1: 0 ben, 0 atk
# L2: 0 ben, 0 atk
# L3: 72 ben, 1728 atk
# L4: 1323 ben, 52977 atk
# L5: 87 ben, 3813 atk
atk_flows = [
    (0, 0),
    (0, 0),
    (0, 0),
    (72, 1728),
    (1323, 52977),
    (87, 3813)
]

COSTS = [
    (0, 100),   # 0: Allow
    (1, -5),    # 1: Alert
    (3, -10),   # 2: Restrict
    (15, -20),  # 3: Quarantine
    (50, -50),  # 4: Block
]

ACTION_NAMES = ['Allow', 'Alert', 'Restrict', 'Quarantine', 'Block']

# Let's check constraints:
# Constraint 1: Severity Monotonicity: a(L0) <= a(L1) <= ... <= a(L5)
# Constraint 2: L0 is Monitor baseline -> a(L0) == 0 (Allow)
# Or all monotonic combos
all_combos = [m for m in itertools.combinations_with_replacement(range(5), 6) if m[0] == 0]

valid_mappings = []
excluded_count = 0

for m in all_combos:
    # Check safety constraint on balanced window: Block (action 4) on benign flows <= 5% (1500.45)
    blocked_ben_bal = sum(bal_flows[lvl][0] for lvl in range(6) if m[lvl] == 4)
    block_fpr_bal = blocked_ben_bal / 30009.0 * 100.0
    
    if block_fpr_bal > 5.0:
        excluded_count += 1
        continue
        
    cost_bal = sum(bal_flows[lvl][0] * COSTS[m[lvl]][0] + bal_flows[lvl][1] * COSTS[m[lvl]][1] for lvl in range(6))
    cost_atk = sum(atk_flows[lvl][0] * COSTS[m[lvl]][0] + atk_flows[lvl][1] * COSTS[m[lvl]][1] for lvl in range(6))
    comb_cost = 0.5 * cost_bal + 0.5 * cost_atk
    
    valid_mappings.append({
        'mapping': m,
        'mapping_str': ' -> '.join([f'L{lvl}:{ACTION_NAMES[m[lvl]]}' for lvl in range(6)]),
        'short_str': '-'.join([ACTION_NAMES[m[lvl]][:3] for lvl in range(6)]),
        'cost_bal': cost_bal,
        'net_ben_bal': -cost_bal,
        'cost_atk': cost_atk,
        'net_ben_atk': -cost_atk,
        'comb_cost': comb_cost,
        'comb_net_ben': -comb_cost,
        'block_fpr_bal': block_fpr_bal
    })

print(f"Total evaluated mappings with a(L0)==Allow: {len(all_combos)}")
print(f"Excluded by safety constraint (Block FPR > 5%): {excluded_count}")
print(f"Valid mappings retained: {len(valid_mappings)}")

# Rank by combined cost
valid_mappings.sort(key=lambda x: x['comb_cost'])

print("\n=== TOP 10 MAPPINGS BY COMBINED COST ===")
default_m = (0, 1, 2, 3, 3, 4)
default_rank = -1
for i, vm in enumerate(valid_mappings):
    if vm['mapping'] == default_m:
        default_rank = i + 1
    if i < 10:
        print(f"{i+1:2d}. {vm['short_str']} | Bal Cost: {vm['cost_bal']:8d} | Atk Cost: {vm['cost_atk']:10d} | Comb Cost: {vm['comb_cost']:10.1f} | Net Benefit: {vm['comb_net_ben']:10.1f}")

print(f"\nDefault Mapping (All-Ale-Res-Qua-Qua-Blo): Rank {default_rank} of {len(valid_mappings)}")
