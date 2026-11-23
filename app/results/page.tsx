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
import { Paper2View } from './_paper2/Paper2View';

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
  const [activeTab, setActiveTab] = useState<'paper1' | 'paper2'>('paper2');

  const [cmp,  setCmp]  = useState<ResearchComparison | null>(null);
  const [pc,   setPc]   = useState<ResearchPerClass | null>(null);
  const [lat,  setLat]  = useState<ResearchLatency | null>(null);
  const [feat, setFeat] = useState<FeatureImportance | null>(null);
  const [busy, setBusy] = useState(true);

  const [mxTab,  setMxTab]  = useState(0);
  const [mxData, setMxData] = useState<Record<string, ResearchConfusionMatrix | null>>({});
  const [mxBusy, setMxBusy] = useState(false);
  const mxFetched = useRef<Set<string>>(new Set());

  // URL query parameter synchronization
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get('tab') || params.get('paper');
      if (tabParam === '1' || tabParam === 'paper1') {
        setActiveTab('paper1');
      } else if (tabParam === '2' || tabParam === 'paper2') {
        setActiveTab('paper2');
      }
    }
  }, []);

  const switchTab = (tab: 'paper1' | 'paper2') => {
    setActiveTab(tab);
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      url.searchParams.set('tab', tab);
      window.history.replaceState({}, '', url.toString());
    }
  };

  useEffect(() => {
    if (activeTab !== 'paper1') return;
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
  }, [activeTab]);

  useEffect(() => {
    if (activeTab !== 'paper1') return;
    const mdlKey = MODEL_KEYS[mxTab];
    if (!mdlKey || mxFetched.current.has(mdlKey)) return;
    mxFetched.current.add(mdlKey);
    setMxBusy(true);
    getResearchConfusionMatrix(mdlKey)
      .then(data => setMxData(prev => ({ ...prev, [mdlKey]: data })))
      .catch(() => setMxData(prev => ({ ...prev, [mdlKey]: null })))
      .finally(() => setMxBusy(false));
  }, [mxTab, activeTab]);

  return (
    <div style={{ maxWidth: '100%', minHeight: '100%' }}>
      {/* Top Paper Selector Tab Bar */}
      <div className="no-print" style={{
        background: '#ffffff',
        borderBottom: '1px solid #e2e8f0',
        padding: '10px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 12,
        boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
        marginBottom: 8,
        borderRadius: 8
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: 10, color: '#64748b',
            letterSpacing: '.12em', fontWeight: 700
          }}>
            MANUSCRIPT:
          </span>

          {/* Paper 2 Tab Button */}
          <button
            onClick={() => switchTab('paper2')}
            style={{
              padding: '8px 18px',
              borderRadius: 6,
              fontFamily: 'var(--font-ui)',
              fontSize: 12,
              fontWeight: activeTab === 'paper2' ? 700 : 500,
              cursor: 'pointer',
              border: activeTab === 'paper2' ? '1px solid #0284c7' : '1px solid #cbd5e1',
              background: activeTab === 'paper2' ? '#0284c7' : '#f8fafc',
              color: activeTab === 'paper2' ? '#ffffff' : '#334155',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              boxShadow: activeTab === 'paper2' ? '0 2px 4px rgba(2,132,199,0.2)' : 'none',
              transition: 'all 0.15s ease'
            }}
          >
            <span style={{
              background: activeTab === 'paper2' ? 'rgba(255,255,255,0.25)' : 'rgba(2,132,199,0.1)',
              color: activeTab === 'paper2' ? '#ffffff' : '#0284c7',
              padding: '2px 6px',
              borderRadius: 4,
              fontSize: 10,
              fontFamily: 'var(--font-mono)',
              fontWeight: 700
            }}>
              ★ RECONCILED
            </span>
            Paper 2 (IEEE IoTJ / CS 2026) — Corrected Dynamic Trust &amp; Adaptive Protection
          </button>

          {/* Paper 1 Tab Button */}
          <button
            onClick={() => switchTab('paper1')}
            style={{
              padding: '8px 18px',
              borderRadius: 6,
              fontFamily: 'var(--font-ui)',
              fontSize: 12,
              fontWeight: activeTab === 'paper1' ? 700 : 500,
              cursor: 'pointer',
              border: activeTab === 'paper1' ? '1px solid #475569' : '1px solid #cbd5e1',
              background: activeTab === 'paper1' ? '#334155' : '#f8fafc',
              color: activeTab === 'paper1' ? '#ffffff' : '#475569',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              boxShadow: activeTab === 'paper1' ? '0 2px 4px rgba(51,65,85,0.2)' : 'none',
              transition: 'all 0.15s ease'
            }}
          >
            <span style={{
              background: activeTab === 'paper1' ? 'rgba(255,255,255,0.2)' : 'rgba(71,85,105,0.1)',
              color: activeTab === 'paper1' ? '#ffffff' : '#475569',
              padding: '2px 6px',
              borderRadius: 4,
              fontSize: 10,
              fontFamily: 'var(--font-mono)'
            }}>
              PUBLISHED
            </span>
            Paper 1 (MDPI JCP 2026) — Multi-Level Protection Framework
          </button>
        </div>

        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#64748b' }}>
          {activeTab === 'paper2' ? (
            <span style={{ color: '#059669', fontWeight: 600 }}>● Active: Paper 2 Reconciled Suite</span>
          ) : (
            <span>● Active: Paper 1 Published Report</span>
          )}
        </div>
      </div>

      {/* Render Selected View */}
      {activeTab === 'paper2' ? (
        <Paper2View />
      ) : (
        <div style={{ display: 'flex', gap: 0, maxWidth: '100%' }}>
          <aside className="no-print" style={{
            position: 'sticky', top: 56, height: 'calc(100vh - 56px)', overflowY: 'auto',
            width: 200, flexShrink: 0, padding: '24px 0',
            background: '#f8fafc', borderRight: '1px solid #e2e8f0',
          }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: '#0284c7', letterSpacing: '.14em', padding: '0 16px 12px' }}>
              SECTIONS (PAPER 1)
            </div>
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
                Topology-Aware Multi-Level Protection Framework (Paper 1)
              </h1>
              <p style={{ fontFamily: 'var(--font-ui)', fontSize: 13, color: 'var(--text-mid)', margin: 0, maxWidth: 680, lineHeight: 1.7 }}>
                Published evaluation of seven models (XGBoost, Random Forest, Decision Tree and
                Naive Bayes / Logistic Regression / KNN / SVM baselines) on the CICIoT2023 benchmark in MDPI <em>Journal of Cybersecurity and Privacy</em> (Oct 2026).
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
      )}
    </div>
  );
}
