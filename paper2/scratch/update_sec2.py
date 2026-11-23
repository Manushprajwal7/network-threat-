sec2_content = r'''# Section 2: Related Work
SEC2_TEXT = r"""2. RELATED WORK

2.1 Multi-Stage IoT Intrusion Detection Architectures
Intrusion detection in Internet of Things (IoT) ecosystems has evolved from monolithic appliances into distributed, multi-stage architectures [5], [6]. General taxonomies categorize these methodologies into signature-based, anomaly-based, and hybrid architectures [14], with empirical deployments spanning smart cities [15], connected agriculture [16], and multi-layer edge topologies [17]. Early signature frameworks like Snort [18] and Bro/Zeek [5] established deterministic pattern-matching, but centralized matchers struggle with zero-day exploits or polymorphic variants in cyber-physical environments [19].

To overcome these constraints, hierarchical multi-tier pipelines have been deployed. Anthi et al. [20] introduced a three-tier framework discriminating between benign traffic, attack categories, and granular threat signatures, though it lacked dynamic behavioral feedback. Pajouh et al. [21] combined Linear Discriminant Analysis with Random Forest and Naive Bayes for industrial IoT, achieving efficient classification but struggling against subtle reconnaissance. Ferrag et al. [6] observed that multi-stage edge pipelines frequently suffer from uncalibrated error propagation across sequential tiers. In our foundational base paper [1] (*J. Cybersecur. Priv.* 2026, 6(5), 181), integrating an upstream XGBoost classifier with graph topology analysis improved context-aware threat scoring; however, uncalibrated inter-stage thresholds caused downstream trust collapse. This study addresses these failure modes as a direct continuation through diagnostic auditing, bi-directional coupling, and response optimization.

2.2 Machine Learning Classifiers and Feature Engineering in Network Telemetry
Supervised machine learning forms the analytical core of modern network security [12], [6], [22]. Grounded in foundational data mining and meta-learning methodologies [23], adaptive profiling of flow-level statistics (connection duration, service type, byte distributions) captures deviations from normal baselines [12].

In high-speed environments, tree-based ensembles, particularly Gradient Boosted Decision Trees (XGBoost) [7], dominate tabular telemetry benchmarks [12]. Ensembles handle non-linear boundaries and feature scale disparities effectively, delivering high throughput. However, standard macro-averaged metrics often mask localized vulnerabilities, such as when extreme class imbalances cause high accuracy despite failing to isolate critical edge cases.

Feature representation remains decisive for generalization [24], [25], [26]. The CICIoT2023 benchmark [11] comprises 46 statistical features capturing packet lengths, inter-arrival times, protocol flags, and flow rates across 34 threat categories. The full 46-feature vector from [1] is retained for all reported experiments.

2.3 Unsupervised Anomaly Detection in Network Security
Unsupervised anomaly detection aims to detect zero-day intrusions without pre-labeled attack signatures [8]. Isolation Forests isolate anomalies by recursively partitioning feature space using orthogonal hyperplanes, leveraging the insight that abnormal points require fewer random splits than normal clusters [8].

Operational deployments, however, face critical challenges [27]. Setting fixed decision thresholds in non-stationary network environments often leads to alarm storms [28], [29]. Furthermore, unsupervised models are vulnerable to training data corruption: when contaminated with unlabeled attack traffic, decision boundaries warp, classifying malicious activity as nominal and benign patterns as anomalous [27].

2.4 Dynamic Trust Modeling and Continuous Risk Assessment
Dynamic trust models complement per-flow classification by maintaining stateful behavioral assessments over temporal inspection windows [30], [31]. Rooted in trust and reputation architectures for distributed systems [30], these frameworks discount historical evaluations using Exponentially Weighted Moving Averages (EWMA) to balance stability with responsiveness.

The Zero Trust Architecture (ZTA) paradigm (NIST SP 800-207) requires continuous evaluation of implicit trust rather than static perimeter defense [32], [33]. In our base paper [1], an Adaptive Dynamic Trust Model (ADTM) evaluated 100-flow batches using multi-source penalties; however, heuristic initialization and uncalibrated anomaly inputs caused severe trust score compression. We mitigate this by enforcing neutral prior initialization ($T_0 = 100.0$) and adaptive EWMA smoothing.

2.5 Network Topology Analysis, Attack Graph Criticality, and Topology Reconciliation
Per-flow detection lacks topological context: an anomalous flow targeting an isolated edge sensor carries less systemic risk than one targeting a central industrial gateway [33]. Attack graph modeling evaluates multi-hop lateral propagation across enterprise subnets [9], [10], [34].

To avoid the combinatorial complexity of full attack graphs, the foundational architecture in our base paper [1] introduced the Topology-Aware Risk Propagation (TARP) metric over a scale-free network graph. TARP computes personalized PageRank centrality, betweenness centrality, and degree distributions to assign each entity a topological risk score $\tau_e \in [0, 1]$:
$$\tau_e = (1-d)\,\mathbf{v} + d\,\mathbf{P}^{\top}\mathbf{p}, \quad \tau_e \in [0,1]$$
where $\mathbf{P}$ is the row-stochastic adjacency transition matrix, $\mathbf{v}$ the teleportation vector, and $d = 0.85$.

Topology Reconciliation Between Foundational and Audited Architectures:
Our audit investigated a structural discrepancy between the graph topologies reported across studies. The base paper [1] specifies $N=120$ nodes and 342 links ($\bar{k} = 5.70$). In contrast, a canonical Barabási-Albert scale-free graph with attachment parameter $m=2$ on 120 nodes yields exactly $E = 2 \times (120 - 2) = 236$ links ($\bar{k} = 3.93$). Mathematical reconciliation confirms that the 342-edge graph was generated via preferential attachment with $m=3$ applied to 114 added nodes ($114 \times 3 = 342\text{ edges}$), yielding 8 hub nodes exceeding the $R \ge 0.75$ threshold. In contrast, the canonical $m=2$ topology yields exactly 2 hub nodes (Node 0 with $R=0.9000$ and Node 4 with $R=0.8089$). Table 2d compares structural graph metrics between both topologies. Both synthetic topologies preserve scale-free degree distributions and yield similar PageRank risk scores; neither topology is fitted to or validated against a measured IoT deployment, so the agreement is a structural sensitivity check rather than reproduction of a real network ($\mu_R = 0.4189, \sigma_R = 0.0721$ under $m=2$; $\mu_R \approx 0.42$ under $m=3$).

Centrality scores are calibrated to a target normal distribution $\mathcal{N}(0.42, 0.08)$ and clipped to $[0.10, 0.90]$ (where Node 0 sits at the upper clip). Consequently, the critical-hub threshold centrality deviation $Z_{\text{thresh}} = (0.75 - 0.4189)/0.0721 = 4.5931\sigma$ is a descriptive property of the synthetic generator distribution rather than empirical statistical proof of network defense efficacy. Furthermore, topological indicator $c_{\text{topo}}$ depends strictly on ingress node mapping $n(b) = b \pmod{120}$ and carries no dynamic traffic information.

2.6 Policy Enforcement, SOAR, and Cost-Sensitive Automated Response
Automated Intrusion Response Systems (IRS) bridge alert generation and incident mitigation [35], [36], [13]. Static alert-to-action scripts lack cost sensitivity: disconnecting a critical medical telemetry node or industrial actuator inflicts disruption costs that often dwarf the threat itself [35], [36]. Security Orchestration, Automation, and Response (SOAR) frameworks seek to optimize response selection via cost-sensitive decision theory [35], [36], [13].

As formalized by Lee et al. [37] and Gaffney and Ulvila [38], optimal response actions minimize expected operational loss over threat states:
$$\mathbb{E}[\mathcal{L}(a \mid \mathbf{x})] = \sum_{y \in \mathcal{Y}} P(y \mid \mathbf{x}) \mathcal{L}(a, y)$$
where $\mathcal{L}(a, y)$ penalizes false disruptions and unmitigated compromises asymmetrically. In Section 3.4, we enumerate all 70 monotonic posture-to-action mappings to identify the lowest-cost mapping and its neighbours under the assumed OCU loss matrix; safety compliance is treated as the monotonicity and boundary constraints, not as a separately verified property.

2.7 Training Data Contamination and Class-Name Mismatches
The empirical impact of training data contamination on unsupervised anomaly detectors in cyber-security remains under-researched. In large-scale benchmarks like CICIoT2023 [11], class-naming conventions frequently diverge across documentation, scripts, and raw data headers. When unsupervised one-class filtering fails silently, the detector trains on the full dataset—which is 97.64% attack traffic in CICIoT2023. Consequently, normality semantics invert: common volumetric attacks are perceived as normal, while benign flows are flagged as anomalies [27], underscoring the importance of computational reproducibility [39] and software provenance [40].

2.8 Conceptual Comparison with Industrial Security Taxonomies
To contextualize our six-level posture model within industrial security standards:
1. IEC 62443 Security Levels (SL1 to SL4) [41]: IEC 62443 specifies design-time target protection levels against intentional compromise. While our framework is a dynamic runtime incident escalation mechanism, its tiered structure ($L_0$–$L_5$) mirrors this progression: low-severity monitoring ($L_0, L_1$) addresses casual operational deviations; intermediate containment ($L_2, L_3$) counters targeted intrusions; and aggressive containment ($L_4, L_5$) mitigates multi-vector campaigns. We note this serves as a conceptual analogy rather than formal compliance equivalence.
2. NIST SP 800-53 Rev. 5 [42]: NIST categorizes security impact into Low, Moderate, and High tiers. Our cost matrix mirrors these categories by heavily penalizing false disruptions of critical endpoints while scaling containment value for high-impact attacks.
3. MITRE ATT&CK Framework [43]: The MITRE matrix structures adversarial tactics from initial reconnaissance to impact. Our pipeline maps telemetry to these tactics: XGBoost classifies known attack types, clean Isolation Forest detects payload evasion anomalies, TARP quantifies lateral movement risk, and ADTM tracks dwell time.
4. Distinction from Evaluation Standards [44]: Unlike Common Criteria Evaluation Assurance Levels (EAL1–EAL7) [44], which evaluate static design verification depth during certification, our posture model governs dynamic runtime escalation under streaming telemetry.

Table 1 provides an architectural and quantitative comparison between the base paper framework [1] and this proposed continuation framework.
"""
'''

with open('draft/sections/sec2_related.py', 'w', encoding='utf-8') as f:
    f.write(sec2_content)

print("Successfully updated draft/sections/sec2_related.py")
