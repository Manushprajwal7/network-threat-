# Section 3: Methodology
SEC3_TEXT = r"""
3. METHODOLOGY

3.1 Threat Model and Operational Assumptions
To establish a formal security foundation, we define the operational threat model and scope governing our multi-stage framework:

1. Adversary Objectives: We consider an active network adversary seeking to achieve one or more of five objectives: (a) orchestrating high-rate volumetric denial-of-service or distributed denial-of-service (DoS/DDoS) floods to exhaust gateway bandwidth; (b) recruiting vulnerable IoT devices into automated botnets (e.g., Mirai); (c) executing credential brute-force attacks against management services (SSH, Telnet); (d) performing application-layer web exploitation (SQL injection, XSS, command injection); or (e) conducting stealthy reconnaissance sweeps to map internal network vulnerabilities.

2. Adversary Capabilities: The adversary can inject arbitrary network packets, spoof transmission source IP and MAC addresses, modulate flow transmission rates (employing either aggressive volumetric bursts or low-and-slow pulsing to evade time-window aggregators), and compromise peripheral IoT edge sensors.

3. Gateway Trust and Placement Assumptions: We assume that the central security gateway hosting the policy engine and software-defined network (SDN) controller represents a trusted execution environment: its internal state, routing tables, and inspection pipelines cannot be directly tampered with by the adversary. The gateway operates at the edge boundary of the IoT subnet, possessing inline packet forwarding and drop capabilities to enforce tiered actions.

3.2 Dataset Telemetry and Evaluation Protocol
1. Benchmark Dataset and Feature Schema: We evaluate our framework using the CICIoT2023 benchmark [11]. Flow records in CICIoT2023 provide 46 statistical flow features but omit transmission source/destination IP addresses and MAC headers. Consequently, individual flows cannot be mapped to physical hardware endpoints. The 46-dimensional feature vector $\mathbf{x} \in \mathbb{R}^{46}$ is ordered according to the official schema:
- 1–7 (Temporal and Rate Counters): `flow_duration`, `Header_Length`, `Protocol Type`, `Duration`, `Rate`, `Srate`, `Drate`;
- 8–19 (TCP Flag Numbers and Occurrence Counters): `fin_flag_number`, `syn_flag_number`, `rst_flag_number`, `psh_flag_number`, `ack_flag_number`, `ece_flag_number`, `cwr_flag_number`, `ack_count`, `syn_count`, `fin_count`, `urg_count`, `rst_count`;
- 20–33 (Protocol and Application Layer Indicators): `HTTP`, `HTTPS`, `DNS`, `Telnet`, `SMTP`, `SSH`, `IRC`, `TCP`, `UDP`, `DHCP`, `ARP`, `ICMP`, `IPv`, `LLC`;
- 34–46 (Statistical Moments and Dimensional Quantities): `Tot sum`, `Min`, `Max`, `AVG`, `Std`, `Tot size`, `IAT`, `Number`, `Magnitue` (retaining the dataset CSV header spelling for Magnitude to preserve schema fidelity), `Radius`, `Covariance`, `Variance`, `Weight`.

2. Supervised Model Complexity: Supervised XGBoost multi-class inference evaluates $M = 150$ boosting rounds across 34 classes, constructing $34 \times 150 = 5,100$ individual decision trees with maximum depth $d_{\max} = 8$. Each flow requires up to $5,100 \times 8 = 40,800$ scalar split comparisons, scaling with complexity $O(C \cdot M \cdot d_{\max})$.

3. Disjoint Partitioning Protocol: To prevent policy-selection bias and evaluation leakage, we establish a strict three-way data protocol:
- (a) Training Partition ($D_{\text{train}}$): The standard 80% partition of CICIoT2023 containing 5,491,971 flows (129,538 clean benign flows [2.36%] and 5,362,433 attack flows [97.64%]). This partition is used exclusively to train the upstream supervised XGBoost classifier and the clean benign Isolation Forest ($N=20,000$ benign calibration flows). We note that random flow-level splitting is standard for CICIoT2023 due to the omission of host IP headers.
- (b) Validation / Policy Selection Split ($D_{\text{val}}$): An independent split of 60,000 flows used to calibrate operational thresholds and evaluate the combinatorial sweep across all 70 monotonic response policies under the formal loss matrix.
- (c) Held-out Independent Test Split ($D_{\text{test}}$): A separate held-out partition of 60,000 flows drawn with a distinct random seed (seed 99) to verify that the selected policy generalizes out-of-sample without overfitting.

4. Operational Window Abstraction and Graph Topology Mapping: To provide a structured operational abstraction without inventing fictional host identifiers, our analysis unit is defined as contiguous, non-overlapping monitoring windows of $W = 100$ consecutive network flows (stride 100), representing local batch inspection at an edge gateway. Because physical flow-to-node topology headers are absent in CICIoT2023, topological routing risk for TARP is simulated over a synthetic 120-node scale-free network topology constructed via Barabási-Albert preferential attachment ($m=2$), with topological risk $R \in [0.10, 0.90]$ derived from personalized PageRank centrality ($\alpha=0.85$), calibrated to $\mu=0.42, \sigma=0.08$ (documented in Experiment E10 [9], [10]). Batches $b \in \{0, \dots, 599\}$ are mapped to network nodes via round-robin index allocation $n(b) = b \pmod{120}$. Because all flows within batch $b$ share the identical node risk $R = R[b \pmod{120}]$, $R$ is uniform within each batch; the previously reported $Z = 41.25\sigma$ was an arithmetic artifact of dividing individual node standard deviations by $\sqrt{100}$ despite uniform intra-batch node assignment. This separation enables the framework to distinguish peripheral edge device streams ($R < 0.75$) from critical backbone transit infrastructure ($R \ge 0.75$).

3.3 The Six-Level Security Posture Model
To bridge the operational divide between isolated component-level telemetry signals and actionable incident response, we formulate an evidence-driven, six-level security posture escalation model. Rather than evaluating individual flows against disconnected thresholds, the posture engine aggregates multi-stage telemetry over contiguous monitoring windows of $W = 100$ flows. Because the CICIoT2023 dataset omits physical source and destination IP and MAC addresses, the ADTM operates as a running stream-level scalar accumulator over windows of $W = 100$ consecutive flows rather than maintaining a per-device host table. All trust evaluations $T_t$, anomaly density counters, and posture assignments evaluate this sequential stream.

3.3.1 Multi-Stage Evidence Synthesis
Within each observation window $W$, multi-modal telemetry generated by upstream analytical components—supervised classification [7], unsupervised anomaly scoring [8], behavioral trust tracking, and graph topological risk [9], [10]—is synthesized into an integer cumulative evidence score $S \in \{0, 1, 2, 3, 4\}$:

$$S = c_{\text{topo}} + c_{\text{trust}} + c_{\text{anom}} + c_{\text{conf}}$$

where each constituent indicator $c_k \in \{0, 1\}$ evaluates an independent analytical dimension against unified operational thresholds fixed on a validation split:

1. Topological Risk Indicator ($c_{\text{topo}}$): Evaluates structural dependency within the 120-node network topology graph, measuring the proportion of window flows exceeding base network risk:
$$c_{\text{topo}} = \mathbb{I}\left(\frac{1}{W} \sum_{t=1}^W \mathbb{I}(R_t \ge 0.42) \ge 0.50\right)$$
where $R \in [0.10, 0.90]$ represents personalized PageRank centrality concentrated on critical routing assets [10], [34]. Component ablation demonstrates that $c_{\text{topo}}$ functions as a static topological centrality prior based on node assignment rather than a dynamic flow anomaly detector: for batches mapped to nodes with $R \ge 0.42$, $c_{\text{topo}} = 1$ unconditionally, whereas $c_{\text{anom}}$, $c_{\text{trust}}$, and $c_{\text{conf}}$ dynamically respond to flow attributes.

2. Dynamic Trust Deficit Indicator ($c_{\text{trust}}$): Evaluates behavioral degradation and compliance failure over time:
$$c_{\text{trust}} = \mathbb{I}\left(\frac{1}{W} \sum_{t=1}^W \mathbb{I}(T_t \le 60.0) \ge 0.50\right)$$
This condition flags traffic windows where the majority of flows transition into the Low, Very Low, or Critical operational trust bands ($T \le 60.0$).

3. Anomaly Extremity Indicator ($c_{\text{anom}}$): Evaluates statistical divergence from nominal benign behavior, measuring the proportion of window flows exhibiting extreme calibrated anomaly scores ($\tilde{s} \ge 0.50$):
$$c_{\text{anom}} = \mathbb{I}\left(\frac{1}{W} \sum_{t=1}^W \mathbb{I}(\tilde{s}_t \ge 0.50) \ge \tau_{\text{anom}}\right)$$
The anomaly density threshold is fixed at unified operating point $\tau_{\text{anom}} = 0.50$ across all evaluation regimes.

4. Classifier Confidence Indicator ($c_{\text{conf}}$): Evaluates explicit threat identification by the 34-class supervised XGBoost model [7]:
$$c_{\text{conf}} = \mathbb{I}\left(\frac{1}{W} \sum_{t=1}^W \mathbb{I}(\hat{y}_t \ne \text{benign} \land c_t \ge 0.90) \ge \tau_{\text{conf}}\right)$$
where $\hat{y}_t \ne \text{benign}$ denotes an attack prediction and $c_t = \max_k P(y=k \mid \mathbf{x}_t)$ represents prediction confidence. We emphasize the structural distinction: $c_t \ge 0.90$ is an individual per-flow confidence threshold, whereas $\tau_{\text{conf}} = 0.50$ is the batch-level proportion threshold (requiring at least 50% of flows in the batch to satisfy high-confidence attack classification).

The synthesized evidence score $S$, combined with the window's mean trust $\bar{T} = \frac{1}{W} \sum_{t=1}^W T_t$ and mean topological risk $\bar{R} = \frac{1}{W} \sum_{t=1}^W R_t$, uniquely determines the operational security posture level $L \in \{L_0, L_1, L_2, L_3, L_4, L_5\}$:
- Level $L_0$ (Normal Monitoring): $S = 0$ and $\bar{T} \ge 60.0$. Traffic exhibits nominal trust, baseline anomaly rates, and zero high-confidence attack detections. Permitted default action: Allow (unit cost: 0).
- Level $L_1$ (Topology-Prior Monitoring): $S = 1$, or $S = 0 \land \bar{T} < 60.0$ (capturing behavioral trust degradation or topological prior exposure even if instantaneous threat indicators have not triggered). Permitted default action: Alert (unit cost: +1 on benign / -5 on attack) under $P_{2\text{-tier}}$, or Allow under $P_{\text{opt}}$.
- Level $L_2$ (Contextual Evaluation): $S = 2$. Two independent components corroborate suspicious behavior. Permitted default action: Restrict (unit cost: +3 on benign / -10 on attack).
- Level $L_3$ (Active Containment): $S \ge 3$ with mean trust $\bar{T} > 20.0$. Multi-source evidence confirms active malicious activity, but trust degradation remains moderate. Permitted default action: Quarantine (unit cost: +15 on benign / -20 on attack).
- Level $L_4$ (Severe Containment - Peripheral / Off-Hub): $S \ge 3$, mean trust $\bar{T} \le 20.0$, and off-hub topology $\bar{R} < 0.75$. Severe threat confirmed on peripheral edge endpoints. Permitted action: Block under policy $P_{2\text{-tier}}$ or Quarantine under conservative policy $P_1$.
- Level $L_5$ (Critical Topological Hub Containment): $S \ge 3$, mean trust $\bar{T} \le 20.0$, and critical hub topology $\bar{R} \ge 0.75$. Maximum containment state targeting core infrastructure routing assets. Permitted action: Block (unit cost: +50 on benign / -50 on attack).

3.2.2 Operational Hysteresis and De-escalation Mechanics
To prevent state flapping and protect flow tables from rapid rule churning, posture transitions enforce formal hysteresis state-transition conditions. Escalation from level $L_j$ to a higher level $L_k$ ($k > j$) occurs immediately upon evaluation of window $W$. In contrast, de-escalation from level $L_k$ to $L_{k-1}$ requires two joint criteria:
1. Cooldown Elapsed Window: $t - t_{\text{last\_escalation}} \ge W_{\text{cooldown}}$, where $W_{\text{cooldown}} = 3W = 300$ consecutive flows without new evidence triggers.
2. Trust Recovery Bound: $\bar{T} \ge 80.0$ for return to Level $L_0$, and $\bar{T} \ge 60.0$ for return to Level $L_1$.
If either condition fails, the system latches at the higher containment tier $L_k$.

We note an operational boundary: while hysteresis algorithmically prevents high-frequency oscillation, it introduces a potential batch density dilution vulnerability. An adversary pulsing attack flows at an average rate below 50% per batch ($\tau_{\text{conf}} < 0.50, \tau_{\text{anom}} < 0.50$) could theoretically evade batch-level escalation to $L_4$, motivating continuous trust decay or hybrid flow-level inspection. Algorithm 1 formalizes the cumulative evidence posture assignment and hysteresis latching. Figure 1 illustrates the multi-stage architecture and component interaction flow.

<<<ALGORITHM_1>>>

3.3 Isolation Forest Contamination Diagnosis and Calibration
The Isolation Forest algorithm [8] isolates anomalies by constructing ensembles of random partitioning trees ($iTrees$). The anomaly score $s(\mathbf{x}, n)$ for an observation $\mathbf{x}$ across a dataset of $n$ instances is given by:

$$s(\mathbf{x}, n) = 2^{-\frac{\mathbb{E}[h(\mathbf{x})]}{c(n)}}$$

where $h(\mathbf{x})$ denotes the path length (number of recursive splits required to isolate $\mathbf{x}$), $\mathbb{E}[h(\mathbf{x})]$ is the average path length across all trees, and $c(n)$ is the average path length of unsuccessful searches in a Binary Search Tree:

$$c(n) = 2 H(n - 1) - \frac{2(n - 1)}{n} = 2\left(\ln(n - 1) + \gamma\right) - \frac{2(n - 1)}{n} = 2\ln(n - 1) + 1.1544313298 - \frac{2(n - 1)}{n}$$

where $H(i)$ is the harmonic number, approximated by $\ln(i) + \gamma$, and $\gamma \approx 0.5772156649$ is Euler's constant ($2\gamma \approx 1.1544313298$). When $h(\mathbf{x}) \to 0$, $s \to 1$, indicating that the observation is isolated rapidly near the root and is statistically anomalous.

In the prior baseline pipeline [1], an unvalidated string literal mismatch occurred: the training script filtered benign samples using `'BENIGN'` (inherited from CICIDS2017), whereas CICIoT2023 designates nominal traffic as `'BenignTraffic'`:

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

Because the conditional check silently fell back to training on the entire uncurated partition, the model was fitted on the full training partition of 5,491,971 flows comprising 5,362,433 attack flows (97.64%) and only 129,538 benign flows (2.36%). This massive contamination inverted the tree topology: common attack flows required deep path traversals, yielding path lengths near $c(n)$ and low anomaly scores, while rare benign flows were isolated rapidly near roots, yielding maximum anomaly scores.

To repair this defect, we retrained the Isolation Forest exclusively on verified clean benign flows extracted from the official CICIoT2023 training partition ($N = 20,000$ calibration instances, selected for memory efficiency and robust representation of the empirical distribution). For any input feature vector $\mathbf{x} \in \mathbb{R}^{46}$, scikit-learn's `IsolationForest.score_samples(x)` returns negative values where higher corresponds to more normal instances. We negate this score ($s(\mathbf{x}) = -\text{score\_samples}(\mathbf{x})$) so that higher values indicate extreme anomalies, and calibrate onto a standardized $[0, 1]$ interval via linear quantile scaling:

$$\tilde{s}(\mathbf{x}) = \text{clip}\left( \frac{s(\mathbf{x}) - s_{p5}}{s_{p95} - s_{p5}} \times 0.80 + 0.10, \; 0.0, \; 1.0 \right)$$

where $s_{p5} = 0.4421$ and $s_{p95} = 0.5284$ denote the empirical 5th and 95th percentiles fitted strictly on the clean benign training partition. Under this quantile calibration, nominal benign training traffic maps to the standardized interval $[0.10, 0.90]$, and by calibration design exactly 5.0% of nominal benign calibration flows exceed 0.90, while malicious traffic scales toward 1.00. Experiment E12 verifies this sign convention with an automated unit test, confirming positive Pearson correlation with attack ground truth ($r = +0.7794, p < 10^{-15}$) and ROC AUC of 0.9505.

3.3.1 Neutral Dynamic Trust Recalibration
Driven by this clean anomaly signal, we formulated a neutral dynamic trust model (ADTM) that eliminates ground-truth label leakage. In earlier baseline formulations, trust scores were initialized using empirical attack family priors ($T_0 \in \{10, 20, 26, \dots\}$), injecting label knowledge into the evaluation. In our clean formulation, all communicating streams initialize at a universal neutral baseline prior: $T_0 = 100.0$.

The instantaneous observed trust $T_{\text{obs}}(t)$ synthesizes four dynamic behavioral components:
1. Supervised Threat Penalty ($S_{\text{class}}$): $S_{\text{class}}(t) = 100.0 \times (1.0 - c_t \cdot \mathbb{I}(\hat{y}_t \ne \text{benign}))$.
2. Anomaly Deflection ($S_{\text{anom}}$): $S_{\text{anom}}(t) = 100.0 \times (1.0 - \tilde{s}_t)$.
3. Topological Exposure ($S_{\text{topo}}$): $S_{\text{topo}}(t) = 100.0 \times (1.0 - R_t)$.
4. Baseline Device Prior ($S_{\text{dev}}$): $S_{\text{dev}} = 100.0$.

Dynamic observed trust is synthesized as:
$$T_{\text{obs}}(t) = \text{clip}\left(0.40 S_{\text{class}}(t) + 0.35 S_{\text{anom}}(t) + 0.15 S_{\text{topo}}(t) + 0.10 S_{\text{dev}}, \; 0.0, \; 100.0\right)$$

This weighting heavily reflects supervised classification confidence ($w_{\text{class}} = 0.40$). At marginal operating thresholds ($c_t = 0.90, \tilde{s}_t = 0.50, R_t = 0.42$), $T_{\text{obs}}(t) \approx 40.9$, which remains well above the critical escalation threshold ($\tau_T \le 20.0$). Rather than relying exclusively on continuous EWMA decay, the framework incorporates an explicit joint hard reset: when the composite condition $c_t \ge 0.90 \land \hat{y}_t \ne \text{benign} \land \tilde{s}_t \ge 0.50$ is satisfied, trust overrides EWMA smoothing directly:
$$T(t) \leftarrow 10.0$$
This reset forces trust into the Critical band ($[0, 20]$), acting as an operational floor ($T = 10.0$) during sustained attack campaigns. Otherwise, trust updates via standard adaptive EWMA smoothing:
$$T(t) = \text{clip}\left(0.30 T_{\text{obs}}(t) + 0.70 T(t-1), \; 0.0, \; 100.0\right)$$
with a single universal smoothing parameter $k = 0.30$ across all traffic streams. Because trust operates as a continuous EWMA accumulator across the stream, an abrupt transition from attack bursts to benign traffic requires a short recovery horizon: empirical evaluation (Experiment E7 / Task 7) demonstrates that following a 100-flow attack burst ($T = 10.0$), trust recovers above $\tau_T = 60.0$ in exactly 4 flows, temporarily depressing 3 benign flows below 60.0 and 0 flows below 20.0. Algorithm 2 formalizes the clean training and trust recalibration pipeline.

<<<ALGORITHM_2>>>

3.4 Cost-Aware Policy Optimization, Baseline Benchmarking, and Combinatorial Search
Intrusion response selection in cyber-physical IoT networks is intrinsically asymmetric: permitting an attack to execute inflicts infrastructure compromise, while mistakenly isolating critical benign nodes inflicts operational disruption [35], [36], [37], [38]. We formalize policy assignment through a decision-theoretic cost matrix $\mathcal{L}(a, y)$ mapping response actions $a \in \mathcal{A} = \{\text{Allow}, \text{Alert}, \text{Restrict}, \text{Quarantine}, \text{Block}\}$ and ground-truth traffic states $y \in \{\text{Benign}, \text{Attack}\}$ to Operational Cost Units (OCU).

Table 2 defines the formal cost matrix $\mathcal{L}(a, y)$. Each action carries a calibrated economic profile:
- Allow: Unit cost 0 on benign traffic (nominal operation); unit cost 0 on attack traffic (representing unmitigated baseline exposure $\mathcal{C}(\text{Allow}) = 0$).
- Alert: Generates passive telemetry. Unit cost $+1$ on benign (negligible analyst triage overhead); unit cost $-5$ on attack (early threat awareness benefit).
- Restrict: Dynamic bandwidth throttling and rate-limiting. Unit cost $+3$ on benign (minor QoS degradation); unit cost $-10$ on attack (partial volumetric mitigation).
- Quarantine: VLAN sandboxing and network isolation. Unit cost $+15$ on benign (service interruption for legitimate users); unit cost $-20$ on attack (complete host containment).
- Block: Total packet dropping. Unit cost $+50$ on benign (severe outage penalty); unit cost $-50$ on attack (maximum threat suppression).

3.4.1 Formulation of Missing Baselines: Pure Per-Flow Classifier vs Hybrid Veto
To address the fundamental trade-off between batch-level posture containment and flow-level granularity, we evaluate two missing decision baselines alongside static posture mappings:
1. Pure Per-Flow Classifier Baseline ($P_{\text{XGB}}$): Operates without temporal batching or posture escalation. For each flow $t$, the supervised XGBoost model [7] predicts $\hat{y}_t$ and confidence $c_t$. If $\hat{y}_t = \text{BenignTraffic}$, the action is Allow; if $\hat{y}_t \ne \text{BenignTraffic}$, the action is Block.
2. Hybrid Posture + Benign Veto Architecture ($P_{\text{hybrid}}$): Combines macroscopic batch posture escalation with microscopic flow-level validation. Batches escalate through levels $L_0$ to $L_5$ according to Algorithm 1. For levels $L_0$ to $L_3$, actions follow canonical policy $P_{2\text{-tier}}$ (Allow, Alert, Restrict, Quarantine). In Level $L_4$ (Block), each individual flow within the batch is inspected by the supervised classifier: if $\hat{y}_t = \text{BenignTraffic}$ with confidence $c_t \ge 0.90$, the flow receives an individual benign veto down to Allow; otherwise, the default batch-level Block action is retained.

3.4.2 Combinatorial Policy Search Space
A response policy is defined as a mapping function $\pi: \mathcal{L}_{\text{levels}} \to \mathcal{A}$ assigning an operational enforcement action to each security level $L_k \in \{L_0, \dots, L_5\}$. Every candidate policy must satisfy the strict non-decreasing severity monotonicity constraint:
$$\text{severity}(\pi(L_i)) \le \text{severity}(\pi(L_j)) \quad \forall \; i < j$$
where $\text{severity}(\text{Allow}) = 0 < \text{severity}(\text{Alert}) = 1 < \text{severity}(\text{Restrict}) = 2 < \text{severity}(\text{Quarantine}) = 3 < \text{severity}(\text{Block}) = 4$.

Enforcing standard operational boundary safety rules:
1. Normal Baseline Safety Rule: $\pi(L_0) = \text{Allow}$. Nominal baseline operations must never throttle or alert on fully verified traffic.
2. Terminal Containment Safety Rule: $\pi(L_5) = \text{Block}$. Maximum multi-vector siege states targeting critical infrastructure must execute complete packet dropping.

With $\pi(L_0)$ fixed to Allow and $\pi(L_5)$ fixed to Block, the search space reduces to selecting the intermediate mappings for the four interior security levels $\{L_1, L_2, L_3, L_4\}$ such that:
$$\text{Allow} \le \pi(L_1) \le \pi(L_2) \le \pi(L_3) \le \pi(L_4) \le \text{Block}$$

The total number of admissible monotonic mappings corresponds to combinations with repetition:
$$N_{\text{admissible}} = \binom{4 + 5 - 1}{5 - 1} = \binom{8}{4} = \frac{8 \times 7 \times 6 \times 5}{24} = \mathbf{70 \text{ unique admissible policies}}$$

Algorithm 3 formalizes the optimization search. The enumeration evaluates all 70 policies in under 5 seconds across 60,000-flow evaluation streams.

<<<ALGORITHM_3>>>

3.4.3 Optimization Objective and Empirical Pareto Frontier
For each candidate policy $\pi \in \Pi_{70}$, we evaluate its total operational cost across all flows in both the balanced multi-state stream ($D_{\text{bal}}$) and the sustained attack-heavy stream ($D_{\text{atk}}$):
$$\text{Cost}(\pi, D) = \sum_{t=1}^N \mathcal{L}(\pi(L_t), y_t)$$

Because $\text{Cost}(\text{Allow}) = 0$ on all traffic, the net operational benefit $\text{NetBenefit}(\pi)$ measures total economic value generated relative to the unmitigated baseline:
$$\text{NetBenefit}(\pi, D) = -\text{Cost}(\pi, D)$$
Thus, $\text{NetBenefit} = -\text{Cost}$; the optimizer maximizes NetBenefit (or equivalently minimizes total operational cost).

To evaluate robust performance across differing network threat densities, the global optimization objective evaluates the combined net operational benefit as the average across both evaluation regimes:
$$\text{NetBenefit}_{\text{comb}}(\pi) = 0.5 \cdot \text{NetBenefit}(\pi, D_{\text{bal}}) + 0.5 \cdot \text{NetBenefit}(\pi, D_{\text{atk}})$$
$$\pi^* = \arg\max_{\pi \in \Pi_{70}} \text{NetBenefit}_{\text{comb}}(\pi) = \arg\min_{\pi \in \Pi_{70}} \text{Cost}_{\text{comb}}(\pi)$$

Figure 8 displays the empirical Pareto frontier across all candidate policies in (Block FPR, Quarantine FPR, Combined Net Benefit) space. A policy $\pi$ is Pareto-optimal if no alternative policy achieves weakly higher combined net benefit and weakly lower false-positive disruption across both dimensions, with at least one strict inequality.
"""
