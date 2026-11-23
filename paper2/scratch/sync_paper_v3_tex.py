import re
import os

with open("clean_experiments_isolated/manuscript/paper_v3.tex", "r", encoding="utf-8") as f:
    tex = f.read()

# 1. Update Abstract
old_abs_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', tex, re.DOTALL)
assert old_abs_match is not None, "Abstract not found in paper_v3.tex"

new_abs = r"""Multi-stage IoT intrusion-response pipelines fuse supervised classification, unsupervised anomaly detection, and dynamic trust scoring. Auditing our published base pipeline \cite{1} on CICIoT2023 revealed two upstream defects: a label mismatch ('BENIGN' vs 'BenignTraffic') leaving the Isolation Forest trained on 97.64\% attack traffic (AUC 0.008, inverted), and trust priors seeded from attack labels. Retraining on clean benign data restores in-distribution AUC to 0.952 ($M=200$); however, inverting the contaminated detector yields 0.9916 and ECOD yields 0.977, framing this contribution as defect repair rather than detector optimality. Neutral priors with runtime telemetry remove audited inference-time leakage, yielding trust AUC 0.986 on closed-world streams, though hard resets consume classifier predictions. On these signals, we formulate a six-level posture model over $W=100$-flow batches. On a stratified stream, active levels $L_0$--$L_4$ populate with non-decreasing attack density (0.0\%, 0.0\%, 46.4\%, 51.7\%, 100.0\%); however, $L_2/L_3$ remain near the 50.2\% base rate, Level $L_5$ is unpopulated (0 flows), and a 1,000-permutation test yields $p=1.000$, confirming this ordering is descriptive. Under an assumed cost matrix, we enumerate 70 monotonic response policies. Standalone confidence-gated XGBoost matches or outperforms posture policies on the balanced mean (+1,472,830 vs. +1,470,740 OCU for $P_{\text{opt}}$ and +1,410,822 for $P_{2\text{-tier}}$); flood stream gains (+0.47\%) arise from batch-level blocking rather than benign veto. In leave-one-family-out tests, posture raises recall on four of five adequately sized held-out families (e.g., Mirai 0.3\% $\to$ 27.4\%), but leaves $\sim$72.6\% unmitigated, while XGBoost beats posture on DoS. Nominal accuracy of 98.99\% coexists with 70.98\% balanced accuracy across 34 classes."""

tex = tex.replace(old_abs_match.group(1), "\n" + new_abs + "\n")

# 2. Remove in-text author names in 1.1, 1.4, Table 1, and 7
tex = tex.replace("(Thirupathi and Reddi, \\textit{J. Cybersecur. Priv.} 2026, 6(5), 181)", "(\\textit{J. Cybersecur. Priv.} 2026, 6(5), 181)")
tex = tex.replace("(Thirupathi \\& Reddi, MDPI JCP 6(5), 181)", "(MDPI JCP 6(5), 181)")
tex = tex.replace("(Thirupathi \\& Reddi, \\textit{Journal of Cybersecurity and Privacy} 2026, 6(5), 181 [1])", "(\\textit{Journal of Cybersecurity and Privacy} 2026, 6(5), 181 [1])")

# 3. Purge fake Zenodo DOI and non-existent 4open URL
old_data_avail_match = re.search(r'\\section\*\{Data and Code Availability\}(.*?)(?=\\section\*|\\begin\{thebibliography\}|$)', tex, re.DOTALL)
if old_data_avail_match:
    new_data_avail = r"""
All source code, trained machine learning model artifacts, evaluation split generation scripts, experimental logs, and reproducibility verification pipelines are archived in the repository package. All experimental CSV tables, models, and algorithmic replication scripts are cryptographically hashed with SHA-256 integrity checksums stored in \texttt{audit\_v3/E11\_reproducibility/MANIFEST.sha256}. Raw network traffic features originate from the public CICIoT2023 benchmark repository hosted by the Canadian Institute for Cybersecurity \cite{3}.
"""
    tex = tex.replace(old_data_avail_match.group(1), new_data_avail)

