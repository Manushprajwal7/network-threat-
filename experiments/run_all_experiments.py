# experiments/run_all_experiments.py
"""
Master test harness to execute all 12 critical experiments E1 to E12 sequentially.
Records execution time, output verification, and error handling.
"""
import os
import sys
import time
import subprocess

EXPERIMENTS = [
    ("E12", "Fast unit test for score_samples sign convention", "experiments/E12_score_sign_test.py"),
    ("E8",  "Level L5 population test and analytical proof", "experiments/E8_l5_population_test.py"),
    ("E10", "TARP topology graph model and PageRank reproducibility", "experiments/E10_tarp_reproducibility.py"),
    ("E11", "Wilson score 95% confidence interval recomputation", "experiments/E11_wilson_ci.py"),
    ("E2",  "Held-out balanced test window evaluation", "experiments/E2_held_out_balanced.py"),
    ("E3",  "Full disruptive FPR audit (all 70 policies)", "experiments/E3_full_disruption_fpr.py"),
    ("E4",  "ADTM component weight sensitivity", "experiments/E4_adtm_weight_sensitivity.py"),
    ("E5",  "Posture threshold sensitivity analysis", "experiments/E5_threshold_sensitivity.py"),
    ("E6",  "Extended cost sensitivity sweep", "experiments/E6_extended_cost_sensitivity.py"),
    ("E7",  "Regime mixture weight sensitivity", "experiments/E7_regime_weight_sensitivity.py"),
    ("E9",  "Minimal regime-aware dynamic policy switcher", "experiments/E9_regime_aware_switcher.py"),
    ("E1",  "Multi-seed stability suite (5 seeds)", "experiments/E1_multiseed_stability.py"),
]

def main():
    print("="*80)
    print("STARTING EXECUTION OF CRITICAL EXPERIMENTS E1 - E12")
    print("="*80)
    
    total_start = time.time()
    results = []
    
    for tag, desc, script in EXPERIMENTS:
        print(f"\n>>> Running {tag}: {desc} ({script})")
        t0 = time.time()
        res = subprocess.run([sys.executable, script], capture_output=True, text=True)
        elapsed = time.time() - t0
        
        if res.returncode == 0:
            print(f">>> {tag} SUCCESS ({elapsed:.2f}s)")
            results.append((tag, "SUCCESS", elapsed, ""))
        else:
            print(f">>> {tag} FAILED ({elapsed:.2f}s)!")
            print(res.stderr)
            print(res.stdout)
            results.append((tag, "FAILED", elapsed, res.stderr))
            
    print("\n" + "="*80)
    print("EXPERIMENT SUITE EXECUTION SUMMARY")
    print("="*80)
    for tag, status, elapsed, err in results:
        print(f"  {tag:<6}: {status:<10} ({elapsed:.2f}s)")
    print(f"\nTotal elapsed time: {time.time() - total_start:.2f}s")

if __name__ == "__main__":
    main()
