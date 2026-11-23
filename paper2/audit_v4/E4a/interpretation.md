# Experiment E4a: Posture Level Density Enrichment Analysis

**Date**: 2026-11-18  
**Evaluation Target**: Statistical significance of attack enrichment over base rate per posture level across 1,000 permutations  

---

## 1. Empirical Findings & Mathematical Proof

1. **Level $L_1$ Shows Negative Attack Enrichment ($-50.20\%$, $p = 1.000$)**:
   - Observed attack density in $L_1$ is **$0.00\%$** on the multi-state benchmark stream (base rate $50.20\%$).
   - In 1,000 randomized permutations, null enrichment averaged $-0.01\%$ (95% CI: $[-0.80\%, +0.80\%]$).
   - The one-sided empirical $p$-value for positive attack enrichment is $p = 1.000$.
   - **Conclusion**: Level $L_1$ operates as an **exclusionary filter on legitimate nominal traffic** that happens to run through topologically critical ingress nodes ($R \ge 0.42$). It is not an attack-detection tier.
2. **Level $L_5$ Shows Zero Enrichment Over $L_4$**:
   - In peripheral edge streams, Level $L_5$ is unpopulated ($0$ flows) because mean edge risk $\bar{R} \approx 0.42 < 0.75$.
   - In attack-heavy streams where $L_5$ is activated for central routing hubs (Node 0, Node 4), $L_5$ attack density is **$99.43\%$**, which is statistically indistinguishable from Level $L_4$ ($99.31\%$ to $100.00\%$, $p = 0.777$).
   - **Conclusion**: Level $L_5$ provides **zero incremental attack containment or enrichment over Level $L_4$**.
   - **Mandatory Editorial Action**: Completely remove all language claiming that $L_5$ provides "containment enrichment." Characterize $L_5$ strictly as a topological priority fail-safe for backbone hubs.
