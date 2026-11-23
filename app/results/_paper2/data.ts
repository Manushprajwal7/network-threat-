// Comprehensive experimental data, 70 policies, 38 audit issues, and latency benchmarks for Paper 2
import POLICIES_70_RAW from './policies_full.json';
import EXPERIMENTS_INVENTORY_RAW from './experiments_inventory.json';
import LATENCY_RAW from './latency_table.json';
import THROUGHPUT_RAW from './throughput_table.json';

export interface PaperComparisonRow {
  dimension: string;
  paper1: string;
  paper2: string;
  delta: string;
}

export const TABLE1_PAPER_COMPARISON: PaperComparisonRow[] = [
  {
    dimension: 'Anomaly Detection (Isolation Forest)',
    paper1: 'Trained on 97.5% attack telemetry (label mismatch); inverted anomaly scores (r = -0.584); AUC = 0.0084 (0.0296 test)',
    paper2: 'Clean benign-only retraining (M=200 trees, 50k subsample); positive anomaly separation; AUC = 0.9523 (0.9567 test); KS D = 0.8659 (p < 10⁻¹⁵)',
    delta: 'AUC: 0.0084 → 0.9523 (+0.9439)'
  },
  {
    dimension: 'Dynamic Behavioral Trust (ADTM)',
    paper1: 'Static weight floor; 200-sample clamp freezing trust; 99.97% trapped in High band; AUC = 0.0441',
    paper2: 'Neutral Prior (T₀ = 100.0), dynamic severity weighting, joint per-flow hard reset T=10, k=0.30; AUC = 0.9858 (0.9644 on 500k stream)',
    delta: 'AUC: 0.0441 → 0.9858 (+0.9417)'
  },
  {
    dimension: 'Security Posture Modeling (L0–L5)',
    paper1: 'Disjoint component heuristics; ad-hoc boolean conditionals; alert accumulation; downstream policy inaction',
    paper2: 'Six-level posture escalation hierarchy (L0–L5) synthesizing cumulative evidence S ∈ [0, 4] over W=100 flows with W_cooldown=300 hysteresis',
    delta: 'Disjoint → 6-Tier Formally Latching Hierarchy'
  },
  {
    dimension: 'Response Policy & Action Precision',
    paper1: 'Heuristic rule baseline (Table 19A); inverted action precision (Alert 100% vs Quarantine 70.50%, Restrict 1.74% precision)',
    paper2: 'Combinatorial sweep over all 70 monotonic mappings in formal OCU; strictly non-decreasing action attack purity (0.0% < 39.7% < 57.4% < 98.2% < 100.0%)',
    delta: 'Action Purity Inversion Completely Resolved'
  },
  {
    dimension: 'Operational Net Benefit (OCU)',
    paper1: 'Unmodeled costs; baseline net benefit +153,952 OCU (balanced) / +329,835 OCU (sustained flood); unranked',
    paper2: 'Decision-theoretic loss matrix L(a, y); P_opt Rank 1 (+1,439,948 OCU on test; 2,052,438 OCU 50-run mean); P2-tier Rank 9 (+1,404,974 OCU test, 2.48× over P1); P_hybrid 2,044,425 OCU mean',
    delta: 'Net Benefit: +154k → +1,440k OCU (9.35× gain)'
  }
];

export interface AuditIssue {
  id: number;
  category: 'Critical' | 'Methodology' | 'Architecture' | 'Publication';
  critique: string;
  rootCause: string;
  resolution: string;
  status: string;
}

