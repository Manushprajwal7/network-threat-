'use client';

import { useState, useEffect } from 'react';
import { getTrustSummary, getDashboardStats, type TrustSummary, type EntityTrust } from '../../../lib/api';

const ALPHA = 0.3;
const BETA  = 0.3;
const GAMMA = 0.4;

function GaugeRing({ value, color, size = 80 }: { value: number; color: string; size?: number }) {
  const r = (size - 10) / 2;
  const circ = 2 * Math.PI * r;
  const filled = circ * Math.max(0, Math.min(1, value));
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(0,0,0,0.18)" strokeWidth="6" />
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="6"
        strokeDasharray={`${filled} ${circ - filled}`}
        strokeDashoffset={circ * 0.25}
        strokeLinecap="round"
        style={{ transition: 'stroke-dasharray 1s ease', filter: `drop-shadow(0 0 4px ${color})` }}
      />
      <text x={size/2} y={size/2 + 1} textAnchor="middle" dominantBaseline="middle"
        style={{ fontFamily: 'Orbitron', fontSize: size * 0.18, fontWeight: 700, fill: color }}>
        {Math.round(value * 100)}
      </text>
    </svg>
  );
}

function EntityRow({ entity, rank }: { entity: EntityTrust; rank: number }) {
  const STATUS: Record<string, string> = {
    online: 'var(--green)', alerted: 'var(--amber)', quarantined: '#ea6c1a', blocked: 'var(--red)',
  };
  const statusColor = STATUS[entity.status] ?? 'var(--text-lo)';
  const trustColor = entity.finalTrust >= 0.8 ? 'var(--green)' : entity.finalTrust >= 0.5 ? 'var(--amber)' : 'var(--red)';

  return (
    <tr>
      <td style={{ color: 'var(--text-lo)', fontFamily: 'var(--font-mono)', fontSize: 10 }}>#{rank}</td>
      <td>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded flex items-center justify-center flex-shrink-0"
            style={{ background: 'rgba(2,132,199,0.12)', border: '1px solid rgba(2,132,199,0.22)' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--cyan)' }}>
              {entity.name.slice(0, 2).toUpperCase()}
            </span>
          </div>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-mid)' }}>{entity.ip}</span>
        </div>
      </td>
      <td>
        <div className="flex items-center gap-2">
          <div className="track flex-1" style={{ height: 4, minWidth: 60 }}>
            <div className="track-fill" style={{ width: `${entity.userTrust * 100}%`, background: 'var(--cyan)', transition: 'width 0.8s' }} />
          </div>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--cyan)', minWidth: 30, textAlign: 'right' }}>
            {Math.round(entity.userTrust * 100)}
          </span>
        </div>
      </td>
      <td>
        <div className="flex items-center gap-2">
          <div className="track flex-1" style={{ height: 4, minWidth: 60 }}>
            <div className="track-fill" style={{ width: `${entity.deviceTrust * 100}%`, background: 'var(--purple)', transition: 'width 0.8s' }} />
          </div>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--purple)', minWidth: 30, textAlign: 'right' }}>
            {Math.round(entity.deviceTrust * 100)}
          </span>
        </div>
      </td>
      <td>
        <div className="flex items-center gap-2">
          <div className="track flex-1" style={{ height: 4, minWidth: 60 }}>
            <div className="track-fill" style={{ width: `${entity.behaviorTrust * 100}%`, background: 'var(--amber)', transition: 'width 0.8s' }} />
          </div>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--amber)', minWidth: 30, textAlign: 'right' }}>
            {Math.round(entity.behaviorTrust * 100)}
          </span>
        </div>
      </td>
      <td>
        <span style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 800, color: trustColor }}>
          {Math.round(entity.finalTrust * 100)}
        </span>
      </td>
      <td>
        <span className="tag" style={{ fontSize: 9,
          background: entity.riskLevel === 'Low' ? 'rgba(5,150,105,0.09)' : entity.riskLevel === 'Critical' ? 'rgba(124,58,237,0.12)' : 'rgba(217,119,6,0.09)',
          color: entity.riskLevel === 'Low' ? 'var(--green)' : entity.riskLevel === 'Critical' ? 'var(--purple)' : entity.riskLevel === 'High' ? 'var(--red)' : 'var(--amber)',
          border: '1px solid rgba(0,0,0,0.20)',
        }}>
          {entity.riskLevel}
        </span>
      </td>
      <td>
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full" style={{ background: statusColor }} />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: statusColor }}>{entity.status.toUpperCase()}</span>
        </div>
      </td>
    </tr>
  );
}

