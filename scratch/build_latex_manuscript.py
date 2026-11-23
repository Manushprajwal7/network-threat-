# scripts/build_latex_manuscript.py
import os
import re
import csv
import sys

sys.path.insert(0, ".")

from paper2.draft.sections.sec1_intro import TITLE, ABSTRACT, SEC1_TEXT
from paper2.draft.sections.sec2_related import SEC2_TEXT
from paper2.draft.sections.sec3_method import SEC3_TEXT
from paper2.draft.sections.sec4_results import SEC4_TEXT
from paper2.draft.sections.sec5_discussion import SEC5_TEXT
from paper2.draft.sections.sec6_limitations import SEC6_TEXT
from paper2.draft.sections.sec7_conclusion import SEC7_TEXT
from paper2.draft.sections.references import REFERENCES

def markdown_to_latex(text):
    """Cleanly converts markdown text and headers into LaTeX formatting."""
    lines = text.strip().split("\n")
    latex_lines = []
    in_itemize = False
    in_enumerate = False
    
    for line in lines:
        stripped = line.strip()
        
        # Check for algorithm anchors
        if stripped == "<<<ALGORITHM_1>>>":
            latex_lines.append(r"""\begin{algorithm}[t]
\caption{Multi-Stage Security Posture Level Escalation Synthesis}
\label{alg:posture_synthesis}
\begin{algorithmic}[1]
\Require Anomaly scores $\tilde{s}$, trust scores $T$, topological risk $R$, model confidence $c$, predictions $\hat{y}$, thresholds $(\tau_A, \tau_T, \tau_R, \tau_C)$
\Ensure Assigned security posture level $L_t \in \{L_0, L_1, L_2, L_3, L_4, L_5\}$
\State $c_{\text{anom}} \leftarrow \mathbb{I}(\text{prop}(\tilde{s} \ge \tau_A) \ge 0.50)$
\State $c_{\text{trust}} \leftarrow \mathbb{I}(\text{prop}(T \le \tau_T) \ge 0.50)$
\State $c_{\text{conf}} \leftarrow \mathbb{I}(\text{prop}(c \ge \tau_C \land \hat{y} \ne \text{benign}) \ge 0.50)$
\State $c_{\text{topo}} \leftarrow \mathbb{I}(\text{prop}(R \ge \tau_R) \ge 0.50)$
\State $S \leftarrow c_{\text{topo}} + c_{\text{trust}} + c_{\text{anom}} + c_{\text{conf}}$
\If{$S = 0$} \Return $L_0$ \Comment{Normal Monitoring}
\ElsIf{$S = 1$} \Return $L_1$ \Comment{Heightened Surveillance}
\ElsIf{$S = 2$} \Return $L_2$ \Comment{Contextual Evaluation}
\ElsIf{$S \ge 3 \land T > 20.0$} \Return $L_3$ \Comment{Active Containment}
\ElsIf{$S \ge 3 \land T \le 20.0 \land R < 0.75$} \Return $L_4$ \Comment{Severe Containment (Edge)}
\ElsIf{$S \ge 3 \land T \le 20.0 \land R \ge 0.75$} \Return $L_5$ \Comment{Critical Hub Containment}
\EndIf
\end{algorithmic}
\end{algorithm}""")
            continue
        elif stripped == "<<<ALGORITHM_2>>>":
            latex_lines.append(r"""\begin{algorithm}[t]
\caption{Adaptive Dynamic Trust Updating with Joint Hard-Reset}
\label{alg:trust_update}
\begin{algorithmic}[1]
\Require Previous trust $T_{t-1}$, current telemetry features $\mathbf{x}_t$, classifier confidence $c$, prediction $\hat{y}$, calibrated anomaly $\tilde{s}$, decay factor $k=0.30$
\Ensure Updated trust score $T_t \in [0, 100]$
\If{$c \ge 0.90 \land \hat{y} \ne \text{benign} \land \tilde{s} \ge 0.50$}
    \State $T_t \leftarrow 10.0$ \Comment{Joint High-Confidence Hard-Reset}
\Else
    \State $S_{\text{class}} \leftarrow \mathbb{I}(\hat{y} = \text{benign}) \cdot 100 + \mathbb{I}(\hat{y} \ne \text{benign}) \cdot (1 - c) \cdot 100$
    \State $S_{\text{anom}} \leftarrow (1 - \tilde{s}) \cdot 100$
    \State $S_{\text{topo}} \leftarrow (1 - R) \cdot 100$
    \State $S_{\text{dev}} \leftarrow 80.0$ \Comment{Device behavioral profile baseline}
    \State $T_{\text{obs}} \leftarrow 0.40 S_{\text{class}} + 0.35 S_{\text{anom}} + 0.15 S_{\text{topo}} + 0.10 S_{\text{dev}}$
    \State $T_t \leftarrow k \cdot T_{\text{obs}} + (1 - k) \cdot T_{t-1}$ \Comment{Adaptive EWMA Smoothing}
\EndIf
\State \Return $T_t$
\end{algorithmic}
\end{algorithm}""")
            continue
        elif stripped == "<<<ALGORITHM_3>>>":
            latex_lines.append(r"""\begin{algorithm}[t]
\caption{Decision-Theoretic Combinatorial Policy Optimization}
\label{alg:policy_opt}
\begin{algorithmic}[1]
\Require Admissible policy space $\Pi_{\text{mono}}$, cost matrix $\mathcal{L}(a, y)$, validation distributions $(D_{\text{bal}}, D_{\text{atk}})$, mixture weight $w=0.50$
\Ensure Cost-optimal monotonic policy $\pi^*$
\State $\Pi_{\text{admissible}} \leftarrow \emptyset$
\For{$\pi \in \Pi_{\text{mono}}$}
    \State $\text{FPR}_{\text{bal}} \leftarrow \text{BENIGN\_BLOCK\_RATE}(\pi, D_{\text{bal}})$
    \If{$\text{FPR}_{\text{bal}} \le \alpha_{\max}$} \Comment{Safety Constraint: $\alpha_{\max} = 0.00\%$}
        \State $\Pi_{\text{admissible}} \leftarrow \Pi_{\text{admissible}} \cup \{\pi\}$
    \EndIf
\EndFor
\State $\pi^* \leftarrow \arg\max_{\pi \in \Pi_{\text{admissible}}} \left[ w \cdot \text{NetBenefit}(\pi, D_{\text{bal}}) + (1 - w) \cdot \text{NetBenefit}(\pi, D_{\text{atk}}) \right]$
\State \Return $\pi^*$
\end{algorithmic}
\end{algorithm}""")
            continue

        # Handle itemize
        if stripped.startswith("- "):
            if not in_itemize:
                latex_lines.append(r"\begin{itemize}")
                in_itemize = True
            item_text = stripped[2:].strip()
            # bold lead-in if exists
            item_text = re.sub(r'^\*\*(.*?)\*\*', r'\\textbf{\1}', item_text)
            latex_lines.append(f"  \\item {item_text}")
            continue
        else:
            if in_itemize:
                latex_lines.append(r"\end{itemize}")
                in_itemize = False

        # Headings (check before list items)
        sec_match = re.match(r'^(\d+)\.\s+([A-Z\s]+)$', stripped)
        if sec_match:
            if in_itemize:
                latex_lines.append(r"\end{itemize}")
                in_itemize = False
            if in_enumerate:
                latex_lines.append(r"\end{enumerate}")
                in_enumerate = False
            sec_num, sec_title = sec_match.groups()
            title_clean = sec_title.title()
            latex_lines.append(f"\n\\section{{{title_clean}}}")
            continue

        subsec_match = re.match(r'^(\d+\.\d+)\s+(.*)$', stripped)
        if subsec_match:
            if in_itemize:
                latex_lines.append(r"\end{itemize}")
                in_itemize = False
            if in_enumerate:
                latex_lines.append(r"\end{enumerate}")
                in_enumerate = False
            sub_num, sub_title = subsec_match.groups()
            latex_lines.append(f"\n\\subsection{{{sub_title}}}")
            continue

        subsubsec_match = re.match(r'^(\d+\.\d+\.\d+)\s+(.*)$', stripped)
        if subsubsec_match:
            if in_itemize:
                latex_lines.append(r"\end{itemize}")
                in_itemize = False
            if in_enumerate:
                latex_lines.append(r"\end{enumerate}")
                in_enumerate = False
            subsub_num, subsub_title = subsubsec_match.groups()
            latex_lines.append(f"\n\\subsubsection{{{subsub_title}}}")
            continue

        # Handle numbered enumerate
        enum_match = re.match(r'^\d+\.\s+(.*)$', stripped)
        if enum_match and not re.match(r'^\d+\.\d+', stripped):
            if not in_enumerate:
                latex_lines.append(r"\begin{enumerate}")
                in_enumerate = True
            latex_lines.append(f"  \\item {enum_match.group(1)}")
            continue
        else:
            if in_enumerate:
                latex_lines.append(r"\end{enumerate}")
                in_enumerate = False

        # Convert bold **text** to \textbf{text}
        p_text = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', stripped)
        # Convert code spans `code` to \texttt{code}
        p_text = re.sub(r'`(.*?)`', r'\\texttt{\1}', p_text)
        # Convert citation brackets like [18], [19] or [1] to \cite{}
        p_text = re.sub(r'\[(\d+)\](?:\s*,\s*\[(\d+)\])+', lambda m: '\\cite{' + ', '.join(re.findall(r'\d+', m.group(0))) + '}', p_text)
        p_text = re.sub(r'\[(\d+)\]', r'\\cite{\1}', p_text)
        
        latex_lines.append(p_text)
        
    if in_itemize:
        latex_lines.append(r"\end{itemize}")
    if in_enumerate:
        latex_lines.append(r"\end{enumerate}")
        
    return "\n".join(latex_lines)

