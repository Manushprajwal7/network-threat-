import csv

rows = [
    [
        "Policy", "Mapping (L0-L5)", "Balanced Net Benefit (OCU)", "Attack-Heavy Net Benefit (OCU)",
        "Combined Net Benefit (OCU)", "Balanced Benign Penalty (OCU)", "Attack-Heavy Benign Penalty (OCU)",
        "Balanced Block FPR (%)", "Attack-Heavy Block FPR (%)", "Search Rank"
    ],
    [
        "P0 (Baseline [1])", "Heuristic (Alert/Quar)", "N/A", "+329,835", "N/A", "N/A", "N/A", "0.00%", "0.00%", "Unranked"
    ],
    [
        "P1 (Default Policy)", "Allo-Aler-Rest-Quar-Quar-Bloc", "+423,686", "+1,149,600", "+786,643", "153,154", "21,600", "0.00%", "0.00%", "Rank 44 of 70"
    ],
    [
        "P2-tier (Recommended)", "Allo-Aler-Rest-Quar-Bloc-Bloc", "+963,686", "+2,856,000", "+1,909,843", "153,154", "72,000", "0.00%", "100.00%", "Rank 9 of 70"
    ],
    [
        "P2 (Cost-Optimal)", "Allo-Rest-Quar-Bloc-Bloc-Bloc", "+907,520", "+2,856,000", "+1,881,760", "252,982", "72,000", "29.90%", "100.00%", "Rank 28 of 70"
    ]
]

with open("paper2/tables/tab7_master_policy.csv", "w", newline="", encoding="utf-8") as fp:
    writer = csv.writer(fp)
    writer.writerows(rows)

print("Updated tab7_master_policy.csv with explicit balanced and attack-heavy columns!")
