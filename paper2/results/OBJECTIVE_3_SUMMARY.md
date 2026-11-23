# Objective 3 Summary: Cost-Aware Policy Optimization and Action Precision Audit

## Executive Summary

Objective 3 completes the end-to-end evaluation of the corrected cybersecurity pipeline for the Q1 manuscript. The published baseline exhibited a catastrophic structural inversion in action precision: **Alert** traffic was 100.00% malicious, while the supposedly higher-severity **Quarantine** tier was only 70.50% malicious, accompanied by massive benign traffic accumulation in **Restrict** (costing \$50,355 in operational penalty).

Through cost-aware policy optimization over 65 safety-constrained mappings on the repaired Isolation Forest and recalibrated ADTM trust engine, Objective 3 delivers:

1. **Resolution of Action Precision Inversion**: Across the six-level posture model, the corrected pipeline achieves strictly non-decreasing action precision ($0.00\% < 39.65\% < 57.42\% < 98.18\% < 100.00\%$) across all five tiers on balanced traffic, eliminating all inversions.
2. **Three-Tier Policy Framework & Recommended Operational Mapping**:
   - **$P_1$ (Conservative Default Baseline)**: The initial manual mapping (`Allow-Alert-Restrict-Quarantine-Quarantine-Block`), ranking 34 of 65 by combined net benefit (+\$856,381). It raises balanced net benefit $2.94\times$ over $P_0$ (+\$153,952 $\to$ +\$453,286).
   - **$P_{2\text{-tier}}$ (Recommended Operational Policy)**: The tier-preserving optimal mapping (`Allow-Alert-Restrict-Quarantine-Block-Block`), ranking 10 of 65 by combined net benefit (+\$1,861,883). By escalating $L_4$ to Block, it adds **+\$468,000 in containment benefit with zero false positives**, achieving **+\$921,286 balanced net benefit ($5.98\times$ over $P_0$)** while strictly guaranteeing **0.00% Block FPR**.
   - **$P_2$ (Aggressive Cost-Optimal)**: The unconstrained cost-optimal mapping (`Allow-Restrict-Quarantine-Block-Block-Block`), ranking 1 of 65 (+\$1,897,691 combined benefit; +\$943,582 balanced benefit). However, it incurs an empirical **0.99% benign Block FPR** (297 legitimate devices dropped), requiring an explicit Block-tolerance SLA.
3. **$51.3\%$ Slashing of Benign Penalty**: By eliminating dysfunctional Restrict misassignments ($16,785 \to 3,321$ benign flows), benign operational penalty plummets from \$54,688 to \$26,609.
4. **Severity-Aware Trust Scoring (Documented Limitation)**: The corrected trust engine achieves a **$3.5\times$ differentiation in mean trust across attack families** (10.13 for Mirai vs 35.84 for Web). However, this differentiation does not propagate to action-level specialization under current thresholds; all attack families concentrate in Quarantine (52–73%). This is documented honestly as an empirical finding and architectural limitation.

---

## 1. Formal Cost Model & Baseline Audit (E3.1)

### Cost Matrix $\mathcal{L}(a, y)$
Operational losses are formalized in [`paper2/tables/O3_cost_matrix.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/tables/O3_cost_matrix.csv):

$$\mathcal{L}(a, y) = \begin{cases} 
C_{\text{benign}}(a) & \text{if } y = 0 \text{ (Benign)} \\
-C_{\text{containment}}(a) & \text{if } y = 1 \text{ (Attack)} 
\end{cases}$$

Net Operational Benefit is defined as $\text{Net Benefit} = -\sum_{i=1}^N \mathcal{L}(a_i, y_i)$.

| Action ($a$) | Severity Index | Benign Cost $C_{\text{benign}}(a)$ | Attack Benefit $C_{\text{containment}}(a)$ | Operational Meaning |
| :--- | :---: | :---: | :---: | :--- |
| **Allow** | 0 | 0 | $-100$ | Unimpeded traffic; unmitigated attack penalty $= 100$ |
| **Alert** | 1 | 1 | $+5$ | Passive telemetry alert; SOC investigation cost $= 1$ |
| **Restrict** | 2 | 3 | $+10$ | QoS bandwidth throttling; benign disruption $= 3$ |
| **Quarantine** | 3 | 15 | $+20$ | Isolated VLAN sandbox; severe service degradation $= 15$ |
| **Block** | 4 | 50 | $+50$ | Total TCP RST / drop; severe benign outage cost $= 50$ |

### E3.1 Baseline Cost Audit Across Evaluation Windows
Saved to [`paper2/tables/O3_E1_baseline_costs.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/tables/O3_E1_baseline_costs.csv):

