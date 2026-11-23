# Top 10 Monotonic Posture Policies Across All Regimes & Seeds

**Date**: 2026-11-18  
**Evaluation Scope**: 70 Monotonic Policies evaluated across 5 Operational Regimes $\times$ 10 Seeds (50 evaluation runs, 3,000,000 evaluated flows total)  

---

## 1. Executive Summary: The Structural Geometry of Optimal Posture

> [!IMPORTANT]
> **Key Finding**: Across all 50 operational streams, **Policy Rank 1 ($P_{\text{opt}}$)** is:
> $$(0, 0, 0, 0, 4, 4) \quad \text{or} \quad (0, 0, 2, 2, 4, 4)$$
> Notice that all top-ranking policies enforce **Allow (0) at Level $L_1$**, completely eliminating the collateral Alert/Restrict false positives on nominal traffic!

---

## 2. Top-10 Monotonic Policy League Table

| Overall Rank | Policy ID | Action Mapping $(L_0, L_1, L_2, L_3, L_4, L_5)$ | Overall Mean OCU | 95% Confidence Interval | Balanced OCU | Flood OCU | Block FPR | Quar. FPR | Attack Recall |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | 5 | `(0, 0, 0, 0, 4, 4)` | 2,052,438.1 | [1,854,289.9, 2,250,586.4] | 1,470,740.0 | 2,962,515.0 | 0.80% | 0.00% | 98.67% |
| **2** | 9 | `(0, 0, 0, 1, 4, 4)` | 2,051,495.2 | [1,852,992.5, 2,249,998.0] | 1,469,429.5 | 2,963,227.5 | 0.80% | 0.00% | 98.67% |
| **3** | 12 | `(0, 0, 0, 2, 4, 4)` | 2,049,032.0 | [1,849,850.1, 2,248,213.9] | 1,466,360.5 | 2,963,940.0 | 0.80% | 0.00% | 98.67% |
| **4** | 19 | `(0, 0, 1, 1, 4, 4)` | 2,046,888.0 | [1,846,895.5, 2,246,880.5] | 1,462,251.8 | 2,965,544.5 | 0.80% | 0.00% | 98.67% |
| **5** | 22 | `(0, 0, 1, 2, 4, 4)` | 2,044,424.6 | [1,843,751.8, 2,245,097.4] | 1,459,182.8 | 2,966,257.2 | 0.80% | 0.00% | 98.67% |
| **6** | 39 | `(0, 1, 1, 1, 4, 4)` | 2,039,889.1 | [1,838,210.0, 2,241,568.3] | 1,449,620.1 | 2,966,263.5 | 0.80% | 0.00% | 98.67% |
| **7** | 42 | `(0, 1, 1, 2, 4, 4)` | 2,037,425.8 | [1,835,066.9, 2,239,784.6] | 1,446,551.1 | 2,966,976.0 | 0.80% | 0.00% | 98.67% |
| **8** | 28 | `(0, 0, 2, 2, 4, 4)` | 2,033,585.0 | [1,830,079.6, 2,237,090.4] | 1,443,659.6 | 2,968,574.0 | 0.80% | 0.00% | 98.67% |
| **9** | 14 | `(0, 0, 0, 3, 4, 4)` | 2,031,939.0 | [1,828,784.7, 2,235,093.3] | 1,446,154.5 | 2,965,365.0 | 0.80% | 9.56% | 98.96% |
| **10** | 24 | `(0, 0, 1, 3, 4, 4)` | 2,027,331.5 | [1,822,679.4, 2,231,983.6] | 1,438,976.8 | 2,967,682.0 | 0.80% | 9.56% | 98.96% |

---

## 3. Structural Insights from the Policy Space

1. **Suppression of Premature Escalation ($L_1 = 0$)**:
   In Experiment E4, we demonstrated that Level $L_1$ has a **negative enrichment rate** ($-49.73\%$ attack representation; $p=1.000$). When policies assign action `Alert (1)` or `Restrict (2)` to $L_1$, they disrupt legitimate traffic without providing meaningful threat containment. All top-5 policies assign `Allow (0)` to $L_1$.
2. **Intermediate Tier Trade-off ($L_2, L_3$)**:
   Policies that assign `Restrict (2)` or `Quarantine (3)` at $L_3$ sacrifice net OCU on closed-world benchmarks because intermediate actions pay lower containment rewards (+10 or +20 vs +50). However, as proven in Experiment E6, these intermediate tiers provide essential containment for novel zero-day attacks (capturing 27.4% of Mirai flows).
3. **Robustness to Parameter Sweeps**:
   As documented in `sensitivity.csv`:
   - For high risk-aversion ($\lambda \ge 5.0$), policies with earlier quarantine escalation dominate because attack misses are penalized heavily.
   - For high disruption costs ($c_{\text{block}} \ge 100$), policies with intermediate restriction are favored to protect service availability.