export const AUDIT_38_ISSUES: AuditIssue[] = [
  { id: 1, category: 'Critical', critique: 'Cost matrix contradicts itself (Allow cost 0 vs 100)', rootCause: 'Historical draft conflated loss L with unmitigated attack penalty.', resolution: 'Unified under formal Decision-Theoretic Cost Matrix in Table 10. Allow is strictly (0, 0), C(Allow) = 0, Net Benefit B = -C.', status: 'RESOLVED ✓' },
  { id: 2, category: 'Critical', critique: 'Monetary claims not economically justified', rootCause: 'Dollar figures assumed arbitrary utility-to-dollar multiplier.', resolution: 'Standardized all economic metrics to formal Operational Cost Units (OCU) and kOCU. Zero dollar claims exist.', status: 'RESOLVED ✓' },
  { id: 3, category: 'Critical', critique: '65-policy optimization derivation incomplete', rootCause: 'Conflated combinatorial formula with empirical data filter.', resolution: 'Derived full monotonic space C(4+5-1, 5-1) = C(8, 4) = 70 mappings. Formalized safety-constrained filter (Block FPR <= 5.0%) admitting 65 policies.', status: 'RESOLVED ✓' },
  { id: 4, category: 'Critical', critique: 'Optimized and evaluated on same data (leakage)', rootCause: 'Re-evaluating policies on validation split created selection bias.', resolution: 'Established 3-way split: Training, Validation/Selection, and Independent Test (60k flows, seed 99). Generalization confirmed: 2.485x vs 2.48x.', status: 'RESOLVED ✓' },
  { id: 5, category: 'Critical', critique: 'Isolation Forest formula omitted 2*gamma', rootCause: 'Term 2(ln(n-1) + gamma) was written without expanding factor 2.', resolution: 'Corrected formula: c(n) = 2*ln(n-1) + 1.1544313298 - 2(n-1)/n, explicitly multiplying Euler constant by 2.', status: 'RESOLVED ✓' },
  { id: 6, category: 'Critical', critique: 'Anomaly-score calibration not reproducible', rootCause: 'Ambiguity between raw path length and score_samples in scikit-learn.', resolution: 'Specified s(x) = -score_samples(x), with s_p5 = 0.4421, s_p95 = 0.5284 fitted strictly on clean benign validation split.', status: 'RESOLVED ✓' },
  { id: 7, category: 'Critical', critique: 'ADTM hard reset in Algorithm 2 damped by EWMA', rootCause: 'Algorithm 2 updated T_obs <- 10.0 then executed smoothing.', resolution: 'Fixed Algorithm 2: hard reset condition immediately executes T_curr <- 10.0, completely overriding EWMA smoothing.', status: 'RESOLVED ✓' },
  { id: 8, category: 'Critical', critique: 'Algorithm 1 did not implement window proportions', rootCause: 'Algorithm 1 used per-flow scalars instead of window rates.', resolution: 'Rewritten to compute window proportions (c_anom, c_conf, c_trust, c_topo) over W=100 flows, matching Section 3.2.1.', status: 'RESOLVED ✓' },
  { id: 9, category: 'Critical', critique: 'Hysteresis equation did not implement safeguards', rootCause: 'Text promised cooldown and trust recovery; eq had cooldown only.', resolution: 'Formalized joint hysteresis rule: requires t - t_last >= 300 flows AND trust recovery (T_mean >= 80.0 for L0).', status: 'RESOLVED ✓' },
  { id: 10, category: 'Methodology', critique: 'Balanced benchmark description misleading', rootCause: '30/40/30 was entity batch proportions, not flow counts.', resolution: 'Explicitly distinguished entity batch sampling (180 benign, 240 mixed, 180 attack) from flow class counts (29,882 benign / 30,118 attack = 50.20%).', status: 'RESOLVED ✓' },
  { id: 11, category: 'Methodology', critique: 'Trust AUC / Critical band taken from different windows', rootCause: 'Table 3 mixed 500k row with 60k evaluations.', resolution: 'Synchronized Table 3: all configurations C0* to C4* evaluated on the identical 60,000-flow stream.', status: 'RESOLVED ✓' },
  { id: 12, category: 'Methodology', critique: 'Six-level model is non-decreasing, not strictly monotonic', rootCause: 'L4 and L5 both exhibit 100.00% attack density.', resolution: 'Replaced "strictly monotonic" with "non-decreasing" or "monotonic" across all text and contributions.', status: 'RESOLVED ✓' },
  { id: 13, category: 'Methodology', critique: 'Level L3 had small sample size in old draft', rootCause: 'Old draft had 7 entities / 700 flows.', resolution: 'Clean multi-state stream has 185 batches (18,500 flows = 30.83% of stream) in L3, statistically separated from L2 (p < 10⁻¹¹).', status: 'RESOLVED ✓' },
  { id: 14, category: 'Methodology', critique: 'Figure 4 contradicted its own description', rootCause: 'Mirai trace rose above 20 in old plot due to label misindexing.', resolution: 'Regenerated Figure 4: Mirai trace hard-resets to T=10.0 and stays strictly at 10.0. Level labels aligned.', status: 'RESOLVED ✓' },
  { id: 15, category: 'Methodology', critique: 'Contamination percentages did not add up (5% vs 2.5%)', rootCause: '27,700 / 554,000 was 5%, not 2.5%.', resolution: 'Replaced with exact official CICIoT2023 counts: 5,491,971 training flows (129,538 benign = 2.36%, 5,362,433 attack = 97.64%).', status: 'RESOLVED ✓' },
  { id: 16, category: 'Methodology', critique: 'Training/evaluation protocol insufficiently specified', rootCause: 'Missing details on entity construction and windowing.', resolution: 'Section 3.1 details 3-way split, 100-flow batch inspection at edge gateway, and synthetic 120-node graph topology mapping.', status: 'RESOLVED ✓' },
  { id: 17, category: 'Methodology', critique: 'Feature list missing features; typos in names', rootCause: 'Tot size was duplicated, Magnitue was altered.', resolution: 'Fully cataloged all 46 features from feature_columns.pkl in exact order, noting dataset column name Magnitue.', status: 'RESOLVED ✓' },
  { id: 18, category: 'Methodology', critique: 'Figure 5 / Table 8 claim 71 monotonic mappings, not 70', rootCause: 'Included invalid identity mapping.', resolution: 'Enumerated exact monotonic sequence: C(8, 4) = 70 valid policies. 65 satisfy safety constraint.', status: 'RESOLVED ✓' },
  { id: 19, category: 'Methodology', critique: 'P2 unconstrained ranking (Rank 1) needs clear framing', rootCause: 'P2 incurs 29.9% benign block FPR on unstratified stream.', resolution: 'Explicitly labeled P2 as unconstrained theoretical optimum; established P2-tier as the primary recommended standard.', status: 'RESOLVED ✓' },
  { id: 20, category: 'Methodology', critique: 'Regime-dependent thresholds not justified', rootCause: 'tau_anom = 0.55 vs 0.28 assumed clairvoyance.', resolution: 'Fixed all operational thresholds to a single unified operating point (tau_anom=0.50, tau_conf=0.90, tau_trust=60.0).', status: 'RESOLVED ✓' },
  { id: 21, category: 'Methodology', critique: '22,296 incremental gain misattributed', rootCause: 'Attributed all P2 gains to L3 Block escalation.', resolution: 'Decomposed exact differences: P2-tier escalates only L4 to Block (+540,000 OCU gain, 0% benign disruption).', status: 'RESOLVED ✓' },
  { id: 22, category: 'Methodology', critique: '0% false-positive blocking claim narrower than suggested', rootCause: 'Benign flows receive Quarantine; 52.68% non-Allow.', resolution: 'Rigorously distinguished Block FPR (0.00%) from Quarantine FPR and overall attention routing (52.68%).', status: 'RESOLVED ✓' },
  { id: 23, category: 'Methodology', critique: 'Operational precision metric needs a clearer name', rootCause: 'Precision confused with binary classifier precision.', resolution: 'Explicitly termed Action Attack Precision / Attack Purity, providing full flow counts in Table 6.', status: 'RESOLVED ✓' },
  { id: 24, category: 'Methodology', critique: '6.77x improvement not an independent result', rootCause: 'Baseline comparison evaluated on same validation data.', resolution: 'Replaced with verified OCU net benefit comparison (+1,909,843 vs +786,643 OCU = 2.43x) validated on held-out test split (2.485x).', status: 'RESOLVED ✓' },
  { id: 25, category: 'Methodology', critique: 'AUC results need uncertainty estimates', rootCause: 'Four-decimal metrics reported without confidence bounds.', resolution: 'Added DeLong 95% CIs for AUC (IF: [0.9482, 0.9564], Trust: [0.9835, 0.9881]) and Wilson score 95% CIs.', status: 'RESOLVED ✓' },
  { id: 26, category: 'Architecture', critique: 'L4 called Topological Hub Isolation but describes off-hub', rootCause: 'L4 has R < 0.75; L5 has R >= 0.75.', resolution: 'Renamed L4: Severe Containment (Peripheral/Edge) and L5: Critical Topological Hub Containment.', status: 'RESOLVED ✓' },
  { id: 27, category: 'Architecture', critique: 'Mapping to IEC 62443 not technically established', rootCause: 'SL1-SL4 are design capabilities, not runtime states.', resolution: 'Re-framed Section 2.8 as a conceptual high-level analogy, emphasizing that IEC 62443 defines design resistance tiers.', status: 'RESOLVED ✓' },
  { id: 28, category: 'Architecture', critique: 'NIST comparison conceptually inaccurate', rootCause: 'FIPS 199 impact on CIA loss, not evidence score S.', resolution: 'Re-framed as an operational analogue for consequence-aware loss matrix parameterization.', status: 'RESOLVED ✓' },
  { id: 29, category: 'Architecture', critique: 'Common Criteria EAL is not runtime posture hierarchy', rootCause: 'EAL1-EAL7 are product assurance evaluation levels.', resolution: 'Removed claim that runtime monotonicity satisfies EAL. Contrasted runtime escalation with static design assurance.', status: 'RESOLVED ✓' },
  { id: 30, category: 'Architecture', critique: 'Response actions not validated against safety requirements', rootCause: 'Offline batch evaluation cannot validate physical switching.', resolution: 'Documented offline batch evaluation boundaries in Section 6.7; distinguished physical actions from evaluated flow routing.', status: 'RESOLVED ✓' },
  { id: 31, category: 'Architecture', critique: 'Sub-second response claim unsupported', rootCause: '7 flows does not guarantee sub-second without arrival rate.', resolution: 'Removed unqualified sub-second claim; parameterized window sizing by flow velocity in Section 5.4.', status: 'RESOLVED ✓' },
  { id: 32, category: 'Architecture', critique: 'Adversary model and entity identity assumptions', rootCause: 'MAC/IP spoofing undermines host tracking.', resolution: 'Clarified that analysis unit is a sliding monitoring window of W=100 flows representing edge gateway traffic inspection.', status: 'RESOLVED ✓' },
  { id: 33, category: 'Architecture', critique: 'Topology model needs stronger sensitivity analysis', rootCause: 'Synthetic 120-node graph entity mapping unspecified.', resolution: 'Documented synthetic topology mapping, personalized PageRank calculation, and TARP threshold tau_R = 0.42.', status: 'RESOLVED ✓' },
  { id: 34, category: 'Publication', critique: 'Reference [1] bibliographically incorrect (now published!)', rootCause: 'Ref [1] was listed as "IEEE Access, under review, 2024".', resolution: 'Updated Ref [1] to published article: Journal of Cybersecurity and Privacy, vol. 6, no. 5, art. 181, pp. 1-28, Oct. 2026.', status: 'RESOLVED ✓' },
  { id: 35, category: 'Publication', critique: 'XGBoost Macro-F1 inconsistent with published paper', rootCause: 'Published reported 71.51%; manuscript reported 88.42%.', resolution: 'Reconciled: 71.51% across all 34 individual granular classes in [1]; 88.42% across consolidated 8 operational families.', status: 'RESOLVED ✓' },
  { id: 36, category: 'Publication', critique: 'Novelty boundary against Paper [1] needs clarity', rootCause: 'Needs explicit comparison of what is reused vs new.', resolution: 'Table 1 provides comprehensive 5-dimension comparison across detection, anomaly repair, dynamic trust, posture escalation, and policy optimization.', status: 'RESOLVED ✓' },
  { id: 37, category: 'Publication', critique: 'Paper not fully anonymized', rootCause: 'Target journal notes on title page; author initials in text.', resolution: 'Scrubbed all author initials and repository paths. Removed target journal note on title page.', status: 'RESOLVED ✓' },
  { id: 38, category: 'Publication', critique: 'Data/code availability needs concrete details', rootCause: 'Vague repository statement without commit/hashes.', resolution: 'Provided concrete repository link, dataset split scripts, model checkpoints, and SHA-256 integrity checksums (checksums.sha256).', status: 'RESOLVED ✓' }
];

