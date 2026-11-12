import numpy as np

levels = [
    {"level": "L0", "entities": 142, "action": "Allow",      "total_flows": 14200, "atk_p": 0.00,  "atk": 0,     "ben": 14200, "mean_trust": 88.91},
    {"level": "L1", "entities": 202, "action": "Alert",      "total_flows": 20200, "atk_p": 39.65, "atk": 8009,  "ben": 12191, "mean_trust": 52.32},
    {"level": "L2", "entities": 78,  "action": "Restrict",   "total_flows": 7800,  "atk_p": 57.42, "atk": 4479,  "ben": 3321,  "mean_trust": 40.25},
    {"level": "L3", "entities": 7,   "action": "Quarantine", "total_flows": 700,   "atk_p": 57.57, "atk": 403,   "ben": 297,   "mean_trust": 29.55},
    {"level": "L4", "entities": 156, "action": "Quarantine", "total_flows": 15600, "atk_p": 100.0,  "atk": 15600, "ben": 0,     "mean_trust": 15.44},
    {"level": "L5", "entities": 15,  "action": "Block",      "total_flows": 1500,  "atk_p": 100.0,  "atk": 1500,  "ben": 0,     "mean_trust": 14.53},
]

COSTS = {
    "Allow":      {0: 0,  1: 100},
    "Alert":      {0: 1,  1: -5},
    "Restrict":   {0: 3,  1: -10},
    "Quarantine": {0: 15, 1: -20},
    "Block":      {0: 50, 1: -50},
}

print("=== PER-LEVEL COST BREAKDOWN ON BALANCED WINDOW ===")
tot_cost_all = 0
for row in levels:
    act = row["action"]
    c_ben = row["ben"] * COSTS[act][0]
    c_atk = row["atk"] * COSTS[act][1]
    c_tot = c_ben + c_atk
    net_ben = -c_tot
    tot_cost_all += c_tot
    print(f"{row['level']}: Entities={row['entities']:3d} | Action={act:<10} | Cost={c_tot:8d} | Net Benefit={net_ben:8d} | Atk%={row['atk_p']:6.2f}% | MeanTrust={row['mean_trust']:5.2f}")

print(f"Total Pipeline Cost: {tot_cost_all}, Net Benefit: {-tot_cost_all}")
