'use client';

import { useState, useEffect, useRef } from 'react';
import { getLiveEvents, getThreatDistribution, getCaptureStatus, type LiveEvent, type ThreatDistItem } from '../../../lib/api';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const SEV: Record<string, { color: string; bg: string; border: string }> = {
  critical: { color: 'var(--purple)', bg: 'rgba(191,95,255,0.07)', border: 'rgba(191,95,255,0.2)' },
  high:     { color: 'var(--red)',    bg: 'rgba(255,45,85,0.07)',  border: 'rgba(255,45,85,0.2)' },
  medium:   { color: 'var(--amber)',  bg: 'rgba(255,176,32,0.07)', border: 'rgba(255,176,32,0.2)' },
  low:      { color: 'var(--cyan)',   bg: 'rgba(0,212,255,0.07)',  border: 'rgba(0,212,255,0.2)' },
};

export default function ThreatsPage() {
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [dist, setDist] = useState<ThreatDistItem[]>([]);
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [backendError, setBackendError] = useState<string | null>(null);
  const [newIds, setNewIds] = useState<Set<string>>(new Set());
  const prevIds = useRef<Set<string>>(new Set());

  useEffect(() => {
    let cancelled = false;
    async function fetchData() {
      try {
        const [evData, distData] = await Promise.all([
          getLiveEvents(200),
          getThreatDistribution(),
        ]);
        if (cancelled) return;
        setBackendError(null);
        const incoming = evData.events;
        const fresh = new Set(incoming.map(e => e.id).filter(id => !prevIds.current.has(id)));
        incoming.forEach(e => prevIds.current.add(e.id));
        if (fresh.size > 0) {
          setNewIds(prev => new Set([...prev, ...fresh]));
          setTimeout(() => setNewIds(prev => { const n = new Set(prev); fresh.forEach(id => n.delete(id)); return n; }), 2000);
        }
        setEvents(incoming);
        setDist(distData.distribution);
      } catch (err) {
        if (!cancelled) setBackendError((err as Error).message);
      }
    }
    fetchData();
    const id = setInterval(fetchData, 3000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const threats = events.filter(e => e.predicted_label.toUpperCase() !== 'BENIGN');
  const filtered = severityFilter === 'all' ? threats : threats.filter(e => e.severity === severityFilter);

  const topSrcs = Object.entries(
    threats.reduce<Record<string, number>>((a, e) => {
      if (e.source_ip) a[e.source_ip] = (a[e.source_ip] ?? 0) + 1; return a;
    }, {})
  ).sort(([,a],[,b]) => b - a).slice(0, 8);

  const stats = {
    total: threats.length,
    critical: threats.filter(e => e.severity === 'critical').length,
    high: threats.filter(e => e.severity === 'high').length,
    medium: threats.filter(e => e.severity === 'medium').length,
    blocked: threats.filter(e => e.action === 'Block' || e.action === 'Quarantine').length,
  };

  return (
    <>
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="section-label mb-2">Intrusion Detection</div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 800, color: 'var(--text-hi)', letterSpacing: '0.03em', lineHeight: 1 }}>
            Threat Analysis
          </h1>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', marginTop: 4 }}>
            CICIDS2017 classification · 13 attack classes · Random Forest
          </p>
        </div>
        <div className="tag"
          style={{
            background: threats.length > 0 ? 'rgba(255,45,85,0.08)' : 'rgba(0,255,157,0.06)',
            color: threats.length > 0 ? 'var(--red)' : 'var(--green)',
            border: `1px solid ${threats.length > 0 ? 'rgba(255,45,85,0.25)' : 'rgba(0,255,157,0.2)'}`,
            fontFamily: 'var(--font-display)', fontSize: 9, letterSpacing: '0.1em', padding: '5px 12px',
          }}>
          <span className={`pulse-dot ${threats.length > 0 ? 'pulse-red' : 'pulse-green'}`} style={{ width: 4, height: 4 }} />
          {threats.length > 0 ? `${threats.length} THREATS ACTIVE` : 'ALL CLEAR'}
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-5">
        {[
          { l: 'Total Threats', v: stats.total, c: 'var(--red)' },
          { l: 'Critical',      v: stats.critical, c: 'var(--purple)' },
          { l: 'High',          v: stats.high, c: 'var(--red)' },
          { l: 'Medium',        v: stats.medium, c: 'var(--amber)' },
          { l: 'Blocked',       v: stats.blocked, c: 'var(--green)' },
        ].map(s => (
          <div key={s.l} className="rounded-xl p-4 bracket-all"
            style={{ background: 'rgba(3,10,22,0.90)', border: '1px solid var(--border-dim)', backdropFilter: 'blur(16px)' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '0.12em', marginBottom: 4 }}>{s.l}</div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 800, color: s.c, lineHeight: 1 }}>{s.v}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-5">
        {/* Attack distribution pie */}
        <div className="rounded-xl p-4 bracket-all"
          style={{ background: 'rgba(3,10,22,0.90)', border: '1px solid var(--border-dim)', backdropFilter: 'blur(16px)' }}>
          <div className="card-header mb-3">
            <span className="card-title">Attack Distribution</span>
          </div>
          {dist.length === 0 ? (
            <div className="flex items-center justify-center" style={{ height: 200 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', textAlign: 'center' }}>
                {backendError ? 'Backend offline' : 'No data — start capture'}
              </span>
            </div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie data={dist} dataKey="count" nameKey="name" cx="50%" cy="50%" outerRadius={70} strokeWidth={0}>
                    {dist.map((d, i) => <Cell key={i} fill={d.color} />)}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: 'rgba(0,8,18,0.95)', border: '1px solid rgba(0,212,255,0.2)', borderRadius: 8, fontFamily: 'JetBrains Mono', fontSize: 10 }}
                    formatter={(v, name) => [`${v} events`, name as string]}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-1 mt-2">
                {dist.slice(0, 5).map(d => (
                  <div key={d.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: d.color }} />
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-mid)' }}>{d.name}</span>
                    </div>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>{d.percentage}%</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Top attacking IPs */}
        <div className="rounded-xl p-4 bracket-all"
          style={{ background: 'rgba(3,10,22,0.90)', border: '1px solid var(--border-dim)', backdropFilter: 'blur(16px)' }}>
          <div className="card-header mb-3">
            <span className="card-title">Top Threat Sources</span>
          </div>
          {topSrcs.length === 0 ? (
            <div className="flex items-center justify-center" style={{ height: 200 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)' }}>No threat sources</span>
            </div>
          ) : (
            <div className="space-y-3">
              {topSrcs.map(([ip, cnt], i) => {
                const max = topSrcs[0][1];
                return (
                  <div key={ip}>
                    <div className="flex justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>#{i + 1}</span>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--red)' }}>{ip}</span>
                      </div>
                      <span style={{ fontFamily: 'var(--font-display)', fontSize: 12, fontWeight: 700, color: 'var(--text-hi)' }}>{cnt}</span>
                    </div>
                    <div className="track" style={{ height: 3 }}>
                      <div className="track-fill" style={{ width: `${(cnt / max) * 100}%`, background: 'var(--red)', transition: 'width 0.8s' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Severity breakdown */}
        <div className="rounded-xl p-4 bracket-all"
          style={{ background: 'rgba(3,10,22,0.90)', border: '1px solid var(--border-dim)', backdropFilter: 'blur(16px)' }}>
          <div className="card-header mb-3">
            <span className="card-title">Severity Breakdown</span>
          </div>
          {(['critical','high','medium','low'] as const).map(sev => {
            const cnt = threats.filter(e => e.severity === sev).length;
            const pct = threats.length > 0 ? Math.round(cnt / threats.length * 100) : 0;
            const cfg = SEV[sev];
            return (
              <div key={sev} className="mb-3">
                <div className="flex justify-between mb-1">
                  <span className="tag" style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}`, fontSize: 9 }}>
                    {sev.toUpperCase()}
                  </span>
                  <div className="flex items-center gap-2">
                    <span style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 700, color: cfg.color }}>{cnt}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>{pct}%</span>
                  </div>
                </div>
                <div className="track" style={{ height: 4 }}>
                  <div className="track-fill" style={{ width: `${pct}%`, background: cfg.color, transition: 'width 0.8s' }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Full threat feed */}
      <div className="rounded-xl overflow-hidden bracket-all mb-5"
        style={{ background: 'rgba(3,10,22,0.90)', border: '1px solid var(--border-dim)', backdropFilter: 'blur(16px)' }}>
        <div className="flex flex-wrap items-center gap-3 px-4 py-3"
          style={{ borderBottom: '1px solid var(--border-dim)', background: 'rgba(0,5,12,0.5)' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--red)" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
          <span className="card-title">Threat Event Log</span>
          <div className="flex gap-1">
            {(['all','critical','high','medium','low'] as const).map(s => (
              <button key={s} onClick={() => setSeverityFilter(s)}
                className="tag transition-all"
                style={{
                  fontSize: 9, cursor: 'pointer',
                  background: severityFilter === s ? (SEV[s]?.bg ?? 'rgba(0,212,255,0.12)') : 'rgba(255,255,255,0.03)',
                  color: severityFilter === s ? (SEV[s]?.color ?? 'var(--cyan)') : 'var(--text-lo)',
                  border: `1px solid ${severityFilter === s ? (SEV[s]?.border ?? 'rgba(0,212,255,0.3)') : 'rgba(255,255,255,0.06)'}`,
                }}>
                {s.toUpperCase()}
              </button>
            ))}
          </div>
          <span className="ml-auto tag" style={{ background: 'rgba(255,45,85,0.06)', color: 'var(--red)', border: '1px solid rgba(255,45,85,0.15)', fontSize: 9 }}>
            {filtered.length} events
          </span>
        </div>

        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16">
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', textAlign: 'center' }}>
              {backendError ? 'Backend offline' : threats.length === 0 ? 'No threats detected yet — start capture from Overview' : `No ${severityFilter} threats`}
            </span>
          </div>
        ) : (
          <div style={{ maxHeight: 480, overflowY: 'auto', overflowX: 'auto' }}>
            <table className="w-full data-table" style={{ minWidth: 900 }}>
              <thead style={{ position: 'sticky', top: 0, background: 'rgba(0,5,14,0.98)', zIndex: 2 }}>
                <tr>
                  {['Time','Source IP','Dest IP','Attack Type','Confidence','Severity','Trust','Action','Reason'].map(h => (
                    <th key={h} className="text-left">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((e, i) => {
                  const sc = SEV[e.severity] ?? SEV.low;
                  const isNew = newIds.has(e.id);
                  return (
                    <tr key={e.id}
                      style={{
                        animation: isNew ? 'data-in 0.3s ease both' : 'none',
                        background: isNew ? 'rgba(255,45,85,0.02)' : 'transparent',
                        opacity: i > 60 ? Math.max(0.3, 1 - (i - 60) * 0.01) : 1,
                      }}>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', whiteSpace: 'nowrap' }}>{e.timestamp}</td>
                      <td style={{ color: 'var(--red)', fontFamily: 'var(--font-mono)', fontSize: 10 }}>{e.source_ip ?? '?'}</td>
                      <td style={{ color: 'var(--text-mid)' }}>{e.dest_ip ?? '?'}</td>
                      <td>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--amber)', fontWeight: 600 }}>
                          {isNew && <span style={{ color: 'var(--red)', marginRight: 4 }}>▶</span>}
                          {e.predicted_label}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-mid)' }}>
                        {(e.confidence * 100).toFixed(1)}%
                      </td>
                      <td>
                        <span className="tag" style={{ background: sc.bg, color: sc.color, border: `1px solid ${sc.border}`, fontSize: 9 }}>
                          {e.severity.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: e.trust_score < 50 ? 'var(--red)' : 'var(--text-mid)' }}>
                        {e.trust_score.toFixed(1)}
                      </td>
                      <td>
                        <span className="tag" style={{
                          fontSize: 9,
                          background: e.action === 'Block' ? 'rgba(255,45,85,0.1)' : e.action === 'Alert' ? 'rgba(255,176,32,0.1)' : 'rgba(255,255,255,0.04)',
                          color: e.action === 'Block' ? 'var(--red)' : e.action === 'Alert' ? 'var(--amber)' : 'var(--text-lo)',
                          border: '1px solid rgba(255,255,255,0.06)',
                        }}>
                          {e.action}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {e.reason}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        <div className="flex justify-between px-4 py-2" style={{ borderTop: '1px solid var(--border-dim)', background: 'rgba(0,5,12,0.4)' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
            {filtered.length} of {threats.length} threats shown · {events.length} total events
          </span>
        </div>
      </div>

      <div style={{ height: 40 }} />
    </>
  );
}
