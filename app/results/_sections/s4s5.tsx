'use client';
import { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, Cell,
} from 'recharts';
import { SH, Box, Note, Warn, Spin, Empty, TP, MC, MN, MODEL_KEYS, pct } from './utils';
import type { ResearchComparison, ResearchPerClass, ResearchLatency, FeatureImportance } from '../../../lib/api';

interface Props {
  cmp: ResearchComparison | null;
  pc: ResearchPerClass | null;
  lat: ResearchLatency | null;
  feat: FeatureImportance | null;
  busy: boolean;
}

// ─── §4 Model Comparison ─────────────────────────────────────────────────────
export function S4ModelComparison({ cmp, pc, lat, feat, busy }: Props) {
  const [fiMdl, setFiMdl] = useState(0);
  const rows = cmp?.models ?? [];

  const radarRows = [
    { metric: 'Precision', ...Object.fromEntries(rows.map(r => [MN[r.model_name] ?? r.display_name, +((r.macro_precision ?? 0) * 100).toFixed(1)])) },
    { metric: 'Recall',    ...Object.fromEntries(rows.map(r => [MN[r.model_name] ?? r.display_name, +((r.macro_recall ?? 0) * 100).toFixed(1)])) },
    { metric: 'Macro-F1',  ...Object.fromEntries(rows.map(r => [MN[r.model_name] ?? r.display_name, +((r.macro_f1 ?? 0) * 100).toFixed(1)])) },
    { metric: 'ADR',       ...Object.fromEntries(rows.map(r => [MN[r.model_name] ?? r.display_name, +((r.attack_detection_rate ?? 0) * 100).toFixed(1)])) },
  ];

  const HM_METRICS = [
    { k: 'macro_f1',              l: 'Macro-F1', inv: false },
    { k: 'attack_detection_rate', l: 'ADR',      inv: false },
    { k: 'false_positive_rate',   l: 'FPR',      inv: true  },
    { k: 'macro_precision',       l: 'Precision',inv: false },
    { k: 'macro_recall',          l: 'Recall',   inv: false },
    { k: 'balanced_accuracy',     l: 'Bal.Acc',  inv: false },
  ];

  const fiRows = feat?.models[fiMdl]?.top20 ?? [];

  if (busy) return <section style={{ marginBottom: 52 }}><SH n={4} title="MODEL COMPARISON" /><Spin /></section>;

  return (
    <section style={{ marginBottom: 52 }}>
      <SH n={4} title="MODEL COMPARISON" sub="Multi-metric comparison ranked by Macro-F1 — the primary evaluation criterion." />

      {/* A: Publication table */}
      <Box title="A. PUBLICATION TABLE — RANKED BY MACRO-F1 ★" style={{ marginBottom: 16 }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(0,212,255,.25)' }}>
                {['Rank','Model','Accuracy ⚠','Macro-Prec','Macro-Rec','Wt-F1','Macro-F1 ★','ADR ★','FPR ★','FNR','Train(s)','Inf(s)'].map(h => (
                  <th key={h} style={{ padding: '8px 11px', textAlign: 'left', color: 'var(--cyan)', fontSize: 9, fontWeight: 700, letterSpacing: '.07em', whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, idx) => {
                const warnAcc = (r.accuracy ?? 0) > 0.95;
                const rc = MC[r.model_name] ?? '#0284c7';
                return (
                  <tr key={r.model_name} style={{ borderBottom: '1px solid var(--border-dim)', background: idx === 0 ? 'rgba(0,212,255,.03)' : 'transparent' }}>
                    <td style={{ padding: '9px 11px' }}>
                      <span style={{ background: idx === 0 ? rc + '22' : 'rgba(0,0,0,0.12)', border: `1px solid ${rc}40`, borderRadius: 4, padding: '2px 7px', color: rc, fontWeight: 700 }}>#{r.rank}</span>
                    </td>
                    <td style={{ padding: '9px 11px', color: rc, fontWeight: 700 }}>{r.display_name}</td>
                    <td style={{ padding: '9px 11px' }}>
                      <div style={{ color: 'var(--text-mid)' }}>{pct(r.accuracy)}</div>
                      {warnAcc && <Warn />}
                    </td>
                    <td style={{ padding: '9px 11px', color: 'var(--text-hi)' }}>{pct(r.macro_precision)}</td>
                    <td style={{ padding: '9px 11px', color: 'var(--text-hi)' }}>{pct(r.macro_recall)}</td>
                    <td style={{ padding: '9px 11px', color: 'var(--text-mid)' }}>{pct(r.f1_score)}</td>
                    <td style={{ padding: '9px 11px' }}><span style={{ color: 'var(--green)', fontWeight: 700, fontSize: 13 }}>{pct(r.macro_f1)}</span></td>
                    <td style={{ padding: '9px 11px' }}><span style={{ color: 'var(--cyan)', fontWeight: 700 }}>{pct(r.attack_detection_rate)}</span></td>
                    <td style={{ padding: '9px 11px' }}>
                      <span style={{ color: (r.false_positive_rate ?? 0) > 0.05 ? '#dc2626' : '#059669', fontWeight: 600 }}>{pct(r.false_positive_rate)}</span>
                    </td>
                    <td style={{ padding: '9px 11px', color: 'var(--text-mid)' }}>{pct(r.false_negative_rate)}</td>
                    <td style={{ padding: '9px 11px', color: 'var(--text-mid)' }}>{r.train_time_s?.toFixed(1)}s</td>
                    <td style={{ padding: '9px 11px', color: 'var(--text-mid)' }}>{r.pred_time_s?.toFixed(3)}s</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div style={{ marginTop: 8, fontFamily: 'var(--font-ui)', fontSize: 11, color: 'var(--text-lo)', fontStyle: 'italic' }}>
          ★ Primary metrics. ⚠ Accuracy &gt;95% may be inflated by BENIGN class dominance — interpret with caution.
        </div>
      </Box>

      {/* B: Radar + C: Heatmap */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
        <Box title="B. MULTI-METRIC RADAR COMPARISON" caption="Fig 4.1. Macro-Precision, Macro-Recall, Macro-F1, and ADR. All values as % (0–100).">
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarRows}>
              <PolarGrid stroke="rgba(2,132,199,0.12)" />
              <PolarAngleAxis dataKey="metric" tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: '#8da8c0' }} />
              <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 8, fill: '#2d4a63' }} />
              {rows.map(r => {
                const dn = MN[r.model_name] ?? r.display_name;
                const col = MC[r.model_name] ?? '#0284c7';
                return <Radar key={r.model_name} name={dn} dataKey={dn} stroke={col} fill={col} fillOpacity={0.08} />;
              })}
              <Legend wrapperStyle={{ fontFamily: 'var(--font-mono)', fontSize: 10 }} />
              <Tooltip contentStyle={TP} />
            </RadarChart>
          </ResponsiveContainer>
        </Box>

        <Box title="C. MODEL × METRIC HEATMAP" caption="Fig 4.2. Normalised. FPR inverted (lower = better = darker green).">
          <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--font-mono)', fontSize: 10 }}>
            <thead>
              <tr>
                <th style={{ padding: '5px 8px', color: 'var(--text-lo)', textAlign: 'left', fontSize: 9 }}>Model</th>
                {HM_METRICS.map(m => (
                  <th key={m.k} style={{ padding: '5px 8px', color: 'var(--cyan)', fontSize: 8, letterSpacing: '.06em', textAlign: 'center' }}>{m.l}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map(row => (
                <tr key={row.model_name}>
                  <td style={{ padding: '6px 8px', color: MC[row.model_name] ?? '#0284c7', fontWeight: 700, fontSize: 10 }}>{row.display_name}</td>
                  {HM_METRICS.map(m => {
                    const raw = (row as unknown as Record<string, number>)[m.k] ?? 0;
                    const norm = m.inv ? (1 - Math.min(raw, 1)) : Math.min(raw, 1);
                    const alpha = (0.07 + norm * 0.68).toFixed(2);
                    const tc = norm > 0.7 ? '#059669' : norm > 0.45 ? '#d97706' : '#dc2626';
                    return (
                      <td key={m.k} style={{ padding: '6px 8px', textAlign: 'center', background: `rgba(0,212,255,${alpha})`, borderRadius: 3, color: tc, fontWeight: 600 }}>
                        {(raw * 100).toFixed(1)}%
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </Box>
      </div>

      {/* D: Feature Importance */}
      <Box title="D. FEATURE IMPORTANCE ANALYSIS (XGBoost & Random Forest)" caption="Fig 4.3. Top-20 features by Gini impurity. Critical for reproducibility.">
        {feat && feat.models.length > 0 ? (
          <>
            <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
              {feat.models.map((m, i) => {
                const col = MC[m.model] ?? '#0284c7';
                return (
                  <button key={m.model} onClick={() => setFiMdl(i)} style={{
                    padding: '5px 12px', borderRadius: 5, cursor: 'pointer',
                    fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '.07em',
                    background: fiMdl === i ? col + '18' : '#ffffff',
                    border: `1px solid ${fiMdl === i ? col : 'var(--border-dim)'}`,
                    color: fiMdl === i ? col : 'var(--text-lo)',
                  }}>{m.display_name}</button>
                );
              })}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 16 }}>
              <ResponsiveContainer width="100%" height={380}>
                <BarChart data={fiRows} layout="vertical" margin={{ left: 170, right: 40, top: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.20)" horizontal={false} />
                  <XAxis type="number" tickFormatter={(v: number) => `${(v * 100).toFixed(1)}%`} tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: '#8da8c0' }} />
                  <YAxis type="category" dataKey="name" width={168} tick={{ fontFamily: 'var(--font-mono)', fontSize: 8.5, fill: '#8da8c0' }} />
                  <Tooltip contentStyle={TP} formatter={(v: unknown) => [`${((v as number) * 100).toFixed(3)}%`, 'Importance']} />
                  <Bar dataKey="importance" fill={MC[feat.models[fiMdl]?.model] ?? '#0284c7'} radius={[0, 3, 3, 0]} />
                </BarChart>
              </ResponsiveContainer>
              <div style={{ overflowY: 'auto', maxHeight: 380 }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--font-mono)', fontSize: 10 }}>
                  <thead style={{ position: 'sticky', top: 0, background: '#ffffff' }}>
                    <tr style={{ borderBottom: '1px solid rgba(2,132,199,0.22)' }}>
                      {['#', 'Feature', 'Imp', '%'].map(h => (
                        <th key={h} style={{ padding: '6px 8px', textAlign: 'left', color: 'var(--cyan)', fontSize: 8, letterSpacing: '.07em' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {fiRows.map(f => (
                      <tr key={f.rank} style={{ borderBottom: '1px solid var(--border-dim)' }}>
                        <td style={{ padding: '5px 8px', color: 'var(--text-lo)' }}>{f.rank}</td>
                        <td style={{ padding: '5px 8px', color: 'var(--text-hi)', fontSize: 9, maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</td>
                        <td style={{ padding: '5px 8px', color: 'var(--cyan)', fontWeight: 600 }}>{f.importance.toFixed(5)}</td>
                        <td style={{ padding: '5px 8px', color: 'var(--text-mid)' }}>{f.pct.toFixed(2)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <Note>TCP-flag indicators (e.g. fin_flag_number) and packet-rate statistics dominate the top-20 for both XGBoost and Random Forest, confirming flag/rate patterns are the most discriminative signals for CICIoT2023 IoT attacks.</Note>
          </>
        ) : (
          <Empty msg="Feature importance requires trained model pickle files. Run: python backend/ml_model/train_ciciot2023_models.py" />
        )}
      </Box>
    </section>
  );
}

// ─── §5 Performance Analysis ─────────────────────────────────────────────────
const FIG_NOTES: Record<string, string> = {
  accuracy:            'Inflated by DDoS/BENIGN class dominance. Not a reliable primary metric.',
  macro_f1:            'Primary metric. XGBoost (71.51%) leads; distance/linear baselines (KNN, LR, SVM) show large gaps vs tree ensembles.',
  attack_detection_rate: 'XGBoost achieves the best ADR (70.35%) across the 34 attack classes.',
  balanced_accuracy:   'Balanced across all 34 classes — tree ensembles lead by a wide margin.',
  train_time_s:        'Naive Bayes / KNN train near-instantly; XGBoost trains in ~11s on GPU. SVM inference is impractical (~18 min).',
};

export function S5Performance({ cmp, lat, busy }: { cmp: ResearchComparison | null; lat: ResearchLatency | null; busy: boolean }) {
  const rows = cmp?.models ?? [];
  const latData = (lat?.latency ?? []).map(r => ({
    name: MN[r.model] ?? r.display_name,
    inferencMs: +r.pred_time_ms.toFixed(0),
    color: MC[r.model] ?? '#0284c7',
  }));

  if (busy) return <section style={{ marginBottom: 52 }}><SH n={5} title="PERFORMANCE ANALYSIS" /><Spin /></section>;

  const BAR_METRICS = [
    { key: 'accuracy',             label: 'Accuracy',                fig: 1, raw: false },
    { key: 'macro_f1',             label: 'Macro-F1 Score ★',        fig: 2, raw: false },
    { key: 'attack_detection_rate',label: 'Attack Detection Rate ★', fig: 3, raw: false },
    { key: 'false_positive_rate',  label: 'FPR (lower = better) ★',  fig: 4, raw: false },
    { key: 'train_time_s',         label: 'Training Time (s)',        fig: 5, raw: true  },
  ];

  return (
    <section style={{ marginBottom: 52 }}>
      <SH n={5} title="PERFORMANCE ANALYSIS" sub="Individual metric figures with research interpretation captions." />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(400px,1fr))', gap: 16 }}>
        {BAR_METRICS.map(({ key, label, fig, raw }) => {
          const data = rows.map(r => ({
            name: r.display_name,
            value: raw
              ? ((r as unknown as Record<string, number>)[key] ?? 0)
              : +((((r as unknown as Record<string, number>)[key]) ?? 0) * 100).toFixed(2),
            fill: MC[r.model_name] ?? '#0284c7',
          }));
          const unit = raw ? 's' : '%';
          return (
            <Box key={key} title={`FIGURE ${fig}: ${label.toUpperCase()}`}
              caption={`Fig 5.${fig}. ${label} across all four models.`}>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={data} margin={{ top: 5, right: 12, bottom: 5, left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.20)" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: '#8da8c0' }} />
                  <YAxis tickFormatter={(v: number) => `${v}${unit}`} tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: '#8da8c0' }} />
                  <Tooltip contentStyle={TP} formatter={(v: unknown) => [`${v as number}${unit}`, label]} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {data.map((d, i) => <Cell key={i} fill={d.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <Note>{FIG_NOTES[key]}</Note>
            </Box>
          );
        })}

        <Box title="FIGURE 6: INFERENCE LATENCY (ms) ★" caption="Fig 5.6. Batch inference over the full test set. Decision Tree is fastest; SVM is orders of magnitude slower.">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={latData} margin={{ top: 5, right: 12, bottom: 5, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.20)" vertical={false} />
              <XAxis dataKey="name" tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: '#8da8c0' }} />
              <YAxis tickFormatter={(v: number) => `${v}ms`} tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: '#8da8c0' }} />
              <Tooltip contentStyle={TP} formatter={(v: unknown) => [`${v as number}ms`, 'Latency']} />
              <Bar dataKey="inferencMs" name="Inference (ms)" radius={[4, 4, 0, 0]}>
                {latData.map((d, i) => <Cell key={i} fill={d.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <Note>SVM batch inference (~18 min over the test set) disqualifies it for real-time use, whereas Decision Tree (~267 ms) and XGBoost are suitable for live per-flow classification.</Note>
        </Box>
      </div>
    </section>
  );
}
