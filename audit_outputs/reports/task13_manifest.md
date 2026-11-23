# Task 13: Claim-to-Evidence Matrix and Verification Manifest

## 1. Executive Summary
Total quantitative claims verified: **20**.
- **Status**: 100% of claims are **VERIFIED** with direct code and CSV artifacts.
- **Traceability**: Every row maps directly to an executable Python script and raw CSV output.

## 2. Claim-to-Evidence Matrix

| Claim ID | Claim Summary | Location | Supporting Artifact | Exact Value | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **C_SPLIT_DISJOINT** | Evaluation splits E1, E2, E21, E8 have pairwise zero overlap from official disjoint test partitions. | Abstract, Sec 3.1, Sec 4.3.2, Appendix A | `audit_outputs/split_pairwise_overlap.csv` | Pairwise Overlap = 0 flows across all pairs (E2 vs E21, E1 vs E21, E8 vs E21) | **VERIFIED** |
| **C_SCHEMA_46** | Dataset feature schema contains exactly 46 flow features (Rate, Srate, Drate present; 'State' and 'Date' do not exist). | Sec 3.1 (Schema Enumeration), Appendix F | `audit_outputs/feature_schema.csv` | num_features = 46 (Rate, Srate, Drate verified present) | **VERIFIED** |
| **C_CLASS_TAXONOMY_34** | Dataset taxonomy comprises 34 classes (1 BenignTraffic + 33 granular attack classes), mapped to 8 macro families + Benign. | Sec 3.1, Sec 4.3.5, Appendix A | `audit_outputs/class_mapping.csv` | num_classes = 34 (1 benign, 33 attacks; 8 attack families) | **VERIFIED** |
| **C_IF_REPAIR_AUC** | Clean retraining of Isolation Forest eliminates contamination, restoring anomaly AUC from 0.008 to 0.952 (KS D = 0.866). | Abstract, Contrib 2, Sec 4.1.1, Table 3, Fig 2 | `paper2/tables/tab3_if_controlled.csv` | Clean IF AUC = 0.9523, KS D = 0.8659, p < 10^-15 | **VERIFIED** |
| **C_TRUST_AUC** | Dynamic trust model with neutral initial prior (T0 = 100.0) achieves AUC 0.986 on attack-heavy and 0.9990 on balanced streams. | Abstract, Contrib 2, Sec 4.1.2, Table 4, Fig 3 | `experiments/E15_five_seed_trust/results.csv` | AUC = 0.9855 +/- 0.0003 (attack-heavy), 0.9990 +/- 0.0001 (balanced) | **VERIFIED** |
| **C_POSTURE_MONOTONICITY** | Security posture model exhibits strictly non-decreasing attack density (0.00% <= 0.00% <= 46.40% <= 51.71% <= 100.00%) and monotonic trust decay (79.44 to 10.17). | Abstract, Contrib 1, Sec 4.2.2, Table 6, Fig 5 | `audit_outputs/wilson_cis.csv` | L0: 0.00%, L1: 0.00%, L2: 46.40%, L3: 51.71%, L4: 100.00% | **VERIFIED** |
| **C_L5_CORE_HUB** | Level L5 is populated only under core-hub monitoring (R >= 0.75, 100,000 flows) and 0 batches on peripheral edge streams. | Abstract, Contrib 1, Sec 4.2.3, Table 12, Appendix B | `audit_outputs/e8_benign_core_hub.csv` | 100% batches at L5 under acute flood; 0 batches at L5 on edge streams (Z = 41.25 sigma) | **VERIFIED** |
| **C_BENIGN_CORE_HUB_L1** | Under clean benign core-hub traffic, 100% of batches populate Level L1 (Alert under P2-tier) with 0.00% Block and Quarantine FPR. | Contrib 1, Sec 4.2.3, Appendix B | `audit_outputs/e8_benign_core_hub.csv` | 100% batches at L1 (Alert), 0.00% Block FPR, 0.00% Quarantine FPR | **VERIFIED** |
| **C_TOPOLOGY_PRIOR** | c_topo acts as a static topological centrality prior based on node assignment (R >= 0.42), not a dynamic flow anomaly detector. | Sec 3.2.1, Sec 5.2, Appendix B | `audit_outputs/evidence_ablation.csv` | Pure benign L1 escalation drops from 50.0% to 0.0% when c_topo=0 | **VERIFIED** |
| **C_ACTION_PREVALENCE_P2** | Action prevalence is strictly non-decreasing under policy P2-tier (0.00% <= 0.00% < 46.40% < 51.71% < 100.00%). | Abstract, Contrib 3, Sec 4.3.1, Table 7, Fig 6 | `audit_outputs/action_prevalence.csv` | Allow: 0.00%, Alert: 0.00%, Restrict: 46.40%, Quarantine: 51.71%, Block: 100.00% | **VERIFIED** |
| **C_ACTION_PREVALENCE_P1** | Conservative policy P1 maps L4 to Quarantine, resulting in 75.52% Quarantine attack prevalence. | Sec 4.3.1, Table 7 | `audit_outputs/action_prevalence.csv` | P1 Quarantine attack prevalence = 75.52% (27,566 attack / 36,500 total) | **VERIFIED** |
| **C_POLICY_P2_TIER_ADVANTAGE** | Policy P2-tier delivers a 2.43x net benefit advantage over conservative baseline P1 (+1,909,843 vs +786,643 OCU). | Abstract, Contrib 3, Sec 4.3.2, Table 8, Fig 7 | `paper2/tables/tab8_master_policy.csv` | Combined Net Benefit = +1,909,843 OCU vs +786,643 OCU (ratio: 2.42789x) | **VERIFIED** |
| **C_COST_SENSITIVITY_BOUND** | P2-tier advantage over P1 is robust across lambda in [0.2, 30.0], with break-even at lambda = 30.8 (Block penalty 1,540 OCU). | Abstract, Contrib 3, Sec 4.3.4, Sec 5.3, Appendix E | `audit_outputs/cost_sensitivity_extended.csv` | Break-even lambda = 30.8; P2/P1 ratio = 1.00 at lambda = 30.8; 0.07 at lambda = 50.0 | **VERIFIED** |
| **C_REGIME_WEIGHT_BOUND** | Across regime mixture weights w_bal in [0, 1.0], P2-tier advantage over P1 spans [2.29x, 2.48x]. | Contrib 3, Sec 4.3.4, Appendix E | `audit_outputs/regime_weight_sweep.csv` | Ratio spans 2.29x (pure balanced) to 2.48x (pure attack-heavy) | **VERIFIED** |
| **C_DISJOINT_E21_GENERALIZATION** | On independent held-out balanced test partition (Seed 99, 60k flows, disjoint from E2), P2-tier yields 0.23% Block FPR and 30.72% Quarantine FPR (+959,843 OCU balanced, +1,907,922 OCU combined). | Abstract, Contrib 3, Sec 4.3.2, Appendix A | `audit_outputs/e21_full_metrics.csv` | Block FPR = 0.233% [0.184%, 0.294%], Quarantine FPR = 30.724% [30.205%, 31.248%], Net Benefit = +959,843 OCU balanced | **VERIFIED** |
| **C_UNSTRATIFIED_STREAM_FPR** | Unstratified random stream evaluation introduces 0.24% Block FPR and 75.18% Quarantine FPR under P2-tier. | Abstract, Sec 4.3.2, Sec 6.7 | `audit_outputs/random_balanced_60k.csv` | Block FPR = 0.241% [0.191%, 0.303%], Quarantine FPR = 75.184% [74.690%, 75.672%] | **VERIFIED** |
| **C_TRUST_CARRYOVER** | ADTM recovers above trust threshold tau_T = 60.0 in 4 flows following a 100-flow attack burst, temporarily depressing 3 benign flows below 60.0 and 0 below 20.0. | Sec 3.3.1, Sec 6.7 | `audit_outputs/trust_carryover.csv` | Recovery flows = 4; depressed flows (<60) = 3; severely depressed (<20) = 0 | **VERIFIED** |
| **C_DYNAMIC_SWITCHER_OFFSET** | Online dynamic switching matches static P2-tier within 0.006% (+1,909,733 vs +1,909,843 OCU, 110 OCU offset due to batch rounding). | Abstract, Sec 4.4, Table 11 | `experiments/E16_dynamic_switcher/results.csv` | Offset = 110 OCU (0.0058%) | **VERIFIED** |
| **C_CLASSIFIER_PERFORMANCE** | Frozen XGBoost classifier achieves 98.99% raw accuracy, but 34-class balanced accuracy is 70.98% and macro F1 is 71.51%, with extreme minority degradation (Malware 1.12%, BruteForce 15.05%). | Sec 4.3.5, Sec 6.7 | `audit_outputs/classifier_per_family.csv` | Raw Acc = 98.99%, Balanced Acc = 70.98%, Macro F1 = 71.51%, Malware Recall = 1.12%, BruteForce Recall = 15.05% | **VERIFIED** |
| **C_PER_FAMILY_RECONCILIATION** | Table 9 threat family distribution strictly sums to 30,118 attack flows across 8 families + 29,882 benign flows = 60,000 flows total; Web mean trust = 16.03. | Sec 4.3.3, Sec 6.3, Table 9, Fig 9 | `paper2/tables/tab9_per_family.csv` | Attack flows = 30,118; Benign flows = 29,882; Total = 60,000; Web trust = 16.03 | **VERIFIED** |

