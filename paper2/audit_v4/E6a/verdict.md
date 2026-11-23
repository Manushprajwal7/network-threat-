# Leave-One-Family-Out (LOFO) Novel Attack Evaluation: Coverage Analysis

**Date**: 2026-11-18  
**Evaluation Scope**: 7 Top-Level Attack Families in CICIoT2023 tested under strict hold-out retraining  
**Key Framing Requirement**: **27.42% recall is NOT containment. It represents materially improved coverage of held-out families relative to supervised classifiers, but absolute recall remains bounded.**

---

## 1. Summary of LOFO Empirical Findings

Across all seven held-out threat families:
1. **Classifier Recall Collapse**: Supervised model $P_{\text{XGB}}$ relies entirely on closed-world learned boundaries. When an unencountered attack family arrives, predictions fall into low-confidence regions ($c_t < 0.90$) or map to benign classes. Recall drops to:
   - Mirai Botnet: **0.33% recall** ($850$ net OCU)
   - Web Attacks: **1.33% recall** ($400$ net OCU)
   - Spoofing (ARP/DNS): **1.69% recall** ($10,000$ net OCU)
   - BruteForce (Dictionary): **1.00% recall** ($100$ net OCU)
2. **Multi-Stage Posture Resilience**: By combining unsupervised Isolation Forest anomaly telemetry with causal ADTM trust degradation, posture escalation achieves active coverage across all 7 families:
   - Mirai Botnet: **27.42% attack recall** ($+178,713$ net OCU, a 210-fold increase over $P_{\text{XGB}}$)
   - Reconnaissance: **23.91% attack recall** ($+93,125$ net OCU vs $+58,950$ for $P_{\text{XGB}}$)
   - Web Exploits: **9.83% attack recall** ($+3,768$ net OCU vs $+400$ for $P_{\text{XGB}}$)
3. **Posture Policies Win in 7 of 7 Folds on Net OCU**:
   - DDoS: Posture wins ($554,938$ vs $497,100$ OCU)
   - DoS: Posture wins ($693,781$ vs $673,900$ OCU)
   - Mirai: Posture wins ($178,713$ vs $850$ OCU)
   - Recon: Posture wins ($93,125$ vs $58,950$ OCU)
   - Web: Posture wins ($3,768$ vs $400$ OCU)
   - Spoofing: Posture wins ($72,480$ vs $10,000$ OCU)
   - BruteForce: Posture wins ($1,453$ vs $100$ OCU)

---

## 2. Rigorous Framing and Limitations
- While posture escalation substantially outperforms $P_{\text{XGB}}$ across novel threats, an attack recall of 27.42% leaves $\approx 72.58\%$ of Mirai flows unmitigated.
- Therefore, we explicitly **refrain from claiming "zero-day containment"**. Instead, we state:  
  *`"Multi-stage posture provides materially better coverage of novel held-out attack families where pure supervised classifiers experience catastrophic failure (27.42% vs 0.33% recall on Mirai), though absolute recall on stealthy application attacks remains bounded without domain signatures."`*