export interface IFMetricRow {
  metric: string;
  contaminated: string;
  corrected: string;
  verdict: string;
}

export const TABLE3_IF_COMPARISON: IFMetricRow[] = [
  { metric: 'AUC (Benign vs Attack)', contaminated: '0.0296', corrected: '0.9567 (95% CI: [0.9482, 0.9564])', verdict: 'RESOLVED ✓' },
  { metric: 'Benign Mean Anomaly Score', contaminated: '1.0000 (Maximal)', corrected: '0.4352 (Clean Nominal)', verdict: 'RESOLVED ✓' },
  { metric: 'Attack Mean Anomaly Score', contaminated: '0.8770 (Nominal)', corrected: '0.9221 (Acute Anomaly)', verdict: 'RESOLVED ✓' },
  { metric: 'Anomaly Separation Gap', contaminated: '−0.1230 (Inverted)', corrected: '+0.4869 (Clean Positive)', verdict: 'RESOLVED ✓' },
  { metric: 'Benign Tail Exceedance (s ≥ 0.90)', contaminated: '100.00% (All flagged)', corrected: '4.99% (Under 5% target)', verdict: 'RESOLVED ✓' },
  { metric: 'Attack Tail Exceedance (s ≥ 0.90)', contaminated: '22.46% (Poor capture)', corrected: '62.72% (Strong capture)', verdict: 'RESOLVED ✓' },
  { metric: 'Kolmogorov-Smirnov Statistic D', contaminated: '0.6720 (Inverted)', corrected: '0.8659 (p < 10⁻¹⁵)', verdict: 'RESOLVED ✓' },
  { metric: 'Ensemble Hyperparameters', contaminated: 'M = 100 trees, 256 subsample', corrected: 'M = 200 trees, 50,000 clean subsample', verdict: 'CONFIGURED ✓' }
];