| Window | Policy | Allow | Alert | Restrict | Quarantine | Block | Total Cost | Net Benefit | Attack Recall | Benign FPR | Benign Quar+Block |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Attack-Heavy 60k** | $P_0$ (Published Table 19A) | 0 | 54,553 | 0 | 5,447 | 0 | −329,835 | +329,835 | 100.00% | 100.00% | 100.00% |
| **Attack-Heavy 60k** | $P_0$ (Freshly Recomputed) | 15 | 51,076 | 1,882 | 7,027 | 0 | −395,769 | +395,769 | 100.00% | 99.06% | 0.74% |
| **Attack-Heavy 60k** | $P_1$ (Conservative Default) | 0 | 0 | 0 | 56,100 | 3,900 | **−1,259,475** | **+1,259,475** | **100.00%** | 100.00% | 100.00% |
| **Balanced 60k** | $P_0$ (Freshly Recomputed) | 11,609 | 27,287 | 17,083 | 4,021 | 0 | −153,952 | +153,952 | 99.99% | 61.32% | 0.65% |
| **Balanced 60k** | $P_1$ (Conservative Default) | 14,200 | 20,200 | 7,800 | 16,300 | 1,500 | **−453,286** | **+453,286** | **100.00%** | **52.68%** | **0.99%** |

---

## 2. Action Precision Audit & Monotonicity Recovery (E3.2)

Saved to [`paper2/tables/O3_E2_action_precision.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/tables/O3_E2_action_precision.csv):

### Empirical Comparison on Stratified Balanced Window (60,000 Flows)

| Policy | Action | Count | Share (%) | Attack Flows | Benign Flows | Attack Precision (%) | Benign Share (%) | Monotonicity Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **$P_0$ (Recomputed)** | Allow | 11,609 | 19.35% | 2 | 11,607 | 0.02% | 99.98% | Baseline |
| | Alert | 27,287 | 45.48% | 25,864 | 1,423 | 94.79% | 5.21% | Monotonic |
| | Restrict | 17,083 | 28.47% | 298 | 16,785 | **1.74%** | 98.26% | **INVERTED ($1.74\% \ll 94.79\%$)** |
| | Quarantine | 4,021 | 6.70% | 3,827 | 194 | 95.18% | 4.82% | Monotonic |
| | Block | 0 | 0.00% | 0 | 0 | — | — | Empty |
| **$P_1$ (New Pipeline)** | Allow | 14,200 | 23.67% | 0 | 14,200 | **0.00%** | 100.00% | Baseline |
| | Alert | 20,200 | 33.67% | 8,009 | 12,191 | **39.65%** | 60.35% | **Strictly Monotonic ✓** |
| | Restrict | 7,800 | 13.00% | 4,479 | 3,321 | **57.42%** | 42.58% | **Strictly Monotonic ✓** |
| | Quarantine | 16,300 | 27.17% | 16,003 | 297 | **98.18%** | 1.82% | **Strictly Monotonic ✓** |
| | Block | 1,500 | 2.50% | 1,500 | 0 | **100.00%** | 0.00% | **Strictly Monotonic ✓** |

> [!NOTE]
> In the new pipeline, action precision is strictly non-decreasing: $0.00\% < 39.65\% < 57.42\% < 98.18\% < 100.00\%$. Restrict precision jumped from a dysfunctional $1.74\%$ in $P_0$ to $57.42\%$ ($33\times$ improvement), eliminating false alarms on 13,464 benign flows.

---

## 3. Level-to-Action Mapping Optimization Sweep (E3.3)

### Formulation & Search Space
All candidate mappings $a: \{L_0, \dots, L_5\} \to \{\text{Allow}, \dots, \text{Block}\}$ were enumerated subject to:
1. **Severity Monotonicity**: $a(L_0) \le a(L_1) \le a(L_2) \le a(L_3) \le a(L_4) \le a(L_5)$
2. **Boundary Anchors**: $a(L_0) = \text{Allow}$, $a(L_5) = \text{Block}$
3. **Safety Operational Constraint**: $\text{Block FPR} \le 5.0\%$ on benign flows (excludes reckless policies that sever legitimate communications).

Out of 70 monotonic sequences, **65 mappings satisfy the safety constraint** (5 excluded where $a(L_2) = \text{Block}$, which would incur $12.06\%$ benign block FPR).

### Top 10 Mappings Ranked by Combined Net Benefit
Saved to [`paper2/tables/O3_E3_top10_mappings.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/tables/O3_E3_top10_mappings.csv):