export default function TrustPage() {
  const [summary, setSummary] = useState<TrustSummary | null>(null);
  const [avgTrustGlobal, setAvgTrustGlobal] = useState<number>(0);
  const [backendError, setBackendError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchData() {
      try {
        const [s, stats] = await Promise.all([getTrustSummary(), getDashboardStats()]);
        if (cancelled) return;
        setBackendError(null);
        setSummary(s);
        setAvgTrustGlobal(stats.average_trust_score);
      } catch (err) {
        if (!cancelled) setBackendError((err as Error).message);
      }
    }
    fetchData();
    const id = setInterval(fetchData, 5000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const entities = summary?.entity_list ?? [];
  const avgU = entities.length > 0 ? entities.reduce((s, e) => s + e.userTrust, 0) / entities.length : 0;
  const avgD = entities.length > 0 ? entities.reduce((s, e) => s + e.deviceTrust, 0) / entities.length : 0;
  const avgB = entities.length > 0 ? entities.reduce((s, e) => s + e.behaviorTrust, 0) / entities.length : 0;

  return (
    <>
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="section-label mb-2">Zero-Trust Architecture</div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 800, color: 'var(--text-hi)', letterSpacing: '0.03em', lineHeight: 1 }}>
            Trust Engine
          </h1>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', marginTop: 4 }}>
            T = α·U + β·D + γ·B where α={ALPHA}, β={BETA}, γ={GAMMA}
          </p>
        </div>
      </div>

      {/* Trust formula & gauges */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-5">
        {/* Formula card */}
        <div className="rounded-xl p-5 bracket-all lg:col-span-1"
          style={{ background: '#ffffff', border: '1px solid #000000', backdropFilter: 'blur(16px)', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
          <div className="card-header mb-4">
            <span className="card-title">Trust Formula</span>
          </div>
          <div className="px-3 py-3 rounded-lg mb-4"
            style={{ background: 'rgba(2,132,199,0.06)', border: '1px solid rgba(2,132,199,0.12)', fontFamily: 'var(--font-display)', fontSize: 13, fontWeight: 700, color: 'var(--cyan)', letterSpacing: '0.06em', textAlign: 'center' }}>
            T = α·U + β·D + γ·B
          </div>
          {[
            { sym: 'α', val: ALPHA, label: 'User Trust', c: 'var(--cyan)', desc: 'User behaviour & auth history' },
            { sym: 'β', val: BETA,  label: 'Device Trust', c: 'var(--purple)', desc: 'Device posture & integrity' },
            { sym: 'γ', val: GAMMA, label: 'Behavior Trust', c: 'var(--amber)', desc: 'Network flow behavioural score' },
          ].map(w => (
            <div key={w.sym} className="mb-3">
              <div className="flex items-center gap-2 mb-1">
                <span className="tag" style={{ background: 'rgba(0,0,0,0.12)', color: w.c, border: '1px solid rgba(0,0,0,0.25)', fontSize: 9, minWidth: 22, textAlign: 'center' }}>
                  {w.sym}={w.val}
                </span>
                <span style={{ fontFamily: 'var(--font-ui)', fontSize: 11, fontWeight: 500, color: 'var(--text-mid)' }}>{w.label}</span>
              </div>
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', paddingLeft: 4 }}>{w.desc}</p>
            </div>
          ))}
        </div>

        {/* Gauge rings */}
        <div className="lg:col-span-3 grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Avg Trust', value: avgTrustGlobal, color: '#059669', sub: 'Global · T score' },
            { label: 'User Trust',     value: avgU, color: '#0284c7', sub: `α = ${ALPHA} weight` },
            { label: 'Device Trust',   value: avgD, color: '#7c3aed', sub: `β = ${BETA} weight` },
            { label: 'Behavior Trust', value: avgB, color: '#d97706', sub: `γ = ${GAMMA} weight` },
          ].map(g => (
            <div key={g.label} className="rounded-xl p-4 bracket-all flex flex-col items-center gap-2"
              style={{ background: '#ffffff', border: '1px solid #000000', backdropFilter: 'blur(16px)', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
              <GaugeRing value={g.value} color={g.color} size={90} />
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 11, fontWeight: 700, color: 'var(--text-mid)', letterSpacing: '0.08em', textAlign: 'center' }}>
                {g.label}
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', textAlign: 'center' }}>{g.sub}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Summary counts */}
      <div className="grid grid-cols-3 gap-4 mb-5">
        {[
          { l: 'High Trust', v: summary?.high_trust_entities ?? 0, c: 'var(--green)', desc: '≥ 80 trust score' },
          { l: 'Med Trust',  v: summary?.medium_trust_entities ?? 0, c: 'var(--amber)', desc: '50–79 trust score' },
          { l: 'Low Trust',  v: summary?.low_trust_entities ?? 0, c: 'var(--red)', desc: '< 50 trust score' },
        ].map(s => (
          <div key={s.l} className="rounded-xl p-4 bracket-all"
            style={{ background: '#ffffff', border: '1px solid #000000', backdropFilter: 'blur(16px)', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '0.12em', marginBottom: 4 }}>{s.l}</div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 800, color: s.c, lineHeight: 1 }}>{s.v}</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', marginTop: 4 }}>{s.desc}</div>
          </div>
        ))}
      </div>

      {/* Entity registry table */}
      <div className="rounded-xl overflow-hidden bracket-all mb-5"
        style={{ background: '#ffffff', border: '1px solid #000000', backdropFilter: 'blur(16px)', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
        <div className="flex items-center gap-3 px-4 py-3"
          style={{ borderBottom: '1px solid var(--border-dim)', background: 'rgba(0,0,0,0.05)' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--purple)" strokeWidth="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          <span className="card-title">Entity Registry</span>
          <span className="tag ml-auto" style={{ background: 'rgba(124,58,237,0.10)', color: 'var(--purple)', border: '1px solid rgba(124,58,237,0.24)', fontSize: 9 }}>
            {entities.length} entities
          </span>
        </div>

        {entities.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16">
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', textAlign: 'center' }}>
              {backendError ? 'Backend offline — start Flask server' : 'No entities yet — start packet capture from Overview'}
            </span>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="w-full data-table" style={{ minWidth: 900 }}>
              <thead style={{ position: 'sticky', top: 0, background: 'rgba(0,0,0,0.08)', zIndex: 2 }}>
                <tr>
                  {['#','Entity IP','User Trust (U)','Device Trust (D)','Behavior Trust (B)','Final T','Risk','Status'].map(h => (
                    <th key={h} className="text-left">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {entities.map((entity, i) => (
                  <EntityRow key={entity.id} entity={entity} rank={i + 1} />
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="px-4 py-2" style={{ borderTop: '1px solid var(--border-dim)', background: 'rgba(0,0,0,0.03)' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
            {entities.length} unique entities · 5s refresh · sorted by ascending trust score
          </span>
        </div>
      </div>

      <div style={{ height: 40 }} />
    </>
  );
}
