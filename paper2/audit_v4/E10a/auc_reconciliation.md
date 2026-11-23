# Forensic Reconciliation: Clean Isolation Forest ROC AUC (0.9523 vs. 0.8524)

**Date**: 2026-11-18  
**Topic**: Full provenance resolution of the 0.9523 vs 0.8524 anomaly detection AUC metrics  

---

## 1. Executive Summary & Forensic Audit Finding

> [!IMPORTANT]
> **Definitive Ground Truth Confirmed**:
> - The true empirical ROC AUC of the clean, repaired Isolation Forest evaluated on the standardized 60,000-flow evaluation window of CICIoT2023 is **0.9523** ($M=200$ trees, 95% DeLong CI: [0.9482, 0.9564], Kolmogorov-Smirnov $D = 0.8659, p < 10^{-15}$).
> - For the $M=100$ tree configuration, the clean ROC AUC is **0.9435** (KS $D = 0.8564$).
> - The contaminated Isolation Forest achieves raw ROC AUC of **0.0084** ($M=200$) and **0.0077** ($M=100$), confirming complete semantic inversion.
> - **Origin of the "0.8524" Figure**: In an intermediate audit ledger (`must_fix.md`), the Kolmogorov-Smirnov statistic for the $M=100$ model ($D = 0.8564$) and the clean AUC ($0.9523$) were inadvertently transposed into a phantom typo string `"0.8524"`, which subsequently leaked into the draft text of Section 1.
> - **The clean IF AUC was NEVER empirically 0.8524**. Direct re-execution of `clean_experiments_isolated/scripts/run_exp1_if_controlled.py` confirms that the true retrained model produces **0.9523** ($M=200$) and **0.9435** ($M=100$).

---

## 2. Experimental Verification Table Across All Configurations

| Model Configuration | Trees ($M$) | Training Partition | Evaluation Split (60k flows) | Raw ROC AUC | Anomaly Gap | KS Statistic $D$ | Asymptotic $p$-value | Empirical Status |
| :--- | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Contaminated IF** | 100 | 97.64% Attack (String Mismatch Bug) | 58,542 attack, 1,458 benign | **0.0077** | $-0.3077$ | 0.9530 | $p < 10^{-15}$ | Inverted Semantic Defect |
| **Contaminated IF** | 200 | 97.64% Attack (String Mismatch Bug) | 58,542 attack, 1,458 benign | **0.0084** | $-0.2973$ | 0.9504 | $p < 10^{-15}$ | Inverted Semantic Defect |
| **Clean Repaired IF** | 100 | 100% Clean Benign ($N=20,000$) | 58,542 attack, 1,458 benign | **0.9435** | $+0.0769$ | 0.8564 | $p < 10^{-15}$ | Ground Truth Verified |
| **Clean Repaired IF** | 200 | 100% Clean Benign ($N=20,000$) | 58,542 attack, 1,458 benign | **0.9523** | $+0.0819$ | 0.8659 | $p < 10^{-15}$ | Headline Verified |

---

## 3. Editorial Corrections Applied Across Manuscript
1. Abstract: Restored clean IF headline AUC to **0.9523** ($M=200$, rounding to 0.952, KS $D = 0.8659, p < 10^{-15}$).
2. Contribution 2: Stated verified clean AUC of **0.9523** ($M=200$) and **0.9435** ($M=100$), completely removing the transient typo "0.8524".
3. Table 1: Standardized anomaly detection row to AUC = 0.9523 and KS $D = 0.8659$.
