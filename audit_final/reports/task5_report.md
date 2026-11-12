# Task 5 Report: Batch-Level Confidence Intervals and Family Sample Size Audit

## 1. Posture Level Confidence Intervals: Flow vs Batch Level
When flows are batched into $W=100$ inspection windows, flows within the same batch share the identical posture assignment. Treating $N=60,000$ individual flows as independent samples yields spuriously narrow confidence intervals.
Evaluating at the batch level ($n_{eff} = 600$ batches) reflects true cluster sampling:

| level   |   batches |   attack_pct | flow_level_95ci   | batch_level_95ci   |   ratio_batch_to_flow_width |
|:--------|----------:|-------------:|:------------------|:-------------------|----------------------------:|
| L0      |        77 |         0    | [0.00%, 0.05%]    | [0.00%, 4.75%]     |                        95.3 |
| L1      |       103 |         0    | [0.00%, 0.04%]    | [0.00%, 3.60%]     |                        96.4 |
| L2      |        55 |        46.4  | [45.08%, 47.72%]  | [34.69%, 60.21%]   |                         9.7 |
| L3      |       185 |        51.71 | [50.99%, 52.43%]  | [44.73%, 58.98%]   |                         9.9 |
| L4      |       180 |       100    | [99.98%, 100.00%] | [97.91%, 100.00%]  |                        97.9 |
| L5      |         0 |         0    | N/A               | N/A                |                         1   |

### Key Findings:
- In Level $L_2$ ($n=55$ batches): Attack density is 46.40%. Batch-level 95% CI is **[34.69%, 60.21%]** (width 25.52%), compared to spuriously narrow flow-level CI **[45.08%, 47.72%]** (width 2.64%).
- In Level $L_3$ ($n=185$ batches): Attack density is 51.71%. Batch-level 95% CI is **[44.73%, 58.98%]**, compared to flow-level CI **[50.99%, 52.43%]**.

## 2. Rare Threat Families in Table 9
For extreme minority classes, asymptotic normal approximations break down. We compute exact Clopper-Pearson binomial intervals:

| family     |   total_flows_N |   blocked_flows |   block_percentage | wilson_95ci      | clopper_pearson_exact_ci   | sample_size_flag                                   |
|:-----------|----------------:|----------------:|-------------------:|:-----------------|:---------------------------|:---------------------------------------------------|
| Benign     |           29882 |               0 |               0    | [0.00%, 0.01%]   | [0.00%, 0.01%]             | Sufficient (N >= 30)                               |
| DDoS       |           22424 |           13430 |              59.89 | [59.25%, 60.53%] | [59.25%, 60.53%]           | Sufficient (N >= 30)                               |
| DoS        |            5328 |            3212 |              60.29 | [58.96%, 61.59%] | [58.96%, 61.60%]           | Sufficient (N >= 30)                               |
| Mirai      |            1788 |            1040 |              58.17 | [55.86%, 60.43%] | [55.84%, 60.46%]           | Sufficient (N >= 30)                               |
| Spoofing   |             322 |             177 |              54.97 | [49.51%, 60.31%] | [49.36%, 60.49%]           | Sufficient (N >= 30)                               |
| Recon      |             235 |             127 |              54.04 | [47.66%, 60.30%] | [47.44%, 60.54%]           | Sufficient (N >= 30)                               |
| Web        |              16 |              12 |              75    | [50.50%, 89.82%] | [47.62%, 92.73%]           | INSUFFICIENT (N < 30) - exact binomial CI required |
| BruteForce |               5 |               3 |              60    | [23.07%, 88.24%] | [14.66%, 94.73%]           | INSUFFICIENT (N < 30) - exact binomial CI required |

### Key Findings:
- **Web ($N=16$ flows)**: Block rate is 75.00% (12/16). Wilson CI is [50.50%, 89.82%]; exact Clopper-Pearson is **[47.62%, 92.73%]**. Footnote added: *“Sample size insufficient for asymptotic inference (N=16); exact Clopper-Pearson binomial CI reported.”*
- **BruteForce ($N=5$ flows)**: Block rate is 60.00% (3/5). Wilson CI is [23.07%, 88.47%]; exact Clopper-Pearson is **[14.66%, 94.73%]**. Footnote added: *“Sample size insufficient for asymptotic inference (N=5); exact Clopper-Pearson binomial CI reported.”*
