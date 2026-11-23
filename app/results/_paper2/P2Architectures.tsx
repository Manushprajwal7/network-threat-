'use client';
import React from 'react';
import { TABLE8B_ARCHITECTURAL_BASELINES } from './data';

export function P2Architectures() {
  const DYNAMIC_SWITCHER_DATA = [
    { policy: 'Static P_opt (Recommended Rank 1)', balanced: '+985,534 OCU', flood: '+2,856,000 OCU', combined: '+1,920,767 OCU', balBlockFpr: '0.00%', balQuarFpr: '0.00%', floodBlockFpr: '100.00%' },
    { policy: 'Static P1 (Default Safe)', balanced: '+423,686 OCU', flood: '+1,149,600 OCU', combined: '+786,643 OCU', balBlockFpr: '0.00%', balQuarFpr: '29.90%', floodBlockFpr: '0.00%' },
    { policy: 'Static P2-tier (Canonical 1-to-1)', balanced: '+963,686 OCU', flood: '+2,856,000 OCU', combined: '+1,909,843 OCU', balBlockFpr: '0.00%', balQuarFpr: '29.90%', floodBlockFpr: '100.00%' },
    { policy: 'Static P2 (Aggressive Baseline)', balanced: '+907,520 OCU', flood: '+2,856,000 OCU', combined: '+1,881,760 OCU', balBlockFpr: '29.90%', balQuarFpr: '9.86%', floodBlockFpr: '100.00%' },
    { policy: 'Dynamic Adaptive Switcher (E9)', balanced: '+963,466 OCU', flood: '+2,856,000 OCU', combined: '+1,909,733 OCU', balBlockFpr: '0.00%', balQuarFpr: '29.90%', floodBlockFpr: '100.00%' }
  ];

  return (
    <section id="p2-s6" style={{ marginBottom: 48, scrollMarginTop: 80 }}>
      {/* Section Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <span style={{
          display: 'inline-block', padding: '3px 8px', borderRadius: 4,
          background: 'rgba(2,132,199,0.12)', border: '1px solid rgba(2,132,199,0.3)',
          fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', fontWeight: 700, letterSpacing: '0.05em'
        }}>
          §P2.6
        </span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: 'var(--text-hi)', margin: 0 }}>
          Architectural Baselines &amp; Hybrid Posture Policy (P_hybrid)
        </h2>
      </div>

      <p style={{ fontFamily: 'var(--font-ui)', fontSize: 13, color: 'var(--text-mid)', lineHeight: 1.7, maxWidth: 900, marginBottom: 20 }}>
        To determine whether structured multi-stage posture escalation outperforms per-flow machine learning classifiers, Paper 2 formalizes
        an architectural tournament between: (1) Posture-only mapping (P_opt and P_2-tier), (2) Pure confidence-gated XGBoost (P_XGB),
        and (3) A unified Hybrid architecture (P_hybrid) combining macroscopic entity posture with a microscopic flow-level benign veto.
      </p>

      {/* Grid: Architectural Baselines Table + Pseudocode */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 20, marginBottom: 24 }}>
        {/* Table 8B: Architectural Baselines */}
        <div style={{
          background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden',
          boxShadow: '0 1px 4px rgba(0,0,0,0.05)'
        }}>
          <div style={{
            padding: '12px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
          }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#334155' }}>
              TABLE 8B: DECISION ARCHITECTURE PARADIGM COMPARISON
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#0284c7', background: 'rgba(2,132,199,0.1)', padding: '2px 8px', borderRadius: 4 }}>
              50-RUN MULTI-SEED
            </span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11, textAlign: 'left' }}>
              <thead>
                <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Architecture</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600, color: '#059669' }}>Balanced Mean</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600, color: '#0284c7' }}>Flood Mean</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600, color: '#7c3aed' }}>50-Run Mean</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Block FPR</th>
                </tr>
              </thead>
              <tbody>
                {TABLE8B_ARCHITECTURAL_BASELINES.map((row, idx) => (
                  <tr key={idx} style={{
                    borderBottom: '1px solid #e2e8f0',
                    background: row.architecture.includes('hybrid') ? 'rgba(2,132,199,0.04)' : idx % 2 === 0 ? '#ffffff' : '#f8fafc'
                  }}>
                    <td style={{ padding: '8px 10px', fontWeight: 600, color: '#1e293b' }}>{row.architecture}</td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#059669' }}>{row.balancedMeanNet}</td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#0284c7' }}>{row.floodMeanNet}</td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#7c3aed' }}>{row.overallMeanNet}</td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: row.balancedBlockFpr === '9.46%' ? '#dc2626' : '#059669', fontWeight: 600 }}>
                      {row.balancedBlockFpr}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pseudocode & Proof Card */}
        <div style={{
          background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 18px',
          boxShadow: '0 1px 4px rgba(0,0,0,0.05)'
        }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', letterSpacing: '0.08em', marginBottom: 8, fontWeight: 700 }}>
            ALGORITHM: RUNTIME BENIGN VETO (ZERO LEAKAGE PROOF)
          </div>
          <div style={{
            fontFamily: 'var(--font-mono)', fontSize: 11, color: '#1e293b', background: '#f8fafc',
            padding: '12px 14px', borderRadius: 6, border: '1px solid #e2e8f0', lineHeight: 1.5, marginBottom: 10
          }}>
            <strong>function</strong> EVALUATE_HYBRID(x, entity_posture):<br />
            &nbsp;&nbsp;a_posture &larr; MAP(entity_posture)<br />
            &nbsp;&nbsp;<strong>if</strong> a_posture == Block <strong>and</strong> entity_posture == L4:<br />
            &nbsp;&nbsp;&nbsp;&nbsp;P_benign &larr; P(y = Benign | x; M_XGB)<br />
            &nbsp;&nbsp;&nbsp;&nbsp;s_anom &nbsp;&larr; S_anom(x; M_IF)<br />
            &nbsp;&nbsp;&nbsp;&nbsp;<strong>if</strong> P_benign &ge; 0.90 <strong>and</strong> s_anom &lt; 0.50:<br />
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<strong>return</strong> Restrict &nbsp;&nbsp;<em>// Benign Veto Applied</em><br />
            &nbsp;&nbsp;<strong>return</strong> a_posture
          </div>
          <p style={{ fontSize: 11, color: '#475569', lineHeight: 1.5, margin: 0 }}>
            <strong>Formal Leakage Proof:</strong> The veto condition relies exclusively on inference-time model probabilities
            P(y = Benign | x) and continuous anomaly score s(x).
            Zero ground-truth test labels y are accessed during runtime routing.
          </p>
        </div>
      </div>

      {/* Table 11: Dynamic Adaptive Switcher */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden',
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)', marginBottom: 20
      }}>
        <div style={{
          padding: '12px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#334155' }}>
            TABLE 11: DYNAMIC ADAPTIVE REGIME SWITCHER BENCHMARK (EXPERIMENT E9)
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#059669', background: 'rgba(5,150,105,0.1)', padding: '2px 8px', borderRadius: 4 }}>
            REAL-TIME REGIME DETECTION
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                <th style={{ padding: '8px 12px', fontWeight: 600 }}>Policy Framework</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, color: '#059669' }}>Balanced Net (OCU)</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, color: '#0284c7' }}>Flood Net (OCU)</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, color: '#7c3aed' }}>Combined Net (OCU)</th>
                <th style={{ padding: '8px 12px', fontWeight: 600 }}>Balanced Block FPR</th>
                <th style={{ padding: '8px 12px', fontWeight: 600 }}>Balanced Quar. FPR</th>
              </tr>
            </thead>
            <tbody>
              {DYNAMIC_SWITCHER_DATA.map((row, idx) => (
                <tr key={idx} style={{
                  borderBottom: '1px solid #e2e8f0',
                  background: row.policy.includes('Dynamic') ? 'rgba(5,150,105,0.04)' : idx % 2 === 0 ? '#ffffff' : '#f8fafc'
                }}>
                  <td style={{ padding: '8px 12px', fontWeight: 600, color: '#1e293b' }}>{row.policy}</td>
                  <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: '#059669' }}>{row.balanced}</td>
                  <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: '#0284c7' }}>{row.flood}</td>
                  <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#7c3aed' }}>{row.combined}</td>
                  <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: row.balBlockFpr === '0.00%' ? '#059669' : '#dc2626', fontWeight: 600 }}>
                    {row.balBlockFpr}
                  </td>
                  <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: '#64748b' }}>{row.balQuarFpr}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
