'use client';
import React, { useState, useEffect } from 'react';
import { TABLE3_IF_COMPARISON, ANOMALY_DENSITY_DATA } from './data';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine
} from 'recharts';

export function P2Anomaly() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <section id="p2-s2" style={{ marginBottom: 48, scrollMarginTop: 80 }}>
      {/* Section Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <span style={{
          display: 'inline-block', padding: '3px 8px', borderRadius: 4,
          background: 'rgba(2,132,199,0.12)', border: '1px solid rgba(2,132,199,0.3)',
          fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', fontWeight: 700, letterSpacing: '0.05em'
        }}>
          §P2.2
        </span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: 'var(--text-hi)', margin: 0 }}>
          Isolation Forest Repair &amp; Anomaly Score Recalibration
        </h2>
      </div>

      <p style={{ fontFamily: 'var(--font-ui)', fontSize: 13, color: 'var(--text-mid)', lineHeight: 1.7, maxWidth: 900, marginBottom: 20 }}>
        The published pipeline in Paper [1] trained the Isolation Forest on uncurated telemetry (97.5% attack data due to a label string mismatch).
        Because attack flows dominated the feature space, legitimate benign communications appeared as statistical outliers, causing benign traffic
        to receive maximum anomaly scores (mean 1.0000) while attack traffic appeared nominal (mean 0.8770), inverting the detector (AUC 0.0296).
        Paper 2 retrains the ensemble strictly on clean benign baseline traffic (M=200 trees, 50,000 clean subsample), completely restoring physical anomaly separation.
      </p>

      {/* Grid: Math Formulation + Figure ROC */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 20, marginBottom: 24 }}>
        {/* Mathematical Formulation Card */}
        <div style={{
          background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '18px 20px',
          boxShadow: '0 1px 4px rgba(0,0,0,0.05)'
        }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', letterSpacing: '0.08em', marginBottom: 8, fontWeight: 700 }}>
            FORMAL MATHEMATICAL SPECIFICATION
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: '#1e293b', background: '#f8fafc', padding: '12px 14px', borderRadius: 6, border: '1px solid #e2e8f0', marginBottom: 12 }}>
            c(n) = 2H(n - 1) - 2(n - 1) / n<br />
            &nbsp;&nbsp;&nbsp;&nbsp;= 2 ln(n - 1) + 2γ - 2(n - 1) / n<br />
            &nbsp;&nbsp;&nbsp;&nbsp;= 2 ln(n - 1) + 1.1544313298 - 2(n - 1) / n
          </div>
          <p style={{ fontSize: 12, color: '#475569', lineHeight: 1.6, margin: '0 0 10px' }}>
            <strong>Euler-Mascheroni Constant Correction:</strong> Resolved Issue 5 by explicitly multiplying Euler’s constant γ by 2
            (yielding 1.1544313298), fixing the mathematical error in the historical draft.
          </p>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#334155', background: '#f1f5f9', padding: '10px 12px', borderRadius: 6 }}>
            <strong>Quantile Score Calibration:</strong><br />
            s̃(x) = clamp((−score_samples(x) − s_p5) / (s_p95 − s_p5), 0, 1)<br />
            where s_p5 = 0.4421 and s_p95 = 0.5284 fitted strictly on clean benign validation split.
          </div>
        </div>

        {/* Figure Card: ROC Comparison */}
        <div style={{
          background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px',
          boxShadow: '0 1px 4px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column'
        }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', letterSpacing: '0.08em', marginBottom: 8, fontWeight: 700 }}>
            FIGURE O2.A: ROC CURVE EMPIRICAL RECONCILIATION
          </div>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 200, background: '#f8fafc', borderRadius: 8, overflow: 'hidden' }}>
            <img
              src="/paper2/figures/O2_A_if_roc_comparison.png"
              alt="Isolation Forest ROC Comparison"
              style={{ maxWidth: '100%', maxHeight: 220, objectFit: 'contain' }}
              onError={(e) => {
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
          </div>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#64748b', marginTop: 8, textAlign: 'center' }}>
            Contaminated Baseline (Red dashed, AUC = 0.0296) vs Corrected Benign-Only Model (Blue solid, AUC = 0.9567)
          </div>
        </div>
      </div>

      {/* Interactive Recharts Density Chart */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '18px 20px',
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)', marginBottom: 24
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#1e293b' }}>
              INTERACTIVE EMPIRICAL DENSITY SEPARATION: BENIGN vs ATTACK PROBABILITY DISTRIBUTIONS
            </div>
            <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#64748b' }}>
              Clean benign training concentrates legitimate flows at low scores (mode ~0.25), while attacks strongly separate above τ_anom = 0.50 (KS D = 0.8659, p &lt; 10⁻¹⁵).
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, background: 'rgba(5,150,105,0.1)', color: '#059669', padding: '3px 8px', borderRadius: 4, fontWeight: 600 }}>
              Separation Gap Δ = +0.4869
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, background: 'rgba(2,132,199,0.1)', color: '#0284c7', padding: '3px 8px', borderRadius: 4, fontWeight: 600 }}>
              Operating Threshold τ = 0.50
            </span>
          </div>
        </div>

        <div style={{ width: '100%', height: 280, minWidth: 0 }}>
          {mounted ? (
            <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={280}>
              <AreaChart data={ANOMALY_DENSITY_DATA} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="benignGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#059669" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#059669" stopOpacity={0.0}/>
                  </linearGradient>
                  <linearGradient id="attackGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#dc2626" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#dc2626" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis
                  dataKey="score"
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  label={{ value: 'Calibrated Anomaly Score s̃(x)', position: 'insideBottom', offset: -5, fontSize: 11, fill: '#475569' }}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  label={{ value: 'Probability Density', angle: -90, position: 'insideLeft', fontSize: 11, fill: '#475569' }}
                />
                <Tooltip
                  contentStyle={{ background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: 8, fontSize: 11, boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
                  formatter={(value: any, name: any) => [`${value} density`, name === 'benign' ? 'Benign Baseline' : 'Attack Telemetry']}
                  labelFormatter={(label) => `Anomaly Score s̃ = ${label}`}
                />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 6 }} />
                <ReferenceLine x={0.50} stroke="#0284c7" strokeDasharray="4 4" label={{ value: 'Threshold τ = 0.50', fill: '#0284c7', fontSize: 10, position: 'top' }} />
                <Area type="monotone" dataKey="benign" name="Benign Traffic" stroke="#059669" strokeWidth={2} fillOpacity={1} fill="url(#benignGrad)" />
                <Area type="monotone" dataKey="attack" name="Attack Traffic" stroke="#dc2626" strokeWidth={2} fillOpacity={1} fill="url(#attackGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 280, background: '#f8fafc', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', fontSize: 12 }}>
              Loading interactive density model...
            </div>
          )}
        </div>
      </div>

      {/* Table O2.A: Quantitative Comparison */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden',
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)'
      }}>
        <div style={{
          padding: '12px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#334155' }}>
            TABLE O2.A: ISOLATION FOREST DETECTOR COMPARISON (M = 200 TREES, 50,000 SUBSAMPLE)
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#059669', background: 'rgba(5,150,105,0.1)', padding: '2px 8px', borderRadius: 4 }}>
            VERIFIED NO CONTAMINATION
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>Statistical Performance Dimension</th>
                <th style={{ padding: '10px 14px', fontWeight: 600, color: '#dc2626' }}>Contaminated Baseline (Paper [1])</th>
                <th style={{ padding: '10px 14px', fontWeight: 600, color: '#059669' }}>Corrected Clean Model (Paper 2)</th>
                <th style={{ padding: '10px 14px', fontWeight: 600 }}>Audit Verdict</th>
              </tr>
            </thead>
            <tbody>
              {TABLE3_IF_COMPARISON.map((row, idx) => (
                <tr key={idx} style={{
                  borderBottom: '1px solid #e2e8f0',
                  background: idx % 2 === 0 ? '#ffffff' : '#f8fafc'
                }}>
                  <td style={{ padding: '10px 14px', fontWeight: 600, color: '#1e293b' }}>{row.metric}</td>
                  <td style={{ padding: '10px 14px', fontFamily: 'var(--font-mono)', color: '#dc2626' }}>{row.contaminated}</td>
                  <td style={{ padding: '10px 14px', fontFamily: 'var(--font-mono)', color: '#059669', fontWeight: 600 }}>{row.corrected}</td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={{
                      padding: '2px 6px', borderRadius: 4, fontSize: 10, fontWeight: 700,
                      background: 'rgba(5,150,105,0.1)', color: '#059669', border: '1px solid rgba(5,150,105,0.3)'
                    }}>
                      {row.verdict}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
