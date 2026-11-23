'use client';
import React, { useState } from 'react';
import { EXPERIMENTS_INVENTORY_DATA } from './data';

export function P2Experiments() {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredExperiments = EXPERIMENTS_INVENTORY_DATA.filter((exp: any) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      exp['ID']?.toLowerCase().includes(q) ||
      exp['Experiment Focus']?.toLowerCase().includes(q) ||
      exp['Split / Dataset']?.toLowerCase().includes(q) ||
      exp['Key Finding / Supported Claim']?.toLowerCase().includes(q) ||
      exp['Primary Artifact']?.toLowerCase().includes(q)
    );
  });

  return (
    <section id="p2-s10" style={{ marginBottom: 48, scrollMarginTop: 80 }}>
      {/* Section Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <span style={{
          display: 'inline-block', padding: '3px 8px', borderRadius: 4,
          background: 'rgba(2,132,199,0.12)', border: '1px solid rgba(2,132,199,0.3)',
          fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', fontWeight: 700, letterSpacing: '0.05em'
        }}>
          §P2.10
        </span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: 'var(--text-hi)', margin: 0 }}>
          Complete 24-Experiment Inventory Ledger &amp; Provenance
        </h2>
      </div>

      <p style={{ fontFamily: 'var(--font-ui)', fontSize: 13, color: 'var(--text-mid)', lineHeight: 1.7, maxWidth: 900, marginBottom: 20 }}>
        To eliminate confirmation bias and guarantee uncompromising scientific reproducibility, Paper 2 documents an exhaustive
        inventory of 24 distinct experimental protocols (E1 through E24). Every numeric claim, statistical confidence bound,
        and algorithmic comparison in the manuscript maps directly to an audited execution log and primary CSV artifact.
      </p>

      {/* Ledger Container */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10,
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)', overflow: 'hidden'
      }}>
        <div style={{
          padding: '14px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#1e293b' }}>
                TABLE APP.A: EXPERIMENT INVENTORY MATRIX (E1 TO E24)
              </span>
              <span style={{
                fontFamily: 'var(--font-mono)', fontSize: 9, fontWeight: 700,
                color: '#059669', background: 'rgba(5,150,105,0.12)', border: '1px solid rgba(5,150,105,0.3)',
                padding: '2px 8px', borderRadius: 12
              }}>
                24 PROTOCOLS DOCUMENTED
              </span>
            </div>
            <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#64748b', marginTop: 3 }}>
              Search across experiment focus, dataset splits, PRNG seeds, and key findings.
            </div>
          </div>

          <input
            type="text"
            placeholder="Search experiment ID, focus, or claim..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              padding: '6px 12px', borderRadius: 6, border: '1px solid #cbd5e1',
              fontFamily: 'var(--font-ui)', fontSize: 12, width: 260
            }}
          />
        </div>

        <div style={{ overflowX: 'auto', maxHeight: 560 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569', position: 'sticky', top: 0, zIndex: 1 }}>
                <th style={{ padding: '8px 12px', fontWeight: 600, width: '55px' }}>ID</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, width: '22%' }}>Experiment Focus</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, width: '15%' }}>Seeds / PRNG</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, width: '18%' }}>Split / Dataset</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, width: '20%' }}>Primary Artifact Path</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, width: '25%' }}>Key Finding / Supported Claim</th>
              </tr>
            </thead>
            <tbody>
              {filteredExperiments.map((exp: any, idx: number) => {
                const idNum = parseInt(exp['ID']?.replace('E', '') || '0', 10);
                return (
                  <tr
                    key={idx}
                    style={{
                      borderBottom: '1px solid #f1f5f9',
                      background: idx % 2 === 0 ? '#ffffff' : '#f8fafc'
                    }}
                  >
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#0284c7' }}>
                      <span style={{
                        padding: '2px 6px', borderRadius: 4, background: 'rgba(2,132,199,0.1)',
                        border: '1px solid rgba(2,132,199,0.25)', fontSize: 10
                      }}>
                        {exp['ID']}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', fontWeight: 600, color: '#1e293b' }}>
                      {exp['Experiment Focus']}
                    </td>
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: '#64748b' }}>
                      {exp['Seeds'] || 'N/A'}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#334155' }}>
                      {exp['Split / Dataset']}
                    </td>
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7' }}>
                      {exp['Primary Artifact']}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#0f172a', lineHeight: 1.4 }}>
                      {exp['Key Finding / Supported Claim']}
                    </td>
                  </tr>
                );
              })}
              {filteredExperiments.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ padding: 24, textAlign: 'center', color: '#94a3b8', fontStyle: 'italic' }}>
                    No experiments match query.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div style={{ padding: '10px 18px', background: '#f8fafc', borderTop: '1px solid #e2e8f0', fontSize: 11, color: '#64748b' }}>
          Showing {filteredExperiments.length} of {EXPERIMENTS_INVENTORY_DATA.length} formal experimental protocols.
        </div>
      </div>
    </section>
  );
}
