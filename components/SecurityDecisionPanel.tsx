'use client';

import { useState, useEffect } from 'react';
import { getSecurityDecisions, getRecentAlerts, type Alert } from '../lib/api';

const DEC = {
  allow:      { color: 'var(--green)',  bg: 'rgba(0,255,157,0.06)',  border: 'rgba(0,255,157,0.18)',  label: 'ALLOW',      icon: '✓', desc: 'Permitted through all security layers' },
  restrict:   { color: 'var(--cyan)',   bg: 'rgba(0,212,255,0.06)',  border: 'rgba(0,212,255,0.18)',  label: 'RESTRICT',   icon: '⊘', desc: 'Rate-limited · bandwidth throttled' },
  alert:      { color: 'var(--amber)',  bg: 'rgba(255,176,32,0.06)', border: 'rgba(255,176,32,0.18)', label: 'ALERT',      icon: '▲', desc: 'Flagged for analyst review' },
  quarantine: { color: '#ff8c42',       bg: 'rgba(255,140,66,0.06)', border: 'rgba(255,140,66,0.18)', label: 'QUARANTINE', icon: '⬡', desc: 'Isolated in sandboxed VLAN' },
  block:      { color: 'var(--red)',    bg: 'rgba(255,45,85,0.06)',  border: 'rgba(255,45,85,0.18)',  label: 'BLOCK',      icon: '✕', desc: 'Dropped · IP blacklisted' },
} as const;

const ALERT_SEV: Record<string, { color: string; bg: string; border: string }> = {
  critical: { color: 'var(--purple)', bg: 'rgba(191,95,255,0.06)', border: 'rgba(191,95,255,0.2)' },
  high:     { color: 'var(--red)',    bg: 'rgba(255,45,85,0.06)',  border: 'rgba(255,45,85,0.2)' },
  medium:   { color: 'var(--amber)',  bg: 'rgba(255,176,32,0.06)', border: 'rgba(255,176,32,0.2)' },
  low:      { color: 'var(--cyan)',   bg: 'rgba(0,212,255,0.06)',  border: 'rgba(0,212,255,0.2)' },
};

const DOT_CLASS: Record<string, string> = {
  critical: 'pulse-purple', high: 'pulse-red', medium: 'pulse-amber', low: 'pulse-cyan',
};

