# E11: Exact Closed-Form Wilson Score 95% Confidence Intervals

## 1. Overview & Research Objective
Calculates exact Wilson score 95% confidence intervals across all active posture levels to establish statistical rigor.

## 2. Master Configuration Anchor
All parameters, thresholds, and seeds used in this experiment are anchored in [`configs/paper.yaml`](../../configs/paper.yaml).

## 3. Execution & Verification
To reproduce this experiment independently:
```bash
bash run.sh
```
or directly via Python:
```bash
python ../../experiments/E11_wilson_ci.py
python plot.py
```

## 4. Primary Results
The complete raw experimental output is archived in [`results.csv`](results.csv).
The visualization plot is automatically generated as [`plot.png`](plot.png).

## 5. Connection to Manuscript
Results from this experiment directly support the quantitative findings in the manuscript:
- Validated in Table / Figure / Section as cross-referenced in `audit_report.md`.
- Synchronized with the isolated verification archive in `paper2/clean_experiments_isolated/`.
