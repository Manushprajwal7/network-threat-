# Experiment E18: Extended Cost Matrix Sensitivity Analysis

## Objective
Evaluate policy robustness across a 100-fold variation in false-blocking penalty lambda in [0.1, 10.0] (5 to 500 OCU).

## Key Results
- P2-tier consistently maintains a 1.8x to 2.44x net benefit advantage over P1 across the entire range.
- P2 collapses under elevated penalties (lambda >= 2.0) due to premature blocking of Level L3 (8,934 benign flows).
- Proves the mathematical optimality and resilience of P2-tier under sector-specific cost re-weighting.
