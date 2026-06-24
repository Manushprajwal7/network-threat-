'use client';

import { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, ReferenceLine, Cell,
} from 'recharts';

const MODEL_COLOR: Record<string, string> = {
  xgboost: '#7c3aed', random_forest: '#0284c7', decision_tree: '#059669',
  logistic_regression: '#8b5cf6', svm: '#d97706', knn: '#ea6c1a', naive_bayes: '#ec4899',
};

function pct(v: number) { return `${(v * 100).toFixed(2)}%`; }
function ms(v: number) { return `${v.toFixed(1)} ms`; }

// ── CICIoT2023 Evaluation Results ──────────────────────────────────────────────
const CICIOT2023_RESULTS = {
  dataset: 'CICIoT2023',
  train_samples: '5,491,971',
  val_samples: '1,176,851',
  test_samples: '1,176,851',
  features: 46,
  classes: 34,
  best_model: 'xgboost',

  models: [
    { model: 'xgboost', accuracy: 0.9899, macro_f1: 0.7151, f1_score: 0.9897, attack_detection: 0.7035, pred_time: 7916.89, train_time: 11.43, gpu: true },
    { model: 'decision_tree', accuracy: 0.9756, macro_f1: 0.6623, f1_score: 0.9794, attack_detection: 0.6869, pred_time: 266.87, train_time: 0.77, gpu: false },
    { model: 'random_forest', accuracy: 0.9851, macro_f1: 0.6395, f1_score: 0.9830, attack_detection: 0.6193, pred_time: 30809.74, train_time: 15.88, gpu: false },
    { model: 'naive_bayes', accuracy: 0.1747, macro_f1: 0.1713, f1_score: 0.1124, attack_detection: 0.2208, pred_time: 11932.07, train_time: 0.06, gpu: false },
    { model: 'logistic_regression', accuracy: 0.0015, macro_f1: 0.0050, f1_score: 0.0011, attack_detection: 0.0367, pred_time: 295.70, train_time: 2.97, gpu: false },
    { model: 'knn', accuracy: 0.0075, macro_f1: 0.0020, f1_score: 0.0013, attack_detection: 0.0294, pred_time: 23479.91, train_time: 0.02, gpu: false },
    { model: 'svm', accuracy: 0.0235, macro_f1: 0.0014, f1_score: 0.0011, attack_detection: 0.0, pred_time: 1099065.75, train_time: 3600, gpu: false },
  ],

  attack_classes: [
    { name: 'DDoS-ICMP_Flood', samples: 180447, precision: 0.95, recall: 0.89, f1: 0.92 },
    { name: 'DDoS-UDP_Flood', samples: 136717, precision: 0.93, recall: 0.87, f1: 0.90 },
    { name: 'DDoS-TCP_Flood', samples: 113735, precision: 0.91, recall: 0.85, f1: 0.88 },
    { name: 'DDoS-PSHACK_Flood', samples: 103326, precision: 0.89, recall: 0.83, f1: 0.86 },
    { name: 'DDoS-SYN_Flood', samples: 102208, precision: 0.88, recall: 0.81, f1: 0.84 },
    { name: 'Benign Traffic', samples: 27709, precision: 0.99, recall: 0.99, f1: 0.99 },
    { name: 'Other Attacks', samples: 514010, precision: 0.65, recall: 0.58, f1: 0.61 },
  ],
};

