# Security Framework Threshold Justifications

This document provides formal methodological justifications for each threshold used in the Multi-Signal Evidence State Machine (Levels L0–L5) in compliance with peer-review standards for IEEE Internet of Things Journal / Computers & Security.

---

## 1. Topologically Aware Risk Propagation (TARP) Thresholds

### $\text{TARP} \ge 0.42$ (Contextual Elevation Threshold)
- **Source**: Inherited directly from Section 3.4 & Section 5.8 of the published baseline manuscript.
- **Justification**: Across the empirical 120-node IoT communication graph ($|V|=120, |E|=342$), the mean propagated contextual node risk is exactly $\bar{R} = 0.4200$. Nodes and communicating entities exhibiting $R_i \ge 0.4200$ represent entities operating above average topological threat exposure. In the 60,000 evaluation window, 11,500 samples (19.17%) originate from entities attached to nodes meeting or exceeding this threshold.

### $\text{TARP} \ge 0.75$ (Critical Topology Isolation Threshold)
- **Source**: Inherited from Section 3.4 of the published manuscript.
- **Justification**: Denotes the critical boundary established in the published topology risk taxonomy ($R_i \ge 0.75$). Exactly 8 critical hub nodes (6.67% of the topology) exceed this threshold, representing central routing nodes whose compromise poses immediate network-wide systemic risk.

---

## 2. Adaptive Dynamic Trust Management (ADTM) Thresholds

All trust thresholds are strictly inherited from the calibrated trust quantization taxonomy defined in Table 9 and Table 18 of the published baseline paper:

| Trust Band | Score Range | Operational Meaning | Framework Threshold |
| :--- | :---: | :--- | :---: |
| **High Trust** | $80 - 100$ | Normal verified operational posture | Baseline ($\text{Trust} > 60$) |
| **Moderate Trust** | $60 - 79$ | Minor behavioral degradation / topological risk | $\text{Trust} \le 60$ (Signal 3) |
| **Low Trust** | $40 - 59$ | Significant behavioral anomaly accumulation | $\text{Trust} \le 40$ |
| **Very Low Trust** | $20 - 39$ | Severe compromise indicators | $\text{Trust} \le 20$ (L4 containment prerequisite) |
| **Critical Trust** | $0 - 19$ | Active multi-vector attack execution | $\text{Trust} \le 10$ |

- **$\text{Trust} \le 60$**: Marks the transition from High/Moderate Trust into the Low Trust regime. In the baseline evaluation cohort, 6,068 flows cross below 60.0.
- **$\text{Trust} \le 40$ & $\text{Trust} \le 20$**: Unreached in the baseline reconstruction due to positive baseline offsets ($\alpha \cdot S_U + \beta \cdot S_D \approx 53.75$), correctly isolating L4/L5 in baseline evaluation and empirically motivating the Objective 2 recalibration.

---

## 3. Machine Learning & Anomaly Detection Thresholds (Validation-Derived)

Both thresholds were validated on the independent partition of **1,176,851 samples** (`validation.csv`) from CICIoT2023.

### Anomaly Score $\tau_{\text{anom}} \ge 0.90$ (Screening Threshold)
- **Empirical Validation**: See [`paper2/tables/E1_1_anomaly_threshold_justification.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/tables/E1_1_anomaly_threshold_justification.csv).
- **Trade-off Analysis**:
  - At $\tau = 0.80$: Recall is $94.65\%$, but FPR is unacceptably high at $18.42\%$ (excessive alert fatigue).
  - At $\tau = 0.85$: Recall is $89.80\%$, with FPR at $12.15\%$.
  - **At $\tau = 0.90$ (Selected)**: Achieves the Pareto-optimal trade-off where **$\text{FPR} \le 10\%$ ($6.84\%$)** while sustaining high attack sensitivity with **$\text{Recall} \ge 85\%$ ($85.32\%$)** and precision of $99.41\%$.
  - At $\tau = 0.95$: Recall sharply drops to $62.45\%$ (37.55% false negatives).

### Classifier Confidence $\tau_{\text{conf}} \ge 0.95$ (Containment Confirmation)
- **Empirical Validation**: See [`paper2/tables/E1_1_conf_threshold_justification.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/tables/E1_1_conf_threshold_justification.csv).
- **Trade-off Analysis**:
  - At $\tau = 0.90$: Precision is $99.94\%$ with coverage of $97.92\%$.
  - **At $\tau = 0.95$ (Selected)**: Guarantees near-perfect attack precision of **$99.96\%$** across attack classes while preserving extensive sample coverage ($97.50\%$).
  - Prevents premature containment triggered by ambiguous model predictions.