# 4. Update Table 10 (tab:topology_confound_summary)
old_tab10_match = re.search(r'(\\begin\{table\*?\}\[t\]\s*\\caption\{.*?tab:topology_confound_summary.*?\\end\{table\*?\})', tex, re.DOTALL)
if old_tab10_match:
    new_tab10 = r"""\begin{table*}[t]
\caption{Topology confound and permutation robustness audit across 1,000 permutations randomizing node assignment $n(b)$ and shuffling batch order, confirming observed Table 6 stream metrics against random permutations.}
\label{tab:topology_confound_summary}
\centering
\small
\begin{tabular}{lcccccc}
\toprule
\textbf{Metric} & \textbf{Observed (Table 6)} & \textbf{Perm Mean} & \textbf{Perm Std} & \textbf{95\% CI Lower} & \textbf{95\% CI Upper} & \textbf{$p$-value} \\
\midrule
Monotonicity Rate & 1.000 & 0.945 & 0.228 & 0.000 & 1.000 & 1.000 \\
$P_1$ Net OCU & 423,686.0 & 442,533.2 & 5,369.2 & 433,602.8 & 454,530.1 & 0.476 \\
$P_{2\text{-tier}}$ Net OCU & 963,686.0 & 973,530.2 & 1,089.2 & 971,449.4 & 975,555.0 & 0.188 \\
$P_{\text{opt}}$ Net OCU & 985,534.0 & 985,756.0 & 360.0 & 985,534.0 & 986,315.0 & 0.254 \\
$L_0$ Flow Count & 7,700.0 & 13,091.5 & 625.2 & 11,897.5 & 14,300.0 & 0.630 \\
$L_1$ Flow Count & 10,300.0 & 4,908.5 & 625.2 & 3,700.0 & 6,102.5 & 0.630 \\
$L_2$ Flow Count & 5,500.0 & 7,985.2 & 459.1 & 7,100.0 & 8,900.0 & 0.290 \\
$L_3$ Flow Count & 18,500.0 & 15,985.5 & 461.9 & 15,100.0 & 16,900.0 & 0.234 \\
$L_4$ Flow Count & 18,000.0 & 17,718.9 & 177.9 & 17,300.0 & 18,000.0 & 1.000 \\
$L_5$ Flow Count & 0.0 & 310.4 & 177.8 & 0.0 & 700.0 & 0.777 \\
$L_0$ Attack Density & 0.0000 & 0.0000 & 0.0000 & 0.0000 & 0.0000 & 1.000 \\
$L_1$ Attack Density & 0.0000 & 0.0000 & 0.0000 & 0.0000 & 0.0000 & 1.000 \\
$L_2$ Attack Density & 0.4640 & 0.4650 & 0.0016 & 0.4617 & 0.4683 & 0.518 \\
$L_3$ Attack Density & 0.5171 & 0.5247 & 0.0019 & 0.5210 & 0.5284 & 0.660 \\
$L_4$ Attack Density & 1.0000 & 0.9995 & 0.0009 & 0.9979 & 1.0000 & 0.062 \\
$L_5$ Attack Density & 0.0000 & 0.9943 & 0.0255 & 0.9073 & 1.0000 & 1.000 \\
\bottomrule
\end{tabular}
\end{table*}"""
    tex = tex.replace(old_tab10_match.group(1), new_tab10)

# 5. Update Table 12 (tab:master_policy)
old_tab12_match = re.search(r'(\\begin\{table\*?\}\[t\]\s*\\caption\{.*?tab:master_policy.*?\\end\{table\*?\})', tex, re.DOTALL)
if old_tab12_match:
    new_tab12 = r"""\begin{table*}[t]
\caption{Level-to-action master policy performance comparison across candidate monotonic mappings in $\Pi_{70}$ evaluated in Operational Cost Units (OCU).}
\label{tab:master_policy}
\centering
\footnotesize
\begin{tabular}{llccccccc}
\toprule
\textbf{Policy} & \textbf{Mapping ($L_0$--$L_5$)} & \textbf{Overall Mean} & \textbf{Balanced Mean} & \textbf{Test Split (s99)} & \textbf{Table 6 OCU} & \textbf{Bal Blk FPR} & \textbf{Bal Quar FPR} & \textbf{Rank} \\
\midrule
$P_{\text{opt}}$ & Allow-Allow-Allow-Allow-Block-Block & +2,052,438.1 & +1,470,740.0 & +1,444,050 & +900,000 & 0.00\% & 0.00\% & Rank 1 \\
Reference & Allow-Allow-Restrict-Restrict-Block-Block & +2,033,585.0 & +1,443,659.6 & +1,439,948 & +985,534 & 0.00\% & 0.00\% & Rank 8 \\
$P_{2\text{-tier}}$ & Allow-Alert-Restrict-Quarantine-Block-Block & +2,009,492.8 & +1,410,822.0 & +1,404,974 & +963,686 & 0.00\% & 29.90\% & Rank 15 \\
$P_1$ & Allow-Alert-Restrict-Quarantine-Quarantine-Block & +778,666.2 & +529,292.5 & +786,643 & +423,686 & 0.00\% & 29.90\% & Rank 50 \\
\bottomrule
\end{tabular}
\end{table*}"""
    tex = tex.replace(old_tab12_match.group(1), new_tab12)