export interface CostMatrixRow {
  action: string;
  severityIndex: number;
  benignCost: number;
  containmentBenefit: number;
  netBenefitAttack: number;
  operationalDescription: string;
}

export const TABLE2_COST_MATRIX: CostMatrixRow[] = [
  { action: 'Allow', severityIndex: 0, benignCost: 0, containmentBenefit: 0, netBenefitAttack: 0, operationalDescription: 'Normal packet routing with zero inspection overhead (Baseline exposure = 0)' },
  { action: 'Alert', severityIndex: 1, benignCost: 1, containmentBenefit: -5, netBenefitAttack: 5, operationalDescription: 'Passive alert telemetry notification to SIEM with baseline security operations triage' },
  { action: 'Restrict', severityIndex: 2, benignCost: 3, containmentBenefit: -10, netBenefitAttack: 10, operationalDescription: 'QoS traffic rate-limiting, TCP window throttling, and token bucket policing applied' },
  { action: 'Quarantine', severityIndex: 3, benignCost: 15, containmentBenefit: -20, netBenefitAttack: 20, operationalDescription: 'Isolated VLAN sandboxing, restricted host access, and deep packet inspection' },
  { action: 'Block', severityIndex: 4, benignCost: 50, containmentBenefit: -50, netBenefitAttack: 50, operationalDescription: 'Immediate hardware flow-table TCAM drop, TCP RST termination, and BGP blackholing' }
];

export interface PostureLevelRow {
  level: string;
  name: string;
  evidenceCondition: string;
  trustCondition: string;
  centralityCondition: string;
  operationalMeaning: string;
  p2TierAction: string;
  pOptAction: string;
}

export const TABLE_POSTURE_LEVELS: PostureLevelRow[] = [
  {
    level: 'L0',
    name: 'Nominal Surveillance',
    evidenceCondition: 'S = 0',
    trustCondition: 'T_mean ≥ 60.0',
    centralityCondition: 'R_mean < 0.75',
    operationalMeaning: 'Zero threat evidence; healthy behavioral trust; nominal egress forwarding',
    p2TierAction: 'Allow',
    pOptAction: 'Allow'
  },
  {
    level: 'L1',
    name: 'Topology-Prior Monitoring',
    evidenceCondition: 'S = 1 (or S = 0)',
    trustCondition: 'T_mean ≥ 60.0 (or T < 60)',
    centralityCondition: 'R_mean ≥ 0.42',
    operationalMeaning: 'Single isolated signal (often c_topo) or mild trust decay; enhanced logging',
    p2TierAction: 'Alert',
    pOptAction: 'Allow'
  },
  {
    level: 'L2',
    name: 'Elevated Monitoring',
    evidenceCondition: 'S = 2',
    trustCondition: '20.0 ≤ T_mean < 60.0',
    centralityCondition: 'R_mean < 0.75',
    operationalMeaning: 'Two concurrent threat indicators; rate limiting / active deep telemetry inspection',
    p2TierAction: 'Restrict',
    pOptAction: 'Restrict'
  },
  {
    level: 'L3',
    name: 'Active Containment',
    evidenceCondition: 'S ≥ 3',
    trustCondition: 'T_mean > 20.0',
    centralityCondition: 'R_mean < 0.75',
    operationalMeaning: 'Three or more concurrent signals with moderate trust remaining; isolated sandboxing',
    p2TierAction: 'Quarantine',
    pOptAction: 'Restrict'
  },
  {
    level: 'L4',
    name: 'Severe Containment (Edge)',
    evidenceCondition: 'S ≥ 3',
    trustCondition: 'T_mean ≤ 20.0',
    centralityCondition: 'R_mean < 0.75',
    operationalMeaning: 'Acute threat saturation with depleted trust on peripheral edge gateways; port isolation',
    p2TierAction: 'Block',
    pOptAction: 'Block'
  },
  {
    level: 'L5',
    name: 'Critical Hub Containment',
    evidenceCondition: 'S ≥ 3',
    trustCondition: 'T_mean ≤ 20.0',
    centralityCondition: 'R_mean ≥ 0.75',
    operationalMeaning: 'Acute threat saturation on high-centrality core SDN transit hubs; immediate BGP shutdown',
    p2TierAction: 'Block',
    pOptAction: 'Block'
  }
];

export interface ActionPrecisionRow {
  policy: string;
  action: string;
  count: number;
  attackFlows: number;
  benignFlows: number;
  attackPrecision: string;
  benignFpr: string;
  status: string;
}

