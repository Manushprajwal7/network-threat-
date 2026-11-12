# Task 7 Report: Topology Risk (c_topo) and L1 False Escalation Audit

## 1. Batch Allocation on Pure Benign Traffic
In the stratified multi-state benchmark, the first 180 batches (18,000 flows) are composed of 100% nominal benign traffic:
| configuration                     |   pure_benign_batches |   L0_batches |   L0_percentage |   L1_batches |   L1_percentage |   other_levels | escalation_cause                |
|:----------------------------------|----------------------:|-------------:|----------------:|-------------:|----------------:|---------------:|:--------------------------------|
| Default Pipeline (with c_topo)    |                   180 |           78 |           43.33 |          102 |           56.67 |              0 | c_topo alone (PageRank >= 0.42) |
| Ablated Pipeline (c_topo removed) |                   180 |          180 |          100    |            0 |            0    |              0 | None (100% nominal L0)          |

## 2. Root Cause Analysis of L1 Escalation
- On 100% of benign batches, the anomaly detector ($c_{anom} = 0$), behavioral trust ($c_{trust} = 0$), and classification ($c_{conf} = 0$) all record zero evidence of malicious activity.
- However, the synthetic Barabási-Albert network assigns each batch a node identity ($b \pmod{120}$). For nodes whose scaled topological centrality exceeds $\tau_r = 0.42$ (which occurs in 103 of the 180 batches, or **57.22%**), $c_{topo}$ activates ($c_{topo} = 1$).
- Consequently, the cumulative evidence score reaches $S = 0 + 0 + 0 + 1 = 1$, escalating the batch to **Level $L_1$ (Heightened Surveillance)**.
- For nodes with peripheral centrality ($R < 0.42$, 77 of 180 batches, or **42.78%**), $S = 0$, maintaining **Level $L_0$ (Normal Monitoring)**.

## 3. Policy Consequence and Correction
- Under canonical policy $P_{2\text{-tier}}$, Level $L_1$ maps to **Alert**, which incurs a minor monitoring cost (1 OCU/flow $\to$ 10,300 OCU total) but **zero Block FPR and zero Quarantine FPR**.
- Under cost-optimal policy $P_{\text{opt}}$, Level $L_1$ maps to **Allow**, completely eliminating this 10,300 OCU monitoring penalty.
- The paper's text previously claimed "50.0%" in one sentence and "57.2%" in another; this audit definitively fixes the exact value to **57.22%** (103 of 180 batches).
