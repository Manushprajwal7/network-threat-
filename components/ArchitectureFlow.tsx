'use client';

import { useState, useEffect } from 'react';

const STAGES = [
  {
    id: 'capture', num: '01', label: 'Packet Capture', sub: 'Raw pcap ingestion · 4.8M pkts/day',
    color: 'var(--cyan)', detail: 'Network tap · promiscuous mode · all layer protocols captured',
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>,
  },
  {
    id: 'extract', num: '02', label: 'Feature Extraction', sub: 'CICFlowMeter · 78 statistical features',
    color: 'var(--purple)', detail: 'Flow-level: IAT, length, flags, duration, bytes, sub-flow',
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>,
  },
  {
    id: 'detect', num: '03', label: 'ML Detection', sub: 'Random Forest · 13 classes · CICIDS2017',
    color: 'var(--green)', detail: 'RFC n=200 estimators · max_depth=20 · class-weighted · balanced',
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/></svg>,
  },
  {
    id: 'trust', num: '04', label: 'Trust Score', sub: 'T = α·U + β·D + γ·B · adaptive weights',
    color: 'var(--amber)', detail: 'α=0.3 · β=0.3 · γ=0.4 · real-time propagation',
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>,
  },
  {
    id: 'decide', num: '05', label: 'Security Decision', sub: 'Allow · Restrict · Alert · Quarantine · Block',
    color: 'var(--red)', detail: 'Multi-level response · feedback loop · policy enforcement',
    icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>,
  },
];

export default function ArchitectureFlow() {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setActive(p => (p + 1) % STAGES.length), 2000);
    return () => clearInterval(id);
  }, []);

  const cur = STAGES[active];

  return (
    <div className="rounded-xl p-5 bracket-all"
      style={{ background: 'rgba(3,10,22,0.90)', border: '1px solid var(--border-dim)', backdropFilter: 'blur(16px)' }}>
      <div className="card-header">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2">
          <circle cx="12" cy="12" r="2"/>
          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
        </svg>
        <span className="card-title">System Architecture Pipeline</span>
        <span className="ml-auto live-indicator">
          <span className="pulse-dot pulse-green" style={{ width: 5, height: 5 }} />
          PROCESSING
        </span>
      </div>

      {/* Pipeline desktop */}
      <div className="hidden md:grid gap-0 mb-4" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
        {STAGES.map((stage, i) => {
          const isActive = active === i;
          const isPast = i < active;
          return (
            <div key={stage.id} className="flex items-center">
              <div className="flex-1 flex flex-col items-center gap-2 p-3 rounded-xl cursor-pointer transition-all duration-300"
                style={{
                  background: isActive ? `${stage.color}10` : 'rgba(255,255,255,0.015)',
                  border: `1px solid ${isActive ? stage.color + '45' : 'rgba(255,255,255,0.05)'}`,
                  boxShadow: isActive ? `0 0 24px ${stage.color}18` : 'none',
                  transform: isActive ? 'translateY(-2px)' : 'none',
                }}
                onClick={() => setActive(i)}>
                {/* Stage number */}
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: isActive ? stage.color : 'var(--text-lo)', letterSpacing: '0.1em' }}>
                  {stage.num}
                </div>
                {/* Icon */}
                <div className="w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300"
                  style={{
                    background: isActive ? `${stage.color}18` : 'rgba(255,255,255,0.04)',
                    color: isActive ? stage.color : isPast ? stage.color + '60' : 'var(--text-lo)',
                    border: `1px solid ${isActive ? stage.color + '40' : 'rgba(255,255,255,0.06)'}`,
                  }}>
                  {stage.icon}
                </div>
                {/* Label */}
                <div className="text-center">
                  <div style={{
                    fontFamily: 'var(--font-display)', fontSize: 9, fontWeight: 600,
                    color: isActive ? stage.color : isPast ? 'var(--text-mid)' : 'var(--text-lo)',
                    letterSpacing: '0.08em', textTransform: 'uppercase', textAlign: 'center',
                  }}>
                    {stage.label}
                  </div>
                </div>
                {/* Progress dots */}
                {isActive && (
                  <div className="flex gap-1">
                    {[0,1,2].map(d => (
                      <div key={d} className="w-1 h-1 rounded-full"
                        style={{ background: stage.color, opacity: 0.6, animation: `neon-pulse ${0.6 + d * 0.3}s ease-in-out infinite` }} />
                    ))}
                  </div>
                )}
              </div>
              {/* Connector */}
              {i < STAGES.length - 1 && (
                <div className="flex items-center justify-center w-6 flex-shrink-0">
                  <svg width="20" height="12" viewBox="0 0 20 12">
                    <line x1="0" y1="6" x2="14" y2="6" stroke={isPast || isActive ? stage.color : 'rgba(255,255,255,0.07)'} strokeWidth="1" strokeDasharray="3 2"/>
                    <polygon points="12,3 20,6 12,9" fill={isPast || isActive ? stage.color : 'rgba(255,255,255,0.08)'} opacity="0.7"/>
                    {/* Animated packet */}
                    {isActive && (
                      <circle r="2.5" fill={stage.color} style={{ filter: `drop-shadow(0 0 4px ${stage.color})` }}>
                        <animateMotion dur="2s" repeatCount="indefinite" path="M 0 6 L 18 6"/>
                      </circle>
                    )}
                  </svg>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Mobile list */}
      <div className="flex flex-col gap-2 md:hidden mb-4">
        {STAGES.map((stage, i) => (
          <div key={stage.id} className="flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all"
            style={{
              background: active === i ? `${stage.color}10` : 'rgba(255,255,255,0.02)',
              border: `1px solid ${active === i ? stage.color + '40' : 'rgba(255,255,255,0.05)'}`,
            }}
            onClick={() => setActive(i)}>
            <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
              style={{ background: `${stage.color}15`, color: stage.color }}>
              {stage.icon}
            </div>
            <div className="flex-1">
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 10, color: stage.color, letterSpacing: '0.08em' }}>{stage.label}</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>{stage.sub}</div>
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>{stage.num}</div>
          </div>
        ))}
      </div>

      {/* Active stage detail */}
      <div className="rounded-lg p-4 transition-all duration-300"
        style={{
          background: `linear-gradient(135deg, ${cur.color}07, rgba(0,0,0,0))`,
          border: `1px solid ${cur.color}25`,
        }}>
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: `${cur.color}15`, color: cur.color, border: `1px solid ${cur.color}35` }}>
            {cur.icon}
          </div>
          <div className="flex-1">
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 12, fontWeight: 700, color: cur.color, letterSpacing: '0.1em', marginBottom: 3 }}>
              STAGE {cur.num} — {cur.label}
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-mid)' }}>{cur.sub}</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', marginTop: 3 }}>{cur.detail}</div>
          </div>
          <div className="flex flex-col items-end gap-1">
            <div className="live-indicator">● ACTIVE</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
              {active + 1} / {STAGES.length}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
