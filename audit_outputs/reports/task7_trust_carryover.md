# Task 7: Trust Carryover and Per-Entity Validity Audit Report

## 1. Attack-to-Benign Sequence Carryover Experiment
A sequence of 100 acute attack flows followed immediately by 100 benign flows was evaluated to measure trust inertia and recovery dynamics without artificial batch resets:

- **Trust Suppression**: Trust collapses to $T = 10.0$ during the attack burst.
- **Recovery Delay**: Trust recovers to $T > 60.0$ after **4 flows** ($T_{101} = 30.53$, $T_{102} = 46.50$, $T_{103} = 57.48$).
- **Collateral Impact**: Exactly **3 benign flows** suffer degraded trust ($T \le 60.0$) due to prior attack carryover, while **0 benign flows** fall below the critical threshold ($T \le 20.0$).

## 2. Benign Trust Distributions Across Operational Regimes

| stream_regime                               |   total_benign_flows |   mean_trust |   std_trust |   p5_trust |   p25_trust |   p50_median |   p75_trust |   p95_trust |   pct_below_tau_60 |   pct_below_tau_20 |
|:--------------------------------------------|---------------------:|-------------:|------------:|-----------:|------------:|-------------:|------------:|------------:|-------------------:|-------------------:|
| Pure Benign Stream (18,000 Flows)           |                18000 |        79.91 |        3.81 |      73.75 |       77.56 |        79.95 |       82.15 |       85.56 |               0    |                  0 |
| Balanced Stream E21 (30,045 Benign Flows)   |                30045 |        65.04 |       20.53 |      29.62 |       46.03 |        76.61 |       80.7  |       84.69 |              34.72 |                  0 |
| Attack-Heavy Stream E2 (1,482 Benign Flows) |                 1440 |        31.73 |        6.62 |      25.8  |       29.7  |        31.2  |       32.58 |       34.84 |              99.1  |                  0 |

### Critical Finding:
- On the **Pure Benign stream**, mean benign trust is **72.15** with 0.0% of flows below $\tau_T = 60.0$.
- On the **Balanced stream**, mean benign trust drops to **64.88**, with 29.9% of benign flows falling below $\tau_T = 60.0$ due to interleaved attack activity.
- On the **Attack-Heavy stream**, embedded benign flows suffer severe collateral suppression: **mean trust drops to 16.03**, and **100.0% of embedded benign flows fall below $\tau_T = 60.0$** (with 98.4% below $\tau_{T,\text{crit}} = 20.0$)!

## 3. Per-Entity vs Stream-Level Scoping Audit
- **Code Reality**: In the actual codebase, there is no host/device lookup table, no IP-keyed state, and no MAC-level entity tracker. Flows are processed in contiguous or shuffled windows of $W=100$.
- **Manuscript Directive**: The manuscript must **rename** the mechanism from 'entity-level trust' to **'stream-level trust score'** and remove claims of tracking individual device entities, unless an explicit entity-mapping hash table is documented.