| Rank (Comb) | Mapping Name | Mapping Definition | Combined Net Benefit | Balanced Net Benefit | Attack-Heavy Net Benefit | Block FPR (Bal) | Action Prec. Monotonic? |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **1 ($P_2$)** | **Allow-Restrict-Quarantine-Block-Block-Block** | $L_0$:All $\to$ $L_1$:Res $\to$ $L_2$:Qua $\to$ $L_3$:Blo $\to$ $L_4$:Blo $\to$ $L_5$:Blo | **+\$1,897,691** | **+\$943,582** | **+\$2,851,800** | 0.99% | **YES ✓** |
| **2** | Allow-Restrict-Restrict-Block-Block-Block | $L_0$:All $\to$ $L_1$:Res $\to$ $L_2$:Res $\to$ $L_3$:Blo $\to$ $L_4$:Blo $\to$ $L_5$:Blo | +\$1,895,222 | +\$938,644 | +\$2,851,800 | 0.99% | YES ✓ |
| **3** | Allow-Alert-Quarantine-Block-Block-Block | $L_0$:All $\to$ $L_1$:Ale $\to$ $L_2$:Qua $\to$ $L_3$:Blo $\to$ $L_4$:Blo $\to$ $L_5$:Blo | +\$1,889,860 | +\$927,919 | +\$2,851,800 | 0.99% | YES ✓ |
| **4** | Allow-Alert-Restrict-Block-Block-Block | $L_0$:All $\to$ $L_1$:Ale $\to$ $L_2$:Res $\to$ $L_3$:Blo $\to$ $L_4$:Blo $\to$ $L_5$:Blo | +\$1,887,391 | +\$922,981 | +\$2,851,800 | 0.99% | YES ✓ |
| **5** | Allow-Alert-Alert-Block-Block-Block | $L_0$:All $\to$ $L_1$:Ale $\to$ $L_2$:Ale $\to$ $L_3$:Blo $\to$ $L_4$:Blo $\to$ $L_5$:Blo | +\$1,879,514 | +\$907,228 | +\$2,851,800 | 0.99% | YES ✓ |
| **6** | Allow-Restrict-Quarantine-Quarantine-Block-Block | $L_0$:All $\to$ $L_1$:Res $\to$ $L_2$:Qua $\to$ $L_3$:Qua $\to$ $L_4$:Blo $\to$ $L_5$:Blo | +\$1,872,184 | +\$941,887 | +\$2,802,480 | **0.00%** | YES ✓ |
| **7** | Allow-Restrict-Restrict-Quarantine-Block-Block | $L_0$:All $\to$ $L_1$:Res $\to$ $L_2$:Res $\to$ $L_3$:Qua $\to$ $L_4$:Blo $\to$ $L_5$:Blo | +\$1,869,715 | +\$936,949 | +\$2,802,480 | **0.00%** | YES ✓ |
| **8** | Allow-Quarantine-Quarantine-Block-Block-Block | $L_0$:All $\to$ $L_1$:Qua $\to$ $L_2$:Qua $\to$ $L_3$:Blo $\to$ $L_4$:Blo $\to$ $L_5$:Blo | +\$1,864,590 | +\$877,380 | +\$2,851,800 | 0.99% | YES ✓ |
| **9** | Allow-Alert-Quarantine-Quarantine-Block-Block | $L_0$:All $\to$ $L_1$:Ale $\to$ $L_2$:Qua $\to$ $L_3$:Qua $\to$ $L_4$:Blo $\to$ $L_5$:Blo | +\$1,864,352 | +\$926,224 | +\$2,802,480 | **0.00%** | YES ✓ |
| **10 ($P_{2\text{-tier}}$)** | **Allow-Alert-Restrict-Quarantine-Block-Block** | $L_0$:All $\to$ $L_1$:Ale $\to$ $L_2$:Res $\to$ $L_3$:Qua $\to$ $L_4$:Blo $\to$ $L_5$:Blo | **+\$1,861,883** | **+\$921,286** | **+\$2,802,480** | **0.00%** | **YES ✓** |
| *34 ($P_1$)* | *Allow-Alert-Restrict-Quarantine-Quarantine-Block* | $L_0$:All $\to$ $L_1$:Ale $\to$ $L_2$:Res $\to$ $L_3$:Qua $\to$ $L_4$:Qua $\to$ $L_5$:Blo | +\$856,381 | +\$453,286 | +\$1,259,475 | **0.00%** | **YES ✓** |

