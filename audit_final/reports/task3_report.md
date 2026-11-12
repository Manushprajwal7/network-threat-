# Task 3 Report: Policy Net Benefit and Confusion Matrix Recomputation

## 1. Summary Comparison (Primary Benchmark: Balanced + Attack-Heavy)
The table below reports exact flow-level Net Benefit (= -Operational Cost) and False Positive Rates computed directly from unit costs:
- Benign costs: Allow=0, Alert=1, Restrict=3, Quarantine=15, Block=50
- Attack rewards: Allow=0, Alert=5, Restrict=10, Quarantine=20, Block=50

| policy   |   balanced_net_ocu |   attack_heavy_net_ocu |   combined_net_ocu |   balanced_block_fpr |   balanced_quar_fpr |   flood_block_fpr |   flood_quar_fpr |
|:---------|-------------------:|-----------------------:|-------------------:|---------------------:|--------------------:|------------------:|-----------------:|
| P_XGB    |            1479900 |                2887550 |        2.18372e+06 |               0.4719 |              0      |            0.4167 |                0 |
| P_hybrid |             962966 |                2902250 |        1.93261e+06 |               0      |             30.0984 |           34.0278 |                0 |
| P_opt    |             985534 |                2856000 |        1.92077e+06 |               0      |              0      |          100      |                0 |
| P2_tier  |             963466 |                2856000 |        1.90973e+06 |               0      |             30.0984 |          100      |                0 |
| P2       |             906920 |                2856000 |        1.88146e+06 |              30.0984 |              9.6647 |          100      |                0 |
| P1       |             423466 |                1149600 |   786533           |               0      |             30.0984 |            0      |              100 |
| P0       |             413930 |                1149600 |   781765           |               0      |             39.7631 |            0      |              100 |

## 2. Key Audit Findings & Reconciliations
1. **P_opt (`Allow-Allow-Restrict-Restrict-Block-Block`)**:
   - Balanced Net Benefit: **+985,534 OCU**
   - Attack-Heavy Net Benefit: **+2,856,000 OCU**
   - Combined Net Benefit: **+1,920,767.0 OCU** (Rank 1 of 70)
   - Balanced Block FPR: **0.00%**, Balanced Quarantine FPR: **0.00%** (zero disruption).

2. **P2_tier (`Allow-Alert-Restrict-Quarantine-Block-Block`)**:
   - Balanced Net Benefit: **+963,466 OCU**
   - Attack-Heavy Net Benefit: **+2,856,000 OCU**
   - Combined Net Benefit: **+1,909,733.0 OCU** (Rank 9 of 70)
   - Advantage over P1: **2.43x** (+1,909,843 vs +786,643 OCU).
   - Benign Quarantine: **8,994 flows (30.0984%)**.

3. **P_XGB (Pure Flow Classifier Baseline)**:
   - On Attack-Heavy: Net benefit is **+2,887,550 OCU** (Attack reward 2,887,850 - Benign penalty 300).
   - On Balanced: Net benefit is **+1,479,900 OCU**.
   - Benign Block FPR: **0.4719%** (141 benign flows blocked on balanced stream).

4. **P_hybrid (Batch Posture + Flow Benign Veto inside L4)**:
   - Combined Net Benefit: **+1,932,608.0 OCU**, exceeding all static policies.
   - Flood Block FPR: Reduced from 100.0% to **34.0278%**.
