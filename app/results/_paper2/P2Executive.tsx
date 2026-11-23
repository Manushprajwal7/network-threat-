'use client';
import React, { useState } from 'react';
import { TABLE1_PAPER_COMPARISON, AUDIT_38_ISSUES } from './data';

export function P2Executive() {
  const [selectedCategory, setSelectedCategory] = useState<'All' | 'Critical' | 'Methodology' | 'Architecture' | 'Publication'>('All');
  const [searchAudit, setSearchAudit] = useState('');
  const [expandedIssue, setExpandedIssue] = useState<number | null>(null);

  const filteredAudit = AUDIT_38_ISSUES.filter(issue => {
    const matchesCat = selectedCategory === 'All' || issue.category === selectedCategory;
    const matchesSearch = !searchAudit ||
      issue.critique.toLowerCase().includes(searchAudit.toLowerCase()) ||
      issue.rootCause.toLowerCase().includes(searchAudit.toLowerCase()) ||
      issue.resolution.toLowerCase().includes(searchAudit.toLowerCase()) ||
      issue.id.toString() === searchAudit;
    return matchesCat && matchesSearch;
  });

  const getCategoryBadgeStyle = (cat: string) => {
    switch (cat) {
      case 'Critical':
        return { bg: 'rgba(220,38,38,0.1)', color: '#dc2626', border: '1px solid rgba(220,38,38,0.3)' };
      case 'Methodology':
        return { bg: 'rgba(217,119,6,0.1)', color: '#d97706', border: '1px solid rgba(217,119,6,0.3)' };
      case 'Architecture':
        return { bg: 'rgba(124,58,237,0.1)', color: '#7c3aed', border: '1px solid rgba(124,58,237,0.3)' };
      case 'Publication':
        return { bg: 'rgba(2,132,199,0.1)', color: '#0284c7', border: '1px solid rgba(2,132,199,0.3)' };
      default:
        return { bg: 'rgba(100,116,139,0.1)', color: '#64748b', border: '1px solid rgba(100,116,139,0.3)' };
    }
  };

  return (
    <section id="p2-s1" style={{ marginBottom: 48, scrollMarginTop: 80 }}>
      {/* Section Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <span style={{
          display: 'inline-block', padding: '3px 8px', borderRadius: 4,
          background: 'rgba(2,132,199,0.12)', border: '1px solid rgba(2,132,199,0.3)',
          fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', fontWeight: 700, letterSpacing: '0.05em'
        }}>
          §P2.1
        </span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: 'var(--text-hi)', margin: 0 }}>
          Executive Summary &amp; Comprehensive Audit Reconciliation
        </h2>
      </div>

      <p style={{ fontFamily: 'var(--font-ui)', fontSize: 13, color: 'var(--text-mid)', lineHeight: 1.7, maxWidth: 900, marginBottom: 24 }}>
        Manuscript 2 (<strong style={{ color: 'var(--text-hi)' }}>IEEE Internet of Things Journal / Computers &amp; Security</strong>) presents
        the complete audit reconciliation of the published baseline framework (MDPI <em>Journal of Cybersecurity and Privacy</em>, 2026).
        Following an exhaustive 38-issue formal peer-review audit, every single experimental and architectural failure—including
        a 97.5% attack-contaminated Isolation Forest, a frozen trust engine, a catastrophic action precision inversion in <em>Restrict</em>, and
        unmodeled economic losses—was systematically resolved with 100% reproducible clean-room benchmarks.
      </p>

      {/* KPI Stat Cards Grid */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 14, marginBottom: 28
      }}>
        <div style={{
          background: 'rgba(255,255,255,0.7)', backdropFilter: 'blur(8px)',
          border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 18px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.04)'
        }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#64748b', letterSpacing: '0.1em', marginBottom: 6 }}>
            ANOMALY DETECTION AUC
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 700, color: '#059669' }}>0.9523</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#dc2626', textDecoration: 'line-through' }}>0.0084</span>
          </div>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#059669', marginTop: 4, fontWeight: 600 }}>
            +0.9439 Δ (KS D = 0.8659, p &lt; 10⁻¹⁵)
          </div>
        </div>

        <div style={{
          background: 'rgba(255,255,255,0.7)', backdropFilter: 'blur(8px)',
          border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 18px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.04)'
        }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#64748b', letterSpacing: '0.1em', marginBottom: 6 }}>
            ADTM TRUST ENGINE AUC
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 700, color: '#0284c7' }}>0.9858</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#dc2626', textDecoration: 'line-through' }}>0.0441</span>
          </div>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#0284c7', marginTop: 4, fontWeight: 600 }}>
            Neutral Prior T₀=100, Hard Reset T=10
          </div>
        </div>

        <div style={{
          background: 'rgba(255,255,255,0.7)', backdropFilter: 'blur(8px)',
          border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 18px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.04)'
        }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#64748b', letterSpacing: '0.1em', marginBottom: 6 }}>
            RESTRICT ATTACK PURITY
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 700, color: '#7c3aed' }}>57.42%</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#dc2626', textDecoration: 'line-through' }}>1.74%</span>
          </div>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#7c3aed', marginTop: 4, fontWeight: 600 }}>
            33× Gain (Precision Inversion Fixed)
          </div>
        </div>

        <div style={{
          background: 'rgba(255,255,255,0.7)', backdropFilter: 'blur(8px)',
          border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 18px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.04)'
        }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#64748b', letterSpacing: '0.1em', marginBottom: 6 }}>
            OPTIMAL NET BENEFIT (OCU)
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 700, color: '#ea580c' }}>+1.44M</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#64748b' }}>test OCU</span>
          </div>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#ea580c', marginTop: 4, fontWeight: 600 }}>
            P_opt Rank 1 / P2-tier Rank 9 (2.48×)
          </div>
        </div>
      </div>

      {/* Table 1: Comprehensive Comparison */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden',
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)', marginBottom: 24
      }}>
        <div style={{
          padding: '12px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#334155' }}>
            TABLE 1: FIVE-DIMENSIONAL FRAMEWORK RECONCILIATION (PAPER 1 vs PAPER 2)
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#0284c7', background: 'rgba(2,132,199,0.1)', padding: '2px 8px', borderRadius: 4 }}>
            PEER-REVIEW VERIFIED
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                <th style={{ padding: '10px 14px', fontWeight: 600, width: '22%' }}>Analytical Dimension</th>
                <th style={{ padding: '10px 14px', fontWeight: 600, width: '33%', color: '#dc2626' }}>Base Paper [1] (MDPI JCP 2026)</th>
                <th style={{ padding: '10px 14px', fontWeight: 600, width: '33%', color: '#059669' }}>Proposed Paper 2 (IEEE IoTJ / CS)</th>
                <th style={{ padding: '10px 14px', fontWeight: 600, width: '12%' }}>Delta / Verification</th>
              </tr>
            </thead>
            <tbody>
              {TABLE1_PAPER_COMPARISON.map((row, idx) => (
                <tr key={idx} style={{
                  borderBottom: '1px solid #e2e8f0',
                  background: idx % 2 === 0 ? '#ffffff' : '#f8fafc'
                }}>
                  <td style={{ padding: '12px 14px', fontWeight: 600, color: '#1e293b' }}>
                    {row.dimension}
                  </td>
                  <td style={{ padding: '12px 14px', color: '#64748b', lineHeight: 1.5 }}>
                    {row.paper1}
                  </td>
                  <td style={{ padding: '12px 14px', color: '#1e293b', lineHeight: 1.5 }}>
                    {row.paper2}
                  </td>
                  <td style={{ padding: '12px 14px', fontFamily: 'var(--font-mono)', fontSize: 11, color: '#0284c7', fontWeight: 600 }}>
                    {row.delta}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Interactive 38-Issue Peer-Review Audit Matrix */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10,
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)', overflow: 'hidden', marginBottom: 24
      }}>
        <div style={{
          padding: '14px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#1e293b' }}>
                FORMAL 38-ISSUE PEER-REVIEW AUDIT &amp; REMEDIATION MATRIX
              </span>
              <span style={{
                fontFamily: 'var(--font-mono)', fontSize: 9, fontWeight: 700,
                color: '#059669', background: 'rgba(5,150,105,0.12)', border: '1px solid rgba(5,150,105,0.3)',
                padding: '2px 8px', borderRadius: 12
              }}>
                38 / 38 RESOLVED (100%)
              </span>
            </div>
            <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#64748b', marginTop: 3 }}>
              Every reviewer critique, underlying root cause, technical remedy, and mathematical verification.
            </div>
          </div>

          <input
            type="text"
            placeholder="Search critique, root cause, or remedy..."
            value={searchAudit}
            onChange={(e) => setSearchAudit(e.target.value)}
            style={{
              padding: '6px 12px', borderRadius: 6, border: '1px solid #cbd5e1',
              fontFamily: 'var(--font-ui)', fontSize: 12, width: 260
            }}
          />
        </div>

        {/* Category Filter Pills */}
        <div style={{
          padding: '10px 18px', background: '#ffffff', borderBottom: '1px solid #f1f5f9',
          display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center'
        }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#64748b', marginRight: 4 }}>
            FILTER CATEGORY:
          </span>
          {(['All', 'Critical', 'Methodology', 'Architecture', 'Publication'] as const).map(cat => {
            const count = cat === 'All' ? AUDIT_38_ISSUES.length : AUDIT_38_ISSUES.filter(i => i.category === cat).length;
            const isSelected = selectedCategory === cat;
            return (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                style={{
                  padding: '4px 10px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                  cursor: 'pointer', transition: 'all 0.15s ease',
                  background: isSelected ? '#0284c7' : '#f1f5f9',
                  color: isSelected ? '#ffffff' : '#475569',
                  border: isSelected ? '1px solid #0284c7' : '1px solid #e2e8f0'
                }}
              >
                {cat} ({count})
              </button>
            );
          })}
        </div>

        {/* Audit Issue Rows */}
        <div style={{ maxHeight: 520, overflowY: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569', position: 'sticky', top: 0, zIndex: 1 }}>
                <th style={{ padding: '8px 12px', fontWeight: 600, width: '60px' }}>Issue</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, width: '110px' }}>Category</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, width: '28%' }}>Reviewer Critique</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, width: '26%' }}>Root Cause in Paper [1]</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, width: '30%' }}>Technical Remedy in Paper 2</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, width: '90px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredAudit.map((issue) => {
                const catStyle = getCategoryBadgeStyle(issue.category);
                const isExpanded = expandedIssue === issue.id;
                return (
                  <tr
                    key={issue.id}
                    onClick={() => setExpandedIssue(isExpanded ? null : issue.id)}
                    style={{
                      borderBottom: '1px solid #f1f5f9',
                      background: isExpanded ? 'rgba(2,132,199,0.03)' : '#ffffff',
                      cursor: 'pointer',
                      transition: 'background 0.1s ease'
                    }}
                  >
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#0284c7' }}>
                      #{issue.id}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <span style={{
                        padding: '2px 7px', borderRadius: 4, fontSize: 10, fontWeight: 700,
                        background: catStyle.bg, color: catStyle.color, border: catStyle.border,
                        display: 'inline-block'
                      }}>
                        {issue.category}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', fontWeight: 600, color: '#1e293b', lineHeight: 1.4 }}>
                      {issue.critique}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#64748b', fontSize: 11, lineHeight: 1.4 }}>
                      {issue.rootCause}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#0f172a', fontSize: 11, lineHeight: 1.4 }}>
                      {issue.resolution}
                    </td>
                    <td style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>
                      <span style={{
                        padding: '2px 6px', borderRadius: 4, fontSize: 10, fontWeight: 700,
                        background: 'rgba(5,150,105,0.12)', color: '#059669', border: '1px solid rgba(5,150,105,0.3)'
                      }}>
                        {issue.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
              {filteredAudit.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ padding: 24, textAlign: 'center', color: '#94a3b8', fontStyle: 'italic' }}>
                    No audit issues match current query or filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div style={{ padding: '8px 18px', background: '#f8fafc', borderTop: '1px solid #e2e8f0', fontSize: 11, color: '#64748b' }}>
          Showing {filteredAudit.length} of {AUDIT_38_ISSUES.length} audit remediation entries. Click any row to highlight.
        </div>
      </div>

      {/* Audit Highlight Banner */}
      <div style={{
        padding: '14px 18px', background: 'rgba(2,132,199,0.05)', border: '1px solid rgba(2,132,199,0.2)',
        borderRadius: 8, display: 'flex', alignItems: 'flex-start', gap: 12
      }}>
        <div style={{
          width: 24, height: 24, borderRadius: '50%', background: '#0284c7', color: '#ffffff',
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, fontSize: 12, fontWeight: 700
        }}>
          ✓
        </div>
        <div style={{ fontSize: 12, color: '#334155', lineHeight: 1.6 }}>
          <strong>Peer Review Audit Scorecard:</strong> All 38 audit issues resolved. The manuscript features an
          isolated benchmark pipeline with independent validation and held-out test splits (60,000 flows each), eliminating all forms of data leakage.
          All monetary claims have been replaced with formal Decision-Theoretic <em>Operational Cost Units (OCU)</em>.
        </div>
      </div>
    </section>
  );
}
