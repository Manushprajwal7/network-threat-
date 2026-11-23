# CHANGELOG: Manuscript & Codebase Reconciliation

**Project**: Multi-Stage Intrusion Response and Posture Escalation in IoT Networks: An Empirical Study on CICIoT2023  
**Author / Auditor**: Senior Reproducibility Auditor & ML Reviewer  
**Date**: November 11, 2026  
**Source of Truth Configuration**: [`configs/paper.yaml`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/configs/paper.yaml)  

All modifications across the codebase, experimental pipelines, configuration matrices, and manuscript sources are cataloged below with exact `file:line`, before/after states, rationale, and proving artifacts.

---

## 1. Codebase & Pipeline Changes (`file:line — before — after — reason`)

| File & Line | Before | After | Technical Reason | Artifact / Experiment |
| :--- | :--- | :--- | :--- | :--- |
| `backend/ml_model/train.py:142` | `y != 'BenignTraffic'` (contaminated IF training data) | `y == 'BenignTraffic'` (clean benign training partition) | String mismatch inverted anomaly labels, contaminating IF model to AUC 0.008 | `experiments/E1_multi_seed/results.csv`, Table 3 |
| `backend/ml_model/anomaly.py:88` | `s_anom = model.score_samples(X)` | `s_anom = -model.score_samples(X)` | scikit-learn convention returns negative scores for anomalies; negation aligns with attack probability ($r = +0.7794$) | `experiments/E22_score_sign/results.csv`, §3.3 |
| `backend/api/security_level_manager.py:215` | Fallback branch undefined when $S=0 \land \bar{T} < 60.0$ | `if S == 0 and T_bar < 60.0: return 1` ($L_1$) | Unhandled branch caused nondeterministic level assignment; behavioral trust degradation warrants heightened monitoring | Algorithm 1, §3.2 |
| `experiments/E14_per_family/run_exp14.py:74` | Substring match dropped Class 0 (`Backdoor_Malware`) and Class 2 (`BrowserHijacking`) | Explicit mapping for all 34 classes into 8 families (BrowserHijacking $\to$ Web, Backdoor $\to$ Malware) | Dropping rare classes created 7-flow discrepancy ($30,111$ vs $30,118$ attack flows) | `experiments/E14_per_family/results.csv`, Table 9 |
| `configs/paper.yaml:63` | Hard-reset threshold contradictory across text ($c > 0.95$ vs $c \ge 0.90$) | Unified to $c_{\text{conf}} \ge 0.90, \hat{y} \ne \text{benign}, \tilde{s}_{\text{anom}} \ge 0.50 \implies T \leftarrow 10.0$ | Eliminates contradictory parameter definitions across text and code | `configs/paper.yaml`, Algorithm 2 |
| `configs/paper.yaml:11` | Inconsistent training attack % (97.5% vs 97.76%) | Standardized to **97.64%** ($5,362,433 / 5,491,971 = 97.641\%$) | Mathematical consistency with CICIoT2023 training partition ground truth | `configs/paper.yaml`, §3.1 |
| `paper2/code/assemble_manuscript.py:340` | Table 10 placed before Table 1 in document flow | Table 10 relocated to Section 3.4 and renumbered sequentially as **Table 2** | Follows IEEE style where tables must appear strictly in order of textual citation | `paper2/tables/tab2_cost_matrix.csv`, Table 2 |
| `paper2/code/assemble_manuscript.py:512` | Obsolete strings `["52.68%", "1.17%"]` in quality check | Updated check strings to `["ranks 34 of 65", "does not emerge", "3,477", "18,500", "5.80%"]` | Quality assertion suite must track empirical round 2 reconciled numbers | `paper2/code/assemble_manuscript.py`, Check 10 |
| `paper2/code/sync_isolated_and_checksums.py:45` | Synced 70 files in isolated clean folder | Updated to sync 83 files including all E1-E25 artifacts, figures, and manuscripts | Content-addressed SHA-256 reproducibility across all 25 experiments | `checksums.sha256` |

---

## 2. Manuscript Text & Table Changes (`file:line — before — after — reason`)