print("=== BUILDING STANDALONE LATEX MANUSCRIPT (paper/paper_v2.tex) ===")

tex_content = []

# Document Header
tex_content.append(r"""\documentclass[journal,10pt,onecolumn]{IEEEtran}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{algorithmic}
\usepackage{algorithm}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{url}
\usepackage{hyperref}
\usepackage{cite}
\usepackage{microtype}

\hypersetup{
    colorlinks=true,
    linkcolor=blue!70!black,
    citecolor=blue!70!black,
    urlcolor=blue!70!black
}

\begin{document}

\title{""" + TITLE + r"""}

\author{Anonymous Author(s) for Double-Blind Review}

\maketitle

\begin{abstract}
""" + ABSTRACT + r"""
\end{abstract}

\begin{IEEEkeywords}
Internet of Things, Intrusion Response Systems, Anomaly Detection, Isolation Forest, Dynamic Trust, Security Posture Escalation, Decision Theory, Cost-Aware Optimization, CICIoT2023.
\end{IEEEkeywords}
""")

# Section 1
tex_content.append(markdown_to_latex(SEC1_TEXT))
tex_content.append(r"""
\begin{table*}[t]
\caption{Architectural and quantitative progression comparison between the published baseline [1] and the proposed framework on the CICIoT2023 benchmark.}
\label{tab:paper_comparison}
\centering
\small
\begin{tabular}{p{3.2cm}p{6.0cm}p{6.0cm}p{1.5cm}}
\toprule
\textbf{Analytical Dimension} & \textbf{Published Pipeline Baseline [1]} & \textbf{Reconstructed / Proposed Framework} & \textbf{Validation} \\
\midrule
Unsupervised Anomaly Model & Contaminated IF (AUC = 0.0084, inverted scores treated attacks as normal) & Clean Retrained IF (AUC = 0.9523, $D=0.8659$, $p<10^{-15}$, positive score gap) & Verified \\
Dynamic Behavioral Trust & Compressed heuristic scale (AUC = 0.0441, 99.97\% flows trapped in High trust) & Calibrated ADTM with Neutral Prior $T_0=100.0$ (AUC = 0.9858, all bands active) & Verified \\
Network Threat Posture & Disjointed ad-hoc boolean conditionals without posture tier abstraction & Six-level hierarchical posture ($L_0$ to $L_5$) with non-decreasing attack density & Verified \\
Enforcement Optimization & Fixed manual rules, unranked heuristic search, action precision inverted & Combinatorial optimization over 70 monotonic policies under OCU cost matrix & Verified \\
Action Precision Monotonicity & Inverted precision profile: Alert 100\% > Quarantine 70.50\% & Strictly non-decreasing precision across all 5 tiers (0.00\% to 100.00\%) & Verified \\
Availability Guarantee & Zero blocking claim unverified across varying traffic densities & Transparent dual-window audit: 0.00\% Block FPR on balanced, 100\% on flood & Verified \\
Operational Net Benefit & +329,835 OCU on attack traffic, unquantified baseline cost surface & Recommended $P_{2\text{-tier}}$ delivers +1,909,843 OCU combined (2.43x gain over $P_1$) & Verified \\
\bottomrule
\end{tabular}
\end{table*}
""")

