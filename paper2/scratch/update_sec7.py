sec7_content = r'''# Section 7: Conclusion and Back Matter
SEC7_TEXT = r"""7. CONCLUSION

This paper has presented the systematic continuation, diagnostic repair, and cost-aware optimization of the multi-stage IoT security framework introduced in our published base paper [1] (*Journal of Cybersecurity and Privacy* 2026, 6(5), 181). Evaluating this architecture on the CICIoT2023 benchmark yields three concrete technical conclusions:

First, controlled evaluation at matched model capacities ($M=100$ and $M=200$ trees) demonstrates that the inverted anomaly performance in earlier iterations (raw AUC $\approx 0.0084$, rounding to 0.008) stemmed entirely from a categorical label mismatch ('BENIGN' vs 'BenignTraffic') during training set curation, rather than model under-capacity. Training on verified clean benign traffic restores discriminative anomaly detection to AUC 0.9523 (rounding to 0.952, with Kolmogorov-Smirnov $D = 0.8659, p < 10^{-15}$), while empirical dose-response curves reveal that anomaly inversion begins at 10% contamination, exhibits directional reversal at 20%, and reaches near-complete inversion at 97.6%, demonstrating the critical importance of training purity in network telemetry baselining as articulated by Sommer and Paxson [27].

Second, by formulating a dynamic trust architecture with neutral initial priors ($T_0 = 100.0$) and removing the two audited inference-time leakage pathways, we demonstrate that runtime evidence alone drives trust degradation. Incorporating clean anomaly scores and high-confidence classification signals elevates trust discrimination AUC from 0.0441 (rounding to 0.044) to 0.9858 (rounding to 0.986) on attack-heavy traffic and 0.9990 on balanced streams, establishing behavioral separation without relying on label-derived priors.

Third, a comprehensive combinatorial sweep over all 70 admissible monotonic level-to-action mappings establishes that response policy selection is inherently regime-dependent. Populated levels $L_0$–$L_4$ are ordered by attack density on the stratified benchmark ($0.00\% \le 0.00\% \le 46.40\% \le 51.71\% \le 100.00\%$) with trust decay ($79.44 \ge 79.27 \ge 28.93 \ge 25.78 \ge 10.17$), though intermediate levels $L_2$ and $L_3$ sit near the 50.20% base rate and provide modest attack enrichment, while $L_5$ is unpopulated under peripheral edge gateway streams. A 1,000-permutation check shows that the peripheral edge-gateway stream never populates Level $L_5$ (0 batches). Under this shuffle the observed monotonicity rate is 0.945 with $p = 1.000$, confirming that monotonic ordering across active levels is descriptive of the stream construction. Candidate policy $P_{\text{opt}}$ (`Allow-Allow-Allow-Allow-Block-Block`, mapping $(0,0,0,0,4,4)$) achieves Rank 1 among all 70 policies across 50 simulation runs (+2,052,438.1 OCU 50-run mean; +1,470,740.0 OCU balanced mean; +900,000 OCU on the Table 6 stream) by assigning $L_0$–$L_3$ to Allow. Canonical reference policy $P_{2\text{-tier}}$ (`Allow-Alert-Restrict-Quarantine-Block-Block`) achieves Rank 15 (+2,009,492.8 OCU 50-run mean; +1,410,822.0 OCU balanced mean; +963,686 OCU on the Table 6 stream, capturing ~64% of achievable 1,505,900 OCU attack reward). Evaluating decision baselines across a 10-seed protocol demonstrates that on stationary closed-world benchmarks, confidence-gated per-flow XGBoost ($P_{\text{XGB}}$) matches or outperforms all static posture policies (+1,472,830 OCU balanced mean). In contrast, in Leave-One-Family-Out (LOFO) evaluation across novel attack families, posture policies raise recall on four of five adequately sized held-out families ($n \ge 235$, e.g., Mirai botnet recall rises from 0.33% to 27.42%), though leaving approximately 72.6% of attacks unmitigated and being outperformed by $P_{\text{XGB}}$ on DoS (+673,900 vs +672,783 OCU). Under volumetric flood saturation, the Hybrid Posture + Benign Veto architecture ($P_{\text{hybrid}}$) delivers slightly higher net utility (+2,974,176 OCU vs. +2,960,105 OCU, a small effect of +0.47% or +14,071 OCU, driven by batch-level Block enforcement). Rather than claiming universal dominance, our findings dictate a conditional strategy balancing closed-world classifier accuracy with multi-tier posture resilience.

DATA AND CODE AVAILABILITY
All source code, trained machine learning model artifacts, evaluation split generation scripts, experimental logs, and reproducibility verification pipelines are archived in the repository package. All experimental CSV tables, models, and algorithmic replication scripts are cryptographically hashed with SHA-256 integrity checksums stored in `audit_v3/E11_reproducibility/MANIFEST.sha256`. Raw network traffic features originate from the public CICIoT2023 benchmark repository hosted by the Canadian Institute for Cybersecurity [11].

FUNDING DECLARATION
This research received no external grant funding. All computational evaluations and model training pipelines were conducted using local workstation infrastructure equipped with an NVIDIA GeForce RTX 3050 Laptop GPU (6GB VRAM) and an x86_64 host processor.

COMPETING INTERESTS
The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the findings reported in this paper.

ACKNOWLEDGMENTS
The authors thank the Canadian Institute for Cybersecurity (CIC) and the University of New Brunswick for curating and maintaining the open CICIoT2023 research repository.
"""
'''

with open('draft/sections/sec7_conclusion.py', 'w', encoding='utf-8') as f:
    f.write(sec7_content)

print("Successfully updated draft/sections/sec7_conclusion.py")
