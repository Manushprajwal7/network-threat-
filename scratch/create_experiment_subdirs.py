# scripts/create_experiment_subdirs.py
import os
import shutil
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

os.makedirs("experiments", exist_ok=True)

exp_defs = [
    {
        "id": "E1_multi_seed",
        "title": "E1: Multi-Seed Stability Suite across 5 Random Seeds",
        "raw_source": "experiments/outputs/E1_multiseed_stability.csv",
        "summary_source": "experiments/outputs/E1_multiseed_summary.csv",
        "description": "Evaluates the stability and variance of Isolation Forest anomaly detection, ADTM trust discrimination, and P2-tier net benefit across 5 random seeds (13, 42, 99, 123, 2024).",
        "script": "experiments/E1_multiseed_stability.py"
    },
    {
        "id": "E2_held_out",
        "title": "E2: Held-Out Balanced Test Partition Evaluation",
        "raw_source": "experiments/outputs/E2_held_out_balanced.csv",
        "description": "Evaluates policy out-of-sample generalization on an entirely held-out test split (Seed 99, 60,000 flows) to eliminate policy-selection bias.",
        "script": "experiments/E2_held_out_balanced.py"
    },
    {
        "id": "E3_full_disruption_fpr",
        "title": "E3: Full Disruptive False Positive Rate Audit Across 70 Policies",
        "raw_source": "experiments/outputs/E3_full_disruption_audit.csv",
        "description": "Computes Quarantine FPR, Block FPR, and Total Disruptive FPR across all 70 admissible monotonic policies on both balanced and attack-heavy streams.",
        "script": "experiments/E3_full_disruption_fpr.py"
    },
    {
        "id": "E4_adtm_weight",
        "title": "E4: ADTM Component Weight Sensitivity Analysis",
        "raw_source": "experiments/outputs/E4_adtm_weight_sensitivity.csv",
        "description": "Tests trust model robustness across 7 distinct component weight allocations (Class-heavy, Anomaly-heavy, Topo-heavy, Uniform, Extreme).",
        "script": "experiments/E4_adtm_weight_sensitivity.py"
    },
    {
        "id": "E5_threshold_sensitivity",
        "title": "E5: Security Posture Escalation Threshold Sensitivity Sweep",
        "raw_source": "experiments/outputs/E5_threshold_sensitivity.csv",
        "description": "Performs parameter sweeps over anomaly threshold tau_anom, trust threshold tau_T, classifier confidence tau_conf, and topological risk tau_topo.",
        "script": "experiments/E5_threshold_sensitivity.py"
    },
    {
        "id": "E6_cost_sensitivity",
        "title": "E6: Extended False-Blocking Cost Sensitivity Sweep",
        "raw_source": "experiments/outputs/E6_extended_cost_sensitivity.csv",
        "description": "Evaluates policy robustness over extended penalty multiplier lambda in [0.2, 20.0], scaling benign Block penalty from 10 to 1,000 OCU.",
        "script": "experiments/E6_extended_cost_sensitivity.py"
    },
    {
        "id": "E7_regime_weight",
        "title": "E7: Evaluation Stream Mixture Weight Sensitivity",
        "raw_source": "experiments/outputs/E7_regime_weight_sensitivity.csv",
        "description": "Sweeps the balanced stream mixture weight w_bal in [0.0, 1.0] to test whether P2-tier search rank stability is sensitive to regime weighting.",
        "script": "experiments/E7_regime_weight_sensitivity.py"
    },
    {
        "id": "E8_l5_population",
        "title": "E8: Posture Level L5 Theoretical & Empirical Population Proof",
        "raw_json": "experiments/outputs/E8_l5_population_analysis.json",
        "description": "Demonstrates analytically (Z = 41.25 sigma) and empirically (100,000 batches) why Level L5 is unpopulated on standard flow streams, establishing L5 as a core hub tier.",
        "script": "experiments/E8_l5_population_test.py"
    },
    {
        "id": "E9_regime_aware_switcher",
        "title": "E9: Minimal Online Regime-Aware Dynamic Policy Switcher",
        "raw_source": "experiments/outputs/E9_regime_aware_switcher.csv",
        "description": "Implements an online window detector switching between P1 and P2-tier based on batch anomaly rate and trust, resolving the static policy trade-off.",
        "script": "experiments/E9_regime_aware_switcher.py"
    },
    {
        "id": "E10_tarp_reproducibility",
        "title": "E10: TARP Graph Topology & PageRank Distribution Reproducibility",
        "raw_json": "experiments/outputs/E10_tarp_topology.json",
        "description": "Generates a Barabasi-Albert (m=2) 120-node scale-free graph with PageRank (alpha=0.85) to verify topological risk distribution properties.",
        "script": "experiments/E10_tarp_reproducibility.py"
    },
    {
        "id": "E11_wilson_ci",
        "title": "E11: Exact Closed-Form Wilson Score 95% Confidence Intervals",
        "raw_source": "experiments/outputs/E11_wilson_ci_verification.csv",
        "description": "Calculates exact Wilson score 95% confidence intervals across all active posture levels to establish statistical rigor.",
        "script": "experiments/E11_wilson_ci.py"
    },
    {
        "id": "E12_score_sign",
        "title": "E12: Isolation Forest Score Negation & Anomaly Monotonicity Test",
        "raw_json": "experiments/outputs/E12_score_sign_test.json",
        "description": "Verifies that scikit-learn Isolation Forest score_samples negation aligns anomaly scores positively with attack labels.",
        "script": "experiments/E12_score_sign_test.py"
    }
]

