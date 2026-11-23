# Systematic Audit & Editorial Checklist: Claims Removed, Softened, or Reconciled

**Audit Suite**: E1 through E11  
**Manuscript**: Six-Level Security Posture Escalation with Training-Data Contamination Repair and Cost-Aware Response Optimization for IoT Intrusion Detection  
**Target Submission**: IEEE Transactions on Information Forensics and Security / IEEE Internet of Things Journal  
**Date**: 2026-11-18  

---

## 1. Summary of Editorial Directives & Audit Reconciliation

This document provides a complete, item-by-item accounting of every claim that was **removed**, **softened**, or **empirically reconciled** during the final editorial pass across the manuscript (`draft/paper2_manuscript.docx` and associated sections `sec1_intro.py` through `sec8_appendix.py`). In accordance with strict academic integrity standards, **no claim is retained that is not directly verified and backed by an experimental artifact in `audit_v3/`**.

---

## 2. Itemized Checklist of Reconciled, Softened, and Removed Claims

### Item 1: MDPI Baseline Reconciliation (Experiments E1 & E2)
- **Previous Status in Literature**: Foundational study [1] (*J. Cybersecur. Priv.* 6(5), 181) reported dynamic trust AUC of 0.7843, 94.25% High Trust trapping, 97.16% attack rate in High Trust, and policy inaction (Alert 90.92%, Quarantine 9.08%, Allow/Restrict/Block 0.00%).
- **Audit Findings**: E1 replicated the exact negative phenomena (94.26% High Trust trapping, 97.38% attack rate in High Trust, Alert 90.92%, Quarantine 9.08%, 0% Block). E2 traced this to two distinct implementation defects:
  1. *Defect A (Label Mismatch)*: `unknown_attack_detector.py` checked `'BENIGN'`, while CICIoT2023 labels benign flows as `'BenignTraffic'`. This caused the Isolation Forest to train on uncurated telemetry with 97.64% attack contamination, producing an inverted raw AUC of 0.0084.
  2. *Defect B (Trust Leakage)*: `trust_manager.py` initialized entity priors using empirical attack family identifiers (`p_benign_map`) and passed ground-truth `is_attack` at runtime.
- **Editorial Action Taken**: 
  - Added dedicated Section 1.4: *"Reconciliation with MDPI J. Cybersecur. Priv. 6(5), 181"* documenting exact replication and code-level root cause tracing.
  - Reconciled Table 1 comparing the MDPI baseline against the repaired pipeline.

---

### Item 2: Barabási-Albert Network Topology Reconciliation (Experiment E3)
- **Previous Claim**: Z-score for topological risk was variously reported as $Z = 4.59$, $Z = 4.125$, and $Z = 41.25$; standard deviation reported as $\sigma = 0.0721$ vs. $\sigma = 0.0800$; $p$-values reported as $2.2 \times 10^{-6}$ vs. $4.4 \times 10^{-6}$ vs. $10^{-15}$.
- **Audit Findings**:
  - Foundational MDPI graph used $m=3$ attachment ($N=120, E=342, \bar{k}=5.70$).
  - Proposed model uses $m=2$ attachment ($N=120, E=236, \bar{k}=3.93$).
  - Empirical PageRank standard deviation is $\sigma_R = 0.0721$, derived from the target theoretical distribution $\mathcal{N}(0.42, 0.08)$.
  - Individual node criticality for Node 0 ($R = 0.9000$) is $Z = 4.5931\sigma$ (1-tailed $p = 2.18 \times 10^{-6}$, 2-tailed $p = 4.37 \times 10^{-6}$) on the empirical graph distribution, and $Z = 4.1250\sigma$ ($p = 1.85 \times 10^{-5}$) under theoretical target parameters.
  - The erroneous $Z = 41.25\sigma$ in previous drafts was an arithmetic error (dividing by $\sqrt{100}$).
- **Editorial Action Taken**:
  - **Removed**: Completely deleted erroneous $Z = 41.25\sigma$ and $p < 10^{-15}$ topology claims.
  - **Standardized**: Clearly labeled empirical realized values ($\sigma_R = 0.0721, Z = 4.5931\sigma$, 1-tailed $p = 2.18 \times 10^{-6}$, 2-tailed $p = 4.37 \times 10^{-6}$) and theoretical target values ($\sigma = 0.0800, Z = 4.1250\sigma, p = 1.85 \times 10^{-5}$).
  - **Added**: Added topology comparison table (`tables/tab_topo_comparison.csv`) in Section 2.5 and Appendix B.

---

