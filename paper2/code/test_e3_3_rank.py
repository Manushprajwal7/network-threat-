import itertools

bal_flows = [(14200, 0), (12191, 8009), (3321, 4479), (297, 403), (0, 15600), (0, 1500)]
atk_flows = [(0, 0), (0, 0), (0, 0), (72, 1728), (1323, 52977), (87, 3813)]

COSTS = [(0, 100), (1, -5), (3, -10), (15, -20), (50, -50)]
ACTION_NAMES = ['Allow', 'Alert', 'Restrict', 'Quarantine', 'Block']

all_70 = [m for m in itertools.combinations_with_replacement(range(5), 6) if m[0] == 0 and m[5] == 4]
safe_mappings = []

for m in all_70:
    blocked_ben_bal = sum(bal_flows[lvl][0] for lvl in range(6) if m[lvl] == 4)
    block_fpr_bal = blocked_ben_bal / 30009.0 * 100.0
    if block_fpr_bal > 5.0:
        continue
    c_bal = sum(bal_flows[lvl][0] * COSTS[m[lvl]][0] + bal_flows[lvl][1] * COSTS[m[lvl]][1] for lvl in range(6))
    c_atk = sum(atk_flows[lvl][0] * COSTS[m[lvl]][0] + atk_flows[lvl][1] * COSTS[m[lvl]][1] for lvl in range(6))
    c_comb = 0.5 * c_bal + 0.5 * c_atk
    
    atk_caught = sum(bal_flows[lvl][1] for lvl in range(6) if m[lvl] > 0)
    atk_recall = atk_caught / 29991.0 * 100.0
    
    ben_acted = sum(bal_flows[lvl][0] for lvl in range(6) if m[lvl] > 0)
    ben_fpr = ben_acted / 30009.0 * 100.0
    
    ben_qb = sum(bal_flows[lvl][0] for lvl in range(6) if m[lvl] >= 3)
    ben_qb_rate = ben_qb / 30009.0 * 100.0
    
    safe_mappings.append({
        'mapping': m,
        'str': ' -> '.join([f'L{lvl}:{ACTION_NAMES[m[lvl]]}' for lvl in range(6)]),
        'short': '-'.join([ACTION_NAMES[m[lvl]][:3] for lvl in range(6)]),
        'cost_bal': c_bal,
        'net_ben_bal': -c_bal,
        'cost_atk': c_atk,
        'net_ben_atk': -c_atk,
        'comb_cost': c_comb,
        'comb_net_ben': -c_comb,
        'atk_recall': atk_recall,
        'ben_fpr': ben_fpr,
        'ben_qb_rate': ben_qb_rate,
        'block_fpr': block_fpr_bal
    })

print(f"Total safe mappings: {len(safe_mappings)}")

# Sort by combined cost
safe_mappings.sort(key=lambda x: x['comb_cost'])

default_m = (0, 1, 2, 3, 3, 4)
default_rank_comb = [i+1 for i, x in enumerate(safe_mappings) if x['mapping'] == default_m][0]

print("=== TOP 10 BY COMBINED COST ===")
for i in range(10):
    vm = safe_mappings[i]
    print(f"{i+1:2d}. {vm['short']} | Comb NetBen: {vm['comb_net_ben']:10.1f} | Bal NetBen: {vm['net_ben_bal']:8d} | Atk NetBen: {vm['net_ben_atk']:10d}")

print(f"\nDefault Mapping Rank (Combined): {default_rank_comb} of {len(safe_mappings)}")

# Sort by balanced cost
by_bal = sorted(safe_mappings, key=lambda x: x['cost_bal'])
default_rank_bal = [i+1 for i, x in enumerate(by_bal) if x['mapping'] == default_m][0]
print("\n=== TOP 10 BY BALANCED WINDOW COST ===")
for i in range(10):
    vm = by_bal[i]
    print(f"{i+1:2d}. {vm['short']} | Bal NetBen: {vm['net_ben_bal']:8d} | Atk NetBen: {vm['net_ben_atk']:10d} | Comb NetBen: {vm['comb_net_ben']:10.1f}")

print(f"\nDefault Mapping Rank (Balanced): {default_rank_bal} of {len(safe_mappings)}")

# Sort by attack-heavy cost
by_atk = sorted(safe_mappings, key=lambda x: x['cost_atk'])
default_rank_atk = [i+1 for i, x in enumerate(by_atk) if x['mapping'] == default_m][0]
print("\n=== TOP 10 BY ATTACK-HEAVY WINDOW COST ===")
for i in range(10):
    vm = by_atk[i]
    print(f"{i+1:2d}. {vm['short']} | Atk NetBen: {vm['net_ben_atk']:10d} | Bal NetBen: {vm['net_ben_bal']:8d} | Comb NetBen: {vm['comb_net_ben']:10.1f}")

print(f"\nDefault Mapping Rank (Attack-Heavy): {default_rank_atk} of {len(safe_mappings)}")