export const TABLE6_ACTION_PRECISION: ActionPrecisionRow[] = [
  { policy: 'P0 (Published Baseline)', action: 'Allow', count: 11609, attackFlows: 2, benignFlows: 11607, attackPrecision: '0.02%', benignFpr: '0.00%', status: 'Nominal' },
  { policy: 'P0 (Published Baseline)', action: 'Alert', count: 27287, attackFlows: 25864, benignFlows: 1423, attackPrecision: '94.79%', benignFpr: '4.76%', status: 'Alert Overflow' },
  { policy: 'P0 (Published Baseline)', action: 'Restrict', count: 17083, attackFlows: 298, benignFlows: 16785, attackPrecision: '1.74%', benignFpr: '56.16%', status: 'CATASTROPHIC INVERSION' },
  { policy: 'P0 (Published Baseline)', action: 'Quarantine', count: 4021, attackFlows: 3827, benignFlows: 194, attackPrecision: '95.18%', benignFpr: '0.65%', status: 'Under-utilized' },
  { policy: 'P0 (Published Baseline)', action: 'Block', count: 0, attackFlows: 0, benignFlows: 0, attackPrecision: '—', benignFpr: '0.00%', status: 'Unused (0%)' },

  { policy: 'P1 (Conservative Default)', action: 'Allow', count: 14200, attackFlows: 0, benignFlows: 14200, attackPrecision: '0.00%', benignFpr: '0.00%', status: 'Pure Benign ✓' },
  { policy: 'P1 (Conservative Default)', action: 'Alert', count: 20200, attackFlows: 8009, benignFlows: 12191, attackPrecision: '39.65%', benignFpr: '40.79%', status: 'Monotonic Escalation ✓' },
  { policy: 'P1 (Conservative Default)', action: 'Restrict', count: 7800, attackFlows: 4479, benignFlows: 3321, attackPrecision: '57.42%', benignFpr: '11.11%', status: '33× Precision Gain ✓' },
  { policy: 'P1 (Conservative Default)', action: 'Quarantine', count: 16300, attackFlows: 16003, benignFlows: 297, attackPrecision: '98.18%', benignFpr: '0.99%', status: 'High Purity Sandboxing ✓' },
  { policy: 'P1 (Conservative Default)', action: 'Block', count: 1500, attackFlows: 1500, benignFlows: 0, attackPrecision: '100.00%', benignFpr: '0.00%', status: '100% Precision Block ✓' },

  { policy: 'P2-tier (Recommended Operational)', action: 'Allow', count: 7700, attackFlows: 0, benignFlows: 7700, attackPrecision: '0.00%', benignFpr: '0.00%', status: 'Pure Benign ✓' },
  { policy: 'P2-tier (Recommended Operational)', action: 'Alert', count: 10300, attackFlows: 0, benignFlows: 10300, attackPrecision: '0.00%', benignFpr: '34.46%', status: 'Pre-Threat Monitoring ✓' },
  { policy: 'P2-tier (Recommended Operational)', action: 'Restrict', count: 5500, attackFlows: 2552, benignFlows: 2948, attackPrecision: '46.40%', benignFpr: '9.86%', status: 'Monotonic ✓' },
  { policy: 'P2-tier (Recommended Operational)', action: 'Quarantine', count: 18500, attackFlows: 9566, benignFlows: 8934, attackPrecision: '51.71%', benignFpr: '29.90%', status: 'VLAN Sandboxed ✓' },
  { policy: 'P2-tier (Recommended Operational)', action: 'Block', count: 18000, attackFlows: 18000, benignFlows: 0, attackPrecision: '100.00%', benignFpr: '0.00%', status: '0.00% Block FPR (Pure Attack) ✓' }
];

export interface MasterPolicyRow {
  policy: string;
  name: string;
  mapping: string;
  balancedNet: string;
  attackHeavyNet: string;
  combinedNet: string;
  balancedBlockFpr: string;
  attackHeavyBlockFpr: string;
  rank: string;
  badge: string;
}

export const TABLE7_MASTER_POLICIES: MasterPolicyRow[] = [
  { policy: 'P_opt', name: 'Global Cost-Optimal', mapping: 'Allow-Allow-Restrict-Restrict-Block-Block', balancedNet: '+985,534 OCU', attackHeavyNet: '+2,856,000 OCU', combinedNet: '+1,920,767 OCU', balancedBlockFpr: '0.00%', attackHeavyBlockFpr: '0.00%', rank: 'Rank 1 of 70', badge: 'Optimal OCU' },
  { policy: 'P2-tier', name: 'Recommended Operational', mapping: 'Allow-Alert-Restrict-Quarantine-Block-Block', balancedNet: '+963,686 OCU', attackHeavyNet: '+2,856,000 OCU', combinedNet: '+1,909,843 OCU', balancedBlockFpr: '0.00%', attackHeavyBlockFpr: '100.00%', rank: 'Rank 9 of 70 (Rank 1 Zero-FPR)', badge: 'Recommended Standard' },
  { policy: 'P_hybrid', name: 'Hybrid Posture + Benign Veto', mapping: 'L4 Posture Escalation + Flow Veto (C_g ≥ 0.90)', balancedNet: '+1,391,654 OCU', attackHeavyNet: '+2,974,176 OCU', combinedNet: '+2,044,425 OCU (50-run)', balancedBlockFpr: '0.72%', attackHeavyBlockFpr: 'N/A (0 Benign)', rank: 'Hybrid Dynamic', badge: 'Zero-Day Resilient' },
  { policy: 'P2', name: 'Aggressive Cost-Optimal', mapping: 'Allow-Restrict-Quarantine-Block-Block-Block', balancedNet: '+907,520 OCU', attackHeavyNet: '+2,856,000 OCU', combinedNet: '+1,881,760 OCU', balancedBlockFpr: '29.90%', attackHeavyBlockFpr: '100.00%', rank: 'Rank 28 of 70', badge: 'High Risk' },
  { policy: 'P1', name: 'Conservative Default', mapping: 'Allow-Alert-Restrict-Quarantine-Quarantine-Block', balancedNet: '+423,686 OCU', attackHeavyNet: '+1,149,600 OCU', combinedNet: '+786,643 OCU', balancedBlockFpr: '0.00%', attackHeavyBlockFpr: '0.00%', rank: 'Rank 44 of 70', badge: 'Conservative' },
  { policy: 'P0', name: 'Published Baseline [1]', mapping: 'Heuristic Rule (Alert/Quarantine)', balancedNet: '+153,952 OCU', attackHeavyNet: '+329,835 OCU', combinedNet: '+241,894 OCU', balancedBlockFpr: '0.00%', attackHeavyBlockFpr: '0.00%', rank: 'Unranked', badge: 'Contaminated Baseline' }
];

export interface ArchBaselineRow {
  architecture: string;
  paradigm: string;
  balancedMeanNet: string;
  floodMeanNet: string;
  overallMeanNet: string;
  balancedBlockFpr: string;
  balancedQuarFpr: string;
  operationalRole: string;
}

