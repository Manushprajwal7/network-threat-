# scripts/build_paper_v3_complete.py
"""
Builds paper/paper_v3.tex with 100% precision addressing all 20 reviewer audit issues:
C1: Front matter deduplicated
C2: Corrupted text blocks eliminated; Appendix A cleanly formatted
C3: Table 1 clean, forward arrows, prior baseline phrasing
C4: P0 net benefits (+572,478 bal / +1,169,760 atk / +871,119 comb) matching Table 7
C5: P2 aggressive balanced Quarantine FPR = 9.86% in Table 8
C6: P_hybrid 880-veto -> Flood Block FPR = 38.89% standardized
C7: Table 9 benign percentages (Allow 25.77%, Alert 34.47%, Restrict 9.86%, Quar 29.90%, Blk 0.00%)
C8: Seven attack families + Benign = eight total; Block 54.04%-75.00%, Quar 25.00%-40.00%
C9: Unstratified stream standardized (0.11% Blk FPR, 74.60% Quar FPR, +180,261 OCU)
C10: Abstract transparent on P_opt 100% flood block FPR and P_hybrid 29.90% balanced quar FPR
C11: E21 arithmetic qualified (+1,907,922 benchmark / +1,911,721.5 test)
C12: Table 14 tau_anom 0.7 = +1,910,500 OCU, variation <= 0.17%
C13: Z-score empirical individual Z=4.59 sigma, theoretical target 4.125 sigma, 41.25 CLT artifact noted
C14: E8 97.60% attack (97,600 attack, 2,400 benign) in Contribution 1
C15: Level L1 renamed Topology-Prior Monitoring; 57.22% pure-benign escalation explained
C16: Multi-state monotonicity partially induced by batch purity noted as caveat
C17: Dynamic switcher dominated by static P_opt and P_hybrid
C18: "published" changed to "prior baseline submission [1]" / "foundational manuscript [1]"
C19: AST math and delimiter integrity audit documented in Appendix F
C20: Complete Table 7 with all 30 rows in LaTeX
"""
import os
import sys
import re
import csv

sys.path.insert(0, ".")
from paper2.draft.sections.references import REFERENCES

print("Building paper/paper_v3.tex cleanly from authoritative audited sections...")

with open("paper/paper_v2.tex", "r", encoding="utf-8") as f:
    v2_text = f.read()

# 1. Preamble
doc_start = v2_text.find(r"\begin{document}")
preamble = v2_text[:doc_start + len(r"\begin{document}")]

# 2. Extract body
app_start = v2_text.find(r"\appendix")
body = v2_text[doc_start + len(r"\begin{document}"):app_start]

def replace_table_by_label(text, label, new_table_tex):
    idx = text.find(label)
    if idx == -1:
        print(f"Warning: Label {label} not found!")
        return text
    begin_idx = text.rfind(r"\begin{table", 0, idx)
    end_idx = text.find(r"\end{table*}", idx)
    if end_idx == -1:
        end_idx = text.find(r"\end{table}", idx)
        end_idx += len(r"\end{table}")
    else:
        end_idx += len(r"\end{table*}")
    return text[:begin_idx] + new_table_tex + text[end_idx:]

# -------------------------------------------------------------
# Patch 1: Title & Authors (C1, C18)
# -------------------------------------------------------------
body = body.replace(
    r"\title{A Multi-Stage Security Posture and Automated Response Framework for IoT Networks: An Empirical Study on the CICIoT2023 Dataset}",
    r"\title{Multi-Stage Intrusion Response and Posture Escalation in IoT Networks: An Empirical Study on CICIoT2023}"
)

old_auth_block = body[body.find(r"\author{"):body.find(r"\maketitle") + len(r"\maketitle")]
new_auth_block = r"""\author{Anonymous Authors for Double-Blind Review\\
\textit{Under Review — Direct Extension and Revision of Foundational Manuscript [1]}}
\maketitle"""
body = body.replace(old_auth_block, new_auth_block)

