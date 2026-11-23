# Task 6: E21 Held-Out Full Metrics Report

## 1. Disjointness Verification
To prevent data leakage, E21 was drawn strictly from the held-out test partition `[60,000:1,176,851]` with Seed 99. Intersection check with E2 (`[0:60,000]`):
- **Pairwise Overlap with E2**: Exactly **0 flows** (Strictly Disjoint).

## 2. Policy Performance on E21 Held-Out Balanced Partition

| split                                     | policy                               | mapping                       |   total_flows |   benign_flows |   attack_flows |   block_fpr_pct |   block_fpr_ci_lower |   block_fpr_ci_upper |   quarantine_fpr_pct |   quarantine_fpr_ci_lower |   quarantine_fpr_ci_upper |   disruptive_fpr_pct |   balanced_net_benefit_ocu |   combined_net_benefit_ocu |   overlap_with_e2 |
|:------------------------------------------|:-------------------------------------|:------------------------------|--------------:|---------------:|---------------:|----------------:|---------------------:|---------------------:|---------------------:|--------------------------:|--------------------------:|---------------------:|---------------------------:|---------------------------:|------------------:|
| E21 Held-Out Balanced (Seed 99, Disjoint) | P1 (Default Posture Policy)          | Allo-Aler-Rest-Quar-Quar-Bloc |         60000 |          30045 |          29955 |           0     |                0     |                0.013 |               30.957 |                    30.437 |                    31.482 |               30.957 |                     418393 |           783996           |                 0 |
| E21 Held-Out Balanced (Seed 99, Disjoint) | P2-tier (Recommended Posture Policy) | Allo-Aler-Rest-Quar-Bloc-Bloc |         60000 |          30045 |          29955 |           0.233 |                0.184 |                0.294 |               30.724 |                    30.205 |                    31.248 |               30.957 |                     959843 |                1.90792e+06 |                 0 |

## 3. Posture Level Distribution and Attack Densities

| posture_level   |   total_flows |   benign_flows |   attack_flows |   attack_density_pct |   ci_lower_pct |   ci_upper_pct |
|:----------------|--------------:|---------------:|---------------:|---------------------:|---------------:|---------------:|
| L0              |          8600 |           8600 |              0 |                0     |          0     |          0.045 |
| L1              |          9400 |           9400 |              0 |                0     |          0     |          0.041 |
| L2              |          5100 |           2744 |           2356 |               46.196 |         44.831 |         47.567 |
| L3              |         18700 |           9231 |           9469 |               50.636 |         49.92  |         51.353 |
| L4              |         18200 |             70 |          18130 |               99.615 |         99.514 |         99.695 |
| L5              |             0 |              0 |              0 |                0     |          0     |          0     |

## 4. Action-Level Attack Prevalence Under P2-tier

| action     | mapped_levels   |   total_flows |   benign_flows |   attack_flows |   attack_prevalence_pct |   ci_lower_pct |   ci_upper_pct |
|:-----------|:----------------|--------------:|---------------:|---------------:|------------------------:|---------------:|---------------:|
| Allow      | [0]             |          8600 |           8600 |              0 |                   0     |          0     |          0.045 |
| Alert      | [1]             |          9400 |           9400 |              0 |                   0     |          0     |          0.041 |
| Restrict   | [2]             |          5100 |           2744 |           2356 |                  46.196 |         44.831 |         47.567 |
| Quarantine | [3]             |         18700 |           9231 |           9469 |                  50.636 |         49.92  |         51.353 |
| Block      | [4, 5]          |         18200 |             70 |          18130 |                  99.615 |         99.514 |         99.695 |

## 5. Manuscript Editing Directive (§4.3.2)
- **Wording Update**: In Section 4.3.2, change the phrase 'combined net operational benefit' when discussing E21 to **'balanced-stream net benefit'** ({p2_tier_eval['bal']['net_benefit']:,} OCU), because E21 specifically tests the balanced stream.
- Cite the verified Block FPR of **0.233%** (Wilson 95% CI [0.184%, 0.294%]) and Quarantine FPR of **30.724%** (Wilson 95% CI [30.205%, 31.248%]).