export const TABLE8B_ARCHITECTURAL_BASELINES: ArchBaselineRow[] = [
  { architecture: 'P_opt (Cost-Optimal Policy)', paradigm: 'Monotonic Posture Mapping (Π_70)', balancedMeanNet: '1,470,740 OCU', floodMeanNet: '2,962,515 OCU', overallMeanNet: '2,052,438 OCU', balancedBlockFpr: '0.80%', balancedQuarFpr: '0.00%', operationalRole: 'Rank 1 Global Level-to-Action Mapping' },
  { architecture: 'P2-tier (Canonical Reference)', paradigm: 'Multi-Stage Graduated Escalation', balancedMeanNet: '1,438,977 OCU', floodMeanNet: '2,967,682 OCU', overallMeanNet: '2,027,332 OCU', balancedBlockFpr: '0.80%', balancedQuarFpr: '9.56%', operationalRole: 'Reference 5-Action Escalation (0% Block on pure benign)' },
  { architecture: 'P_hybrid (Posture + Benign Veto)', paradigm: 'Hybrid Posture + Flow Veto (C_g ≥ 0.90)', balancedMeanNet: '1,391,654 OCU', floodMeanNet: '2,974,176 OCU', overallMeanNet: '2,044,425 OCU', balancedBlockFpr: '0.72%', balancedQuarFpr: '9.37%', operationalRole: 'Highest Flood Containment & Zero-Day Resilience' },
  { architecture: 'P_XGB (Confidence-Gated)', paradigm: 'Per-Flow Classifier (C_g ≥ 0.90)', balancedMeanNet: '1,472,830 OCU', floodMeanNet: '2,960,105 OCU', overallMeanNet: '2,053,543 OCU', balancedBlockFpr: '0.45%', balancedQuarFpr: '0.00%', operationalRole: 'Optimal on Closed-World Known Attacks' },
  { architecture: 'P_XGB (Ungated Raw)', paradigm: 'Per-Flow Classifier (Argmax)', balancedMeanNet: '1,360,450 OCU', floodMeanNet: '2,928,000 OCU', overallMeanNet: '2,144,225 OCU', balancedBlockFpr: '9.46%', balancedQuarFpr: '0.00%', operationalRole: 'Catastrophic Availability Violation (9.46% Block FPR)' }
];

export interface LOFORow {
  family: string;
  flows: number;
  xgbRecall: string;
  hybridRecall: string;
  optRecall: string;
  p2TierRecall: string;
  xgbNetOcu: number;
  hybridNetOcu: number;
  optNetOcu: number;
  p2TierNetOcu: number;
  generalizationAdvantage: string;
}

export const TABLE8D_LOFO: LOFORow[] = [
  { family: 'DDoS', flows: 22424, xgbRecall: '67.33%', hybridRecall: '74.06%', optRecall: '74.06%', p2TierRecall: '74.06%', xgbNetOcu: 497100, hybridNetOcu: 547872, optNetOcu: 547872, p2TierNetOcu: 532872, generalizationAdvantage: '+6.73% Recall / +$50.7k OCU' },
  { family: 'DoS', flows: 5328, xgbRecall: '83.74%', hybridRecall: '83.59%', optRecall: '83.59%', p2TierRecall: '83.59%', xgbNetOcu: 673900, hybridNetOcu: 672783, optNetOcu: 672783, p2TierNetOcu: 657783, generalizationAdvantage: 'Comparable (-0.15%)' },
  { family: 'Mirai', flows: 1788, xgbRecall: '0.33%', hybridRecall: '27.42%', optRecall: '27.42%', p2TierRecall: '27.42%', xgbNetOcu: 850, hybridNetOcu: 178713, optNetOcu: 178713, p2TierNetOcu: 163713, generalizationAdvantage: '83.1× Recall (+177.8k OCU) ★' },
  { family: 'Recon', flows: 235, xgbRecall: '13.41%', hybridRecall: '23.91%', optRecall: '23.91%', p2TierRecall: '23.91%', xgbNetOcu: 58950, hybridNetOcu: 93125, optNetOcu: 93125, p2TierNetOcu: 78125, generalizationAdvantage: '1.78× Recall (+34.2k OCU)' },
  { family: 'Spoofing', flows: 322, xgbRecall: '1.69%', hybridRecall: '4.19%', optRecall: '4.19%', p2TierRecall: '4.19%', xgbNetOcu: 10000, hybridNetOcu: 72480, optNetOcu: 72480, p2TierNetOcu: 57480, generalizationAdvantage: '2.48× Recall (+62.5k OCU)' },
  { family: 'Web', flows: 15, xgbRecall: '1.33%', hybridRecall: '9.83%', optRecall: '9.83%', p2TierRecall: '9.83%', xgbNetOcu: 400, hybridNetOcu: 3768, optNetOcu: 3768, p2TierNetOcu: 2268, generalizationAdvantage: '7.39× Recall (+3.4k OCU)' },
  { family: 'BruteForce', flows: 5, xgbRecall: '1.00%', hybridRecall: '2.67%', optRecall: '2.67%', p2TierRecall: '2.67%', xgbNetOcu: 100, hybridNetOcu: 1453, optNetOcu: 1453, p2TierNetOcu: -47, generalizationAdvantage: '2.67× Recall (+1.3k OCU)' }
];

export interface ThreatFamilyRow {
  family: string;
  flows: number;
  share: string;
  meanTrust: number;
  allowPct: string;
  alertPct: string;
  restrictPct: string;
  quarantinePct: string;
  blockPct: string;
  dominantAction: string;
}

export const TABLE8_PER_FAMILY: ThreatFamilyRow[] = [
  { family: 'Benign', flows: 29882, share: '49.80%', meanTrust: 64.88, allowPct: '25.8%', alertPct: '34.5%', restrictPct: '9.9%', quarantinePct: '29.9%', blockPct: '0.0%', dominantAction: 'Alert (Zero Block)' },
  { family: 'DDoS', flows: 22424, share: '37.37%', meanTrust: 10.13, allowPct: '0.0%', alertPct: '0.0%', restrictPct: '8.5%', quarantinePct: '31.7%', blockPct: '59.9%', dominantAction: 'Block' },
  { family: 'DoS', flows: 5328, share: '8.88%', meanTrust: 10.15, allowPct: '0.0%', alertPct: '0.0%', restrictPct: '8.4%', quarantinePct: '31.3%', blockPct: '60.3%', dominantAction: 'Block' },
  { family: 'Mirai', flows: 1788, share: '2.98%', meanTrust: 10.13, allowPct: '0.0%', alertPct: '0.0%', restrictPct: '8.4%', quarantinePct: '33.4%', blockPct: '58.2%', dominantAction: 'Block' },
  { family: 'Recon', flows: 235, share: '0.39%', meanTrust: 16.27, allowPct: '0.0%', alertPct: '0.0%', restrictPct: '11.1%', quarantinePct: '34.9%', blockPct: '54.0%', dominantAction: 'Block' },
  { family: 'Spoofing', flows: 322, share: '0.54%', meanTrust: 15.71, allowPct: '0.0%', alertPct: '0.0%', restrictPct: '9.9%', quarantinePct: '35.1%', blockPct: '55.0%', dominantAction: 'Block' },
  { family: 'Web', flows: 9, share: '0.01%', meanTrust: 16.03, allowPct: '0.0%', alertPct: '0.0%', restrictPct: '0.0%', quarantinePct: '22.2%', blockPct: '77.8%', dominantAction: 'Block' },
  { family: 'BruteForce', flows: 5, share: '0.01%', meanTrust: 14.04, allowPct: '0.0%', alertPct: '0.0%', restrictPct: '0.0%', quarantinePct: '40.0%', blockPct: '60.0%', dominantAction: 'Block' }
];

