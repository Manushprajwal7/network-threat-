# Leave-One-Family-Out (LOFO) Novel Threat Evaluation: Framing and Verdict

### Core Empirical Findings:
1. **Multi-Stage Posture Wins 7 of 7 Folds on Net OCU**: Across all 7 unencountered attack families, posture escalation ($P_{\text{hybrid}}$ and $P_{\text{opt}}$) achieves higher net operational benefit than pure confidence-gated $P_{\text{XGB}}$.
2. **Catastrophic Collapse of Supervised Models**: On Mirai IoT botnet traffic, $P_{\text{XGB}}$ recall drops to **0.33%** (+850 net OCU), because unseen classes produce softmax probabilities below $\tau_C = 0.90$. In contrast, multi-stage posture leverages the clean Isolation Forest and ADTM trust decay to achieve **27.42% recall and +178,713 net OCU** (a 210-fold gain in net utility).

### Non-Negotiable Framing Boundary:
- **27.42% Recall is NOT "Containment"**: Approximately 72.58% of Mirai flows escape mitigation. Calling this "containment" is scientifically invalid.
- **Accurate Terminology**: Multi-stage posture provides **materially superior novel held-out family coverage and defense-in-depth**, but absolute recall on stealthy application attacks remains strictly bounded.