## 3. Cryptographic Hash Manifest
A total of 61 files in `audit_outputs/` and `experiments/audit/` are cryptographically registered in `audit_outputs/SHA256SUMS.txt`.

```text
b7aaeba2b3f42b3144e766d1376c0cab8c004903e124db778b10fd5ac7327ace  audit_outputs/AUDIT_CHECKSUMS.sha256
de7eb376fdcdf6875b7479b8a8375879c102a37d69080ecadd2b0bc892de1e3c  audit_outputs/action_prevalence.csv
c0f9da381dc193c4af355f8871448f0318a229598706161d8776f2aefd772574  audit_outputs/all_70_policies.csv
d1eb452df4225d5be0f4e20a8ea554eb351a3622038d8bf2edfe5f6ce9e401ab  audit_outputs/all_70_policies_held_out_test.csv
7e639375fa9e3d1b48fc19a87de6bcf57fd0ab55f48ffd9b4cb5852c7eec16c6  audit_outputs/anomaly_detectors_comparison.csv
f61f84f06d8533e1d5a340a4c77e2f275cd84d7439629834c3b2b14464697378  audit_outputs/claim_evidence_matrix.csv
9a3f79de2e4b9a904d47a05eec2498748dea78f2c3bec0bc3d680f62fa52eb6a  audit_outputs/class_mapping.csv
aa4a4dc46d8b6e862e0dfe9316c6dd319d6d88359af95ffc45109f7f3865e319  audit_outputs/classifier_34_classes.csv
c4363a7d4c076a79a6cdc3f9f1d505bc3f893ed3a580a15067e906b36c84e485  audit_outputs/classifier_aggregate_summary.csv
de50f2230a0a63c19ab16e01539c8048da092ad403194a50a0f922f488f54782  audit_outputs/classifier_per_family.csv
694539639dd3fe780040e06f6742ff791e092b870dee7933641b6cfc5ea13fad  audit_outputs/contamination_dose_response.csv
72e652ca79c00be7aa126419dccd540de8aaba173bc311b3949e1fd713666965  audit_outputs/cost_sensitivity_extended.csv
5686235a15d9de5682f240941e031e122756b4117eb860cfe804779e282a0658  audit_outputs/e1_disjoint_indices.npy
cafd658741dbed682bb1589f12012ff7fbc78d596eea384c84c044134d620eb2  audit_outputs/e21_action_prevalence.csv
2b477ba8d76dde935e4265399f7f699c1841b6f3993c6464292e0253d3b2e814  audit_outputs/e21_disjoint_indices.npy
... (46 additional files hashed)
```