---

## 4. Entity Aggregation Semantics

- **Aggregation Window**: 100 contiguous network flows per entity (600 entities across the 60,000 evaluation window).
- **Operational Reality**: In operational network environments, intrusion assessment is conducted per host/device entity over aggregated micro-windows rather than per isolated packet.
- **Cumulative Evidence Score $S$**:
  $$S = \mathbb{I}(\text{TARP} \ge 0.42) + \mathbb{I}(\text{trust} \le 60.0) + \mathbb{I}(\text{Anom\_Rate} \ge 0.28) + \mathbb{I}(\text{Conf\_Attack\_Rate} \ge 0.98)$$
  Ensures that higher security tiers represent strictly monotonic accumulations of corroborating threat evidence across orthogonal sensors.

### 4.1 Entity-Level Aggregation Thresholds

Entity thresholds = 75th percentile of validation-set entity distribution (top quartile of anomalous activity).

Entity-level anomaly and confidence thresholds are calibrated per evaluation window: for attack-heavy windows, 0.28/0.26 (75th percentile of attack-heavy validation); for balanced windows, 0.55/0.55 (75th percentile of balanced validation). This reflects operational reality: the threshold regime depends on whether the deployment is under active attack (window-tuned) or in mixed operation (balanced-tuned). Operators would select the regime based on their operational context.

Evaluated across the independent partition of 11,768 host entities (1,176,800 validation flows):

| Metric | 50th Percentile | 75th Percentile (Selected) | 90th Percentile | 95th Percentile | Operational Meaning |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **$\text{Anom\_Rate}$ ($\ge 0.90$)** | 25.00% | **28.00%** | 31.00% | 33.00% | Top quartile of behavioral anomaly concentration. |
| **$\text{Conf\_Attack\_Rate}$ ($\ge 0.95$)** | 96.00% | **98.00%** | 99.00% | 99.00% | Top quartile of validated high-confidence attack execution. |

- **$\tau_{\text{Anom\_Rate}} = 0.2800$**: Identifies entities whose proportion of anomalous flows ($\tau \ge 0.90$) places them in the top quartile (75th percentile) of entity-level anomaly density.
- **$\tau_{\text{Conf\_Attack\_Rate}} = 0.9800$**: Identifies entities whose proportion of confirmed attack flows ($\tau \ge 0.95$) reaches the top quartile (75th percentile) of high-confidence attack activity.


---

## 5. Objective 2 Trust Recalibration Formulations

### Family-Aware Initial Priors (Intervention 1)
"Family-aware priors derive initial trust per class from the class's empirical benign-likelihood in the training set. $\lambda_{\text{prior}} = 0.55$, chosen to produce ~30-point spread across families. This provides a more realistic prior than uniform $T_0 = 100$."
Formulation:
$$T_0(\text{BenignTraffic}) = 100.0$$
$$T_0(c) = 100.0 - 0.55 \cdot (100.0 - p_{\text{benign}}(c))$$
where $p_{\text{benign}}(c)$ is the mean XGBoost $P(\text{benign})$ predicted for class $c$ in the training set.

### Hard Reset on Confirmed Attacks (Intervention 2)
$$
\text{if } \text{conf}_t \ge 0.95 \land \text{pred}_t \ne \text{Benign} \land \text{anom}_t \ge 0.90 \text{ for 2 consecutive samples}:
$$
$$T = 20.0 \quad (\text{locked for 200 samples})$$

### Adaptive EWMA Decay (Intervention 3)
"Adaptive EWMA decays trust faster for high-severity families and slower for benign traffic, preventing benign jitter from destabilizing entity trust."
Formulation:
$$T_{\text{next}} = \alpha_{\text{family}} \cdot T_{\text{obs}} + (1 - \alpha_{\text{family}}) \cdot T_{\text{prev}}$$
where:
- $\alpha_{\text{family}} = 0.50$ for high-severity (DDoS, DoS, Mirai)
- $\alpha_{\text{family}} = 0.30$ for mid-severity (Spoofing, Web-based, Brute-force)
- $\alpha_{\text{family}} = 0.15$ for low-severity (Reconnaissance)
- $\alpha_{\text{family}} = 0.05$ for BenignTraffic
