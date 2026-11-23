# Senior Reproducibility Engineer & ML Reviewer Final Report
**Manuscript**: *Regime-Aware Multi-Stage Intrusion Response and Posture Escalation in IoT Networks: An Empirical Study on CICIoT2023*  
**Date**: November 11, 2026  
**Auditor / Reproducibility Engineer**: Senior Verification Agent  
**Source of Truth Configuration**: `configs/paper.yaml`  
**Compiled Artifacts**:
- Word Document: [`paper2_manuscript.docx`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/draft/paper2_manuscript.docx) (26 pages)
- Exported PDF: [`paper2_manuscript.pdf`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/draft/paper2_manuscript.pdf) (26 pages)
- Audit Report: [`audit_report.md`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/audit_report.md)
- Changelog: [`CHANGELOG.md`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/CHANGELOG.md)
- Isolated Package: [`paper2/clean_experiments_isolated/`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/clean_experiments_isolated/) (70 SHA-256 verified files)

---

## 1. Executive Summary & Verification Verdict

The manuscript and experimental pipeline have undergone a complete, rigorous, and end-to-end technical reconstruction. Every discrepancy, unverified number, and algorithmic inconsistency identified in prior reviewer reports has been resolved, re-derived from first principles, and empirically tested without data fabrication.

### Core Audit & Remediation Outcomes
1. **Single Source of Truth (`configs/paper.yaml`)**:
   All dataset dimensions, random seeds, anomaly calibration percentiles, ADTM weights, hard-reset conditions, TARP topology parameters, and decision-theoretic OCU values are centralized in a single configuration file.
2. **Arithmetic Correction Verified**:
   The hand derivation of the benign penalty for policy P2 on the balanced window was verified:
   $$\text{Penalty}_{\text{benign}} = 10,300(3) + 2,948(15) + 8,934(50) = 30,900 + 44,220 + 446,700 = \mathbf{521,820\text{ OCU}}.$$
   The legacy typo in earlier drafts reporting `252,982 OCU` has been corrected in both text and tables. The net benefit remains verified at:
   $$\text{Net Benefit} = +1,429,340 - 521,820 = \mathbf{+907,520\text{ OCU}}.$$
3. **Dual-Window False-Positive Blocking Transparency**:
   The paper now transparently reports Block FPR across both evaluation regimes:
   - **Balanced Multi-State Stream**: P2-tier achieves **0.00% Block FPR** ($0 / 29,882$), at the cost of **29.90% benign Quarantine FPR** ($8,934 / 29,882$). Total disruptive FPR is $29.90\%$.
   - **Attack-Heavy Surge Stream**: P2-tier achieves **100.00% Block FPR** ($1,440 / 1,440$), because all 60,000 flows collapse into Level $L_4$. Conservative policy P1 achieves **0.00% Block FPR** but incurs **100.00% Quarantine FPR** ($1,440 / 1,440$) while forfeiting 1,706,400 OCU in threat containment value. The paper explicitly presents this Pareto trade-off.
4. **Regime-Aware Dynamic Switching (§4.4 / E9)**:
   The title is retained with *"Regime-Aware"*, supported by the addition of Section 4.4 presenting an online adaptive controller:
   $$\pi_b = \begin{cases} P_{2\text{-tier}}, & \text{if } \bar{T}_b \le 40.0 \land \bar{s}_b \ge 0.50 \quad (\text{Acute Attack Regime}) \\ P_1, & \text{otherwise} \quad (\text{Nominal / Mixed Regime}) \end{cases}$$
   The dynamic controller matches the full $+1,909,733\text{ OCU}$ combined net benefit of static $P_{2\text{-tier}}$ while maintaining strictly 0.00% Block FPR on balanced traffic.
5. **Table Renumbering in Sequential Order (Tables 1 to 10)**:
   The Decision-Theoretic Cost Matrix (formerly Table 10) was moved to Section 3.4 as **Table 2**. All subsequent experimental tables were renumbered sequentially from 3 to 10 in exact order of appearance. Table 8 includes explicit Quarantine FPR and Disruptive FPR columns, and Table 9 percentages sum to exactly 100.0%.
6. **Figure 5 Dual-Panel Side-by-Side Visualization**:
   `generate_all_clean_figures.py` regenerated Figure 5 (`fig4_two_window_distribution.png`) as a dual-panel figure at 300 DPI showing both (a) Sustained Attack-Heavy and (b) Stratified Multi-State stream posture distributions.
7. **Phase 1 Critical Experiments (E1 to E12)**:
   All 12 experimental scripts were executed under `experiments/`, with raw outputs logged in `experiments/outputs/`. All 12 passed.
8. **Manuscript Assembly & Quality Verification**:
   The manuscript was compiled via `assemble_manuscript.py`. All 16 quality verification checks passed. The final page count in Word COM (`doc.ComputeStatistics(2)`) is **26 pages**, safely within the 30-page journal limit.

---

## 2. Phase 0 Audit Summary (`audit_report.md`)

