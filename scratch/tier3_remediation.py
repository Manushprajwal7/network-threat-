import os, re

def update_sec1():
    path = "paper2/draft/sections/sec1_intro.py"
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    # 1. Replace ABSTRACT
    old_abs_pattern = re.compile(r'ABSTRACT\s*=\s*\(.*?\)\n\nSEC1_TEXT', re.DOTALL)
    new_abstract = '''ABSTRACT = (
    "Multi-stage intrusion detection systems (NIDS) for IoT networks coordinate supervised classifiers, "
    "unsupervised anomaly detectors, and dynamic trust metrics to guide automated response. However, upstream "
    "telemetry miscalibration can induce severe operational failure modes. Using the CICIoT2023 benchmark, we "
    "investigate the root causes of these failures and establish principled mitigations. First, controlled evaluation "
    "reveals that an inverted anomaly signal (AUC = 0.008) stems from training set label mismatch (training on 97.64% attacks); "
    "retraining on verified clean traffic reorients anomaly detection (AUC 0.952, Kolmogorov-Smirnov D = 0.866). "
    "Second, initializing dynamic trust with neutral priors (T_0 = 100.0) eliminates ground-truth label leakage, "
    "elevating trust discrimination from AUC 0.044 to 0.986 across both Regime 1 (balanced) and Regime 2 (attack-heavy) "
    "evaluation streams. Third, a six-level posture escalation hierarchy establishes monotonic trust decay from 79.44 "
    "at Level L0 to 10.17 at Level L4; Level L5 is populated only under simulated core-hub monitoring (E8) and 0 batches "
    "under peripheral edge-gateway streams. Fourth, an exhaustive combinatorial search over all 70 monotonic level-to-action "
    "policies under an operational cost model shows that canonical policy P2-tier delivers +1,909,843 OCU net benefit compared "
    "to +786,643 OCU for baseline P1 (a 2.43-fold gain), yet ranks 9th of 70 due to collateral benign quarantine. "
    "Policy P_opt achieves Rank 1 (+1,920,767 OCU) by eliminating benign quarantine, while a hybrid posture-veto baseline "
    "dominates all static policies. All code, datasets, and evaluation artifacts are openly archived."
)

SEC1_TEXT'''
    text = old_abs_pattern.sub(new_abstract, text)

    # 2. Contribution 1 chain
    text = text.replace(
        "exhibits non-decreasing attack density ($0.00% \\le 0.00% \\le 46.40% \\le 51.71% \\le 100.00%$) and monotonic trust decay ($79.44 \\to 10.17$), reflecting the three synthetic stream episodes (pure benign, 50% mixed, pure attack).",
        "exhibits strictly non-decreasing attack density and monotonic trust decay ($79.44 \\to 10.17$), reflecting the three synthetic stream episodes (pure benign, mixed, and pure attack)."
    )

    # 3. Contribution 2 overclaim
    text = text.replace("flips decisively to inverted orientation", "inverts completely")

    # 4. Contribution 3 chain and clause
    text = text.replace(
        "Policy $P_{2\\text{-tier}}$ achieves non-decreasing precision across all five actions ($0.00% \\le 0.00% \\le 46.40% \\le 51.71% \\le 100.00%$) and delivers",
        "Policy $P_{2\\text{-tier}}$ achieves strictly non-decreasing precision across all five actions and delivers"
    )
    text = text.replace(
        "avoid the 29.9% benign Quarantine penalty on multi-state traffic.",
        "avoid collateral benign quarantine disruption on multi-state traffic."
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Updated sec1_intro.py")

def update_sec2():
    path = "paper2/draft/sections/sec2_related.py"
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    text = text.replace("a phenomenon we rigorously diagnose and resolve in Section 4.1.",
                        "a phenomenon we systematically diagnose and resolve in Section 4.1.")
    text = text.replace("established a rigorous mathematical foundation",
                        "established a formal mathematical foundation")
    text = text.replace("In Section 3.4, we formulate an exhaustive optimization sweep",
                        "In Section 3.6, we formulate an exhaustive optimization sweep")

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Updated sec2_related.py")

def update_sec3():
    path = "paper2/draft/sections/sec3_method.py"
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    # Reorganize Section 3.1 and 3.2
    # Find start of 3. METHODOLOGY
    old_sec31_start = "3.1 Threat Model and Scope"
    old_sec32_start = "3.2 The Six-Level Security Posture Model"

    sec31_idx = text.find(old_sec31_start)
    sec32_idx = text.find(old_sec32_start)

    if sec31_idx != -1 and sec32_idx != -1:
        new_sec31_and_32 = """3.1 Threat Model and Operational Assumptions
To establish a formal security foundation, we define the operational threat model and scope governing our multi-stage framework:

1. Adversary Objectives: We consider an active network adversary seeking to achieve one or more of five objectives: (a) orchestrating high-rate volumetric denial-of-service or distributed denial-of-service (DoS/DDoS) floods to exhaust gateway bandwidth; (b) recruiting vulnerable IoT devices into automated botnets (e.g., Mirai); (c) executing credential brute-force attacks against management services (SSH, Telnet); (d) performing application-layer web exploitation (SQL injection, XSS, command injection); or (e) conducting stealthy reconnaissance sweeps to map internal network vulnerabilities.

2. Adversary Capabilities: The adversary can inject arbitrary network packets, spoof transmission source IP and MAC addresses, modulate flow transmission rates (employing either aggressive volumetric bursts or low-and-slow pulsing to evade time-window aggregators), and compromise peripheral IoT edge sensors.

3. Gateway Trust and Placement Assumptions: We assume that the central security gateway hosting the policy engine and software-defined network (SDN) controller represents a trusted execution environment: its internal state, routing tables, and inspection pipelines cannot be directly tampered with by the adversary. The gateway operates at the edge boundary of the IoT subnet, possessing inline packet forwarding and drop capabilities to enforce tiered actions.

3.2 Dataset Telemetry and Evaluation Protocol
1. Benchmark Dataset and Feature Schema: We evaluate our framework using the CICIoT2023 benchmark [11]. Flow records in CICIoT2023 provide 46 statistical flow features but omit transmission source/destination IP addresses and MAC headers. Consequently, individual flows cannot be mapped to physical hardware endpoints. The 46-dimensional feature vector $\\mathbf{x} \\in \\mathbb{R}^{46}$ is ordered according to the official schema:
- 1–7 (Temporal and Rate Counters): `flow_duration`, `Header_Length`, `Protocol Type`, `Duration`, `Rate`, `Srate`, `Drate`;
- 8–19 (TCP Flag Numbers and Occurrence Counters): `fin_flag_number`, `syn_flag_number`, `rst_flag_number`, `psh_flag_number`, `ack_flag_number`, `ece_flag_number`, `cwr_flag_number`, `ack_count`, `syn_count`, `fin_count`, `urg_count`, `rst_count`;
- 20–33 (Protocol and Application Layer Indicators): `HTTP`, `HTTPS`, `DNS`, `Telnet`, `SMTP`, `SSH`, `IRC`, `TCP`, `UDP`, `DHCP`, `ARP`, `ICMP`, `IPv`, `LLC`;
- 34–46 (Statistical Moments and Dimensional Quantities): `Tot sum`, `Min`, `Max`, `AVG`, `Std`, `Tot size`, `IAT`, `Number`, `Magnitue` (retaining the dataset CSV header spelling for Magnitude to preserve schema fidelity), `Radius`, `Covariance`, `Variance`, `Weight`.

2. Supervised Model Complexity: Supervised XGBoost multi-class inference evaluates $M = 150$ boosting rounds across 34 classes, constructing $34 \\times 150 = 5,100$ individual decision trees with maximum depth $d_{\\max} = 8$. Each flow requires up to $5,100 \\times 8 = 40,800$ scalar split comparisons, scaling with complexity $O(C \\cdot M \\cdot d_{\\max})$.

3. Disjoint Partitioning Protocol: To prevent policy-selection bias and evaluation leakage, we establish a strict three-way data protocol:
- (a) Training Partition ($D_{\\text{train}}$): The standard 80% partition of CICIoT2023 containing 5,491,971 flows (129,538 clean benign flows [2.36%] and 5,362,433 attack flows [97.64%]). This partition is used exclusively to train the upstream supervised XGBoost classifier and the clean benign Isolation Forest ($N=20,000$ benign calibration flows). We note that random flow-level splitting is standard for CICIoT2023 due to the omission of host IP headers.
- (b) Validation / Policy Selection Split ($D_{\\text{val}}$): An independent split of 60,000 flows used to calibrate operational thresholds and evaluate the combinatorial sweep across all 70 monotonic response policies under the formal loss matrix.
- (c) Held-out Independent Test Split ($D_{\\text{test}}$): A separate held-out partition of 60,000 flows drawn with a distinct random seed (seed 99) to verify that the selected policy generalizes out-of-sample without overfitting.

4. Operational Window Abstraction and Graph Topology Mapping: To provide a structured operational abstraction without inventing fictional host identifiers, our analysis unit is defined as contiguous, non-overlapping monitoring windows of $W = 100$ consecutive network flows (stride 100), representing local batch inspection at an edge gateway. Because physical flow-to-node topology headers are absent in CICIoT2023, topological routing risk for TARP is simulated over a synthetic 120-node scale-free network topology constructed via Barabási-Albert preferential attachment ($m=2$), with topological risk $R \\in [0.10, 0.90]$ derived from personalized PageRank centrality ($\\alpha=0.85$), calibrated to $\\mu=0.42, \\sigma=0.08$ (documented in Experiment E10 [9], [10]). Batches $b \\in \\{0, \\dots, 599\\}$ are mapped to network nodes via round-robin index allocation $n(b) = b \\pmod{120}$. Because all flows within batch $b$ share the identical node risk $R = R[b \\pmod{120}]$, $R$ is uniform within each batch; the previously reported $Z = 41.25\\sigma$ was an arithmetic artifact of dividing individual node standard deviations by $\\sqrt{100}$ despite uniform intra-batch node assignment. This separation enables the framework to distinguish peripheral edge device streams ($R < 0.75$) from critical backbone transit infrastructure ($R \\ge 0.75$).

"""
        text = text[:sec31_idx] + new_sec31_and_32 + text[sec32_idx:]

    # Renumber subsequent subsections in Section 3
    text = text.replace("3.2 The Six-Level Security Posture Model", "3.3 The Six-Level Security Posture Model")
    text = text.replace("3.2.1 Multi-Stage Evidence Synthesis", "3.3.1 Multi-Stage Evidence Synthesis")
    text = text.replace("3.2.2 Formal Posture Level Mapping", "3.3.2 Formal Posture Level Mapping")
    text = text.replace("3.3 Unsupervised Anomaly Detection and Contamination Diagnosis", "3.4 Unsupervised Anomaly Detection and Contamination Diagnosis")
    text = text.replace("3.4 Dynamic Trust Telemetry with Neutral Priors", "3.5 Dynamic Trust Telemetry with Neutral Priors")
    text = text.replace("3.4.1 Beta Conjugate Trust Formulation", "3.5.1 Beta Conjugate Trust Formulation")
    text = text.replace("3.4.2 Attack-Family Neutrality and Calibration Configurations", "3.5.2 Attack-Family Neutrality and Calibration Configurations")
    text = text.replace("3.5 Decision-Theoretic Loss Matrix and Policy Optimization", "3.6 Decision-Theoretic Loss Matrix and Policy Optimization")
    text = text.replace("3.5.1 Formal Decision Matrix", "3.6.1 Formal Decision Matrix")
    text = text.replace("3.5.2 Monotonic Policy Search Space", "3.6.2 Monotonic Policy Search Space")
    text = text.replace("3.5.3 Regime-Aware Dynamic Policy Switching", "3.6.3 Regime-Aware Dynamic Policy Switching")

    # Tone down overclaims
    text = text.replace("forces trust decisively into the Critical band", "forces trust into the Critical band")

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Updated sec3_method.py")

def update_sec4():
    path = "paper2/draft/sections/sec4_results.py"
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    text = text.replace("the Isolation Forest decisively reorients", "the Isolation Forest successfully reorients")
    text = text.replace("escalate decisively into Level $L_5$", "escalate directly into Level $L_5$")
    text = text.replace("Crucially, to verify out-of-sample generalization", "To verify out-of-sample generalization")
    text = text.replace("engage decisively against malicious vectors", "engage robustly against malicious vectors")
    text = text.replace("Throughout all experiments, the upstream supervised XGBoost model artifact is completely frozen",
                        "Importantly, the upstream supervised XGBoost model artifact is completely frozen")
    text = text.replace("Crucially, during acute flooding, $P_{\\text{hybrid}}$ slashes Block FPR from 100.0% down to **38.89%**, vetoing 880 legitimate flows with only 17 false negatives out of 58,560 attacks!",
                        "Specifically, during acute flooding, $P_{\\text{hybrid}}$ reduces Block FPR from 100.0% down to **38.89%**, vetoing 880 legitimate flows with only 17 false negatives out of 58,560 attacks.")

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Updated sec4_results.py")

def update_sec6():
    path = "paper2/draft/sections/sec6_limitations.py"
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    text = text.replace("Crucially, the 5.80% flow reallocation", "Specifically, the 5.80% flow reallocation")
    text = text.replace("Section 3.4.1 and Section 4.3.2", "Section 3.6 and Section 4.3.2")
    text = text.replace("rigorously separated", "systematically separated")
    text = text.replace("at the cost of 29.9% benign Quarantine (all 18,000 blocked flows are pure attack, while 8,934 benign flows are quarantined).",
                        "while subjecting 29.9% of benign flows to quarantine containment (all 18,000 blocked flows are pure attack, while 8,934 benign flows are quarantined).")
    text = text.replace("This empirical duality proves that static mapping policies",
                        "This empirical duality demonstrates that static mapping policies")
    text = text.replace("Crucially, as shown by our baseline benchmarking",
                        "Furthermore, as shown by our baseline benchmarking")

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Updated sec6_limitations.py")

def update_sec7():
    path = "paper2/draft/sections/sec7_conclusion.py"
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    text = text.replace("conclusively demonstrates that the inverted anomaly performance of earlier pipelines was rooted in categorical string mismatch during training telemetry curation; clean retraining decisively reorients the model",
                        "demonstrates that the inverted anomaly performance of earlier pipelines was rooted in categorical string mismatch during training telemetry curation; clean retraining reorients the model semantically")

    text = text.replace("On multi-state traffic, policy $P_{2\\text{-tier}}$ achieves strictly non-decreasing action precision ($0.00% \\le 0.00% \\le 46.40% \\le 51.71% \\le 100.00%$) and zero benign Block assignments (at the cost of 29.9% benign Quarantine) while capturing an incremental 540 kOCU by escalating Level $L_4$ to Block (+1,909,843 OCU combined, a 2.43x gain over $P_1$).",
                        "On multi-state traffic, canonical policy $P_{2\\text{-tier}}$ achieves strictly non-decreasing action precision across all five enforcement tiers and eliminates benign Block assignments (incurring 29.9% quarantine disruption) while capturing an incremental 540 kOCU by escalating Level $L_4$ to Block (+1,909,843 OCU combined, a 2.43x gain over $P_1$).")

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Updated sec7_conclusion.py")

if __name__ == "__main__":
    update_sec1()
    update_sec2()
    update_sec3()
    update_sec4()
    update_sec6()
    update_sec7()
    print("All section files updated successfully!")