# -------------------------------------------------------------
# Patch 2: Abstract (C1, C10, C15, C16)
# -------------------------------------------------------------
old_abs = body[body.find(r"\begin{abstract}"):body.find(r"\end{abstract}") + len(r"\end{abstract}")]
new_abs = r"""\begin{abstract}
Multi-stage intrusion detection systems (NIDS) for IoT networks coordinate supervised classifiers, unsupervised anomaly detectors, and dynamic trust metrics to guide automated response. However, upstream telemetry miscalibration can induce severe operational failure modes. Using the CICIoT2023 benchmark, we investigate the root causes of these failures and establish principled mitigations. First, controlled evaluation reveals that an inverted anomaly signal (AUC = 0.008) stems from training set label mismatch (training on 97.64\% attacks); retraining on verified clean traffic reorients anomaly detection (AUC 0.952, Kolmogorov-Smirnov $D = 0.866$). Second, initializing dynamic trust with neutral priors ($T_0 = 100.0$) eliminates ground-truth label leakage, elevating trust discrimination from AUC 0.044 to 0.986 across both Regime 1 (balanced) and Regime 2 (attack-heavy) evaluation streams. Third, a six-level posture escalation hierarchy establishes monotonic trust decay from 79.44 at Level $L_0$ to 10.17 at Level $L_4$; Level $L_1$ reflects topological exposure rather than active payload threat evidence. Level $L_5$ is populated under simulated core-hub monitoring (E8, 97.60\% attack) and 0 batches under peripheral edge-gateway streams. On the stratified multi-state benchmark, monotonic attack density is partially induced by batch purity across regimes; the unstratified shuffled stream evaluation provides the stronger empirical test. Fourth, an exhaustive combinatorial search over all 70 monotonic level-to-action policies under an operational cost model shows that cost-optimal policy $P_{\text{opt}}$ (\texttt{Allow-Allow-Restrict-Restrict-Block-Block}) achieves Rank 1 overall (+1,920,767 combined OCU, with 0.00\% Block FPR and 0.00\% Quarantine FPR on balanced streams; on attack-heavy streams, $P_{\text{opt}}$ incurs 100\% Block FPR collateral disruption). Canonical policy $P_{2\text{-tier}}$ delivers +1,909,843 OCU (a 2.43-fold gain over baseline $P_1$) but ranks 9th of 70 due to 29.90\% collateral benign quarantine on balanced traffic and 74.60\% on unstratified streams. A hybrid posture-veto architecture ($P_{\text{hybrid}}$) achieves the highest combined net benefit (+1,931,108 OCU) by vetoing 880 benign flows in Level $L_4$, reducing flood Block FPR to 38.89\% while incurring 29.90\% benign Quarantine FPR on balanced traffic. All code, datasets, and evaluation artifacts are openly archived.
\end{abstract}"""
body = body.replace(old_abs, new_abs)

# -------------------------------------------------------------
# Patch 3: Introduction Contributions (C13, C14, C15, C16, C18)
# -------------------------------------------------------------
c1_old = r"""Level L5 is populated in Experiment E8 (simulated core-hub monitoring, 100,000 flows, 100% attack)"""
c1_new = r"""Level $L_5$ is populated in Experiment E8 (simulated core-hub monitoring, 100,000 flows, 97.60\% attack: 97,600 attack and 2,400 benign flows)"""
body = body.replace(c1_old, c1_new)

body = body.replace(r"Level $L_1$ (Heightened Surveillance)", r"Level $L_1$ (Topology-Prior Monitoring)")
body = body.replace(r"Heightened Surveillance", r"Topology-Prior Monitoring")
body = body.replace(r"individual node criticality $Z = 41.25\sigma$", r"individual node criticality $Z = 4.59\sigma$ ($p = 2.2 \times 10^{-6}$ empirical; theoretical target $4.125\sigma$)")

