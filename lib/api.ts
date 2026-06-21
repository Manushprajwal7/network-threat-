/**
 * API service layer — all communication with the Flask backend.
 *
 * Base URL is read from NEXT_PUBLIC_BACKEND_URL (defaults to localhost:5000).
 * Every function throws on network / HTTP error so callers can show error states.
 */

const BASE =
  process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, '') ?? 'http://localhost:5000';

async function apiFetch<T = unknown>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`HTTP ${res.status}: ${body || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface LiveEvent {
  id: string;
  timestamp: string;
  timestamp_unix: number;
  source_ip: string | null;
  dest_ip: string | null;
  source_port: number | null;
  dest_port: number | null;
  protocol: string;
  packet_length: number;
  predicted_label: string;
  confidence: number;        // 0–1
  risk_level: string;        // Low / Medium / High / Critical
  trust_score: number;       // 0–100
  trust_level: string;
  user_trust: number;        // 0–100
  device_trust: number;      // 0–100
  behavior_trust: number;    // 0–100
  action: string;
  reason: string;
  policy_level: string;
  severity: string;          // low / medium / high / critical
}

export interface DashboardStats {
  total_packets: number;
  active_flows: number;
  threats_detected: number;
  average_trust_score: number;  // 0–1
  blocked_connections: number;
  model_confidence: number;     // 0–1
  benign_count: number;
  attack_count: number;
  critical_count: number;
  high_risk_count: number;
  source: string;
  timestamp: string;
}

export interface ThreatDistItem {
  name: string;
  count: number;
  percentage: number;
  color: string;
}

export interface EntityTrust {
  id: string;
  name: string;
  ip: string;
  userTrust: number;       // 0–1
  deviceTrust: number;     // 0–1
  behaviorTrust: number;   // 0–1
  finalTrust: number;      // 0–1
  riskLevel: string;
  status: string;
}

export interface TrustSummary {
  average_trust_score: number;  // 0–1
  high_trust_entities: number;
  medium_trust_entities: number;
  low_trust_entities: number;
  entity_list: EntityTrust[];
  timestamp?: string;
}

export interface Alert {
  id: string;
  severity: string;
  message: string;
  time: string;
  acked: boolean;
}

export interface NetworkFlow {
  id: string;
  srcIP: string;
  dstIP: string;
  protocol: string;
  packetCount: number;
  flowDuration: string;
  bytes: string;
  status: string;
  attackType: string;
}

export interface CaptureStatus {
  is_running: boolean;
  selected_interface: string | null;
  resolved_interface: string | null;
  packets_captured: number;
  events_analyzed: number;
  packets_failed: number;
  raw_packets_seen: number;
  tshark_available: boolean;
  tshark_path: string | null;
  tshark_error: string | null;
  ml_ready: boolean;
  error: string | null;
  last_packet_error: string | null;
  uptime_seconds: number;
}

export interface HealthStatus {
  backend: string;
  models_loaded: boolean;
  available_models: string[];
  primary_model: string | null;
  tshark_available: boolean;
  tshark_info: string;
  timestamp: string;
}

export interface DebugInfo {
  ml_ready: boolean;
  events_in_queue: number;
  packets_captured: number;
  events_analyzed: number;
  packets_failed: number;
  last_error: string | null;
  sample_events: unknown[];
  timestamp: string;
}

export interface ModelComparisonRow {
  model_name: string;
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
  [key: string]: string | number | undefined;
}

export interface NetworkInterface {
  index: string;
  name: string;
  device: string;
}

export interface TrafficPoint {
  time: string;
  normal: number;
  threats: number;
  packets: number;
}

export interface TopologyNode {
  id: string;
  packet_count: number;
  threat_count: number;
  trust_score: number;
  risk_level: string;
  protocols: string[];
  actions: string[];
  is_local: boolean;
}

export interface TopologyEdge {
  source: string;
  target: string;
  count: number;
  protocols: string[];
  bytes: number;
  has_threat: boolean;
}

export interface TopologyData {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
  total_events: number;
  timestamp?: string;
}

// ── API functions ─────────────────────────────────────────────────────────────

export const getDashboardStats = () =>
  apiFetch<DashboardStats>('/api/dashboard-stats');

export const getLiveEvents = (limit = 50) =>
  apiFetch<{ events: LiveEvent[]; count: number }>(`/api/live-events?limit=${limit}`);

export const getThreatDistribution = () =>
  apiFetch<{ distribution: ThreatDistItem[]; total_events: number }>('/api/threat-distribution');

export const getTrustSummary = () =>
  apiFetch<TrustSummary>('/api/trust-summary');

export const getRecentAlerts = (limit = 20) =>
  apiFetch<{ alerts: Alert[]; count: number }>(`/api/recent-alerts?limit=${limit}`);

export const getNetworkFlows = (limit = 25) =>
  apiFetch<{ flows: NetworkFlow[]; count: number }>(`/api/network-flows?limit=${limit}`);

export const getTrafficTrend = () =>
  apiFetch<{ trend: TrafficPoint[] }>('/api/traffic-trend');

export const getSecurityDecisions = () =>
  apiFetch<{ decisions: Record<string, { count: number; percentage: number }> }>(
    '/api/security-decisions'
  );

export const getInterfaces = () =>
  apiFetch<{ interfaces: NetworkInterface[]; tshark_available: boolean; default_index: string | null; error?: string }>(
    '/api/interfaces'
  );

export const startCapture = (interfaceName: string) =>
  apiFetch<{ ok: boolean; error?: string }>('/api/capture/start', {
    method: 'POST',
    body: JSON.stringify({ interface: interfaceName }),
  });

export const stopCapture = () =>
  apiFetch<{ ok: boolean; error?: string }>('/api/capture/stop', {
    method: 'POST',
  });

export const getCaptureStatus = () =>
  apiFetch<CaptureStatus>('/api/capture/status');

export const getHealth = () =>
  apiFetch<HealthStatus>('/health');

export const getDebugInfo = () =>
  apiFetch<DebugInfo>('/api/debug');

export const getModelComparison = () =>
  apiFetch<{ models: ModelComparisonRow[]; count: number }>('/api/model-comparison');

export const getTopology = () =>
  apiFetch<TopologyData>('/api/topology');

// ── Evaluation / Research types ───────────────────────────────────────────────

export interface EvalModelRow {
  model: string;
  accuracy: number;
  balanced_accuracy?: number;
  precision: number;
  recall: number;
  f1_score: number;
  macro_precision?: number;
  macro_recall?: number;
  macro_f1?: number;
  attack_detection_rate?: number;
  train_time_s: number;
  pred_time_s: number;
}

export interface EvalSummary {
  models: EvalModelRow[];
  count: number;
  best_model: string;
  best_f1: number;
  best_macro_f1: number | null;
  best_attack_detect: number | null;
  best_accuracy: number;
  experiment: {
    dataset: string;
    split_strategy: string;
    deduplication: string;
    outlier_clipping: string;
    num_features: number;
    num_classes: number;
    attack_classes: string[];
    models_trained: string[];
    primary_model: string;
    trained_at: string | null;
    framework: string;
    python_version: string;
    evaluation_metric: string;
    reference_paper: string;
  };
  reports_available: {
    model_comparison: boolean;
    classification_report: boolean;
    confusion_matrix: boolean;
  };
  timestamp: string;
}

export interface PerClassEntry {
  class: string;
  precision: number;
  recall: number;
  f1: number;
  support: number;
}

export interface PerClassMetrics {
  primary_model: string;
  classes: PerClassEntry[];
  total_support: number;
  macro_f1: number;
  attack_detection_rate: number;
  timestamp: string;
}

export interface LatencyEntry {
  model: string;
  pred_time_ms: number;
  pred_time_s: number;
  train_time_s: number;
  realtime_ok: boolean;
}

export interface TrustSample {
  ts: string;
  score: number;
  entity: string;
}

export interface ExperimentEntry {
  run_id: string;
  model: string;
  split: string;
  dedup: string;
  clipping: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  train_time_s: number;
  pred_time_ms: number;
  status: string;
  trained_at: string;
}

export interface ExperimentLog {
  experiment_name: string;
  paper_title: string;
  dataset: string;
  entries: ExperimentEntry[];
  total: number;
  timestamp: string;
}

// ── Evaluation API functions ──────────────────────────────────────────────────

export const getEvalSummary = () =>
  apiFetch<EvalSummary>('/api/evaluation/summary');

export const getPerClassMetrics = () =>
  apiFetch<PerClassMetrics>('/api/evaluation/per-class');

export const getConfusionMatrixImage = () =>
  apiFetch<{ available: boolean; image_base64?: string; format?: string }>('/api/evaluation/confusion-matrix');

export const getLatencyBreakdown = () =>
  apiFetch<{ latency: LatencyEntry[]; fastest: string; slowest: string }>('/api/evaluation/latency');

export const getTrustTrend = () =>
  apiFetch<{ samples: TrustSample[]; source: string }>('/api/evaluation/trust-trend');

export const getExperimentLog = () =>
  apiFetch<ExperimentLog>('/api/evaluation/experiment-log');

export const getExportCsvUrl = () => `${BASE}/api/evaluation/export/csv`;

// ── Simulation types ──────────────────────────────────────────────────────────

export type SimType = 'dos' | 'portscan' | 'bruteforce' | 'botnet' | 'unknown';

export interface SimStatus {
  running: boolean;
  sim_type: SimType | null;
  duration: number;
  elapsed_seconds: number;
  remaining_seconds: number;
  events_generated: number;
}

export interface SimEvent {
  id: string;
  sequence: number;
  timestamp: string;
  simulation: true;
  sim_type: SimType;
  attack_type: string;
  risk_level: string;
  source_ip: string;
  dest_ip: string;
  source_port: number;
  dest_port: number;
  protocol: string;
  safety_label: string;
  predicted_attack?: string;
  confidence?: number;
  anomaly_score?: number;
  trust_score?: number;
  trust_level?: string;
  security_action?: string;
  known_or_unknown?: string;
  description?: string;
  [key: string]: unknown;
}

export interface BlockedEntity {
  ip: string;
  reason: string;
  action: string;
  count: number;
  timestamp: string;
  mode: string;
}

export interface BlockHistory {
  event: 'block' | 'unblock';
  ip: string;
  reason: string;
  timestamp: string;
}

// ── Simulation API functions ──────────────────────────────────────────────────

export const startSimulation = (type: SimType, duration_seconds = 30) =>
  apiFetch<{ ok: boolean; sim_type: string; duration: number; error?: string }>(
    '/api/simulation/start', {
      method: 'POST',
      body: JSON.stringify({ type, duration_seconds }),
    }
  );

export const stopSimulation = () =>
  apiFetch<{ ok: boolean; events_generated: number; error?: string }>(
    '/api/simulation/stop', { method: 'POST' }
  );

export const getSimulationStatus = () =>
  apiFetch<SimStatus>('/api/simulation/status');

export const getSimulationEvents = (limit = 50) =>
  apiFetch<{ events: SimEvent[]; count: number; timestamp: string }>(
    `/api/simulation/events?limit=${limit}`
  );

// ── Blocking API functions ────────────────────────────────────────────────────

export const getBlockedEntities = () =>
  apiFetch<{ entities: BlockedEntity[]; count: number; mode: string }>(
    '/api/blocked-entities'
  );

export const blockEntity = (ip: string, reason: string) =>
  apiFetch<{ ok: boolean; ip: string; action: string; error?: string }>(
    '/api/block', {
      method: 'POST',
      body: JSON.stringify({ ip, reason }),
    }
  );

export const unblockEntity = (ip: string) =>
  apiFetch<{ ok: boolean; ip: string; error?: string }>(
    '/api/unblock', {
      method: 'POST',
      body: JSON.stringify({ ip }),
    }
  );

export const getBlockHistory = (limit = 50) =>
  apiFetch<{ history: BlockHistory[]; count: number }>(
    `/api/block-history?limit=${limit}`
  );

// ── Research report ───────────────────────────────────────────────────────────

export const getResearchReport = () =>
  apiFetch<Record<string, unknown>>('/api/research-report');

export const getResearchReportCsvUrl = () => `${BASE}/api/research-report/csv`;

// ── Research Results API ──────────────────────────────────────────────────────

export interface ResearchModelRow {
  model_name:            string;
  display_name:          string;
  split_mode:            string;
  accuracy:              number;
  balanced_accuracy:     number;
  precision:             number;
  recall:                number;
  f1_score:              number;
  macro_precision:       number;
  macro_recall:          number;
  macro_f1:              number;
  attack_detection_rate: number;
  false_positive_rate:   number;
  false_negative_rate:   number;
  roc_auc:               number | null;
  train_time_s:          number;
  pred_time_s:           number;
  rank:                  number;
}

export interface ResearchComparison {
  models:       ResearchModelRow[];
  count:        number;
  best_model:   string;
  best_macro_f1:number;
  best_adr:     number;
  best_accuracy:number;
  split_mode:   string;
  dataset:      string;
  num_features: number;
  num_classes:  number;
  metric_note:  string;
  timestamp:    string;
}

export interface ResearchPerClassRow {
  model:        string;
  display_name: string;
  class:        string;
  precision:    number;
  recall:       number;
  f1:           number;
  support:      number;
}

export interface ResearchPerClass {
  classes:     ResearchPerClassRow[];
  models_data: Record<string, { rows: ResearchPerClassRow[]; summary: { best_class: string; best_f1: number; worst_class: string; worst_f1: number; adr: number } }>;
  model_list:  string[];
  display_map: Record<string, string>;
  total_rows:  number;
  timestamp:   string;
}

export interface ResearchLatencyRow {
  model:          string;
  display_name:   string;
  train_time_s:   number;
  pred_time_s:    number;
  pred_time_ms:   number;
  per_sample_us:  number;
  realtime_ok:    boolean;
  inference_note: string;
}

export interface ResearchLatency {
  latency:        ResearchLatencyRow[];
  fastest_train:  string;
  count:          number;
  note:           string;
  timestamp:      string;
}

export interface ResearchConfusionMatrix {
  available:    boolean;
  model:        string;
  display_name: string;
  image_base64: string | null;
  format:       string;
  size_bytes:   number;
  timestamp:    string;
}

export const getResearchComparison = () =>
  apiFetch<ResearchComparison>('/api/research/model-comparison');

export const getResearchPerClass = () =>
  apiFetch<ResearchPerClass>('/api/research/per-class-metrics');

export const getResearchLatency = () =>
  apiFetch<ResearchLatency>('/api/research/latency-report');

export const getResearchSummaryText = () =>
  apiFetch<{ content: string; timestamp: string }>('/api/research/summary');

export const getResearchConfusionMatrix = (modelName: string) =>
  apiFetch<ResearchConfusionMatrix>(`/api/research/confusion-matrix/${modelName}`);

export const getResearchConfusionMatrixList = () =>
  apiFetch<{ matrices: Array<{ model: string; display_name: string; available: boolean; size_bytes: number }> }>(
    '/api/research/confusion-matrix-list'
  );

export const researchExportUrls = {
  modelComparisonCsv: () => `${BASE}/api/research/export/model-comparison-csv`,
  perClassCsv:        () => `${BASE}/api/research/export/per-class-csv`,
  summaryTxt:         () => `${BASE}/api/research/export/summary-txt`,
  confusionMatrix:    (model: string) => `${BASE}/api/research/export/confusion-matrix/${model}`,
};

// ── Normalisation helpers (used by components) ────────────────────────────────

/** Convert backend trust score (0–100) to 0–1 fraction. */
export const normTrust = (v: number) => Math.round(v) / 100;

/** Map action string to flow status key used by NetworkMonitor. */
export const actionToStatus = (action: string): string =>
  ({ Allow: 'allowed', Restrict: 'restricted', Alert: 'alerted', Quarantine: 'quarantined', Block: 'blocked' }[
    action
  ] ?? 'allowed');