### Item 3: Level L5 Attack Enrichment and Containment Framing (Experiment E4)
- **Previous Claim**: Level $L_5$ was characterized as an active attack containment tier providing incremental attack-density enrichment beyond Level $L_4$.
- **Audit Findings**:
  - In balanced nominal traffic, Level $L_5$ contains 0 flows (unpopulated on edge gateway streams where $\bar{R} < 0.75$).
  - In attack-heavy traffic, Level $L_5$ captures 99.43% attack density, which is identical to Level $L_4$ (which captures 97.6%–100% attack density).
  - Permutation testing (1,000 runs) confirms $L_5$ does not enrich attack density over $L_4$.
- **Editorial Action Taken**:
  - **Removed**: Deleted all claims that $L_5$ provides incremental "attack enrichment" or "containment capacity" over $L_4$.
  - **Re-framed**: Redefined $L_5$ strictly as a specialized topological priority circuit-breaker for core backbone hubs ($R \ge 0.75$) under coordinated assault, dormant on edge gateways to prevent catastrophic disconnection.

---

### Item 4: Hybrid Policy ($P_{\text{hybrid}}$) Performance & Dominance Framing (Experiment E5)
- **Previous Claim**: $P_{\text{hybrid}}$ was claimed to "strictly dominate" all policies, including confidence-gated XGBoost ($P_{\text{XGB}}$), across all operational metrics.
- **Audit Findings**:
  - On stationary closed-world balanced benchmarks, pure confidence-gated XGBoost ($P_{\text{XGB}}$) achieves $+1,472,830 \pm 4,194$ OCU, significantly outperforming $P_{\text{hybrid}}$ ($+1,391,654 \pm 7,984$ OCU, paired difference $+81,176$ OCU, Wilcoxon $p = 0.002$).
  - On unstratified traffic, $P_{\text{XGB}}$ also outperforms $P_{\text{hybrid}}$ ($+1,472,830$ vs. $+1,326,419$ OCU, difference $+146,411$ OCU, $p = 0.002$).
  - $P_{\text{hybrid}}$ significantly outperforms $P_{\text{XGB}}$ on volumetric flood saturation ($+2,974,176$ vs. $+2,960,105$ OCU, difference $+14,071$ OCU, $p = 0.002$) and sustained attack-heavy traffic ($+2,896,961$ vs. $+2,891,120$ OCU, difference $+5,841$ OCU, $p = 0.002$).
  - In LOFO novel attack evaluation, posture policies beat $P_{\text{XGB}}$ in 7 of 7 folds on net OCU.
- **Editorial Action Taken**:
  - **Removed**: Removed all claims of unqualified or universal "dominance" for $P_{\text{hybrid}}$.
  - **Softened / Re-framed**: Formulated a rigorous **conditional decision rule**:
    - *Closed-world, stationary environments with known attack signatures*: $P_{\text{XGB}}$ is mathematically superior in net OCU.
    - *Open-world, adversarial environments requiring auditability, multi-tier escalation, and zero-day defense*: $P_{\text{hybrid}}$ is recommended conditionally.

---

### Item 5: Regime-Shift Defense-in-Depth vs. Zero-Day Generalization (Experiment E6)
- **Previous Claim 5A**: Multi-stage posture escalation provides "defense-in-depth against regime shift" under degraded or unstratified traffic.
- **Previous Claim 5B**: Multi-stage posture escalation provides zero-day novel attack containment.
- **Audit Findings**:
  - *Regime Shift (Refuted)*: $P_{\text{hybrid}}$ advantage over $P_{\text{XGB}}$ collapses monotonically as batch homogeneity degrades: $+14\text{k}$ (flood) $\to +5.8\text{k}$ (attack-heavy) $\to -81\text{k}$ (balanced) $\to -146\text{k}$ (unstratified shuffle). Benign flows co-located within sliding windows suffer collateral quarantine (Quarantine FPR escalates from 9.37% to 20.29%).
  - *Zero-Day Novel Attacks (Empirically Validated)*: LOFO cross-validation across all 7 top-level attack families (DDoS, DoS, Mirai, Recon, Web, Spoofing, BruteForce) confirmed that posture beats $P_{\text{XGB}}$ in **7 of 7 folds**. For Mirai botnets, $P_{\text{XGB}}$ recall collapsed to 0.33% (+850 OCU), while posture achieved 27.42% containment recall (+178,713 OCU, a 210-fold increase).
- **Editorial Action Taken**:
  - **Removed**: Completely deleted the claim that posture provides "defense-in-depth against regime shift." Documented sliding-window vulnerability under unstratified traffic as an explicit architectural limitation in Section 6.7 and 6.12.
  - **Retained**: Fully retained and highlighted the **zero-day defense-in-depth claim**, supported by complete LOFO empirical tables.

---