| File & Line | Before | After | Technical Reason | Artifact / Experiment |
| :--- | :--- | :--- | :--- | :--- |
| `paper/paper_v3.tex:1` | *"Regime-Aware Multi-Stage Intrusion Response and Posture Escalation..."* | *"Multi-Stage Intrusion Response and Posture Escalation in IoT Networks: An Empirical Study on CICIoT2023"* | Online dynamic switcher ties static $P_{2\text{-tier}}$ (+1,909,733 vs +1,909,843 OCU); "Regime-Aware" removed | `experiments/E16_dynamic_switcher/results.csv`, §4.4 |
| `paper/paper_v3.tex:42` | *"2.43x net benefit advantage … on multi-state traffic"* | *"2.43x combined net benefit across both regimes (+1,909,843 vs +786,643 OCU: 2.27x on balanced, 2.48x on attack-heavy)"* | Disaggregates combined net benefit across dual evaluation windows | `experiments/E1_multi_seed/results.csv`, Table 8 |
| `paper/paper_v3.tex:47` | *"preserves strictly 0.00% false-positive blocking across all actions"* | *"zero benign Block assignments (at the cost of 29.9% benign Quarantine on balanced streams and 100% on flood streams)"* | Full availability disruption accounting; eliminates unqualified false-positive claim | `experiments/E3_full_disruption_fpr/results.csv`, Table 7 |
| `paper/paper_v3.tex:52` | *"without artificial weight floors"* | *"under universal neutral initial priors ($T_0 = 100.0$) without label-derived priors"* | Hard reset $T \leftarrow 10.0$ operates as a floor; phrase reworded for technical accuracy | `experiments/E4_adtm_weight/results.csv`, §4.1.2 |
| `paper/paper_v3.tex:58` | *"confirmed that the sixth tier dynamically engages for high-centrality backbone infrastructure"* | *"L5 is populated in Experiment E8 (simulated core-hub monitoring, 100,000 flows, 100% attack); under peripheral edge-gateway streams L5 remains empty"* | Edge streams ($R \approx 0.42$) assign 0 batches to $L_5$; core hubs ($R \ge 0.75$) escalate 100% under acute flood | `experiments/E8_l5_population/results.csv`, Table 12 |
| `paper/paper_v3.tex:315` | References [25], [26] cited neural network papers; [28], [29] lacked reproducibility context | Replaced with Foo et al. 2005 [25] (ADEPTS), Shameli-Sendi et al. 2014 [26] (IRS), NASEM 2019 [28], Boettiger 2015 [29] (Docker) | Primary literature must directly support intrusion response and software reproducibility claims | `paper/paper_v3.tex`, §2.6, §2.7 |
| `paper/paper_v3.tex:412` | Missing technical topology details | Added Section 3.1.1 detailing Barab\'asi-Albert ($N=120, m=2$), PageRank ($\alpha=0.85$), and round-robin batch mapping | Eliminates ambiguity regarding synthetic graph generation and centrality scaling | `experiments/E10_tarp_reproducibility/results.csv`, §3.1.1, App B |
| `paper/paper_v3.tex:590` | Figure 3 caption copied $C_3^*$ numbers (`60.55% Critical`) | Synchronized to code $C_4^*$ output: `91.34% Critical, 7.89% Very Low, 0.24% Low, 0.49% Moderate, 0.04% High` | Caption must match regenerated Figure 3 and Table 4 code output | `experiments/E13_table4_figure3/results.csv`, Table 4, Fig 3 |
| `paper/paper_v3.tex:720` | Table 5 Level $L_4$ attack share CI misprinted as `[97.47%, 97.52%]` | Recomputed and corrected upper bound to `[97.47%, 97.72%]` | Exact statsmodels Wilson score confidence interval calculation ($58,560 / 60,000$, $\alpha = 0.05$) | `experiments/E23_wilson_ci/results.csv`, Table 5 |
| `paper/paper_v3.tex:785` | Table 6 reported potential degenerate zero-width intervals `[0.0%, 0.0%]` | Recomputed non-degenerate intervals: $L_0$: `[0.00%, 0.05%]`, $L_4$: `[99.98%, 100.00%]` | Strict binomial Wilson score formula with continuity correction prevents degenerate bounds | `experiments/E23_wilson_ci/results.csv`, Table 6 |
| `paper/paper_v3.tex:895` | Table 8 reported P2 benign penalty as `252,982 OCU` | Corrected arithmetic to **`521,820 OCU`** ($10,300 \times 3 + 2,948 \times 15 + 8,934 \times 50$) | Corrects legacy tabular entry typo; net benefit invariant at $+907,520$ OCU | `paper2/tables/tab8_master_policy.csv`, Table 8 |
| `paper/paper_v3.tex:920` | Section 4.3.2 claimed P2-tier achieves 0.00% Block FPR without out-of-sample split | Added held-out test split evaluation (seed 99, 60k flows, E21): Block FPR = 0.12%, Quarantine FPR = 31.01%, Net = +1,907,694 OCU | Documents real out-of-sample generalization performance on unseen test flows | `experiments/E21_held_out_balanced/results.csv`, §4.3.2 |
| `paper/paper_v3.tex:1015` | Section 4.4 claimed dynamic switcher "ties" with 110 OCU discrepancy | Explained 110 OCU offset (0.006%) as discrete batch boundary variation; static policy captures full benefit | Transparently reconciles numerical difference between dynamic and static models | `experiments/E16_dynamic_switcher/results.csv`, §4.4 |
| `paper/paper_v3.tex:1110` | Section 6.1 described commit drift as minor variance | Formally documented as 5.80% flow reallocation (3,477 flows) with strict total conservation $\sum \Delta = 0$ | Quantifies operational impact of decision engine commit drift | `paper2/draft/sections/sec6_limitations.py`, §6.1 |
| `paper/paper_v3.tex:1145` | Section 6.3 cited Web attack mean trust as `35.84` | Reconciled to empirical code output: **`16.03`** (matching Table 9) | Section text had cited uncalibrated legacy model value | `experiments/E14_per_family/results.csv`, Table 9, §6.3 |
| `paper/paper_v3.tex:1180` | Section 6.4 reported benign actions as `Alert 40.62%, Restrict 11.07%, total 52.68%` | Reconciled under $P_{2\text{-tier}}$: Alert 34.4%, Restrict 9.9% (attention 44.3%), Quarantine 29.9%, Block 0.0% | Section text had cited legacy uncalibrated split; reconciled to Table 9 under $P_{2\text{-tier}}$ | `experiments/E16_dynamic_switcher/results.csv`, Table 9, §6.4 |
| `paper/paper_v3.tex:1210` | Section 6.5 stated Level $L_3$ held "as few as 1.17% of flows" | Removed 1.17% exploratory artifact; cited clean empirical count: 18,500 flows (30.83% of stream) | Section text had carried over an obsolete exploratory prototype metric | `paper2/tables/tab6_posture_balanced.csv`, Table 6, §6.5 |
| `paper/paper_v3.tex:1235` | Section 6.6 lacked disaggregated OCU quantification for $P_1$ sacrifice | Explicitly quantified: conservative $P_1$ sacrifices 1,706,400 OCU on attack-heavy and 540,000 OCU on balanced streams | Quantifies availability vs containment trade-off in exact cost units | `paper/paper_v3.tex`, §6.6 |
| `paper/paper_v3.tex:1250` | Appendices placed inline in monolithic block | Modularized into `paper/appendices/A.tex` through `F.tex` and included via `\input{appendices/*.tex}` | Establishes clean, maintainable, modular LaTeX architecture for publication | `paper/appendices/A-F.tex`, `paper/paper_v3.tex` |

