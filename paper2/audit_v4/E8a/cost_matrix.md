# Formal Operational Loss and Utility Matrix $\mathcal{L}(a, y)$

## 1. Specification of Decision Space and Ground Truth
In network threat response optimization, automated policies map observed continuous telemetry into discrete containment postures:
- **Decision Space $\mathcal{A}$**: $\{a_0, a_1, a_2, a_3, a_4\} = \{\text{Allow}, \text{Alert}, \text{Restrict}, \text{Quarantine}, \text{Block}\}$.
- **Ground-Truth State $\mathcal{Y}$**: $y \in \{0, 1\}$, where $y=0$ denotes legitimate network traffic (`BenignTraffic`) and $y=1$ denotes active adversarial flows (`Attack`).

---

## 2. Formal Operational Loss Matrix $\mathcal{L}(a, y)$ (10 Values)

The operational loss $\mathcal{L}(a, y)$ represents the net business and security disruption incurred when taking action $a$ given ground truth $y$:

| Action $a$ | Action Index | Operational Enforcement Mechanism | Loss on Benign $\mathcal{L}(a, 0) = c_b(a)$ (OCU) | Loss on Attack $\mathcal{L}(a, 1) = c_a(a)$ (OCU) | Net Containment Utility $\mathcal{U}(a, y)$ (OCU) |
| :--- | :---: | :--- | :---: | :---: | :---: |
| **Allow** | 0 | Unrestricted packet forwarding; nominal egress routing | $0$ | $0$ (Unmitigated Attack) | $0$ |
| **Alert** | 1 | Passive SOC SIEM log generation; zero packet delay | $+1$ | $-5$ | $+5 \cdot y - 1 \cdot (1-y)$ |
| **Restrict** | 2 | Rate-limiting bandwidth cap (10 Mbps token bucket); priority demotion | $+3$ | $-10$ | $+10 \cdot y - 3 \cdot (1-y)$ |
| **Quarantine**| 3 | Sandbox diversion; VLAN isolation; TLS MITM proxy inspection | $+15$ | $-20$ | $+20 \cdot y - 15 \cdot (1-y)$ |
| **Block** | 4 | Immediate TCP RST / drop flow; ACL blackhole filter | $+50$ | $-50$ | $+50 \cdot y - 50 \cdot (1-y)$ |

---

## 3. OCU Derivation Formula
For an evaluation stream of $N$ flows $\{(\mathbf{x}_t, y_t)\}_{t=1}^N$ under policy $\pi$:
$$\text{OCU}(\pi) = \sum_{t=1}^N \left[ y_t \cdot r_a(\pi(\mathbf{x}_t)) - (1 - y_t) \cdot c_b(\pi(\mathbf{x}_t)) \right]$$
where $r_a(a) = -\mathcal{L}(a, 1) \in \{0, 5, 10, 20, 50\}$ represents the attack containment reward, and $c_b(a) = \mathcal{L}(a, 0) \in \{0, 1, 3, 15, 50\}$ represents the benign false-positive disruption penalty.

### Parameterized Loss with Risk-Aversion Multiplier $\lambda$:
$$\text{OCU}_{\lambda}(\pi) = \sum_{t=1}^N \left[ \lambda \cdot y_t \cdot r_a(\pi(\mathbf{x}_t)) - (1 - y_t) \cdot c_b(\pi(\mathbf{x}_t)) \right]$$

---

## 4. Reconciliation of OCU Shift (~500k Difference Explained)
Reviewers comparing earlier manuscript drafts against audited results will note a numerical shift:
- **Earlier Manuscript Draft**: Reported $P_{\text{opt}} \approx +1,920,767$ OCU and $P_{2\text{-tier}} \approx +1,909,843$ OCU.
- **Audited Held-Out Test ($D_{\text{test}}$, Seed 99)**: Reports $P_{\text{opt}} = +1,439,948$ OCU and $P_{2\text{-tier}} = +1,404,974$ OCU.
- **50-Run Overall Mean**: Reports $P_{\text{opt}} = +2,052,438.1$ OCU and $P_{2\text{-tier}} = +2,027,331.5$ OCU.

### Exact Explanation of the Difference:
1. **The Cost Matrix Did NOT Change**: The loss values $\mathcal{L}(a, y)$ have remained identical across all studies (Benign penalties: $0, 1, 3, 15, 50$; Attack rewards: $0, 5, 10, 20, 50$).
2. **Shift Driven by Evaluation Regime Aggregation**:
   - In earlier drafts, the headline metric was a **50/50 dual-regime combination** between the Balanced stream (where $P_{\text{opt}}$ earned $+985,534$ OCU) and the Attack-Heavy stream (where $P_{\text{opt}}$ earned $+2,856,000$ OCU):
     $$\text{Combined OCU} = 0.5 \times 985,534 + 0.5 \times 2,856,000 = \mathbf{1,920,767 \ \text{OCU}}$$
   - In the audited revision, $+1,439,948$ OCU represents the **single-regime Balanced benchmark evaluated on the held-out test split $D_{\text{test}}$ (seed 99)**.
   - The 50-run overall mean ($+2,052,438.1$ OCU) represents the unweighted arithmetic mean across all 5 distinct operational regimes (Balanced, Attack-Heavy, Multi-State, Unstratified, Flood across 10 seeds).
   - In particular, the Volumetric Flood regime (100% attack, 60,000 attack flows) yields $+2,962,515$ OCU, which elevates the 5-regime pooled average.