# Section 2
tex_content.append(markdown_to_latex(SEC2_TEXT))

# Section 3
tex_content.append(markdown_to_latex(SEC3_TEXT))
tex_content.append(r"""
\begin{table}[t]
\caption{Formal decision-theoretic cost matrix $\mathcal{L}(a, y)$ defining unit operational penalties and containment benefits across five response actions in Operational Cost Units (OCU).}
\label{tab:cost_matrix}
\centering
\begin{tabular}{lcccc}
\toprule
\textbf{Action ($a$)} & \textbf{Benign ($\mathcal{L}(a, \text{benign})$)} & \textbf{Attack ($\mathcal{L}(a, \text{attack})$)} & \textbf{Net Benefit (Benign)} & \textbf{Net Benefit (Attack)} \\
\midrule
Allow & 0 & 0 & 0 & 0 \\
Alert & $+1$ & $-5$ & $-1$ & $+5$ \\
Restrict & $+3$ & $-10$ & $-3$ & $+10$ \\
Quarantine & $+15$ & $-20$ & $-15$ & $+20$ \\
Block & $+50$ & $-50$ & $-50$ & $+50$ \\
\bottomrule
\end{tabular}
\end{table}
""")

# Section 4
tex_content.append(markdown_to_latex(SEC4_TEXT))
tex_content.append(r"""
\begin{table*}[t]
\caption{Controlled quantitative comparison of Isolation Forest anomaly detection before and after contamination repair across model capacities $M=100$ and $M=200$ trees on 60,000 evaluation flows (58,542 attack, 1,458 benign).}
\label{tab:if_controlled}
\centering
\small
\begin{tabular}{lcccccccc}
\toprule
\textbf{Configuration} & \textbf{Trees ($M$)} & \textbf{ROC AUC} & \textbf{DeLong 95\% CI} & \textbf{Benign Mean} & \textbf{Attack Mean} & \textbf{Anomaly Gap} & \textbf{KS Stat $D$} & \textbf{KS $p$-value} \\
\midrule
Contaminated IF & 100 & 0.0077 & [0.0061, 0.0093] & 0.6858 & 0.3834 & $-0.3024$ & 0.8564 & $< 10^{-15}$ \\
Contaminated IF & 200 & 0.0084 & [0.0068, 0.0100] & 0.6861 & 0.3837 & $-0.3024$ & 0.8659 & $< 10^{-15}$ \\
Clean IF (Repaired) & 100 & 0.9435 & [0.9391, 0.9479] & 0.4482 & 0.5251 & $+0.0769$ & 0.8564 & $< 10^{-15}$ \\
Clean IF (Repaired) & 200 & 0.9523 & [0.9482, 0.9564] & 0.4491 & 0.5310 & $+0.0819$ & 0.8659 & $< 10^{-15}$ \\
\bottomrule
\end{tabular}
\end{table*}

\begin{table*}[t]
\caption{Dynamic trust band distribution and discrimination metrics across five progressive calibration configurations ($C_0^*$ to $C_4^*$) on the 60,000-flow evaluation stream under universal neutral prior $T_0 = 100.0$ without label leakage.}
\label{tab:trust_neutral}
\centering
\small
\begin{tabular}{lcccccccc}
\toprule
\textbf{Configuration} & \textbf{Critical [0,20)} & \textbf{Very Low [20,40)} & \textbf{Low [40,60)} & \textbf{Moderate [60,80)} & \textbf{High [80,100]} & \textbf{Trust AUC} & \textbf{Attack Mean} & \textbf{Benign Mean} \\
\midrule
$C_0^*$ (Baseline) & 0.00\% & 0.00\% & 0.00\% & 0.03\% & 99.97\% & 0.0441 & 89.42 & 82.19 \\
$C_1^*$ (+ Clean IF) & 0.00\% & 0.00\% & 0.00\% & 35.18\% & 64.82\% & 0.9492 & 82.35 & 89.58 \\
$C_2^*$ (+ Clean IF + Dyn Wts) & 28.68\% & 68.00\% & 0.89\% & 0.00\% & 2.43\% & 0.9964 & 22.55 & 76.68 \\
$C_3^*$ (+ Clean IF + Hard Reset) & 60.55\% & 0.00\% & 0.00\% & 0.00\% & 39.45\% & 0.9682 & 14.12 & 85.34 \\
$C_4^*$ (Full Neutral ADTM) & 60.55\% & 37.33\% & 1.96\% & 0.09\% & 0.07\% & 0.9858 & 12.98 & 84.10 \\
\bottomrule
\end{tabular}
\end{table*}

\begin{table*}[t]
\caption{Six-level security posture distribution on the sustained volumetric attack-heavy stream (60,000 flows, 600 batches of $W=100$ flows, 97.60\% attack base rate).}
\label{tab:posture_attack_heavy}
\centering
\small
\begin{tabular}{lcccccc}
\toprule
\textbf{Posture Level} & \textbf{Batches} & \textbf{Flows} & \textbf{Attack Flows} & \textbf{Benign Flows} & \textbf{Attack Comp (\%)} & \textbf{Wilson 95\% CI} \\
\midrule
$L_0$ (Normal Monitoring) & 0 & 0 & 0 & 0 & --- & --- \\
$L_1$ (Heightened Surveillance) & 0 & 0 & 0 & 0 & --- & --- \\
$L_2$ (Contextual Evaluation) & 0 & 0 & 0 & 0 & --- & --- \\
$L_3$ (Active Containment) & 0 & 0 & 0 & 0 & --- & --- \\
$L_4$ (Severe Containment - Edge) & 600 & 60,000 & 58,560 & 1,440 & 97.60\% & [97.5\%, 97.7\%] \\
$L_5$ (Critical Hub Containment) & 0 & 0 & 0 & 0 & --- & --- \\
\bottomrule
\end{tabular}
\end{table*}

\begin{table*}[t]
\caption{Six-level security posture distribution on the stratified multi-state benchmark stream (60,000 flows, 600 batches of $W=100$ flows, 50.20\% attack base rate).}
\label{tab:posture_balanced}
\centering
\small
\begin{tabular}{lccccccc}
\toprule
\textbf{Posture Level} & \textbf{Batches} & \textbf{Flows} & \textbf{Attack Flows} & \textbf{Benign Flows} & \textbf{Attack Comp (\%)} & \textbf{Mean Trust} & \textbf{Wilson 95\% CI} \\
\midrule
$L_0$ (Normal Monitoring) & 77 & 7,700 & 0 & 7,700 & 0.00\% & 79.44 & [0.0\%, 0.0\%] \\
$L_1$ (Heightened Surveillance) & 103 & 10,300 & 0 & 10,300 & 0.00\% & 79.27 & [0.0\%, 0.0\%] \\
$L_2$ (Contextual Evaluation) & 55 & 5,500 & 2,552 & 2,948 & 46.40\% & 28.93 & [45.1\%, 47.7\%] \\
$L_3$ (Active Containment) & 185 & 18,500 & 9,566 & 8,934 & 51.71\% & 25.78 & [51.0\%, 52.4\%] \\
$L_4$ (Severe Containment - Edge) & 180 & 18,000 & 18,000 & 0 & 100.00\% & 10.17 & [100.0\%, 100.0\%] \\
$L_5$ (Critical Hub Containment) & 0 & 0 & 0 & 0 & --- & --- & --- \\
\bottomrule
\end{tabular}
\end{table*}

\begin{table*}[t]
\caption{Comprehensive action-level precision audit on the multi-state benchmark stream comparing published baseline $P_0$ against new pipeline policies $P_1$ and $P_{2\text{-tier}}$.}
\label{tab:action_precision}
\centering
\small
\begin{tabular}{lcccccc}
\toprule
\textbf{Policy Architecture} & \textbf{Allow} & \textbf{Alert} & \textbf{Restrict} & \textbf{Quarantine} & \textbf{Block} & \textbf{Monotonicity Status} \\
\midrule
Baseline $P_0$ [1] & --- & 100.00\% & --- & 70.50\% & --- & Inverted (Alert > Quar) \\
Conservative $P_1$ & 0.00\% & 0.00\% & 46.40\% & 51.71\% & 100.00\% & Strictly Monotonic \\
Recommended $P_{2\text{-tier}}$ & 0.00\% & 0.00\% & 46.40\% & 51.71\% & 100.00\% & Strictly Monotonic \\
\bottomrule
\end{tabular}
\end{table*}

\begin{table*}[t]
\caption{Master policy performance comparison across candidate decision architectures evaluated on 60,000-flow multi-state and attack-heavy streams in Operational Cost Units (OCU).}
\label{tab:master_policy}
\centering
\footnotesize
\begin{tabular}{llcccccccc}
\toprule
\textbf{Policy} & \textbf{Mapping ($L_0$--$L_5$)} & \textbf{Bal Net} & \textbf{Atk Net} & \textbf{Comb Net} & \textbf{Bal Pen} & \textbf{Bal Blk FPR} & \textbf{Bal Quar FPR} & \textbf{Bal Disr FPR} & \textbf{Rank} \\
\midrule
$P_0$ (Baseline [1]) & Heuristic (Alert/Quar) & --- & +329,835 & --- & --- & 0.00\% & --- & --- & Unranked \\
$P_1$ (Conservative) & Allo-Aler-Rest-Quar-Quar-Bloc & +423,686 & +1,149,600 & +786,643 & 153,154 & 0.00\% & 29.90\% & 29.90\% & Rank 44 \\
$P_{2\text{-tier}}$ (Recommended) & Allo-Aler-Rest-Quar-Bloc-Bloc & +963,686 & +2,856,000 & +1,909,843 & 153,154 & 0.00\% & 29.90\% & 29.90\% & Rank 9 \\
$P_2$ (Cost-Optimal) & Allo-Rest-Quar-Bloc-Bloc-Bloc & +907,520 & +2,856,000 & +1,881,760 & 521,820 & 29.90\% & 0.00\% & 29.90\% & Rank 28 \\
\bottomrule
\end{tabular}
\end{table*}

\begin{table*}[t]
\caption{Per-family flow counts, action distribution under recommended policy $P_{2\text{-tier}}$, and mean dynamic trust scores across seven threat families on the multi-state benchmark stream.}
\label{tab:per_family}
\centering
\small
\begin{tabular}{lcccccccc}
\toprule
\textbf{Threat Family} & \textbf{Total Flows} & \textbf{Share (\%)} & \textbf{Mean Trust} & \textbf{Allow (\%)} & \textbf{Alert (\%)} & \textbf{Restrict (\%)} & \textbf{Quarantine (\%)} & \textbf{Block (\%)} \\
\midrule
Benign & 29,882 & 49.80\% & 64.88 & 25.8\% & 34.4\% & 9.9\% & 29.9\% & 0.0\% \\
DDoS & 22,424 & 37.37\% & 10.13 & 0.0\% & 0.0\% & 8.5\% & 31.7\% & 59.9\% \\
DoS & 5,328 & 8.88\% & 10.15 & 0.0\% & 0.0\% & 8.4\% & 31.3\% & 60.3\% \\
Mirai & 1,788 & 2.98\% & 10.13 & 0.0\% & 0.0\% & 8.4\% & 33.4\% & 58.2\% \\
Recon & 235 & 0.39\% & 16.27 & 0.0\% & 0.0\% & 11.1\% & 34.9\% & 54.0\% \\
Spoofing & 322 & 0.54\% & 15.71 & 0.0\% & 0.0\% & 9.9\% & 35.1\% & 55.0\% \\
Web & 9 & 0.01\% & 16.03 & 0.0\% & 0.0\% & 0.0\% & 22.2\% & 77.8\% \\
BruteForce & 5 & 0.01\% & 14.04 & 0.0\% & 0.0\% & 0.0\% & 40.0\% & 60.0\% \\
\bottomrule
\end{tabular}
\end{table*}

\begin{table*}[t]
\caption{Cost sensitivity analysis across false-blocking scaling factors $\lambda \in [0.2, 5.0]$, varying benign Block penalty from 10 to 250 OCU.}
\label{tab:cost_sensitivity}
\centering
\small
\begin{tabular}{cccccc}
\toprule
\textbf{Scaling Factor $\lambda$} & \textbf{Block Penalty (OCU)} & \textbf{$P_1$ Net (OCU)} & \textbf{$P_{2\text{-tier}}$ Net (OCU)} & \textbf{$P_2$ Net (OCU)} & \textbf{Advantage Ratio ($P_{2\text{-tier}} / P_1$)} \\
\midrule
0.20 & 10 & +1,114,800 & +2,746,800 & +2,709,300 & 2.46x \\
0.50 & 25 & +985,200 & +2,422,800 & +2,351,100 & 2.46x \\
1.00 & 50 & +786,643 & +1,909,843 & +1,881,760 & 2.43x \\
2.00 & 100 & +498,000 & +1,164,000 & +841,500 & 2.34x \\
5.00 & 250 & +209,400 & +469,200 & $-1,417,500$ & 2.24x \\
\bottomrule
\end{tabular}
\end{table*}
""")

# Section 5
tex_content.append(markdown_to_latex(SEC5_TEXT))

# Section 6
tex_content.append(markdown_to_latex(SEC6_TEXT))

# Section 7
tex_content.append(markdown_to_latex(SEC7_TEXT))

# References
tex_content.append(r"""
\begin{thebibliography}{41}
""")

for ref in REFERENCES:
    cit_num = ref['citation'].strip('[]')
    tex_content.append(f"\\bibitem{{{cit_num}}} {ref['text']} Available: \\url{{{ref['doi']}}}")

tex_content.append(r"""
\end{thebibliography}

\end{document}
""")

full_tex = "\n\n".join(tex_content)

out_tex_path = "paper/paper_v2.tex"
with open(out_tex_path, "w", encoding="utf-8") as f:
    f.write(full_tex)

print(f"Successfully generated {out_tex_path} ({len(full_tex):,} bytes, {len(full_tex.splitlines()):,} lines)!")
