# E6: Extended False-Blocking Cost Sensitivity Sweep

## 1. Overview & Research Objective
Evaluates policy robustness over extended penalty multiplier lambda in [0.2, 20.0], scaling benign Block penalty from 10 to 1,000 OCU.

## 2. Master Configuration Anchor
All parameters, thresholds, and seeds used in this experiment are anchored in [`configs/paper.yaml`](../../configs/paper.yaml).

## 3. Execution & Verification
To reproduce this experiment independently:
```bash
bash run.sh
```
or directly via Python:
```bash
python ../../experiments/E6_extended_cost_sensitivity.py
python plot.py
```

## 4. Primary Results
The complete raw experimental output is archived in [`results.csv`](results.csv).
The visualization plot is automatically generated as [`plot.png`](plot.png).

## 5. Connection to Manuscript
Results from this experiment directly support the quantitative findings in the manuscript:
- Validated in Table / Figure / Section as cross-referenced in `audit_report.md`.
- Synchronized with the isolated verification archive in `paper2/clean_experiments_isolated/`.
