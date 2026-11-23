'use client';
import React from 'react';
import { TABLE_POSTURE_LEVELS, TABLE6_ACTION_PRECISION } from './data';

export function P2Posture() {
  return (
    <section id="p2-s4" style={{ marginBottom: 48, scrollMarginTop: 80 }}>
      {/* Section Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <span style={{
          display: 'inline-block', padding: '3px 8px', borderRadius: 4,
          background: 'rgba(2,132,199,0.12)', border: '1px solid rgba(2,132,199,0.3)',
          fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', fontWeight: 700, letterSpacing: '0.05em'
        }}>
          §P2.4
        </span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: 'var(--text-hi)', margin: 0 }}>
          Six-Level Posture Escalation (L0–L5) &amp; Action Attack Purity
        </h2>
      </div>

      <p style={{ fontFamily: 'var(--font-ui)', fontSize: 13, color: 'var(--text-mid)', lineHeight: 1.7, maxWidth: 900, marginBottom: 20 }}>
        The published baseline exhibited a catastrophic structural inversion in operational action precision: <em>Alert</em> traffic
        was 94.79% malicious, while the supposedly higher-severity <em>Restrict</em> tier was only <strong>1.74% malicious</strong> (dumping 16,785
        legitimate benign flows into throttle queues). Paper 2 formalizes a cohesive six-level escalation state machine (L0–L5) that
        synthesizes cumulative threat evidence S &isin; [0, 4], mean trust T_mean, and topological hub centrality R_mean,
        guaranteeing strictly non-decreasing action attack purity across all operational tiers.
      </p>

      {/* Figures Row: Architecture + Action Precision Bars */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 20, marginBottom: 24 }}>
        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px', boxShadow: '0 1px 4px rgba(0,0,0,0.05)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', letterSpacing: '0.08em', marginBottom: 8, fontWeight: 700 }}>
            FIGURE 1: SIX-LEVEL POSTURE ESCALATION ARCHITECTURE (L0 TO L5)
          </div>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 220, background: '#f8fafc', borderRadius: 8, overflow: 'hidden' }}>
            <img
              src="/paper2/figures/fig1_posture_architecture.png"
              alt="Posture Escalation Architecture"
              style={{ maxWidth: '100%', maxHeight: 240, objectFit: 'contain' }}
              onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }}
            />
          </div>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#64748b', marginTop: 8, textAlign: 'center' }}>
            Multi-stage evidence integration (S &isin; [0, 4]) mapping to discrete SDN routing policies with hysteresis latching.
          </div>
        </div>

        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px', boxShadow: '0 1px 4px rgba(0,0,0,0.05)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', letterSpacing: '0.08em', marginBottom: 8, fontWeight: 700 }}>
            FIGURE O3: ACTION ATTACK PURITY COMPARISON BARS
          </div>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 220, background: '#f8fafc', borderRadius: 8, overflow: 'hidden' }}>
            <img
              src="/paper2/figures/O3_action_precision_bars.png"
              alt="Action Attack Precision Bars"
              style={{ maxWidth: '100%', maxHeight: 240, objectFit: 'contain' }}
              onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }}
            />
          </div>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#64748b', marginTop: 8, textAlign: 'center' }}>
            Resolution of the Restrict inversion: P0 (1.74% in Restrict) vs P1 (57.42% in Restrict, 98.18% in Quarantine, 100% in Block).
          </div>
        </div>
      </div>

      {/* Table: Posture Levels Definition */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden',
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)', marginBottom: 24
      }}>
        <div style={{
          padding: '12px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#334155' }}>
            TABLE 5: SIX-LEVEL POSTURE STATE MACHINE DEFINITION (L0 THROUGH L5)
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#0284c7', background: 'rgba(2,132,199,0.1)', padding: '2px 8px', borderRadius: 4 }}>
            WINDOW W = 100 FLOWS
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                <th style={{ padding: '10px 12px', fontWeight: 600 }}>Tier</th>
                <th style={{ padding: '10px 12px', fontWeight: 600 }}>Posture Name</th>
                <th style={{ padding: '10px 12px', fontWeight: 600 }}>Evidence (S)</th>
                <th style={{ padding: '10px 12px', fontWeight: 600 }}>Trust Condition</th>
                <th style={{ padding: '10px 12px', fontWeight: 600 }}>Centrality (R)</th>
                <th style={{ padding: '10px 12px', fontWeight: 600 }}>Operational Meaning</th>
                <th style={{ padding: '10px 12px', fontWeight: 600, color: '#0284c7' }}>P_2-tier</th>
                <th style={{ padding: '10px 12px', fontWeight: 600, color: '#059669' }}>P_opt</th>
              </tr>
            </thead>
            <tbody>
              {TABLE_POSTURE_LEVELS.map((row, idx) => (
                <tr key={idx} style={{
                  borderBottom: '1px solid #e2e8f0',
                  background: idx % 2 === 0 ? '#ffffff' : '#f8fafc'
                }}>
                  <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#0284c7' }}>{row.level}</td>
                  <td style={{ padding: '10px 12px', fontWeight: 600, color: '#1e293b' }}>{row.name}</td>
                  <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: '#475569' }}>{row.evidenceCondition}</td>
                  <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: '#475569' }}>{row.trustCondition}</td>
                  <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: '#475569' }}>{row.centralityCondition}</td>
                  <td style={{ padding: '10px 12px', color: '#64748b', fontSize: 11 }}>{row.operationalMeaning}</td>
                  <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#0284c7' }}>{row.p2TierAction}</td>
                  <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#059669' }}>{row.pOptAction}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Table: Action Attack Purity Comparison */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden',
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)'
      }}>
        <div style={{
          padding: '12px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#334155' }}>
            TABLE 6: ACTION ATTACK PURITY &amp; FALSE POSITIVE AUDIT (STRATIFIED BALANCED 60,000 FLOWS)
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#059669', background: 'rgba(5,150,105,0.1)', padding: '2px 8px', borderRadius: 4 }}>
            MONOTONIC PURITY RECOVERED
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                <th style={{ padding: '10px 12px', fontWeight: 600 }}>Policy Framework</th>
                <th style={{ padding: '10px 12px', fontWeight: 600 }}>Action</th>
                <th style={{ padding: '10px 12px', fontWeight: 600 }}>Total Flows</th>
                <th style={{ padding: '10px 12px', fontWeight: 600 }}>Attack Flows</th>
                <th style={{ padding: '10px 12px', fontWeight: 600 }}>Benign Flows</th>
                <th style={{ padding: '10px 12px', fontWeight: 600, color: '#0284c7' }}>Attack Purity (%)</th>
                <th style={{ padding: '10px 12px', fontWeight: 600 }}>Benign FPR (%)</th>
                <th style={{ padding: '10px 12px', fontWeight: 600 }}>Monotonicity Status</th>
              </tr>
            </thead>
            <tbody>
              {TABLE6_ACTION_PRECISION.map((row, idx) => {
                const isInverted = row.status.includes('INVERSION');
                return (
                  <tr key={idx} style={{
                    borderBottom: '1px solid #e2e8f0',
                    background: isInverted ? 'rgba(220,38,38,0.04)' : idx % 2 === 0 ? '#ffffff' : '#f8fafc'
                  }}>
                    <td style={{ padding: '10px 12px', fontWeight: 600, color: '#1e293b' }}>{row.policy}</td>
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{row.action}</td>
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)' }}>{row.count.toLocaleString()}</td>
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: '#dc2626' }}>{row.attackFlows.toLocaleString()}</td>
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: '#059669' }}>{row.benignFlows.toLocaleString()}</td>
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: isInverted ? '#dc2626' : '#0284c7' }}>
                      {row.attackPrecision}
                    </td>
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: '#64748b' }}>{row.benignFpr}</td>
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-ui)', fontSize: 11, fontWeight: 600, color: isInverted ? '#dc2626' : '#059669' }}>
                      {row.status}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
