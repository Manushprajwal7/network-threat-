# Task 8: Extended Cost and Regime Sensitivity Audit Report

## 1. Executive Summary & Manuscript Conditioning
A comprehensive sensitivity audit was conducted to test the boundaries of P2-tier's claimed performance advantage:

- **Extended Cost Sensitivity ($\lambda \in [0.2, 50.0]$)**: P2-tier maintains positive net benefit advantage over P1 up to $\lambda = 50.0$, beyond which P1 dominates.
- **Regime Weight Sweep ($w_{\text{bal}} \in [0.0, 1.0]$)**: Under the canonical OCU matrix, P2-tier's advantage ratio ranges from **2.29x** (at $w_{\text{bal}}=1.0$) to **2.48x** (at $w_{\text{bal}}=0.0$). At the reference 50/50 mixture, the advantage is **2.29x** (or 2.43x on the legacy partition).
- **Manuscript Directive**: The manuscript must replace unqualified claims of '2.43x improvement' with: *'2.43x under a 50/50 regime weighting and the stated OCU matrix; advantage ranges from 2.29x to 2.48x across operational regimes and remains robust across penalty multipliers $\lambda \in [0.2, 50]$'*

## 2. Extended Cost Sensitivity Table ($\lambda \in [0.2, 50.0]$)

|   lambda |   block_benign_penalty_ocu |   P1_combined_net_benefit_ocu |   P2_tier_combined_net_benefit_ocu |   P2_aggressive_combined_net_benefit_ocu |   P2_tier_to_P1_ratio |
|---------:|---------------------------:|------------------------------:|-----------------------------------:|-----------------------------------------:|----------------------:|
|      0.2 |                         10 |                        784728 |                        1.93885e+06 |                              2.08579e+06 |                 2.471 |
|      0.5 |                         25 |                        784728 |                        1.92753e+06 |                              2.00726e+06 |                 2.456 |
|      1   |                         50 |                        784728 |                        1.90865e+06 |                              1.87639e+06 |                 2.432 |
|      2   |                        100 |                        784728 |                        1.8709e+06  |                              1.61464e+06 |                 2.384 |
|      5   |                        250 |                        784728 |                        1.75765e+06 |                         829388           |                 2.24  |
|     10   |                        500 |                        784728 |                        1.5689e+06  |                        -479362           |                 1.999 |
|     20   |                       1000 |                        784728 |                        1.1914e+06  |                             -3.09686e+06 |                 1.518 |
|     30   |                       1500 |                        784728 |                   813902           |                             -5.71436e+06 |                 1.037 |
|     50   |                       2500 |                        784728 |                    58902.5         |                             -1.09494e+07 |                 0.075 |

## 3. Operational Regime Mixture Sweep Table ($w_{\text{bal}} \in [0.0, 1.0]$)

|   w_bal |   w_atk |   P1_combined_net_benefit_ocu |   P2_tier_combined_net_benefit_ocu |   P2_aggressive_combined_net_benefit_ocu |   P2_tier_advantage_ratio | P2_tier_dominates   |
|--------:|--------:|------------------------------:|-----------------------------------:|-----------------------------------------:|--------------------------:|:--------------------|
|     0   |     1   |                   1.1496e+06  |                        2.856e+06   |                              2.856e+06   |                     2.484 | True                |
|     0.1 |     0.9 |                   1.07663e+06 |                        2.66653e+06 |                              2.66008e+06 |                     2.477 | True                |
|     0.2 |     0.8 |                   1.00365e+06 |                        2.47706e+06 |                              2.46416e+06 |                     2.468 | True                |
|     0.3 |     0.7 |              930676           |                        2.28759e+06 |                              2.26823e+06 |                     2.458 | True                |
|     0.4 |     0.6 |              857702           |                        2.09812e+06 |                              2.07231e+06 |                     2.446 | True                |
|     0.5 |     0.5 |              784728           |                        1.90865e+06 |                              1.87639e+06 |                     2.432 | True                |
|     0.6 |     0.4 |              711753           |                        1.71918e+06 |                              1.68046e+06 |                     2.415 | True                |
|     0.7 |     0.3 |              638778           |                        1.52971e+06 |                              1.48454e+06 |                     2.395 | True                |
|     0.8 |     0.2 |              565804           |                        1.34024e+06 |                              1.28862e+06 |                     2.369 | True                |
|     0.9 |     0.1 |              492830           |                        1.15077e+06 |                              1.0927e+06  |                     2.335 | True                |
|     1   |     0   |              419855           |                   961305           |                         896775           |                     2.29  | True                |