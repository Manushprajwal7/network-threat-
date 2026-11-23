# Task 10: Action Prevalence and Density Table Corrections (Table 7) Report

## 1. Metric Definition & Caption Corrections
- **Renaming**: The metric previously labeled 'Action Precision' has been formally renamed to **'Attack Prevalence within Action'**, defined mathematically as $\text{Prevalence}(a) = \frac{\text{Attack Flows}(a)}{\text{Total Flows}(a)}$. This clarifies that the metric describes the operational attack density of the enforcement queue, rather than a binary classifier precision.

- **Monotonicity Scope**: The monotonic sequence:
  $$\text{Allow (0.00%)} \le \text{Alert (0.00%)} < \text{Restrict (46.40%)} < \text{Quarantine (51.71%)} < \text{Block (100.00%)}$$
  applies **strictly to P2-tier**. Under default policy P1, Level L4 is mapped to Quarantine, collapsing the upper tiers into a single Quarantine queue with 75.52% attack prevalence.

- **P0 Baseline Inclusion**: Explicit evaluation rows for P0 (Published Heuristic Table 19A) are now included, resolving the omission from earlier revisions.

## 2. Reconciled Table 7: Enforcement Action Queue Composition

| Window                  | Policy                               | Action     |   Total Flows |   Attack Flows |   Benign Flows | Attack Prevalence within Action (%)   | Wilson 95% CI     |
|:------------------------|:-------------------------------------|:-----------|--------------:|---------------:|---------------:|:--------------------------------------|:------------------|
| Attack-Heavy 60k        | P0 (Heuristic Table 19A)             | Allow      |             0 |              0 |              0 | N/A (empty)                           | N/A               |
| Attack-Heavy 60k        | P0 (Heuristic Table 19A)             | Alert      |         1,440 |              0 |          1,440 | 0.00%                                 | [0.00%, 0.27%]    |
| Attack-Heavy 60k        | P0 (Heuristic Table 19A)             | Restrict   |             0 |              0 |              0 | N/A (empty)                           | N/A               |
| Attack-Heavy 60k        | P0 (Heuristic Table 19A)             | Quarantine |        58,560 |         58,560 |              0 | 100.00%                               | [99.99%, 100.00%] |
| Attack-Heavy 60k        | P0 (Heuristic Table 19A)             | Block      |             0 |              0 |              0 | N/A (empty)                           | N/A               |
| Attack-Heavy 60k        | P1 (Default Posture Policy)          | Allow      |             0 |              0 |              0 | N/A (empty)                           | N/A               |
| Attack-Heavy 60k        | P1 (Default Posture Policy)          | Alert      |             0 |              0 |              0 | N/A (empty)                           | N/A               |
| Attack-Heavy 60k        | P1 (Default Posture Policy)          | Restrict   |             0 |              0 |              0 | N/A (empty)                           | N/A               |
| Attack-Heavy 60k        | P1 (Default Posture Policy)          | Quarantine |        60,000 |         58,560 |          1,440 | 97.60%                                | [97.47%, 97.72%]  |
| Attack-Heavy 60k        | P1 (Default Posture Policy)          | Block      |             0 |              0 |              0 | N/A (empty)                           | N/A               |
| Attack-Heavy 60k        | P2-tier (Recommended Posture Policy) | Allow      |             0 |              0 |              0 | N/A (empty)                           | N/A               |
| Attack-Heavy 60k        | P2-tier (Recommended Posture Policy) | Alert      |             0 |              0 |              0 | N/A (empty)                           | N/A               |
| Attack-Heavy 60k        | P2-tier (Recommended Posture Policy) | Restrict   |             0 |              0 |              0 | N/A (empty)                           | N/A               |
| Attack-Heavy 60k        | P2-tier (Recommended Posture Policy) | Quarantine |             0 |              0 |              0 | N/A (empty)                           | N/A               |
| Attack-Heavy 60k        | P2-tier (Recommended Posture Policy) | Block      |        60,000 |         58,560 |          1,440 | 97.60%                                | [97.47%, 97.72%]  |
| Balanced Stratified 60k | P0 (Heuristic Table 19A)             | Allow      |             0 |              0 |              0 | N/A (empty)                           | N/A               |
| Balanced Stratified 60k | P0 (Heuristic Table 19A)             | Alert      |        29,882 |              0 |         29,882 | 0.00%                                 | [0.00%, 0.01%]    |
| Balanced Stratified 60k | P0 (Heuristic Table 19A)             | Restrict   |             0 |              0 |              0 | N/A (empty)                           | N/A               |
| Balanced Stratified 60k | P0 (Heuristic Table 19A)             | Quarantine |        30,118 |         30,118 |              0 | 100.00%                               | [99.99%, 100.00%] |
| Balanced Stratified 60k | P0 (Heuristic Table 19A)             | Block      |             0 |              0 |              0 | N/A (empty)                           | N/A               |
| Balanced Stratified 60k | P1 (Default Posture Policy)          | Allow      |         7,700 |              0 |          7,700 | 0.00%                                 | [0.00%, 0.05%]    |
| Balanced Stratified 60k | P1 (Default Posture Policy)          | Alert      |        10,300 |              0 |         10,300 | 0.00%                                 | [0.00%, 0.04%]    |
| Balanced Stratified 60k | P1 (Default Posture Policy)          | Restrict   |         5,500 |          2,552 |          2,948 | 46.40%                                | [45.08%, 47.72%]  |
| Balanced Stratified 60k | P1 (Default Posture Policy)          | Quarantine |        36,500 |         27,566 |          8,934 | 75.52%                                | [75.08%, 75.96%]  |
| Balanced Stratified 60k | P1 (Default Posture Policy)          | Block      |             0 |              0 |              0 | N/A (empty)                           | N/A               |
| Balanced Stratified 60k | P2-tier (Recommended Posture Policy) | Allow      |         7,700 |              0 |          7,700 | 0.00%                                 | [0.00%, 0.05%]    |
| Balanced Stratified 60k | P2-tier (Recommended Posture Policy) | Alert      |        10,300 |              0 |         10,300 | 0.00%                                 | [0.00%, 0.04%]    |
| Balanced Stratified 60k | P2-tier (Recommended Posture Policy) | Restrict   |         5,500 |          2,552 |          2,948 | 46.40%                                | [45.08%, 47.72%]  |
| Balanced Stratified 60k | P2-tier (Recommended Posture Policy) | Quarantine |        18,500 |          9,566 |          8,934 | 51.71%                                | [50.99%, 52.43%]  |
| Balanced Stratified 60k | P2-tier (Recommended Posture Policy) | Block      |        18,000 |         18,000 |              0 | 100.00%                               | [99.98%, 100.00%] |