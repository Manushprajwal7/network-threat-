'use client';
import React, { useState, useEffect } from 'react';
import { TABLE8D_LOFO, TABLE8_PER_FAMILY, LOFO_BAR_DATA } from './data';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';

export function P2Lofo() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <section id="p2-s7" style={{ marginBottom: 48, scrollMarginTop: 80 }}>
      {/* Section Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <span style={{
          display: 'inline-block', padding: '3px 8px', borderRadius: 4,
          background: 'rgba(2,132,199,0.12)', border: '1px solid rgba(2,132,199,0.3)',
          fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', fontWeight: 700, letterSpacing: '0.05em'
        }}>
          §P2.7
        </span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: 'var(--text-hi)', margin: 0 }}>
          Leave-One-Family-Out (LOFO) Zero-Day Generalization
        </h2>
      </div>

      <p style={{ fontFamily: 'var(--font-ui)', fontSize: 13, color: 'var(--text-mid)', lineHeight: 1.7, maxWidth: 900, marginBottom: 20 }}>
        Supervised ML models (such as XGBoost) excel in closed-world benchmarks where test attacks match training distributions, but
        suffer catastrophic blindness when encountering novel zero-day attack variants. Paper 2 executes a rigorous Leave-One-Family-Out (LOFO)
        benchmark, demonstrating that unsupervised Isolation Forest anomalies and dynamic trust degradation detect and contain novel attack families
        where supervised classifiers collapse.
      </p>

      {/* Interactive LOFO Grouped Bar Chart */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '18px 20px',
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)', marginBottom: 24
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#1e293b' }}>
              INTERACTIVE LOFO ZERO-DAY ATTACK RECALL COMPARISON ACROSS HELD-OUT THREAT FAMILIES (%)
            </div>
            <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#64748b' }}>
              Supervised XGBoost collapses on unseen attack structures (Mirai: 0.33%, Web: 1.33%), while the hybrid defense delivers up to 83.1× higher recall.
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, background: 'rgba(124,58,237,0.1)', color: '#7c3aed', padding: '3px 8px', borderRadius: 4, fontWeight: 600 }}>
              Mirai Zero-Day: 83.1× Gain
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, background: 'rgba(5,150,105,0.1)', color: '#059669', padding: '3px 8px', borderRadius: 4, fontWeight: 600 }}>
              Web Attacks: 7.4× Gain
            </span>
          </div>
        </div>

        <div style={{ width: '100%', height: 290, minWidth: 0 }}>
          {mounted ? (
            <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={290}>
              <BarChart data={LOFO_BAR_DATA} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="family" tick={{ fontSize: 11, fill: '#475569' }} />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  label={{ value: 'Attack Recall (%)', angle: -90, position: 'insideLeft', fontSize: 11, fill: '#475569' }}
                />
                <Tooltip
                  contentStyle={{ background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: 8, fontSize: 11, boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
                  formatter={(value: any, name: any) => [`${value}% recall`, name]}
                />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 6 }} />
                <Bar dataKey="XGBoost" name="Supervised XGBoost Alone" fill="#dc2626" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Hybrid" name="P_hybrid Defense" fill="#0284c7" radius={[4, 4, 0, 0]} />
                <Bar dataKey="PostureOpt" name="P_opt Graduated Posture" fill="#059669" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 290, background: '#f8fafc', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', fontSize: 12 }}>
              Loading interactive LOFO benchmark...
            </div>
          )}
        </div>
      </div>

      {/* Table 8D: LOFO Results */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden',
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)', marginBottom: 24
      }}>
        <div style={{
          padding: '12px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#334155' }}>
            TABLE 8D: LEAVE-ONE-FAMILY-OUT ZERO-DAY ATTACK RECALL &amp; GENERALIZATION
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#7c3aed', background: 'rgba(124,58,237,0.1)', padding: '2px 8px', borderRadius: 4 }}>
            UNSUPERVISED ZERO-DAY DETECTION
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Held-Out Family</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Test Flows</th>
                <th style={{ padding: '8px 10px', fontWeight: 600, color: '#dc2626' }}>P_XGB Recall</th>
                <th style={{ padding: '8px 10px', fontWeight: 600, color: '#0284c7' }}>P_hybrid Recall</th>
                <th style={{ padding: '8px 10px', fontWeight: 600, color: '#059669' }}>P_opt Recall</th>
                <th style={{ padding: '8px 10px', fontWeight: 600, color: '#7c3aed' }}>P_2-tier Recall</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Generalization Advantage</th>
              </tr>
            </thead>
            <tbody>
              {TABLE8D_LOFO.map((row, idx) => (
                <tr key={idx} style={{
                  borderBottom: '1px solid #e2e8f0',
                  background: row.family === 'Mirai' || row.family === 'Web' ? 'rgba(124,58,237,0.04)' : idx % 2 === 0 ? '#ffffff' : '#f8fafc'
                }}>
                  <td style={{ padding: '8px 10px', fontWeight: 700, color: '#1e293b' }}>{row.family}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)' }}>{row.flows.toLocaleString()}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#dc2626', fontWeight: 600 }}>{row.xgbRecall}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#0284c7', fontWeight: 700 }}>{row.hybridRecall}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#059669', fontWeight: 600 }}>{row.optRecall}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#7c3aed', fontWeight: 600 }}>{row.p2TierRecall}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-ui)', fontSize: 11, fontWeight: 600, color: '#059669' }}>
                    {row.generalizationAdvantage}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Grid: Per-Family Heatmap + Per-Family Table */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 20, marginBottom: 20 }}>
        {/* Figure Card: Per-Family Heatmap */}
        <div style={{
          background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px',
          boxShadow: '0 1px 4px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column'
        }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', letterSpacing: '0.08em', marginBottom: 8, fontWeight: 700 }}>
            FIGURE O3: THREAT FAMILY TRUST DEGRADATION &amp; ROUTING HEATMAP
          </div>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 200, background: '#f8fafc', borderRadius: 8, overflow: 'hidden' }}>
            <img
              src="/paper2/figures/O3_per_family_heatmap.png"
              alt="Per-Family Heatmap"
              style={{ maxWidth: '100%', maxHeight: 220, objectFit: 'contain' }}
              onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }}
            />
          </div>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#64748b', marginTop: 8, textAlign: 'center' }}>
            Action routing across all 8 threat families under P_2-tier, showing zero Block false positives on Benign traffic.
          </div>
        </div>

        {/* Table 8: Per-Family Breakdown Table */}
        <div style={{
          background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden',
          boxShadow: '0 1px 4px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column'
        }}>
          <div style={{
            padding: '12px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
          }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#334155' }}>
              TABLE 8: PER-FAMILY ATTACK CHARACTERIZATION
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#0284c7', background: 'rgba(2,132,199,0.1)', padding: '2px 8px', borderRadius: 4 }}>
              8 FAMILIES
            </span>
          </div>

          <div style={{ flex: 1, overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11, textAlign: 'left' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Family</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Test Flows</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Share</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Mean Trust</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Dominant Action</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600, color: '#dc2626' }}>Block %</th>
                </tr>
              </thead>
              <tbody>
                {TABLE8_PER_FAMILY.map((row, idx) => (
                  <tr key={idx} style={{
                    borderBottom: '1px solid #e2e8f0',
                    background: row.family === 'Benign' ? 'rgba(5,150,105,0.04)' : idx % 2 === 0 ? '#ffffff' : '#f8fafc'
                  }}>
                    <td style={{ padding: '8px 10px', fontWeight: 600, color: '#1e293b' }}>{row.family}</td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)' }}>{row.flows.toLocaleString()}</td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#64748b' }}>{row.share}</td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: row.meanTrust >= 80 ? '#059669' : '#dc2626', fontWeight: 600 }}>
                      {row.meanTrust.toFixed(1)}
                    </td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#0284c7' }}>{row.dominantAction}</td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: row.blockPct === '0.00%' ? '#059669' : '#dc2626', fontWeight: 600 }}>
                      {row.blockPct}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
}