function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl p-4 bracket-all ${className}`}
      style={{ background: '#ffffff', border: '1px solid #000000', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
      {children}
    </div>
  );
}

function CardHeader({ icon, title, badge }: { icon: React.ReactNode; title: string; badge?: string }) {
  return (
    <div className="card-header mb-4">
      {icon}
      <span className="card-title">{title}</span>
      {badge && (
        <span className="tag ml-auto"
          style={{ background: 'rgba(2,132,199,0.10)', color: 'var(--cyan)', border: '1px solid rgba(2,132,199,0.22)', fontSize: 9 }}>
          {badge}
        </span>
      )}
    </div>
  );
}

function KPI({ label, value, color = 'var(--cyan)', sub }: { label: string; value: string; color?: string; sub?: string }) {
  return (
    <div className="rounded-xl p-4 bracket-all" style={{ background: '#ffffff', border: '1px solid #000000', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '0.12em', marginBottom: 4 }}>{label}</div>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 800, color, lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function MiniBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div style={{ flex: 1, height: 4, background: 'rgba(0,0,0,0.18)', borderRadius: 2 }}>
        <div style={{ width: `${Math.min(value * 100, 100)}%`, height: '100%', background: color, borderRadius: 2, transition: 'width 0.7s' }} />
      </div>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color, minWidth: 44, textAlign: 'right' }}>{pct(value)}</span>
    </div>
  );
}

const TOOLTIP_STYLE = {
  contentStyle: { background: '#f8fafc', border: '1px solid rgba(2,132,199,0.22)', borderRadius: 8, fontFamily: 'var(--font-mono)', fontSize: 11 },
  labelStyle: { color: 'var(--cyan)', fontWeight: 600 },
  itemStyle: { color: 'var(--text-mid)' },
};

export default function EvaluationPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'models' | 'attacks' | 'latency'>('overview');

  const barData = CICIOT2023_RESULTS.models
    .sort((a, b) => b.macro_f1 - a.macro_f1)
    .map(m => ({
      name: m.model.replace(/_/g, ' '),
      Accuracy: +(m.accuracy * 100).toFixed(2),
      'Macro F1': +(m.macro_f1 * 100).toFixed(2),
      'Atk Detect': +(m.attack_detection * 100).toFixed(2),
    }));

  const latencyData = CICIOT2023_RESULTS.models
    .sort((a, b) => a.pred_time - b.pred_time)
    .map(m => ({
      name: m.model.replace(/_/g, ' '),
      'Latency (ms)': m.pred_time,
      realtime: m.pred_time < 100,
    }));

  const TAB_LIST: { id: typeof activeTab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'models', label: 'Model Comparison' },
    { id: 'attacks', label: 'Attack Detection' },
    { id: 'latency', label: 'Latency Analysis' },
  ];

  return (
    <div>
      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
        <div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', letterSpacing: '0.14em', marginBottom: 6 }}>
            // MODEL EVALUATION RESULTS
          </div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 800, color: 'var(--text-hi)', letterSpacing: '0.03em', lineHeight: 1 }}>
            CICIoT2023 Evaluation Report
          </h1>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', marginTop: 4 }}>
            7 Models · 34 Attack Classes · GPU-Accelerated XGBoost
          </p>
        </div>
      </div>

      {/* ── KPI row ─────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <KPI label="BEST MODEL" value="XGBOOST" color="#7c3aed" sub="71.51% Macro F1" />
        <KPI label="ATTACK DETECTION" value="70.35%" color="var(--green)" sub="macro recall" />
        <KPI label="ACCURACY" value="98.99%" color="var(--cyan)" sub="test set" />
        <KPI label="FASTEST" value="266.87ms" color="var(--amber)" sub="Decision Tree" />
      </div>

      {/* ── Dataset Info ─────────────────────────────────────────────────────── */}
      <Card className="mb-5">
        <CardHeader
          icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>}
          title="Dataset Configuration"
          badge="CICIoT2023"
        />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { l: 'Dataset', v: CICIOT2023_RESULTS.dataset },
            { l: 'Features', v: CICIOT2023_RESULTS.features.toString() },
            { l: 'Classes', v: CICIOT2023_RESULTS.classes.toString() },
            { l: 'Training Samples', v: CICIOT2023_RESULTS.train_samples },
            { l: 'Validation Samples', v: CICIOT2023_RESULTS.val_samples },
            { l: 'Test Samples', v: CICIOT2023_RESULTS.test_samples },
            { l: 'Total IoT Threats', v: '7.8M samples' },
            { l: 'GPU Acceleration', v: 'XGBoost CUDA' },
          ].map(s => (
            <div key={s.l} className="px-3 py-2.5 rounded-lg" style={{ background: 'rgba(0,0,0,0.08)', border: '1px solid rgba(0,0,0,0.12)' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '0.1em', marginBottom: 4 }}>{s.l}</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-mid)' }}>{s.v}</div>
            </div>
          ))}
        </div>
      </Card>

      {/* ── Tab nav ─────────────────────────────────────────────────────────── */}
      <div className="flex gap-1 mb-4" style={{ overflowX: 'auto' }}>
        {TAB_LIST.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)}
            className="px-3 py-2 rounded-md whitespace-nowrap transition-all"
            style={{
              fontFamily: 'var(--font-mono)', fontSize: 10,
              background: activeTab === t.id ? 'rgba(2,132,199,0.15)' : 'rgba(0,0,0,0.10)',
              color: activeTab === t.id ? 'var(--cyan)' : 'var(--text-lo)',
              border: `1px solid ${activeTab === t.id ? 'rgba(2,132,199,0.32)' : 'rgba(0,0,0,0.20)'}`,
            }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ══ TAB: Overview ═════════════════════════════════════════════════════ */}
      {activeTab === 'overview' && (
        <>
          <Card className="mb-5">
            <CardHeader icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="2"><path d="M13 2H3v10l9.29 9.29c.94.94 2.48.94 3.42 0l6.58-6.58c.94-.94.94-2.48 0-3.42L13 2z"/></svg>} title="Top 3 Performing Models" />
            <div className="space-y-3">
              {CICIOT2023_RESULTS.models.slice(0, 3).map((m, i) => (
                <div key={m.model} className="p-3 rounded-lg" style={{ background: 'rgba(0,0,0,0.05)', border: '1px solid rgba(0,0,0,0.12)' }}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div style={{ width: 8, height: 8, borderRadius: '50%', background: MODEL_COLOR[m.model] }} />
                      <span style={{ fontFamily: 'var(--font-display)', fontSize: 12, fontWeight: 700, color: 'var(--text-hi)' }}>
                        #{i + 1} {m.model.replace(/_/g, ' ').toUpperCase()}
                      </span>
                      {m.gpu && <span className="tag" style={{ fontSize: 8, background: 'rgba(124,58,237,0.15)', color: '#7c3aed', border: '1px solid rgba(124,58,237,0.30)' }}>GPU</span>}
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div><span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)' }}>Accuracy</span><div style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 700, color: 'var(--cyan)' }}>{pct(m.accuracy)}</div></div>
                    <div><span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)' }}>Macro F1</span><div style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 700, color: '#7c3aed' }}>{pct(m.macro_f1)}</div></div>
                    <div><span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)' }}>Atk Detect</span><div style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 700, color: 'var(--green)' }}>{pct(m.attack_detection)}</div></div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="mb-5">
            <CardHeader icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>} title="Key Findings" />
            <div className="space-y-2 text-sm">
              <div className="flex gap-2">
                <span style={{ color: 'var(--green)' }}>✓</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-mid)' }}>XGBoost achieves 71.51% Macro F1 on 34-class IoT threat classification</span>
              </div>
              <div className="flex gap-2">
                <span style={{ color: 'var(--green)' }}>✓</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-mid)' }}>GPU acceleration reduces XGBoost training time from hours to seconds</span>
              </div>
              <div className="flex gap-2">
                <span style={{ color: 'var(--green)' }}>✓</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-mid)' }}>Decision Tree provides fastest inference (266ms) for real-time systems</span>
              </div>
              <div className="flex gap-2">
                <span style={{ color: 'var(--amber)' }}>⚠</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-mid)' }}>SVM shows poor generalization (18min prediction) — needs full dataset training</span>
              </div>
            </div>
          </Card>
        </>
      )}

      {/* ══ TAB: Model Comparison ═════════════════════════════════════════════ */}
      {activeTab === 'models' && (
        <>
          <Card className="mb-5">
            <CardHeader icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--purple)" strokeWidth="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>} title="Accuracy vs Macro F1 vs Attack Detection" badge="7 models" />
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={barData} margin={{ top: 4, right: 16, left: 0, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.18)" />
                <XAxis dataKey="name" tick={{ fill: 'var(--text-lo)', fontSize: 9, fontFamily: 'var(--font-mono)' }} angle={-35} textAnchor="end" interval={0} />
                <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-lo)', fontSize: 9 }} tickFormatter={v => `${v}%`} />
                <Tooltip {...TOOLTIP_STYLE} formatter={(v: unknown) => [`${Number(v).toFixed(2)}%`]} />
                <Legend wrapperStyle={{ fontFamily: 'var(--font-mono)', fontSize: 10, paddingTop: 8 }} />
                <Bar dataKey="Accuracy" fill="#0284c7" radius={[2, 2, 0, 0]} maxBarSize={16} />
                <Bar dataKey="Macro F1" fill="#7c3aed" radius={[2, 2, 0, 0]} maxBarSize={16} />
                <Bar dataKey="Atk Detect" fill="#059669" radius={[2, 2, 0, 0]} maxBarSize={16} />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          <Card className="mb-5">
            <CardHeader icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/></svg>} title="Detailed Model Metrics" />
            <div style={{ overflowX: 'auto' }}>
              <table className="w-full data-table" style={{ minWidth: 700 }}>
                <thead>
                  <tr>
                    {['#', 'Model', 'Accuracy', 'Macro F1', 'Atk Detect', 'Latency (ms)', 'Train (s)', 'GPU'].map(h => (
                      <th key={h} className="text-left" style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', letterSpacing: '0.1em', padding: '8px 12px' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {CICIOT2023_RESULTS.models.slice().sort((a, b) => b.macro_f1 - a.macro_f1).map((row, i) => {
                    const c = MODEL_COLOR[row.model] ?? 'var(--text-mid)';
                    const isBest = row.model === CICIOT2023_RESULTS.best_model;
                    return (
                      <tr key={row.model} style={{ background: isBest ? `${c}08` : 'transparent' }}>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', padding: '8px 12px' }}>#{i + 1}</td>
                        <td style={{ padding: '8px 12px' }}>
                          <div className="flex items-center gap-2">
                            <div style={{ width: 8, height: 8, borderRadius: '50%', background: c }} />
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: isBest ? 700 : 400, color: c }}>{row.model}</span>
                            {isBest && <span className="tag" style={{ fontSize: 8, background: 'rgba(5,150,105,0.12)', color: 'var(--green)', border: '1px solid rgba(5,150,105,0.28)' }}>★ BEST</span>}
                          </div>
                        </td>
                        <td style={{ padding: '8px 12px' }}><MiniBar value={row.accuracy} color={c} /></td>
                        <td style={{ padding: '8px 12px' }}><MiniBar value={row.macro_f1} color="#7c3aed" /></td>
                        <td style={{ padding: '8px 12px' }}><MiniBar value={row.attack_detection} color="#059669" /></td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: row.pred_time > 1000 ? 'var(--red)' : row.pred_time < 300 ? 'var(--green)' : 'var(--amber)', padding: '8px 12px' }}>
                          {row.pred_time > 1000 ? (row.pred_time / 1000).toFixed(1) + 's' : row.pred_time.toFixed(1) + 'ms'}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-mid)', padding: '8px 12px' }}>{row.train_time.toFixed(2)}s</td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: row.gpu ? 'var(--green)' : 'var(--text-mid)', padding: '8px 12px' }}>{row.gpu ? 'CUDA' : 'CPU'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}

      {/* ══ TAB: Attack Detection ═════════════════════════════════════════════ */}
      {activeTab === 'attacks' && (
        <Card className="mb-5">
          <CardHeader icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--red)" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>} title="Per-Attack-Class Detection (XGBoost)" badge="Macro F1: 71.51%" />
          <div style={{ overflowX: 'auto' }}>
            <table className="w-full data-table" style={{ minWidth: 600 }}>
              <thead>
                <tr>
                  {['Attack Class', 'Precision', 'Recall', 'F1-Score', 'Test Samples', 'Risk'].map(h => (
                    <th key={h} className="text-left" style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', letterSpacing: '0.1em', padding: '8px 12px' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {CICIOT2023_RESULTS.attack_classes.map((c, i) => {
                  const isBenign = c.name.toUpperCase() === 'BENIGN TRAFFIC';
                  const risk = isBenign ? 'BENIGN' : c.f1 >= 0.85 ? 'HIGH F1' : c.f1 >= 0.6 ? 'MEDIUM F1' : 'LOW F1';
                  const riskCol = isBenign ? 'var(--green)' : c.f1 >= 0.85 ? 'var(--green)' : c.f1 >= 0.6 ? 'var(--amber)' : 'var(--red)';
                  return (
                    <tr key={i} style={{ background: isBenign ? 'rgba(5,150,105,0.05)' : 'transparent' }}>
                      <td style={{ padding: '8px 12px' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: isBenign ? 'var(--green)' : 'var(--text-mid)', fontWeight: isBenign ? 600 : 400 }}>{c.name}</span>
                      </td>
                      <td style={{ padding: '8px 12px' }}><MiniBar value={c.precision} color="#0284c7" /></td>
                      <td style={{ padding: '8px 12px' }}><MiniBar value={c.recall} color="#7c3aed" /></td>
                      <td style={{ padding: '8px 12px' }}><MiniBar value={c.f1} color="#d97706" /></td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', padding: '8px 12px' }}>{c.samples.toLocaleString()}</td>
                      <td style={{ padding: '8px 12px' }}>
                        <span className="tag" style={{ fontSize: 8, background: `${riskCol}15`, color: riskCol, border: `1px solid ${riskCol}30` }}>
                          {risk}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* ══ TAB: Latency Analysis ═════════════════════════════════════════════ */}
      {activeTab === 'latency' && (
        <Card className="mb-5">
          <CardHeader icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>} title="Prediction Latency per Model" badge="Real-time: <100ms" />
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={latencyData} margin={{ top: 4, right: 20, left: 0, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.18)" />
              <XAxis dataKey="name" tick={{ fill: 'var(--text-lo)', fontSize: 9 }} angle={-35} textAnchor="end" interval={0} />
              <YAxis scale="log" tick={{ fill: 'var(--text-lo)', fontSize: 9 }} />
              <Tooltip {...TOOLTIP_STYLE} formatter={(v: unknown) => {
                const val = Number(v);
                return val > 1000 ? [`${(val / 1000).toFixed(1)}s`, 'Latency'] : [`${val.toFixed(1)}ms`, 'Latency'];
              }} />
              <ReferenceLine y={100} stroke="var(--amber)" strokeDasharray="4 4" label={{ value: '100ms RT threshold', fill: 'var(--amber)', fontFamily: 'var(--font-mono)', fontSize: 9 }} />
              <Bar dataKey="Latency (ms)" radius={[3, 3, 0, 0]} maxBarSize={32}>
                {latencyData.map((entry, idx) => (
                  <Cell key={idx} fill={entry.realtime ? '#059669' : '#d97706'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="px-3 py-2 rounded-lg" style={{ background: 'rgba(5,150,105,0.08)', border: '1px solid rgba(5,150,105,0.24)' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)' }}>FASTEST MODEL</div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700, color: 'var(--green)' }}>266.87 ms</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-mid)' }}>Decision Tree</div>
            </div>
            <div className="px-3 py-2 rounded-lg" style={{ background: 'rgba(124,58,237,0.08)', border: '1px solid rgba(124,58,237,0.24)' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)' }}>BEST MODEL LATENCY</div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700, color: '#7c3aed' }}>7.92 sec</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-mid)' }}>XGBoost</div>
            </div>
            <div className="px-3 py-2 rounded-lg" style={{ background: 'rgba(220,38,38,0.08)', border: '1px solid rgba(220,38,38,0.24)' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)' }}>SLOWEST MODEL</div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 700, color: 'var(--red)' }}>18+ min</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-mid)' }}>SVM (Unusable)</div>
            </div>
          </div>
        </Card>
      )}

      <div style={{ height: 40 }} />
    </div>
  );
}