---

## 4. L4 Block Escalation: A Free Improvement

The $L_4$ (Isolate) security posture level captures 15,600 flows on the balanced evaluation window, all 100.00% attack-labelled (0 benign flows). 

The initial manual $P_1$ mapping assigned Quarantine (cost −20/attack) to $L_4$. Escalating $L_4$ to Block (cost −50/attack) in $P_{2\text{-tier}}$ adds:
$$15,600 \times (50 - 20) = 15,600 \times 30 = \mathbf{+\$468,000}$$
in operational net benefit with **strictly zero false-positive blocks**.

This empirical finding is visualized in [`paper2/figures/O3_L4_escalation_analysis.png`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/figures/O3_L4_escalation_analysis.png):
- **Panel (a)** shows the traffic composition of $L_4$: 0 benign flows vs 15,600 attack flows.
- **Panel (b)** shows the net containment value leaping from \$312,000 (Quarantine) to \$780,000 (Block).

### Two Key Operational Lessons:
1. **Automated Policy Optimization Overcomes Heuristic Flaws**: Human operators naturally default to conservative containment tiers (assigning Quarantine to both $L_3$ and $L_4$). Exhaustive mapping search proves that $P_1$ was leaving \$468,000 of containment value on the table, ranking 34 of 65.
2. **Level-Wise Benign Composition Dictates Escalation Ceiling**: When a posture level exhibits 0.00% benign contamination, Block strictly dominates Quarantine without incurring any collateral outage penalty.

### Policy Adoption Recommendation:
We present three operational policies for enterprise adoption:
- **$P_1$ (Conservative Default Baseline)**: The manually designed baseline mapping, ranking 34 of 65. Retained for benchmark comparability.
- **$P_{2\text{-tier}}$ (Recommended Operational Policy)**: Escalates $L_4 \to \text{Block}$ while keeping $L_3 \to \text{Quarantine}$, ranking 10 of 65. It captures **$97.6\%$ of $P_2$'s benefit** (+\$921,286 vs +\$943,582) while guaranteeing **0.00% Block FPR**. Recommended for general production deployment.
- **$P_2$ (Aggressive Cost-Optimal)**: Escalates $L_3 \to \text{Block}$, achieving rank 1 (+\$943,582 balanced; +\$1,897,691 combined). It incurs an empirical **0.99% benign Block FPR** (297 legitimate devices dropped), and is recommended only for high-threat environments with automated review SLAs.

---

## 5. Per-Family Analysis: Trust Differentiation vs Action Specialization (E3.4)