export interface CostSensitivityRow {
  lambda: number;
  blockPenalty: number;
  p1Benefit: string;
  p2TierBenefit: string;
  p2Benefit: string;
  p2TierAdvantage: string;
}

export const TABLE9_COST_SENSITIVITY: CostSensitivityRow[] = [
  { lambda: 0.2, blockPenalty: 10, p1Benefit: '+786,643 OCU', p2TierBenefit: '+1,938,643 OCU', p2Benefit: '+2,089,240 OCU', p2TierAdvantage: '2.46× over P1' },
  { lambda: 0.5, blockPenalty: 25, p1Benefit: '+786,643 OCU', p2TierBenefit: '+1,927,843 OCU', p2Benefit: '+2,011,435 OCU', p2TierAdvantage: '2.45× over P1' },
  { lambda: 1.0, blockPenalty: 50, p1Benefit: '+786,643 OCU', p2TierBenefit: '+1,909,843 OCU', p2Benefit: '+1,881,760 OCU', p2TierAdvantage: '2.43× over P1' },
  { lambda: 1.5, blockPenalty: 75, p1Benefit: '+786,643 OCU', p2TierBenefit: '+1,891,843 OCU', p2Benefit: '+1,752,085 OCU', p2TierAdvantage: '2.40× over P1' },
  { lambda: 2.0, blockPenalty: 100, p1Benefit: '+786,643 OCU', p2TierBenefit: '+1,873,843 OCU', p2Benefit: '+1,622,410 OCU', p2TierAdvantage: '2.38× over P1' },
  { lambda: 3.0, blockPenalty: 150, p1Benefit: '+786,643 OCU', p2TierBenefit: '+1,837,843 OCU', p2Benefit: '+1,363,060 OCU', p2TierAdvantage: '2.34× over P1' },
  { lambda: 4.0, blockPenalty: 200, p1Benefit: '+786,643 OCU', p2TierBenefit: '+1,801,843 OCU', p2Benefit: '+1,103,710 OCU', p2TierAdvantage: '2.29× over P1' },
  { lambda: 5.0, blockPenalty: 250, p1Benefit: '+786,643 OCU', p2TierBenefit: '+1,765,843 OCU', p2Benefit: '+844,360 OCU', p2TierAdvantage: '2.24× over P1' }
];

export interface TopologyConfoundRow {
  metric: string;
  observed: string;
  permMean: string;
  permStd: string;
  permCi95: string;
  pValue: string;
  status: string;
}

export const TABLE_TOPOLOGY_CONFOUND: TopologyConfoundRow[] = [
  { metric: 'Posture Monotonicity Rate', observed: '1.000', permMean: '0.945', permStd: '0.228', permCi95: '[0.000, 1.000]', pValue: '1.000', status: 'ROBUST ✓' },
  { metric: 'P1 Net Benefit (OCU)', observed: '446,388', permMean: '442,533', permStd: '5,369', permCi95: '[433,603, 454,530]', pValue: '0.476', status: 'ROBUST ✓' },
  { metric: 'P2-tier Net Benefit (OCU)', observed: '974,983', permMean: '973,530', permStd: '1,089', permCi95: '[971,449, 975,555]', pValue: '0.188', status: 'ROBUST ✓' },
  { metric: 'P_opt Net Benefit (OCU)', observed: '986,315', permMean: '985,756', permStd: '360', permCi95: '[985,534, 986,315]', pValue: '0.254', status: 'ROBUST ✓' },
  { metric: 'L0 Attack Density', observed: '0.000 (0.0%)', permMean: '0.000', permStd: '0.000', permCi95: '[0.000, 0.000]', pValue: '1.000', status: 'ROBUST ✓' },
  { metric: 'L1 Attack Density', observed: '0.000 (0.0%)', permMean: '0.000', permStd: '0.000', permCi95: '[0.000, 0.000]', pValue: '1.000', status: 'ROBUST ✓' },
  { metric: 'L2 Attack Density', observed: '0.466 (46.6%)', permMean: '0.465', permStd: '0.002', permCi95: '[0.462, 0.468]', pValue: '0.518', status: 'ROBUST ✓' },
  { metric: 'L3 Attack Density', observed: '0.526 (52.6%)', permMean: '0.525', permStd: '0.002', permCi95: '[0.521, 0.528]', pValue: '0.660', status: 'ROBUST ✓' },
  { metric: 'L4 Attack Density', observed: '0.998 (99.8%)', permMean: '0.999', permStd: '0.001', permCi95: '[0.998, 1.000]', pValue: '0.062', status: 'ROBUST ✓' },
  { metric: 'L5 Attack Density', observed: '1.000 (100.0%)', permMean: '0.994', permStd: '0.026', permCi95: '[0.907, 1.000]', pValue: '1.000', status: 'ROBUST ✓' }
];

export interface RegimeRow {
  regime: string;
  flows: string;
  batches: number;
  attackRate: string;
  composition: string;
  purpose: string;
}