### Item 6: Anomaly Calibration Data Leakage Decoupling (Experiment E7)
- **Previous Status**: Anomaly score quantiles ($q_{0.05}, q_{0.95}$) were computed on validation telemetry, creating potential data leakage into policy optimization.
- **Audit Findings**: An independent partition of 20,000 verified clean benign flows ($D_{\text{calib}}$) was evaluated. The clean quantiles ($q_{0.05} = 0.4404, q_{0.95} = 0.5586$) yielded Spearman rank correlation $\rho_s = 0.999405$ ($p = 3.51 \times 10^{-101}$) with zero rank inversions across all 70 monotonic policies.
- **Editorial Action Taken**:
  - Replaced quantile definitions in Section 3.2 and Section 4.1 with clean $D_{\text{calib}}$ values.
  - Stated complete policy ranking invariance under decoupled calibration.

---

### Item 7: Exhaustive 70-Policy Combinatorial Evaluation (Experiment E8)
- **Previous Status**: Earlier drafts reported isolated, single-seed numbers for $P_{\text{opt}}$, $P_{2\text{-tier}}$, and $P_1$, with discrepancies across sections (e.g. 1.92M vs 1.44M; 1.91M vs 1.40M).
- **Audit Findings**: Evaluated all 70 admissible monotonic policies across 50 streams (5 operational regimes $\times$ 10 random seeds = 3,000,000 flows total):
  - $P_{\text{opt}}$: $D_{\text{test}}$ Seed 99 = $+1,439,948$ OCU; 50-run overall mean = $+2,052,438.1$ OCU (Rank 1 of 70).
  - $P_{2\text{-tier}}$: $D_{\text{test}}$ Seed 99 = $+1,404,974$ OCU; 50-run overall mean = $+2,027,331.5$ OCU (Rank 9 of 70). On baseline multi-state split, $+1,909,843$ OCU (2.43x over $P_1$).
  - $P_1$: $D_{\text{test}}$ Seed 99 = $+786,643$ OCU; 50-run overall mean = $+1,184,210.4$ OCU (Rank 44 of 70).
  - Boundary constraint space: $\binom{5+4-1}{4} = \binom{8}{4} = 70$ admissible monotonic mappings out of $5^6 = 15,625$ unconstrained combinations.
- **Editorial Action Taken**:
  - Replaced all outdated policy numbers in Table 1, Table 8, Table 8b, and Section 4.3 with exact E8 artifact numbers.
  - Fully cited $D_{\text{test}}$ Seed 99 and 50-run overall means with standard deviations and 95% CIs.

---

### Item 8: Throughput, Latency, and "Real-Time" Qualification (Experiment E9)
- **Previous Claim**: The multi-stage pipeline was described as operating in "real-time" without operational qualification.
- **Audit Findings**:
  - End-to-end pipeline throughput: 18,244.3 flows/sec ($54.81 \ \mu\text{s}$ per flow amortized) under micro-windows of $B = 1024$.
  - Standalone single-flow GPU inference ($B=1$) consumes median latency of $2,499.7 \ \mu\text{s}$ ($2.5 \ \text{ms}$) due to CUDA kernel launch overhead, meaning standalone GPU inference cannot operate at line rate without micro-batching ($B \ge 256$).
  - Microscopic benign veto executes in $0.177 \ \mu\text{s}$ ($177 \ \text{ns}$).
  - Causal ADTM update executes in $0.86 \ \mu\text{s}$ ($1.15\text{M}$ updates/sec).
- **Editorial Action Taken**:
  - **Removed / Softened**: Removed unqualified "real-time" claims.
  - **Qualified**: Stated: *"sub-millisecond line-rate processing (>18,000 flows/sec) under batched micro-windows ($B \ge 256$),"* and explicitly documented single-flow GPU latency (2.5 ms) and buffering delay (1.0 s at 100 flows/sec) in Section 6.10.

---

### Item 9: False-Positive Rate (FPR) Terminology & Flood FPR (Experiment E10)
- **Previous Claim**: Flood Block FPR was reported as 34.66% vs. 38.89%; unqualified "near-zero FPR" was used without distinguishing attention from enforcement.
- **Audit Findings**:
  - In pure volumetric flood saturation, 100% of flows are malicious ($N_{\text{benign}} = 0$). By mathematical definition, $\text{Block FPR} = 0/0 = \text{N/A}$.
  - Across mixed operational regimes, $P_{\text{hybrid}}$ maintains Block FPR of 0.72% on balanced and 1.10% on unstratified streams.
  - Attention FPR (Alert + Restrict) must be strictly decoupled from Enforcement FPR (Quarantine + Block).
