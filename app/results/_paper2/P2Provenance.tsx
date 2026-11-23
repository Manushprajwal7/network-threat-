'use client';
import React, { useState } from 'react';
import { TABLE_REGIMES, SCHEMA_46_FEATURES } from './data';

export function P2Provenance() {
  const [showAllFeatures, setShowAllFeatures] = useState(false);

  const displayedFeatures = showAllFeatures ? SCHEMA_46_FEATURES : SCHEMA_46_FEATURES.slice(0, 16);

  return (
    <section id="p2-s9" style={{ marginBottom: 48, scrollMarginTop: 80 }}>
      {/* Section Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <span style={{
          display: 'inline-block', padding: '3px 8px', borderRadius: 4,
          background: 'rgba(2,132,199,0.12)', border: '1px solid rgba(2,132,199,0.3)',
          fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', fontWeight: 700, letterSpacing: '0.05em'
        }}>
          §P2.9
        </span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: 'var(--text-hi)', margin: 0 }}>
          Evaluation Regimes, 46-Feature Schema &amp; Cryptographic Ledger
        </h2>
      </div>

      <p style={{ fontFamily: 'var(--font-ui)', fontSize: 13, color: 'var(--text-mid)', lineHeight: 1.7, maxWidth: 900, marginBottom: 20 }}>
        To guarantee scientific reproducibility, Paper 2 provides complete transparency across all five evaluation regimes,
        an exact catalog of all 46 features matching the underlying schema, training data splits (5,491,971 rows),
        and cryptographic SHA-256 verification hashes.
      </p>

      {/* Table: Evaluation Regimes */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden',
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)', marginBottom: 24
      }}>
        <div style={{
          padding: '12px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#334155' }}>
            TABLE 13: FIVE DISTINCT EVALUATION REGIMES &amp; OPERATIONAL PURPOSES
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#0284c7', background: 'rgba(2,132,199,0.1)', padding: '2px 8px', borderRadius: 4 }}>
            60,000 FLOWS EACH
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Regime Identifier</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Total Flows</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Batches ($W=100$)</th>
                <th style={{ padding: '8px 10px', fontWeight: 600, color: '#dc2626' }}>Attack Base Rate</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Batch Composition Structure</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Operational Evaluation Purpose</th>
              </tr>
            </thead>
            <tbody>
              {TABLE_REGIMES.map((row, idx) => (
                <tr key={idx} style={{
                  borderBottom: '1px solid #e2e8f0',
                  background: idx % 2 === 0 ? '#ffffff' : '#f8fafc'
                }}>
                  <td style={{ padding: '8px 10px', fontWeight: 600, color: '#1e293b' }}>{row.regime}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)' }}>{row.flows}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)' }}>{row.batches}</td>
                  <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', fontWeight: 600, color: row.attackRate === '100.00%' ? '#dc2626' : '#0284c7' }}>
                    {row.attackRate}
                  </td>
                  <td style={{ padding: '8px 10px', color: '#475569' }}>{row.composition}</td>
                  <td style={{ padding: '8px 10px', color: '#64748b' }}>{row.purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Grid: 46 Features Schema + Cryptographic Checksums */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 20, marginBottom: 20 }}>
        {/* 46 Features Catalog */}
        <div style={{
          background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 18px',
          boxShadow: '0 1px 4px rgba(0,0,0,0.05)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#334155' }}>
              EXACT 46-FEATURE SCHEMA CATALOG
            </span>
            <button
              onClick={() => setShowAllFeatures(!showAllFeatures)}
              style={{
                fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', background: 'none',
                border: '1px solid rgba(2,132,199,0.3)', borderRadius: 4, padding: '2px 8px', cursor: 'pointer'
              }}
            >
              {showAllFeatures ? 'Collapse' : 'Show All (46)'}
            </button>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {displayedFeatures.map((feat, idx) => (
              <span key={idx} style={{
                fontFamily: 'var(--font-mono)', fontSize: 10, padding: '3px 7px', borderRadius: 4,
                background: '#f1f5f9', border: '1px solid #e2e8f0', color: '#334155'
              }}>
                <span style={{ color: '#0284c7', marginRight: 4 }}>{idx + 1}.</span>
                {feat}
              </span>
            ))}
          </div>
          <div style={{ marginTop: 10, fontFamily: 'var(--font-ui)', fontSize: 11, color: '#64748b' }}>
            Extracted in exact order from <code>feature_columns.pkl</code>, preserving raw dataset column names (including <code>Magnitue</code> and distinct <code>Tot size</code> vs <code>Tot sum</code>).
          </div>
        </div>

        {/* Cryptographic Ledger & Data Provenance */}
        <div style={{
          background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 18px',
          boxShadow: '0 1px 4px rgba(0,0,0,0.05)'
        }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#334155', marginBottom: 10 }}>
            CRYPTOGRAPHIC PROVENANCE &amp; CHECKSUMS
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#475569', lineHeight: 1.8 }}>
            <div><strong>Training Telemetry:</strong> 5,491,971 flows (129,538 benign = 2.36%, 5,362,433 attack = 97.64%)</div>
            <div><strong>Evaluation Split:</strong> 60,000 flows held-out test split (Seed 99)</div>
            <div><strong>Manuscript Target:</strong> IEEE IoTJ / Computers &amp; Security (24 Pages, 10,813 words)</div>
            <div><strong>Reproducibility:</strong> SHA-256 audited in <code>checksums.sha256</code></div>
          </div>
          <div style={{
            marginTop: 12, padding: '8px 12px', background: 'rgba(5,150,105,0.06)',
            border: '1px solid rgba(5,150,105,0.2)', borderRadius: 6, fontSize: 11, color: '#059669', fontWeight: 600
          }}>
            ✓ All 16 quality verification checks passed. 100% reproducible clean-room benchmark suite.
          </div>
        </div>
      </div>
    </section>
  );
}
