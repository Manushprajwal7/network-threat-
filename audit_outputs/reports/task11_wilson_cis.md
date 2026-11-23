# Task 11: Statistical CI Reconciliation Report

## 1. Mathematical Framework for Non-Degenerate Wilson Intervals
For an observed proportion $\hat{p} = k / n$ under sample size $n$ with standard normal critical value $z = 1.95996$ (95% confidence):

$$\tilde{p} = \frac{k + z^2 / 2}{n + z^2}, \quad \text{Margin} = \frac{z}{n + z^2} \sqrt{\frac{k(n-k)}{n} + \frac{z^2}{4}}$$
$$\text{CI}_{95\%} = [\max(0, \tilde{p} - \text{Margin}), \min(1, \tilde{p} + \text{Margin})]$$

### Boundary Behavior:
- **Zero Observed Rate ($k = 0$)**: The Wilson interval yields $[0.00\%, \frac{z^2}{n + z^2} \times 100\%]$. For $n = 7,700$ (Table 6 Allow), $\text{CI} = [0.00\%, 0.05\%]$. For $n = 29,882$ (Table 9 Benign Block), $\text{CI} = [0.00\%, 0.013\%]$.
- **Perfect Rate ($k = n$)**: The Wilson interval yields $[(1 - \frac{z^2}{n + z^2}) \times 100\%, 100.00\%]$. For $n = 18,000$ (Table 6 Block), $\text{CI} = [99.98\%, 100.00\%]$. For $n = 1$ (Malware Block), $\text{CI} = [20.65\%, 100.00\%]$.

## 2. Master Wilson CI Reconciliation Table

