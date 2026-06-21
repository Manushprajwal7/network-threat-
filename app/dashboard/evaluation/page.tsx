'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  LineChart, Line, ReferenceLine, Cell,
} from 'recharts';
import {
  getEvalSummary, getPerClassMetrics, getConfusionMatrixImage,
  getLatencyBreakdown, getTrustTrend, getExperimentLog, getExportCsvUrl,
  type EvalSummary, type PerClassEntry, type LatencyEntry,
  type TrustSample, type ExperimentEntry, type PerClassMetrics,
} from '../../../lib/api';

// ── Colour palette ─────────────────────────────────────────────────────────────
const MODEL_COLOR: Record<string, string> = {
  random_forest: '#00d4ff', decision_tree: '#00ff9d',
  logistic_regression: '#bf5fff', svm: '#ffb020',
  knn: '#ff8c42', gradient_boosting: '#ff2d55', naive_bayes: '#a78bfa',
};
const RISK_COLOR: Record<string, string> = {
  High: '#00ff9d', Medium: '#ffb020', Low: '#ff2d55',
};

function pct(v: number) { return `${(v * 100).toFixed(2)}%`; }
function ms(v: number)  { return `${(v * 1000).toFixed(1)} ms`; }

// ── Small reusable pieces ─────────────────────────────────────────────────────

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)',
      letterSpacing: '0.14em', marginBottom: 6 }}>
      {children}
    </div>
  );
}

