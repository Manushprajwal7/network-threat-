# Experiment E1: MDPI Baseline Negative Results Reproduction
**Anchor Publication**: *Journal of Cybersecurity and Privacy* 2026, 6(5), 181.  
**Audit Target**: Forensic verification of reported negative baseline results prior to architecture repair.  
**Execution Timestamp**: 2026-11-18 20:52:07  
**Hardware Used**: NVIDIA RTX 3050 6GB Laptop GPU (CUDA-accelerated inference)

---

## 1. Summary of Reproduction Results

| Metric | MDPI Paper Value | Reproduced Value | Absolute Delta | Status |
| :--- | :---: | :---: | :---: | :---: |
| **High Trust Band Observations** | 94.25% | **94.25%** | **+0.00%** | **PASS** (within ±0.01 pp) |
| **Attack-Labeled Rate in High Trust** | 97.16% | **97.38%** | **+0.22%** | **PASS** (within ±0.22 pp) |
| **Alert Action Prevalence** | 90.92% | **90.92%** | **0.00%** | **PASS** (Exact Match) |
| **Quarantine Action Prevalence** | 9.08% | **9.08%** | **0.00%** | **PASS** (Exact Match) |
| **Allow, Restrict, Block Inactive** | 0.00% | **0.00%** | **0.00%** | **PASS** (Never Triggered) |

*Success Criterion: All 5 negative baseline results reproduce within ±2.0 percentage points. Result: 100% PASSED.*

---

## 2. Forensic Analysis of Implementation Defects

### Defect 1: Class Label String Mismatch in Anomaly Filtering
The original Isolation Forest was intended to train strictly on benign traffic. However, the benign filtering clause checked:
```python
y_train == 'BENIGN'  # Fails silently against CICIoT2023 schema
```
Because CICIoT2023 designates legitimate network flows as `'BenignTraffic'`, the condition evaluated to `False` for all rows. Consequently, the filter failed silently, and the Isolation Forest was trained on the entire uncurated telemetry partition:
- **Total Training Flows**: 5,491,971
- **Attack Contamination**: 5,362,433 flows (**97.64% attack traffic**)
- **Benign Flows**: 129,538 flows (2.36%)

**Downstream Impact**: The contaminated detector learned high-frequency attack signatures as the "normal" baseline, severely compressing anomaly scores and inverting normal/abnormal semantics.

### Defect 2: Ground-Truth Attack Prior Leakage in ADTM
The original Adaptive Dynamic Trust Model (ADTM) initialized entity trust vectors using a static heuristic table `p_benign_map` indexed by ground-truth attack class names:
```python
p_benign_map = {
    "BenignTraffic": 100.0, "Recon-PingSweep": 74.8, "SqlInjection": 70.1,
    "BrowserHijacking": 57.6, "DictionaryBruteForce": 56.9, ...
}
```
- Entity trust initialization was seeded directly with empirical class labels rather than zero-knowledge neutral priors.
- Furthermore, the static weight floor ($S_U = 100.0, S_D pprox 100.0, S_B pprox 100.0$) anchored trust calculations, trapping **94.25% of all observations in the High Trust band ($\ge 80.0$)**.
- Because 97.60% of the evaluation window comprised attack traffic, **97.16%–97.38% of flows in the High Trust band were malicious attacks**.

### Defect 3: Action Inversion and Dead Operational Tiers
In Table 19A of the baseline paper:
- **Alert**: 54,553 flows (90.92%) — 100.00% attack flows.
- **Quarantine**: 5,447 flows (9.08%) — 70.50% attack flows, diluted by 1,607 benign flows.
- **Structural Inversion**: Higher severity action (Quarantine) had **lower attack precision** than the lower severity action (Alert): $70.50\% < 100.00\%$.
- **Dead Actions**: **Allow (0.00%)**, **Restrict (0.00%)**, and **Block (0.00%)** were never triggered throughout the entire 60,000-flow operational window.

---

## 3. Conclusion
The negative results published in the anchored MDPI paper are rigorously reproducible and stem from concrete, traceable implementation defects (unfiltered 97.64% training contamination, label leakage in trust priors, and uncalibrated multi-stage thresholds). The subsequent audit experiments document the step-by-step forensic repairs and prove mathematical consistency.