Saved to [`paper2/tables/O3_E4_per_family_actions.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/tables/O3_E4_per_family_actions.csv):

### Traffic Distribution Across Families Under $P_1$ (Balanced Window)

| Traffic Family | Flow Count | Share (%) | Allow (%) | Alert (%) | Restrict (%) | Quarantine (%) | Block (%) | Dominant Action | Mean Trust | Mean TARP | Mean Cost / Flow |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Benign** | 30,009 | 50.02% | **47.32%** | 40.62% | 11.07% | 0.99% | 0.00% | **Allow** | **77.96** | 0.411 | +\$0.89 |
| **DDoS** | 22,329 | 37.21% | 0.00% | 26.71% | 15.03% | **53.30%** | 4.96% | **Quarantine** | **19.28** | 0.429 | −\$15.98 |
| **DoS** | 5,322 | 8.87% | 0.00% | 27.04% | 14.34% | **53.72%** | 4.90% | **Quarantine** | **20.71** | 0.426 | −\$15.98 |
| **Mirai** | 1,726 | 2.88% | 0.00% | 26.83% | 15.41% | **52.43%** | 5.33% | **Quarantine** | **10.13** | 0.432 | −\$16.03 |
| **Recon** | 262 | 0.44% | 0.00% | 22.90% | 15.27% | **56.11%** | 5.73% | **Quarantine** | **27.80** | 0.440 | −\$16.76 |
| **Spoofing** | 320 | 0.53% | 0.00% | 23.44% | 15.94% | **53.44%** | 7.19% | **Quarantine** | **33.48** | 0.435 | −\$17.05 |
| **Web** | 21 | 0.03% | 0.00% | 28.57% | 9.52% | **52.38%** | 9.52% | **Quarantine** | **35.84** | 0.437 | −\$17.62 |
| **BruteForce** | 11 | 0.02% | 0.00% | 18.18% | 9.09% | **72.73%** | 0.00% | **Quarantine** | **26.06** | 0.359 | −\$16.36 |

### Scientific Finding & Architectural Limitation:
1. **Trust Strongly Differentiates Families ($3.5\times$ Range)**:
   The corrected trust model achieves substantial family-level differentiation: mean trust ranges from **10.13** (Mirai, aggressive IoT botnet) to **35.84** (Web, moderate-severity application attacks), with DDoS (19.28), DoS (20.71), BruteForce (26.06), Recon (27.80), and Spoofing (33.48) spread logically across the spectrum. This confirms that the ADTM trust engine responds dynamically to attack volatility and persistence.
2. **Action Specialization Does Not Emerge**:
   However, this trust differentiation does **not** propagate to action specialization under the current level thresholds. All attack families exhibit nearly identical action profiles, concentrating in Quarantine (52–73%), because the $L_3$ mean-trust threshold of 40 absorbs the entire attack distribution. Reconnaissance (low severity) receives 56.11% Quarantine, while DDoS (high severity) receives 53.30% Quarantine.
3. **Documented Limitation & Future Work**:
   Converting continuous trust differentiation into discrete action specialization would require finer level thresholds (e.g., setting intermediate thresholds between 10, 20, and 35) or per-family policy tuning. The current pipeline provides severity-aware trust scoring and safety-constrained action assignment, but **not** per-family action specialization. This is documented as an empirical limitation rather than an over-claimed capability.

---

## 6. Master Policy Comparison (E3.5)

Saved to [`paper2/tables/O3_E5_final_comparison.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/tables/O3_E5_final_comparison.csv):

### Headline Contribution Table

| Metric | $P_0$ (Published Table 19A) | $P_0$ (Freshly Recomputed) | $P_1$ (Conservative Default) | $P_{2\text{-tier}}$ (**Recommended Operational**) | $P_2$ (Aggressive Cost-Optimal) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Pipeline Architecture** | Contaminated IF + Published Engine | Contaminated IF + Original Engine (Fair Eval) | Corrected IF + Recalibrated Trust + Default Map | Corrected Pipeline + 5-Tier Optimal Map | Corrected Pipeline + Sweep Optimal Map |
| **Level Mapping** | *Ad-hoc Rules* | *Ad-hoc Rules* | `All-Ale-Res-Qua-Qua-Blo` | `All-Ale-Res-Qua-Blo-Blo` | `All-Res-Qua-Blo-Blo-Blo` |
| **Search Space Rank** | *Manual* | *Manual* | Rank 34 of 65 | **Rank 10 of 65** | **Rank 1 of 65** |
| **Balanced Net Benefit** | *N/A (untested)* | +\$153,952 | **+\$453,286** ($2.94\times$) | **+\$921,286** ($5.98\times$) | **+\$943,582** ($6.13\times$) |
| **Attack-Heavy Net Benefit** | +\$329,835 | +\$395,769 | **+\$1,259,475** ($3.18\times$) | **+\$2,802,480** ($7.08\times$) | **+\$2,851,800** ($7.21\times$) |
| **Combined Net Benefit** | *N/A* | +\$274,861 | **+\$856,381** ($3.12\times$) | **+\$1,861,883** ($6.77\times$) | **+\$1,897,691** ($6.90\times$) |
| **Benign Penalty (Balanced)**| *N/A* | \$54,688 | **\$26,609** (−51.3%) | **\$26,609** (−51.3%) | \$101,238 |
| **Attack Containment (Bal)** | *N/A* | −\$208,640 | **−\$479,895** ($2.30\times$) | **−\$947,895** ($4.54\times$) | **−\$1,044,820** ($5.01\times$) |
| **Action Precision Ordering**| **NO (Inverted)** | **NO (Inverted)** | **YES (Strictly Monotonic)**| **YES (Strictly Monotonic)**| **YES (Strictly Monotonic)** |
| **Inversion Count** | 1 (Alert > Quar) | 1 (Alert > Restrict) | **0** | **0** | **0** |
| **Benign Block FPR (Bal)** | 0.00% | 0.00% | **0.00%** | **0.00% (Strict Zero)** | 0.99% (297 flows) |
| **Attack Recall (Bal)** | *N/A* | 99.99% | **100.00%** | **100.00%** | **100.00%** |

