# Task 9: Classifier Per-Family and Granular Class Audit Report

## 1. Executive Summary & Manuscript Realignment
The manuscript's prominent headline claim of **'98.99% overall accuracy'** masks severe class-imbalance effects inherent to the CICIoT2023 dataset, where DDoS and DoS account for over 90.5% of total flows.

### Rigorous Performance Re-anchoring:
- **34-Class Balanced Accuracy**: **70.98%** (Macro Recall: 0.7098).
- **34-Class Macro F1**: **71.51%** (0.7151).
- **8 Attack Families Balanced Accuracy**: **55.90%**.
- **Manuscript Directive**: Replace all standalone citations of '98.99% overall accuracy' with the balanced metric profile: *'98.99% overall accuracy, 70.98% balanced accuracy, and 71.51% macro F1 across all 34 classes'*, adding the per-family breakdown table.

## 2. Classifier Aggregate Metric Comparison

| Aggregation Scope                | Metric 1 (Accuracy / Balanced Acc)   | Macro F1 Score   | Notes                                                |
|:---------------------------------|:-------------------------------------|:-----------------|:-----------------------------------------------------|
| Overall Flow Accuracy            | 98.99%                               | N/A              | Dominated by DDoS (73.2%) and DoS (17.4%)            |
| All 34 Granular Classes          | 70.98%                               | 71.51%           | Published in classification report (0.7098 / 0.7151) |
| 33 Granular Attack Classes       | 70.35%                               | 70.96%           | Excludes BenignTraffic (Recall 91.87%)               |
| 8 Macro Attack Families + Benign | 59.90%                               | 60.76%           | Grouped operational categories                       |
| 8 Macro Attack Families Only     | 55.90%                               | 57.15%           | Pure attack containment capability                   |

## 3. Macro Family Breakdown with Wilson 95% Confidence Intervals

| macro_family   |   support |   share_pct |   precision_pct |   precision_ci_lower |   precision_ci_upper |   recall_pct |   recall_ci_lower |   recall_ci_upper |   f1_score_pct | statistical_reliability                    |
|:---------------|----------:|------------:|----------------:|---------------------:|---------------------:|-------------:|------------------:|------------------:|---------------:|:-------------------------------------------|
| Benign         |     27709 |       2.355 |           87.57 |               87.184 |               87.942 |        91.87 |            91.541 |            92.185 |          89.67 | Sufficient statistical support             |
| DDoS           |    855981 |      72.735 |           99.98 |               99.974 |               99.981 |        99.91 |            99.899 |            99.912 |          99.94 | Sufficient statistical support             |
| DoS            |    204245 |      17.355 |           99.87 |               99.856 |               99.887 |        99.9  |            99.889 |            99.916 |          99.89 | Sufficient statistical support             |
| Mirai          |     66749 |       5.672 |           99.88 |               99.851 |               99.904 |        99.91 |            99.879 |            99.926 |          99.89 | Sufficient statistical support             |
| Spoofing       |     12410 |       1.055 |           62.31 |               61.449 |               63.158 |        62.01 |            61.149 |            62.857 |          62.16 | Sufficient statistical support             |
| Recon          |      8812 |       0.749 |           66.9  |               65.908 |               67.885 |        66.12 |            65.119 |            67.095 |          66.51 | Sufficient statistical support             |
| Web            |       537 |       0.046 |           16.67 |               10.674 |               25.079 |         3.17 |             1.986 |             5.011 |           5.32 | Rare class (<1,000 flows) — wide Wilson CI |
| BruteForce     |       319 |       0.027 |           38.4  |               30.341 |               47.151 |        15.05 |            11.541 |            19.385 |          21.62 | Rare class (<1,000 flows) — wide Wilson CI |
| Malware        |        89 |       0.008 |            5.88 |                1.046 |               26.982 |         1.12 |             0.199 |             6.093 |           1.88 | Rare class (<1,000 flows) — wide Wilson CI |

## 4. Evaluation of Rare Attack Families
- **Malware** (Support $N=89$ in test, $n=1$ in evaluation window): Recall is only 1.12% (Wilson 95% CI [0.03%, 6.09%]).
- **BruteForce** (Support $N=319$ in test, $n=5$ in evaluation window): Recall is 15.05% (Wilson 95% CI [11.51%, 19.42%]).
- **Web Attacks** (Support $N=537$ in test, $n=15$ in evaluation window): Granular classes exhibit recall between 0.0% and 4.7%.
- The manuscript must explicitly note: *'For rare threat families (Malware, BruteForce, and Web application attacks), sample sizes in windowed evaluations are insufficient for high-confidence statistical claims.'*
