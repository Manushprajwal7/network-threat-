import re

def update_tex():
    path = "paper/paper_v3.tex"
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    # 1. Update Abstract
    old_abs_pat = re.compile(r'\\begin\{abstract\}.*?\\end\{abstract\}', re.DOTALL)
    new_abs = r"""\begin{abstract}
Multi-stage intrusion detection systems (NIDS) for IoT networks coordinate supervised classifiers, unsupervised anomaly detectors, and dynamic trust metrics to guide automated response. However, upstream telemetry miscalibration can induce severe operational failure modes. Using the CICIoT2023 benchmark, we investigate the root causes of these failures and establish principled mitigations. First, controlled evaluation reveals that an inverted anomaly signal (AUC = 0.008) stems from training set label mismatch (training on 97.64\% attacks); retraining on verified clean traffic reorients anomaly detection (AUC 0.952, Kolmogorov-Smirnov $D = 0.866$). Second, initializing dynamic trust with neutral priors ($T_0 = 100.0$) eliminates ground-truth label leakage, elevating trust discrimination from AUC 0.044 to 0.986 across both Regime 1 (balanced) and Regime 2 (attack-heavy) evaluation streams. Third, a six-level posture escalation hierarchy establishes monotonic trust decay from 79.44 at Level $L_0$ to 10.17 at Level $L_4$; Level $L_5$ is populated only under simulated core-hub monitoring (E8) and 0 batches under peripheral edge-gateway streams. Fourth, an exhaustive combinatorial search over all 70 monotonic level-to-action policies under an operational cost model shows that canonical policy $P_{2\text{-tier}}$ delivers +1,909,843 OCU net benefit compared to +786,643 OCU for baseline $P_1$ (a 2.43-fold gain), yet ranks 9th of 70 due to collateral benign quarantine. Policy $P_{\text{opt}}$ achieves Rank 1 (+1,920,767 OCU) by eliminating benign quarantine, while a hybrid posture-veto baseline dominates all static policies. All code, datasets, and evaluation artifacts are openly archived.
\end{abstract}"""
    text = old_abs_pat.sub(lambda m: new_abs, text)

    # 2. Update Keywords
    old_kw_pat = re.compile(r'\\begin\{IEEEkeywords\}.*?\\end\{IEEEkeywords\}', re.DOTALL)
    new_kw = r"""\begin{IEEEkeywords}
Internet of Things, Intrusion Response Systems, Anomaly Detection, Isolation Forest, Training Data Purity, Dynamic Trust, Security Posture Escalation, Decision Theory, Cost-Aware Optimization, CICIoT2023.
\end{IEEEkeywords}"""
    text = old_kw_pat.sub(lambda m: new_kw, text)

    # 3. Update Section 3.1 & 3.2
    old_sec3_pat = re.compile(
        r'\\subsection\{Threat Model and Scope\}.*?\\subsection\{The Six-Level Security Posture Model\}',
        re.DOTALL
    )
    new_sec3 = r"""\subsection{Threat Model and Operational Assumptions}
To establish a formal security foundation, we define the operational threat model and scope governing our multi-stage framework:

\begin{enumerate}
  \item \textbf{Adversary Objectives}: We consider an active network adversary seeking to achieve one or more of five objectives: (a) orchestrating high-rate volumetric denial-of-service or distributed denial-of-service (DoS/DDoS) floods to exhaust gateway bandwidth; (b) recruiting vulnerable IoT devices into automated botnets (e.g., Mirai); (c) executing credential brute-force attacks against management services (SSH, Telnet); (d) performing application-layer web exploitation (SQL injection, XSS, command injection); or (e) conducting stealthy reconnaissance sweeps to map internal network vulnerabilities.
  \item \textbf{Adversary Capabilities}: The adversary can inject arbitrary network packets, spoof transmission source IP and MAC addresses, modulate flow transmission rates (employing either aggressive volumetric bursts or low-and-slow pulsing to evade time-window aggregators), and compromise peripheral IoT edge sensors.
  \item \textbf{Gateway Trust and Placement Assumptions}: We assume that the central security gateway hosting the policy engine and software-defined network (SDN) controller represents a trusted execution environment: its internal state, routing tables, and inspection pipelines cannot be directly tampered with by the adversary. The gateway operates at the edge boundary of the IoT subnet, possessing inline packet forwarding and drop capabilities to enforce tiered actions.
\end{enumerate}

\subsection{Dataset Telemetry and Evaluation Protocol}
\begin{enumerate}
  \item \textbf{Benchmark Dataset and Feature Schema}: We evaluate our framework using the CICIoT2023 benchmark \cite{ferrag2023ciciot2023}. Flow records in CICIoT2023 provide 46 statistical flow features but omit transmission source/destination IP addresses and MAC headers. Consequently, individual flows cannot be mapped to physical hardware endpoints. The 46-dimensional feature vector $\mathbf{x} \in \mathbb{R}^{46}$ is ordered according to the official schema:
  \begin{itemize}
    \item 1–7 (Temporal and Rate Counters): \texttt{flow_duration}, \texttt{Header_Length}, \texttt{Protocol Type}, \texttt{Duration}, \texttt{Rate}, \texttt{Srate}, \texttt{Drate};
    \item 8–19 (TCP Flag Numbers and Occurrence Counters): \texttt{fin_flag_number}, \texttt{syn_flag_number}, \texttt{rst_flag_number}, \texttt{psh_flag_number}, \texttt{ack_flag_number}, \texttt{ece_flag_number}, \texttt{cwr_flag_number}, \texttt{ack_count}, \texttt{syn_count}, \texttt{fin_count}, \texttt{urg_count}, \texttt{rst_count};
    \item 20–33 (Protocol and Application Layer Indicators): \texttt{HTTP}, \texttt{HTTPS}, \texttt{DNS}, \texttt{Telnet}, \texttt{SMTP}, \texttt{SSH}, \texttt{IRC}, \texttt{TCP}, \texttt{UDP}, \texttt{DHCP}, \texttt{ARP}, \texttt{ICMP}, \texttt{IPv}, \texttt{LLC};
    \item 34–46 (Statistical Moments and Dimensional Quantities): \texttt{Tot sum}, \texttt{Min}, \texttt{Max}, \texttt{AVG}, \texttt{Std}, \texttt{Tot size}, \texttt{IAT}, \texttt{Number}, \texttt{Magnitue} (retaining original schema spelling), \texttt{Radius}, \texttt{Covariance}, \texttt{Variance}, \texttt{Weight}.
  \end{itemize}
  \item \textbf{Supervised Model Complexity}: Supervised XGBoost multi-class inference evaluates $M = 150$ boosting rounds across 34 classes, constructing $34 \times 150 = 5,100$ individual decision trees with maximum depth $d_{\max} = 8$. Each flow requires up to $5,100 \times 8 = 40,800$ scalar split comparisons, scaling with complexity $O(C \cdot M \cdot d_{\max})$.
  \item \textbf{Disjoint Partitioning Protocol}: To prevent policy-selection bias and evaluation leakage, we establish a strict three-way data protocol:
  \begin{itemize}
    \item (a) Training Partition ($D_{\text{train}}$): The standard 80\% partition of CICIoT2023 containing 5,491,971 flows (129,538 clean benign flows [2.36\%] and 5,362,433 attack flows [97.64\%]). Used exclusively to train the upstream supervised XGBoost classifier and clean benign Isolation Forest ($N=20,000$ benign calibration flows).
    \item (b) Validation / Policy Selection Split ($D_{\text{val}}$): An independent split of 60,000 flows used to calibrate operational thresholds and evaluate the combinatorial sweep across all 70 monotonic response policies under the formal loss matrix.
    \item (c) Held-out Independent Test Split ($D_{\text{test}}$): A separate held-out partition of 60,000 flows drawn with a distinct random seed (seed 99) to verify that the selected policy generalizes out-of-sample without overfitting.
  \end{itemize}
  \item \textbf{Operational Window Abstraction and Graph Topology Mapping}: To provide a structured operational abstraction without inventing fictional host identifiers, our analysis unit is defined as contiguous, non-overlapping monitoring windows of $W = 100$ consecutive network flows (stride 100), representing local batch inspection at an edge gateway. Because physical flow-to-node topology headers are absent in CICIoT2023, topological routing risk for TARP is simulated over a synthetic 120-node scale-free network topology constructed via Barabási-Albert preferential attachment ($m=2$), with topological risk $R \in [0.10, 0.90]$ derived from personalized PageRank centrality ($\alpha=0.85$), calibrated to $\mu=0.42, \sigma=0.08$ (documented in Experiment E10 \cite{phillips2002graph, wang2006attack}). Batches $b \in \{0, \dots, 599\}$ are mapped to network nodes via round-robin index allocation $n(b) = b \pmod{120}$. Because all flows within batch $b$ share identical node risk $R = R[b \pmod{120}]$, $R$ is uniform within each batch. This separation enables the framework to distinguish peripheral edge device streams ($R < 0.75$) from critical backbone transit infrastructure ($R \ge 0.75$).
\end{enumerate}

\subsection{The Six-Level Security Posture Model}"""
    text = old_sec3_pat.sub(lambda m: new_sec3, text)

    # 4. Overclaim and tone replacements
    text = text.replace("conclusively demonstrates", "demonstrates")
    text = text.replace("flips decisively", "inverts completely")
    text = text.replace("escalate decisively into Level $L_5$", "escalate directly into Level $L_5$")
    text = text.replace("engage decisively against malicious vectors", "engage robustly against malicious vectors")
    text = text.replace("the Isolation Forest decisively reorients", "the Isolation Forest successfully reorients")
    text = text.replace("while malicious traffic scales decisively toward 1.00.", "while malicious traffic scales toward 1.00.")
    text = text.replace("Crucially, flow records in CICIoT2023", "Specifically, flow records in CICIoT2023")
    text = text.replace("Crucially, to verify out-of-sample generalization", "To verify out-of-sample generalization")
    text = text.replace("Crucially, this classifier performance is completely invariant", "This classifier performance is completely invariant")
    text = text.replace("Crucially, total flow counts are strictly conserved:", "Importantly, total flow counts are strictly conserved:")
    text = text.replace("Crucially, we emphasize that the 2.43-fold net benefit", "Importantly, we emphasize that the 2.43-fold net benefit")
    text = text.replace("Crucially, high topological criticality alone", "Importantly, high topological criticality alone")
    text = text.replace("a phenomenon we rigorously diagnose and resolve in Section 4.1", "a phenomenon we systematically diagnose and resolve in Section 4.1")
    text = text.replace("monitoring attention overhead must be rigorously decoupled", "monitoring attention overhead must be systematically decoupled")
    text = text.replace("This empirical duality proves that static mapping policies", "This empirical duality demonstrates that static mapping policies")
    text = text.replace("Crucially, as shown by our baseline benchmarking", "Specifically, as shown by our baseline benchmarking")

    # 5. Formulaic clauses & repetitive chains
    text = text.replace("at the cost of 29.9% benign Quarantine,", "with 29.9% benign quarantine disruption,")
    text = text.replace("at the cost of 29.9% benign Quarantine (all 18,000 blocked flows are pure attack, while 8,934 benign flows are quarantined).",
                        "while subjecting 29.9% of benign flows to quarantine containment (all 18,000 blocked flows are pure attack, while 8,934 benign flows are quarantined).")
    text = text.replace("avoiding Block-level disruption at the cost of 29.9% benign Quarantine.",
                        "avoiding Block-level disruption while incurring 29.9% benign Quarantine.")

    # 6. Update Table 3
    old_tab3_latex = r"""\begin{table*}[t]
\caption{Isolation Forest anomaly detection metrics across model capacities before and after contamination repair (60,000 evaluation flows).}
\label{tab:if_controlled}
\centering
\small
\begin{tabular}{lcccccccl}
\toprule
\textbf{Configuration} & \textbf{Trees ($M$)} & \textbf{Training Data} & \textbf{ROC AUC} & \textbf{KS $D$} & \textbf{Anomaly Gap} & \textbf{Benign Mean} & \textbf{Attack Mean} \\
\midrule
Contaminated IF & 100 & 97.5\% Contaminated & 0.0077 & 0.9530 & $-0.3077$ & 0.6901 & 0.3825 \\
Contaminated IF & 200 & 97.5\% Contaminated & 0.0084 & 0.9504 & $-0.2973$ & 0.6810 & 0.3837 \\
Clean IF (Repaired) & 100 & 100\% Clean Benign & 0.9435 & 0.8564 & $+0.0769$ & 0.4843 & 0.5612 \\
Clean IF (Repaired) & 200 & 100\% Clean Benign & 0.9523 & 0.8659 & $+0.0819$ & 0.4829 & 0.5649 \\
\bottomrule
\end{tabular}
\end{table*}"""
    tab3_pat = re.compile(r'\\begin\{table\*\}\[t\]\s*\\caption\{Controlled quantitative comparison of Isolation Forest.*?\\end\{table\*\}', re.DOTALL)
    text = tab3_pat.sub(lambda m: old_tab3_latex, text)

    # 7. Update Table 8
    old_tab8_latex = r"""\begin{table*}[t]
\caption{Operational performance comparison across candidate response policies on multi-state and attack-heavy evaluation streams (OCU).}
\label{tab:master_policy}
\centering
\footnotesize
\begin{tabular}{llccccccc}
\toprule
\textbf{Policy} & \textbf{Enforcement Mapping ($L_0$--$L_5$)} & \textbf{Bal Net} & \textbf{Atk Net} & \textbf{Comb Net} & \textbf{Bal Blk FPR} & \textbf{Bal Quar FPR} & \textbf{Flood Blk FPR} & \textbf{Search Rank} \\
\midrule
$P_0$ (Baseline [1]) & Heuristic (Alert / Quarantine) & --- & +329,835 & --- & 0.00\% & --- & 0.00\% & Unranked \\
$P_{\text{opt}}$ (Global Optimum) & [Allow, Allow, Restrict, Restrict, Block, Block] & +985,534 & +2,856,000 & +1,920,767 & 0.00\% & 0.00\% & 0.00\% & Rank 1 of 70 \\
$P_1$ (Conservative Default) & [Allow, Alert, Restrict, Quarantine, Quarantine, Block] & +423,686 & +1,149,600 & +786,643 & 0.00\% & 29.90\% & 0.00\% & Rank 44 of 70 \\
$P_{2\text{-tier}}$ (Canonical) & [Allow, Alert, Restrict, Quarantine, Block, Block] & +963,686 & +2,856,000 & +1,909,843 & 0.00\% & 29.90\% & 100.00\% & Rank 9 of 70 \\
$P_2$ (Aggressive Baseline) & [Allow, Restrict, Quarantine, Block, Block, Block] & +907,520 & +2,856,000 & +1,881,760 & 29.90\% & 0.00\% & 100.00\% & Rank 28 of 70 \\
$P_{\text{XGB}}$ (Pure Flow Classifier) & Per-Flow Classifier (No Posture) & +1,360,450 & +2,928,000 & +2,144,225 & 9.46\% & 0.00\% & 9.44\% & Unranked (9.5\% FPR) \\
$P_{\text{hybrid}}$ (Posture + Benign Veto) & Tiered Posture + Flow Veto ($L_4$) & +963,066 & +2,899,150 & +1,931,108 & 0.00\% & 30.10\% & 38.89\% & Dominates Static \\
\bottomrule
\end{tabular}
\end{table*}"""
    tab8_pat = re.compile(r'\\begin\{table\*\}\[t\]\s*\\caption\{Master policy performance comparison.*?\\end\{table\*\}', re.DOTALL)
    text = tab8_pat.sub(lambda m: old_tab8_latex, text)

    # 8. Update Table Captions to concise descriptive titles
    text = text.replace(
        r"\caption{Architectural and quantitative progression comparison between the published baseline [1] and the proposed framework on the CICIoT2023 benchmark.}",
        r"\caption{Comparison between published baseline [1] and the proposed framework on the CICIoT2023 benchmark.}"
    )
    text = text.replace(
        r"\caption{Formal decision-theoretic cost matrix $\mathcal{L}(a, y)$ defining unit operational penalties and containment benefits across five response actions in Operational Cost Units (OCU) for benign and attack ground-truth traffic states.}",
        r"\caption{Decision-theoretic cost matrix $\mathcal{L}(a, y)$ defining unit operational penalties and containment benefits across five response actions (OCU).}"
    )
    text = text.replace(
        r"\caption{Dynamic trust band distribution and discrimination metrics across five progressive calibration configurations ($C_0^*$ to $C_4^*$) on the 60,000-flow evaluation stream under universal neutral prior $T_0 = 100.0$ without label leakage.}",
        r"\caption{Dynamic trust score distribution and discrimination metrics across calibration configurations $C_0^*$ to $C_4^*$ under neutral prior $T_0 = 100.0$.}"
    )
    text = text.replace(
        r"\caption{Six-level security posture distribution on the sustained volumetric attack-heavy stream (60,000 flows, 600 batches of $W=100$ flows, 97.60\% attack base rate).}",
        r"\caption{Security posture level distribution and attack composition under sustained volumetric attack stream (60,000 flows, $W=100$).}"
    )
    text = text.replace(
        r"\caption{Six-level security posture distribution on the stratified multi-state benchmark stream (60,000 flows, 600 batches of $W=100$ flows, 50.20\% attack base rate).}",
        r"\caption{Security posture level distribution and attack composition under stratified multi-state benchmark stream (60,000 flows, $W=100$).}"
    )
    text = text.replace(
        r"\caption{Comprehensive action-level attack prevalence audit ($\text{Attack Flows} / \text{Total Flows}$) on the multi-state benchmark stream. Published baseline $P_0$ exhibited severe action precision inversion (Alert 100.00\% > Quarantine 70.50\%), whereas proposed policies $P_1$ and $P_{2\text{-tier}}$ establish strictly non-decreasing precision across all five enforcement tiers ($0.00\% \le 0.00\% < 46.40\% < 51.71\% < 100.00\%$).}",
        r"\caption{Action-level precision and false positive rates under baseline $P_0$, $P_1$, and proposed $P_{2\text{-tier}}$ on the multi-state benchmark stream.}"
    )
    text = text.replace(
        r"\caption{Per-family flow counts, action distribution under recommended policy $P_{2\text{-tier}}$, and mean dynamic trust scores across eight threat families on the multi-state benchmark stream (incorporating all 30,118 attack flows).}",
        r"\caption{Per-family flow counts, enforcement action distributions, and mean dynamic trust scores under policy $P_{2\text{-tier}}$ (30,118 attack flows).}"
    )
    text = text.replace(
        r"\caption{Cost sensitivity analysis across false-blocking scaling factors $\lambda \in [0.2, 5.0]$, varying benign Block penalty from 10 to 250 OCU. Policy $P_{2\text{-tier}}$ consistently maintains a 2.24x to 2.46x benefit advantage over conservative baseline $P_1$ across the entire parameter space.}",
        r"\caption{Cost sensitivity analysis across false-blocking scaling factors $\lambda \in [0.2, 5.0]$ on the multi-state stream.}"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Updated paper_v3.tex successfully!")

if __name__ == "__main__":
    update_tex()
