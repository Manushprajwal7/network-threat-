# experiments/audit/task11_wilson_cis.py
"""
TASK 11: Statistical CI Reconciliation
Recomputes exact non-degenerate Wilson 95% score confidence intervals for all proportions
in Tables 5, 6, 7, and 9.
Specifically verifies non-degenerate intervals for boundary cases (k = 0 and k = n).
Saves audit_outputs/wilson_cis.csv and markdown report.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

OUTPUT_DIR = ROOT / "audit_outputs"
REPORT_DIR = OUTPUT_DIR / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def wilson_score_interval(k, n, confidence=0.95):
    """
    Computes Wilson score interval without continuity correction.
    Non-degenerate for k = 0 and k = n.
    Returns (percentage, lower_bound_pct, upper_bound_pct).
    """
    if n == 0:
        return 0.0, 0.0, 0.0
    z = stats.norm.ppf((1 + confidence) / 2) # 1.95996 for 95%
    p = k / n
    denom = 1 + (z**2) / n
    center = (p + (z**2) / (2 * n)) / denom
    margin = (z / denom) * np.sqrt((p * (1 - p) / n) + ((z**2) / (4 * (n**2))))
    
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return round(p * 100.0, 3), round(lower * 100.0, 3), round(upper * 100.0, 3)

def run_task11():
    print("=" * 60)
    print("TASK 11: STATISTICAL CI RECONCILIATION ACROSS TABLES 5, 6, 7, 9")
    print("=" * 60)
    
    ci_records = []
    
    # -------------------------------------------------------------------------
    # TABLE 5: Attack-Heavy 60k Posture Distribution (N = 60,000)
    # -------------------------------------------------------------------------
    tab5_data = [
        {"Level": "L0", "Total": 0, "Attack": 0, "Benign": 0},
        {"Level": "L1", "Total": 0, "Attack": 0, "Benign": 0},
        {"Level": "L2", "Total": 0, "Attack": 0, "Benign": 0},
        {"Level": "L3", "Total": 0, "Attack": 0, "Benign": 0},
        {"Level": "L4", "Total": 60000, "Attack": 58560, "Benign": 1440},
        {"Level": "L5", "Total": 0, "Attack": 0, "Benign": 0},
    ]
    for d in tab5_data:
        p, low, up = wilson_score_interval(d["Attack"], d["Total"])
        ci_records.append({
            "Table": "Table 5 (Attack-Heavy Posture)",
            "Item": f"Posture {d['Level']} Attack Density",
            "k_numerator": d["Attack"],
            "n_denominator": d["Total"],
            "point_estimate_pct": p if d["Total"] > 0 else "N/A",
            "ci_lower_pct": low if d["Total"] > 0 else "N/A",
            "ci_upper_pct": up if d["Total"] > 0 else "N/A",
            "formatted_string": f"{p:.2f}% [{low:.2f}%, {up:.2f}%]" if d["Total"] > 0 else "N/A (empty)"
        })
        
    # -------------------------------------------------------------------------
    # TABLE 6: Stratified Balanced 60k Posture Distribution (N = 60,000)
    # -------------------------------------------------------------------------
    tab6_data = [
        {"Level": "L0", "Total": 7700, "Attack": 0, "Benign": 7700},
        {"Level": "L1", "Total": 10300, "Attack": 0, "Benign": 10300},
        {"Level": "L2", "Total": 5500, "Attack": 2552, "Benign": 2948},
        {"Level": "L3", "Total": 18500, "Attack": 9566, "Benign": 8934},
        {"Level": "L4", "Total": 18000, "Attack": 18000, "Benign": 0},
        {"Level": "L5", "Total": 0, "Attack": 0, "Benign": 0},
    ]
    for d in tab6_data:
        p, low, up = wilson_score_interval(d["Attack"], d["Total"])
        ci_records.append({
            "Table": "Table 6 (Balanced Posture)",
            "Item": f"Posture {d['Level']} Attack Density",
            "k_numerator": d["Attack"],
            "n_denominator": d["Total"],
            "point_estimate_pct": p if d["Total"] > 0 else "N/A",
            "ci_lower_pct": low if d["Total"] > 0 else "N/A",
            "ci_upper_pct": up if d["Total"] > 0 else "N/A",
            "formatted_string": f"{p:.2f}% [{low:.2f}%, {up:.2f}%]" if d["Total"] > 0 else "N/A (empty)"
        })

    # -------------------------------------------------------------------------
    # TABLE 7: Enforcement Queue Attack Prevalence (Balanced Stream, P2-tier)
    # -------------------------------------------------------------------------
    tab7_data = [
        {"Action": "Allow", "Total": 7700, "Attack": 0},
        {"Action": "Alert", "Total": 10300, "Attack": 0},
        {"Action": "Restrict", "Total": 5500, "Attack": 2552},
        {"Action": "Quarantine", "Total": 18500, "Attack": 9566},
        {"Action": "Block", "Total": 18000, "Attack": 18000},
    ]
    for d in tab7_data:
        p, low, up = wilson_score_interval(d["Attack"], d["Total"])
        ci_records.append({
            "Table": "Table 7 (Action Prevalence P2-tier)",
            "Item": f"Action {d['Action']} Attack Prevalence",
            "k_numerator": d["Attack"],
            "n_denominator": d["Total"],
            "point_estimate_pct": p,
            "ci_lower_pct": low,
            "ci_upper_pct": up,
            "formatted_string": f"{p:.2f}% [{low:.2f}%, {up:.2f}%]"
        })

    # -------------------------------------------------------------------------
    # TABLE 9: Threat Family Enforcement Action Allocation under P2-tier
    # -------------------------------------------------------------------------
    tab9_data = [
        {"Family": "Benign", "Total": 29882, "Actions": [("Allow", 7700), ("Alert", 10300), ("Restrict", 2948), ("Quarantine", 8934), ("Block", 0)]},
        {"Family": "DDoS", "Total": 22424, "Actions": [("Restrict", 1908), ("Quarantine", 7108), ("Block", 13408)]},
        {"Family": "DoS", "Total": 5328, "Actions": [("Restrict", 448), ("Quarantine", 1668), ("Block", 3212)]},
        {"Family": "Mirai", "Total": 1788, "Actions": [("Restrict", 150), ("Quarantine", 598), ("Block", 1040)]},
        {"Family": "Spoofing", "Total": 322, "Actions": [("Restrict", 32), ("Quarantine", 113), ("Block", 177)]},
        {"Family": "Recon", "Total": 235, "Actions": [("Restrict", 26), ("Quarantine", 82), ("Block", 127)]},
        {"Family": "Web", "Total": 15, "Actions": [("Quarantine", 2), ("Block", 13)]},
        {"Family": "BruteForce", "Total": 5, "Actions": [("Quarantine", 2), ("Block", 3)]},
        {"Family": "Malware", "Total": 1, "Actions": [("Block", 1)]},
    ]
    
    for fam in tab9_data:
        tot = fam["Total"]
        for act_name, cnt in fam["Actions"]:
            p, low, up = wilson_score_interval(cnt, tot)
            ci_records.append({
                "Table": "Table 9 (Per-Family P2-tier Actions)",
                "Item": f"{fam['Family']} -> {act_name}",
                "k_numerator": cnt,
                "n_denominator": tot,
                "point_estimate_pct": p,
                "ci_lower_pct": low,
                "ci_upper_pct": up,
                "formatted_string": f"{p:.1f}% [{low:.1f}%, {up:.1f}%]"
            })
            
    df_ci = pd.DataFrame(ci_records)
    out_csv = OUTPUT_DIR / "wilson_cis.csv"
    df_ci.to_csv(out_csv, index=False)
    print(f"Saved {len(df_ci)} recomputed Wilson CIs to {out_csv}")
    
    # Markdown Report
    report_path = REPORT_DIR / "task11_wilson_cis.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Task 11: Statistical CI Reconciliation Report\n\n")
        f.write("## 1. Mathematical Framework for Non-Degenerate Wilson Intervals\n")
        f.write("For an observed proportion $\\hat{p} = k / n$ under sample size $n$ with standard normal critical value $z = 1.95996$ (95% confidence):\n\n")
        f.write("$$\\tilde{p} = \\frac{k + z^2 / 2}{n + z^2}, \\quad \\text{Margin} = \\frac{z}{n + z^2} \\sqrt{\\frac{k(n-k)}{n} + \\frac{z^2}{4}}$$\n")
        f.write("$$\\text{CI}_{95\\%} = [\\max(0, \\tilde{p} - \\text{Margin}), \\min(1, \\tilde{p} + \\text{Margin})]$$\n\n")
        f.write("### Boundary Behavior:\n")
        f.write("- **Zero Observed Rate ($k = 0$)**: The Wilson interval yields $[0.00\\%, \\frac{z^2}{n + z^2} \\times 100\\%]$. For $n = 7,700$ (Table 6 Allow), $\\text{CI} = [0.00\\%, 0.05\\%]$. For $n = 29,882$ (Table 9 Benign Block), $\\text{CI} = [0.00\\%, 0.013\\%]$.\n")
        f.write("- **Perfect Rate ($k = n$)**: The Wilson interval yields $[(1 - \\frac{z^2}{n + z^2}) \\times 100\\%, 100.00\\%]$. For $n = 18,000$ (Table 6 Block), $\\text{CI} = [99.98\\%, 100.00\\%]$. For $n = 1$ (Malware Block), $\\text{CI} = [20.65\\%, 100.00\\%]$.\n\n")
        f.write("## 2. Master Wilson CI Reconciliation Table\n\n")
        f.write(df_ci[["Table", "Item", "k_numerator", "n_denominator", "formatted_string"]].to_markdown(index=False))
        
    print(f"Saved Task 11 report to {report_path}")

if __name__ == "__main__":
    run_task11()
