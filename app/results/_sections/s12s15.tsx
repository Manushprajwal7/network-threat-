'use client';
import { SH, Box, Note, Spin, Empty, MC, MN, MODEL_KEYS, pct } from './utils';
import { getResearchConfusionMatrix } from '../../../lib/api';
import type { ResearchComparison, ResearchConfusionMatrix, ResearchPerClass, ResearchLatency, FeatureImportance } from '../../../lib/api';

// All CICIoT2023 models that have a generated confusion-matrix PNG.
const ALL_CM_MODELS = [
  'xgboost', 'random_forest', 'decision_tree',
  'logistic_regression', 'svm', 'knn', 'naive_bayes',
] as const;

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

// ─── §15 Export helpers (client-side, dependency-free) ────────────────────────

function downloadBlob(filename: string, blob: Blob) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Build a CSV blob from an array of flat objects (union of all keys = header). */
function csvBlob(rows: Record<string, unknown>[]): Blob {
  const cols = Array.from(rows.reduce<Set<string>>((s, r) => {
    Object.keys(r).forEach(k => s.add(k)); return s;
  }, new Set()));
  const esc = (v: unknown) => {
    const s = v == null ? '' : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const lines = [cols.join(','), ...rows.map(r => cols.map(c => esc(r[c])).join(','))];
  return new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' });
}

/** Decode a base64 string into a Blob (default PNG). */
function b64ToBlob(b64: string, type = 'image/png'): Blob {
  const bytes = atob(b64);
  const arr = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
  return new Blob([arr], { type });
}

/**
 * Download one confusion-matrix PNG by fetching the base64 image from the
 * (working) display endpoint and saving it via a same-origin blob URL.
 * This avoids the cross-origin `download`-attribute limitation entirely.
 * Returns true on success.
 */
async function downloadConfusionMatrix(model: string): Promise<boolean> {
  try {
    const data = await getResearchConfusionMatrix(model);
    if (!data?.available || !data.image_base64) return false;
    downloadBlob(`confusion_matrix_${model}_ciciot2023.png`, b64ToBlob(data.image_base64));
    return true;
  } catch {
    return false;
  }
}

/** Download every available confusion matrix, one PNG per model. */
async function downloadAllConfusionMatrices() {
  let ok = 0, fail = 0;
  for (const m of ALL_CM_MODELS) {
    const done = await downloadConfusionMatrix(m);
    if (done) ok++; else fail++;
    // Small gap so the browser reliably processes each separate download.
    await new Promise(r => setTimeout(r, 450));
  }
  if (fail > 0) {
    alert(`Downloaded ${ok} confusion matrix PNG(s). ${fail} unavailable — ensure the backend is running and models are trained.`);
  }
}

/** Rasterise a single SVG element to an HTMLImageElement at its rendered size. */
function svgToImage(svg: SVGSVGElement): Promise<{ img: HTMLImageElement; w: number; h: number }> {
  const w = Math.round(+svg.getAttribute('width')! || svg.getBoundingClientRect().width || 600);
  const h = Math.round(+svg.getAttribute('height')! || svg.getBoundingClientRect().height || 300);
  const clone = svg.cloneNode(true) as SVGSVGElement;
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  clone.setAttribute('width', String(w));
  clone.setAttribute('height', String(h));
  // Opaque white background so transparent chart areas don't render black.
  const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  bg.setAttribute('x', '0'); bg.setAttribute('y', '0');
  bg.setAttribute('width', String(w)); bg.setAttribute('height', String(h));
  bg.setAttribute('fill', '#ffffff');
  clone.insertBefore(bg, clone.firstChild);
  const data = new XMLSerializer().serializeToString(clone);
  const url = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(data);
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve({ img, w, h });
    img.onerror = reject;
    img.src = url;
  });
}

