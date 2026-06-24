'use client';

import { useState, useEffect } from 'react';
import { getTrustSummary, type TrustSummary, type EntityTrust } from '../lib/api';

const RISK: Record<string, { color: string; bg: string; border: string }> = {
  Low:      { color: 'var(--green)',  bg: 'rgba(5,150,105,0.08)',  border: 'rgba(5,150,105,0.22)' },
  Medium:   { color: 'var(--amber)',  bg: 'rgba(217,119,6,0.08)',  border: 'rgba(217,119,6,0.22)' },
  High:     { color: 'var(--red)',    bg: 'rgba(220,38,38,0.08)',  border: 'rgba(220,38,38,0.22)' },
  Critical: { color: 'var(--purple)', bg: 'rgba(124,58,237,0.08)', border: 'rgba(124,58,237,0.22)' },
};

const STATUS_DOT: Record<string, string> = {
  online: 'pulse-green', alerted: 'pulse-amber', quarantined: 'pulse-amber', blocked: 'pulse-red',
};

// Weights from backend trust_manager.py
const ALPHA = 0.3;
const BETA  = 0.3;
const GAMMA = 0.4;

function GaugeRing({ value, label, color, size = 88 }: { value: number; label: string; color: string; size?: number }) {
  const [anim, setAnim] = useState(0);
  const r = size / 2 - 8;
  const circ = 2 * Math.PI * r;

  useEffect(() => {
    const t = setTimeout(() => setAnim(value), 350);
    return () => clearTimeout(t);
  }, [value]);

  const offset = circ - anim * circ;
  const pct = Math.round(anim * 100);

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(0,0,0,0.25)" strokeWidth="7"/>
          <circle cx={size/2} cy={size/2} r={r} fill="none"
            stroke={color} strokeWidth="7" strokeLinecap="round"
            strokeDasharray={circ} strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 1.4s cubic-bezier(0.22,1,0.36,1)', transform: 'rotate(-90deg)', transformOrigin: 'center' }}
          />
          <circle cx={size/2} cy={size/2} r={r} fill="none"
            stroke={color} strokeWidth="2" strokeLinecap="round"
            strokeDasharray={circ} strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 1.4s cubic-bezier(0.22,1,0.36,1)', transform: 'rotate(-90deg)', transformOrigin: 'center', opacity: 0.2, filter: 'blur(3px)' }}
          />
          <text x={size/2} y={size/2 - 4} textAnchor="middle"
            style={{ fill: color, fontFamily: 'var(--font-display)', fontSize: size * 0.185, fontWeight: 700 }}>
            {pct}
          </text>
          <text x={size/2} y={size/2 + 12} textAnchor="middle"
            style={{ fill: 'var(--text-lo)', fontFamily: 'var(--font-mono)', fontSize: 9 }}>
            /100
          </text>
        </svg>
      </div>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', letterSpacing: '0.08em', textAlign: 'center' }}>{label}</span>
    </div>
  );
}

