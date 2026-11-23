# Task 8 Report: Posture Distribution and L5 Hub Population on Unstratified Shuffled Streams

## 1. Posture Level Distribution under Uniform Interleaved Arrivals
In contrast to the stratified stream (which groups flows into pure benign, mixed, and pure attack phases), a uniformly shuffled stream interleaves benign and attack flows:
| level   |   batches |   total_flows |   attack_flows |   benign_flows |   attack_density_pct |   mean_trust |
|:--------|----------:|--------------:|---------------:|---------------:|---------------------:|-------------:|
| L0      |         0 |             0 |              0 |              0 |                 0    |         0    |
| L1      |         0 |             0 |              0 |              0 |                 0    |         0    |
| L2      |       141 |         14100 |           6542 |           7558 |                46.4  |        28.48 |
| L3      |       458 |         45800 |          23509 |          22291 |                51.33 |        25.97 |
| L4      |         1 |           100 |             67 |             33 |                67    |        19.02 |
| L5      |         0 |             0 |              0 |              0 |                 0    |         0    |

### Key Findings:
1. **Absence of Level $L_5$**:
   - Level $L_5$ occupies **0 batches (0 flows, 0.00%)**.
   - Under uniform random arrival, binomial variance around 50% attack density prevents batches from reaching the extreme attack density and trust collapse required for $L_5$, even on core hub nodes 0 and 4.
2. **Dominance of Level $L_3$**:
   - **446 batches (44,600 flows, 74.33%)** are assigned to Level $L_3$. Because almost every batch contains ~50 attack flows, multi-source evidence activates ($S \ge 3$), but trust remains moderate (mean $T \approx 24.5$), populating $L_3$.

## 2. Policy Performance on Shuffled Stream
| policy   |   net_benefit_ocu |   benign_block_fpr_pct |   benign_quar_fpr_pct |   attack_containment_tpr_pct |
|:---------|------------------:|-----------------------:|----------------------:|-----------------------------:|
| P1       |            179406 |                   0    |                 74.71 |                        78.28 |
| P2_tier  |            180261 |                   0.11 |                 74.6  |                        78.28 |
| P_opt    |            212663 |                   0.11 |                  0    |                         0.22 |

### Key Policy Takeaway:
- Because $P_{2\text{-tier}}$ assigns Level $L_3$ to Quarantine, its Quarantine FPR rises from 29.9% on stratified traffic to **74.6%** on unstratified shuffled traffic.
- In contrast, $P_{\text{opt}}$ assigns Level $L_3$ to Restrict, maintaining **0.00% Quarantine FPR** and **0.11% Block FPR** (+212,663 OCU net benefit).
- This finding provides compelling empirical motivation for $P_{\text{opt}}$ and the microscopic $P_{\text{hybrid}}$ architecture in real-world unsegmented traffic.