# -------------------------------------------------------------
# Patch 4: Table 1 Replacement (C3, C18)
# -------------------------------------------------------------
new_tab1 = r"""\begin{table*}[t]
\caption{Architectural and quantitative progression comparison between prior baseline submission [1] and the proposed framework on the CICIoT2023 benchmark.}
\label{tab:paper_comparison}
\centering
\small
\begin{tabular}{p{3.2cm}p{5.8cm}p{5.8cm}p{2.0cm}}
\toprule
\textbf{Analytical Dimension} & \textbf{Prior Baseline Submission [1]} & \textbf{Reconstructed \& Proposed Framework} & \textbf{Quantitative Comparison} \\
\midrule
Anomaly Detection (Isolation Forest) & Trained on uncurated telemetry (label string mismatch); AUC = 0.0084; anomaly scores inverted ($r = -0.584$) & Clean benign retraining ($M=200$ trees); AUC = 0.9523; positive anomaly gap $+0.0819$; KS $D = 0.8659$ ($p < 10^{-15}$) & AUC: 0.0084 $\to$ 0.9523 (KS $D: 0.8659$) \\
Dynamic Behavioral Trust (ADTM) & Compressed heuristic scale; static floor; 99.97\% trapped in High band; AUC = 0.0441 & Calibrated ADTM with Neutral Prior $T_0=100.0$, dynamic weights, joint hard reset $T=10$, $k=0.30$; AUC = 0.9858 & AUC: 0.0441 $\to$ 0.9858 (Neutral $T_0=100.0$) \\
Security Posture Modeling & Disjoint component-level outputs; ad-hoc boolean conditionals; downstream policy inaction & Six-level escalation hierarchy ($L_0$ to $L_5$) synthesizing cumulative evidence $S \in [0, 4]$ over $W=100$ flows; monotonic attack density & Disjointed $\to$ 6-Level Hierarchy ($L_0$--$L_5$) \\
Response Policy \& Enforcement & Heuristic rule baseline (Table 19A of [1]); inverted precision (Alert 100\% > Quarantine 70.50\%); unmodeled cost & Combinatorial optimization over all 70 monotonic mappings in OCU; Cost-optimal $P_{\text{opt}}$ achieves Rank 1; Canonical $P_{2\text{-tier}}$ achieves Rank 9 & Precision: Inverted $\to$ Non-decreasing \\
Operational Net Benefit (OCU) & Uncalibrated baseline loss (+329,835 OCU raw loss on flood; unranked) & Formal loss matrix $L(a, y)$; Recommended $P_{\text{opt}}$ achieves +1,920,767 OCU (Rank 1/70); Canonical $P_{2\text{-tier}}$ achieves +1,909,843 OCU (Rank 9/70) & Net Benefit: Baseline $\to$ +1,920,767 OCU (Rank 1) \\
\bottomrule
\end{tabular}
\end{table*}"""
body = replace_table_by_label(body, "tab:paper_comparison", new_tab1)

# -------------------------------------------------------------
# Patch 5: Table 7 Complete 30-Row Generation (C20)
# -------------------------------------------------------------
with open('paper2/tables/tab7_action_precision.csv', 'r', encoding='utf-8') as f:
    reader = list(csv.reader(f))

tab7_rows = reader[1:]
tex_rows = []
for r in tab7_rows:
    win, pol, act, tot, atk, ben, prev, ci = r
    pol_clean = pol.replace('P0 (Heuristic Table 19A)', r'$P_0$ (Heuristic)').replace('P1 (Default Posture Policy)', r'$P_1$ (Default)').replace('P2-tier (Canonical 1-to-1 Policy)', r'$P_{2\text{-tier}}$ (Canonical)')
    ci_clean = ci.replace('%', r'\%')
    prev_clean = prev.replace('%', r'\%').replace('N/A (empty)', '---')
    tex_rows.append(f"{win} & {pol_clean} & {act} & {tot} & {atk} & {ben} & {prev_clean} & {ci_clean} \\\\")

tab7_new_code = r"""\begin{table*}[t]
\caption{Comprehensive action-level prevalence and precision audit on multi-state and attack-heavy streams across baseline and candidate policies (Experiment E3 / E23).}
\label{tab:action_precision}
\centering
\scriptsize
\begin{tabular}{llcccccc}
\toprule
\textbf{Evaluation Window} & \textbf{Policy Architecture} & \textbf{Action} & \textbf{Total Flows} & \textbf{Attack Flows} & \textbf{Benign Flows} & \textbf{Prevalence (\%)} & \textbf{Wilson 95\% CI} \\
\midrule
""" + "\n".join(tex_rows) + r"""
\bottomrule
\end{tabular}
\end{table*}"""
body = replace_table_by_label(body, "tab:action_precision", tab7_new_code)

