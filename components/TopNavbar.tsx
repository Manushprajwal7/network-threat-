'use client';

import { useState, useEffect } from 'react';
import { getDashboardStats, getCaptureStatus } from '../lib/api';

export default function TopNavbar() {
  const [time, setTime] = useState('--:--:--');
  const [date, setDate] = useState('');
  const [ping, setPing] = useState(12);
  const [metrics, setMetrics] = useState({ flows: '—', threats: '—', trust: '—', conf: '—' });
  const [capturing, setCapturing] = useState(false);

  // Clock
  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString('en-US', { hour12: false }));
      setDate(now.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }));
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  // Live metrics from backend
  useEffect(() => {
    let cancelled = false;

    async function fetchMetrics() {
      try {
        const t0 = Date.now();
        const [stats, status] = await Promise.all([
          getDashboardStats(),
          getCaptureStatus(),
        ]);
        if (cancelled) return;
        setPing(Date.now() - t0);
        setCapturing(status.is_running);
        if (stats.source === 'live') {
          setMetrics({
            flows:   stats.active_flows.toLocaleString(),
            threats: stats.threats_detected.toLocaleString(),
            trust:   `${(stats.average_trust_score * 100).toFixed(1)}%`,
            conf:    stats.model_confidence > 0
              ? `${(stats.model_confidence * 100).toFixed(1)}%`
              : '—',
          });
        } else {
          setMetrics({ flows: '—', threats: '—', trust: '—', conf: '—' });
        }
      } catch {
        if (!cancelled) {
          setMetrics({ flows: 'ERR', threats: 'ERR', trust: 'ERR', conf: 'ERR' });
          setCapturing(false);
        }
      }
    }

    fetchMetrics();
    const id = setInterval(fetchMetrics, 3000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  return (
    <header id="top-bar"
      className="fixed top-0 right-0 z-30 flex items-center gap-3 px-4"
      style={{
        left: 240,
        height: 56,
        background: '#ffffff',
        borderBottom: '1px solid var(--border-dim)',
        backdropFilter: 'blur(20px)',
        boxShadow: '0 1px 0 0 rgba(0,0,0,0.15)',
        transition: 'left 0.3s',
      }}>

      <div className="absolute top-0 left-0 right-0 h-px"
        style={{ background: 'linear-gradient(90deg, transparent, rgba(2,132,199,0.4), rgba(124,58,237,0.3), transparent)' }} />

      <div className="flex items-center gap-2 ml-8 lg:ml-0 mr-4">
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--cyan)', letterSpacing: '0.1em' }}>NETSHIELD</span>
        <span style={{ color: 'var(--text-lo)' }}>/</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-mid)' }}>SOC Dashboard</span>
      </div>

      <div className="live-indicator hidden md:flex"
        style={capturing ? undefined : { color: 'var(--text-lo)', background: 'rgba(0,0,0,0.12)', borderColor: 'rgba(0,0,0,0.30)' }}>
        <span className={`pulse-dot ${capturing ? 'pulse-green' : 'pulse-amber'}`} style={{ width: 5, height: 5 }} />
        {capturing ? 'LIVE' : 'IDLE'}
      </div>

      <div className="flex-1" />

      <div className="hidden lg:flex items-center gap-4">
        {[
          { label: 'FLOWS',   val: metrics.flows,   color: 'var(--cyan)' },
          { label: 'THREATS', val: metrics.threats, color: 'var(--red)' },
          { label: 'TRUST',   val: metrics.trust,   color: 'var(--green)' },
          { label: 'CONF',    val: metrics.conf,    color: 'var(--amber)' },
        ].map(m => (
          <div key={m.label} className="text-center px-3 py-1 rounded"
            style={{ background: 'rgba(0,0,0,0.10)', borderLeft: `2px solid ${m.color}40` }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', letterSpacing: '0.12em', marginBottom: 1 }}>{m.label}</div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 13, fontWeight: 700, color: m.color }}>{m.val}</div>
          </div>
        ))}
      </div>

      <div className="hidden lg:block w-px h-6 mx-1" style={{ background: 'var(--border-dim)' }} />

      <div className="hidden sm:flex flex-col items-end">
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 14, fontWeight: 500, color: 'var(--cyan)', letterSpacing: '0.08em' }}>
          {time}
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
          {date} · {ping}ms
        </div>
      </div>

      <div className="flex items-center gap-1.5">
        <button className="relative p-2 rounded-md transition-colors"
          style={{ color: 'var(--text-lo)', borderRadius: '6px' }}
          onMouseEnter={e => { e.currentTarget.style.color = 'var(--cyan)'; e.currentTarget.style.background = 'var(--cyan-dim)'; }}
          onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-lo)'; e.currentTarget.style.background = 'transparent'; }}>
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
        </button>
        <div className="hex-badge w-8 h-8 flex items-center justify-center cursor-pointer ml-1"
          style={{ background: 'linear-gradient(135deg, rgba(2,132,199,0.18), rgba(124,58,237,0.18))', border: '1px solid rgba(2,132,199,0.30)' }}>
          <span style={{ fontFamily: 'var(--font-display)', fontSize: 10, fontWeight: 700, color: 'var(--cyan)' }}>LT</span>
        </div>
      </div>
    </header>
  );
}
