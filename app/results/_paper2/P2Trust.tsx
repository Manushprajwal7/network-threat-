'use client';
import React, { useState, useEffect } from 'react';
import { TRUST_TIMELINE_DATA } from './data';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine
} from 'recharts';

export function P2Trust() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  const TRUST_CONFIGS = [
    { config: "C0' (Baseline)", window: 'Attack-heavy 60k', high: '3.21%', mod: '83.69%', low: '13.10%', veryLow: '0.00%', crit: '0.00%', auc: '0.7843', l4: '0.00%', l5: '0.00%', gap: '7.79' },
    { config: "C1' (Dynamic Weights)", window: 'Attack-heavy 60k', high: '0.14%', mod: '2.50%', low: '3.83%', veryLow: '93.53%', crit: '0.00%', auc: '0.8969', l4: '0.00%', l5: '0.00%', gap: '7.79' },
    { config: "C2' (T=10 Hard Reset)", window: 'Attack-heavy 60k', high: '0.12%', mod: '1.00%', low: '3.16%', veryLow: '35.38%', crit: '60.34%', auc: '0.9468', l4: '6.67%', l5: '90.33%', gap: '21.68' },
    { config: "C3' (Mean Trust)", window: 'Attack-heavy 60k', high: '0.09%', mod: '0.18%', low: '2.50%', veryLow: '33.77%', crit: '63.46%', auc: '0.9641', l4: '6.67%', l5: '90.33%', gap: '23.75' },
    { config: "C4' (500k Stream)", window: 'Attack-heavy 500k', high: '0.06%', mod: '0.14%', low: '2.25%', veryLow: '33.84%', crit: '63.71%', auc: '0.9644', l4: '6.72%', l5: '90.96%', gap: '23.65' },
    { config: "C4' (Balanced)", window: 'Balanced Flow-Level', high: '0.09%', mod: '1.25%', low: '48.20%', veryLow: '18.15%', crit: '32.31%', auc: '0.9638', l4: '3.43%', l5: '0.00%', gap: '24.10' }
  ];

  return (
    <section id="p2-s3" style={{ marginBottom: 48, scrollMarginTop: 80 }}>
      {/* Section Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <span style={{
          display: 'inline-block', padding: '3px 8px', borderRadius: 4,
          background: 'rgba(2,132,199,0.12)', border: '1px solid rgba(2,132,199,0.3)',
          fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', fontWeight: 700, letterSpacing: '0.05em'
        }}>
          §P2.3
        </span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: 'var(--text-hi)', margin: 0 }}>
          Calibrated ADTM Behavioral Trust &amp; Anti-Freezing Dynamics
        </h2>
      </div>

      <p style={{ fontFamily: 'var(--font-ui)', fontSize: 13, color: 'var(--text-mid)', lineHeight: 1.7, maxWidth: 900, marginBottom: 20 }}>
        In Paper [1], the Adaptive Dynamic Trust Management (ADTM) engine suffered from a design freeze bug: an arbitrary 200-sample clamp locked
        trust values permanently once a threat was flagged, preventing subsequent benign recovery and trapping 99.97% of entities in the High band.
        Paper 2 implements a principled recalibration with a <strong style={{ color: 'var(--text-hi)' }}>Neutral Trust Prior (T₀ = 100.0)</strong>,
        guaranteeing zero test-time label leakage, and three targeted architectural bug repairs.
      </p>

      {/* Three Design Bug Fixes */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14, marginBottom: 24 }}>
        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 8, padding: '14px 16px', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', fontWeight: 700, marginBottom: 4 }}>BUG 1: REMOVED 200-SAMPLE CLAMP</div>
          <p style={{ fontSize: 12, color: '#475569', lineHeight: 1.5, margin: 0 }}>
            Replaced permanent trust locking with <strong>per-flow hard reset</strong>. When conf &ge; 0.95 &and; attack &and; anom &ge; 0.90, trust is set to T = 10 for that flow only; legitimate recovery begins immediately upon benign arrival.
          </p>
        </div>

        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 8, padding: '14px 16px', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#059669', fontWeight: 700, marginBottom: 4 }}>BUG 2: POPULATED CRITICAL BAND (T = 10)</div>
          <p style={{ fontSize: 12, color: '#475569', lineHeight: 1.5, margin: 0 }}>
            Set outright hard-reset target trust to <strong>T = 10.0</strong> (centering the Critical band [0, 19]). This populates Critical trust (60.3%–63.7%), resolving the published failure where 0% entered Critical.
          </p>
        </div>

        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 8, padding: '14px 16px', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#7c3aed', fontWeight: 700, marginBottom: 4 }}>BUG 3: ENTITY MEAN TRUST HIERARCHY</div>
          <p style={{ fontSize: 12, color: '#475569', lineHeight: 1.5, margin: 0 }}>
            Downstream escalation evaluates <strong>mean trust over W = 100 flows</strong> with W_cooldown = 300 hysteresis, preventing single noisy packets from triggering false posture escalations.
          </p>
        </div>
      </div>

      {/* Interactive Trust Evolution Timeline */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '18px 20px',
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)', marginBottom: 24
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#1e293b' }}>
              INTERACTIVE REAL-TIME TRUST TRAJECTORY T(t) ACROSS MULTI-PHASE TRAFFIC STREAM (600 BATCHES)
            </div>
            <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#64748b' }}>
              Observing instantaneous hard reset (T = 10.0) at attack onset (batch 181), suppression during sustained flood, and full restitution to ~99 upon benign recovery.
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, background: 'rgba(2,132,199,0.1)', color: '#0284c7', padding: '3px 8px', borderRadius: 4, fontWeight: 600 }}>
              Prior T₀ = 100.0
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, background: 'rgba(220,38,38,0.1)', color: '#dc2626', padding: '3px 8px', borderRadius: 4, fontWeight: 600 }}>
              Hard Reset T = 10.0
            </span>
          </div>
        </div>

        <div style={{ width: '100%', height: 280, minWidth: 0 }}>
          {mounted ? (
            <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={280}>
              <LineChart data={TRUST_TIMELINE_DATA} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis
                  dataKey="batch"
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  label={{ value: 'Batch Index (100 flows / batch)', position: 'insideBottom', offset: -5, fontSize: 11, fill: '#475569' }}
                />
                <YAxis
                  domain={[0, 105]}
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  label={{ value: 'Trust Score T(t)', angle: -90, position: 'insideLeft', fontSize: 11, fill: '#475569' }}
                />
                <Tooltip
                  contentStyle={{ background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: 8, fontSize: 11, boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
                  formatter={(value: any, name: any) => [`${value} / 100`, name]}
                  labelFormatter={(label, payload) => {
                    const phase = payload && payload[0] && (payload[0].payload as any).phase;
                    return `Batch ${label} — Phase: ${phase || 'Active'}`;
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 6 }} />
                <ReferenceLine y={80} stroke="#059669" strokeDasharray="3 3" label={{ value: 'High Band (T ≥ 80)', fill: '#059669', fontSize: 10, position: 'insideTopRight' }} />
                <ReferenceLine y={20} stroke="#dc2626" strokeDasharray="3 3" label={{ value: 'Critical Band (T < 20)', fill: '#dc2626', fontSize: 10, position: 'insideBottomRight' }} />
                <Line type="monotone" dataKey="Benign" stroke="#059669" strokeWidth={2.5} dot={{ r: 3 }} name="Benign Host Traffic" />
                <Line type="monotone" dataKey="DDoS" stroke="#dc2626" strokeWidth={2} dot={{ r: 3 }} name="DDoS Volumetric Target" />
                <Line type="monotone" dataKey="Mirai" stroke="#7c3aed" strokeWidth={2} strokeDasharray="4 2" dot={{ r: 3 }} name="Mirai Botnet Host" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 280, background: '#f8fafc', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', fontSize: 12 }}>
              Loading interactive trust trajectory...
            </div>
          )}
        </div>
      </div>

      {/* Visualizations Grid: Band Distribution + Trust Traces */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 20, marginBottom: 24 }}>
        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px', boxShadow: '0 1px 4px rgba(0,0,0,0.05)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', letterSpacing: '0.08em', marginBottom: 8, fontWeight: 700 }}>
            FIGURE O2.B: FIVE-BAND TRUST DISTRIBUTION RECONCILIATION
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 200, background: '#f8fafc', borderRadius: 8, overflow: 'hidden' }}>
            <img
              src="/paper2/figures/O2_B_band_distribution_comparison.png"
              alt="Trust Band Distribution"
              style={{ maxWidth: '100%', maxHeight: 220, objectFit: 'contain' }}
              onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }}
            />
          </div>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#64748b', marginTop: 8, textAlign: 'center' }}>
            Evolution across configurations C0&#39; to C4&#39;, achieving healthy dispersion into Low (48.2%) and Critical (32.3%) bands.
          </div>
        </div>

        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px', boxShadow: '0 1px 4px rgba(0,0,0,0.05)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', letterSpacing: '0.08em', marginBottom: 8, fontWeight: 700 }}>
            FIGURE 10: DYNAMIC TRUST DEGRADATION &amp; BENIGN RECOVERY TRACES
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 200, background: '#f8fafc', borderRadius: 8, overflow: 'hidden' }}>
            <img
              src="/paper2/figures/fig10_trust_traces.png"
              alt="Dynamic Trust Traces"
              style={{ maxWidth: '100%', maxHeight: 220, objectFit: 'contain' }}
              onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }}
            />
          </div>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#64748b', marginTop: 8, textAlign: 'center' }}>
            Continuous sliding-window evaluation demonstrating rapid penalty on attack onset and unconstrained benign recovery.
          </div>
        </div>
      </div>

      {/* Table O2.B6: Combined Configurations */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden',
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)'
      }}>
        <div style={{
          padding: '12px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#334155' }}>
            TABLE O2.B6: COMBINED TRUST REPAIR CONFIGURATIONS (AUC &amp; BAND COVERAGE)
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#0284c7', background: 'rgba(2,132,199,0.1)', padding: '2px 8px', borderRadius: 4 }}>
            AUDIT BENCHMARK
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Configuration</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Evaluation Window</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>High Band</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Moderate</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Low</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Very Low</th>
                <th style={{ padding: '8px 10px', fontWeight: 600, color: '#dc2626' }}>Critical</th>
                <th style={{ padding: '8px 10px', fontWeight: 600, color: '#059669' }}>Trust AUC</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>L4 Escalation</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>L5 Escalation</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Separation Gap</th>
              </tr>
            </thead>
            <tbody>
              {TRUST_CONFIGS.map((row, idx) => (
                <tr key={idx} style={{
                  borderBottom: '1px solid #e2e8f0',
                  background: row.config.includes("C4'") ? 'rgba(2,132,199,0.04)' : idx % 2 === 0 ? '#ffffff' : '#f8fafc'
                }}>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#1e293b' }}>{row.config}</td>
                  <td style={{ padding: '8px 10px', color: '#64748b' }}>{row.window}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)' }}>{row.high}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)' }}>{row.mod}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)' }}>{row.low}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)' }}>{row.veryLow}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#dc2626', fontWeight: 600 }}>{row.crit}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#059669', fontWeight: 700 }}>{row.auc}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)' }}>{row.l4}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)' }}>{row.l5}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#0284c7', fontWeight: 600 }}>+{row.gap}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
