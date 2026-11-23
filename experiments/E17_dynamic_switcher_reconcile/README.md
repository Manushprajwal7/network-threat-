# Experiment E17: Dynamic Switcher & 110 OCU Reconciled

## Objective
Reconcile the 110 OCU difference between Table 8 (+1,909,843 OCU) and Section 4.4 / Experiment E9 (+1,909,733 OCU).

## Mathematical Provenance
- In Table 8, balanced net benefit is +963,686 OCU and attack-heavy is +2,856,000 OCU.
  Combined = 0.5 * 963,686 + 0.5 * 2,856,000 = +1,909,843 OCU.
- In Seed 42, minor batch randomizations yield balanced net benefit of +963,466 OCU (220 OCU lower).
  Combined = 0.5 * 963,466 + 0.5 * 2,856,000 = +1,909,733 OCU (exactly 110 OCU lower).
- Relative difference is 110 / 1,909,843 = 0.0058% (< 0.006%).

## Conclusion
The dynamic switcher matches static P2-tier within 0.006%, confirming that dynamic switching achieves the full economic benefit of P2-tier while maintaining zero Block FPR on nominal traffic.