print("=== CREATING EXPERIMENT SUBDIRECTORIES (E1 TO E12) ===")

for exp in exp_defs:
    dir_path = os.path.join("experiments", exp["id"])
    os.makedirs(dir_path, exist_ok=True)
    
    # 1. results.csv
    csv_dest = os.path.join(dir_path, "results.csv")
    if "raw_source" in exp:
        shutil.copy(exp["raw_source"], csv_dest)
    elif "raw_json" in exp:
        with open(exp["raw_json"], "r") as fp:
            jdata = json.load(fp)
        # flatten to DataFrame
        rows = []
        for k, v in jdata.items():
            if isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    rows.append({"Parameter": f"{k}.{sub_k}", "Value": sub_v})
            else:
                rows.append({"Parameter": k, "Value": v})
        df = pd.DataFrame(rows)
        df.to_csv(csv_dest, index=False)
        
    # 2. run.sh
    sh_content = f"""#!/bin/bash
# Shell runner for {exp['title']}
set -e
echo "Running {exp['title']}..."
python ../../{exp['script']}
python plot.py
echo "{exp['id']} finished successfully!"
"""
    with open(os.path.join(dir_path, "run.sh"), "w", newline="\n", encoding="utf-8") as fp:
        fp.write(sh_content)
        
    # 3. README.md
    readme_content = f"""# {exp['title']}

## 1. Overview & Research Objective
{exp['description']}

## 2. Master Configuration Anchor
All parameters, thresholds, and seeds used in this experiment are anchored in [`configs/paper.yaml`](../../configs/paper.yaml).

## 3. Execution & Verification
To reproduce this experiment independently:
```bash
bash run.sh
```
or directly via Python:
```bash
python ../../{exp['script']}
python plot.py
```

## 4. Primary Results
The complete raw experimental output is archived in [`results.csv`](results.csv).
The visualization plot is automatically generated as [`plot.png`](plot.png).

## 5. Connection to Manuscript
Results from this experiment directly support the quantitative findings in the manuscript:
- Validated in Table / Figure / Section as cross-referenced in `audit_report.md`.
- Synchronized with the isolated verification archive in `paper2/clean_experiments_isolated/`.
"""
    with open(os.path.join(dir_path, "README.md"), "w", encoding="utf-8") as fp:
        fp.write(readme_content)
        
    print(f"Created directory and baseline files for {exp['id']}")

print("All 12 experiment subdirectories successfully initialized.")
