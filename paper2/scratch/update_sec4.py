sec4_content = r'''# Section 4: Experimental Results
SEC4_TEXT = r"""4. EXPERIMENTAL RESULTS

4.1 Isolation Forest Contamination and Dynamic Trust Recalibration

4.1.1 Controlled Isolation Forest Anomaly Detection Comparison
Table 3 reports the performance metrics across controlled model configurations on 60,000 evaluation flows (58,542 attack and 1,458 benign). In earlier iterations, the contaminated Isolation Forest ($M=200$) achieved a raw ROC AUC of 0.0084 (rounding to 0.008), completely inverting normal detection semantics. Benign traffic received an average anomaly score of 0.6810 while attack traffic averaged 0.3837, producing a negative anomaly gap of -0.2973. Despite this directional inversion, the Kolmogorov-Smirnov statistic was $D = 0.9504$, reflecting strong two-sample distributional divergence that had been inverted in orientation.

Retraining on clean benign telemetry restores in-distribution anomaly detection to ROC AUC 0.9523 ($M=200$, DeLong 95% CI: [0.9482, 0.9564], Kolmogorov-Smirnov $D = 0.8659, p < 10^{-15}$) and 0.9435 ($M=100$). The anomaly gap shifts from negative to positive (+0.0819), with attack traffic scoring 0.5847 and clean benign traffic scoring 0.5028. Figure 2 visualizes this diagnostic breakthrough.

Dose-response experiments systematically varying contamination rates demonstrate that performance degrades non-linearly: 0% (AUC 0.9427), 1% (AUC 0.9686), 2% (AUC 0.9566), 5% (AUC 0.8219), 10% (AUC 0.5794), 20% (AUC 0.2457), 50% (AUC 0.0600), 80% (AUC 0.0206), and 97.6% (AUC 0.0088). Inversion begins at 10% contamination and exhibits directional reversal at 20%. Benchmarking alternative detectors reveals that an empirical copula detector (ECOD) achieves AUC 0.977, Diagonal Mahalanobis distance achieves AUC 0.963, and inverting the contaminated Isolation Forest achieves AUC 0.9916 on this split. These results confirm that retraining represents defect diagnosis and repair rather than detector optimality.

4.1.2 Progressive Dynamic Trust Model Recalibration
Table 4 details the trust band distributions across five progressive calibration configurations ($C_0^*$ to $C_4^*$) on the 60,000-flow attack-heavy stream under universal neutral prior $T_0 = 100.0$ without label leakage. In the baseline configuration ($C_0^*$), uncalibrated inputs cause trust scores to collapse into a narrow range: 99.97% of attack flows remain in the High Trust band ($\bar{T} = 94.27$), yielding an inverted AUC of 0.0441 (rounding to 0.044).

Replacing contaminated anomaly telemetry with clean calibrated scores ($C_1^*$) restores basic discrimination, elevating trust AUC to 0.9492. Progressively integrating dynamic behavioral component weights ($C_2^*$, AUC 0.9964 on balanced streams) and joint hard resets ($C_4^*$) elevates final trust AUC to 0.9858 (rounding to 0.986) on the 60,000-flow attack-heavy stream and 0.9990 on balanced streams. Attack flows average a trust score of 12.98, with 91.34% concentrating in the Critical trust band ($[0, 20]$). Figure 3 visualizes the evolution of dynamic trust band distributions.

We note two methodological caveats: first, benign flows under attack-heavy saturation incur an availability penalty deduction (10.0 deduction per 10% packet drop), depressing their mean trust to 32.96; second, trust scores on replayed packet streams exhibit temporal autocorrelation due to EWMA smoothing ($k=0.30$), so reported AUC metrics reflect closed-world sequential discrimination.

4.1.3 Temporal Trust Kinematics
Figure 4 displays the dynamic trust traces over a 100-flow sequence under Algorithm 2 for four representative traffic streams:
1. Clean Benign: Operates with stable trust ($\bar{T} \approx 85.0$), occasionally dipping to 75.0 during minor protocol fluctuations.
2. Intermittent Anomaly: Experiences temporary trust degradation down to 45.0, recovering smoothly within 8 to 12 flows via EWMA smoothing.
3. Reconnaissance Probe: Shows gradual trust erosion down to 35.0 as low-rate scanning persists across observation windows.
4. Volumetric Flood / Mirai Infection: Emits an initial high-confidence packet with extreme anomaly, immediately triggering hard reset to $T = 10.0$, remaining pinned in the Critical band ($[0, 20]$).

4.2 Security Posture Escalation Validation

4.2.1 Posture Dynamics Under Sustained Flooding (Attack-Heavy Regime)
Table 5 presents the batch distribution across posture levels on the sustained volumetric attack-heavy stream (60,000 flows, 600 batches of $W=100$ flows, 97.60% attack base rate). Under sustained saturation, multi-stage evidence consistently reaches $S \ge 3$ with mean trust $\bar{T} = 10.70$ and mean topological risk $\bar{R} = 0.4201$. Consequently, all 600 batches concentrate in Level $L_4$ (Severe Containment - Peripheral / Off-Hub). Level $L_4$ captures 58,560 attack flows and 1,440 benign flows (97.60% attack composition, 95% CI: [97.47%, 97.72%]). Zero batches escalate into Level $L_5$ because edge gateway topology ($\bar{R} \approx 0.42$) remains strictly below the critical hub threshold $\tau_{\text{topo}} = 0.75$.

4.2.2 Posture Dynamics Under Multi-State Traffic (Balanced Benchmark)
Table 6 presents the batch distribution on the stratified multi-state benchmark stream (60,000 flows, 600 batches, 50.20% attack base rate). On this stream, active levels populate with non-decreasing attack density ($0.00\% \le 0.00\% \le 46.40\% \le 51.71\% \le 100.00\%$) and monotonic trust decay ($79.44 \ge 79.27 \ge 28.93 \ge 25.78 \ge 10.17$):
- Level $L_0$ (Normal Monitoring): 77 batches (7,700 flows), 0.00% attack density, mean trust 79.44.
- Level $L_1$ (Topology-Prior Monitoring): 103 batches (10,300 flows), 0.00% attack density, mean trust 79.27, populated by nominal traffic mapped to assets with $R \ge 0.42$.
- Level $L_2$ (Contextual Evaluation): 55 batches (5,500 flows), 46.40% attack density, mean trust 28.93.
- Level $L_3$ (Active Containment): 185 batches (18,500 flows), 51.71% attack density, mean trust 25.78.
- Level $L_4$ (Severe Containment): 180 batches (18,000 flows), 100.00% attack density, mean trust 10.17.
- Level $L_5$ (Critical Hub Containment): 0 batches (0 flows), mean trust N/A.

Figure 5 illustrates this escalation profile. While attack density is non-decreasing across active levels, intermediate levels $L_2$ (46.40%) and $L_3$ (51.71%) sit close to the stream's 50.20% base rate, and the extreme densities (0.00% in $L_0/L_1$ and 100.00% in $L_4$) reflect the block construction of the stratified stream.

4.2.3 Topology Confound Permutation Analysis (Experiment E6)
Table 6b audits posture allocation robustness across 1,000 permutations randomizing ingress node mapping $n(b)$ and shuffling batch arrival order. On the observed Table 6 stream, counts are: $L_0 = 7,700$, $L_1 = 10,300$, $L_2 = 5,500$, $L_3 = 18,500$, $L_4 = 18,000$, and $L_5 = 0$.

Under 1,000 random permutations, the permutation mean monotonicity rate is 0.945 (observed is 1.000, $p = 1.000$). The empirical $p$-value of 1.000 indicates that monotonic ordering across active levels is an expected descriptive property of how the synthetic stream was assembled rather than statistically significant evidence of dynamic adaptation. Furthermore, Level $L_5$ remains dormant (0 flows) on the Table 6 stream because normal draws of $R$ across flows never exceeded 0.75; under graph round-robin $n(b) = b \pmod{120}$, only 4 batches met $S \ge 3 \land \bar{T} \le 20.0$ and coincided with hub nodes 0 or 4.

4.3 Cost-Aware Policy Optimization, Baseline Benchmarking, and Action Precision

4.3.1 Action Precision Monotonicity
Table 7 audits action-level precision across candidate decision architectures on the multi-state benchmark stream. In baseline $P_0$, severe action precision inversion occurred (Alert precision 100.00% > Quarantine precision 70.50% in [1]). In contrast, our monotonic policies guarantee non-decreasing precision by construction: Allow 0.00% $\le$ Alert 0.00% $\le$ Restrict 46.40% $\le$ Quarantine 51.71% $\le$ Block 100.00% under $P_{2\text{-tier}}$ (Algorithm 1). Figure 6 visualizes this strictly non-decreasing precision profile.

4.3.2 Master Policy Comparison Across 70 Monotonic Mappings and 50 Evaluation Streams
Table 8 compares candidate level-to-action policies across the search space $\Pi_{70}$ (Algorithm 3):
- Candidate Policy $P_{\text{opt}}$ (`Allow-Allow-Allow-Allow-Block-Block`, mapping $(0,0,0,0,4,4)$): Achieves Rank 1 among all 70 policies across 50 simulation runs (+2,052,438.1 OCU 50-run overall mean; +1,470,740.0 OCU balanced mean; +900,000 OCU on Table 6 stream). By assigning $L_0$–$L_3$ to Allow, $P_{\text{opt}}$ incurs 0.00% Block FPR and 0.00% Quarantine FPR on benign flows.
- Reference Mapping $(0,0,2,2,4,4)$ (`Allow-Allow-Restrict-Restrict-Block-Block`): Achieves Rank 8 (+2,033,585.0 OCU 50-run mean; +1,443,659.6 balanced mean; +1,439,948 OCU on test split seed 99; +985,534 OCU on Table 6 stream).
- Canonical Policy $P_{2\text{-tier}}$ (`Allow-Alert-Restrict-Quarantine-Block-Block`, mapping $(0,1,2,3,4,4)$): Achieves Rank 15 (+2,009,492.8 OCU 50-run mean; +1,410,822.0 balanced mean; +1,404,974 OCU on test split; +963,686 OCU on Table 6 stream, capturing ~64% of achievable 1,505,900 OCU attack reward). It incurs 0.00% Block FPR and 29.90% Quarantine FPR on balanced streams.
- Conservative Baseline $P_1$ (`Allow-Alert-Restrict-Quarantine-Quarantine-Block`, mapping $(0,1,2,3,3,4)$): Ranks 50th of 70 (+778,666.2 OCU 50-run mean; +529,292.5 balanced mean; +786,643 OCU on test split; +423,686 OCU on Table 6 stream).

Table 8b compares architectural baselines ($P_{\text{XGB}}$, $P_{\text{hybrid}}$, $P_1$, $P_{2\text{-tier}}$, $P_{\text{opt}}$). Table 8c documents the exhaustive enumeration of all 70 policies. Table 8e provides cross-regime breakdowns across all 50 evaluation runs. Figure 7 illustrates net benefit comparisons across candidate policies. Figure 8 details the economic value of Level $L_4$ Block escalation.

4.3.3 Per-Family Enforcement Action Breakdown
Table 9 details the distribution of enforcement actions across the eight CICIoT2023 threat families under policy $P_{2\text{-tier}}$ on the multi-state benchmark stream (30,118 attack flows). Benign traffic incurs 0.00% Block (with 29.90% Quarantine disruption). Attack families incur 0.00% Allow and Alert, concentrating in Block (54.0% to 75.0%) and Quarantine (25.0% to 40.0%). Web attacks comprise 16 flows in this multi-state stream (compared to 15 filtered flows in LOFO).

We frame the finding that 25% to 46% of attack flows receive intermediate actions (Restrict or Quarantine) rather than Block as an operational trade-off: these tiers enforce rate limiting and sandbox redirection, which mitigates malicious impact while avoiding premature blocking under uncertainty. Figure 9 presents the per-family action heatmap.

4.3.4 Cost Sensitivity Analysis Across Penalty Ratios and 2D Grids
To evaluate whether the advantage of policy $P_{2\text{-tier}}$ is sensitive to loss matrix parameterization, Table 10 reports sensitivity analysis across false-blocking scaling factors $\lambda \in [0.2, 5.0]$, varying the benign Block penalty from 10 OCU to 250 OCU. Across this range, $P_{2\text{-tier}}$ maintains a 2.24x to 2.46x benefit advantage over conservative baseline $P_1$. We note that $P_1$ (Rank 50) represents a weak comparator, and that the false-blocking sweep touches only the 1,440 benign flows present in the attack-heavy stream. Figure 10 visualizes these sensitivity trajectories.

4.3.5 Decision Architecture Baselines: Pure Classifier ($P_{\text{XGB}}$) vs. Hybrid Posture ($P_{\text{hybrid}}$)
Evaluating decision architectures exposes distinct operational trade-offs:
1. Balanced Traffic: Pure confidence-gated XGBoost ($P_{\text{XGB}}$) achieves $+1,472,830 \pm 4,194$ OCU across 10 seeds (+2,053,543 OCU 50-run mean), matching or outperforming static posture policies ($P_{\text{opt}}$: +1,470,740 OCU; $P_{2\text{-tier}}$: +1,410,822 OCU; $P_{\text{hybrid}}$: +1,391,654 OCU). XGBoost's closed-world superiority arises from high confidence on known attack signatures.
2. Volumetric Flood Traffic: Under pure volumetric flood saturation, $P_{\text{hybrid}}$ yields $+2,974,176 \pm 1,291$ OCU vs. $+2,960,105 \pm 0$ OCU for $P_{\text{XGB}}$, a modest advantage of +0.47% (+14,071 OCU). Because flood streams contain zero benign flows, this gain cannot derive from the benign veto; rather, it arises from batch-level Block enforcement. While a Wilcoxon signed-rank test yields $p = 0.002$, experimental seeds are resamples from a single finite dataset, so this $p$-value overstates true statistical independence. Hybrid attack-heavy Block FPR was not separately measured.

4.3.6 Leave-One-Family-Out (LOFO) Novel Attack Evaluation: Coverage Analysis (Experiment E6)
Table 8d compiles performance across all 7 top-level attack families under LOFO cross-validation. Evaluation streams were generated using 50/50 resampled traffic with replacement (40k flows for DDoS, DoS, Mirai; 17.6k for Recon; 24.8k for Spoofing; 1.2k for Web; 600 for BruteForce).

Multi-stage posture policies achieve higher recall than pure $P_{\text{XGB}}$ on four of five adequately sized held-out families ($n \ge 235$): DDoS (74.06% vs 67.33%), Mirai (27.42% vs 0.33%), Recon (23.91% vs 13.41%), and Spoofing (4.19% vs 1.69%). On DoS, pure XGBoost achieves slightly higher recall (83.74% vs 83.59%, +673,900 vs +672,783 OCU). Mirai recall of 27.42% under posture represents a meaningful improvement over XGBoost (0.33%), but leaves ~72.58% of botnet flows unmitigated. We note that DDoS, DoS, and Mirai share volumetric features (sibling classes), aiding cross-detection. Test folds for Web ($n=15$) and BruteForce ($n=5$) have sample sizes too small to be statistically interpretable. Across all seven folds, $P_{\text{opt}}$ and $P_{\text{hybrid}}$ achieve higher net OCU on 6 of 7 folds, while $P_{2\text{-tier}}$ wins on 5 of 7 folds.

4.3.7 Empirical Refutation of Defense-in-Depth Against Regime Shift (Experiment E6)
On unstratified streams where 60,000 flows arrive in random uniform order, batch attack proportions fluctuate around the 50.20% global mean. Under this unstratified regime, 74.33% of batches concentrate in Level $L_3$. Consequently, static policy $P_{2\text{-tier}}$ suffers a surge in Quarantine FPR to 74.60% (+180,261 OCU), while $P_{\text{hybrid}}$ limits Quarantine FPR to 20.29% (+1,072,488 OCU). This refutes the assumption that static multi-stage pipelines are inherently robust to arbitrary arrival dynamics without adaptive gating.

4.3.8 Runtime Latency and Throughput Micro-Benchmarks (Experiment E9)
Component benchmarking on local workstation GPU infrastructure (NVIDIA GeForce RTX 3050 Laptop GPU / CUDA) evaluates computational feasibility. Standalone single-flow GPU kernel invocation consumes $p_{50} = 13.8$ ms and $p_{99} = 21.6$ ms; the 2.5 ms estimate in preliminary notes represented a warm model invocation without buffer delays. Under batched micro-windows ($B \ge 256$), the end-to-end pipeline processes 18,244 flows/sec ($54.81 \ \mu\text{s}$ per flow amortized), with the benign veto evaluating in $0.177 \ \mu\text{s}$ per flow. On low-bandwidth peripheral IoT links processing 100 flows/sec, non-overlapping batches of $W = 100$ flows require 1.0 full second of buffer accumulation time before posture evaluation.
"""
'''

with open('draft/sections/sec4_results.py', 'w', encoding='utf-8') as f:
    f.write(sec4_content)

print("Successfully updated draft/sections/sec4_results.py")