| Section | Focus Area | Finding & Resolution |
|---|---|---|
| **0.1 Config Extraction** | Numeric Constants & Thresholds | Verified all 24 numerical parameters against codebase. Unified hard-reset thresholds to $c_{\text{conf}} \ge 0.90, \hat{y} \ne \text{benign}, \tilde{s} \ge 0.50 \implies T \leftarrow 10.0$. Standardized training attack percentage to 97.64%. |
| **0.2 Artifact Provenance** | Tables 1–10 & Figures 1–10 | Re-linked each table to its generating script and CSV. Reconciled figure captions with exact table metrics. |
| **0.3 Arithmetic Re-Derivation** | Decision Costs & FPRs | Step-by-step verification of P1, P2-tier, and P2 on both evaluation streams. Diagnosed and fixed the 252,982 OCU typo. |
| **0.4 Algorithm Correctness** | Algorithms 1, 2, 3 & Score Negation | Harmonized Algorithm 1 condition indicators to window proportions $\ge 0.50$. Confirmed Algorithm 3 argmax over net benefit is exact cost minimization dual. Validated Isolation Forest score negation (`-score_samples`). |
| **0.5 Citation Audit** | Problematic Reference Keys | Replaced Anthi et al. [2] for CICIDS2017 with Sharafaldin et al. [39]. Replaced Jyothsna et al. [31] for TON_IoT with Alsaedi et al. [40]. Replaced "Noel & Jajodia [12]" with Wang et al. [12]. Added NIST FIPS PUB 199 [41] to bibliography. Corrected NIST SP 800-207 [7] attribution. Anonymized Reference [1] for double-blind compliance. |
| **0.6 Data Reconciliation** | Empirical Discrepancies | Reconciled 7 missing flows in Table 8. Corrected Web trust score from 35.84 to 16.03. Corrected non-Allow allocation to 44.40%. Corrected Level 3 flow volume to 18,500 flows (30.83%). Corrected policy sweep space to 70 candidates. |

---

## 3. Phase 1 Critical Experiments (E1 to E12)

| Tag | Experiment Title | Script | Status | Key Quantitative Result |
|---|---|---|---|---|
| **E1** | Multi-Seed Stability Suite | `experiments/E1_multiseed_stability.py` | PASSED | 5 seeds: Clean IF AUC = $0.9380 \pm 0.0087$; Trust AUC = $0.9990 \pm 0.0001$; P2-tier Combined Net = $+1,909,278 \pm 1,127\text{ OCU}$. |
| **E2** | Held-Out Balanced Test Window | `experiments/E2_held_out_balanced.py` | PASSED | Seed 99: P1 Block FPR = $0.00\%$; P2-tier Block FPR = $0.12\%$; P2-tier Net = $+959,388\text{ OCU}$ (Balanced), $+1,907,694\text{ OCU}$ (Combined). |
| **E3** | Full Disruptive FPR Audit | `experiments/E3_full_disruption_fpr.py` | PASSED | Evaluated all 70 policies. P1 and P2-tier both exhibit 29.90% Quarantine FPR on balanced, and 100.0% disruptive action on attack-heavy. |
| **E4** | ADTM Weight Sensitivity | `experiments/E4_adtm_weight_sensitivity.py` | PASSED | Swept 7 weight allocations (Class-heavy, Anomaly-heavy, Topo-heavy, Uniform, Extreme). Trust AUC remained $0.9985 - 0.9993$. |
| **E5** | Threshold Sensitivity Analysis | `experiments/E5_threshold_sensitivity.py` | PASSED | Swept $\tau_{\text{anom}} \in [0.4, 0.6]$, $\tau_T \in [50, 70]$, $\tau_{\text{conf}} \in [0.85, 0.95]$, $\tau_{\text{topo}} \in [0.35, 0.50]$. Posture monotonicity preserved across all sweeps. |
| **E6** | Extended Cost Sensitivity Sweep | `experiments/E6_extended_cost_sensitivity.py` | PASSED | Swept Block penalty multiplier $\lambda \in [0.2, 20.0]$ (10 to 1,000 OCU). P2-tier maintains $\ge 1.56\times$ advantage over P1 across entire range. |
| **E7** | Regime Mixture Weight Sensitivity | `experiments/E7_regime_weight_sensitivity.py` | PASSED | Swept $w_{\text{bal}} \in [0.0, 1.0]$. P2-tier consistently ranks 9th of 70 for $w_{\text{bal}} \in [0.1, 1.0]$, while P1 consistently ranks 44th. |
| **E8** | Level L5 Population Test & Proof | `experiments/E8_l5_population_test.py` | PASSED | Proved analytically and empirically ($100,000$ batches) that batch mean risk never reaches $\tau_R=0.75$ ($Z = 41.25\sigma$). Formally established Level $L_5$ as an architectural extension for core backbone SDN hubs. |
| **E9** | Minimal Regime-Aware Switcher | `experiments/E9_regime_aware_switcher.py` | PASSED | Online detector switching between P1 and P2-tier based on batch anomaly rate and trust achieves $+1,909,733\text{ OCU}$ combined with 0.00% Block FPR on balanced traffic. |
| **E10** | TARP Topology Reproducibility | `experiments/E10_tarp_reproducibility.py` | PASSED | Generated Barabasi-Albert ($m=2$) scale-free graph (120 nodes, 236 edges), computed PageRank ($\alpha=0.85$), verified risk distribution $\mu=0.4200, \sigma=0.0800$. |
| **E11** | Wilson Score 95% CI Verification | `experiments/E11_wilson_ci.py` | PASSED | Recomputed exact closed-form Wilson intervals for all active levels in Tables 5 and 6 using `scipy.stats.norm.ppf`. |
| **E12** | Score Samples Sign Unit Test | `experiments/E12_score_sign_test.py` | PASSED | Fast automated test: verified $- \text{score\_samples}$ has Pearson $r = +0.7794$ with attack labels and AUC = $0.9505$. |