| Table                                | Item                                |   k_numerator |   n_denominator | formatted_string          |
|:-------------------------------------|:------------------------------------|--------------:|----------------:|:--------------------------|
| Table 5 (Attack-Heavy Posture)       | Posture L0 Attack Density           |             0 |               0 | N/A (empty)               |
| Table 5 (Attack-Heavy Posture)       | Posture L1 Attack Density           |             0 |               0 | N/A (empty)               |
| Table 5 (Attack-Heavy Posture)       | Posture L2 Attack Density           |             0 |               0 | N/A (empty)               |
| Table 5 (Attack-Heavy Posture)       | Posture L3 Attack Density           |             0 |               0 | N/A (empty)               |
| Table 5 (Attack-Heavy Posture)       | Posture L4 Attack Density           |         58560 |           60000 | 97.60% [97.47%, 97.72%]   |
| Table 5 (Attack-Heavy Posture)       | Posture L5 Attack Density           |             0 |               0 | N/A (empty)               |
| Table 6 (Balanced Posture)           | Posture L0 Attack Density           |             0 |            7700 | 0.00% [0.00%, 0.05%]      |
| Table 6 (Balanced Posture)           | Posture L1 Attack Density           |             0 |           10300 | 0.00% [0.00%, 0.04%]      |
| Table 6 (Balanced Posture)           | Posture L2 Attack Density           |          2552 |            5500 | 46.40% [45.09%, 47.72%]   |
| Table 6 (Balanced Posture)           | Posture L3 Attack Density           |          9566 |           18500 | 51.71% [50.99%, 52.43%]   |
| Table 6 (Balanced Posture)           | Posture L4 Attack Density           |         18000 |           18000 | 100.00% [99.98%, 100.00%] |
| Table 6 (Balanced Posture)           | Posture L5 Attack Density           |             0 |               0 | N/A (empty)               |
| Table 7 (Action Prevalence P2-tier)  | Action Allow Attack Prevalence      |             0 |            7700 | 0.00% [0.00%, 0.05%]      |
| Table 7 (Action Prevalence P2-tier)  | Action Alert Attack Prevalence      |             0 |           10300 | 0.00% [0.00%, 0.04%]      |
| Table 7 (Action Prevalence P2-tier)  | Action Restrict Attack Prevalence   |          2552 |            5500 | 46.40% [45.09%, 47.72%]   |
| Table 7 (Action Prevalence P2-tier)  | Action Quarantine Attack Prevalence |          9566 |           18500 | 51.71% [50.99%, 52.43%]   |
| Table 7 (Action Prevalence P2-tier)  | Action Block Attack Prevalence      |         18000 |           18000 | 100.00% [99.98%, 100.00%] |
| Table 9 (Per-Family P2-tier Actions) | Benign -> Allow                     |          7700 |           29882 | 25.8% [25.3%, 26.3%]      |
| Table 9 (Per-Family P2-tier Actions) | Benign -> Alert                     |         10300 |           29882 | 34.5% [33.9%, 35.0%]      |
| Table 9 (Per-Family P2-tier Actions) | Benign -> Restrict                  |          2948 |           29882 | 9.9% [9.5%, 10.2%]        |
| Table 9 (Per-Family P2-tier Actions) | Benign -> Quarantine                |          8934 |           29882 | 29.9% [29.4%, 30.4%]      |
| Table 9 (Per-Family P2-tier Actions) | Benign -> Block                     |             0 |           29882 | 0.0% [0.0%, 0.0%]         |
| Table 9 (Per-Family P2-tier Actions) | DDoS -> Restrict                    |          1908 |           22424 | 8.5% [8.2%, 8.9%]         |
| Table 9 (Per-Family P2-tier Actions) | DDoS -> Quarantine                  |          7108 |           22424 | 31.7% [31.1%, 32.3%]      |
| Table 9 (Per-Family P2-tier Actions) | DDoS -> Block                       |         13408 |           22424 | 59.8% [59.1%, 60.4%]      |
| Table 9 (Per-Family P2-tier Actions) | DoS -> Restrict                     |           448 |            5328 | 8.4% [7.7%, 9.2%]         |
| Table 9 (Per-Family P2-tier Actions) | DoS -> Quarantine                   |          1668 |            5328 | 31.3% [30.1%, 32.6%]      |
| Table 9 (Per-Family P2-tier Actions) | DoS -> Block                        |          3212 |            5328 | 60.3% [59.0%, 61.6%]      |
| Table 9 (Per-Family P2-tier Actions) | Mirai -> Restrict                   |           150 |            1788 | 8.4% [7.2%, 9.8%]         |
| Table 9 (Per-Family P2-tier Actions) | Mirai -> Quarantine                 |           598 |            1788 | 33.4% [31.3%, 35.7%]      |
| Table 9 (Per-Family P2-tier Actions) | Mirai -> Block                      |          1040 |            1788 | 58.2% [55.9%, 60.4%]      |
| Table 9 (Per-Family P2-tier Actions) | Spoofing -> Restrict                |            32 |             322 | 9.9% [7.1%, 13.7%]        |
| Table 9 (Per-Family P2-tier Actions) | Spoofing -> Quarantine              |           113 |             322 | 35.1% [30.1%, 40.5%]      |
| Table 9 (Per-Family P2-tier Actions) | Spoofing -> Block                   |           177 |             322 | 55.0% [49.5%, 60.3%]      |
| Table 9 (Per-Family P2-tier Actions) | Recon -> Restrict                   |            26 |             235 | 11.1% [7.7%, 15.7%]       |
| Table 9 (Per-Family P2-tier Actions) | Recon -> Quarantine                 |            82 |             235 | 34.9% [29.1%, 41.2%]      |
| Table 9 (Per-Family P2-tier Actions) | Recon -> Block                      |           127 |             235 | 54.0% [47.7%, 60.3%]      |
| Table 9 (Per-Family P2-tier Actions) | Web -> Quarantine                   |             2 |              15 | 13.3% [3.7%, 37.9%]       |
| Table 9 (Per-Family P2-tier Actions) | Web -> Block                        |            13 |              15 | 86.7% [62.1%, 96.3%]      |
| Table 9 (Per-Family P2-tier Actions) | BruteForce -> Quarantine            |             2 |               5 | 40.0% [11.8%, 76.9%]      |
| Table 9 (Per-Family P2-tier Actions) | BruteForce -> Block                 |             3 |               5 | 60.0% [23.1%, 88.2%]      |
| Table 9 (Per-Family P2-tier Actions) | Malware -> Block                    |             1 |               1 | 100.0% [20.7%, 100.0%]    |