function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl p-4 bracket-all ${className}`}
      style={{ background: 'rgba(3,10,22,0.90)', border: '1px solid var(--border-dim)',
        backdropFilter: 'blur(16px)' }}>
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
          style={{ background: 'rgba(0,212,255,0.08)', color: 'var(--cyan)',
            border: '1px solid rgba(0,212,255,0.2)', fontSize: 9 }}>
          {badge}
        </span>
      )}
    </div>
  );
}

function KPI({ label, value, color = 'var(--cyan)', sub }: {
  label: string; value: string; color?: string; sub?: string;
}) {
  return (
    <div className="rounded-xl p-4 bracket-all"
      style={{ background: 'rgba(3,10,22,0.90)', border: '1px solid var(--border-dim)' }}>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)',
        letterSpacing: '0.12em', marginBottom: 4 }}>{label}</div>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 800,
        color, lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)',
        marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function MiniBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div style={{ flex: 1, height: 4, background: 'rgba(255,255,255,0.05)', borderRadius: 2 }}>
        <div style={{ width: `${Math.min(value * 100, 100)}%`, height: '100%',
          background: color, borderRadius: 2, transition: 'width 0.7s' }} />
      </div>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color,
        minWidth: 44, textAlign: 'right' }}>{pct(value)}</span>
    </div>
  );
}

const TOOLTIP_STYLE = {
  contentStyle: { background: '#000c1a', border: '1px solid rgba(0,212,255,0.2)',
    borderRadius: 8, fontFamily: 'var(--font-mono)', fontSize: 11 },
  labelStyle: { color: 'var(--cyan)', fontWeight: 600 },
  itemStyle: { color: 'var(--text-mid)' },
};

// recharts v3 formatter: ValueType | undefined -> string tuple
type RechartsFormatter = (v: unknown) => [string] | [string, string];
const fmtPct: RechartsFormatter = (v) => [`${Number(v ?? 0).toFixed(2)}%`];
const fmtMs:  RechartsFormatter = (v) => [`${Number(v ?? 0).toFixed(3)} ms`, 'Latency'];

// ── Print / export helpers ─────────────────────────────────────────────────────

function downloadClientCSV(rows: ExperimentEntry[]) {
  const headers = ['run_id','model','accuracy','precision','recall','f1_score',
    'train_time_s','pred_time_ms','split','status','trained_at'];
  const lines = [
    headers.join(','),
    ...rows.map(r => headers.map(h => String((r as unknown as Record<string,unknown>)[h] ?? '')).join(',')),
  ];
  const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'experiment_log_cicids2017.csv';
  a.click();
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function EvaluationPage() {
  const [summary, setSummary]         = useState<EvalSummary | null>(null);
  const [perClass, setPerClass]       = useState<PerClassEntry[]>([]);
  const [perClassMeta, setPerClassMeta] = useState<Pick<PerClassMetrics, 'macro_f1' | 'attack_detection_rate' | 'total_support'> | null>(null);
  const [latency, setLatency]         = useState<LatencyEntry[]>([]);
  const [trustTrend, setTrustTrend]   = useState<TrustSample[]>([]);
  const [expLog, setExpLog]           = useState<ExperimentEntry[]>([]);
  const [cmImage, setCmImage]         = useState<string | null>(null);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState<string | null>(null);
  const [activeTab, setActiveTab]     = useState<'metrics'|'perclass'|'latency'|'trust'|'log'>('metrics');
  const printRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    try {
      const [s, pc, lat, tt, el, cm] = await Promise.allSettled([
        getEvalSummary(),
        getPerClassMetrics(),
        getLatencyBreakdown(),
        getTrustTrend(),
        getExperimentLog(),
        getConfusionMatrixImage(),
      ]);
      if (s.status === 'fulfilled')  setSummary(s.value);
      if (pc.status === 'fulfilled') {
        setPerClass(pc.value.classes);
        setPerClassMeta({ macro_f1: pc.value.macro_f1, attack_detection_rate: pc.value.attack_detection_rate, total_support: pc.value.total_support });
      }
      if (lat.status === 'fulfilled') setLatency(lat.value.latency);
      if (tt.status === 'fulfilled') setTrustTrend(tt.value.samples);
      if (el.status === 'fulfilled') setExpLog(el.value.entries);
      if (cm.status === 'fulfilled' && cm.value.available && cm.value.image_base64) {
        setCmImage(cm.value.image_base64);
      }
      if (s.status === 'rejected') setError((s.reason as Error).message);
      else setError(null);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // ── Chart data prep ────────────────────────────────────────────────────────
  const barData = (summary?.models ?? []).map(m => ({
    name: m.model.replace(/_/g, ' '),
    Accuracy:    +(m.accuracy  * 100).toFixed(2),
    'W-F1':      +(m.f1_score * 100).toFixed(2),
    'Macro-F1':  +((m.macro_f1 ?? 0) * 100).toFixed(2),
    'Atk Detect': +((m.attack_detection_rate ?? 0) * 100).toFixed(2),
    color: MODEL_COLOR[m.model] ?? '#888',
  })).sort((a, b) => b['Macro-F1'] - a['Macro-F1']);

  // radarData kept for potential future use; primary vis is horizontal bar chart
  const radarData = perClass.slice(0, 8).map(c => ({
    subject: c.class.length > 14 ? c.class.slice(0, 13) + '…' : c.class,
    F1:        +(c.f1        * 100).toFixed(1),
    Recall:    +(c.recall    * 100).toFixed(1),
    Precision: +(c.precision * 100).toFixed(1),
  }));
  void radarData; // kept for type-check; replaced by horizontal bar chart

  const latencyData = latency.map(l => ({
    name:  l.model.replace(/_/g, ' '),
    'Latency (ms)': l.pred_time_ms,
    realtime: l.realtime_ok,
  })).sort((a, b) => a['Latency (ms)'] - b['Latency (ms)']);

  const trustData = trustTrend.map((s, i) => ({
    t:     i,
    Score: s.score,
    label: s.ts.slice(11, 16),
  }));

  const TAB_LIST: { id: typeof activeTab; label: string }[] = [
    { id: 'metrics',  label: 'Model Comparison' },
    { id: 'perclass', label: 'Per-Class Detection' },
    { id: 'latency',  label: 'Latency Analysis' },
    { id: 'trust',    label: 'Trust Variation' },
    { id: 'log',      label: 'Experiment Logs' },
  ];

  const exp = summary?.experiment;

  return (
    <div ref={printRef}>
      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-start justify-between gap-4 mb-6 print-header">
        <div>
          <SectionLabel>// RESEARCH EVALUATION MODULE</SectionLabel>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 800,
            color: 'var(--text-hi)', letterSpacing: '0.03em', lineHeight: 1 }}>
            Model Evaluation &amp; Report
          </h1>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', marginTop: 4 }}>
            {exp?.dataset ?? 'CICIDS2017'} · {exp?.split_strategy ?? 'Temporal Split'} · {exp?.num_features ?? '—'} features · {exp?.num_classes ?? '—'} classes
          </p>
        </div>

        <div className="flex items-center gap-2 no-print">
          {/* CSV Export */}
          <a href={getExportCsvUrl()} download
            className="flex items-center gap-1.5 px-3 py-2 rounded-md transition-all"
            style={{ background: 'rgba(0,255,157,0.07)', border: '1px solid rgba(0,255,157,0.25)',
              color: 'var(--green)', fontFamily: 'var(--font-mono)', fontSize: 10, textDecoration: 'none' }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Export CSV
          </a>
          {/* Client CSV (experiment log) */}
          <button onClick={() => expLog.length && downloadClientCSV(expLog)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-md transition-all"
            style={{ background: 'rgba(191,95,255,0.07)', border: '1px solid rgba(191,95,255,0.25)',
              color: 'var(--purple)', fontFamily: 'var(--font-mono)', fontSize: 10 }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
            </svg>
            Exp Log CSV
          </button>
          {/* JSON export */}
          <button
            onClick={() => {
              const blob = new Blob([JSON.stringify({
                generated_at: new Date().toISOString(),
                paper: summary?.experiment?.reference_paper ?? '',
                dataset: 'CICIDS2017',
                model_results: summary?.models ?? [],
                per_class_metrics: perClass,
                latency,
                trust_trend: trustTrend,
                experiment_log: expLog,
              }, null, 2)], { type: 'application/json' });
              const a = document.createElement('a');
              a.href = URL.createObjectURL(blob);
              a.download = 'netshield_evaluation_cicids2017.json';
              a.click();
            }}
            className="flex items-center gap-1.5 px-3 py-2 rounded-md transition-all"
            style={{ background: 'rgba(191,95,255,0.07)', border: '1px solid rgba(191,95,255,0.25)',
              color: 'var(--purple)', fontFamily: 'var(--font-mono)', fontSize: 10 }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
            </svg>
            JSON
          </button>
          {/* PDF */}
          <button onClick={() => window.print()}
            className="flex items-center gap-1.5 px-3 py-2 rounded-md transition-all"
            style={{ background: 'rgba(255,176,32,0.07)', border: '1px solid rgba(255,176,32,0.25)',
              color: 'var(--amber)', fontFamily: 'var(--font-mono)', fontSize: 10 }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/>
            </svg>
            Print / PDF
          </button>
        </div>
      </div>

      {/* ── Backend offline warning ──────────────────────────────────────────── */}
      {error && (
        <div className="rounded-xl p-3 mb-5"
          style={{ background: 'rgba(255,45,85,0.05)', border: '1px solid rgba(255,45,85,0.2)' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--red)' }}>
            Backend offline or models not trained — {error}. Start Flask: <code>python backend/api/app.py</code>
          </span>
        </div>
      )}

      {/* ── KPI row ─────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <KPI label="BEST MODEL"
          value={summary?.best_model?.replace(/_/g,' ').toUpperCase() ?? (loading ? '…' : '—')}
          color="var(--cyan)" sub="ranked by Macro-F1" />
        <KPI label="ATTACK DETECTION RATE"
          value={summary?.best_attack_detect != null
            ? pct(summary.best_attack_detect)
            : perClassMeta?.attack_detection_rate != null
            ? pct(perClassMeta.attack_detection_rate)
            : (loading ? '…' : '—')}
          color="var(--green)" sub="macro recall · non-BENIGN classes" />
        <KPI label="MACRO F1-SCORE"
          value={summary?.best_macro_f1 != null ? pct(summary.best_macro_f1) : (loading ? '…' : '—')}
          color="var(--purple)" sub="honest per-class metric" />
        <KPI label="WEIGHTED F1"
          value={summary?.best_f1 != null ? pct(summary.best_f1) : (loading ? '…' : '—')}
          color="var(--amber)" sub="inflated when BENIGN dominates" />
      </div>

      {/* ── Experiment metadata ─────────────────────────────────────────────── */}
      {exp && (
        <Card className="mb-5">
          <CardHeader
            icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>}
            title="Experiment Configuration"
            badge="CICIDS2017"
          />
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {[
              { l: 'Dataset',           v: exp.dataset },
              { l: 'Split Strategy',    v: exp.split_strategy },
              { l: 'Deduplication',     v: exp.deduplication },
              { l: 'Outlier Clipping',  v: exp.outlier_clipping },
              { l: 'Features',          v: String(exp.num_features) },
              { l: 'Classes',           v: String(exp.num_classes) },
              { l: 'Framework',         v: exp.framework },
              { l: 'Eval Metric',       v: exp.evaluation_metric },
            ].map(s => (
              <div key={s.l} className="px-3 py-2.5 rounded-lg"
                style={{ background: 'rgba(255,255,255,0.018)', border: '1px solid rgba(255,255,255,0.04)' }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)',
                  letterSpacing: '0.1em', marginBottom: 4 }}>{s.l}</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-mid)' }}>{s.v}</div>
              </div>
            ))}
          </div>
          <div className="mt-3 px-3 py-2 rounded"
            style={{ background: 'rgba(0,212,255,0.03)', border: '1px solid rgba(0,212,255,0.08)' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
              Attack classes: {exp.attack_classes.join(' · ')}
            </span>
          </div>
        </Card>
      )}

      {/* ── Tab nav ─────────────────────────────────────────────────────────── */}
      <div className="flex gap-1 mb-4 no-print" style={{ overflowX: 'auto' }}>
        {TAB_LIST.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)}
            className="px-3 py-2 rounded-md whitespace-nowrap transition-all"
            style={{
              fontFamily: 'var(--font-mono)', fontSize: 10,
              background: activeTab === t.id ? 'rgba(0,212,255,0.12)' : 'rgba(255,255,255,0.03)',
              color: activeTab === t.id ? 'var(--cyan)' : 'var(--text-lo)',
              border: `1px solid ${activeTab === t.id ? 'rgba(0,212,255,0.3)' : 'rgba(255,255,255,0.06)'}`,
            }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ══ TAB: Model Comparison ══════════════════════════════════════════════ */}
      {activeTab === 'metrics' && (
        <>
          {/* Grouped bar chart */}
          <Card className="mb-5">
            <CardHeader
              icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--purple)" strokeWidth="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>}
              title="Accuracy / Precision / Recall / F1 — All Models"
              badge={`${barData.length} models`}
            />
            {barData.length === 0 ? (
              <div className="py-12 text-center">
                <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)' }}>
                  {loading ? 'Loading…' : 'No data — run python ml_model/train_models.py'}
                </p>
              </div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={barData} margin={{ top: 4, right: 16, left: 0, bottom: 60 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" tick={{ fill: 'var(--text-lo)', fontSize: 9, fontFamily: 'var(--font-mono)' }} angle={-35} textAnchor="end" interval={0} />
                    <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-lo)', fontSize: 9 }} tickFormatter={v => `${v}%`} />
                    <Tooltip {...TOOLTIP_STYLE} formatter={fmtPct} />
                    <Legend wrapperStyle={{ fontFamily: 'var(--font-mono)', fontSize: 10, paddingTop: 8 }} />
                    <Bar dataKey="Accuracy"    fill="#00d4ff" radius={[2,2,0,0]} maxBarSize={16} />
                    <Bar dataKey="W-F1"        fill="#ffb020" radius={[2,2,0,0]} maxBarSize={16} />
                    <Bar dataKey="Macro-F1"    fill="#bf5fff" radius={[2,2,0,0]} maxBarSize={16} />
                    <Bar dataKey="Atk Detect"  fill="#00ff9d" radius={[2,2,0,0]} maxBarSize={16} />
                  </BarChart>
                </ResponsiveContainer>
                <div className="mt-2 px-3 py-2 rounded"
                  style={{ background: 'rgba(191,95,255,0.03)', border: '1px solid rgba(191,95,255,0.08)' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
                    ★ Macro-F1 = honest per-class metric (sorted) &nbsp;·&nbsp; Atk Detect = macro recall over non-BENIGN attack classes &nbsp;·&nbsp; W-F1 inflated when BENIGN dominates test set
                  </span>
                </div>
              </>
            )}
          </Card>

          {/* Detailed metrics table */}
          <Card className="mb-5">
            <CardHeader
              icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/></svg>}
              title="Detailed Metrics Table"
            />
            <div style={{ overflowX: 'auto' }}>
              <table className="w-full data-table" style={{ minWidth: 680 }}>
                <thead>
                  <tr>
                    {['#','Model','Accuracy','W-F1','Macro-F1 ★','Atk Detect ★','Train (s)','Pred (ms)'].map(h => (
                      <th key={h} className="text-left" style={{ fontFamily: 'var(--font-mono)', fontSize: 9,
                        color: h.includes('★') ? 'var(--green)' : 'var(--text-lo)',
                        letterSpacing: '0.1em', padding: '8px 12px' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(summary?.models ?? [])
                    .slice().sort((a,b) => (b.macro_f1 ?? 0) - (a.macro_f1 ?? 0))
                    .map((row, i) => {
                      const c = MODEL_COLOR[row.model] ?? 'var(--text-mid)';
                      const isPrimary = row.model === summary?.experiment?.primary_model;
                      const isBest    = row.model === summary?.best_model;
                      return (
                        <tr key={row.model} style={{ background: isPrimary ? `${c}08` : 'transparent' }}>
                          <td style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', padding: '8px 12px' }}>#{i+1}</td>
                          <td style={{ padding: '8px 12px' }}>
                            <div className="flex items-center gap-2">
                              <div style={{ width: 8, height: 8, borderRadius: '50%', background: c, boxShadow: `0 0 5px ${c}` }} />
                              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: isPrimary ? 700 : 400, color: c }}>
                                {row.model}
                              </span>
                              {isBest && <span className="tag" style={{ fontSize: 8, background: 'rgba(0,255,157,0.1)', color: 'var(--green)', border: '1px solid rgba(0,255,157,0.25)' }}>★ BEST</span>}
                              {isPrimary && !isBest && <span className="tag" style={{ fontSize: 8, background: `${c}15`, color: c, border: `1px solid ${c}30` }}>PRIMARY</span>}
                            </div>
                          </td>
                          <td style={{ padding: '8px 12px' }}><MiniBar value={row.accuracy}  color={c} /></td>
                          <td style={{ padding: '8px 12px' }}><MiniBar value={row.f1_score}  color="#ffb020" /></td>
                          <td style={{ padding: '8px 12px' }}><MiniBar value={row.macro_f1 ?? 0} color="#bf5fff" /></td>
                          <td style={{ padding: '8px 12px' }}><MiniBar value={row.attack_detection_rate ?? 0} color="#00ff9d" /></td>
                          <td style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-mid)', padding: '8px 12px' }}>
                            {row.train_time_s.toFixed(1)}s
                          </td>
                          <td style={{ fontFamily: 'var(--font-mono)', fontSize: 10, padding: '8px 12px',
                            color: row.pred_time_s * 1000 < 100 ? 'var(--green)' : 'var(--amber)' }}>
                            {(row.pred_time_s * 1000).toFixed(1)} ms
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
            <div className="px-2 pt-2" style={{ borderTop: '1px solid var(--border-dim)' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
                Evaluated on CICIDS2017 Friday test set · Temporal split · Metrics: weighted average
              </span>
            </div>
          </Card>

          {/* Confusion matrix */}
          <Card className="mb-5">
            <CardHeader
              icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>}
              title="Confusion Matrix — Random Forest"
              badge="primary model"
            />
            {cmImage ? (
              <div className="flex justify-center">
                <img src={`data:image/png;base64,${cmImage}`} alt="Confusion Matrix"
                  style={{ maxWidth: '100%', borderRadius: 8, border: '1px solid var(--border-dim)' }} />
              </div>
            ) : (
              <div className="py-10 text-center">
                <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)' }}>
                  {loading ? 'Loading confusion matrix…' : 'confusion_matrix.png not found — run python ml_model/verify_models.py'}
                </p>
              </div>
            )}
          </Card>
        </>
      )}

      {/* ══ TAB: Per-Class Detection ══════════════════════════════════════════ */}
      {activeTab === 'perclass' && (
        <>
          {/* Horizontal bar chart — all attack classes */}
          {perClass.filter(c => c.class.toUpperCase() !== 'BENIGN').length > 0 && (
            <Card className="mb-5">
              <CardHeader
                icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--red)" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>}
                title="Attack-Wise Detection — Precision / Recall / F1 per Class"
                badge="Random Forest"
              />
              {perClassMeta && (
                <div className="flex gap-5 mb-3 flex-wrap">
                  {[
                    { l: 'Macro F1', v: pct(perClassMeta.macro_f1), c: 'var(--purple)' },
                    { l: 'Atk Detect Rate', v: pct(perClassMeta.attack_detection_rate), c: 'var(--green)' },
                    { l: 'Total Support', v: (perClassMeta.total_support ?? 0).toLocaleString(), c: 'var(--text-mid)' },
                  ].map(({ l, v, c }) => (
                    <div key={l}>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '0.1em' }}>{l}</div>
                      <div style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 700, color: c }}>{v}</div>
                    </div>
                  ))}
                </div>
              )}
              <ResponsiveContainer width="100%" height={Math.max(260, perClass.filter(c => c.class.toUpperCase() !== 'BENIGN').length * 36)}>
                <BarChart
                  data={perClass.filter(c => c.class.toUpperCase() !== 'BENIGN').map(c => ({
                    name: c.class.length > 22 ? c.class.slice(0, 20) + '…' : c.class,
                    Precision: +(c.precision * 100).toFixed(1),
                    Recall:    +(c.recall    * 100).toFixed(1),
                    'F1-Score': +(c.f1       * 100).toFixed(1),
                  }))}
                  layout="vertical"
                  margin={{ top: 4, right: 20, left: 120, bottom: 4 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} tick={{ fill: 'var(--text-lo)', fontSize: 9 }} tickFormatter={v => `${v}%`} />
                  <YAxis type="category" dataKey="name" width={115} tick={{ fill: 'var(--text-mid)', fontSize: 9, fontFamily: 'var(--font-mono)' }} />
                  <Tooltip {...TOOLTIP_STYLE} formatter={fmtPct} />
                  <Legend wrapperStyle={{ fontFamily: 'var(--font-mono)', fontSize: 10 }} />
                  <Bar dataKey="Precision" fill="#00d4ff" radius={[0,2,2,0]} maxBarSize={10} />
                  <Bar dataKey="Recall"    fill="#bf5fff" radius={[0,2,2,0]} maxBarSize={10} />
                  <Bar dataKey="F1-Score"  fill="#00ff9d" radius={[0,2,2,0]} maxBarSize={10} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}

          {/* Per-class table */}
          <Card className="mb-5">
            <CardHeader
              icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>}
              title="Per-Attack-Class Detection Performance"
              badge="Random Forest"
            />
            {perClass.length === 0 ? (
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', textAlign: 'center', padding: '32px 0' }}>
                {loading ? 'Loading…' : 'No data — run python ml_model/verify_models.py'}
              </p>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table className="w-full data-table" style={{ minWidth: 600 }}>
                  <thead>
                    <tr>
                      {['Attack Class','Precision','Recall','F1-Score','Support','Risk'].map(h => (
                        <th key={h} className="text-left" style={{ fontFamily: 'var(--font-mono)', fontSize: 9,
                          color: 'var(--text-lo)', letterSpacing: '0.1em', padding: '8px 12px' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {perClass.map((c, i) => {
                      const isBenign = c.class.toUpperCase() === 'BENIGN';
                      const risk = isBenign ? 'Low' : c.f1 >= 0.85 ? 'High' : c.f1 >= 0.6 ? 'Medium' : 'Low';
                      const riskCol = isBenign ? 'var(--green)' : c.f1 >= 0.85 ? 'var(--green)' : c.f1 >= 0.6 ? 'var(--amber)' : 'var(--red)';
                      return (
                        <tr key={i} style={{ background: isBenign ? 'rgba(0,255,157,0.03)' : 'transparent' }}>
                          <td style={{ padding: '8px 12px' }}>
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10,
                              color: isBenign ? 'var(--green)' : 'var(--text-mid)', fontWeight: isBenign ? 600 : 400 }}>
                              {c.class}
                            </span>
                          </td>
                          <td style={{ padding: '8px 12px' }}><MiniBar value={c.precision} color="#00d4ff" /></td>
                          <td style={{ padding: '8px 12px' }}><MiniBar value={c.recall}    color="#bf5fff" /></td>
                          <td style={{ padding: '8px 12px' }}><MiniBar value={c.f1}        color="#ffb020" /></td>
                          <td style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', padding: '8px 12px' }}>
                            {c.support.toLocaleString()}
                          </td>
                          <td style={{ padding: '8px 12px' }}>
                            <span className="tag" style={{ fontSize: 8, background: `${riskCol}15`,
                              color: riskCol, border: `1px solid ${riskCol}30` }}>
                              {isBenign ? 'BENIGN' : risk.toUpperCase() + ' F1'}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}

      {/* ══ TAB: Latency ══════════════════════════════════════════════════════ */}
      {activeTab === 'latency' && (
        <Card className="mb-5">
          <CardHeader
            icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>}
            title="Prediction Latency per Model"
            badge="real-time threshold: 100ms"
          />
          {latencyData.length === 0 ? (
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', textAlign: 'center', padding: '32px 0' }}>
              {loading ? 'Loading…' : 'No data'}
            </p>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={latencyData} margin={{ top: 4, right: 20, left: 0, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" tick={{ fill: 'var(--text-lo)', fontSize: 9 }} angle={-35} textAnchor="end" interval={0} />
                  <YAxis tick={{ fill: 'var(--text-lo)', fontSize: 9 }} tickFormatter={v => `${v}ms`} />
                  <Tooltip {...TOOLTIP_STYLE} formatter={fmtMs} />
                  <ReferenceLine y={100} stroke="var(--amber)" strokeDasharray="4 4"
                    label={{ value: '100ms RT threshold', fill: 'var(--amber)', fontFamily: 'var(--font-mono)', fontSize: 9, position: 'insideTopRight' }} />
                  <Bar dataKey="Latency (ms)" radius={[3,3,0,0]} maxBarSize={32}>
                    {latencyData.map((entry, idx) => (
                      <Cell key={idx} fill={entry['Latency (ms)'] < 100 ? '#00ff9d' : '#ffb020'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2">
                {latencyData.map(l => (
                  <div key={l.name} className="px-3 py-2 rounded-lg"
                    style={{ background: 'rgba(255,255,255,0.018)', border: '1px solid rgba(255,255,255,0.04)' }}>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)',
                      letterSpacing: '0.08em', marginBottom: 2 }}>{l.name}</div>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 700,
                      color: l['Latency (ms)'] < 100 ? 'var(--green)' : 'var(--amber)' }}>
                      {l['Latency (ms)'].toFixed(2)} ms
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, marginTop: 1,
                      color: l['Latency (ms)'] < 100 ? 'var(--green)' : 'var(--amber)' }}>
                      {l['Latency (ms)'] < 100 ? '✓ Real-time OK' : '⚠ Above threshold'}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </Card>
      )}

      {/* ══ TAB: Trust Variation ══════════════════════════════════════════════ */}
      {activeTab === 'trust' && (
        <Card className="mb-5">
          <CardHeader
            icon={<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>}
            title="Trust Score Variation Over Time"
            badge={trustTrend.length > 0 ? (trustData[0]?.Score != null ? 'live' : 'demo') : 'demo'}
          />
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', marginBottom: 12 }}>
            Formula: Trust = 0.3 × User Trust + 0.3 × Device Trust + 0.4 × Behaviour Trust
          </p>
          {trustData.length === 0 ? (
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', textAlign: 'center', padding: '32px 0' }}>
              {loading ? 'Loading…' : 'No data'}
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trustData} margin={{ top: 4, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="label" tick={{ fill: 'var(--text-lo)', fontSize: 8 }} interval={Math.floor(trustData.length / 8)} />
                <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-lo)', fontSize: 9 }} tickFormatter={v => `${v}`} />
                <Tooltip {...TOOLTIP_STYLE} formatter={(v: unknown) => [`${Number(v ?? 0).toFixed(1)}`, 'Trust Score'] as [string, string]} />
                <defs>
                  <linearGradient id="trustGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#00ff9d" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00ff9d" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <ReferenceLine y={80} stroke="#00ff9d" strokeDasharray="4 4"
                  label={{ value: 'HIGH ≥80', fill: '#00ff9d', fontFamily: 'var(--font-mono)', fontSize: 8, position: 'insideTopLeft' }} />
                <ReferenceLine y={50} stroke="#ffb020" strokeDasharray="4 4"
                  label={{ value: 'MED ≥50', fill: '#ffb020', fontFamily: 'var(--font-mono)', fontSize: 8, position: 'insideTopLeft' }} />
                <Line type="monotone" dataKey="Score" stroke="#00ff9d" strokeWidth={2} dot={false}
                  activeDot={{ r: 4, fill: '#00ff9d' }} />
              </LineChart>
            </ResponsiveContainer>
          )}
          <div className="mt-3 flex gap-4">
            {[
              { label: 'High Trust',   range: '80–100', color: 'var(--green)' },
              { label: 'Medium Trust', range: '50–79',  color: 'var(--amber)' },
              { label: 'Low Trust',    range: '0–49',   color: 'var(--red)' },
            ].map(t => (
              <div key={t.label} className="flex items-center gap-1.5">
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: t.color }} />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
                  {t.label} ({t.range})
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* ══ TAB: Experiment Logs ══════════════════════════════════════════════ */}
      {activeTab === 'log' && (
        <Card className="mb-5">
          <div className="flex items-center gap-3 mb-4">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--purple)" strokeWidth="2">
              <path d="M12 2H2v10l9.29 9.29c.94.94 2.48.94 3.42 0l6.58-6.58c.94-.94.94-2.48 0-3.42L12 2z"/><line x1="7" y1="7" x2="7.01" y2="7"/>
            </svg>
            <span className="card-title">Experiment Log — Research Paper</span>
            <span className="tag ml-auto" style={{ background: 'rgba(191,95,255,0.08)', color: 'var(--purple)',
              border: '1px solid rgba(191,95,255,0.2)', fontSize: 9 }}>
              {expLog.length} runs
            </span>
            <button onClick={() => expLog.length && downloadClientCSV(expLog)}
              className="tag no-print"
              style={{ background: 'rgba(0,255,157,0.07)', color: 'var(--green)',
                border: '1px solid rgba(0,255,157,0.2)', fontSize: 9, cursor: 'pointer' }}>
              Export
            </button>
          </div>
          {expLog.length === 0 ? (
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', textAlign: 'center', padding: '32px 0' }}>
              {loading ? 'Loading…' : 'No experiment data — run training first'}
            </p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table className="w-full data-table" style={{ minWidth: 860 }}>
                <thead>
                  <tr>
                    {['Run ID','Model','Accuracy','Precision','Recall','F1','Train (s)','Pred (ms)','Split','Status'].map(h => (
                      <th key={h} className="text-left" style={{ fontFamily: 'var(--font-mono)', fontSize: 9,
                        color: 'var(--text-lo)', letterSpacing: '0.1em', padding: '8px 10px' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {expLog.map(e => {
                    const c = MODEL_COLOR[e.model] ?? 'var(--text-mid)';
                    return (
                      <tr key={e.run_id}>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', padding: '8px 10px' }}>{e.run_id}</td>
                        <td style={{ padding: '8px 10px' }}>
                          <div className="flex items-center gap-1.5">
                            <div style={{ width: 6, height: 6, borderRadius: '50%', background: c }} />
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: c }}>{e.model}</span>
                          </div>
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-mid)', padding: '8px 10px' }}>{pct(e.accuracy)}</td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-mid)', padding: '8px 10px' }}>{pct(e.precision)}</td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-mid)', padding: '8px 10px' }}>{pct(e.recall)}</td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 9, fontWeight: 600, color: c, padding: '8px 10px' }}>{pct(e.f1_score)}</td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-mid)', padding: '8px 10px' }}>{e.train_time_s}s</td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 9,
                          color: e.pred_time_ms < 100 ? 'var(--green)' : 'var(--amber)', padding: '8px 10px' }}>
                          {e.pred_time_ms} ms
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', padding: '8px 10px' }}>{e.split}</td>
                        <td style={{ padding: '8px 10px' }}>
                          <span className="tag" style={{ fontSize: 8, background: 'rgba(0,255,157,0.07)',
                            color: 'var(--green)', border: '1px solid rgba(0,255,157,0.2)' }}>
                            {e.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
          <div className="mt-3 px-3 py-2 rounded"
            style={{ background: 'rgba(191,95,255,0.03)', border: '1px solid rgba(191,95,255,0.08)' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
              Paper: {summary?.experiment?.reference_paper ?? '—'} · Dataset: CICIDS2017 · Evaluation: Weighted F1
            </span>
          </div>
        </Card>
      )}

      <div style={{ height: 40 }} />

      {/* ── Print CSS injected inline ──────────────────────────────────────── */}
      <style>{`
        @media print {
          .no-print { display: none !important; }
          body { background: white !important; color: black !important; }
          .rounded-xl { border: 1px solid #ccc !important; }
        }
      `}</style>
    </div>
  );
}