/** Capture every Recharts SVG inside #report-content into one stacked PNG. */
async function exportAllChartsPng() {
  const svgs = Array.from(
    document.querySelectorAll<SVGSVGElement>('#report-content svg.recharts-surface')
  );
  if (!svgs.length) { alert('No charts are currently rendered on the page.'); return; }
  const imgs = await Promise.all(svgs.map(svgToImage));
  const pad = 28, scale = 2;
  const width  = Math.max(...imgs.map(i => i.w)) + pad * 2;
  const height = imgs.reduce((acc, i) => acc + i.h + pad, pad);
  const canvas = document.createElement('canvas');
  canvas.width = width * scale; canvas.height = height * scale;
  const ctx = canvas.getContext('2d')!;
  ctx.scale(scale, scale);
  ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, width, height);
  let y = pad;
  for (const im of imgs) {
    const x = (width - im.w) / 2;
    ctx.drawImage(im.img, x, y, im.w, im.h);
    y += im.h + pad;
  }
  canvas.toBlob(b => { if (b) downloadBlob('results_all_charts.png', b); }, 'image/png');
}

// ─── §15 Export Results ───────────────────────────────────────────────────────
export function S15Export({
  exportUrls,
  cmp,
  pc,
  lat,
  feat,
}: {
  exportUrls: { modelComparisonCsv: () => string; perClassCsv: () => string; summaryTxt: () => string; confusionMatrix: (m: string) => string };
  cmp: ResearchComparison | null;
  pc: ResearchPerClass | null;
  lat: ResearchLatency | null;
  feat: FeatureImportance | null;
}) {
  // Derived, dataset-accurate figures (no hardcoded values).
  const numModels  = cmp?.count ?? 7;
  const numClasses = cmp?.num_classes ?? 34;
  const numFeats   = cmp?.num_features ?? 46;

  // Test-set size = total support of any single model's per-class rows.
  const testSamples = (() => {
    if (!pc) return null;
    const firstModel = pc.model_list?.[0];
    const rows = firstModel ? pc.models_data?.[firstModel]?.rows : undefined;
    if (!rows?.length) return null;
    return rows.reduce((s, r) => s + (r.support ?? 0), 0);
  })();

  // ── Client-side generators (everything currently on the page) ───────────────
  const exportFullDataJson = () => {
    const payload = {
      report: 'Topology-Aware Multi-Level Protection Framework — Results & Discussion',
      dataset: cmp?.dataset ?? 'CICIoT2023',
      split_mode: cmp?.split_mode ?? 'train/val/test',
      generated_at: new Date().toISOString(),
      summary: {
        best_model: cmp?.best_model ?? null,
        best_macro_f1: cmp?.best_macro_f1 ?? null,
        best_adr: cmp?.best_adr ?? null,
        best_accuracy: cmp?.best_accuracy ?? null,
        num_models: numModels, num_classes: numClasses,
        num_features: numFeats, test_samples: testSamples,
      },
      model_comparison: cmp,
      per_class_metrics: pc,
      latency: lat,
      feature_importance: feat,
    };
    downloadBlob('results_full_data.json',
      new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' }));
  };

  const exportLatencyCsv = () => {
    if (!lat?.latency?.length) { alert('Latency data not loaded yet.'); return; }
    downloadBlob('latency_report_ciciot2023.csv',
      csvBlob(lat.latency as unknown as Record<string, unknown>[]));
  };

  const exportFeatureCsv = () => {
    if (!feat?.models?.length) { alert('Feature-importance data not loaded yet.'); return; }
    const rows = feat.models.flatMap(m =>
      m.top20.map(f => ({
        model: m.model, display_name: m.display_name,
        rank: f.rank, feature: f.name, importance: f.importance, pct: f.pct,
      }))
    );
    downloadBlob('feature_importance_ciciot2023.csv', csvBlob(rows));
  };

  // ── Comprehensive "everything" actions ──────────────────────────────────────
  const PRIMARY = [
    {
      title: 'FULL REPORT (PDF)', icon: '🧾', color: '#7c3aed',
      desc: 'Print or save the entire results page — all 15 sections, tables, charts and matrices — as a single PDF.',
      action: () => window.print(),
      cta: 'PRINT / SAVE PDF',
    },
    {
      title: 'ALL DATA (JSON)', icon: '🗃️', color: '#0284c7',
      desc: 'Every metric on this page in one structured JSON file: comparison, per-class, latency and feature importance.',
      action: exportFullDataJson,
      cta: 'DOWNLOAD JSON',
    },
    {
      title: 'ALL CHARTS (PNG)', icon: '📈', color: '#059669',
      desc: 'Every rendered graph and chart on the page captured into one stacked high-resolution PNG image.',
      action: exportAllChartsPng,
      cta: 'DOWNLOAD PNG',
    },
    {
      title: 'ALL CONFUSION MATRICES', icon: '🔢', color: '#dc2626',
      desc: `Download all ${ALL_CM_MODELS.length} per-model ${numClasses}×${numClasses} confusion-matrix PNGs in one click.`,
      action: downloadAllConfusionMatrices,
      cta: `DOWNLOAD ${ALL_CM_MODELS.length} PNGs`,
    },
  ];

  // ── Individual data files ───────────────────────────────────────────────────
  const FILE_EXPORTS: Array<{
    title: string; icon: string; color: string; desc: string;
    url?: string; filename: string; action?: () => void;
  }> = [
    {
      title: 'MODEL COMPARISON CSV', icon: '📊', color: '#0284c7',
      desc: `Full ${numModels}-model comparison table with all metrics (Macro-F1, ADR, balanced accuracy, accuracy, latency)`,
      url: exportUrls.modelComparisonCsv(),
      filename: 'model_comparison_ciciot2023.csv',
    },
    {
      title: 'PER-CLASS METRICS CSV', icon: '📋', color: '#059669',
      desc: `Per-class Precision / Recall / F1 / support for all ${numModels} models × ${numClasses} classes`,
      url: exportUrls.perClassCsv(),
      filename: 'per_class_metrics_ciciot2023.csv',
    },
    {
      title: 'LATENCY REPORT CSV', icon: '⏱️', color: '#0891b2',
      desc: 'Train / prediction time, per-sample latency and real-time suitability for every model.',
      action: exportLatencyCsv,
      filename: 'latency_report_ciciot2023.csv',
    },
    {
      title: 'FEATURE IMPORTANCE CSV', icon: '🧮', color: '#d97706',
      desc: 'Top-20 most important features (importance + %) for each tree-ensemble model.',
      action: exportFeatureCsv,
      filename: 'feature_importance_ciciot2023.csv',
    },
    {
      title: 'RESEARCH SUMMARY TXT', icon: '📄', color: '#7c3aed',
      desc: 'Human-readable research summary for citation and documentation',
      url: exportUrls.summaryTxt(),
      filename: 'research_summary_ciciot2023.txt',
    },
    ...ALL_CM_MODELS.map(mk => ({
      title: `CONFUSION MATRIX — ${(MN[mk] ?? mk).toUpperCase()}`, icon: '🔢', color: MC[mk] ?? '#0284c7',
      desc: `${numClasses}×${numClasses} confusion matrix PNG for ${MN[mk] ?? mk}`,
      action: () => { void downloadConfusionMatrix(mk); },
      filename: `confusion_matrix_${mk}_ciciot2023.png`,
    })),
  ];

  const cardInner = (e: { icon: string; color: string; title: string; desc: string; cta: string }) => (
    <div style={{
      background: `${e.color}08`, border: `1px solid ${e.color}20`,
      borderTop: `2px solid ${e.color}`, borderRadius: '0 0 10px 10px', padding: '14px 16px',
      cursor: 'pointer', transition: 'background .2s', height: '100%',
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
        ↓ {e.cta}
      </div>
    </div>
  );

  return (
    <section style={{ marginBottom: 52 }}>
      {/* Print styling: isolate the report, drop app chrome + interactive controls. */}
      <style>{`
        @media print {
          body * { visibility: hidden !important; }
          #report-content, #report-content * { visibility: visible !important; }
          #report-content { position: absolute !important; left: 0; top: 0; width: 100% !important; margin: 0 !important; padding: 12px !important; }
          .no-print, .no-print * { display: none !important; }
          section { break-inside: avoid; page-break-inside: avoid; }
          @page { margin: 14mm; }
        }
      `}</style>

      <SH n={15} title="EXPORT RESULTS" sub="Export everything on this page — full report, raw data, charts and individual artefacts — for publication, citation or offline analysis." />

      {cmp && (
        <div style={{
          background: 'linear-gradient(135deg,rgba(0,212,255,.06),rgba(0,255,157,.03))',
          border: '1px solid rgba(2,132,199,0.22)', borderRadius: 12, padding: '16px 20px', marginBottom: 16,
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(140px,1fr))', gap: 16,
        }}>
          {[
            { l: 'Best Model',   v: cmp.best_model ?? 'XGBoost', c: 'var(--cyan)' },
            { l: 'Macro-F1 ★',   v: pct(cmp.best_macro_f1),      c: '#059669' },
            { l: 'Best ADR',     v: pct(cmp.best_adr),           c: '#d97706' },
            { l: 'Models',       v: String(numModels),           c: 'var(--text-hi)' },
            { l: 'Test Samples', v: testSamples != null ? testSamples.toLocaleString() : '—', c: 'var(--text-hi)' },
            { l: 'Classes',      v: String(numClasses),          c: 'var(--text-hi)' },
            { l: 'Features',     v: String(numFeats),            c: 'var(--text-hi)' },
          ].map(m => (
            <div key={m.l}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '.12em', marginBottom: 4 }}>{m.l}</div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700, color: m.c }}>{m.v}</div>
            </div>
          ))}
        </div>
      )}

      {/* Comprehensive "export everything" actions */}
      <div className="no-print" style={{ marginBottom: 8, fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--cyan)', letterSpacing: '.14em' }}>
        ▸ COMPLETE EXPORTS
      </div>
      <div className="no-print" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(260px,1fr))', gap: 14, marginBottom: 22 }}>
        {PRIMARY.map(e => (
          <button key={e.title} onClick={e.action}
            style={{ all: 'unset', display: 'block', cursor: 'pointer' }}>
            {cardInner(e)}
          </button>
        ))}
      </div>

      {/* Individual data files */}
      <div className="no-print" style={{ marginBottom: 8, fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--cyan)', letterSpacing: '.14em' }}>
        ▸ INDIVIDUAL ARTEFACTS
      </div>
      <div className="no-print" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))', gap: 14 }}>
        {FILE_EXPORTS.map(e => {
          const cta = `DOWNLOAD ${e.filename.split('.').pop()?.toUpperCase()}`;
          return e.url ? (
            <a key={e.title} href={e.url} download={e.filename} style={{ textDecoration: 'none' }}>
              {cardInner({ ...e, cta })}
            </a>
          ) : (
            <button key={e.title} onClick={e.action} style={{ all: 'unset', display: 'block', cursor: 'pointer' }}>
              {cardInner({ ...e, cta })}
            </button>
          );
        })}
      </div>

      <div className="no-print" style={{ marginTop: 20, fontFamily: 'var(--font-ui)', fontSize: 11, color: 'var(--text-lo)', textAlign: 'center', lineHeight: 1.7 }}>
        CSV / TXT / matrix artefacts are served from the local Flask backend at <code style={{ color: 'var(--cyan)', fontFamily: 'var(--font-mono)' }}>localhost:5000/api/research/</code>.
        Ensure it is running: <code style={{ color: 'var(--cyan)', fontFamily: 'var(--font-mono)' }}>cd backend &amp;&amp; python api/app.py</code>.
        JSON, chart-PNG and full-report PDF are generated in your browser and need no backend.
      </div>
    </section>
  );
}
