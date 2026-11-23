# Formal Operational Loss and Utility Matrix $\mathcal{L}(a, y)$

## 1. Specification of Decision Space and Ground Truth

In network threat response optimization, automated policies map observed continuous telemetry into discrete containment postures:
- **Decision Space $\mathcal{A}$**: $\{a_0, a_1, a_2, a_3, a_4\} = \{\text{Allow}, \text{Alert}, \text{Restrict}, \text{Quarantine}, \text{Block}\}$.
- **Ground-Truth State $\mathcal{Y}$**: $y \in \{0, 1\}$, where $y=0$ denotes legitimate network traffic (`BenignTraffic`) and $y=1$ denotes active adversarial flows (`Attack`).

---

## 2. Formal Operational Loss Matrix $\mathcal{L}(a, y)$

The operational loss $\mathcal{L}(a, y)$ represents the net business and security disruption incurred when taking action $a$ given ground truth $y$:

| Action $a$ | Action Index | Operational Enforcement Mechanism | Loss on Benign $\mathcal{L}(a, 0) = c_b(a)$ | Loss on Attack $\mathcal{L}(a, 1) = c_a(a)$ | Net Containment Utility $\mathcal{U}(a, y)$ |
| :--- | :---: | :--- | :---: | :---: | :---: |
| **Allow** | 0 | Unrestricted packet forwarding; nominal egress routing | $0$ | $0$ (Unmitigated Attack) | $0$ |
| **Alert** | 1 | Passive SOC SIEM log generation; zero packet delay | $+1$ | $-5$ | $+5 \cdot y - 1 \cdot (1-y)$ |
| **Restrict** | 2 | Rate-limiting bandwidth cap (10 Mbps token bucket); priority demotion | $+3$ | $-10$ | $+10 \cdot y - 3 \cdot (1-y)$ |
| **Quarantine**| 3 | Sandbox diversion; VLAN isolation; TLS MITM proxy inspection | $+15$ | $-20$ | $+20 \cdot y - 15 \cdot (1-y)$ |
| **Block** | 4 | Immediate TCP RST / drop flow; ACL blackhole filter | $+50$ | $-50$ | $+50 \cdot y - 50 \cdot (1-y)$ |

---

## 3. Net Operational Containment Utility (OCU)

For an evaluation stream of $N$ flows $\{(\mathbf{x}_t, y_t)\}_{t=1}^N$ under policy $\pi$:
$$\text{OCU}(\pi) = \sum_{t=1}^N \left[ y_t \cdot (-c_a(\pi(\mathbf{x}_t))) - (1 - y_t) \cdot c_b(\pi(\mathbf{x}_t)) \right]$$

### Parameterized Loss with Risk-Aversion Multiplier $\lambda$:
$$\text{OCU}_{\lambda}(\pi) = \sum_{t=1}^N \left[ \lambda \cdot y_t \cdot (-c_a(\pi(\mathbf{x}_t))) - (1 - y_t) \cdot c_b(\pi(\mathbf{x}_t)) \right]$$
where $\lambda$ represents the marginal value of attack containment relative to benign service disruption.
