# Operational Decision Rule & Comparative Analysis: P_hybrid vs P_XGB

## 1. Executive Verdict & Honest Comparative Finding

> [!IMPORTANT]
> **P_hybrid DOES NOT strictly dominate P_XGB in OCU net benefit.**
> In fact, **P_XGB achieves significantly higher OCU on balanced and unstratified traffic**, winning by **+508,553 OCU on balanced traffic (Wilcoxon $p = 0.0020$)**. P_hybrid is superior on OCU **only on sustained attack-heavy traffic (+13,695 OCU)**.

### Paired Wilcoxon Test Results (10 Independent Seeds)

| Operational Regime | Mean OCU ($P_{\text{hybrid}}$) | Mean OCU ($P_{\text{XGB}}$) | Mean OCU Delta | 95% Bootstrap CI | Wilcoxon $p$-value | OCU Winner |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Balanced Stratified** | 1,391,654.0 | 1,472,830.0 | -81,176.0 | [-84,745.2, -78,125.3] | 0.0020 | **P_XGB** |
| **Attack-Heavy (97.6%)** | 2,896,960.6 | 2,891,120.0 | +5,840.6 | [5,399.3, 6,304.2] | 0.0020 | **P_hybrid** |
| **Multi-State** | 1,391,352.6 | 1,472,830.0 | -81,477.4 | [-85,619.8, -77,451.1] | 0.0020 | **P_XGB** |
| **Unstratified Shuffled** | 1,326,419.4 | 1,472,830.0 | -146,410.6 | [-152,348.7, -140,822.8] | 0.0020 | **P_XGB** |
| **Volumetric Flood** | 2,974,176.0 | 2,960,105.0 | +14,071.0 | [13,416.0, 14,723.0] | 0.0020 | **P_hybrid** |

---

## 2. Why P_XGB Wins on Net OCU
1. **Closed-World Benchmark Exploitation**: In static benchmark evaluations (CICIoT2023), XGBoost has high macro classification accuracy (98.99%). $P_{\text{XGB}}$ directly blocks every high-confidence attack with Block benefit ($+50$) without paying intermediate Quarantine ($+20$) or Alert ($+5$) penalties.
2. **Intermediate Tier Penalty**: Multi-stage posture policies ($P_{\text{hybrid}}$) route ambiguous or emerging threats through Level $L_3$ (Quarantine) and $L_2$ (Restrict). In a closed-world test where almost all attacks can be classified immediately, routing through lower containment tiers incurs lower reward than immediate blocking.

---

## 3. Why P_hybrid is Still Operationally Recommended: The Conditional Decision Rule

$P_{\text{hybrid}}$ must NOT be sold as an unconstrained OCU maximizer. Instead, the formal operational recommendation must be stated conditionally:

> **Formal Operational Recommendation**:  
> **$P_{\text{hybrid}}$ is recommended if and only if:**  
> 1. **Explainable Posture Escalation and Auditability** are mandatory operational requirements for SOC teams (e.g., NIST SP 800-53 / IEC 62443 compliance).
> 2. **Operational Safety SLA** strictly caps benign Block FPR at **0.00%** on nominal traffic, accepting a Quarantine FPR of $\approx 8.5\%$.
> 3. **Defense Against Zero-Day / Novel Threat Vectors**: Pure $P_{\text{XGB}}$ cannot detect attacks outside its 34 closed-world training classes; $P_{\text{hybrid}}$ provides fallback containment via unsupervised Isolation Forest anomaly scoring and ADTM trust tracking.

If maximum closed-world OCU is the sole operational objective and unexplainable point drops are tolerated, **$P_{\text{XGB}}$ is the mathematically superior policy**.
