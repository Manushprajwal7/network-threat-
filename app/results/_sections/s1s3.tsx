'use client';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts';
import { SH, Box, Note, TP, pct } from './utils';
import type { ResearchComparison, ResearchPerClass } from '../../../lib/api';

// ─── §1 Executive Summary ─────────────────────────────────────────────────────
export function S1Executive({ cmp }: { cmp: ResearchComparison | null }) {
  const kpis = [
    { l: 'Dataset',      v: 'CICIoT2023',                             s: 'IoT intrusion benchmark',     c: 'var(--cyan)' },
    { l: 'Features',     v: String(cmp?.num_features ?? 46),          s: 'Flow-level features',         c: 'var(--cyan)' },
    { l: 'Classes',      v: String(cmp?.num_classes ?? 34),           s: 'Traffic categories',          c: '#7c3aed' },
    { l: 'Evaluation',   v: 'Train/Val/Test',                         s: 'Separate folder split',       c: 'var(--green)' },
    { l: 'Best Macro-F1',v: cmp ? pct(cmp.best_macro_f1) : '71.51%', s: cmp?.best_model ?? 'XGBoost', c: 'var(--green)' },
    { l: 'Best ADR',     v: cmp ? pct(cmp.best_adr)     : '70.35%',  s: 'Attack Detection Rate',      c: '#d97706' },
  ];
  const findings = [
    { n: 1, c: '#7c3aed', t: 'XGBoost Leads Macro-F1',
      d: `XGBoost (GPU-accelerated) achieves Macro-F1 = ${cmp ? pct(cmp.best_macro_f1) : '71.51%'} at 98.99% accuracy — the best of the seven models across all 34 classes.` },
    { n: 2, c: '#0284c7', t: 'Tree Ensembles Dominate',
      d: 'XGBoost, Decision Tree (66.23%) and Random Forest (63.95%) lead by a wide margin, motivating the RF + XGBoost live ensemble.' },
    { n: 3, c: '#ec4899', t: 'Distance/Linear Baselines Fail',
      d: 'Naive Bayes (17.13% Macro-F1) and KNN / Logistic Regression / SVM (<1%) do not generalise on this 34-class IoT problem.' },
    { n: 4, c: '#d97706', t: 'Accuracy Misleads on CICIoT2023',
      d: 'Models reach >98% accuracy due to DDoS/BENIGN dominance. Macro-F1 and ADR reveal the true per-class performance gaps.' },
  ];

  return (
    <section style={{ marginBottom: 52 }}>
      <SH n={1} title="EXECUTIVE SUMMARY" sub="High-level overview of key experimental outcomes and primary metrics." />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(175px,1fr))', gap: 12, marginBottom: 16 }}>
        {kpis.map(k => (
          <div key={k.l} style={{ background: '#ffffff', border: '1px solid #000000', borderRadius: 11, padding: '16px 18px' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '.14em', marginBottom: 6 }}>{k.l}</div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 700, color: k.c, lineHeight: 1 }}>{k.v}</div>
            <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: 'var(--text-mid)', marginTop: 5 }}>{k.s}</div>
          </div>
        ))}
      </div>
      {cmp && (
        <div style={{
          background: 'linear-gradient(135deg,rgba(0,0,0,0.20),rgba(5,150,105,0.06))',
          border: '1px solid rgba(2,132,199,0.22)', borderRadius: 12, padding: '18px 22px', marginBottom: 16,
        }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--cyan)', letterSpacing: '.14em', marginBottom: 8 }}>
            BEST PERFORMING MODEL (ranked by Macro-F1)
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 24, flexWrap: 'wrap' }}>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 32, fontWeight: 700, color: 'var(--cyan)' }}>{cmp.best_model}</div>
            {[
              { l: 'Macro-F1 ★', v: pct(cmp.best_macro_f1) },
              { l: 'ADR ★',      v: pct(cmp.best_adr) },
              { l: 'Accuracy ⚠', v: pct(cmp.best_accuracy) },
              { l: 'Split',      v: 'Train/Val/Test' },
            ].map(m => (
              <div key={m.l}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '.1em' }}>{m.l}</div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700, color: 'var(--text-hi)' }}>{m.v}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))', gap: 12 }}>
        {findings.map(f => (
          <div key={f.n} style={{
            background: '#ffffff', borderLeft: `3px solid ${f.c}`,
            border: `1px solid ${f.c}22`, borderLeftWidth: 3, borderRadius: '0 10px 10px 0', padding: '13px 15px',
          }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: f.c, letterSpacing: '.1em', marginBottom: 5 }}>FINDING #{f.n}</div>
            <div style={{ fontFamily: 'var(--font-ui)', fontSize: 13, fontWeight: 600, color: 'var(--text-hi)', marginBottom: 5 }}>{f.t}</div>
            <p style={{ fontFamily: 'var(--font-ui)', fontSize: 12, color: 'var(--text-mid)', margin: 0, lineHeight: 1.65 }}>{f.d}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

// ─── §2 Dataset Analysis ─────────────────────────────────────────────────────
export function S2Dataset({ pc }: { pc: ResearchPerClass | null }) {
  const isBenign = (n: string) => n === 'BENIGN' || n === 'BenignTraffic';
  const classDist = (pc?.models_data['xgboost']?.rows ?? []).map(r => ({
    name: r.class, value: r.support, fill: isBenign(r.class) ? '#0284c7' : '#dc2626',
  }));
  const total = classDist.reduce((s, d) => s + d.value, 0);
  const benign = classDist.find(d => isBenign(d.name))?.value ?? 0;
  const attack = total - benign;
  const pieData = [{ name: 'Attack', value: attack }, { name: 'Benign', value: benign }];

  return (
    <section style={{ marginBottom: 52 }}>
      <SH n={2} title="DATASET ANALYSIS" sub="Statistical characterisation of the CICIoT2023 IoT benchmark dataset." />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <Box
          title="A. CLASS DISTRIBUTION — TEST PARTITION"
          caption="Fig 2.1. Sample counts per class in the held-out test set (1,176,851 flows across 34 classes)."
        >
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, alignItems: 'start' }}>
            <ResponsiveContainer width="100%" height={340}>
              <BarChart data={classDist} layout="vertical" margin={{ left: 140, right: 30, top: 4, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.20)" horizontal={false} />
                <XAxis type="number" tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: '#8da8c0' }} />
                <YAxis type="category" dataKey="name" width={138} tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: '#8da8c0' }} />
                <Tooltip contentStyle={TP} />
                <Bar dataKey="value" name="Samples" radius={[0, 3, 3, 0]}>
                  {classDist.map((d, i) => <Cell key={i} fill={d.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 11, color: 'var(--cyan)', letterSpacing: '.08em', marginBottom: 14 }}>CLASS STATISTICS</div>
              {classDist.map(d => {
                const share = total > 0 ? (d.value / total * 100).toFixed(1) : '0.0';
                return (
                  <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 5 }}>
                    <div style={{ width: 6, height: 6, borderRadius: 2, background: d.fill, flexShrink: 0 }} />
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-mid)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d.name}</span>
                    <span style={{ fontFamily: 'var(--font-display)', fontSize: 12, fontWeight: 600, color: d.fill, flexShrink: 0 }}>{d.value.toLocaleString()}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', flexShrink: 0, width: 40, textAlign: 'right' }}>{share}%</span>
                  </div>
                );
              })}
            </div>
          </div>
          <Note>
            Severe class imbalance: large DDoS/DoS floods dominate while rare classes such as Uploading_Attack,
            Recon-PingSweep, Backdoor_Malware and XSS have very low test support — making per-class F1 unreliable for
            these classes and directly motivating Macro-F1 over weighted F1.
          </Note>
        </Box>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <Box title="B. ATTACK VS BENIGN COMPOSITION" caption="Fig 2.2. Traffic composition in the temporal test partition.">
            <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
              <ResponsiveContainer width="50%" height={200}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={48} outerRadius={78} dataKey="value" paddingAngle={4}>
                    <Cell fill="#dc2626" /><Cell fill="#0284c7" />
                  </Pie>
                  <Tooltip contentStyle={TP} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ flex: 1 }}>
                {[{ n: 'Attack Traffic', v: attack, c: '#dc2626' }, { n: 'Benign Traffic', v: benign, c: '#0284c7' }].map(d => (
                  <div key={d.n} style={{ marginBottom: 14 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                      <div style={{ width: 8, height: 8, borderRadius: 2, background: d.c }} />
                      <span style={{ fontFamily: 'var(--font-ui)', fontSize: 12, color: 'var(--text-mid)' }}>{d.n}</span>
                    </div>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: d.c }}>
                      {d.v.toLocaleString()}
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', marginLeft: 6 }}>
                        ({total > 0 ? (d.v / total * 100).toFixed(1) : '0.0'}%)
                      </span>
                    </div>
                  </div>
                ))}
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '.1em' }}>
                  TOTAL: {total.toLocaleString()} SAMPLES
                </div>
              </div>
            </div>
          </Box>

          <Box title="C. DATASET SPECIFICATIONS">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              {[
                { l: 'Dataset',        v: 'CICIoT2023' },
                { l: 'Features',       v: '46 (network flow)' },
                { l: 'Total Classes',  v: '34 (33 attack + 1 benign)' },
                { l: 'Split',          v: 'Train/Val/Test folders' },
                { l: 'Scaler',         v: 'StandardScaler (train-fit)' },
                { l: 'Outlier Clip',   v: '1st–99th percentile' },
                { l: 'Deduplication',  v: 'Class-aware (BENIGN)' },
                { l: 'Primary Metric', v: 'Macro-F1 + ADR' },
                { l: 'Test Samples',   v: total.toLocaleString() },
                { l: 'Attack Samples', v: attack.toLocaleString() },
              ].map(r => (
                <div key={r.l} style={{ background: 'rgba(0,212,255,.03)', border: '1px solid #000000', borderRadius: 6, padding: '8px 10px' }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '.08em', marginBottom: 2 }}>{r.l}</div>
                  <div style={{ fontFamily: 'var(--font-ui)', fontSize: 12, color: 'var(--text-hi)' }}>{r.v}</div>
                </div>
              ))}
            </div>
          </Box>
        </div>
      </div>
    </section>
  );
}

