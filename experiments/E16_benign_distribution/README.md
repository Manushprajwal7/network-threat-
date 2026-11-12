# Experiment E16: Benign Traffic Allocation Audit (Section 6.4 Reconciliation)

## Objective
Reconcile Section 6.4 text numbers against Table 9:
- Section 6.4 previously reported Alert 40.62%, Restrict 11.07% (51.69% / 52.68%), which was derived from a legacy 30,009-flow split under P1.
- Under the authoritative 29,882-flow balanced partition and recommended policy P2-tier:
  - Allow: 25.8% (7,700 flows)
  - Alert: 34.4% (10,300 flows)
  - Restrict: 9.9% (2,948 flows)
  - Quarantine: 29.9% (8,934 flows)
  - Block: 0.0% (0 flows)
  - Non-disruptive attention (Alert + Restrict): 44.3%
  - Total non-Allow allocation (attention overhead): 74.2%

## Resolution
Section 6.4 is updated to reflect the authoritative numbers (Alert 34.4%, Restrict 9.9%, Quarantine 29.9%), citing Table 9 and eliminating the obsolete legacy split reference.