export default function TrustScore() {
  const [summary, setSummary] = useState<TrustSummary | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchTrust() {
      try {
        const data = await getTrustSummary();
        if (!cancelled) {
          setBackendError(null);
          setSummary(data);
        }
      } catch (err) {
        if (!cancelled) setBackendError((err as Error).message);
      }
    }

    fetchTrust();
    const id = setInterval(fetchTrust, 5000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  // Aggregate trust from entity list or fall back to zeros
  const entities = summary?.entity_list ?? [];
  const avgTrust = summary?.average_trust_score ?? 0;
  const avgUser    = entities.length ? entities.reduce((s, e) => s + e.userTrust, 0) / entities.length : 0;
  const avgDevice  = entities.length ? entities.reduce((s, e) => s + e.deviceTrust, 0) / entities.length : 0;
  const avgBehav   = entities.length ? entities.reduce((s, e) => s + e.behaviorTrust, 0) / entities.length : 0;

  const riskLevel = avgTrust >= 0.8 ? 'Low' : avgTrust >= 0.5 ? 'Medium' : avgTrust >= 0.25 ? 'High' : 'Critical';
  const rc = RISK[riskLevel];
  const hasData = entities.length > 0;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

      {/* Trust Engine */}
      <div className="rounded-xl p-5 bracket-all"
        style={{ background: '#ffffff', border: '1px solid #000000', backdropFilter: 'blur(16px)', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
        <div className="card-header">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--purple)" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <span className="card-title">Dynamic Trust Engine</span>
          {backendError && (
            <span className="ml-auto tag" style={{ background: 'rgba(220,38,38,0.09)', color: 'var(--red)', border: '1px solid rgba(220,38,38,0.25)', fontSize: 9 }}>
              OFFLINE
            </span>
          )}
        </div>

        {/* Formula */}
        <div className="rounded-lg px-3 py-2.5 mb-5"
          style={{ background: 'rgba(124,58,237,0.07)', border: '1px solid rgba(124,58,237,0.18)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', letterSpacing: '0.12em', marginBottom: 3 }}>// TRUST FORMULA</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 15, fontWeight: 700, color: 'var(--purple)', letterSpacing: '0.04em' }}>
            T = {ALPHA}·U + {BETA}·D + {GAMMA}·B
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', marginTop: 3 }}>
            U=User Trust · D=Device Trust · B=Behavior Trust
          </div>
        </div>

        {/* Gauges */}
        <div className="grid grid-cols-3 gap-3 mb-5">
          <GaugeRing value={hasData ? avgUser   : 0} label="User Trust"     color="var(--cyan)"   />
          <GaugeRing value={hasData ? avgDevice : 0} label="Device Trust"   color="var(--purple)" />
          <GaugeRing value={hasData ? avgBehav  : 0} label="Behavior Trust" color="var(--amber)"  />
        </div>

        {/* Final score */}
        <div className="rounded-lg p-4"
          style={{ background: 'linear-gradient(135deg, rgba(2,132,199,0.07), rgba(124,58,237,0.07))', border: '1px solid rgba(2,132,199,0.20)' }}>
          <div className="flex items-end justify-between">
            <div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', letterSpacing: '0.12em', marginBottom: 4 }}>
                // COMPOSITE SCORE
              </div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 38, fontWeight: 800, color: 'var(--cyan)', letterSpacing: '-0.03em', textShadow: '0 0 24px rgba(2,132,199,0.4)', lineHeight: 1 }}>
                {hasData ? avgTrust.toFixed(3) : (backendError ? 'ERR' : '—')}
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: hasData ? 'var(--green)' : 'var(--text-lo)', marginTop: 4 }}>
                {hasData ? `${summary?.high_trust_entities ?? 0} high · ${summary?.medium_trust_entities ?? 0} med · ${summary?.low_trust_entities ?? 0} low trust` : 'Start capture to compute trust'}
              </div>
            </div>
            <div className="text-right">
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', letterSpacing: '0.1em', marginBottom: 4 }}>RISK LEVEL</div>
              <span className="tag" style={{ background: rc?.bg, color: rc?.color, border: `1px solid ${rc?.border}`, fontFamily: 'var(--font-display)', fontSize: 11, letterSpacing: '0.12em', padding: '5px 12px' }}>
                {hasData ? riskLevel.toUpperCase() : '—'}
              </span>
            </div>
          </div>
          <div className="track mt-4" style={{ height: 5 }}>
            <div className="track-fill"
              style={{ width: `${avgTrust * 100}%`, background: 'linear-gradient(90deg, var(--cyan), var(--purple))', boxShadow: '0 0 8px rgba(2,132,199,0.30)', transition: 'width 1s ease' }} />
          </div>
        </div>

        {/* Weight bars */}
        <div className="mt-4 space-y-2">
          {[
            { label: 'α Weight (User)',     val: ALPHA, color: 'var(--cyan)' },
            { label: 'β Weight (Device)',   val: BETA,  color: 'var(--purple)' },
            { label: 'γ Weight (Behavior)', val: GAMMA, color: 'var(--amber)' },
          ].map(w => (
            <div key={w.label} className="flex items-center gap-3">
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', width: 120, flexShrink: 0 }}>{w.label}</span>
              <div className="track flex-1" style={{ height: 3 }}>
                <div className="track-fill" style={{ width: `${w.val * 100}%`, background: w.color }} />
              </div>
              <span style={{ fontFamily: 'var(--font-display)', fontSize: 11, color: w.color, width: 28, textAlign: 'right' }}>{w.val}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Entity Registry */}
      <div className="rounded-xl overflow-hidden bracket-all"
        style={{ background: '#ffffff', border: '1px solid #000000', backdropFilter: 'blur(16px)', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
        <div className="card-header px-4 pt-4 pb-3" style={{ borderBottom: '1px solid var(--border-dim)' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2">
            <rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
          <span className="card-title">Entity Trust Registry</span>
          <span className="ml-auto" style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
            {entities.length} entities
          </span>
        </div>

        {!hasData ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--text-lo)" strokeWidth="1.5">
              <rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', textAlign: 'center', maxWidth: 200 }}>
              {backendError ? 'Backend offline — start Flask server' : 'No entities seen yet — start packet capture'}
            </span>
          </div>
        ) : (
          <div style={{ maxHeight: 500, overflowY: 'auto' }}>
            {entities.map((dev: EntityTrust, i: number) => {
              const rc2 = RISK[dev.riskLevel] ?? RISK.Low;
              const dotCls = STATUS_DOT[dev.status] ?? 'pulse-cyan';
              const trustColor = dev.finalTrust < 0.3 ? 'var(--red)' : dev.finalTrust < 0.6 ? 'var(--amber)' : 'var(--green)';
              return (
                <div key={dev.id}
                  className="px-4 py-3 transition-all cursor-default"
                  style={{ borderBottom: '1px solid rgba(0,0,0,0.18)', animationDelay: `${i * 40}ms` }}
                  onMouseEnter={e => { e.currentTarget.style.background = 'rgba(2,132,199,0.06)'; }}
                  onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}>
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`pulse-dot ${dotCls}`} style={{ flexShrink: 0 }} />
                      <div>
                        <div style={{ fontFamily: 'var(--font-ui)', fontSize: 13, fontWeight: 600, color: 'var(--text-hi)' }}>{dev.ip}</div>
                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>{dev.id}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="tag" style={{ background: rc2?.bg, color: rc2?.color, border: `1px solid ${rc2?.border}`, fontSize: 9 }}>{dev.riskLevel}</span>
                      <span style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 700, color: trustColor }}>{dev.finalTrust.toFixed(2)}</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { l: 'User',     v: dev.userTrust,     c: 'var(--cyan)' },
                      { l: 'Device',   v: dev.deviceTrust,   c: 'var(--purple)' },
                      { l: 'Behavior', v: dev.behaviorTrust, c: 'var(--amber)' },
                    ].map(m => (
                      <div key={m.l}>
                        <div className="flex justify-between mb-0.5">
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>{m.l}</span>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: m.c }}>{Math.round(m.v * 100)}</span>
                        </div>
                        <div className="track" style={{ height: 3 }}>
                          <div className="track-fill" style={{ width: `${m.v * 100}%`, background: m.c, opacity: 0.75 }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
