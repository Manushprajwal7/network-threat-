'use client';

import { useState, useEffect } from 'react';
import { getSecurityDecisions, getRecentAlerts, getLiveEvents, type Alert, type LiveEvent } from '../../../lib/api';

const DEC_CFG: Record<string, { color: string; bg: string; border: string; icon: string; desc: string }> = {
  allow:      { color: 'var(--green)',  bg: 'rgba(0,255,157,0.06)',  border: 'rgba(0,255,157,0.2)',  icon: '✓', desc: 'Traffic cleared through all security layers' },
  restrict:   { color: 'var(--cyan)',   bg: 'rgba(0,212,255,0.06)',  border: 'rgba(0,212,255,0.2)',  icon: '⊘', desc: 'Rate-limited — bandwidth throttled' },
  alert:      { color: 'var(--amber)',  bg: 'rgba(255,176,32,0.06)', border: 'rgba(255,176,32,0.2)', icon: '▲', desc: 'Flagged for SOC analyst review' },
  quarantine: { color: '#ff8c42',       bg: 'rgba(255,140,66,0.06)', border: 'rgba(255,140,66,0.2)', icon: '⬡', desc: 'Isolated in sandboxed VLAN segment' },
  block:      { color: 'var(--red)',    bg: 'rgba(255,45,85,0.06)',  border: 'rgba(255,45,85,0.2)',  icon: '✕', desc: 'Dropped — source IP blacklisted' },
};

const SEV_CFG: Record<string, { color: string; bg: string; border: string }> = {
  critical: { color: 'var(--purple)', bg: 'rgba(191,95,255,0.06)', border: 'rgba(191,95,255,0.2)' },
  high:     { color: 'var(--red)',    bg: 'rgba(255,45,85,0.06)',  border: 'rgba(255,45,85,0.2)' },
  medium:   { color: 'var(--amber)',  bg: 'rgba(255,176,32,0.06)', border: 'rgba(255,176,32,0.2)' },
  low:      { color: 'var(--cyan)',   bg: 'rgba(0,212,255,0.06)',  border: 'rgba(0,212,255,0.2)' },
};

