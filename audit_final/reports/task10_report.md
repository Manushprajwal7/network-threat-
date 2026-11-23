# Task 10 Report: Supervised Classifier Performance and Family Metrics Audit

## 1. Global Performance Metrics (Frozen XGBoost Artifact)
| metric                               | scope                  |   value |
|:-------------------------------------|:-----------------------|--------:|
| Overall Accuracy                     | All 34 Classes         |  0.9899 |
| Balanced Accuracy                    | All 34 Classes         |  0.7098 |
| Macro Precision                      | All 34 Classes         |  0.7098 |
| Macro Recall                         | All 34 Classes         |  0.7098 |
| Macro F1-Score                       | All 34 Classes         |  0.7098 |
| Weighted F1-Score                    | All 34 Classes         |  0.9899 |
| Attack Detection Rate (Macro Recall) | 33 Attack Classes      |  0.7035 |
| Attack Macro F1                      | 33 Attack Classes      |  0.7035 |
| 8-Family Macro Precision             | 8 Operational Families |  0.884  |
| 8-Family Macro Recall                | 8 Operational Families |  0.885  |
| 8-Family Macro F1                    | 8 Operational Families |  0.8842 |

## 2. Per-Family Consolidated Metrics (Test Split: 1,176,851 flows)
| family     |   classes_count |   test_support |   true_positives |   precision |   recall | recall_95ci      |   f1_score |
|:-----------|----------------:|---------------:|-----------------:|------------:|---------:|:-----------------|-----------:|
| DDoS       |              12 |         855981 |           855174 |      0.9991 |   0.9991 | [99.90%, 99.91%] |     0.9991 |
| DoS        |               4 |         204245 |           204048 |      0.999  |   0.999  | [99.89%, 99.92%] |     0.999  |
| Mirai      |               3 |          66749 |            66686 |      0.9991 |   0.9991 | [99.88%, 99.93%] |     0.9991 |
| Benign     |               1 |          27709 |            25456 |      0.9187 |   0.9187 | [91.54%, 92.19%] |     0.9187 |
| Spoofing   |               2 |          12410 |             7695 |      0.6201 |   0.6201 | [61.15%, 62.86%] |     0.6201 |
| Recon      |               5 |           8812 |             5826 |      0.6612 |   0.6612 | [65.12%, 67.10%] |     0.6612 |
| Web        |               5 |            537 |               17 |      0.0317 |   0.0317 | [1.99%, 5.01%]   |     0.0317 |
| BruteForce |               1 |            319 |               48 |      0.1505 |   0.1505 | [11.54%, 19.39%] |     0.1505 |
| Malware    |               1 |             89 |                1 |      0.0112 |   0.0112 | [0.20%, 6.09%]   |     0.0112 |

## 3. Minority Class Audit and Reconciliation
- **Malware (`Backdoor_Malware`)**: Total test support is $N=89$ flows. The model correctly recalls exactly 1 flow (recall 1.12%, Wilson 95% CI: [0.20%, 6.09%]). On the 60,000-flow multi-state evaluation stream, exactly 1 flow is present; merging this single flow into the Web family or reporting it separately does not alter macroscopic metrics.
- **BruteForce (`DictionaryBruteForce`)**: Support is $N=319$ flows; recall is 15.05% (48 flows detected, Wilson 95% CI: [11.51%, 19.42%]).
- **Web Applications**: CommandInjection (recall 3.36%), BrowserHijacking (recall 3.73%), SqlInjection (recall 4.73%), Uploading_Attack (recall 0.00%), XSS (recall 0.97%).
- These findings fully support the limitation disclosure in Section 4.3.5 and Section 6.
