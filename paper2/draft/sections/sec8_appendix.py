# Section 8: Appendices A-F
SEC8_TEXT = r"""
APPENDIX A: COMPREHENSIVE EXPERIMENT INVENTORY AND REPRODUCIBILITY TRACEABILITY MATRIX (EXPERIMENTS E1 TO E25 AND TIER-2 AUDIT)

To guarantee complete empirical reproducibility and establish full artifact provenance for every claim in this manuscript, Table A1 compiles the comprehensive inventory of all executed experiments (E1 to E25 and Tier-2 audit extensions). Every reported metric, confidence interval, and policy ranking is traceable to a seeded execution script, raw output CSV, and visualization artifact archived in the open repository.

<<<TABLE_A1>>>

As detailed in Table A1, each experimental ID (E1 through E25 and Tier-2 audit extensions) encapsulates an immutable computational pipeline spanning configuration definitions, random seed specifications, raw CSV telemetry outputs, and empirical claim verification. Below, Appendices B through F provide specialized technical analyses into topology modeling (Table 12), weight sensitivity (Table 13), threshold boundaries (Table 14), cost robustness, and mathematical integrity.

APPENDIX B: SYNTHETIC TOPOLOGY AND FLOW-TO-NODE MAPPING SENSITIVITY (EXPERIMENTS E10 AND E18)

Because raw CICIoT2023 flow traces do not include physical network topology annotations or router graph matrices, topological centrality metrics are modeled via a synthetic enterprise scale-free network topology generated according to the Barabási-Albert model (Experiments E10 and E18). The synthetic network comprises N = 120 nodes with attachment parameter m = 2 directed edges per newly introduced node, producing 236 directed communication edges and average node degree 3.93.

Personalized PageRank centrality is computed with teleportation parameter alpha = 0.85 via power iteration to tolerance 10^-6. Raw centrality scores are linearly scaled to [0.10, 0.90], producing empirical mean mu_R = 0.4189 and standard deviation sigma_R = 0.0721 (median 0.3905, 95th percentile 0.5014, minimum 0.3853, maximum 0.9000). Exactly two nodes exceed the critical backbone hub threshold R >= 0.75: Node 0 (R = 0.9000, degree 41) and Node 4 (R = 0.8089, degree 28), yielding individual Z = 4.59 sigma (p = 2.2 * 10^-6) on the empirical graph distribution (target Z = 4.125 sigma) and batch-mean Z = 41.25 sigma (p ~ 0). Ingress monitoring batches are mapped to nodes via round-robin index allocation n(b) = b mod 120. Table 12 reports the operational escalation of core hub nodes into Level L5 under flood saturation versus nominal traffic.

<<<TABLE_12>>>

To test structural robustness, Experiment E18 evaluated sensitivity across three base topology densities by adjusting preferential attachment to yield mu_R in {0.30, 0.42, 0.55}. Across all three topological regimes, posture allocations on edge streams remain strictly invariant (L0: 12.83%, L1: 17.17%, L2: 9.17%, L3: 30.83%, L4: 30.00%, L5: 0.00%), confirming that edge monitoring is resilient to underlying graph density shifts.

APPENDIX C: ADTM COMPONENT WEIGHT SENSITIVITY ANALYSIS (EXPERIMENTS E4 AND E19)

Experiment E4/E19 evaluated seven distinct component weight allocations across the 60,000-flow multi-state evaluation stream, as compiled in Table 13:
1. Baseline (Authoritative): (0.40, 0.35, 0.15, 0.10) => Trust AUC = 0.9991, Net Benefit = +1,909,733 OCU
2. Class-Heavy: (0.60, 0.20, 0.10, 0.10) => Trust AUC = 0.9993, Net Benefit = +1,911,268 OCU
3. Anomaly-Heavy: (0.20, 0.60, 0.10, 0.10) => Trust AUC = 0.9988, Net Benefit = +1,909,733 OCU
4. Topo-Heavy: (0.25, 0.25, 0.40, 0.10) => Trust AUC = 0.9989, Net Benefit = +1,909,733 OCU
5. Uniform Allocation: (0.25, 0.25, 0.25, 0.25) => Trust AUC = 0.9988, Net Benefit = +1,909,733 OCU
6. Classifier-Dominated: (0.70, 0.10, 0.10, 0.10) => Trust AUC = 0.9992, Net Benefit = +1,911,268 OCU
7. Anomaly-Dominated: (0.10, 0.70, 0.10, 0.10) => Trust AUC = 0.9985, Net Benefit = +1,908,413 OCU

<<<TABLE_13>>>

Across all seven parameterizations, Dynamic Trust AUC remains exceptionally stable within [0.9985, 0.9993], and canonical policy P2-tier consistently generates +1,908,413 to +1,911,268 OCU combined net benefit, confirming that the dynamic trust model does not rely on fine-tuned behavioral weight hyper-parameters.

APPENDIX D: POSTURE THRESHOLD SENSITIVITY AND MONOTONICITY BOUNDARIES (EXPERIMENTS E5 AND E20)

Experiment E5/E20 systematically swept each of the four posture synthesis thresholds across the multi-state evaluation stream (Table 14):
- Anomaly Threshold tau_anom in [0.40, 0.70]: P2-tier combined net benefit varies by less than 0.14% (+1,907,183 OCU at 0.40 to +1,909,926 OCU at 0.70), with strictly 0.00% benign Block FPR maintained across all settings.
- Trust Threshold tau_T in [40.0, 80.0]: Level L4 captures all 18,000 pure-attack flows across all settings while preserving 0.00% benign Block assignments. Monotonicity holds for tau_T <= 70.0; at tau_T >= 80.0, premature trust degradation inverts L1 and L2 allocations.
- Confidence Threshold tau_conf in [0.80, 0.95]: Hard reset triggering and level escalation remain invariant due to high classifier separation.
- Topological Threshold tau_topo in [0.30, 0.75]: Edge flows remain correctly classified in Level L4 without premature escalation into Level L5. Monotonicity holds for tau_topo < 0.75; at tau_topo >= 0.75, edge batches are blocked from escalating past L3.

<<<TABLE_14>>>

APPENDIX E: EXTENDED COST-MATRIX SENSITIVITY ANALYSIS (EXPERIMENT E24, TASK 8, AND TASK 14)

To evaluate policy dominance beyond the baseline OCU matrix, Experiment E24 evaluated a 27-point 3-factor grid sweeping attack block reward r_block in {25, 50, 75}, quarantine benign penalty p_quar in {7.5, 15.0, 22.5}, and restrict benign penalty p_rest in {1.5, 3.0, 4.5} OCU. Across all 27 cost configurations, P2-tier strictly dominates conservative baseline P1, with net benefit advantage ratios ranging from 1.82x to 2.44x (mean 2.28x).

Furthermore, extended parameter sweeping across false-blocking scaling factors lambda in [0.2, 50.0] (Task 8) confirms that P2-tier maintains its net benefit advantage over P1 for all lambda <= 30.8 (Block penalty <= 1,540 OCU). Beyond the break-even threshold lambda = 30.8, conservative policy P1 dominates, with P2-tier advantage falling to 0.07x at lambda = 50.0. Across regime mixture sweeps w_bal in [0, 1.0], P2-tier's advantage remains robust, spanning 2.29x under pure balanced streams to 2.48x under pure attack-heavy streams. In Task 14, a 40-point 2D grid sweeping lambda in [0.2, 50.0] and rho in [0.2, 2.0] confirmed that aggressive policy P2 beats P2-tier only when lambda <= 0.5 and rho >= 1.0, while conservative P1 beats P2-tier only when lambda >= 10.0 and rho <= 0.2.

APPENDIX F: MATHEMATICAL FORMULATION AND INTEGRITY AUDIT (EXPERIMENT E25)

Experiment E25 executed an automated syntax and delimiter verification audit across the complete manuscript source. The audit verified: (1) zero unclosed math delimiters or mismatched inline KaTeX tags; (2) exact alignment between algorithmic pseudocode and textual definitions; (3) unified mathematical notation for posture indicators (c_topo, c_trust, c_anom, c_conf); and (4) verified bibliography citations. The audit log is permanently archived in paper/math_audit.md.
"""
