sec3_content = r'''# Section 3: Methodology
SEC3_TEXT = r"""3. METHODOLOGY

3.1 Threat Model, Deployment Assumptions, and Benchmark Partitions
To establish an operational foundation, we define the threat model and network boundary governing this study:
1. Adversary Capabilities: We consider an active network adversary capable of injecting malicious flows, modulating transmission rates, and orchestrating distributed attacks, including high-rate volumetric denial-of-service (DDoS/DoS) floods, automated botnet recruitment (e.g., Mirai), lateral reconnaissance, web exploitation, and brute-force authentication attempts.
2. Threat Model Boundaries: The adversary cannot modify SDN controller firmware, compromise the internal state of the feature extraction pipeline, or forge ground-truth labels during runtime inference.
3. System Operational Context and Assumed Deployment: We evaluate the security gateway and SDN controller within an assumed inline edge deployment model, where batched flow inspection maps to OpenFlow or P4 flow-table drop enforcement. The empirical evaluations reported herein derive from offline replay rather than live hardware packet processing. Component profiling on workstation GPU infrastructure (Experiment E9) shows that single-flow GPU kernel invocation consumes 13.8 ms (p50) and 21.6 ms (p99), whereas batched micro-windows ($B \ge 256$) process flows in 16.78 $\mu\text{s}$ to 54.81 $\mu\text{s}$ per flow amortized (>18,000 flows/sec). On low-bandwidth peripheral IoT links processing 100 flows/sec, accumulating non-overlapping batches of $W = 100$ flows incurs a 1.0-second buffering latency before posture evaluation.
4. Dataset Partition Protocol: We evaluate our framework on verified partitions of the CICIoT2023 benchmark [11], adhering to a strict three-way data split:
- (a) Training Partition ($D_{\text{train}}$): The official 80% partition containing 5,491,971 flows (129,538 clean benign flows [2.36%] and 5,362,433 attack flows [97.64%]). Used exclusively to train the upstream XGBoost classifier and the repaired benign Isolation Forest.
- (b) Calibration Partition ($D_{\text{calib}}$): An independent 20,000-flow clean benign slice carved from $D_{\text{train}}$, completely disjoint from validation and test sets, used exclusively to fit anomaly score quantile boundaries ($q_{0.05}, q_{0.95}$) without evaluation leakage.
- (c) Validation Split ($D_{\text{val}}$): Independent 60,000-flow split (seed 42) evaluating all 70 monotonic response policies under the loss matrix.
- (d) Held-Out Test Split ($D_{\text{test}}$): Independent 60,000-flow split (seed 99) verifying that policy rankings generalize out-of-sample without overfitting.

Table 2c details the formal composition and operational characteristics of each regime.

5. Operational Batch Abstraction and Graph Topology Mapping: Our primary analysis unit is defined as contiguous, non-overlapping monitoring batches of $W = 100$ consecutive network flows. Topological routing risk for TARP is simulated over a synthetic 120-node scale-free network topology constructed via Barabási-Albert preferential attachment ($m=2$), with topological risk $R \in [0.10, 0.90]$ derived from personalized PageRank centrality ($\alpha=0.85$), calibrated to empirical mean $\mu_R = 0.4189$ and $\sigma_R = 0.0721$ derived from target distribution $\mathcal{N}(0.42, 0.08)$ [9], [10]. Batches $b \in \{0, \dots, 599\}$ map to network nodes via round-robin allocation $n(b) = b \pmod{120}$, where all flows in batch $b$ share the ingress node risk $R = R[b \pmod{120}]$. The critical-hub threshold centrality deviation is $Z_{\text{thresh}} = (0.75 - 0.4189)/0.0721 = 4.5931\sigma$, with individual hub nodes exhibiting deviations of $Z_0 = 6.6727\sigma$ (Node 0, $R=0.9000$) and $Z_4 = 5.4092\sigma$ (Node 4, $R=0.8089$). These Z-scores represent descriptive properties of the synthetic generator distribution rather than empirical statistical proof of network defense efficacy.

3.2 Upstream Analytical Telemetry and Diagnostic Defect Repair

3.2.1 Supervised Threat Classification (XGBoost)
The supervised classification tier uses a 34-class Gradient Boosted Decision Tree (XGBoost) model [7] trained on $D_{\text{train}}$ across the full 46-feature representation from [1]. The model yields predictions $\hat{y}_t \in \mathcal{Y}$ and associated confidence scores $c_t = \max_k P(y=k \mid \mathbf{x}_t) \in [0, 1]$. While nominal multi-class accuracy reaches 98.99%, balanced accuracy across the 34 classes is 70.98%, reflecting severe recall deficits on extreme minority attack vectors.

3.2.2 Isolation Forest Contamination Diagnosis and Clean Retraining
The Isolation Forest algorithm [8] isolates anomalies by constructing ensembles of random partitioning trees ($iTrees$). The anomaly score $s(\mathbf{x}, n)$ for an observation $\mathbf{x}$ across a dataset of $n$ instances is given by:

$$s(\mathbf{x}, n) = 2^{-\frac{\mathbb{E}[h(\mathbf{x})]}{c(n)}}$$

where $h(\mathbf{x})$ denotes path length, $\mathbb{E}[h(\mathbf{x})]$ is average path length across all trees, and $c(n)$ is average path length of unsuccessful searches in a Binary Search Tree:

$$c(n) = 2 H(n - 1) - \frac{2(n - 1)}{n} = 2\left(\ln(n - 1) + \gamma\right) - \frac{2(n - 1)}{n} = 2\ln(n - 1) + 1.1544313298 - \frac{2(n - 1)}{n}$$

where $H(i)$ is the harmonic number, approximated by $\ln(i) + \gamma$, and $\gamma \approx 0.5772156649$ is Euler's constant ($2\gamma \approx 1.1544313298$).

In our base paper pipeline [1], an unvalidated string literal mismatch occurred: the training script filtered benign samples using `'BENIGN'` (inherited from CICIDS2017), whereas CICIoT2023 designates nominal traffic as `'BenignTraffic'`:

```python
# Contamination Defect in LOFO Training Routine
is_benign = (y_train == 'BENIGN')  # Evaluated to False for all rows
if np.sum(is_benign) == 0:
    X_train_if = X_train_scaled    # Silently trained on 97.64% attack traffic!
isolation_forest.fit(X_train_if)

# Corrected Training Routine
is_benign_corrected = (y_train == 'BenignTraffic')
X_train_clean = X_train_scaled[is_benign_corrected]  # 100% clean benign telemetry
isolation_forest_corrected.fit(X_train_clean)
```

Because the filter fell back silently, the model was fitted on 5,491,971 uncurated flows (5,362,433 attack flows [97.64%] and 129,538 benign flows [2.36%]). This contamination inverted the tree topology: common attack flows required deep path traversals yielding low anomaly scores, while rare benign flows were isolated rapidly near roots, producing inverted anomaly scores (raw AUC 0.0084, rounding to 0.008; Kolmogorov-Smirnov $D = 0.9504$).

To repair this defect, we retrained the Isolation Forest ($M=200$ trees, `max_samples=256`, `contamination=0.05`, `random_state=42`) exclusively on the $N_{\text{benign}} = 129,538$ verified clean benign flows extracted from $D_{\text{train}}$. For any input feature vector $\mathbf{x} \in \mathbb{R}^{46}$, scikit-learn's `score_samples(x)` returns negative values where higher corresponds to more normal instances. We negate this score ($s(\mathbf{x}) = -\text{score\_samples}(\mathbf{x})$) so that higher values indicate extreme anomalies, and calibrate onto a standardized $[0, 1]$ interval.

3.2.3 Anomaly Score Quantile Calibration on Decoupled Split
Raw anomaly scores $s(\mathbf{x}) \in [0, 1]$ produced by the Isolation Forest are uncalibrated and non-linearly distributed. To establish standard probabilistic semantics for downstream trust scoring and posture indicators, we apply a two-point linear piecewise quantile calibration fitted strictly on independent clean benign calibration flows from $D_{\text{calib}}$ ($N=20,000$):
$$\tilde{s}_{\text{calib}}(\mathbf{x}) = \text{clip}\left(0.10 + 0.80 \cdot \frac{s(\mathbf{x}) - q_{0.05}}{q_{0.95} - q_{0.05}}, \; 0.0, \; 1.0\right)$$
where $q_{0.05} = 0.4404$ and $q_{0.95} = 0.5586$ denote empirical 5th and 95th percentiles of raw anomaly scores on clean benign traffic. Fitting quantiles on the decoupled partition $D_{\text{calib}}$ eliminates calibration-to-validation leakage while preserving complete policy ranking invariance across all 70 monotonic policies.

3.2.4 Neutral Dynamic Trust Recalibration (ADTM)
Driven by this clean anomaly signal, we formulated a neutral dynamic trust model (ADTM) removing the two audited inference-time label-leakage pathways. In earlier baseline formulations, trust scores were initialized using empirical attack family priors ($T_0 \in \{10, 20, 26, \dots\}$), injecting label knowledge into evaluation. In our clean formulation, all communicating streams initialize at universal neutral baseline prior: $T_0 = 100.0$.

The instantaneous observed trust $T_{\text{obs}}(t)$ synthesizes four dynamic behavioral components:
1. Supervised Threat Penalty ($S_{\text{class}}$): $S_{\text{class}}(t) = 100.0 \times (1.0 - c_t \cdot \mathbb{I}(\hat{y}_t \ne \text{benign}))$.
2. Anomaly Deflection ($S_{\text{anom}}$): $S_{\text{anom}}(t) = 100.0 \times (1.0 - \tilde{s}_t)$.
3. Topological Exposure ($S_{\text{topo}}$): $S_{\text{topo}}(t) = 100.0 \times (1.0 - R_t)$.
4. Baseline Device Prior ($S_{\text{dev}}$): $S_{\text{dev}} = 100.0$.

Dynamic observed trust is synthesized as:
$$T_{\text{obs}}(t) = \text{clip}\left(0.40 S_{\text{class}}(t) + 0.35 S_{\text{anom}}(t) + 0.15 S_{\text{topo}}(t) + 0.10 S_{\text{dev}}, \; 0.0, \; 100.0\right)$$

When the composite condition $c_t \ge 0.90 \land \hat{y}_t \ne \text{benign} \land \tilde{s}_t \ge 0.50$ is satisfied, trust overrides EWMA smoothing directly:
$$T(t) \leftarrow 10.0$$
This reset forces trust into the Critical band ($[0, 20]$), acting as an operational floor ($T = 10.0$) during sustained attacks. Otherwise, trust updates via adaptive EWMA smoothing:
$$T(t) = \text{clip}\left(0.30 T_{\text{obs}}(t) + 0.70 T(t-1), \; 0.0, \; 100.0\right)$$
with universal smoothing parameter $k = 0.30$. Following a 100-flow attack burst ($T = 10.0$), trust recovers above $\tau_T = 60.0$ in exactly 4 flows. Algorithm 2 formalizes clean training and trust recalibration.

<<<ALGORITHM_2>>>

3.2.5 Topology-Aware Risk Propagation (TARP)
Topological centrality is simulated via personalized PageRank on the synthetic Barabási-Albert graph ($m=2$):
$$\mathbf{p} = (1 - d)\,\mathbf{v} + d\,\mathbf{P}^{\top}\mathbf{p}$$
where $\mathbf{P}$ is the transition matrix, $\mathbf{v}$ the teleportation vector, and $d=0.85$. Batch topological risk $\bar{R}$ assigns the ingress node centrality to all flows within batch $b$.

3.3 The Six-Level Security Posture Escalation Model
The posture engine aggregates multi-stage telemetry over contiguous, non-overlapping monitoring batches of $W = 100$ flows. Because CICIoT2023 omits physical IP/MAC addresses, the ADTM operates as a running stream-level scalar accumulator over non-overlapping batches of $W = 100$ flows rather than maintaining a per-device host table.

3.3.1 Multi-Stage Evidence Synthesis
Within each observation batch $W$, multi-modal telemetry generated by upstream analytical components—supervised classification [7], unsupervised anomaly scoring [8], behavioral trust tracking, and graph topological risk [9], [10]—is synthesized into an integer cumulative evidence score $S \in \{0, 1, 2, 3, 4\}$:

$$S = c_{\text{topo}} + c_{\text{trust}} + c_{\text{anom}} + c_{\text{conf}}$$

where each constituent indicator $c_k \in \{0, 1\}$ evaluates an independent analytical dimension against unified operational thresholds fixed on validation data:

1. Topological Risk Indicator ($c_{\text{topo}}$): Evaluates structural dependency within the 120-node network topology graph:
$$c_{\text{topo}} = \mathbb{I}\left( \frac{1}{W}\sum_{t=1}^{W}\mathbb{I}(R_t \ge 0.42) \ge 0.50 \right)$$
Because all $W=100$ flows within monitoring batch $b$ map to the same network node $n(b) = b \pmod{120}$, they share identical topological routing risk $R_t = R(b)$. Thus, the condition evaluates deterministically to $\mathbb{I}(R(b) \ge 0.42)$, which is either 0 or 1 for the entire batch.

2. Dynamic Trust Deficit Indicator ($c_{\text{trust}}$): Evaluates behavioral degradation and compliance failure over time:
$$c_{\text{trust}} = \mathbb{I}\left( \frac{1}{W}\sum_{t=1}^{W}\mathbb{I}(T_t \le 60.0) \ge 0.50 \right)$$
This condition flags traffic batches where the majority ($\ge 50\%$) of flows transition into the Low, Very Low, or Critical operational trust bands ($T \le 60.0$).

3. Anomaly Extremity Indicator ($c_{\text{anom}}$): Evaluates statistical divergence from nominal benign behavior:
$$c_{\text{anom}} = \mathbb{I}\left( \frac{1}{W}\sum_{t=1}^{W}\mathbb{I}(\tilde{s}_t \ge 0.50) \ge 0.50 \right)$$
requiring $\ge 50\%$ of batch flows to exceed calibrated anomaly threshold $\tilde{s}_t \ge 0.50$.

4. Classifier Confidence Indicator ($c_{\text{conf}}$): Evaluates explicit threat identification by the 34-class supervised XGBoost model [7]:
$$c_{\text{conf}} = \mathbb{I}\left( \frac{1}{W}\sum_{t=1}^{W}\mathbb{I}(\hat{y}_t \neq \text{benign} \land c_t \ge 0.90) \ge 0.50 \right)$$
where $\hat{y}_t \neq \text{benign}$ denotes an attack prediction and $c_t \ge 0.90$ represents high prediction confidence.

3.3.2 Six-Level Posture Assignment Logic
The synthesized evidence score $S$, combined with continuous trust $\bar{T}$ and topological centrality $\bar{R}$, maps the monitoring batch into six formal escalation levels:
- Level $L_0$ (Normal Monitoring): $S = 0 \land \bar{T} \ge 60.0 \land \bar{R} < 0.75$. Permitted default action: Allow (unit cost: 0).
- Level $L_1$ (Topology-Prior Monitoring): $S = 1 \lor (S = 0 \land \bar{T} < 60.0) \land \bar{R} < 0.75$. Permitted default action: Alert under $P_{2\text{-tier}}$, or Allow under $P_{\text{opt}}$.
- Level $L_2$ (Contextual Evaluation): $S = 2 \land \bar{R} < 0.75$. Two independent components corroborate suspicious behavior. Permitted default action: Restrict under $P_{2\text{-tier}}$ and $P_{\text{opt}}$.
- Level $L_3$ (Active Containment): $S \ge 3 \land \bar{T} > 20.0 \land \bar{R} < 0.75$. Multi-source evidence confirms active malicious activity. Permitted default action: Quarantine under $P_{2\text{-tier}}$, or Restrict under $P_{\text{opt}}$.
- Level $L_4$ (Severe Containment - Peripheral / Off-Hub): $S \ge 3 \land \bar{T} \le 20.0 \land \bar{R} < 0.75$. Severe threat confirmed on peripheral endpoints. Permitted action: Block under policy $P_{2\text{-tier}}$ and $P_{\text{opt}}$, or Quarantine under conservative policy $P_1$.
- Level $L_5$ (Critical Topological Hub Containment): Requires BOTH $(S \ge 3 \land \bar{T} \le 20.0)$ AND critical hub topology ($\bar{R} \ge 0.75$). Maximum containment state targeting core routing assets. Permitted action: Block unconditionally.

Table 2b formalizes this six-level assignment logic across evidence score $S$, batch mean trust $\bar{T}$, and topological risk $\bar{R}$.

Architectural Note on Level $L_1$ Redefinition: In our base paper [1], Level $L_1$ was defined as an anomaly screen operating on contaminated signals. We decouple anomaly extremity (isolated to $c_{\text{anom}}$) and redefine Level $L_1$ strictly as Topology-Prior Monitoring ($S=1$ driven by $c_{\text{topo}}=1$, or $S=0 \land \bar{T} < 60.0$). Under peripheral edge routing, $L_1$ captures structural asset criticality ($c_{\text{topo}}=1$) during nominal periods with 0.00% attack density, ensuring high-value assets receive passive logging (Alert under $P_{2\text{-tier}}$, Allow under $P_{\text{opt}}$) without disruptive throttling.

Architectural Role and Activation Boundary of Level $L_5$: Level $L_5$ (Critical Hub Containment) serves as an operational boundary condition for core network infrastructure. Escalation to $L_5$ requires BOTH multi-stage threat corroboration ($S \ge 3 \land \bar{T} \le 20.0$) AND critical topological centrality ($\bar{R} \ge 0.75$). In peripheral edge gateways—where PageRank centrality averages $\bar{R} \approx 0.42 < 0.75$—Level $L_5$ is dormant by design, populating 0 batches and bounding edge escalation to levels $L_0$ through $L_4$.

3.3.3 Operational Hysteresis and Cooldown Mechanics
Escalation from level $L_j$ to a higher level $L_k$ ($k > j$) occurs immediately upon evaluation of batch $W$. In contrast, de-escalation from level $L_k$ to $L_{k-1}$ requires two joint criteria:
1. Cooldown Elapsed Window: $t - t_{\text{last\_escalation}} \ge W_{\text{cooldown}}$, where $W_{\text{cooldown}} = 3W = 300$ consecutive flows without new evidence triggers.
2. Trust Recovery Bound: $\bar{T} \ge 80.0$ for return to Level $L_0$, and $\bar{T} \ge 60.0$ for return to Level $L_1$.
If either condition fails, the system latches at the higher containment tier $L_k$. We note that hysteresis represents an architectural cooldown specification; in the static policy evaluations reported in Section 4, posture assignments are computed batch-by-batch without temporal latching, and no empirical hysteresis experiment was performed. Algorithm 1 formalizes cumulative evidence posture assignment and hysteresis latching. Figure 1 illustrates the multi-stage architecture and component interaction flow.

<<<ALGORITHM_1>>>

3.4 Cost-Aware Policy Optimization, Baseline Benchmarking, and Combinatorial Search

3.4.1 Operational Cost Matrix Formulation (Table 2)
Intrusion response selection in cyber-physical IoT networks is intrinsically asymmetric. We formalize policy assignment through a decision-theoretic cost matrix $\mathcal{L}(a, y)$ mapping response actions $a \in \mathcal{A} = \{\text{Allow}, \text{Alert}, \text{Restrict}, \text{Quarantine}, \text{Block}\}$ and ground-truth traffic states $y \in \{\text{Benign}, \text{Attack}\}$ to Operational Cost Units (OCU).

Table 2 defines the formal cost matrix $\mathcal{L}(a, y)$ across all 10 action-state pairs:
- Allow: Unit cost $c_b(\text{Allow}) = 0$ on benign; attack cost $c_a(\text{Allow}) = 0$ (unmitigated attack, net benefit $r_a = 0$).
- Alert: Unit cost $c_b(\text{Alert}) = +1$ on benign (analyst triage overhead); attack cost $c_a(\text{Alert}) = -5$ (early threat awareness, net benefit $r_a = +5$).
- Restrict: Unit cost $c_b(\text{Restrict}) = +3$ on benign (minor QoS degradation); attack cost $c_a(\text{Restrict}) = -10$ (partial rate throttling, net benefit $r_a = +10$).
- Quarantine: Unit cost $c_b(\text{Quarantine}) = +15$ on benign (service diversion); attack cost $c_a(\text{Quarantine}) = -20$ (host isolation, net benefit $r_a = +20$).
- Block: Unit cost $c_b(\text{Block}) = +50$ on benign (severe false outage penalty); attack cost $c_a(\text{Block}) = -50$ (hardware drop, net benefit $r_a = +50$).

OCU Derivation Formula:
For an evaluation stream of $N$ flows $\{(\mathbf{x}_t, y_t)\}_{t=1}^N$ under policy $\pi$:
$$\text{OCU}(\pi) = \sum_{t=1}^N \left[ y_t \cdot r_a(\pi(\mathbf{x}_t)) - (1 - y_t) \cdot c_b(\pi(\mathbf{x}_t)) \right]$$
where $r_a(a) = -\mathcal{L}(a, 1) \in \{0, 5, 10, 20, 50\}$ represents attack containment reward, and $c_b(a) = \mathcal{L}(a, 0) \in \{0, 1, 3, 15, 50\}$ represents the false-positive disruption penalty.

3.4.2 Architectural Decision Baselines
We evaluate two baseline decision paradigms alongside static posture mappings:
1. Pure Per-Flow Classifier Baseline ($P_{\text{XGB}}$): Operates without temporal batching or posture escalation. In confidence-gated formulation ($P_{\text{XGB}}$), flows with $\hat{y}_t \neq \text{BenignTraffic} \land c_t \ge 0.90$ map to Block, while other flows map to Allow. In ungated formulation ($P_{\text{XGB, ungated}}$), flows are blocked purely on argmax prediction. Raw ungated classification inflicts a prohibitive 9.46% Block FPR on benign flows (blocking 2,827 legitimate connections), violating availability SLAs. On stationary closed-world balanced traffic, confidence-gated $P_{\text{XGB}}$ achieves +1,472,830 OCU, outperforming static posture policies.
2. Hybrid Posture + Benign Veto Architecture ($P_{\text{hybrid}}$): Combines macroscopic batch posture escalation with microscopic flow-level validation. Batches escalate through levels $L_0$ to $L_5$ according to Algorithm 1. For levels $L_0$ to $L_3$, actions follow canonical policy $P_{2\text{-tier}}$ (Allow, Alert, Restrict, Quarantine). In Level $L_4$ (Block), individual flows are inspected by the supervised classifier: if $\hat{y}_t = \text{BenignTraffic}$ with confidence $c_t \ge 0.90$, the flow receives an individual benign veto down to Allow; otherwise, default batch Block is retained. Under volumetric flood saturation (0 benign flows), the benign veto cannot increase OCU; the +14,071 OCU gain over standalone XGBoost arises from batch-level Block enforcement.

3.4.3 Combinatorial Policy Search Space ($\Pi_{70}$)
A response policy is a mapping $\pi: \mathcal{L}_{\text{levels}} \to \mathcal{A}$ assigning an enforcement action to each level $L_k \in \{L_0, \dots, L_5\}$. Candidate policies must satisfy severity monotonicity:
$$\text{severity}(\pi(L_i)) \le \text{severity}(\pi(L_j)) \quad \forall \; i < j$$
where $\text{severity}(\text{Allow}) = 0 < \text{severity}(\text{Alert}) = 1 < \text{severity}(\text{Restrict}) = 2 < \text{severity}(\text{Quarantine}) = 3 < \text{severity}(\text{Block}) = 4$.

Enforcing boundary rules: $\pi(L_0) = \text{Allow}$ and $\pi(L_5) = \text{Block}$. The search space selects intermediate mappings for interior levels $\{L_1, L_2, L_3, L_4\}$ such that:
$$\text{Allow} \le \pi(L_1) \le \pi(L_2) \le \pi(L_3) \le \pi(L_4) \le \text{Block}$$

Out of the $5^6 = 15,625$ unconstrained assignments, the total number of admissible monotonic mappings is given by combinations with replacement:
$$N_{\text{admissible}} = \binom{5 + 4 - 1}{4} = \binom{8}{4} = \frac{8 \times 7 \times 6 \times 5}{24} = \mathbf{70 \text{ unique admissible policies}}$$
Algorithm 3 formalizes the evaluation search across all 70 monotonic mappings without safety filtering. Policy $P_{\text{opt}}$ (`Allow-Allow-Allow-Allow-Block-Block`, mapping $(0,0,0,0,4,4)$) achieves Rank 1 among the 70 static monotonic posture policies across 50 simulation runs under the assumed OCU matrix.

<<<ALGORITHM_3>>>

3.4.4 Optimization Objective, Pareto Frontier, and Clarification of Historical OCU Shifts
For each candidate policy $\pi \in \Pi_{70}$, we evaluate total operational cost across flows in both balanced ($D_{\text{bal}}$) and attack-heavy ($D_{\text{atk}}$) streams:
$$\text{Cost}(\pi, D) = \sum_{t=1}^N \mathcal{L}(\pi(L_t), y_t), \quad \text{NetBenefit}(\pi, D) = -\text{Cost}(\pi, D)$$

Global optimization evaluates combined net benefit as the average across both regimes:
$$\text{NetBenefit}_{\text{comb}}(\pi) = 0.5 \cdot \text{NetBenefit}(\pi, D_{\text{bal}}) + 0.5 \cdot \text{NetBenefit}(\pi, D_{\text{atk}})$$

Clarification of Historical OCU Numbers across Evaluation Protocols:
Readers comparing results across tables should distinguish three distinct evaluation protocols:
1. Single-Stream Table 6 Benchmark: Evaluated on the 60,000-flow multi-state stream with 30,118 attack flows (max achievable attack reward = $30,118 \times 50 = 1,505,900$ OCU). On this stream, $P_{\text{opt}}$ yields +985,534 OCU, canonical $P_{2\text{-tier}}$ yields +963,686 OCU (capturing 63.99% $\approx 64\%$ of achievable attack containment), and conservative $P_1$ yields +423,686 OCU.
2. Historical Dual-Regime Average: In preliminary drafts, the headline metric was a 50/50 weighted average combining the single Table 6 stream (+963,686 OCU) and the attack-heavy stream (+2,856,000 OCU), yielding $(963,686 + 2,856,000)/2 = \mathbf{+1,909,843 \ \text{OCU}}$.
3. 50-Run Multi-Regime Replication Protocol: In the full multi-regime evaluation across 10 random seeds per regime (50 runs total, 3,000,000 flows), resampled 50/50 balanced streams yield a balanced regime mean of +1,470,740.0 OCU for $P_{\text{opt}}$ (Rank 1), +1,410,822.0 OCU for $P_{2\text{-tier}}$ (Rank 15), and +529,292.5 OCU for $P_1$ (Rank 50). Across all 50 runs, the unweighted overall mean is +2,052,438.1 OCU for $P_{\text{opt}}$, +2,009,492.8 OCU for $P_{2\text{-tier}}$, and +778,666.2 OCU for $P_1$. Held-out test split $D_{\text{test}}$ (seed 99) yields +1,439,948 OCU for reference mapping $(0,0,2,2,4,4)$ (Rank 8), +1,404,974 OCU for $P_{2\text{-tier}}$, and +786,643 OCU for $P_1$.

3.4.5 Implementation Note: Veto Input Constraints and Absence of Inference Label Arguments
Under $P_{\text{hybrid}}$, batches escalate through levels $L_0$ to $L_5$ according to Algorithm 1. For levels $L_0$ through $L_3$, actions follow canonical policy $P_{2\text{-tier}}$ ($\text{Allow}, \text{Alert}, \text{Restrict}, \text{Quarantine}$). In Level $L_4$ (Block), individual flows $\mathbf{x}_t$ undergo micro-validation:

$$a_t = \begin{cases} \text{Allow}, & \text{if } \hat{y}_t = \text{BenignTraffic} \land c_t \ge 0.90 \\ \text{Block}, & \text{otherwise} \end{cases}$$

where $\hat{y}_t = \arg\max_k f_{\text{XGB}}(\mathbf{x}_t)$ and $c_t = \max_k P(y=k \mid \mathbf{x}_t)$. If the classifier certifies the flow as benign ($c_t \ge 0.90$), the system executes a runtime benign veto, downgrading enforcement from batch Block to Allow.

We verified by manual code inspection and execution trace audits that the veto decision function $V(\mathbf{x}_t)$ accepts strictly input features $\mathbf{x}_t$ and model parameters $\boldsymbol{\theta}_{\text{XGB}}$. Ground-truth label $y_t$ is neither passed as an argument nor referenced in any sub-routine of $V(\mathbf{x}_t)$. We note this constitutes an implementation verification of the function signature rather than an independent third-party cryptographic or leakage audit.

Algorithm 4 formalizes the complete hybrid posture-veto execution pipeline.

<<<ALGORITHM_4>>>

3.5 Evaluation Protocol and Experimental Regimes
To evaluate pipeline robustness under traffic variation, we evaluate across five operational regimes:
1. Balanced Stratified Stream: 50% attack, 50% benign, evaluating baseline multi-state discrimination.
2. Sustained Attack-Heavy Stream: 97.60% attack traffic, representing saturation conditions.
3. Multi-State Benchmark Stream: 60,000 flows structured with alternating operational phases.
4. Unstratified Stream: Random uniform flow shuffling, testing sensitivity to batch composition.
5. Volumetric Flood Saturation: Pure high-rate attack traffic, evaluating maximum containment throughput.
"""
'''

with open('draft/sections/sec3_method.py', 'w', encoding='utf-8') as f:
    f.write(sec3_content)

print("Successfully updated draft/sections/sec3_method.py")