// ─── §3 Experimental Setup ───────────────────────────────────────────────────
const SETUP_CARDS = [
  { title: 'EVALUATION PIPELINE', color: '#0284c7', items: [
    'Separate train / validation / test folders — no random leakage',
    'StandardScaler fitted on training partition only',
    '1st/99th percentile clipping (train-fit, test-applied)',
    'Class-aware deduplication preserving all attack diversity',
    'Class-weighted training to counter imbalance',
  ]},
  { title: 'MODELS EVALUATED (7)', color: '#059669', items: [
    'XGBoost — GPU-accelerated gradient-boosted trees',
    'Random Forest — bagging ensemble of decision trees',
    'Decision Tree — single CART baseline',
    'Naive Bayes · Logistic Regression · KNN · SVM baselines',
    'Live inference uses an RF + XGBoost ensemble',
  ]},
  { title: 'PRIMARY EVALUATION METRICS', color: '#7c3aed', items: [
    'Macro-F1 Score (equal weight per class)',
    'Attack Detection Rate (ADR = macro-average attack recall)',
    'Balanced accuracy across all 34 classes',
    'Per-class Precision / Recall / F1-Score',
    'Training time and inference latency',
  ]},
  { title: 'INTEGRITY CONTROLS', color: '#d97706', items: [
    'Accuracy warning badges for results >95%',
    'Macro-F1 reported as the primary (honest) metric',
    'Held-out test folder never seen during training',
    'Class-aware dedup avoids BENIGN train/test overlap',
    'Separate classification report + confusion matrix per model',
  ]},
];

export function S3Setup() {
  return (
    <section style={{ marginBottom: 52 }}>
      <SH n={3} title="EXPERIMENTAL SETUP" sub="Research-grade evaluation pipeline with strict temporal integrity and class-imbalance controls." />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(270px,1fr))', gap: 14 }}>
        {SETUP_CARDS.map(c => (
          <Box key={c.title} title={c.title} accent={c.color}>
            <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
              {c.items.map((it, i) => (
                <li key={i} style={{ display: 'flex', gap: 8, marginBottom: 8, fontFamily: 'var(--font-ui)', fontSize: 12, color: 'var(--text-mid)', lineHeight: 1.55 }}>
                  <span style={{ color: c.color, flexShrink: 0 }}>›</span>{it}
                </li>
              ))}
            </ul>
          </Box>
        ))}
      </div>
    </section>
  );
}
