'use client';
import React, { useState } from 'react';
import { P2Executive } from './P2Executive';
import { P2Anomaly } from './P2Anomaly';
import { P2Trust } from './P2Trust';
import { P2Posture } from './P2Posture';
import { P2Policies } from './P2Policies';
import { P2Architectures } from './P2Architectures';
import { P2Lofo } from './P2Lofo';
import { P2Robustness } from './P2Robustness';
import { P2Provenance } from './P2Provenance';
import { P2Experiments } from './P2Experiments';
import { P2Latency } from './P2Latency';

const P2_NAV = [
  { id: 'p2-s1', n: 'P2.1', label: 'Executive & Audit Summary' },
  { id: 'p2-s2', n: 'P2.2', label: 'Isolation Forest Repair' },
  { id: 'p2-s3', n: 'P2.3', label: 'ADTM Trust Recalibration' },
  { id: 'p2-s4', n: 'P2.4', label: 'Posture Escalation (L0–L5)' },
  { id: 'p2-s5', n: 'P2.5', label: 'Cost Model & 70 Policies' },
  { id: 'p2-s6', n: 'P2.6', label: 'Architectural Baselines' },
  { id: 'p2-s7', n: 'P2.7', label: 'LOFO Zero-Day Benchmark' },
  { id: 'p2-s8', n: 'P2.8', label: '1,000-Permutation Robustness' },
  { id: 'p2-s9', n: 'P2.9', label: 'Regimes & 46-Feature Schema' },
  { id: 'p2-s10', n: 'P2.10', label: '24-Experiment Inventory' },
  { id: 'p2-s11', n: 'P2.11', label: 'Hardware Latency & Throughput' },
];

export function Paper2View() {
  const [activeSection, setActiveSection] = useState('p2-s1');

  return (
    <div style={{ display: 'flex', gap: 0, maxWidth: '100%' }}>
      {/* Paper 2 Sub-Navigation Sidebar */}
      <aside className="no-print" style={{
        position: 'sticky', top: 56, height: 'calc(100vh - 56px)', overflowY: 'auto',
        width: 230, flexShrink: 0, padding: '24px 0',
        background: '#f8fafc', borderRight: '1px solid #e2e8f0',
      }}>
        <div style={{
          fontFamily: 'var(--font-mono)', fontSize: 9, color: '#0284c7',
          letterSpacing: '.14em', padding: '0 16px 12px', fontWeight: 700
        }}>
          MANUSCRIPT 2 SECTIONS
        </div>

        {P2_NAV.map((s) => (
          <a
            key={s.id}
            href={`#${s.id}`}
            onClick={() => setActiveSection(s.id)}
            style={{
              display: 'block', padding: '7px 16px',
              fontFamily: 'var(--font-ui)', fontSize: 11,
              color: activeSection === s.id ? '#0284c7' : '#64748b',
              fontWeight: activeSection === s.id ? 600 : 400,
              textDecoration: 'none', lineHeight: 1.4,
              borderLeft: activeSection === s.id ? '2px solid #0284c7' : '2px solid transparent',
              background: activeSection === s.id ? 'rgba(2,132,199,0.06)' : 'transparent',
              transition: 'all 0.15s ease'
            }}
            onMouseEnter={(e) => {
              if (activeSection !== s.id) (e.currentTarget.style.color = '#0284c7');
            }}
            onMouseLeave={(e) => {
              if (activeSection !== s.id) (e.currentTarget.style.color = '#64748b');
            }}
          >
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#0284c7', marginRight: 6 }}>
              §{s.n}
            </span>
            {s.label}
          </a>
        ))}

        <div style={{ padding: '20px 16px 0', borderTop: '1px solid #e2e8f0', marginTop: 20 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#64748b', marginBottom: 6 }}>
            ARTIFACTS &amp; CODE
          </div>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#334155', lineHeight: 1.5 }}>
            <span style={{ color: '#059669', fontWeight: 600 }}>✓ 100% Isolated</span><br />
            50 Multi-Seed Runs<br />
            Held-out Test (60k flows)<br />
            24 Benchmark Experiments
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div style={{ flex: 1, minWidth: 0, padding: '28px 32px', overflowX: 'hidden' }}>
        {/* Paper 2 Header Banner */}
        <div style={{
          marginBottom: 36, padding: '24px 28px', background: 'linear-gradient(135deg, rgba(2,132,199,0.06) 0%, rgba(124,58,237,0.05) 100%)',
          border: '1px solid rgba(2,132,199,0.2)', borderRadius: 12
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8, flexWrap: 'wrap' }}>
            <span style={{
              fontFamily: 'var(--font-mono)', fontSize: 9, color: '#ffffff', background: '#0284c7',
              padding: '3px 8px', borderRadius: 4, fontWeight: 700, letterSpacing: '0.08em'
            }}>
              MANUSCRIPT 2
            </span>
            <span style={{
              fontFamily: 'var(--font-mono)', fontSize: 9, color: '#7c3aed', background: 'rgba(124,58,237,0.1)',
              padding: '3px 8px', borderRadius: 4, fontWeight: 600
            }}>
              TARGET: IEEE IoTJ / COMPUTERS &amp; SECURITY
            </span>
            <span style={{
              fontFamily: 'var(--font-mono)', fontSize: 9, color: '#059669', background: 'rgba(5,150,105,0.1)',
              padding: '3px 8px', borderRadius: 4, fontWeight: 600
            }}>
              38/38 AUDIT ISSUES RESOLVED
            </span>
          </div>

          <h1 style={{
            fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 700, color: 'var(--text-hi)',
            margin: '0 0 10px', lineHeight: 1.25
          }}>
            Corrected Topology-Aware Dynamic Trust &amp; Cost-Aware Adaptive Protection Framework
          </h1>

          <p style={{
            fontFamily: 'var(--font-ui)', fontSize: 13, color: 'var(--text-mid)', margin: 0, maxWidth: 840, lineHeight: 1.7
          }}>
            Complete publication-grade experimental reconciliation of the cybersecurity framework on CICIoT2023.
            Presents clean benign-only Isolation Forest retraining (AUC 0.9523), anti-freezing ADTM behavioral trust (AUC 0.9858),
            monotonically non-decreasing action attack purity, combinatorial optimization over all 70 monotonic policies in formal Operational Cost Units (OCU),
            and empirical leave-one-family-out (LOFO) zero-day resilience.
          </p>
        </div>

        {/* Paper 2 Sections */}
        <P2Executive />
        <P2Anomaly />
        <P2Trust />
        <P2Posture />
        <P2Policies />
        <P2Architectures />
        <P2Lofo />
        <P2Robustness />
        <P2Provenance />
        <P2Experiments />
        <P2Latency />
      </div>
    </div>
  );
}
