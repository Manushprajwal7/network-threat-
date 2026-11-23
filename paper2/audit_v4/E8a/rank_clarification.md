# Policy Rank Clarification: Static Monotonic Set vs. Decision Baselines

## 1. Explicit Scope of "Rank 1"
> [!IMPORTANT]
> **Policy $P_{\text{opt}}$ (`Allow-Allow-Restrict-Restrict-Block-Block` or `(0, 0, 0, 0, 4, 4)`) is Rank 1 strictly among the 70 admissible monotonic static posture policies ($\Pi_{70}$).**  
> It is **NOT** Rank 1 across all possible decision architectures, because standalone confidence-gated XGBoost ($P_{\text{XGB}}$) achieves higher net benefit on stationary closed-world benchmarks.

---

## 2. Global Performance Ranking on Balanced Benchmark Traffic (60,000 Flows)

| Global Rank | Decision Architecture | Paradigm | Balanced Mean OCU | 95% Confidence Interval | Block FPR | Quarantine FPR | Operational Role / Trade-off |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **1** | **$P_{\text{XGB}}$ (Confidence-Gated)** | Per-Flow Supervised Classifier ($c_t \ge 0.90$) | **1,472,830.0** | [1,469,829.8, 1,475,830.2] | 0.45% | N/A (0.00%) | **Optimal on Stationary Closed-World Benchmark**; zero temporal memory; collapses on zero-day attacks (0.33% recall on Mirai). |
| **2** | **$P_{\text{opt}}$ (Cost-Optimal)** | Monotonic Posture Mapping ($\Pi_{70}$, Rank 1) | **1,470,740.0** | [1,467,520.1, 1,473,959.9] | 0.80% | N/A (0.00%) | **Rank 1 among 70 Static Posture Policies**; eliminates quarantine disruption; vulnerable to flood false blocking. |
| **3** | **$P_{2\text{-tier}}$ (Canonical)** | 5-Action Posture Escalation ($\Pi_{70}$, Rank 9) | **1,438,976.8** | [1,435,210.4, 1,442,743.2] | 0.80% | 9.56% | Canonical reference preserving 5 distinct enforcement actions; incurs 29.9% quarantine disruption on multi-state. |
| **4** | **$P_{\text{hybrid}}$ (Hybrid Veto)** | Posture Escalation + Flow Veto ($L_4$) | **1,391,654.0** | [1,385,942.9, 1,397,365.1] | 0.72% | 9.37% | **Optimal on Volumetric Floods (+2.97M OCU) & Zero-Day LOFO (7/7 wins)**; balances macroscopic posture with microscopic flow veto. |
| **5** | **$P_{\text{XGB}}$ (Raw Ungated)** | Raw Supervised Classifier (argmax) | **1,360,450.0** | [1,354,120.0, 1,366,780.0] | **9.46%** | N/A (0.00%) | **Violates Availability SLAs** (blocks 2,827 legitimate connections). |
| **6** | **$P_1$ (Heuristic Default)** | Heuristic Manual Policy ($\Pi_{70}$, Rank 44) | **529,292.5** | [524,100.2, 534,484.8] | 0.00% | 10.36% | Overly conservative baseline; maps $L_4$ to Quarantine, sacrificing containment utility. |

*Footnote on Flood Regime*: In pure volumetric flood saturation (100% attack, 60,000 flows), benign flows are completely absent ($N_{\text{benign}}=0$). Consequently, OCU in the flood regime reflects strictly the attack-block reward ($60,000 \times 50 = 3,000,000$ theoretical maximum), and Block FPR is mathematically undefined ($0/0 = \text{N/A}$).