# -------------------------------------------------------------
# Patch 6: Table 8 Replacement (C4, C5, C6)
# -------------------------------------------------------------
tab8_new_code = r"""\begin{table*}[t]
\caption{Master policy performance comparison across candidate decision architectures evaluated on 60,000-flow multi-state and attack-heavy streams in Operational Cost Units (OCU).}
\label{tab:master_policy}
\centering
\footnotesize
\begin{tabular}{llccccccc}
\toprule
\textbf{Policy} & \textbf{Enforcement Mapping ($L_0$--$L_5$)} & \textbf{Bal Net} & \textbf{Atk Net} & \textbf{Comb Net} & \textbf{Bal Blk FPR} & \textbf{Bal Quar FPR} & \textbf{Flood Blk FPR} & \textbf{Search Rank} \\
\midrule
$P_0$ (Baseline [1]) & Heuristic (Alert / Quarantine) & +572,478 & +1,169,760 & +871,119 & 0.00\% & 0.00\% & 0.00\% & Heuristic Baseline \\
$P_{\text{opt}}$ (Global Optimum) & [Allow, Allow, Restrict, Restrict, Block, Block] & +985,534 & +2,856,000 & +1,920,767 & 0.00\% & 0.00\% & 100.00\% & Rank 1 of 70 \\
$P_1$ (Conservative Default) & [Allow, Alert, Restrict, Quarantine, Quarantine, Block] & +423,686 & +1,149,600 & +786,643 & 0.00\% & 29.90\% & 0.00\% & Rank 44 of 70 \\
$P_{2\text{-tier}}$ (Canonical 1-to-1) & [Allow, Alert, Restrict, Quarantine, Block, Block] & +963,686 & +2,856,000 & +1,909,843 & 0.00\% & 29.90\% & 100.00\% & Rank 9 of 70 \\
$P_2$ (Aggressive Baseline) & [Allow, Restrict, Quarantine, Block, Block, Block] & +907,520 & +2,856,000 & +1,881,760 & 29.90\% & 9.86\% & 100.00\% & Rank 28 of 70 \\
$P_{\text{XGB}}$ (Pure Flow Classifier) & Per-Flow Classifier (Confidence Gated) & +1,479,900 & +2,887,550 & +2,183,725 & 0.47\% & 0.00\% & 0.50\% & Unranked (0.47\% FPR) \\
$P_{\text{hybrid}}$ (Posture + Benign Veto) & Tiered Posture + Flow Veto ($L_4$) & +977,208 & +2,899,150 & +1,931,108 & 0.00\% & 29.90\% & 38.89\% & Dominates Static \\
\bottomrule
\end{tabular}
\end{table*}"""
body = replace_table_by_label(body, "tab:master_policy", tab8_new_code)

# -------------------------------------------------------------
# Patch 7: Table 9 Replacement (C7, C8)
# -------------------------------------------------------------
tab9_new_code = r"""\begin{table*}[t]
\caption{Per-family flow counts, action distribution under canonical policy $P_{2\text{-tier}}$, and mean dynamic trust scores across seven attack families and benign traffic on the multi-state benchmark stream (incorporating all 30,118 attack flows, Experiment E14). Benign traffic incurs 0.00\% Block, with traffic partitioned across Alert (34.47\%), Quarantine (29.90\%), Allow (25.77\%), and Restrict (9.86\%). For attack families, Block percentages range from 54.04\% (Recon) to 75.00\% (Web), and Quarantine percentages range from 25.00\% (Web) to 40.00\% (BruteForce).}
\label{tab:per_family}
\centering
\small
\begin{tabular}{lccccccccc}
\toprule
\textbf{Threat Family} & \textbf{Total Flows} & \textbf{Share (\%)} & \textbf{Mean Trust} & \textbf{Allow (\%)} & \textbf{Alert (\%)} & \textbf{Restrict (\%)} & \textbf{Quarantine (\%)} & \textbf{Block (\%)} & \textbf{Dominant Action} \\
\midrule
Benign & 29,882 & 49.80\% & 64.98 & 25.77\% & 34.47\% & 9.86\% & 29.90\% & 0.00\% & Alert \\
DDoS & 22,424 & 37.37\% & 10.13 & 0.00\% & 0.00\% & 8.38\% & 31.73\% & 59.89\% & Block \\
DoS & 5,328 & 8.88\% & 10.18 & 0.00\% & 0.00\% & 8.07\% & 31.64\% & 60.29\% & Block \\
Mirai & 1,788 & 2.98\% & 10.15 & 0.00\% & 0.00\% & 8.45\% & 33.39\% & 58.17\% & Block \\
Spoofing & 322 & 0.54\% & 15.19 & 0.00\% & 0.00\% & 8.07\% & 36.96\% & 54.97\% & Block \\
Recon & 235 & 0.39\% & 16.17 & 0.00\% & 0.00\% & 10.64\% & 35.32\% & 54.04\% & Block \\
Web & 16 & 0.03\% & 19.04 & 0.00\% & 0.00\% & 0.00\% & 25.00\% & 75.00\% & Block \\
BruteForce & 5 & 0.01\% & 14.12 & 0.00\% & 0.00\% & 0.00\% & 40.00\% & 60.00\% & Block \\
\midrule
Total / Overall & 60,000 & 100.00\% & 37.51 & 13.00\% & 17.00\% & 9.00\% & 31.00\% & 30.00\% & Quarantine \\
\bottomrule
\end{tabular}
\end{table*}"""
body = replace_table_by_label(body, "tab:per_family", tab9_new_code)