# 6. Update Table 15 (tab:lofo_full)
old_tab15_match = re.search(r'(\\begin\{table\*?\}\[t\]\s*\\caption\{.*?tab:lofo_full.*?\\end\{table\*?\})', tex, re.DOTALL)
if old_tab15_match:
    new_tab15 = r"""\begin{table*}[t]
\caption{Full Leave-One-Family-Out (LOFO) novel attack cross-validation audit across all seven top-level attack families in CICIoT2023 (incorporating all 28 evaluation rows: 7 threat families $\times$ 4 decision policies) comparing pure classifier $P_{\text{XGB}}$ against multi-stage posture policies on replayed streams.}
\label{tab:lofo_full}
\centering
\small
\begin{tabular}{llcccccc}
\toprule
\textbf{Held-Out Family} & \textbf{Policy} & \textbf{Replayed Flows} & \textbf{Attack Recall (\%)} & \textbf{Block FPR (\%)} & \textbf{Quarantine FPR (\%)} & \textbf{Net OCU} \\
\midrule
DDoS & $P_{\text{XGB}}$ & 40,000 & 67.33\% & 0.02\% & 0.00\% & +497,100 \\
DDoS & $P_{\text{hybrid}}$ & 40,000 & 74.06\% & 0.17\% & 20.88\% & +547,872 \\
DDoS & $P_{\text{opt}}$ & 40,000 & 74.06\% & 0.17\% & 0.00\% & +554,938 \\
DDoS & $P_{2\text{-tier}}$ & 40,000 & 74.06\% & 0.17\% & 20.88\% & +547,872 \\
\midrule
DoS & $P_{\text{XGB}}$ & 40,000 & 67.50\% & 0.10\% & 0.00\% & +673,900 \\
DoS & $P_{\text{hybrid}}$ & 40,000 & 83.59\% & 0.41\% & 19.72\% & +672,783 \\
DoS & $P_{\text{opt}}$ & 40,000 & 67.51\% & 0.41\% & 0.00\% & +693,781 \\
DoS & $P_{2\text{-tier}}$ & 40,000 & 83.59\% & 0.41\% & 19.72\% & +672,783 \\
\midrule
Mirai & $P_{\text{XGB}}$ & 40,000 & 0.27\% & 0.19\% & 0.00\% & +850 \\
Mirai & $P_{\text{hybrid}}$ & 40,000 & 27.35\% & 0.18\% & 6.77\% & +178,713 \\
Mirai & $P_{\text{opt}}$ & 40,000 & 0.26\% & 0.18\% & 0.00\% & +113,288 \\
Mirai & $P_{2\text{-tier}}$ & 40,000 & 27.35\% & 0.18\% & 6.77\% & +178,713 \\
\midrule
Recon & $P_{\text{XGB}}$ & 17,600 & 13.44\% & 0.05\% & 0.00\% & +58,950 \\
Recon & $P_{\text{hybrid}}$ & 17,600 & 23.89\% & 0.07\% & 7.02\% & +93,125 \\
Recon & $P_{\text{opt}}$ & 17,600 & 10.90\% & 0.07\% & 0.00\% & +78,347 \\
Recon & $P_{2\text{-tier}}$ & 17,600 & 23.89\% & 0.07\% & 7.02\% & +93,125 \\
\midrule
Spoofing & $P_{\text{XGB}}$ & 24,800 & 1.69\% & 0.07\% & 0.00\% & +10,000 \\
Spoofing & $P_{\text{hybrid}}$ & 24,800 & 4.19\% & 0.07\% & 1.31\% & +72,480 \\
Spoofing & $P_{\text{opt}}$ & 24,800 & 1.14\% & 0.07\% & 0.00\% & +46,034 \\
Spoofing & $P_{2\text{-tier}}$ & 24,800 & 4.19\% & 0.07\% & 1.31\% & +72,480 \\
\midrule
Web ($n=15$) & $P_{\text{XGB}}$ & 1,200 & 1.33\% & 0.00\% & 0.00\% & +400 \\
Web ($n=15$) & $P_{\text{hybrid}}$ & 1,200 & 9.83\% & 0.00\% & 3.17\% & +3,768 \\
Web ($n=15$) & $P_{\text{opt}}$ & 1,200 & 1.17\% & 0.00\% & 0.00\% & +2,589 \\
Web ($n=15$) & $P_{2\text{-tier}}$ & 1,200 & 9.83\% & 0.00\% & 3.17\% & +3,768 \\
\midrule
BruteForce ($n=5$) & $P_{\text{XGB}}$ & 600 & 1.00\% & 0.33\% & 0.00\% & +100 \\
BruteForce ($n=5$) & $P_{\text{hybrid}}$ & 600 & 2.67\% & 0.33\% & 1.00\% & +1,453 \\
BruteForce ($n=5$) & $P_{\text{opt}}$ & 600 & 0.33\% & 0.33\% & 0.00\% & +903 \\
BruteForce ($n=5$) & $P_{2\text{-tier}}$ & 600 & 2.67\% & 0.33\% & 1.00\% & +1,453 \\
\bottomrule
\end{tabular}
\end{table*}"""
    tex = tex.replace(old_tab15_match.group(1), new_tab15)

with open("clean_experiments_isolated/manuscript/paper_v3.tex", "w", encoding="utf-8") as f:
    f.write(tex)

# Synchronize to ../paper/paper_v3.tex if it exists
if os.path.exists("../paper/paper_v3.tex"):
    with open("../paper/paper_v3.tex", "w", encoding="utf-8") as f:
        f.write(tex)
    print("Synchronized to ../paper/paper_v3.tex")

print("Successfully updated LaTeX manuscript!")