---

## 4. Phase 2 Sequential Table Structure

| Revised Table | Content / Description | Placement |
|---|---|---|
| **Table 1** | Architectural and quantitative progression comparison between baseline [1] and proposed framework | Section 2.8 |
| **Table 2** | Formal decision-theoretic cost matrix $\mathcal{L}(a, y)$ in OCU across response actions *(formerly Table 10)* | Section 3.4 |
| **Table 3** | Controlled quantitative comparison of Isolation Forest before/after contamination repair ($M=100, 200$) | Section 4.1.1 |
| **Table 4** | Dynamic trust band distribution across 5 progressive neutral calibration configurations ($C_0^*$ to $C_4^*$) | Section 4.1.2 |
| **Table 5** | Six-level security posture distribution on sustained volumetric attack-heavy stream (60,000 flows) | Section 4.2.1 |
| **Table 6** | Six-level security posture distribution on stratified multi-state benchmark stream (60,000 flows) | Section 4.2.2 |
| **Table 7** | Action-level precision audit across enforcement tiers on multi-state benchmark stream | Section 4.3.1 |
| **Table 8** | Master policy performance comparison across candidate architectures in OCU *(with corrected 521,820 OCU and FPR columns)* | Section 4.3.2 |
| **Table 9** | Per-family flow counts, action distribution, and dynamic trust across seven threat families *(100.0% row sum)* | Section 4.3.3 |
| **Table 10** | Cost sensitivity analysis across false-blocking scaling factors $\lambda \in [0.2, 5.0]$ | Section 4.3.4 |

---

## 5. Quality Verification Report (16 / 16 Checks Passed)

```
================================================================================
QUALITY VERIFICATION REPORT:
================================================================================
PASS [✓]   | Check 1: Tables 1-10 cited in text                 | All 10 tables cited
PASS [✓]   | Check 2: Figures 1-10 cited in text                | All 10 figures cited
PASS [✓]   | Check 3: All 41 references cited in text           | All 41 references cited
PASS [✓]   | Check 4: Every [n] in text exists in reference list | No orphan citations
PASS [✓]   | Check 5: No claim of 'P1 is optimal'               | PASSED: P1 correctly documented as suboptimal baseline
PASS [✓]   | Check 6: No false claim of per-family action specialization | PASSED: Documented as limitation (does not emerge at current thresholds)
PASS [✓]   | Check 7: No unqualified 'near-zero FPR' claim      | PASSED: Attention FPR and Enforcement FPR rigorously distinguished
PASS [✓]   | Check 8: No operational 'real-time' or 'low-latency' claims | PASSED: Offline batch evaluation bounds explicitly stated in Sec 6.7
PASS [✓]   | Check 9: IF contamination code excerpt present in Sec 3.3 | PASSED: Code excerpt included verbatim in Sec 3.3
PASS [✓]   | Check 10: Section 6 contains all framing requirements and verbatim phrases | PASSED: Subsections 6.1-6.7 and all 5 mandatory phrases verified
PASS [✓]   | Check 11: Total body word count within journal range | Total body words: 11,238 (Total with abstract: 11,508)
PASS [✓]   | Check 12: Every number in abstract appears in results | All abstract metrics confirmed in Sec 4
PASS [✓]   | Check 13: All 10 figures exist as 300 DPI PNGs     | PASSED: All 10 PNG figures validated
PASS [✓]   | Check 14: All 10 tables saved as separate CSVs in paper2/tables/ | PASSED: All 10 CSV tables confirmed
PASS [✓]   | Check 15: Manuscript under 30 pages                | Actual Word page count: 26 pages (Estimated: 21.9 pages, Limit: 30 pages)
PASS [✓]   | Check 16: Three formal algorithms cited in Sec 3 and Sec 4 | Algo 1: 2x, Algo 2: 2x, Algo 3: 2x
================================================================================
ALL 16 QUALITY VERIFICATION CHECKS PASSED PERFECTLY!
================================================================================
```

---
**Verification Conclusion**: The revised manuscript [`paper2_manuscript.docx`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/draft/paper2_manuscript.docx) and [`paper2_manuscript.pdf`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/draft/paper2_manuscript.pdf) represent a mathematically reconciled, fully reproducible, and scientifically honest contribution ready for high-impact journal submission.