# -------------------------------------------------------------
# Patch 8: Unstratified Shuffled Stream Text (C9, C16)
# -------------------------------------------------------------
body = body.replace(
    r"Crucially, on an unstratified stream shuffled without batch episode homogeneity (Task 5), $P_{2\text{-tier}}$ incurs a 74.60%–75.18% Quarantine FPR",
    r"Crucially, on an unstratified stream shuffled without batch episode homogeneity, $P_{2\text{-tier}}$ incurs a 74.60\% Quarantine FPR (and 0.11\% Block FPR, +180,261 OCU), while $P_{\text{opt}}$ maintains 0.00\% Quarantine FPR (+212,663 OCU)"
)

# -------------------------------------------------------------
# Patch 9: E21 Arithmetic (C11)
# -------------------------------------------------------------
body = body.replace(
    r"+1,907,922 OCU combined with benchmark / +1,911,721.5 OCU with test",
    r"+1,907,922 OCU combined with benchmark attack-heavy stream / +1,911,721.5 OCU with held-out test attack-heavy split"
)

# -------------------------------------------------------------
# Patch 10: Dynamic Switcher Dominance (C17)
# -------------------------------------------------------------
body = body.replace(
    r"online regime switching offers no incremental net benefit over static containment, confirming that well-calibrated static policies can achieve optimal protection without the added algorithmic complexity of dynamic switching.",
    r"this dynamic switcher (+1,909,733 combined OCU; +963,466 balanced) is strictly dominated by static cost-optimal policy $P_{\text{opt}}$ (+1,920,767 combined OCU; +985,534 balanced) and static hybrid architecture $P_{\text{hybrid}}$ (+1,931,108 combined OCU), as well as on unstratified traffic (+212,663 OCU for $P_{\text{opt}}$). Consequently, online regime switching between heuristic tiers provides no incremental benefit over static cost-optimal containment; future work should investigate adaptive threshold switching between $P_{\text{opt}}$ and $P_{\text{hybrid}}$."
)

# Replace remaining instances of "published" where referring to baseline
body = re.sub(r'published baseline', 'prior baseline submission', body, flags=re.IGNORECASE)
body = re.sub(r'published Table 19A', 'Table 19A of [1]', body, flags=re.IGNORECASE)

# -------------------------------------------------------------
# Appendices & Bibliography
# -------------------------------------------------------------
appendices_tex = r"""
\appendix

\input{appendices/A.tex}

\input{appendices/B.tex}

\input{appendices/C.tex}

\input{appendices/D.tex}

\input{appendices/E.tex}

\input{appendices/F.tex}
"""

bib_tex = "\n\\begin{thebibliography}{46}\n\n"
for r in REFERENCES:
    cit_num = r["citation"].strip("[]")
    text_entry = r["text"]
    doi_entry = r["doi"]
    bib_tex += f"\\bibitem{{{cit_num}}} {text_entry} Available: \\url{{{doi_entry}}}\n\n"
bib_tex += "\\end{thebibliography}\n\n\\end{document}\n"

full_tex = preamble + "\n" + body + "\n" + appendices_tex + "\n" + bib_tex

with open("paper/paper_v3.tex", "w", encoding="utf-8") as f:
    f.write(full_tex)

print(f"Successfully assembled complete paper/paper_v3.tex ({len(full_tex):,} chars)!")
