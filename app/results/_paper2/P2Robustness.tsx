'use client';
import React from 'react';
import { TABLE_TOPOLOGY_CONFOUND, TABLE9_COST_SENSITIVITY } from './data';

export function P2Robustness() {
  return (
    <section id="p2-s8" style={{ marginBottom: 48, scrollMarginTop: 80 }}>
      {/* Section Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <span style={{
          display: 'inline-block', padding: '3px 8px', borderRadius: 4,
          background: 'rgba(2,132,199,0.12)', border: '1px solid rgba(2,132,199,0.3)',
          fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', fontWeight: 700, letterSpacing: '0.05em'
        }}>
          §P2.8
        </span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: 'var(--text-hi)', margin: 0 }}>
          Statistical Rigor &amp; 1,000-Permutation Topology Confounder Audit
        </h2>
      </div>

      <p style={{ fontFamily: 'var(--font-ui)', fontSize: 13, color: 'var(--text-mid)', lineHeight: 1.7, maxWidth: 900, marginBottom: 20 }}>
        The peer review audit raised a critical concern (Task 2 / E2): whether the observed posture monotonicity and high L5 attack concentration
        were genuine properties of the multi-level architecture or merely an artifact of the synthetic round-robin node assignment n(b) = b mod 120.
        Paper 2 executed a full <strong style={{ color: 'var(--text-hi)' }}>1,000-permutation test</strong>, randomizing node assignments and shuffling batch order.
        Every key operational metric fell squarely within the 95% permutation confidence interval, conclusively proving architectural robustness.
      </p>

      {/* Table: 1,000 Permutations */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden',
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)', marginBottom: 24
      }}>
        <div style={{
          padding: '12px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#334155' }}>
            TABLE 12: 1,000-PERMUTATION TOPOLOGY CONFOUND TEST (OBSERVED vs PERMUTATION DISTRIBUTION)
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#059669', background: 'rgba(5,150,105,0.1)', padding: '2px 8px', borderRadius: 4 }}>
            100% ROBUST ACROSS ALL METRICS
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Evaluated Metric</th>
                <th style={{ padding: '8px 10px', fontWeight: 600, color: '#0284c7' }}>Observed Round-Robin</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Permutation Mean</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Std Dev</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>95% Confidence Interval</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Empirical p-value</th>
                <th style={{ padding: '8px 10px', fontWeight: 600, color: '#059669' }}>Robustness Status</th>
              </tr>
            </thead>
            <tbody>
              {TABLE_TOPOLOGY_CONFOUND.map((row, idx) => (
                <tr key={idx} style={{
                  borderBottom: '1px solid #e2e8f0',
                  background: idx % 2 === 0 ? '#ffffff' : '#f8fafc'
                }}>
                  <td style={{ padding: '8px 10px', fontWeight: 600, color: '#1e293b' }}>{row.metric}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#0284c7' }}>{row.observed}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)' }}>{row.permMean}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#64748b' }}>{row.permStd}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#334155' }}>{row.permCi95}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>p = {row.pValue}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#059669', fontWeight: 700 }}>{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Table 9: Cost Parameter Sensitivity Sweep */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden',
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)', marginBottom: 20
      }}>
        <div style={{
          padding: '12px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#334155' }}>
            TABLE 9: COST PARAMETER SENSITIVITY SWEEP (&lambda; &isin; [0.2, 5.0])
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#0284c7', background: 'rgba(2,132,199,0.1)', padding: '2px 8px', borderRadius: 4 }}>
            RANK INVARIANT
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                <th style={{ padding: '8px 12px', fontWeight: 600 }}>Scaling Parameter (&lambda;)</th>
                <th style={{ padding: '8px 12px', fontWeight: 600 }}>Block Benign Penalty (OCU)</th>
                <th style={{ padding: '8px 12px', fontWeight: 600 }}>P1 Net Benefit (OCU)</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, color: '#0284c7' }}>P_2-tier Net Benefit (OCU)</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, color: '#dc2626' }}>P2 Net Benefit (OCU)</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, color: '#059669' }}>P_2-tier Advantage over P1</th>
              </tr>
            </thead>
            <tbody>
              {TABLE9_COST_SENSITIVITY.map((row, idx) => (
                <tr key={idx} style={{
                  borderBottom: '1px solid #e2e8f0',
                  background: row.lambda === 1.0 ? 'rgba(2,132,199,0.05)' : idx % 2 === 0 ? '#ffffff' : '#f8fafc'
                }}>
                  <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>&lambda; = {row.lambda}</td>
                  <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)' }}>+{row.blockPenalty} OCU</td>
                  <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)' }}>{row.p1Benefit}</td>
                  <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#0284c7' }}>{row.p2TierBenefit}</td>
                  <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: '#dc2626' }}>{row.p2Benefit}</td>
                  <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#059669' }}>{row.p2TierAdvantage}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
