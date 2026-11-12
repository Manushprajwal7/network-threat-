# experiments/E11_wilson_ci.py
"""
E11: Exact Wilson score 95% confidence interval verification.
Uses standard closed-form Wilson score interval with scipy.stats.norm.ppf
to rigorously verify all confidence intervals reported in Tables 5 and 6.
"""
import os
import json
import pandas as pd
import numpy as np
from scipy import stats

def wilson_score_interval(k, n, confidence=0.95):
    if n == 0:
        return 0.0, 0.0
    z = stats.norm.ppf(1.0 - (1.0 - confidence) / 2.0)
    p_hat = k / n
    denom = 1.0 + z**2 / n
    centre = (p_hat + z**2 / (2.0 * n)) / denom
    margin = (z / denom) * np.sqrt(p_hat * (1.0 - p_hat) / n + z**2 / (4.0 * n**2))
    ci_low = max(0.0, centre - margin)
    ci_high = min(1.0, centre + margin)
    return ci_low, ci_high

def run_e11():
    print("=== RUNNING E11: WILSON SCORE 95% CONFIDENCE INTERVAL RECOMPUTATION ===")
    
    # 1. Attack-Heavy Stream Counts
    atk_heavy_counts = [
        {"Level": "L0", "total": 0, "attack": 0},
        {"Level": "L1", "total": 0, "attack": 0},
        {"Level": "L2", "total": 0, "attack": 0},
        {"Level": "L3", "total": 0, "attack": 0},
        {"Level": "L4", "total": 60000, "attack": 58560},
        {"Level": "L5", "total": 0, "attack": 0},
    ]
    
    # 2. Balanced Stream Counts
    balanced_counts = [
        {"Level": "L0", "total": 7700, "attack": 0},
        {"Level": "L1", "total": 10300, "attack": 0},
        {"Level": "L2", "total": 5500, "attack": 2552},
        {"Level": "L3", "total": 18500, "attack": 9566},
        {"Level": "L4", "total": 18000, "attack": 18000},
        {"Level": "L5", "total": 0, "attack": 0},
    ]
    
    def process_counts(stream_name, counts):
        rows = []
        for d in counts:
            n = d["total"]
            k = d["attack"]
            if n > 0:
                p_hat = k / n
                ci_low, ci_high = wilson_score_interval(k, n, confidence=0.95)
                ci_str = f"[{ci_low*100.0:.2f}%, {ci_high*100.0:.2f}%]"
                ci_round_str = f"[{ci_low*100.0:.1f}%, {ci_high*100.0:.1f}%]"
            else:
                p_hat = 0.0
                ci_low, ci_high = 0.0, 0.0
                ci_str = "N/A"
                ci_round_str = "N/A"
                
            rows.append({
                "Stream": stream_name,
                "Level": d["Level"],
                "Total": n,
                "Attack": k,
                "Attack Pct": f"{p_hat*100.0:.2f}%" if n > 0 else "0.00%",
                "Wilson 95% CI (Exact)": ci_str,
                "Wilson 95% CI (Paper Format)": ci_round_str
            })
        return rows
        
    all_rows = process_counts("Attack-Heavy", atk_heavy_counts) + process_counts("Balanced Stratified", balanced_counts)
    df = pd.DataFrame(all_rows)
    out_csv = "experiments/outputs/E11_wilson_ci_verification.csv"
    df.to_csv(out_csv, index=False)
    print(f"\nSaved E11 results to {out_csv}")
    print(df.to_string(index=False))

if __name__ == "__main__":
    run_e11()
