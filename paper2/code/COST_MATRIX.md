# Operational Cost Matrix Justification

This document formalizes the unitless operational cost matrix used in Objective 3 for Cost-Aware Policy Optimization and Action Precision Audit in compliance with peer-review standards for IEEE Internet of Things Journal / Computers & Security.

---

## 1. Cost Matrix Formulation

Unitless operational costs are assigned to each \((\text{Action}, \text{True Label})\) pair. These costs reflect relative operational preferences, risk severity, and analyst overhead rather than arbitrary currency values.

| Enforcement Action | True Benign ($y = 0$) | True Attack ($y = 1$) | Operational Rationale |
| :--- | :---: | :---: | :--- |
| **Allow** | **0** | **+100** | **Benign**: Correct operational pass-through with zero friction.<br>**Attack**: Worst-case outcome (false negative). Attack traverses network unimpeded, causing unmitigated data exfiltration, lateral movement, or service disruption. |
| **Alert** | **+1** | **-5** | **Benign**: Minor analyst triage overhead (reviewing a benign log event).<br>**Attack**: Attack detected in non-blocking monitoring mode. Provides security visibility and audit trails, though traffic is not throttled. |
| **Restrict** | **+3** | **-10** | **Benign**: Mild user/device friction (e.g., bandwidth rate-limiting, QoS deprioritization).<br>**Attack**: Active attack throughput throttled, partially impeding adversary progression while preserving forensic collection. |
| **Quarantine** | **+15** | **-20** | **Benign**: Moderate operational disruption. Host/device isolated to sandbox VLAN; requires administrative validation and manual release.<br>**Attack**: Attack actively contained before damaging core infrastructure or propagating across network boundaries. |
| **Block** | **+50** | **-50** | **Benign**: Severe disruption (false positive). Critical device dropped from network, causing service downtime, potential SLA breaches, or data pipeline interruption.<br>**Attack**: Host completely terminated at edge router/firewall. Maximum threat mitigation and complete risk neutralization. |

---

## 2. Mathematical Optimization Objective

Let $\mathcal{A} = \{\text{Allow}, \text{Alert}, \text{Restrict}, \text{Quarantine}, \text{Block}\}$ denote the set of enforcement actions, and $y_i \in \{0, 1\}$ denote the ground-truth label of flow $i$ (0 for Benign, 1 for Attack).

Given a policy $\pi: \text{Flow}_i \to a_i \in \mathcal{A}$, the total expected operational cost across an evaluation cohort of $N$ flows is:

$$\mathcal{C}(\pi) = \sum_{i=1}^N \mathcal{L}(a_i, y_i)$$

where $\mathcal{L}(a, y)$ is the cost lookup function defined in the matrix above.

The average expected cost per flow is:

$$\bar{\mathcal{C}}(\pi) = \frac{1}{N} \mathcal{C}(\pi)$$

Negative values indicate net operational benefit (where the value of mitigating active attacks outweighs false-positive disruption costs). Policies that achieve lower total cost $\mathcal{C}(\pi)$ deliver superior operational utility.

---

## 3. Structural Constraints on Policy Optimization

To prevent unprincipled or degenerate policies during level-to-action optimization:
1. **Severity Monotonicity**:
   $$\text{Severity}(a(L_0)) \le \text{Severity}(a(L_1)) \le \text{Severity}(a(L_2)) \le \text{Severity}(a(L_3)) \le \text{Severity}(a(L_4)) \le \text{Severity}(a(L_5))$$
   where $\text{Severity}(\text{Allow}) < \text{Severity}(\text{Alert}) < \text{Severity}(\text{Restrict}) < \text{Severity}(\text{Quarantine}) < \text{Severity}(\text{Block})$.
2. **Operational Safety Constraint**:
   $$\text{FPR}_{\text{Block}} = \frac{\sum_{i: y_i = 0} \mathbb{I}(a_i = \text{Block})}{\sum_{i: y_i = 0} 1} \le 5.0\%$$
   Ensures that aggressive blocking policies do not jeopardize normal network operations.
