# Task 4 Report: Reconciliation of E21 Arithmetic and Combined Net Benefit

## 1. Discrepancy Origin Traced
The manuscript exhibited a historical divergence between three numbers:
1. `+1,907,922 OCU`: Formed by (959,843 + 2,856,000) / 2 = 1,907,921.5 ~= +1,907,922 OCU, pairing the held-out balanced stream (Seed 99, +959,843 OCU) with the benchmark attack-heavy stream (+2,856,000 OCU).
2. `+1,911,721.5 OCU`: Formed by (959,843 + 2,863,600) / 2 = 1,911,721.5 OCU, pairing the held-out balanced stream (Seed 99, +959,843 OCU) with the held-out test attack-heavy stream (Seed 99, +2,863,600 OCU).
3. `+1,907,694 OCU`: Formed by an early iteration where balanced net benefit was +959,388 OCU paired with +2,856,000 OCU: (959,388 + 2,856,000) / 2 = 1,907,694.0 OCU.

## 2. Standardized Reporting Matrix
To eliminate ambiguity, all references are standardized:
- **Held-Out Balanced Split alone (E21, Seed 99)**: +959,843 OCU, Block FPR = 0.23% (Wilson 95% CI: [0.18%, 0.29%]), Quarantine FPR = 30.72% ([30.21%, 31.25%]).
- **Combined with Master Attack-Heavy (+2,856,000 OCU)**: +1,907,922 OCU.
- **Combined with Seed 99 Attack-Heavy (+2,863,600 OCU)**: +1,911,721.5 OCU.
- Both pairings and their exact arithmetic are explicitly stated in Section 4.3.2, Appendix A, and `claimed_vs_proven.md`.
