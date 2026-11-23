'use client';
import React, { useState, useEffect, useMemo } from 'react';
import { TABLE2_COST_MATRIX, TABLE7_MASTER_POLICIES, POLICY_BAR_DATA, POLICIES_70_DATA } from './data';
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

export function P2Policies() {
  const [mounted, setMounted] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterMode, setFilterMode] = useState<'all' | 'safe' | 'top10'>('all');
  const [sortBy, setSortBy] = useState<'rank' | 'ocu' | 'blockFpr' | 'recall'>('rank');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  useEffect(() => {
    setMounted(true);
  }, []);

  // Filter & Sort All 70 Policies
  const filteredPolicies = useMemo(() => {
    let list = [...POLICIES_70_DATA];

    if (filterMode === 'safe') {
      list = list.filter(p => parseFloat(p.mean_block_fpr_pct) <= 5.0);
    } else if (filterMode === 'top10') {
      list = list.filter(p => parseInt(p.overall_rank, 10) <= 10);
    }

    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      list = list.filter(p =>
        p.policy_name.toLowerCase().includes(q) ||
        p.action_mapping.includes(q) ||
        p.overall_rank === q ||
        p.policy_id === q
      );
    }

    list.sort((a, b) => {
      if (sortBy === 'rank') {
        return parseInt(a.overall_rank, 10) - parseInt(b.overall_rank, 10);
      } else if (sortBy === 'ocu') {
        return parseFloat(b.overall_mean_ocu) - parseFloat(a.overall_mean_ocu);
      } else if (sortBy === 'blockFpr') {
        return parseFloat(a.mean_block_fpr_pct) - parseFloat(b.mean_block_fpr_pct);
      } else if (sortBy === 'recall') {
        return parseFloat(b.mean_attack_recall_pct) - parseFloat(a.mean_attack_recall_pct);
      }
      return 0;
    });

    return list;
  }, [searchTerm, filterMode, sortBy]);

  const totalPages = Math.max(1, Math.ceil(filteredPolicies.length / pageSize));
  const pageItems = filteredPolicies.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const getActionName = (code: string) => {
    const map: Record<string, string> = {
      '0': 'Allow',
      '1': 'Alert',
      '2': 'Restrict',
      '3': 'Quarantine',
      '4': 'Block'
    };
    return map[code] || code;
  };

  const renderActionBadges = (mappingStr: string) => {
    // format is "(0, 0, 0, 0, 4, 4)"
    const digits = mappingStr.replace(/[() ]/g, '').split(',');
    return (
      <div style={{ display: 'inline-flex', gap: 3, alignItems: 'center' }}>
        {digits.map((d, i) => {
          let bg = '#e2e8f0';
          let color = '#334155';
          if (d === '4') { bg = '#dc2626'; color = '#ffffff'; }
          else if (d === '3') { bg = '#ea580c'; color = '#ffffff'; }
          else if (d === '2') { bg = '#f59e0b'; color = '#ffffff'; }
          else if (d === '1') { bg = '#0284c7'; color = '#ffffff'; }
          else if (d === '0') { bg = '#10b981'; color = '#ffffff'; }

          return (
            <span
              key={i}
              title={`L${i}: ${getActionName(d)}`}
              style={{
                fontFamily: 'var(--font-mono)', fontSize: 9, fontWeight: 700,
                padding: '1px 5px', borderRadius: 3, background: bg, color: color
              }}
            >
              {d}
            </span>
          );
        })}
      </div>
    );
  };

  return (
    <section id="p2-s5" style={{ marginBottom: 48, scrollMarginTop: 80 }}>
      {/* Section Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <span style={{
          display: 'inline-block', padding: '3px 8px', borderRadius: 4,
          background: 'rgba(2,132,199,0.12)', border: '1px solid rgba(2,132,199,0.3)',
          fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', fontWeight: 700, letterSpacing: '0.05em'
        }}>
          §P2.5
        </span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: 'var(--text-hi)', margin: 0 }}>
          Decision-Theoretic Cost Model &amp; 70-Policy Combinatorial Optimization
        </h2>
      </div>

      <p style={{ fontFamily: 'var(--font-ui)', fontSize: 13, color: 'var(--text-mid)', lineHeight: 1.7, maxWidth: 900, marginBottom: 20 }}>
        Historical drafts evaluated policies using arbitrary dollar multipliers without decision-theoretic grounding.
        Paper 2 standardizes all economic metrics under formal <strong style={{ color: 'var(--text-hi)' }}>Operational Cost Units (OCU)</strong>.
        The loss matrix L(a, y) anchors <em>Allow</em> as the zero baseline (C(Allow) = 0), quantifying
        action penalties for benign disruption vs containment benefits on attack flows.
      </p>

      {/* Grid: Loss Matrix + Heatmap Figure */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 20, marginBottom: 24 }}>
        {/* Table 10: Cost Matrix */}
        <div style={{
          background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden',
          boxShadow: '0 1px 4px rgba(0,0,0,0.05)'
        }}>
          <div style={{
            padding: '12px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
          }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#334155' }}>
              TABLE 10: DECISION-THEORETIC LOSS MATRIX L(a, y)
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#0284c7', background: 'rgba(2,132,199,0.1)', padding: '2px 8px', borderRadius: 4 }}>
              FORMAL OCU MATRIX
            </span>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                <th style={{ padding: '8px 12px', fontWeight: 600 }}>Action (a)</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, color: '#dc2626' }}>Benign Cost C_b(a)</th>
                <th style={{ padding: '8px 12px', fontWeight: 600, color: '#059669' }}>Attack Benefit C_c(a)</th>
                <th style={{ padding: '8px 12px', fontWeight: 600 }}>Net Threat Gain</th>
              </tr>
            </thead>
            <tbody>
              {TABLE2_COST_MATRIX.map((row, idx) => (
                <tr key={idx} style={{
                  borderBottom: '1px solid #e2e8f0',
                  background: idx % 2 === 0 ? '#ffffff' : '#f8fafc'
                }}>
                  <td style={{ padding: '8px 12px', fontWeight: 600, color: '#1e293b' }}>{row.action}</td>
                  <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: '#dc2626' }}>+{row.benignCost} OCU</td>
                  <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: '#059669' }}>{row.containmentBenefit} OCU</td>
                  <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#0284c7' }}>+{row.netBenefitAttack} OCU</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ padding: '10px 14px', background: '#f8fafc', fontSize: 11, color: '#64748b', borderTop: '1px solid #e2e8f0' }}>
            Net Operational Benefit defined as B(&pi;) = -&sum; L(a_i, y_i).
          </div>
        </div>

        {/* Heatmap Figure Card */}
        <div style={{
          background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px',
          boxShadow: '0 1px 4px rgba(0,0,0,0.05)', display: 'flex', flexDirection: 'column'
        }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', letterSpacing: '0.08em', marginBottom: 8, fontWeight: 700 }}>
            FIGURE O3: COST MATRIX UTILITY TRADEOFF HEATMAP
          </div>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 180, background: '#f8fafc', borderRadius: 8, overflow: 'hidden' }}>
            <img
              src="/paper2/figures/O3_cost_matrix_heatmap.png"
              alt="Cost Matrix Heatmap"
              style={{ maxWidth: '100%', maxHeight: 200, objectFit: 'contain' }}
              onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }}
            />
          </div>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#64748b', marginTop: 8, textAlign: 'center' }}>
            Payoff gradient illustrating the 50:1 penalty ratio on Block and containment payoff across escalation tiers.
          </div>
        </div>
      </div>

      {/* Interactive Policy Benefit Bar Chart */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '18px 20px',
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)', marginBottom: 24
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#1e293b' }}>
              OPERATIONAL NET BENEFIT (OCU) ACROSS CANDIDATE DEFENSE POLICIES
            </div>
            <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#64748b' }}>
              Comparing Balanced Multi-State, Sustained Flood, and Combined Net Benefits across key operating policies.
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, background: 'rgba(5,150,105,0.1)', color: '#059669', padding: '3px 8px', borderRadius: 4, fontWeight: 600 }}>
              P_opt: +1.92M Combined
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, background: 'rgba(2,132,199,0.1)', color: '#0284c7', padding: '3px 8px', borderRadius: 4, fontWeight: 600 }}>
              P2-tier: +1.91M Combined (2.43× vs P1)
            </span>
          </div>
        </div>

        <div style={{ width: '100%', height: 280, minWidth: 0 }}>
          {mounted ? (
            <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={280}>
              <BarChart data={POLICY_BAR_DATA} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#475569' }} />
                <YAxis
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  tickFormatter={(val) => `${(val / 1000).toFixed(0)}k`}
                  label={{ value: 'Net Benefit (OCU)', angle: -90, position: 'insideLeft', fontSize: 11, fill: '#475569' }}
                />
                <Tooltip
                  contentStyle={{ background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: 8, fontSize: 11, boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
                  formatter={(value: any, name: any) => [`+${Number(value).toLocaleString()} OCU`, name]}
                />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 6 }} />
                <Bar dataKey="balanced" name="Balanced Multi-State" fill="#059669" radius={[4, 4, 0, 0]} />
                <Bar dataKey="flood" name="Sustained Flood" fill="#0284c7" radius={[4, 4, 0, 0]} />
                <Bar dataKey="combined" name="Combined Net Benefit" fill="#7c3aed" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 280, background: '#f8fafc', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', fontSize: 12 }}>
              Loading policy net benefit benchmark...
            </div>
          )}
        </div>
      </div>

      {/* Master Policies Benchmark Table */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden',
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)', marginBottom: 24
      }}>
        <div style={{
          padding: '12px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#334155' }}>
            TABLE 7: MASTER POLICY BENCHMARK ACROSS EVALUATION WINDOWS (OCU)
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#059669', background: 'rgba(5,150,105,0.1)', padding: '2px 8px', borderRadius: 4 }}>
            70 MONOTONIC MAPPINGS ENUMERATED
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                <th style={{ padding: '10px 12px', fontWeight: 600 }}>Policy</th>
                <th style={{ padding: '10px 12px', fontWeight: 600 }}>Action Mapping (L0 to L5)</th>
                <th style={{ padding: '10px 12px', fontWeight: 600, color: '#059669' }}>Balanced Net</th>
                <th style={{ padding: '10px 12px', fontWeight: 600, color: '#0284c7' }}>Flood Net</th>
                <th style={{ padding: '10px 12px', fontWeight: 600, color: '#7c3aed' }}>Combined Net</th>
                <th style={{ padding: '10px 12px', fontWeight: 600 }}>Balanced Block FPR</th>
                <th style={{ padding: '10px 12px', fontWeight: 600 }}>Search Rank</th>
                <th style={{ padding: '10px 12px', fontWeight: 600 }}>Role</th>
              </tr>
            </thead>
            <tbody>
              {TABLE7_MASTER_POLICIES.map((row, idx) => (
                <tr key={idx} style={{
                  borderBottom: '1px solid #e2e8f0',
                  background: row.policy === 'P2-tier' ? 'rgba(2,132,199,0.04)' : row.policy === 'P_opt' ? 'rgba(5,150,105,0.04)' : idx % 2 === 0 ? '#ffffff' : '#f8fafc'
                }}>
                  <td style={{ padding: '10px 12px', fontWeight: 700, color: '#1e293b' }}>{row.policy}</td>
                  <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', fontSize: 11 }}>{row.mapping}</td>
                  <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: '#059669', fontWeight: 600 }}>{row.balancedNet}</td>
                  <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: '#0284c7', fontWeight: 600 }}>{row.attackHeavyNet}</td>
                  <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: '#7c3aed', fontWeight: 700 }}>{row.combinedNet}</td>
                  <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: row.balancedBlockFpr === '0.00%' ? '#059669' : '#dc2626', fontWeight: 600 }}>
                    {row.balancedBlockFpr}
                  </td>
                  <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', fontSize: 11, color: '#334155' }}>{row.rank}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{
                      padding: '2px 6px', borderRadius: 4, fontSize: 10, fontWeight: 600,
                      background: row.policy === 'P2-tier' ? '#0284c7' : row.policy === 'P_opt' ? '#059669' : '#64748b',
                      color: '#ffffff'
                    }}>
                      {row.badge}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Complete 70-Policy Combinatorial Exploration Suite */}
      <div style={{
        background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10,
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)', overflow: 'hidden', marginBottom: 20
      }}>
        <div style={{
          padding: '14px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#1e293b' }}>
                FULL 70 MONOTONIC RESPONSE POLICIES CATALOG (AUDITED ACROSS 50 RUNS)
              </span>
              <span style={{
                fontFamily: 'var(--font-mono)', fontSize: 9, fontWeight: 700,
                color: '#0284c7', background: 'rgba(2,132,199,0.1)', border: '1px solid rgba(2,132,199,0.3)',
                padding: '2px 8px', borderRadius: 12
              }}>
                C(8, 4) = 70 POLICIES
              </span>
            </div>
            <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#64748b', marginTop: 3 }}>
              Full enumeration of all monotonically non-decreasing escalation mappings with 95% bootstrap confidence bounds.
            </div>
          </div>

          <input
            type="text"
            placeholder="Search policy name, mapping, or rank..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            style={{
              padding: '6px 12px', borderRadius: 6, border: '1px solid #cbd5e1',
              fontFamily: 'var(--font-ui)', fontSize: 12, width: 260
            }}
          />
        </div>

        {/* Filter Controls & Sorting Bar */}
        <div style={{
          padding: '10px 18px', background: '#ffffff', borderBottom: '1px solid #f1f5f9',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12
        }}>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#64748b' }}>FILTER:</span>
            <button
              onClick={() => { setFilterMode('all'); setCurrentPage(1); }}
              style={{
                padding: '3px 10px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                cursor: 'pointer',
                background: filterMode === 'all' ? '#0284c7' : '#f1f5f9',
                color: filterMode === 'all' ? '#ffffff' : '#475569',
                border: filterMode === 'all' ? '1px solid #0284c7' : '1px solid #e2e8f0'
              }}
            >
              All 70 Policies
            </button>
            <button
              onClick={() => { setFilterMode('safe'); setCurrentPage(1); }}
              style={{
                padding: '3px 10px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                cursor: 'pointer',
                background: filterMode === 'safe' ? '#059669' : '#f1f5f9',
                color: filterMode === 'safe' ? '#ffffff' : '#475569',
                border: filterMode === 'safe' ? '1px solid #059669' : '1px solid #e2e8f0'
              }}
            >
              Safety Constrained (65, Block FPR &le; 5%)
            </button>
            <button
              onClick={() => { setFilterMode('top10'); setCurrentPage(1); }}
              style={{
                padding: '3px 10px', borderRadius: 6, fontSize: 11, fontWeight: 600,
                cursor: 'pointer',
                background: filterMode === 'top10' ? '#7c3aed' : '#f1f5f9',
                color: filterMode === 'top10' ? '#ffffff' : '#475569',
                border: filterMode === 'top10' ? '1px solid #7c3aed' : '1px solid #e2e8f0'
              }}
            >
              Top 10 Ranked
            </button>
          </div>

          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#64748b' }}>SORT BY:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              style={{
                padding: '4px 8px', borderRadius: 6, border: '1px solid #cbd5e1',
                fontSize: 11, fontFamily: 'var(--font-ui)', color: '#334155'
              }}
            >
              <option value="rank">Overall Search Rank</option>
              <option value="ocu">Mean Net Benefit (OCU)</option>
              <option value="blockFpr">Lowest Block FPR %</option>
              <option value="recall">Highest Attack Recall %</option>
            </select>
          </div>
        </div>

        {/* Paginated 70-Policy Table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11, textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                <th style={{ padding: '8px 10px', fontWeight: 600, width: '50px' }}>Rank</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Policy Identifier</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Action Vector [L0..L5]</th>
                <th style={{ padding: '8px 10px', fontWeight: 600, color: '#059669' }}>Overall Mean OCU</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>95% Bootstrap CI</th>
                <th style={{ padding: '8px 10px', fontWeight: 600, color: '#dc2626' }}>Mean Block FPR</th>
                <th style={{ padding: '8px 10px', fontWeight: 600, color: '#ea580c' }}>Quarantine FPR</th>
                <th style={{ padding: '8px 10px', fontWeight: 600, color: '#0284c7' }}>Attack Recall</th>
                <th style={{ padding: '8px 10px', fontWeight: 600 }}>Classification</th>
              </tr>
            </thead>
            <tbody>
              {pageItems.map((policy) => {
                const rankNum = parseInt(policy.overall_rank, 10);
                const isPopt = rankNum === 1;
                const isP2tier = rankNum === 9 || policy.policy_name === 'P_0_0_0_0_4_4';
                return (
                  <tr
                    key={policy.policy_id}
                    style={{
                      borderBottom: '1px solid #f1f5f9',
                      background: isPopt ? 'rgba(5,150,105,0.06)' : isP2tier ? 'rgba(2,132,199,0.06)' : '#ffffff'
                    }}
                  >
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: rankNum <= 3 ? '#0284c7' : '#64748b' }}>
                      #{policy.overall_rank}
                    </td>
                    <td style={{ padding: '8px 10px', fontWeight: 600, color: '#1e293b' }}>
                      {policy.policy_name}
                    </td>
                    <td style={{ padding: '8px 10px' }}>
                      {renderActionBadges(policy.action_mapping)}
                    </td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#059669' }}>
                      +{parseFloat(policy.overall_mean_ocu).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', fontSize: 10, color: '#64748b' }}>
                      [{parseFloat(policy.ci95_lower).toLocaleString(undefined, { maximumFractionDigits: 0 })}, {parseFloat(policy.ci95_upper).toLocaleString(undefined, { maximumFractionDigits: 0 })}]
                    </td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: parseFloat(policy.mean_block_fpr_pct) === 0 ? '#059669' : '#dc2626', fontWeight: 600 }}>
                      {policy.mean_block_fpr_pct}%
                    </td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#ea580c' }}>
                      {policy.mean_quarantine_fpr_pct}%
                    </td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#0284c7', fontWeight: 600 }}>
                      {policy.mean_attack_recall_pct}%
                    </td>
                    <td style={{ padding: '8px 10px' }}>
                      {isPopt ? (
                        <span style={{ padding: '2px 6px', borderRadius: 4, fontSize: 9, fontWeight: 700, background: '#059669', color: '#fff' }}>
                          P_opt (Rank 1)
                        </span>
                      ) : rankNum <= 10 ? (
                        <span style={{ padding: '2px 6px', borderRadius: 4, fontSize: 9, fontWeight: 700, background: '#0284c7', color: '#fff' }}>
                          Top 10 Tier
                        </span>
                      ) : parseFloat(policy.mean_block_fpr_pct) <= 5.0 ? (
                        <span style={{ padding: '2px 6px', borderRadius: 4, fontSize: 9, fontWeight: 600, background: '#f1f5f9', color: '#475569' }}>
                          Safe Tier
                        </span>
                      ) : (
                        <span style={{ padding: '2px 6px', borderRadius: 4, fontSize: 9, fontWeight: 600, background: 'rgba(220,38,38,0.1)', color: '#dc2626' }}>
                          Unconstrained
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
              {pageItems.length === 0 && (
                <tr>
                  <td colSpan={9} style={{ padding: 24, textAlign: 'center', color: '#94a3b8', fontStyle: 'italic' }}>
                    No policy mappings match the query.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Navigation Bar */}
        <div style={{
          padding: '10px 18px', background: '#f8fafc', borderTop: '1px solid #e2e8f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10
        }}>
          <div style={{ fontSize: 11, color: '#64748b' }}>
            Showing {((currentPage - 1) * pageSize) + 1}–{Math.min(currentPage * pageSize, filteredPolicies.length)} of {filteredPolicies.length} candidate policies
          </div>
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              style={{
                padding: '4px 10px', borderRadius: 6, border: '1px solid #cbd5e1',
                background: currentPage === 1 ? '#f1f5f9' : '#ffffff',
                color: currentPage === 1 ? '#94a3b8' : '#334155',
                fontSize: 11, cursor: currentPage === 1 ? 'not-allowed' : 'pointer'
              }}
            >
              &larr; Previous
            </button>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#475569', padding: '0 6px' }}>
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              style={{
                padding: '4px 10px', borderRadius: 6, border: '1px solid #cbd5e1',
                background: currentPage === totalPages ? '#f1f5f9' : '#ffffff',
                color: currentPage === totalPages ? '#94a3b8' : '#334155',
                fontSize: 11, cursor: currentPage === totalPages ? 'not-allowed' : 'pointer'
              }}
            >
              Next &rarr;
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
