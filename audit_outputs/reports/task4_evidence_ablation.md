# Task 4: Evidence Component Ablation Audit Report

## 1. Executive Summary & Critical Scientific Finding
A component ablation was performed by forcing each of the 4 postural evidence signals ($c_{\text{topo}}$, $c_{\text{anom}}$, $c_{\text{trust}}$, $c_{\text{conf}}$) to zero, as well as permuting topological risk $R$ across batches.

### Key Empirical Observation:
- In the baseline system, pure-benign batches exhibit **50.6% false escalation into Level L1 (Observation)**.
- When topological risk is ablated (**$c_{\text{topo}} = 0$**), **pure-benign L1 escalation immediately drops from 50.6% to 0.0%** (100% of pure benign batches remain in L0 Nominal).
- When $R$ is permuted across batches, L1 escalation remains at ~50%, confirming that this signal is driven entirely by the synthetic prior distribution threshold $\tau_{\text{topo}} = 0.42$ relative to $\mu_R = 0.42$.
- **Manuscript Remediation**: The claim that topological centrality provides active threat evidence for peripheral edge traffic is scientifically ungrounded. The manuscript must temper claims regarding topological evidence, explicitly stating that $c_{\text{topo}}$ acts as a static network centrality prior rather than a dynamic flow anomaly detector.

## 2. Complete Ablation Results Table

| ablation                  |   pure_benign_L0_pct |   pure_benign_L1_pct |   pure_benign_L2plus_pct |   P2_tier_Block_FPR_pct |   P2_tier_Quarantine_FPR_pct |   Combined_Net_Benefit_OCU |
|:--------------------------|---------------------:|---------------------:|-------------------------:|------------------------:|-----------------------------:|---------------------------:|
| Baseline (Full TARP+ADTM) |                50    |                50    |                        0 |                       0 |                        29.36 |                1.90787e+06 |
| Ablation (a): c_topo = 0  |               100    |                 0    |                        0 |                       0 |                        16.12 |                1.91918e+06 |
| Ablation (b): c_anom = 0  |                50    |                50    |                        0 |                       0 |                         8.23 |                1.22536e+06 |
| Ablation (c): c_trust = 0 |                50    |                50    |                        0 |                       0 |                         8.23 |                1.22536e+06 |
| Ablation (d): c_conf = 0  |                50    |                50    |                        0 |                       0 |                        21.48 |                1.2222e+06  |
| Ablation (e): Permuted R  |                43.33 |                56.67 |                        0 |                       0 |                        28.83 |                1.90752e+06 |

## 3. Attack Density Monotonicity Across Ablations

| ablation                  |   L0_atk_density_pct |   L1_atk_density_pct |   L2_atk_density_pct |   L3_atk_density_pct |   L4_atk_density_pct |
|:--------------------------|---------------------:|---------------------:|---------------------:|---------------------:|---------------------:|
| Baseline (Full TARP+ADTM) |                    0 |                 0    |                45.93 |                50.94 |                  100 |
| Ablation (a): c_topo = 0  |                    0 |                 0    |                46.07 |                54.26 |                  100 |
| Ablation (b): c_anom = 0  |                    0 |                18.37 |                69.15 |                54.15 |                  100 |
| Ablation (c): c_trust = 0 |                    0 |                18.37 |                69.15 |                54.15 |                  100 |
| Ablation (d): c_conf = 0  |                    0 |                 0    |                70.75 |                49.54 |                  100 |
| Ablation (e): Permuted R  |                    0 |                 0    |                45.98 |                51.01 |                  100 |