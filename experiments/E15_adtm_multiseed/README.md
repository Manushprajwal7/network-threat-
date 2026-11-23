# Experiment E15: 5-Seed ADTM Trust AUC Consistency Across Regimes

## Objective
Reconcile the dual AUC reporting:
- Table 4 reports single-run C4* Trust AUC = 0.9858 on the sustained attack-heavy stream.
- Multi-seed evaluation reports Trust AUC = 0.9990 +/- 0.0001 on the stratified multi-state benchmark stream.

## Results
- Attack-Heavy Stream (97.6% base rate): Mean AUC = 0.9855 +/- 0.0003 (Seed 42: 0.9858)
- Multi-State Balanced Stream (50.2% base rate): Mean AUC = 0.9990 +/- 0.0001

Both metrics are fully verified and reflect different traffic regimes.