- **Editorial Action Taken**:
  - **Removed**: Deleted conflicting 34.66% and 38.89% flood Block FPR numbers. Marked pure flood Block FPR as strictly N/A ($0/0$).
  - **Clarified**: Replaced with exact mixed-stream Block FPR: 0.72% (balanced) and 1.10% (unstratified).
  - Enforced strict terminology distinguishing passive monitoring overhead from disruptive containment.

---

### Item 10: Cryptographic Reproducibility Package (Experiment E11)
- **Previous Status**: General claims of open-source reproducibility without cryptographic manifest.
- **Audit Findings**: E11 generated an authoritative reproducibility package containing:
  - Exact seed catalog: `42` (train/split), `99` (evaluation hold-out), `2024` (baseline IF), and 10-seed ensemble `[13, 42, 99, 123, 2024, 7, 77, 101, 2023, 31415]`.
  - 56 cryptographic SHA-256 hashes of all scripts, models, configurations, and CSV outputs archived in `audit_v3/E11_reproducibility/MANIFEST.sha256`.
  - Self-contained replication tarball `audit_v3/E11_reproducibility/artifact.tar.gz`.
- **Editorial Action Taken**:
  - Updated Section 1.4, Section 7, and Appendix A with explicit pointers to `MANIFEST.sha256` and the replication package.

---

### Item 11: Notation, Typography, and Minor Fixes
- **Editorial Corrections**:
  - Corrected all occurrences of "CICloT" to "CICIoT2023".
  - Verified trust inequality directions: $T \le 60.0 \implies \text{degradation}$; $T \ge 80.0 \implies \text{High}$.
  - Total combinatorial space corrected to $5^6 = 15,625$ mappings.
  - Corrected $P_{\text{opt}}$ mapping: Level $L_1 \to \text{Allow}$, Level $L_3 \to \text{Restrict}$, achieving 0.00% Quarantine FPR (marked N/A).
  - Removed "uniquely preserving 1-to-1" phrase in Section 6.2; rephrased to "enforcing canonical 1-to-1 action tiering".

---

## 3. Verification Sign-off Table

| Audit Area | Pre-Audit Claim | Verified Artifact Ground Truth | Editorial Resolution | Status |
| :--- | :--- | :--- | :--- | :---: |
| **E1: MDPI Baseline** | Negative results assumed anecdotal | Exact reproduction: 94.26% High Trust, 97.38% attack in High Trust, 0% Block | Added Section 1.4 reconciliation | **RESOLVED** |
| **E2: Defect Trace** | Suspected model under-capacity | Lexical label mismatch (`BENIGN` vs `BenignTraffic`) & prior leakage | Documented exact file and line trace | **RESOLVED** |
| **E3: Topology** | $Z = 41.25\sigma, \sigma = 0.08$ | BA($m=2$): $\sigma_R = 0.0721, Z = 4.5931\sigma$ ($p = 2.18\times 10^{-6}$) | Removed $Z=41.25$; added Table 2.5 | **RESOLVED** |
| **E4: Posture / L5** | $L_5$ enriches attack containment | $L_5$ is dormant on edge (0 flows) and provides hub prioritization (99.43% atk) | Removed enrichment; defined as hub barrier | **RESOLVED** |
| **E5: $P_{\text{hybrid}}$** | $P_{\text{hybrid}}$ universally dominates | $P_{\text{XGB}}$ wins balanced (+81k); $P_{\text{hybrid}}$ wins flood (+14k) & LOFO | Formulated conditional recommendation | **RESOLVED** |
| **E6: Shift & Zero-Day** | Posture provides regime defense | Monotonic collapse under shuffle (-146k); wins 7/7 on novel zero-day attacks | Removed regime defense; retained zero-day | **RESOLVED** |
| **E7: Calibration** | Validation split leakage | $D_{\text{calib}}$ (20k clean benign): $q_{0.05}=0.4404, q_{0.95}=0.5586, \rho_s=0.9994$ | Updated quantiles; rank invariant | **RESOLVED** |
| **E8: Cost Sweep** | 1.92M / 1.91M single-seed | $P_{\text{opt}}$: 1,439,948 test / 2,052,438 mean; $P_{2\text{-tier}}$: 1,404,974 test | Updated Table 1, 8, 8b with 50-run means | **RESOLVED** |
| **E9: Latency** | Unqualified "real-time" | 18,244 flows/sec ($54.8 \ \mu\text{s}$/flow); GPU single-flow 2.5 ms | Qualified to micro-batched line-rate | **RESOLVED** |
| **E10: Consistency** | 18 numeric discrepancies | Consistency ledger reconciling all 18 claims | All 18 items corrected in manuscript | **RESOLVED** |
| **E11: Reproducibility** | General claims | 56 SHA-256 hashes, seed catalog, tarball | MANIFEST.sha256 and README.md linked | **RESOLVED** |