---

## 7. Artifact & Figure Registry

All generated artifacts, tables, and publication-ready figures are archived:

1. **Tables**:
   - Cost Matrix: [`paper2/tables/O3_cost_matrix.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/tables/O3_cost_matrix.csv)
   - E3.1 Baseline Costs: [`paper2/tables/O3_E1_baseline_costs.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/tables/O3_E1_baseline_costs.csv)
   - E3.1 Baseline Bounds: [`paper2/tables/O3_E1_baseline_bounds.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/tables/O3_E1_baseline_bounds.csv)
   - E3.1 Level Breakdown: [`paper2/tables/O3_E1_level_breakdown.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/tables/O3_E1_level_breakdown.csv)
   - E3.2 Action Precision: [`paper2/tables/O3_E2_action_precision.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/tables/O3_E2_action_precision.csv)
   - E3.3 Mapping Sweep (65 Mappings): [`paper2/tables/O3_E3_mapping_sweep.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/tables/O3_E3_mapping_sweep.csv)
   - E3.3 Top 10 Mappings: [`paper2/tables/O3_E3_top10_mappings.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/tables/O3_E3_top10_mappings.csv)
   - E3.4 Per-Family Analysis: [`paper2/tables/O3_E4_per_family_actions.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/tables/O3_E4_per_family_actions.csv)
   - E3.5 Headline Master Table: [`paper2/tables/O3_E5_final_comparison.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/tables/O3_E5_final_comparison.csv)

2. **Figures**:
   - $L_4$ Block Escalation Analysis: [`paper2/figures/O3_L4_escalation_analysis.png`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/figures/O3_L4_escalation_analysis.png)
   - Net Operational Benefit Comparison: [`paper2/figures/O3_cost_comparison_bars.png`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/figures/O3_cost_comparison_bars.png)
   - Benign Penalty Breakdown: [`paper2/figures/O3_benign_penalty_breakdown.png`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/figures/O3_benign_penalty_breakdown.png)
   - Action Precision Monotonicity: [`paper2/figures/O3_action_precision_bars.png`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/figures/O3_action_precision_bars.png)
   - Family Enforcement Heatmap: [`paper2/figures/O3_per_family_heatmap.png`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/figures/O3_per_family_heatmap.png)
   - Cost Matrix Heatmap: [`paper2/figures/O3_cost_matrix_heatmap.png`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/figures/O3_cost_matrix_heatmap.png)

3. **Code & Audit Scripts**:
   - $L_4$ Escalation Plotter: [`paper2/code/plot_l4_escalation.py`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/code/plot_l4_escalation.py)
   - Combined Optimization Engine: [`paper2/code/run_e3_combined.py`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/code/run_e3_combined.py)
   - Precision Audit: [`paper2/code/run_e3_2.py`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/code/run_e3_2.py)
   - Baseline & Bounds Audit: [`paper2/code/run_e3_1.py`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/code/run_e3_1.py)
   - Analytical Context & Notes: [`paper2/results/O3_notes.md`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/results/O3_notes.md)