---

## 3. Summary of Configuration & Threshold Constants

All experimental scripts and manuscripts strictly inherit the unified configuration from `configs/paper.yaml`:

- **Primary Seeds**: Development/Calibration: `42`; Held-out test: `99`; Multi-seed suite: `[13, 42, 99, 123, 2024]`.
- **IF Model**: `n_estimators=100, 200`, `max_samples=256`, `contamination=0.05`, clean sample size: `20,000`.
- **Quantile Calibration**: $p_5 = 0.4421$, $p_{95} = 0.5284$, $\tau_{\text{anom}} = 0.50$.
- **ADTM Trust Engine**: $T_0 = 100.0$ (neutral prior), $k = 0.30$, weights: $w = (0.40, 0.35, 0.15, 0.10)$, hard reset: $c_{\text{conf}} \ge 0.90 \land \hat{y} \ne \text{benign} \land \tilde{s}_{\text{anom}} \ge 0.50 \implies T \leftarrow 10.0$, $\tau_T = 60.0$, $\tau_{T,\text{crit}} = 20.0$.
- **Synthetic Network**: Barab\'asi-Albert ($N=120, m=2$), PageRank $\alpha=0.85$, $\mu_R = 0.4200, \sigma_R = 0.0799$, $\tau_{\text{topo}} = 0.42$, $\tau_{R,\text{hub}} = 0.75$.
- **Cost Matrix (OCU)**: Allow [0, 0], Alert [1, -5], Restrict [3, -10], Quarantine [15, -20], Block [50, -50].
- **Policies**: 70 monotonic candidates; $P_1$ default mapping `[0,1,2,3,3,4]` (rank 44); $P_{2\text{-tier}}$ recommended mapping `[0,1,2,3,4,4]` (rank 9); $P_2$ aggressive mapping `[0,2,3,4,4,4]` (rank 28).
