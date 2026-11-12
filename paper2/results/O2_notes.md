# Objective 2 Experimental Notes: Isolation Forest Repair & Trust Recalibration

## 1. Baseline Freeze Verification
- The contaminated pipeline baseline was frozen to [`paper2_baseline_if_contaminated/`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2_baseline_if_contaminated/) prior to any modification. All 6 original files preserved unmodified.

## 2. Part A — Isolation Forest Contamination Root Cause & Repair
- **Bug Location**: [`backend/ml_model/unknown_attack_detector.py`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/backend/ml_model/unknown_attack_detector.py#L67-L75).
  The label lookup `list(label_encoder.classes_).index("BENIGN")` failed because CICIoT2023 labels benign traffic as `"BenignTraffic"`. 
  This triggered fallback `X_benign = X_train`, training the Isolation Forest on 5.49M samples that were 97.5% attack traffic.
- **Empirical Contamination**:
  - Contaminated model scored benign samples at mean = 1.0000 and attack samples at mean = 0.8770.
  - Inverted AUC (detecting attacks as anomaly): **0.0296**.
  - Benign flows flagging $\ge 0.90$: **100.00%**.
- **Corrected Retraining**:
  - Matched label `"BenignTraffic"` (class index 1).
  - Trained on **129,538 benign-only samples** (`n_estimators=200`, `contamination=0.05`, `max_samples=256`, `random_state=42`).
  - Saved to [`backend/ml_model/saved_models/isolation_forest_corrected.pkl`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/backend/ml_model/saved_models/isolation_forest_corrected.pkl).
- **Discrimination Verification ([`paper2/tables/O2_A_if_comparison.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/tables/O2_A_if_comparison.csv))**:
  - AUC(Attack vs Benign): **0.9567** (Target: $\ge 0.90$, PASS ✓).
  - Mean Benign Anomaly: **0.4352**.
  - Mean Attack Anomaly: **0.9221**.
  - Anomaly Gap: **0.4869** (Target: $\ge 0.30$, PASS ✓).
  - Benign $\ge 0.90$: **4.99%** (Target: ~5.0% matching contamination, PASS ✓).
  - Attack $\ge 0.90$: **62.72%**.
  - ROC Curve saved to [`paper2/figures/O2_A_if_roc_comparison.png`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/figures/O2_A_if_roc_comparison.png).

## 3. Part B — Trust Recalibration Diagnostics (Configurations C0 through C4)
- **C0 (B.1 Baseline Update with Corrected Anomaly)**:
  - Trust distribution: High = 3.21%, Moderate = 83.69%, Low = 13.10%, Very Low = 0.00%, Critical = 0.00%.
  - AUC(trust, attack) = 0.7843, Trust Gap = 7.96 points.
  - Confirms Very Low and Critical are 0.00% in baseline ADTM, motivating interventions.
- **C1 (B.2 Family-Aware Priors)**:
  - $\lambda_{\text{prior}} = 0.55$, derived from the 54.17% empirical spread in training set XGBoost $P(\text{benign})$.
  - Trust distribution: High = 0.14%, Moderate = 2.50%, Low = 3.83%, Very Low = 93.53%, Critical = 0.00%.
  - **AUC(trust, attack) = 0.8969** (~0.90), Trust Gap = 8.48 points.
  - High discrimination preserved; Very Low band successfully populated.
- **C2 (B.3 Hard Reset to T=20 for 200 samples)**:
  - Trust distribution: High = 0.08%, Moderate = 0.04%, Low = 1.16%, Very Low = 98.72%, Critical = 0.00%.
  - AUC(trust, attack) = 0.5052, Trust Gap = 0.93 points.
  - L5 entities = 100.00%, L4 entities = 0.00%.
- **C3 (B.4 Adaptive EWMA)**:
  - Trust distribution: High = 0.11%, Moderate = 0.01%, Low = 2.07%, Very Low = 97.81%, Critical = 0.00%.
  - AUC(trust, attack) = 0.5050, Trust Gap = 0.88 points.
- **C4 (B.5 Extended 500k Stratified Window)**:
  - Trust distribution: High = 0.09%, Moderate = 0.02%, Low = 2.17%, Very Low = 97.71%, Critical = 0.00%.
  - AUC(trust, attack) = 0.5057, Trust Gap = 0.84 points.
  - L5 entities = 100.00%, L4 entities = 0.00%.

## 4. Scientific Root-Cause of C4 Success Target Deviations
1. **Critical Band (0-19) is 0.00%**:
   The prompt specification explicitly set:
   `if hard_reset_count >= 2: T = 20 (Very Low); lock T = 20 for next 200 samples`.
   Because trust is clamped to $20.0$, all escalated flows land in the Very Low band ($[20, 40)$), never reaching the Critical band ($[0, 20)$).
2. **Trust AUC Collapses in C2-C4 (0.8969 $\rightarrow$ 0.5057)**:
   In a continuous network stream, a 200-sample hard reset lock keeps the entity clamped at $T = 20.0$. 
   Because intermittent benign packets that occur within attack streams are also locked at $T = 20.0$, the model cannot differentiate benign from attack flows during the lock window, causing the trust AUC to collapse from **0.8969** (in C1) down to **0.5057**.
3. **L4 vs L5 Priority Routing**:
   Entities with $S \ge 3$ and $\min(T) \le 20$ evaluate `distinct_fams >= 2` first. Because almost all attack entity windows in CICIoT2023 involve multi-vector threats ($>1$ family), all entities route to L5 (Adaptive Block), leaving L4 at 0%.

## 5. Final Part B Iteration: Stratified Balanced Window & Monotonic Level Definitions

### 5.1 Stratified Entity Window Construction (Fix 1)
"The balanced evaluation window uses stratified entity construction: 30% pure-benign, 40% mixed, 30% pure-attack. This is more realistic than uniform random sampling, which mathematically cannot produce pure-benign entities under a 50/50 flow mix. Stratified construction reflects the deployment reality where benign IoT sensors and attack sources are distinct entities, with some entities experiencing mixed traffic."

- **Structure**: 600 entities $\times$ 100 flows = 60,000 flows total:
  - 180 pure-benign entities ($18,000$ flows, $0\%$ attack)
  - 240 mixed entities ($24,000$ flows, $k_{\text{atk}} \sim \text{Binomial}(100, 0.5)$ per entity)
  - 180 pure-attack entities ($18,000$ flows, $100\%$ attack)
- **Outcome**: Resolves the mathematical impossibility of uniform flow shuffling ($B(100, 0.5)$ concentration), populating all security tiers naturally.

### 5.2 Strict Level Monotonicity Hierarchy (Fix 2)
To eliminate inversion between L4 and L5, the escalation tiers are defined with strict subset containment:
- **Level L5 (Multi-Vector Attack on Critical Hub)**:
  $$S \ge 3 \land \text{mean\_trust} \le 20 \land \text{distinct\_families} \ge 3 \land \text{TARP} \ge 0.75$$
- **Level L4 (Multi-Vector Attack off Critical Hub)**:
  $$S \ge 3 \land \text{mean\_trust} \le 20 \land \text{distinct\_families} \ge 2 \land \text{NOT}(\text{TARP} \ge 0.75)$$
- **Level L3 (Moderate Severity Threat Accumulation)**:
  $$S \ge 3 \land \text{NOT}(L_4) \land \text{NOT}(L_5)$$

### 5.3 Calibrated Operational Regimes (Fix 3)
Entity anomaly and confidence thresholds are window-calibrated:
- Attack-heavy window ($97.5\%$ attack): $\tau_{\text{anom}} = 0.28, \tau_{\text{conf}} = 0.26$
- Balanced window ($50.0\%$ attack): $\tau_{\text{anom}} = 0.55, \tau_{\text{conf}} = 0.55$

