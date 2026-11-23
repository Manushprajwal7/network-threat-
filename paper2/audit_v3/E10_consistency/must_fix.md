# Numeric Consistency Audit & Must-Fix Priority Ledger

**Audit Date**: 2026-11-18  
**Scope**: Full manuscript numeric claims reconciled against verified experimental artifacts in `audit_v3/` (E1–E9).  
**Ledger Output**: [`audit_v3/E10_consistency/consistency.csv`](file:///C:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/audit_v3/E10_consistency/consistency.csv)

---

## 1. Executive Summary: Audit Reconciliation Status

| Severity Level | Item Count | Status | Required Editorial Action |
| :--- | :---: | :---: | :--- |
| **CRITICAL** | 4 | Action Required | Must be corrected before submission; represents mathematical contradictions or ungrounded claims. |
| **HIGH** | 6 | Action Required | Inconsistent values across sections; must be harmonized to artifact ground truth. |
| **MEDIUM** | 3 | Action Required | Minor rounding or notation ambiguity (1-tail vs 2-tail p-values, KS scores). |
| **LOW** | 1 | Polishing | Decimal precision harmonization. |
| **VERIFIED / INFO** | 4 | Fully Verified | Empirical claims confirmed and mathematically backed by E1–E9 artifacts. |

---

## 2. Priority 1: CRITICAL MUST-FIX ITEMS (Blockers)

### Critical #1: Abstract & Sec 4.4 Table 1
- **Claimed in Draft**: P_hybrid OCU reported as 1.93M (or 1,934,546 or 1,931,108 in earlier drafts)
- **Artifact Source**: `audit_v3/E5_p_hybrid/comparison_table.csv & E8 full_policy_table.csv`
- **Artifact Recomputed Truth**: **Balanced: 1,391,654.0 | Flood: 2,974,176.0 | Overall 50-run Mean: 2,044,424.6 | Test Seed 99: 1,404,974**
- **Required Editorial Fix**: Replace single pooled number with exact per-regime mean ± SD: Balanced 1,391,654 ± 7,984; Flood 2,974,176 ± 1,291.

### Critical #2: Sec 4.4 / Table 1
- **Claimed in Draft**: P_hybrid flood Block FPR reported as 34.66% vs 38.89%
- **Artifact Source**: `audit_v3/E5_p_hybrid/comparison_table.csv & E8 full_policy_table.csv`
- **Artifact Recomputed Truth**: **Flood has 0 benign flows -> Block FPR is strictly N/A (0/0). Across all 4 mixed regimes, mean Block FPR is 1.10% (max 1.47% in attack-heavy)**
- **Required Editorial Fix**: Mark Flood Block FPR as N/A (0 benign flows in pure flood); report mixed regime Block FPR as 0.72% (balanced) and 1.10% (unstratified).

### Critical #3: Sec 3.3 Topology
- **Claimed in Draft**: Z-score reported as Z=4.59 vs Z=4.125 vs Z=41.25
- **Artifact Source**: `audit_v3/E3_topology/summary.md`
- **Artifact Recomputed Truth**: **Empirical graph: Z = 4.5931 sigma (p = 2.18e-6). Theoretical target: Z = 4.1250 sigma (p = 1.85e-5). Z=41.25 was an arithmetic batch sqrt(100) error.**
- **Required Editorial Fix**: Delete erroneous Z=41.25. State: Z = 4.59 sigma (empirical, p = 2.18e-6) and Z = 4.125 sigma (theoretical, p = 1.85e-5).

### Critical #4: Sec 4.6 Regime Shift
- **Claimed in Draft**: P_hybrid provides defense-in-depth against degraded unstratified traffic
- **Artifact Source**: `audit_v3/E6_regime_shift/verdict.md & E5 comparison_table.csv`
- **Artifact Recomputed Truth**: **Refuted: P_hybrid advantage drops from +14k (flood) to -146k (unstratified shuffle). Quarantine FPR rises to 20.29%.**
- **Required Editorial Fix**: Remove 'defense-in-depth against regime shift' claim; replace with honest trade-off analysis.

---

## 3. Priority 2: HIGH SEVERITY FIXES (Harmonization)

### High #1: Sec 4.3 Table 1
- **Claimed in Draft**: P_opt OCU reported as 1,922,671 vs 1,920,767
- **Artifact Source**: `audit_v3/E7_calibration_split/test_policy_table.csv & E8 full_policy_table.csv`
- **Artifact Recomputed Truth**: **D_test Seed 99: 1,439,948 | 50-run Overall Mean: 2,052,438.1 [1,854,289.9, 2,250,586.4]**
- **Required Editorial Fix**: Update Table 1 with validated D_test OCU: 1,439,948 (balanced) and overall 50-run mean: 2,052,438.

### High #2: Sec 4.3 Table 1
- **Claimed in Draft**: P_2-tier OCU reported as 1,912,063 vs 1,909,843
- **Artifact Source**: `audit_v3/E7_calibration_split/test_policy_table.csv & E8 full_policy_table.csv`
- **Artifact Recomputed Truth**: **D_test Seed 99: 1,404,974 | 50-run Overall Mean: 2,027,331.5**
- **Required Editorial Fix**: Update Table 1 with validated D_test OCU: 1,404,974.

### High #3: Sec 4.1 Methodology
- **Claimed in Draft**: Seeds reported inconsistently as 5 seeds vs 10 seeds
- **Artifact Source**: `audit_v3/E5_p_hybrid/wilcoxon_results.csv & E8 full_policy_table.csv`
- **Artifact Recomputed Truth**: **Exact 10 seeds evaluated across all experiments: [13, 42, 99, 123, 2024, 7, 77, 101, 2023, 31415]**
- **Required Editorial Fix**: State unequivocally in Section 4.1: '10 independent pseudo-random seeds were evaluated across all 5 operational regimes'.

### High #4: Sec 4.2 Posture Analysis
- **Claimed in Draft**: L5 attack density reported as 97.60% vs 99.43%
- **Artifact Source**: `audit_v3/E4_permutation_v2/results.csv & interpretation.md`
- **Artifact Recomputed Truth**: **In balanced stream, Level L5 contains 0 flows (unpopulated). In attack-heavy stream, L5 is 99.43% attack. Null monotonicity rate is 0.40%.**
- **Required Editorial Fix**: Clarify stream dependence: L5 is unpopulated in balanced nominal traffic; under attack-heavy streams it reaches 99.43% attack density.

### High #5: Sec 3.3 Topology
- **Claimed in Draft**: Topology risk std reported as sigma=0.0721 in one place and sigma=0.08 elsewhere
- **Artifact Source**: `audit_v3/E3_topology/summary.md & ba_topology.csv`
- **Artifact Recomputed Truth**: **Empirical BA(m=2) standard deviation is sigma_R = 0.0721; theoretical target distribution is sigma = 0.0800**
- **Required Editorial Fix**: Standardize: state theoretical distribution N(0.42, 0.08) and report empirical realized sigma_R = 0.0721 for the generated 120-node graph.

### High #6: Sec 5 Deployment / Real-Time
- **Claimed in Draft**: Multi-modal response operates in 'real-time'
- **Artifact Source**: `audit_v3/E9_latency/latency_table.csv & throughput.csv`
- **Artifact Recomputed Truth**: **End-to-End pipeline throughput = 18,244 flows/sec (54.8 us/flow). GPU single flow = 2.5 ms (requires B >= 256 micro-batching). Veto = 0.177 us.**
- **Required Editorial Fix**: Qualify 'real-time' claim: state 'sub-millisecond line-rate processing (>18,000 flows/sec) under batched micro-windows (B >= 256)'.

---

## 4. Priority 3: MEDIUM & LOW SEVERITY FIXES

### Medium/Low #1: Sec 4.3 Table 1
- **Claimed in Draft**: P_1 OCU reported as 787,074 vs 786,643
- **Artifact Source**: `audit_v3/E8_cost_and_policy/full_policy_table.csv`
- **Artifact Recomputed Truth**: **D_test Seed 99: 786,643 | 50-run Overall Mean: 1,184,210.4**
- **Required Editorial Fix**: Standardize on D_test Seed 99: 786,643 and report 10-seed CI.

### Medium/Low #2: Sec 3.3 Topology
- **Claimed in Draft**: p-values reported inconsistently as 2.2e-6 vs 4.4e-6; 10^-15 vs 10^-5
- **Artifact Source**: `audit_v3/E3_topology/summary.md`
- **Artifact Recomputed Truth**: **1-tailed p = 2.18e-6; 2-tailed p = 4.37e-6. Node 0 extreme Z=6.67 sigma has p = 1.25e-11.**
- **Required Editorial Fix**: Explicitly label 1-tailed p = 2.2e-6 and 2-tailed p = 4.4e-6.

### Medium/Low #3: Sec 4.2 Statistical Separation
- **Claimed in Draft**: KS statistic between Benign and Attack anomaly scores reported as 0.950 vs 0.866
- **Artifact Source**: `audit_v3/E7_calibration_split/summary.md & paper2/audit/lofo/cache/`
- **Artifact Recomputed Truth**: **Raw decision score KS = 0.866; Calibrated s_cal KS = 0.866; 0.95 was an informal upper quantile reference**
- **Required Editorial Fix**: Standardize on empirical KS statistic D = 0.866 (p < 1e-300).

### Medium/Low #4: Sec 1 & Sec 4.1
- **Claimed in Draft**: Contaminated IF AUC reported as 0.008 vs 0.0084
- **Artifact Source**: `audit_v3/E2_defect_trace/defects.md`
- **Artifact Recomputed Truth**: **Exact contaminated IF ROC-AUC on BenignTraffic is 0.0084 (corrected clean IF AUC = 0.8524)**
- **Required Editorial Fix**: Harmonize to 4 decimal places: AUC = 0.0084.

