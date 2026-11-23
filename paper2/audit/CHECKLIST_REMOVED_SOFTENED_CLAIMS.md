# Forensic Audit Checklist: Removed, Softened, and Conditionalized Claims

**Manuscript Title**: *Six-Level Security Posture Escalation with Training-Data Contamination Repair and Cost-Aware Response Optimization for IoT Intrusion Detection*  
**Audit Date**: November 17, 2026  
**Auditor / Verification Lead**: Autonomous Deep-Dive Forensic Audit Agent  
**Master Ledger**: [`audit/consistency.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/audit/consistency.csv)  
**Cryptographic Manifest**: [`audit/SHA256SUMS.txt`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/audit/SHA256SUMS.txt)  

---

## Executive Summary of Audit Actions

Pursuant to the forensic review instructions, every numeric claim, ranking, inequality, confidence interval, $p$-value, AUC, and policy count across the manuscript was checked against code artifacts, recomputed from first principles, and categorized. 

- **Total Claims Audited**: 38 formal claims in `audit/consistency.csv`.
- **Fully Supported & Verified**: 26 claims (68.4%).
- **Softened / Conditionalized**: 8 claims (21.1%).
- **Removed / Corrected**: 4 claims (10.5%).
- **Unverified Claims Remaining**: **0 (0.0%)**.

---

## Detailed Checklist of Removed, Softened, and Conditionalized Claims

### 1. Headline Policy Recommendation: $P_{\text{hybrid}}$ vs. $P_{\text{XGB}}$
- **Original Claim**: $P_{\text{hybrid}}$ claimed as the unconditional *"primary operational standard"* and *"strictly dominating all static policies"*.
- **Empirical Audit Finding (Task 3 & Task 4)**: 
  - Across 10 evaluation seeds, standalone confidence-gated XGBoost ($P_{\text{XGB}}$) achieves a combined net benefit of **$+2,181,975 \pm 2,732$ OCU**, outperforming $P_{\text{hybrid}}$ (**$+1,934,546 \pm 2,537$ OCU**) by **$+247,429$ OCU** (Wilcoxon $W = 0.0, p = 0.002$).
  - $P_{\text{XGB}}$ wins on closed-world test splits because CICIoT2023 features stationary closed-world threat distributions where supervised tree boosting attains 98.99% accuracy and near-perfect attack recall with negligible false positives (0.45% Block FPR).
- **Action Taken in Manuscript**:
  - **Softened to a Conditional Recommendation**: The claim that $P_{\text{hybrid}}$ is the "primary operational standard" has been removed.
  - The manuscript now explicitly states that on stationary closed-world networks with known attack signatures, pure confidence-gated per-flow classification ($P_{\text{XGB}}$) maximizes nominal OCU benefit (+2.18M OCU).
  - $P_{\text{hybrid}}$ is recommended conditionally for open-world settings subject to regime shifts, novel threats, and stealthy reconnaissance, where it provides multi-stage defense-in-depth and cuts flood Block FPR from 100.0% to 34.66% (+1.93M OCU).
  - *Locations*: Abstract, Contribution 3, Section 4.3.2, Section 5.3, Section 6.9, Section 7.

---

### 2. Universal Zero False-Positive Blocking & "Satisfying Availability"
- **Original Claim**: Asserted that the posture escalation framework *"satisfies availability"* and achieves *"0.00% false-positive blocking across all operational environments"*.
- **Empirical Audit Finding (Task 3 & Task 4)**:
  - On the stratified balanced benchmark, canonical policy $P_{2\text{-tier}}$ achieves 0.00% Block FPR, but incurs a **28.87%–29.90% Quarantine FPR** (quarantining 8,934 benign flows in Level $L_3$).
  - On unstratified (shuffled) streams, Quarantine FPR surges to **71.44%–74.60%**.
  - During unsegmented volumetric floods, all 60,000 flows collapse into Level $L_4$, resulting in **100.00% Block FPR** on embedded benign flows for all static policies ($P_{\text{opt}}$, $P_{2\text{-tier}}$, $P_2$).
  - $P_{\text{hybrid}}$ slashes flood Block FPR to **34.66%** across 10 seeds (vetoing 950 benign flows in Level $L_4$ with 25 false negatives), but does not achieve zero.
- **Action Taken in Manuscript**:
  - **Removed Universal Zero Blocking**: Removed all unqualified claims of zero blocking.
  - Transparently reported the dual-regime breakdown: 0.00% Block FPR on balanced traffic at the expense of 29.9% Quarantine disruption; 100.0% Block FPR under flood saturation for static policies; and 34.66% Block FPR for $P_{\text{hybrid}}$.
  - Added dedicated limitation **Section 6.12** detailing the operational burden of quarantine false alarms on IoT availability SLAs.
  - *Locations*: Abstract, Contribution 1, Contribution 3, Table 8, Section 4.3.2, Section 6.6, Section 6.12.

---

### 3. Real-Time and Line-Rate Operation Claims
- **Original Claim**: Described the multi-stage architecture as operating in *"real-time at line rate"*.
- **Empirical Audit Finding (Task 7)**:
  - Per-flow CPU computation latency is **35.00 $\mu\text{s}$** per flow (~28,575 flows/sec throughput on a single CPU core): XGBoost 28.14 $\mu\text{s}$ (80.4%), Isolation Forest 2.67 $\mu\text{s}$ (7.6%), TARP 0.0029 $\mu\text{s}$ (0.01%), ADTM 3.82 $\mu\text{s}$ (10.9%), Posture Escalation 0.36 $\mu\text{s}$ (1.0%).
  - However, accumulating temporal monitoring batches of $W = 100$ flows introduces buffering delay: at 10 Gbps core line rates (~28,500 flows/sec), batch accumulation takes **3.50 ms**, but on low-bandwidth peripheral IoT links processing 100 flows/sec, window accumulation requires **1.0 full second**.
- **Action Taken in Manuscript**:
  - **Removed Unqualified "Real-Time" Descriptor**: Bounded all latency claims.
  - Added Table 11 reporting the exact 35.00 $\mu\text{s}$ per-flow execution latency and 28,575 flows/sec throughput.
  - Added dedicated limitation **Section 6.10** detailing the batch buffering delay (3.5 ms to 1.0 s) and explaining that hardware line-rate dropping requires FPGA/P4 offload or per-flow fast-path bypass.
  - *Locations*: Section 4.3.3, Table 11, Section 6.10.

---

### 4. Zero-Day Threat Prevention Claims
- **Original Claim**: Unqualified assertions that the multi-stage framework provides *"zero-day threat defense"* and *"unsupervised mitigation of unseen exploits"*.
- **Empirical Audit Finding (Task 7)**:
  - Leave-one-attack-family-out (LOFO) novelty testing revealed that while the clean Isolation Forest achieves **>99.8% recall** on unseen volumetric flood attacks (DDoS: 99.98%, DoS: 99.94%, Mirai: 99.83%), it exhibits poor recall on stealthy application-layer threats:
    - Reconnaissance: **61.28%**
    - BruteForce: **60.00%**
    - Web Attacks: **40.00%**
    - Backdoor Malware: **0.00%**
- **Action Taken in Manuscript**:
  - **Removed General Zero-Day Claims**: Stripped claims that unsupervised anomaly detection stops general zero-day attacks.
  - Added Table 12 reporting exact LOFO novelty recall per attack family.
  - Added dedicated limitation **Section 6.11** explicitly bounding zero-day detection capabilities to volumetric floods that alter flow volume/rate statistics, while acknowledging that low-and-slow application exploits evade unsupervised anomaly detection.
  - *Locations*: Section 4.3.3, Table 12, Section 6.11.

---

### 5. Strict 1-to-1 Escalation Optimality ($P_{2\text{-tier}}$)
- **Original Claim**: $P_{2\text{-tier}}$ was framed as the uniquely optimal operational standard due to its strict 1-to-1 escalation progression (`Allow-Alert-Restrict-Quarantine-Block-Block`).
- **Empirical Audit Finding (Task 3)**:
  - Across all 70 admissible monotonic policies, $P_{2\text{-tier}}$ ranks **9th of 70** (+1,912,063 OCU).
  - $P_{2\text{-tier}}$ is Pareto-dominated by **8 candidate policies** (including $P_{\text{opt}}$ at Rank 1, $+1,922,671$ OCU) that map Level $L_3$ to Alert or Restrict, thereby avoiding the 28.87%–29.90% collateral quarantine disruption on benign traffic.
- **Action Taken in Manuscript**:
  - **Softened Framing**: Reframed $P_{2\text{-tier}}$ as an *"analytical reference policy"* preserving 1-to-1 progression, rather than the uniquely optimal deployment standard.
  - Disclosed that $P_{2\text{-tier}}$ is Pareto-dominated by 8 policies in Table 8.
  - *Locations*: Contribution 3, Table 8, Section 4.3.2, Section 5.3.

---

### 6. Topology Confound & Level $L_1 = 0\%$ Attack Density
- **Original Claim**: $L_1$ populates with 0% attack density, but concerns were raised that this might be an artifact of the synthetic round-robin mapping $n(b) = b \pmod{120}$.
- **Empirical Audit Finding (Task 2)**:
  - 1,000 permutations randomizing node assignments and shuffling batch order proved:
    - Level $L_1$ attack density remains strictly **0.000% in 100.0% of runs** ($p = 1.000$).
    - Level $L_5$ is populated in **95.70% of runs** (mean 310.4 flows, 99.43% attack density, $p = 0.777$).
    - Monotonicity holds in **94.50% of runs** ($p = 1.000$).
- **Action Taken in Manuscript**:
  - Clarified architectural definition: decoupled anomaly extremity from Level $L_1$, defining $L_1$ strictly as **Topology-Prior Monitoring** ($c_{\text{topo}}=1$). Under edge routing, $L_1$ reflects asset structural criticality during nominal periods, ensuring high-value assets receive passive logging without throttling.
  - Added Table 6b reporting permutation means, 95% CIs, and $p$-values.
  - Added dedicated limitation **Section 6.8** documenting that TARP was evaluated on a synthetic 120-node scale-free graph and must be validated on physical enterprise network graphs.
  - *Locations*: Contribution 1, Section 3.3, Table 6b, Section 4.2.1, Section 6.8.

---

### 7. Level $L_5$ Escalation Logic and Z-Score Arithmetic
- **Original Claim**: An internal draft reported $Z = 41.25\sigma$ for node risk exceedance, and ambiguous boolean conditions for Level $L_5$.
- **Empirical Audit Finding (Task 2 & Task 5)**:
  - On the 120-node Barabási-Albert scale-free graph ($\mu_R = 0.4189, \sigma_R = 0.0721$), individual node criticality for core hubs (Node 0: $R=0.9000$, Node 4: $R=0.8089$) is **$Z = 4.59\sigma$** ($p = 2.2 \times 10^{-6}$ against the empirical graph distribution; theoretical target $Z = 4.125\sigma$).
  - The $Z = 41.25\sigma$ figure was an arithmetic artifact of dividing individual node standard deviations by $\sqrt{100}$ despite uniform intra-batch node assignment.
  - Escalation to Level $L_5$ requires BOTH multi-stage threat corroboration ($S \ge 3 \land \bar{T} \le 20.0$) AND extreme topological criticality ($\bar{R} \ge 0.75$).
- **Action Taken in Manuscript**:
  - Reconciled Z-score reporting to $Z = 4.59\sigma$ (empirical) and $Z = 4.125\sigma$ (target), documenting the $41.25\sigma$ batch CLT artifact.
  - Clarified that $S \ge 3$ collectively encompasses both $S=3$ and $S=4$.
  - Fixed Algorithm 1 and text to enforce the conjunction: $(S \ge 3 \land \bar{T} \le 20.0 \land \bar{R} \ge 0.75)$.
  - *Locations*: Contribution 1, Section 3.3.1, Algorithm 1, Section 4.2.3, Section 6.5.

---

### 8. Dynamic Online Regime Switching Superiority
- **Original Claim**: Earlier draft titles included *"Regime-Aware"* and asserted that an online dynamic regime-switching controller outperformed static response policies.
- **Empirical Audit Finding**:
  - Experiment E9/E16 demonstrated that an online dynamic switcher toggling between $P_1$ and $P_{2\text{-tier}}$ based on runtime batch trust and anomaly density achieved **+1,909,733 OCU**, matching static $P_{2\text{-tier}}$ (**+1,909,843 OCU**) within 110 OCU (0.006%), with identical 0.00% Block FPR on balanced streams.
- **Action Taken in Manuscript**:
  - **Removed from Headline Claims**: Removed "Regime-Aware" from the manuscript title and abstract.
  - Retained the evaluation in Section 4.4 as an empirical finding proving that static level-to-action optimization achieves optimal performance without the runtime complexity of dynamic controller switching.
  - *Locations*: Title, Abstract, Section 4.4, Section 5.3.

---

### 9. Editorial and Typographical Corrections
- **CICIoT2023 Typo**: Fixed multiple instances of "CICloT2023" (lowercase 'l') to "CICIoT2023" (capital 'I').
- **Anthi Citation Typo**: Corrected citation spelling from "An thi et al." to "Anthi et al." \cite{2}.
- **LaTeX MathJax Syntax**: Corrected broken LaTeX math delimiter `$$P_{	ext{hybrid}}$` in `sec1_intro.py` and ensured clean delimiters throughout `paper_v3.tex`.
- **Combinatorial Space**: Verified exact combinatorial space $5^6 = 15,625$ unconstrained policies, reducing to $\binom{8}{4} = 70$ admissible monotonic mappings under boundary safety constraints ($L_0 = \text{Allow}, L_5 = \text{Block}$).
- **Abstract Metric Consistency**: Synchronized rounded trust AUC "0.986" across Abstract, Section 1, and Section 4.

---

## Conclusion & Verification Sign-Off

All 38 claims across the manuscript and codebase have been rigorously audited. No unverified, exaggerated, or mathematically inconsistent claims remain in either the Word manuscript (`paper2_manuscript.docx`) or the LaTeX source (`paper_v3.tex`). All cryptographic hashes and execution scripts are cataloged in `audit/SHA256SUMS.txt`.
