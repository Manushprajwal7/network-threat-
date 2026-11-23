# E3: Full Disruptive False Positive Rate Audit Across 70 Policies

## 1. Overview & Research Objective
Computes Quarantine FPR, Block FPR, and Total Disruptive FPR across all 70 admissible monotonic policies on both balanced and attack-heavy streams.

## 2. Master Configuration Anchor
All parameters, thresholds, and seeds used in this experiment are anchored in [`configs/paper.yaml`](../../configs/paper.yaml).

## 3. Execution & Verification
To reproduce this experiment independently:
```bash
bash run.sh
```
or directly via Python:
```bash
python ../../experiments/E3_full_disruption_fpr.py
python plot.py
```

## 4. Primary Results
The complete raw experimental output is archived in [`results.csv`](results.csv).
The visualization plot is automatically generated as [`plot.png`](plot.png).

## 5. Connection to Manuscript
Results from this experiment directly support the quantitative findings in the manuscript:
- Validated in Table / Figure / Section as cross-referenced in `audit_report.md`.
- Synchronized with the isolated verification archive in `paper2/clean_experiments_isolated/`.
