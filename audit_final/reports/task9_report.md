# Task 9 Report: Table 9 Verification and Reconciliation

## 1. Verified Table 9
| Threat Family   |   Total Flows | Share (%)   |   Mean Trust | Allow (%)   | Alert (%)   | Restrict (%)   | Quarantine (%)   | Block (%)   | Dominant Action   |
|:----------------|--------------:|:------------|-------------:|:------------|:------------|:---------------|:-----------------|:------------|:------------------|
| Benign          |        29,882 | 49.80%      |        64.98 | 26.10%      | 34.13%      | 9.66%          | 30.10%           | 0.00%       | Alert             |
| DDoS            |        22,424 | 37.37%      |        10.13 | 0.00%       | 0.00%       | 8.38%          | 31.73%           | 59.89%      | Block             |
| DoS             |         5,328 | 8.88%       |        10.18 | 0.00%       | 0.00%       | 8.07%          | 31.64%           | 60.29%      | Block             |
| Mirai           |         1,788 | 2.98%       |        10.15 | 0.00%       | 0.00%       | 8.45%          | 33.39%           | 58.17%      | Block             |
| Spoofing        |           322 | 0.54%       |        15.19 | 0.00%       | 0.00%       | 8.07%          | 36.96%           | 54.97%      | Block             |
| Recon           |           235 | 0.39%       |        16.17 | 0.00%       | 0.00%       | 10.64%         | 35.32%           | 54.04%      | Block             |
| Web             |            16 | 0.03%       |        19.04 | 0.00%       | 0.00%       | 0.00%          | 25.00%           | 75.00%      | Block             |
| BruteForce      |             5 | 0.01%       |        14.12 | 0.00%       | 0.00%       | 0.00%          | 40.00%           | 60.00%      | Block             |
| Total / Overall |        60,000 | 100.00%     |        37.51 | 13.00%      | 17.00%      | 9.00%          | 31.00%           | 30.00%      | Quarantine        |

## 2. Key Audit Checks Passed:
1. **Conserved Flow Sum**:
   - Benign flows: 29,882 (49.80%)
   - Attack flows: 22,424 + 5,328 + 1,788 + 322 + 235 + 16 + 5 = **30,118 flows (50.20%)**
   - Total flows: 29,882 + 30,118 = **60,000 flows (100.00%)**
2. **Corrected Block Percentage**:
   - The erroneous 30.29% has been replaced with the exact mathematical value:
     $$\frac{18,000}{60,000} = 30.00\%$$
3. **Calibrated Web Trust**:
   - Web application threat family (16 flows) records a mean trust of **19.04** (identical to Section 6.3 and Section 4.3.3).
4. **Benign False Block Rate**:
   - Benign traffic incurs strictly **0.00% Block** (0 flows blocked out of 29,882).