export default function SecurityDecisionPanel() {
  const [decisions, setDecisions] = useState<Record<string, { count: number; percentage: number }>>({});
  const [alerts, setAlerts] = useState<(Alert & { _acked?: boolean })[]>([]);
  const [backendError, setBackendError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      try {
        const [decData, alertData] = await Promise.all([
          getSecurityDecisions(),
          getRecentAlerts(20),
        ]);
        if (cancelled) return;
        setBackendError(null);
        setDecisions(decData.decisions);
        // Merge fresh alerts but preserve acked state
        setAlerts(prev => {
          const ackedIds = new Set(prev.filter(a => a._acked).map(a => a.id));
          return alertData.alerts.map(a => ({ ...a, _acked: ackedIds.has(a.id) }));
        });
      } catch (err) {
        if (!cancelled) setBackendError((err as Error).message);
      }
    }

    fetchData();
    const id = setInterval(fetchData, 3000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const ack = (id: string) => setAlerts(p => p.map(a => a.id === id ? { ...a, _acked: true } : a));
  const ackAll = () => setAlerts(p => p.map(a => ({ ...a, _acked: true })));

  const total = Object.values(decisions).reduce((s, d) => s + d.count, 0);
  const hasDecisions = total > 0;
  const hasAlerts = alerts.length > 0;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

      {/* Decision Engine */}
      <div className="rounded-xl p-4 bracket-all"
        style={{ background: 'rgba(3,10,22,0.90)', border: '1px solid var(--border-dim)', backdropFilter: 'blur(16px)' }}>
        <div className="card-header">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span className="card-title">Security Decision Engine</span>
          <span className="ml-auto" style={{ fontFamily: 'var(--font-display)', fontSize: 14, color: 'var(--cyan)' }}>
            {total > 0 ? total.toLocaleString() : '—'}
          </span>
        </div>

        {!hasDecisions ? (
          <div className="flex flex-col items-center justify-center py-12 gap-3">
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', textAlign: 'center' }}>
              {backendError ? 'Backend offline' : 'No decisions yet — start packet capture'}
            </span>
          </div>
        ) : (
          <div className="space-y-2">
            {(Object.entries(DEC) as Array<[keyof typeof DEC, typeof DEC[keyof typeof DEC]]>).map(([key, cfg]) => {
              const d = decisions[key] ?? { count: 0, percentage: 0 };
              return (
                <div key={key} className="rounded-lg p-3 transition-all cursor-default"
                  style={{ background: 'rgba(255,255,255,0.018)', border: `1px solid ${cfg.border}` }}
                  onMouseEnter={e => { e.currentTarget.style.background = cfg.bg; }}
                  onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.018)'; }}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2.5">
                      <span className="w-6 h-6 rounded flex items-center justify-center text-sm"
                        style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}` }}>
                        {cfg.icon}
                      </span>
                      <div>
                        <div style={{ fontFamily: 'var(--font-display)', fontSize: 10, fontWeight: 700, color: cfg.color, letterSpacing: '0.1em' }}>{cfg.label}</div>
                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', marginTop: 1 }}>{cfg.desc}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 700, color: 'var(--text-hi)', lineHeight: 1 }}>{d.count.toLocaleString()}</div>
                      <div className="flex items-center gap-1 justify-end mt-0.5">
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>{d.percentage.toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                  <div className="track" style={{ height: 3 }}>
                    <div className="track-fill" style={{ width: `${d.percentage}%`, background: cfg.color, transition: 'width 0.8s ease' }} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Alerts */}
      <div className="rounded-xl overflow-hidden bracket-all"
        style={{ background: 'rgba(3,10,22,0.90)', border: '1px solid var(--border-dim)', backdropFilter: 'blur(16px)' }}>
        <div className="flex items-center gap-3 px-4 py-3" style={{ borderBottom: '1px solid var(--border-dim)', background: 'rgba(0,5,12,0.5)' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--red)" strokeWidth="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          <span className="card-title">Active Alerts</span>
          <span className="tag" style={{ background: 'rgba(255,45,85,0.1)', color: 'var(--red)', border: '1px solid rgba(255,45,85,0.2)', fontSize: 9 }}>
            {alerts.filter(a => !a._acked).length} UNACKED
          </span>
          {hasAlerts && (
            <button className="ml-auto text-xs px-2 py-1 rounded transition-all"
              style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', border: '1px solid var(--border-dim)' }}
              onClick={ackAll}
              onMouseEnter={e => { e.currentTarget.style.color = 'var(--cyan)'; e.currentTarget.style.borderColor = 'var(--border-mid)'; }}
              onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-lo)'; e.currentTarget.style.borderColor = 'var(--border-dim)'; }}>
              ACK ALL
            </button>
          )}
        </div>

        {!hasAlerts ? (
          <div className="flex flex-col items-center justify-center py-12 gap-3">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--text-lo)" strokeWidth="1.5">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', textAlign: 'center', maxWidth: 200 }}>
              {backendError ? 'Backend offline — start Flask server' : 'No alerts yet — start packet capture'}
            </span>
          </div>
        ) : (
          <div style={{ maxHeight: 440, overflowY: 'auto' }}>
            {alerts.map((alert) => {
              const sc = ALERT_SEV[alert.severity] ?? ALERT_SEV.low;
              const dot = DOT_CLASS[alert.severity] ?? 'pulse-cyan';
              const acked = !!alert._acked;
              return (
                <div key={alert.id}
                  className="px-4 py-3 transition-all"
                  style={{
                    borderBottom: '1px solid rgba(0,212,255,0.03)',
                    background: acked ? 'transparent' : sc.bg,
                    opacity: acked ? 0.4 : 1,
                    transition: 'all 0.4s ease',
                  }}>
                  <div className="flex items-start gap-3">
                    <span className={`pulse-dot ${dot} mt-1 flex-shrink-0`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="tag" style={{ background: sc.bg, color: sc.color, border: `1px solid ${sc.border}`, fontSize: 9, fontFamily: 'var(--font-display)', letterSpacing: '0.1em' }}>
                          {alert.severity.toUpperCase()}
                        </span>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>{alert.id}</span>
                      </div>
                      <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-mid)', lineHeight: 1.5 }}>{alert.message}</p>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', display: 'block', marginTop: 3 }}>{alert.time}</span>
                    </div>
                    <button
                      disabled={acked}
                      onClick={() => ack(alert.id)}
                      className="flex-shrink-0 text-xs px-2 py-1 rounded transition-all"
                      style={{
                        fontFamily: 'var(--font-mono)', fontSize: 9,
                        background: acked ? 'transparent' : 'rgba(0,212,255,0.07)',
                        color: acked ? 'var(--text-lo)' : 'var(--cyan)',
                        border: acked ? '1px solid transparent' : '1px solid rgba(0,212,255,0.2)',
                        cursor: acked ? 'default' : 'pointer',
                      }}>
                      {acked ? '✓ ACK' : 'ACK'}
                    </button>
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
