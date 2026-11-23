sec8_content = r'''# Section 8: Appendices A-E
SEC8_TEXT = r"""APPENDIX A: COMPREHENSIVE EXPERIMENT INVENTORY AND REPRODUCIBILITY TRACEABILITY MATRIX (EXPERIMENTS E1 TO E24)

To guarantee complete empirical reproducibility and establish full artifact provenance for every claim in this manuscript, Table A1 compiles the comprehensive inventory of all executed experiments across the audit suite (Experiments E1 to E24). Every reported metric, confidence interval, and policy ranking is traceable to a seeded execution script, raw output CSV, and visualization artifact archived in the open repository and cryptographically hashed with SHA-256 checksums in `audit_v3/E11_reproducibility/MANIFEST.sha256`.

<<<TABLE_A1>>>

As detailed in Table A1, each experimental ID (E1 through E24) encapsulates an immutable computational pipeline spanning configuration definitions, random seed specifications, raw CSV telemetry outputs, and empirical claim verification. Below, Appendices B through E provide specialized technical analyses into topology modeling, weight sensitivity, threshold boundaries, and cost robustness.

APPENDIX B: SYNTHETIC TOPOLOGY AND FLOW-TO-NODE MAPPING SENSITIVITY (EXPERIMENTS E3 AND E10)

Because raw CICIoT2023 flow traces do not include physical network topology annotations or router graph matrices, topological centrality metrics are modeled via a synthetic enterprise scale-free network topology generated according to the Barabási-Albert model (Experiments E3 and E10). The synthetic network comprises $N = 120$ nodes with attachment parameter $m = 2$ directed edges per newly introduced node, producing 236 directed communication edges and average node degree $\bar{k} = 3.93$. In contrast, the preliminary configuration in foundational study [1] utilized $m = 3$ attachment (producing 342 edges and average degree $\bar{k} = 5.70$).

Personalized PageRank centrality is computed with teleportation parameter $\alpha = 0.85$ via power iteration to tolerance $10^{-6}$. Centrality scores across the synthetic topology span from minimum $R_{\min} = 0.3853$ to maximum $R_{\max} = 0.9000$, producing empirical mean $\mu_R = 0.4189$ and standard deviation $\sigma_R = 0.0721$ (derived from target normal distribution $\mathcal{N}(0.42, 0.08)$). Exactly two nodes exceed the critical backbone hub threshold $R \ge 0.75$: Node 0 ($R = 0.9000$, degree 41) and Node 4 ($R = 0.8089$, degree 28), yielding individual node criticality $Z = 4.5931\sigma$ on the empirical graph distribution. This Z-score represents a descriptive property of the synthetic generator distribution rather than empirical statistical proof of network defense efficacy. We note that topological risk $R$ is assigned per ingress node and remains identical across all 100 flows within any single monitoring batch. Ingress monitoring batches are mapped to nodes via round-robin index allocation $n(b) = b \pmod{120}$. Consequently, $c_{\text{topo}}$ carries no dynamic traffic information. Table 12 reports the operational escalation of core hub nodes into Level $L_5$ under flood saturation versus nominal traffic.

<<<TABLE_12>>>

To test structural robustness, sensitivity testing evaluated three base topology densities by adjusting preferential attachment to yield $\mu_R \in \{0.30, 0.42, 0.55\}$. Across all three topological regimes, posture allocations on edge streams remain strictly invariant ($L_0$: 12.83%, $L_1$: 17.17%, $L_2$: 9.17%, $L_3$: 30.83%, $L_4$: 30.00%, $L_5$: 0.00%), indicating that edge monitoring is resilient to underlying graph density shifts.

APPENDIX C: ADTM COMPONENT WEIGHT SENSITIVITY ANALYSIS (EXPERIMENT E4)

Component weight evaluation across seven distinct weight allocations on the 60,000-flow multi-state evaluation stream demonstrates stability:
1. Baseline (Reference Controlled): $(0.40, 0.35, 0.15, 0.10) \implies \text{Trust AUC} = 0.9991, \text{Net Benefit} = +1,909,733 \ \text{OCU}$
2. Class-Heavy (+50%): $(0.60, 0.20, 0.10, 0.10) \implies \text{Trust AUC} = 0.9993, \text{Net Benefit} = +1,909,733 \ \text{OCU}$
3. Anomaly-Heavy (+50%): $(0.25, 0.525, 0.125, 0.10) \implies \text{Trust AUC} = 0.9989, \text{Net Benefit} = +1,910,263 \ \text{OCU}$
4. Topo-Heavy (+50%): $(0.35, 0.325, 0.225, 0.10) \implies \text{Trust AUC} = 0.9990, \text{Net Benefit} = +1,909,733 \ \text{OCU}$
5. Uniform Allocation: $(0.25, 0.25, 0.25, 0.25) \implies \text{Trust AUC} = 0.9988, \text{Net Benefit} = +1,909,733 \ \text{OCU}$
6. Classifier-Dominated: $(0.70, 0.10, 0.10, 0.10) \implies \text{Trust AUC} = 0.9993, \text{Net Benefit} = +1,909,733 \ \text{OCU}$
7. Anomaly-Dominated: $(0.10, 0.70, 0.10, 0.10) \implies \text{Trust AUC} = 0.9985, \text{Net Benefit} = +1,911,268 \ \text{OCU}$

<<<TABLE_13>>>

Across all seven parameterizations, Dynamic Trust AUC remains stable within $[0.9985, 0.9993]$, and canonical policy $P_{2\text{-tier}}$ consistently generates $+1,908,413$ to $+1,911,268$ OCU combined net benefit, demonstrating that the dynamic trust model does not rely on fine-tuned behavioral weight hyper-parameters.

APPENDIX D: POSTURE THRESHOLD SENSITIVITY AND MONOTONICITY BOUNDARIES (EXPERIMENTS E5 AND E8)

Systematic sweeping across each of the four posture synthesis thresholds over the multi-state evaluation stream establishes:
- Anomaly Threshold $\tau_{\text{anom}} \in [0.40, 0.70]$: $P_{2\text{-tier}}$ combined net benefit varies by less than 0.17% (+1,907,183 OCU at 0.40 to +1,910,500 OCU at 0.70), with strictly 0.00% benign Block FPR maintained across all settings.
- Trust Threshold $\tau_T \in [40.0, 80.0]$: Level $L_4$ captures all 18,000 pure-attack flows across all settings while preserving 0.00% benign Block assignments. Monotonicity holds for $\tau_T \le 70.0$; at $\tau_T \ge 80.0$, premature trust degradation inverts $L_1$ and $L_2$ allocations.
- Confidence Threshold $\tau_{\text{conf}} \in [0.80, 0.95]$: Hard reset triggering and level escalation remain invariant due to high classifier separation.
- Topological Threshold $\tau_{\text{topo}} \in [0.30, 0.75]$: Edge flows remain correctly classified in Level $L_4$ without premature escalation into Level $L_5$. Monotonicity holds for $\tau_{\text{topo}} < 0.75$; at $\tau_{\text{topo}} \ge 0.75$, edge batches are blocked from escalating past $L_3$.

<<<TABLE_14>>>

APPENDIX E: EXTENDED COST-MATRIX SENSITIVITY ANALYSIS (EXPERIMENT E8)

To evaluate policy dominance beyond the baseline OCU matrix, sensitivity testing evaluated a 27-point 3-factor grid sweeping attack block reward $r_{\text{block}} \in \{25, 50, 75\}$, quarantine benign penalty $p_{\text{quar}} \in \{7.5, 15.0, 22.5\}$, and restrict benign penalty $p_{\text{rest}} \in \{1.5, 3.0, 4.5\}$ OCU. Across all 27 cost configurations, $P_{2\text{-tier}}$ strictly dominates conservative baseline $P_1$, with net benefit advantage ratios ranging from 1.82x to 2.44x (mean 2.28x).

Furthermore, extended parameter sweeping across false-blocking scaling factors $\lambda \in [0.2, 50.0]$ shows that $P_{2\text{-tier}}$ maintains its net benefit advantage over $P_1$ for all $\lambda \le 30.8$ (Block penalty $\le 1,540$ OCU). Beyond the break-even threshold $\lambda = 30.8$, conservative policy $P_1$ dominates, with $P_{2\text{-tier}}$ advantage falling to 0.07x at $\lambda = 50.0$. Across regime mixture sweeps $w_{\text{bal}} \in [0, 1.0]$, $P_{2\text{-tier}}$'s advantage remains robust, spanning 2.29x under pure balanced streams to 2.48x under pure attack-heavy streams. In a 40-point 2D grid sweeping $\lambda \in [0.2, 50.0]$ and $\rho \in [0.2, 2.0]$, aggressive policy $P_2$ beats $P_{2\text{-tier}}$ only when $\lambda \le 0.5$ and $\rho \ge 1.0$, while conservative $P_1$ beats $P_{2\text{-tier}}$ only when $\lambda \ge 10.0$ and $\rho \le 0.2$.
"""
'''

with open('draft/sections/sec8_appendix.py', 'w', encoding='utf-8') as f:
    f.write(sec8_content)

print("Successfully updated draft/sections/sec8_appendix.py")