export default function DecisionsPage() {
  const [decisions, setDecisions] = useState<Record<string, { count: number; percentage: number; trend?: string }>>({});
  const [alerts, setAlerts] = useState<(Alert & { _acked?: boolean })[]>([]);
  const [recentEvents, setRecentEvents] = useState<LiveEvent[]>([]);
  const [backendError, setBackendError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchData() {
      try {
        const [decData, alertData, evData] = await Promise.all([
          getSecurityDecisions(),
          getRecentAlerts(50),
          getLiveEvents(30),
        ]);
        if (cancelled) return;
        setBackendError(null);
        setDecisions(decData.decisions);
        setAlerts(prev => {
          const ackedIds = new Set(prev.filter(a => a._acked).map(a => a.id));
          return alertData.alerts.map(a => ({ ...a, _acked: ackedIds.has(a.id) }));
        });
        setRecentEvents(evData.events);
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
  const unacked = alerts.filter(a => !a._acked).length;

  return (
    <>
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="section-label mb-2">Policy Enforcement</div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 800, color: 'var(--text-hi)', letterSpacing: '0.03em', lineHeight: 1 }}>
            Security Decisions
          </h1>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', marginTop: 4 }}>
            Zero-trust decision engine · live enforcement · 3s refresh
          </p>
        </div>
        {unacked > 0 && (
          <div className="tag"
            style={{ background: 'rgba(255,45,85,0.08)', color: 'var(--red)', border: '1px solid rgba(255,45,85,0.25)', fontFamily: 'var(--font-display)', fontSize: 10, letterSpacing: '0.1em', padding: '5px 12px' }}>
            <span className="pulse-dot pulse-red" style={{ width: 4, height: 4 }} />
            {unacked} UNACKNOWLEDGED
          </div>
        )}
      </div>

      {/* Decision counters */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-5">
        {(Object.entries(DEC_CFG) as Array<[keyof typeof DEC_CFG, (typeof DEC_CFG)[keyof typeof DEC_CFG]]>).map(([key, cfg]) => {
          const d = decisions[key] ?? { count: 0, percentage: 0 };
          return (
            <div key={key} className="rounded-xl p-4 bracket-all"
              style={{ background: 'rgba(3,10,22,0.90)', border: `1px solid ${cfg.border}`, backdropFilter: 'blur(16px)' }}>
              <div className="flex items-center gap-2 mb-2">
                <span className="w-6 h-6 rounded flex items-center justify-center text-xs"
                  style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}` }}>
                  {cfg.icon}
                </span>
                <span style={{ fontFamily: 'var(--font-display)', fontSize: 9, fontWeight: 700, color: cfg.color, letterSpacing: '0.1em' }}>
                  {key.toUpperCase()}
                </span>
              </div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 800, color: 'var(--text-hi)', lineHeight: 1 }}>{d.count}</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', marginTop: 4 }}>{d.percentage?.toFixed(1) ?? 0}% of total</div>
              <div className="track mt-2" style={{ height: 3 }}>
                <div className="track-fill" style={{ width: `${d.percentage ?? 0}%`, background: cfg.color, transition: 'width 0.8s' }} />
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        {/* Decision engine panel */}
        <div className="rounded-xl p-4 bracket-all"
          style={{ background: 'rgba(3,10,22,0.90)', border: '1px solid var(--border-dim)', backdropFilter: 'blur(16px)' }}>
          <div className="card-header mb-4">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <span className="card-title">Decision Engine Breakdown</span>
            <span className="ml-auto" style={{ fontFamily: 'var(--font-display)', fontSize: 14, color: 'var(--cyan)' }}>
              {total > 0 ? total.toLocaleString() : '—'} total
            </span>
          </div>

          {!hasDecisions ? (
            <div className="flex items-center justify-center py-12">
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', textAlign: 'center' }}>
                {backendError ? 'Backend offline' : 'No decisions yet — start capture from Overview'}
              </span>
            </div>
          ) : (
            <div className="space-y-3">
              {(Object.entries(DEC_CFG) as Array<[string, typeof DEC_CFG[string]]>).map(([key, cfg]) => {
                const d = decisions[key] ?? { count: 0, percentage: 0 };
                return (
                  <div key={key} className="rounded-lg p-3 transition-all"
                    style={{ background: 'rgba(255,255,255,0.015)', border: `1px solid ${cfg.border}` }}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded flex items-center justify-center"
                          style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}` }}>
                          {cfg.icon}
                        </span>
                        <div>
                          <div style={{ fontFamily: 'var(--font-display)', fontSize: 10, fontWeight: 700, color: cfg.color, letterSpacing: '0.1em' }}>
                            {key.toUpperCase()}
                          </div>
                          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>{cfg.desc}</div>
                        </div>
                      </div>
                      <div style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 800, color: 'var(--text-hi)' }}>
                        {d.count}
                      </div>
                    </div>
                    <div className="track" style={{ height: 3 }}>
                      <div className="track-fill" style={{ width: `${d.percentage ?? 0}%`, background: cfg.color, transition: 'width 0.8s' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Recent decision log */}
        <div className="rounded-xl overflow-hidden bracket-all"
          style={{ background: 'rgba(3,10,22,0.90)', border: '1px solid var(--border-dim)', backdropFilter: 'blur(16px)' }}>
          <div className="flex items-center gap-3 px-4 py-3"
            style={{ borderBottom: '1px solid var(--border-dim)', background: 'rgba(0,5,12,0.5)' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
            <span className="card-title">Recent Policy Log</span>
          </div>
          {recentEvents.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)' }}>
                {backendError ? 'Backend offline' : 'No events yet'}
              </span>
            </div>
          ) : (
            <div style={{ maxHeight: 380, overflowY: 'auto' }}>
              {recentEvents.map(e => {
                const actionColor = e.action === 'Block' ? 'var(--red)' : e.action === 'Alert' ? 'var(--amber)' : e.action === 'Quarantine' ? '#ff8c42' : e.action === 'Restrict' ? 'var(--cyan)' : 'var(--green)';
                return (
                  <div key={e.id} className="px-4 py-3 transition-all"
                    style={{ borderBottom: '1px solid rgba(0,212,255,0.03)' }}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span style={{ fontFamily: 'var(--font-display)', fontSize: 10, fontWeight: 700, color: actionColor }}>
                          {e.action.toUpperCase()}
                        </span>
                        <span className="tag" style={{ fontSize: 9, background: 'rgba(255,255,255,0.03)', color: 'var(--text-lo)', border: '1px solid rgba(255,255,255,0.05)' }}>
                          {e.protocol}
                        </span>
                      </div>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>{e.timestamp.slice(11)}</span>
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-mid)' }}>
                      {e.source_ip ?? '?'} → {e.dest_ip ?? '?'}
                    </div>
                    {e.reason && (
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', marginTop: 2 }}>{e.reason}</div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Alert queue */}
      <div className="rounded-xl overflow-hidden bracket-all mb-5"
        style={{ background: 'rgba(3,10,22,0.90)', border: '1px solid var(--border-dim)', backdropFilter: 'blur(16px)' }}>
        <div className="flex items-center gap-3 px-4 py-3"
          style={{ borderBottom: '1px solid var(--border-dim)', background: 'rgba(0,5,12,0.5)' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--red)" strokeWidth="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          <span className="card-title">Alert Queue</span>
          <span className="tag" style={{ background: 'rgba(255,45,85,0.08)', color: 'var(--red)', border: '1px solid rgba(255,45,85,0.15)', fontSize: 9 }}>
            {unacked} UNACKED
          </span>
          {alerts.length > 0 && (
            <button className="ml-auto tag transition-all" onClick={ackAll}
              style={{ fontSize: 9, cursor: 'pointer', color: 'var(--text-lo)', border: '1px solid var(--border-dim)' }}
              onMouseEnter={e => { e.currentTarget.style.color = 'var(--cyan)'; }}
              onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-lo)'; }}>
              ACK ALL
            </button>
          )}
        </div>

        {alerts.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', textAlign: 'center' }}>
              {backendError ? 'Backend offline' : 'No alerts yet — threats will appear here'}
            </span>
          </div>
        ) : (
          <div style={{ maxHeight: 440, overflowY: 'auto' }}>
            {alerts.map(alert => {
              const sc = SEV_CFG[alert.severity] ?? SEV_CFG.low;
              return (
                <div key={alert.id} className="px-4 py-3 transition-all"
                  style={{
                    borderBottom: '1px solid rgba(0,212,255,0.03)',
                    background: alert._acked ? 'transparent' : sc.bg,
                    opacity: alert._acked ? 0.4 : 1,
                    transition: 'all 0.4s ease',
                  }}>
                  <div className="flex items-start gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="tag" style={{ background: sc.bg, color: sc.color, border: `1px solid ${sc.border}`, fontSize: 9 }}>
                          {alert.severity.toUpperCase()}
                        </span>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>{alert.id}</span>
                      </div>
                      <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-mid)' }}>{alert.message}</p>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', display: 'block', marginTop: 2 }}>{alert.time}</span>
                    </div>
                    <button disabled={!!alert._acked} onClick={() => ack(alert.id)}
                      className="flex-shrink-0 tag transition-all"
                      style={{
                        fontSize: 9, cursor: alert._acked ? 'default' : 'pointer',
                        background: alert._acked ? 'transparent' : 'rgba(0,212,255,0.07)',
                        color: alert._acked ? 'var(--text-lo)' : 'var(--cyan)',
                        border: alert._acked ? '1px solid transparent' : '1px solid rgba(0,212,255,0.2)',
                      }}>
                      {alert._acked ? '✓ ACK' : 'ACK'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="px-4 py-2" style={{ borderTop: '1px solid var(--border-dim)', background: 'rgba(0,5,12,0.4)' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
            {alerts.length} alerts · {unacked} unacknowledged · 3s refresh
          </span>
        </div>
      </div>

      <div style={{ height: 40 }} />
    </>
  );
}
