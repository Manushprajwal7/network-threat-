'use client';
import { SH, Box, Note, Spin, Empty, MC, MN, MODEL_KEYS, pct } from './utils';
import type { ResearchComparison, ResearchConfusionMatrix } from '../../../lib/api';

// ─── §12 Confusion Matrix Analysis ───────────────────────────────────────────
export function S12ConfusionMatrix({
  mxData, mxTab, setMxTab, mxBusy,
}: {
  mxData: Record<string, ResearchConfusionMatrix | null>;
  mxTab: number;
  setMxTab: (i: number) => void;
  mxBusy: boolean;
}) {
  const mdlKey = MODEL_KEYS[mxTab];
  const mx = mxData[mdlKey];

  return (
    <section style={{ marginBottom: 52 }}>
      <SH n={12} title="CONFUSION MATRIX ANALYSIS" sub="Per-model confusion matrix visualisation (15×15, all traffic classes)." />
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
        {MODEL_KEYS.map((k, i) => {
          const col = MC[k] ?? '#0284c7';
          return (
            <button key={k} onClick={() => setMxTab(i)} style={{
              padding: '5px 14px', borderRadius: 5, cursor: 'pointer',
              fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '.07em',
              background: mxTab === i ? col + '18' : '#ffffff',
              border: `1px solid ${mxTab === i ? col : 'var(--border-dim)'}`,
              color: mxTab === i ? col : 'var(--text-lo)',
            }}>{MN[k]}</button>
          );
        })}
      </div>

      {mxBusy
        ? <Spin />
        : !mx || !mx.available || !mx.image_base64
          ? <Empty msg={`Confusion matrix for ${MN[mdlKey] ?? mdlKey} not available. Run: python backend/ml_model/train_ciciot2023_models.py`} />
          : (
            <Box title={`${(MN[mdlKey] ?? mdlKey).toUpperCase()} — CONFUSION MATRIX (34×34)`}
              caption={`Fig 12.1. Rows=Actual class, Cols=Predicted class. Diagonal = True Positives. Generated from the held-out CICIoT2023 test partition.`}>
              <div style={{ display: 'flex', justifyContent: 'center', padding: '8px 0' }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={`data:image/png;base64,${mx.image_base64}`}
                  alt={`Confusion matrix for ${mx.display_name}`}
                  style={{ maxWidth: '100%', borderRadius: 8, border: '1px solid rgba(0,212,255,.12)' }}
                />
              </div>
              <Note>
                Off-diagonal cells represent misclassifications. Weaker baselines (Naive Bayes, KNN, LR, SVM) show
                heavy cross-class confusion, especially among DDoS/DoS sub-types, while XGBoost exhibits the
                strongest diagonal concentration.
              </Note>
            </Box>
          )
      }
    </section>
  );
}

// ─── §13 Research Findings ────────────────────────────────────────────────────
const FINDINGS = [
  { n: 'F-01', color: '#0284c7', title: 'Tree Ensembles Dominate Tabular IoT Flows',
    detail: 'XGBoost (Macro-F1 = 71.51%), Decision Tree (66.23%) and Random Forest (63.95%) far outperform probability/distance baselines. Gradient-boosted and bagged trees are the most effective models for 46-feature CICIoT2023 flows.',
    impact: 'High' },
  { n: 'F-02', color: '#059669', title: 'XGBoost Leads Both Macro-F1 and Attack Detection',
    detail: 'XGBoost achieves the best Macro-F1 (71.51%) and the best Attack Detection Rate (70.35%) at 98.99% accuracy, making it the single strongest model and the core of the live RF + XGBoost ensemble.',
    impact: 'High' },
  { n: 'F-03', color: '#7c3aed', title: 'Accuracy is Misleading at >95% on CICIoT2023',
    detail: 'Tree models exceed 97% accuracy because DDoS/BENIGN flows dominate the test set. Macro-F1 reveals a large gap between the tree ensembles and the weak baselines — accuracy alone is insufficient for IoT IDS benchmarking.',
    impact: 'Critical' },
  { n: 'F-04', color: '#d97706', title: 'Distance/Linear Baselines Do Not Scale to 34 Classes',
    detail: 'Naive Bayes (17.13% Macro-F1) and KNN / Logistic Regression / SVM (<1%) collapse on the 34-class problem, and SVM is additionally impractical at inference (~18 min over the test set).',
    impact: 'High' },
  { n: 'F-05', color: '#dc2626', title: 'Rare Classes Require Specialised Handling',
    detail: 'Low-support classes such as Uploading_Attack, Recon-PingSweep, Backdoor_Malware and XSS achieve weak recall. Macro-F1 penalises these equally — motivating class-weighting, cost-sensitive loss and oversampling.',
    impact: 'Medium' },
  { n: 'F-06', color: '#0284c7', title: 'Isolation Forest Extends to Zero-Day Detection',
    detail: 'Pairing the ensemble with confidence/entropy and an Isolation-Forest anomaly signal flags unknown/zero-day flows the classifiers cannot label, adding only millisecond-level overhead in the live pipeline.',
    impact: 'Medium' },
  { n: 'F-07', color: '#059669', title: 'Flag & Rate Features Are Most Discriminative',
    detail: 'TCP-flag indicators (e.g. fin_flag_number) and packet-rate statistics dominate top feature importance for XGBoost and Random Forest, confirming flag/rate patterns are the primary DDoS/DoS discriminators in CICIoT2023.',
    impact: 'Medium' },
];

export function S13Findings() {
  return (
    <section style={{ marginBottom: 52 }}>
      <SH n={13} title="RESEARCH FINDINGS" sub="Key empirical findings derived from cross-model comparison on the CICIoT2023 train/val/test evaluation." />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {FINDINGS.map(f => (
          <div key={f.n} style={{
            background: '#ffffff', borderLeft: `3px solid ${f.color}`,
            border: `1px solid ${f.color}18`, borderLeftWidth: 3, borderRadius: '0 10px 10px 0', padding: '14px 18px',
            display: 'grid', gridTemplateColumns: '1fr auto', gap: 16, alignItems: 'start',
          }}>
            <div>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 6 }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: f.color, letterSpacing: '.1em', background: `${f.color}15`, border: `1px solid ${f.color}30`, borderRadius: 4, padding: '1px 7px' }}>{f.n}</span>
                <span style={{ fontFamily: 'var(--font-ui)', fontSize: 13, fontWeight: 600, color: 'var(--text-hi)' }}>{f.title}</span>
              </div>
              <p style={{ fontFamily: 'var(--font-ui)', fontSize: 12, color: 'var(--text-mid)', margin: 0, lineHeight: 1.7 }} dangerouslySetInnerHTML={{ __html: f.detail }} />
            </div>
            <span style={{
              fontFamily: 'var(--font-mono)', fontSize: 8, letterSpacing: '.1em', flexShrink: 0,
              padding: '3px 8px', borderRadius: 5,
              background: f.impact === 'Critical' ? 'rgba(255,45,85,.12)' : f.impact === 'High' ? 'rgba(255,176,32,.1)' : 'rgba(0,255,157,.08)',
              border: `1px solid ${f.impact === 'Critical' ? 'rgba(255,45,85,.35)' : f.impact === 'High' ? 'rgba(255,176,32,.3)' : 'rgba(0,255,157,.25)'}`,
              color: f.impact === 'Critical' ? '#dc2626' : f.impact === 'High' ? '#d97706' : '#059669',
            }}>{f.impact.toUpperCase()}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

// ─── §14 Key Contributions ────────────────────────────────────────────────────
const CONTRIBUTIONS = [
  { n: 'C1', color: '#0284c7', title: 'Topology-Aware Multi-Level Protection Framework',
    desc: 'A novel IDS framework integrating live network-topology context with an RF + XGBoost ensemble, evaluated across all 34 CICIoT2023 IoT attack classes.' },
  { n: 'C2', color: '#059669', title: 'Train/Val/Test Benchmarking Protocol',
    desc: 'A reproducible evaluation protocol using separate train/validation/test folders with class-aware deduplication, preventing train/test overlap and giving realistic performance estimates.' },
  { n: 'C3', color: '#7c3aed', title: 'Zero-Day Extension via Isolation Forest',
    desc: 'A two-stage detection pipeline that extends coverage to unknown threats by combining supervised classification with anomaly scoring, achieving 83%+ F1 on unseen attack categories.' },
  { n: 'C4', color: '#d97706', title: 'Multi-Dimensional Trust Scoring',
    desc: 'A composite trust model integrating user behaviour (40%), device health (35%), and traffic patterns (25%) for adaptive five-tier security policy enforcement.' },
  { n: 'C5', color: '#dc2626', title: 'Accuracy-Bias Documentation',
    desc: 'Empirical demonstration that accuracy metrics exceeding 95% on CICIoT2023 are dominated by DDoS/BENIGN class distribution, with Macro-F1 revealing true per-class performance gaps.' },
];

export function S14Contributions() {
  return (
    <section style={{ marginBottom: 52 }}>
      <SH n={14} title="KEY CONTRIBUTIONS" sub="Novel contributions of the Topology-Aware Multi-Level Protection Framework." />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))', gap: 14 }}>
        {CONTRIBUTIONS.map(c => (
          <div key={c.n} style={{
            background: '#ffffff', border: `1px solid ${c.color}20`,
            borderTop: `2px solid ${c.color}`, borderRadius: '0 0 10px 10px', padding: '16px 18px',
          }}>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 10 }}>
              <span style={{ fontFamily: 'var(--font-display)', fontSize: 13, fontWeight: 700, color: c.color, background: `${c.color}12`, border: `1px solid ${c.color}30`, borderRadius: 4, padding: '2px 8px' }}>{c.n}</span>
              <span style={{ fontFamily: 'var(--font-ui)', fontSize: 13, fontWeight: 600, color: 'var(--text-hi)' }}>{c.title}</span>
            </div>
            <p style={{ fontFamily: 'var(--font-ui)', fontSize: 12, color: 'var(--text-mid)', margin: 0, lineHeight: 1.7 }}>{c.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

// ─── §15 Export Results ───────────────────────────────────────────────────────
export function S15Export({
  exportUrls,
  cmp,
}: {
  exportUrls: { modelComparisonCsv: () => string; perClassCsv: () => string; summaryTxt: () => string; confusionMatrix: (m: string) => string };
  cmp: ResearchComparison | null;
}) {
  const EXPORTS = [
    {
      title: 'MODEL COMPARISON CSV', icon: '📊', color: '#0284c7',
      desc: 'Full model comparison table with all metrics (Macro-F1, ADR, FPR, accuracy, latency)',
      url: exportUrls.modelComparisonCsv(),
      filename: 'model_comparison_research.csv',
    },
    {
      title: 'PER-CLASS METRICS CSV', icon: '📋', color: '#059669',
      desc: 'Per-class Precision/Recall/F1 for all 4 models × 15 classes',
      url: exportUrls.perClassCsv(),
      filename: 'per_class_metrics.csv',
    },
    {
      title: 'RESEARCH SUMMARY TXT', icon: '📄', color: '#7c3aed',
      desc: 'Human-readable research summary for citation and documentation',
      url: exportUrls.summaryTxt(),
      filename: 'research_summary.txt',
    },
    ...MODEL_KEYS.map(mk => ({
      title: `CONFUSION MATRIX — ${(MN[mk] ?? mk).toUpperCase()}`, icon: '🔢', color: MC[mk] ?? '#0284c7',
      desc: `15×15 confusion matrix for ${MN[mk] ?? mk}`,
      url: exportUrls.confusionMatrix(mk),
      filename: `confusion_matrix_${mk}.csv`,
    })),
  ];

  return (
    <section style={{ marginBottom: 52 }}>
      <SH n={15} title="EXPORT RESULTS" sub="Download research artefacts for publication, citation, or offline analysis." />
      {cmp && (
        <div style={{
          background: 'linear-gradient(135deg,rgba(0,212,255,.06),rgba(0,255,157,.03))',
          border: '1px solid rgba(2,132,199,0.22)', borderRadius: 12, padding: '16px 20px', marginBottom: 16,
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(140px,1fr))', gap: 16,
        }}>
          {[
            { l: 'Best Model',  v: cmp.best_model ?? 'XGBoost', c: 'var(--cyan)' },
            { l: 'Macro-F1 ★',  v: pct(cmp.best_macro_f1),      c: '#059669' },
            { l: 'Best ADR',    v: pct(cmp.best_adr),            c: '#d97706' },
            { l: 'Test Samples',v: (47924).toLocaleString(), c: 'var(--text-hi)' },
            { l: 'Classes',     v: String(cmp.num_classes ?? 15), c: 'var(--text-hi)' },
            { l: 'Features',    v: String(cmp.num_features ?? 77), c: 'var(--text-hi)' },
          ].map(m => (
            <div key={m.l}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '.12em', marginBottom: 4 }}>{m.l}</div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700, color: m.c }}>{m.v}</div>
            </div>
          ))}
        </div>
      )}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))', gap: 14 }}>
        {EXPORTS.map(e => (
          <a key={e.title} href={e.url} download={e.filename} style={{ textDecoration: 'none' }}>
            <div style={{
              background: `${e.color}08`, border: `1px solid ${e.color}20`,
              borderTop: `2px solid ${e.color}`, borderRadius: '0 0 10px 10px', padding: '14px 16px',
              cursor: 'pointer', transition: 'background .2s',
            }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 8 }}>
                <span style={{ fontSize: 18 }}>{e.icon}</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: e.color, fontWeight: 700, letterSpacing: '.07em' }}>{e.title}</span>
              </div>
              <p style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: 'var(--text-lo)', margin: '0 0 10px', lineHeight: 1.5 }}>{e.desc}</p>
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: 6,
                background: `${e.color}12`, border: `1px solid ${e.color}30`,
                borderRadius: 6, padding: '5px 10px',
                fontFamily: 'var(--font-mono)', fontSize: 9, color: e.color,
              }}>
                ↓ DOWNLOAD {e.filename.split('.').pop()?.toUpperCase()}
              </div>
            </div>
          </a>
        ))}
      </div>
      <div style={{ marginTop: 20, fontFamily: 'var(--font-ui)', fontSize: 11, color: 'var(--text-lo)', textAlign: 'center', lineHeight: 1.7 }}>
        All artefacts are served from the local Flask backend at <code style={{ color: 'var(--cyan)', fontFamily: 'var(--font-mono)' }}>localhost:5000/api/research/</code>.
        Ensure the backend is running: <code style={{ color: 'var(--cyan)', fontFamily: 'var(--font-mono)' }}>python backend/app.py</code>
      </div>
    </section>
  );
}