export const TABLE_REGIMES: RegimeRow[] = [
  { regime: 'Balanced Multi-State', flows: '60,000', batches: 600, attackRate: '50.20%', composition: '180 pure benign, 240 mixed (binomial p=0.50), 180 pure attack batches', purpose: 'Evaluates graduated posture escalation and precision monotonicity across threat phases' },
  { regime: 'Attack-Heavy Surge', flows: '60,000', batches: 600, attackRate: '97.60%', composition: 'Contiguous test slice matching empirical high-rate volumetric DDoS/Mirai floods', purpose: 'Evaluates high-volume threat containment benefit and measures collateral benign blocking' },
  { regime: 'Multi-State Phase Transition', flows: '60,000', batches: 600, attackRate: '50.20%', composition: 'Sequential phase transitions (Nominal → Probe → Lateral → Flood → Recovery)', purpose: 'Validates hysteresis latching and cooldown de-escalation over continuous time' },
  { regime: 'Unstratified Shuffled', flows: '60,000', batches: 600, attackRate: '50.20%', composition: '60k flows randomly interleaved without batch purity stratification', purpose: 'Assesses sensitivity to batch structuring and measures worst-case unstratified disruption' },
  { regime: 'Pure Volumetric Flood', flows: '60,000', batches: 600, attackRate: '100.00%', composition: '60,000 consecutive attack flows across DDoS, DoS, and Mirai attack families', purpose: 'Measures maximum threat containment reward under total malicious link saturation' }
];

export const SCHEMA_46_FEATURES = [
  'flow_duration', 'Header_Length', 'Protocol Type', 'Duration', 'Rate', 'Srate', 'Drate',
  'fin_flag_number', 'syn_flag_number', 'rst_flag_number', 'psh_flag_number', 'ack_flag_number',
  'ece_flag_number', 'cwr_flag_number', 'ack_count', 'syn_count', 'fin_count', 'urg_count',
  'rst_count', 'HTTP', 'HTTPS', 'DNS', 'Telnet', 'SMTP', 'SSH', 'IRC', 'TCP', 'UDP',
  'DHCP', 'ARP', 'ICMP', 'IPv', 'LLC', 'Tot sum', 'Min', 'Max', 'AVG', 'Std', 'Tot size',
  'IAT', 'Number', 'Magnitue', 'Radius', 'Covariance', 'Variance', 'Weight'
];

// Raw JSON Bundled Exports
export const POLICIES_70_DATA = POLICIES_70_RAW;
export const EXPERIMENTS_INVENTORY_DATA = EXPERIMENTS_INVENTORY_RAW;
export const LATENCY_DATA = LATENCY_RAW;
export const THROUGHPUT_DATA = THROUGHPUT_RAW;

// Interactive Chart Datasets for Recharts
export const ANOMALY_DENSITY_DATA = [
  { score: 0.05, benign: 12.4, attack: 0.1 },
  { score: 0.15, benign: 38.6, attack: 0.2 },
  { score: 0.25, benign: 64.2, attack: 0.5 },
  { score: 0.35, benign: 88.5, attack: 1.2 },
  { score: 0.45, benign: 52.1, attack: 2.8 },
  { score: 0.50, benign: 24.3, attack: 6.4 }, // Threshold tau = 0.50
  { score: 0.55, benign: 10.2, attack: 14.5 },
  { score: 0.65, benign: 4.1, attack: 36.8 },
  { score: 0.75, benign: 1.8, attack: 68.4 },
  { score: 0.85, benign: 0.6, attack: 94.2 },
  { score: 0.95, benign: 0.1, attack: 128.5 }
];

export const TRUST_TIMELINE_DATA = [
  { batch: 1, phase: 'Nominal', Benign: 99.4, DDoS: 99.2, Mirai: 99.1 },
  { batch: 50, phase: 'Nominal', Benign: 98.6, DDoS: 98.4, Mirai: 98.5 },
  { batch: 100, phase: 'Nominal', Benign: 99.1, DDoS: 98.8, Mirai: 98.9 },
  { batch: 181, phase: 'Attack Onset', Benign: 97.5, DDoS: 42.1, Mirai: 10.0 }, // Hard reset T=10
  { batch: 220, phase: 'Sustained Flood', Benign: 98.0, DDoS: 10.1, Mirai: 10.0 },
  { batch: 300, phase: 'Sustained Flood', Benign: 96.8, DDoS: 10.1, Mirai: 10.0 },
  { batch: 380, phase: 'Sustained Flood', Benign: 97.4, DDoS: 10.1, Mirai: 10.0 },
  { batch: 421, phase: 'Recovery Transition', Benign: 97.8, DDoS: 38.4, Mirai: 32.1 },
  { batch: 500, phase: 'Benign Recovery', Benign: 98.9, DDoS: 84.5, Mirai: 81.2 },
  { batch: 600, phase: 'Full Restitution', Benign: 99.3, DDoS: 97.6, Mirai: 96.8 }
];

export const POLICY_BAR_DATA = [
  { name: 'P_opt (Rank 1)', balanced: 985534, flood: 2856000, combined: 1920767 },
  { name: 'P2-tier (Rank 9)', balanced: 963686, flood: 2856000, combined: 1909843 },
  { name: 'P_hybrid', balanced: 1391654, flood: 2974176, combined: 2044425 },
  { name: 'P2 (Unconstrained)', balanced: 907520, flood: 2856000, combined: 1881760 },
  { name: 'P1 (Conservative)', balanced: 423686, flood: 1149600, combined: 786643 },
  { name: 'P0 (Baseline [1])', balanced: 153952, flood: 329835, combined: 241894 }
];

export const LOFO_BAR_DATA = [
  { family: 'DDoS', XGBoost: 67.33, Hybrid: 74.06, PostureOpt: 74.06 },
  { family: 'DoS', XGBoost: 83.74, Hybrid: 83.59, PostureOpt: 83.59 },
  { family: 'Mirai', XGBoost: 0.33, Hybrid: 27.42, PostureOpt: 27.42 }, // 83x spike!
  { family: 'Recon', XGBoost: 13.41, Hybrid: 23.91, PostureOpt: 23.91 },
  { family: 'Spoofing', XGBoost: 1.69, Hybrid: 4.19, PostureOpt: 4.19 },
  { family: 'Web', XGBoost: 1.33, Hybrid: 9.83, PostureOpt: 9.83 },
  { family: 'BruteForce', XGBoost: 1.00, Hybrid: 2.67, PostureOpt: 2.67 }
];
