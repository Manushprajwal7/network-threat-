'use client';
import { useEffect, useRef, useState } from 'react';
import {
  getResearchComparison, getResearchPerClass, getResearchLatency,
  getResearchConfusionMatrix, getResearchFeatureImportance,
  researchExportUrls,
  type ResearchComparison, type ResearchPerClass, type ResearchLatency,
  type ResearchConfusionMatrix, type FeatureImportance,
} from '../../lib/api';
import { MODEL_KEYS } from './_sections/utils';
import { S1Executive, S2Dataset, S3Setup } from './_sections/s1s3';
import { S4ModelComparison, S5Performance } from './_sections/s4s5';
import { S6PerClass, S7AttackDetection, S8UnknownThreats } from './_sections/s6s8';
import { S9Trust, S10SecurityDecision, S11Latency } from './_sections/s9s11';
import { S12ConfusionMatrix, S13Findings, S14Contributions, S15Export } from './_sections/s12s15';

const NAV = [
  { n: 1, label: 'Executive Summary' },
  { n: 2, label: 'Dataset Analysis' },
  { n: 3, label: 'Experimental Setup' },
  { n: 4, label: 'Model Comparison' },
  { n: 5, label: 'Performance Analysis' },
  { n: 6, label: 'Per-Class Analysis' },
  { n: 7, label: 'Attack Detection' },
  { n: 8, label: 'Unknown Threats' },
  { n: 9, label: 'Trust Management' },
  { n: 10, label: 'Security Decisions' },
  { n: 11, label: 'Latency Analysis' },
  { n: 12, label: 'Confusion Matrix' },
  { n: 13, label: 'Research Findings' },
  { n: 14, label: 'Key Contributions' },
  { n: 15, label: 'Export Results' },
];

export default function ResultsPage() {
  const [cmp,  setCmp]  = useState<ResearchComparison | null>(null);
  const [pc,   setPc]   = useState<ResearchPerClass | null>(null);
  const [lat,  setLat]  = useState<ResearchLatency | null>(null);
  const [feat, setFeat] = useState<FeatureImportance | null>(null);
  const [busy, setBusy] = useState(true);

  const [mxTab,  setMxTab]  = useState(0);
  const [mxData, setMxData] = useState<Record<string, ResearchConfusionMatrix | null>>({});
  const [mxBusy, setMxBusy] = useState(false);
  const mxFetched = useRef<Set<string>>(new Set());

  useEffect(() => {
    setBusy(true);
    Promise.allSettled([
      getResearchComparison(),
      getResearchPerClass(),
      getResearchLatency(),
      getResearchFeatureImportance(),
    ]).then(([r1, r2, r3, r4]) => {
      if (r1.status === 'fulfilled') setCmp(r1.value);
      if (r2.status === 'fulfilled') setPc(r2.value);
      if (r3.status === 'fulfilled') setLat(r3.value);
      if (r4.status === 'fulfilled') setFeat(r4.value);
      setBusy(false);
    });
  }, []);

  useEffect(() => {
    const mdlKey = MODEL_KEYS[mxTab];
    if (!mdlKey || mxFetched.current.has(mdlKey)) return;
    mxFetched.current.add(mdlKey);
    setMxBusy(true);
    getResearchConfusionMatrix(mdlKey)
      .then(data => setMxData(prev => ({ ...prev, [mdlKey]: data })))
      .catch(() => setMxData(prev => ({ ...prev, [mdlKey]: null })))
      .finally(() => setMxBusy(false));
  }, [mxTab]);

  return (
    <div style={{ display: 'flex', gap: 0, maxWidth: '100%' }}>
      <aside className="no-print" style={{
        position: 'sticky', top: 0, height: '100vh', overflowY: 'auto',
        width: 200, flexShrink: 0, padding: '24px 0',
        background: '#f8fafc', borderRight: '1px solid #e2e8f0',
      }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: '#0284c7', letterSpacing: '.14em', padding: '0 16px 12px' }}>SECTIONS</div>
        {NAV.map(s => (
          <a key={s.n} href={`#s${s.n}`} style={{
            display: 'block', padding: '6px 16px',
            fontFamily: 'var(--font-ui)', fontSize: 11, color: '#64748b',
            textDecoration: 'none', lineHeight: 1.4,
          }}
            onMouseEnter={e => (e.currentTarget.style.color = '#0284c7')}
            onMouseLeave={e => (e.currentTarget.style.color = '#64748b')}
          >
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: '#0284c7', marginRight: 6 }}>§{s.n}</span>
            {s.label}
          </a>
        ))}
      </aside>

      <main id="report-content" style={{ flex: 1, minWidth: 0, padding: '32px 28px', overflowX: 'hidden' }}>
        <div style={{ marginBottom: 36 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--cyan)', letterSpacing: '.18em', marginBottom: 8 }}>
            RESULTS &amp; DISCUSSION — CICIoT2023 — TRAIN/VAL/TEST SPLIT
          </div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 700, color: 'var(--text-hi)', margin: '0 0 8px', lineHeight: 1.2 }}>
            Topology-Aware Multi-Level Protection Framework
          </h1>
          <p style={{ fontFamily: 'var(--font-ui)', fontSize: 13, color: 'var(--text-mid)', margin: 0, maxWidth: 680, lineHeight: 1.7 }}>
            Comprehensive publication-grade evaluation of seven models (XGBoost, Random Forest, Decision Tree and
            Naive Bayes / Logistic Regression / KNN / SVM baselines) on the CICIoT2023 benchmark. Primary metric:
            Macro-F1. Accuracy metrics above 95% are flagged for interpretation caution.
          </p>
        </div>

        <S1Executive cmp={cmp} />
        <S2Dataset pc={pc} />
        <S3Setup />
        <S4ModelComparison cmp={cmp} pc={pc} lat={lat} feat={feat} busy={busy} />
        <S5Performance cmp={cmp} lat={lat} busy={busy} />
        <S6PerClass pc={pc} busy={busy} />
        <S7AttackDetection pc={pc} cmp={cmp} busy={busy} />
        <S8UnknownThreats />
        <S9Trust />
        <S10SecurityDecision />
        <S11Latency lat={lat} busy={busy} />
        <S12ConfusionMatrix mxData={mxData} mxTab={mxTab} setMxTab={setMxTab} mxBusy={mxBusy} />
        <S13Findings />
        <S14Contributions />
        <S15Export exportUrls={researchExportUrls} cmp={cmp} pc={pc} lat={lat} feat={feat} />
      </main>
    </div>
  );
}
