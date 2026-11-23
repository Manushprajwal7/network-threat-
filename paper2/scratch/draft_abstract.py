title = "Six-Level Security Posture Escalation with Training-Data Contamination Repair and Cost-Aware Response Optimization for IoT Intrusion Detection"

abstract = (
    "Multi-stage IoT intrusion-response pipelines fuse supervised classification, unsupervised anomaly detection, and dynamic trust scoring. "
    "Auditing our published base pipeline [1] on CICIoT2023 revealed two upstream defects: a label mismatch ('BENIGN' vs 'BenignTraffic') "
    "leaving the Isolation Forest trained on 97.64% attack traffic (AUC 0.008, inverted), and trust priors seeded from attack labels. "
    "Retraining on clean benign data restores in-distribution AUC to 0.952 (M=200); however, inverting the contaminated detector yields 0.9916 and ECOD yields 0.977, "
    "framing this contribution as defect repair rather than detector optimality. Neutral priors with runtime telemetry remove audited inference-time leakage, "
    "yielding trust AUC 0.986 on closed-world streams, though hard resets consume classifier predictions. On these signals, we formulate a six-level posture model "
    "over W=100-flow batches. On a stratified stream, active levels L0–L4 populate with non-decreasing attack density (0.0%, 0.0%, 46.4%, 51.7%, 100.0%); "
    "however, L2/L3 remain near the 50.2% base rate, Level L5 is unpopulated (0 flows), and a 1,000-permutation test yields p=1.000, confirming this ordering is descriptive. "
    "Under an assumed cost matrix, we enumerate 70 monotonic response policies. Standalone confidence-gated XGBoost matches or outperforms posture policies on the balanced "
    "mean (+1,472,830 vs. +1,470,740 OCU for P_opt and +1,410,822 for P_2-tier); flood stream gains (+0.47%) arise from batch-level blocking rather than benign veto. "
    "In leave-one-family-out tests, posture raises recall on four of five adequately sized held-out families (e.g., Mirai 0.3% -> 27.4%), but leaves ~72.6% unmitigated, "
    "while XGBoost beats posture on DoS. Nominal accuracy of 98.99% coexists with 70.98% balanced accuracy across 34 classes."
)

words = abstract.split()
print("Abstract word count:", len(words))

nums_in_abstract = ["0.008", "0.952", "0.986", "70", "46.4", "51.7", "27.4", "0.3"]
missing = [n for n in nums_in_abstract if n not in abstract]
print("Missing numbers:", missing)
assert len(missing) == 0, f"Missing numbers: {missing}"
assert len(words) <= 250, f"Abstract is too long: {len(words)} words"
print("SUCCESS: Abstract meets all constraints!")
