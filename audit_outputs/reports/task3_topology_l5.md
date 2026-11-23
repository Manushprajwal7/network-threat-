# Task 3: Topology and Level L5 Audit Report

## 1. Scale-Free Synthetic Topology Audit
The 120-node synthetic network generates a Barabási-Albert scale-free graph ($m=2$, seed 42) with PageRank centrality mapped to continuous risk scores $R \in [0.10, 0.90]$.

- **Mean Risk $\mu_R$**: 0.4189 (Target 0.4200)
- **Standard Deviation $\sigma_R$**: 0.0721 (Target 0.0800)
- **5th / 50th / 95th Percentiles**: 0.3859 / 0.3905 / 0.5014
- **Core Hub Nodes ($R \ge 0.75$)**: Exactly **2 nodes** (Node IDs: `[0, 4]`). Node 0 ($R = 0.9000$) and Node 4 ($R = 0.8089$) represent primary high-centrality SDN switches.

## 2. Statistical Z-Score Recomputation for Edge Batches
When peripheral edge-gateway batches ($W=100$) are monitored:
- **Individual Flow / Node Z-Score**: $Z = \frac{0.75 - 0.42}{0.08} = \mathbf{4.125\sigma}$ ($p = 1.854e-05$).
- **Batch-Mean Standard Error**: $\text{SE}(\bar{R}) = \frac{\sigma_R}{\sqrt{100}} = \frac{0.08}{10} = \mathbf{0.0080}$.
- **Batch-Mean Z-Score**: $Z = \frac{0.75 - 0.42}{0.008} = \mathbf{41.25\sigma}$ ($p = 0.000e+00 \approx 10^{-372}$).
This mathematically proves that peripheral edge batches can **never** breach the $\tau_{R,\text{hub}} = 0.75$ boundary to reach Level L5.

## 3. E8 Core-Hub Benign Control & Manuscript Correction
Under the 100,000-flow benign core-hub control (clean benign traffic traversing high-centrality Node 0):
- **Actual Posture Level**: **100% of benign batches populate Level L1 (Observation)** (100,000 / 100,000 flows).
- **Correction to Manuscript**: The claim that benign core-hub traffic remains 'locked at L0' is **empirically disproven**. Because $R = 0.90 \ge 0.42$, the topological signal $c_{\text{topo}} = 1$ is actively triggered, which sets $S = 1$, placing benign core-hub traffic into **Level L1 (Observation)**. Crucially, under policy P2-tier, Level L1 maps to **Alert**, resulting in **0.00% Block FPR and 0.00% Quarantine FPR** (zero service disruption).

### E8 Level Distribution Table

| posture_level   |   benign_control_flows |   benign_control_pct |   attack_experiment_flows |   attack_experiment_pct | assigned_p2_action   |
|:----------------|-----------------------:|---------------------:|--------------------------:|------------------------:|:---------------------|
| L0              |                      0 |                    0 |                         0 |                       0 | Allow                |
| L1              |                 100000 |                  100 |                         0 |                       0 | Alert                |
| L2              |                      0 |                    0 |                         0 |                       0 | Restrict             |
| L3              |                      0 |                    0 |                         0 |                       0 | Quarantine           |
| L4              |                      0 |                    0 |                         0 |                       0 | Block                |
| L5              |                      0 |                    0 |                    100000 |                     100 | Block                |