'use client';

import { useState, useEffect, useRef } from 'react';
import { getNetworkFlows, getCaptureStatus, getTrafficTrend, type NetworkFlow, type CaptureStatus } from '../../../lib/api';
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';

const STATUS_CFG: Record<string, { color: string; bg: string; label: string }> = {
  allowed:    { color: 'var(--green)',  bg: 'rgba(5,150,105,0.09)',  label: 'ALLOWED' },
  blocked:    { color: 'var(--red)',    bg: 'rgba(220,38,38,0.09)',  label: 'BLOCKED' },
  alerted:    { color: 'var(--amber)',  bg: 'rgba(217,119,6,0.09)', label: 'ALERTED' },
  quarantined:{ color: '#ea6c1a',       bg: 'rgba(255,140,66,0.07)', label: 'QUARANTINE' },
  restricted: { color: 'var(--cyan)',   bg: 'rgba(2,132,199,0.09)',  label: 'RESTRICTED' },
};

const PROTO_COLORS: Record<string, string> = {
  TCP: 'var(--cyan)', UDP: 'var(--purple)', ICMP: 'var(--amber)',
  DNS: 'var(--green)', HTTP: '#ea6c1a', HTTPS: '#0284c7', UNKNOWN: 'var(--text-lo)',
};

export default function MonitorPage() {
  const [flows, setFlows] = useState<NetworkFlow[]>([]);
  const [status, setStatus] = useState<CaptureStatus | null>(null);
  const [trend, setTrend] = useState<{ time: string; normal: number; threats: number }[]>([]);
  const [filter, setFilter] = useState<'all' | 'allowed' | 'blocked' | 'alerted' | 'quarantined' | 'restricted'>('all');
  const [protoFilter, setProtoFilter] = useState('all');
  const [backendError, setBackendError] = useState<string | null>(null);
  const [newIds, setNewIds] = useState<Set<string>>(new Set());
  const prevIds = useRef<Set<string>>(new Set());

  useEffect(() => {
    let cancelled = false;
    async function fetchData() {
      try {
        const [flowData, statusData, trendData] = await Promise.all([
          getNetworkFlows(100),
          getCaptureStatus(),
          getTrafficTrend(),
        ]);
        if (cancelled) return;
        setBackendError(null);
        const incoming = flowData.flows;
        const fresh = new Set(incoming.map(f => f.id).filter(id => !prevIds.current.has(id)));
        incoming.forEach(f => prevIds.current.add(f.id));
        if (fresh.size > 0) {
          setNewIds(prev => new Set([...prev, ...fresh]));
          setTimeout(() => setNewIds(prev => { const n = new Set(prev); fresh.forEach(id => n.delete(id)); return n; }), 2000);
        }
        setFlows(incoming);
        setStatus(statusData);
        setTrend(trendData.trend);
      } catch (err) {
        if (!cancelled) setBackendError((err as Error).message);
      }
    }
    fetchData();
    const id = setInterval(fetchData, 3000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const protos = ['all', ...Array.from(new Set(flows.map(f => f.protocol)))];
  const filtered = flows
    .filter(f => filter === 'all' || f.status === filter)
    .filter(f => protoFilter === 'all' || f.protocol === protoFilter);

  const protoCounts = flows.reduce<Record<string, number>>((acc, f) => {
    acc[f.protocol] = (acc[f.protocol] ?? 0) + 1; return acc;
  }, {});

  return (
    <>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="section-label mb-2">Live Network Traffic</div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 800, color: 'var(--text-hi)', letterSpacing: '0.03em', lineHeight: 1 }}>
            Net Monitor
          </h1>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', marginTop: 4 }}>
            Real-time packet flow analysis · 3s refresh · tshark capture
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="tag"
            style={{
              background: status?.is_running ? 'rgba(5,150,105,0.09)' : 'rgba(0,0,0,0.10)',
              color: status?.is_running ? 'var(--green)' : 'var(--text-lo)',
              border: `1px solid ${status?.is_running ? 'rgba(5,150,105,0.28)' : 'rgba(0,0,0,0.20)'}`,
              fontFamily: 'var(--font-display)', fontSize: 9, letterSpacing: '0.1em', padding: '5px 10px',
            }}>
            <span className={`pulse-dot ${status?.is_running ? 'pulse-green' : 'pulse-amber'}`} style={{ width: 4, height: 4 }} />
            {status?.is_running ? 'CAPTURING' : 'IDLE'}
          </div>
        </div>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
        {[
          { l: 'Packets Captured', v: status?.packets_captured.toLocaleString() ?? '—', c: 'var(--cyan)' },
          { l: 'Events Analyzed',  v: status?.events_analyzed.toLocaleString() ?? '—',  c: 'var(--purple)' },
          { l: 'Active Flows',     v: filtered.length.toLocaleString(),                  c: 'var(--green)' },
          { l: 'Uptime',           v: status?.uptime_seconds ? `${status.uptime_seconds}s` : '—', c: 'var(--amber)' },
        ].map(s => (
          <div key={s.l} className="rounded-xl p-4 bracket-all"
            style={{ background: '#ffffff', border: '1px solid #000000', backdropFilter: 'blur(16px)', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '0.12em', marginBottom: 4 }}>{s.l}</div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 800, color: s.c, lineHeight: 1 }}>{s.v}</div>
          </div>
        ))}
      </div>

      {/* Traffic trend chart */}
      {trend.length > 0 && (
        <div className="rounded-xl p-4 bracket-all mb-5"
          style={{ background: '#ffffff', border: '1px solid #000000', backdropFilter: 'blur(16px)', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
          <div className="card-header mb-3">
            <span className="card-title">Traffic Trend — 12m Rolling Window</span>
          </div>
          <ResponsiveContainer width="100%" height={120}>
            <AreaChart data={trend} margin={{ top: 5, right: 10, left: -30, bottom: 0 }}>
              <defs>
                <linearGradient id="gNorm" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0284c7" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#0284c7" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="gThreat" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#dc2626" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#dc2626" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="time" tick={{ fontFamily: 'JetBrains Mono', fontSize: 9, fill: '#4a5a6a' }} />
              <YAxis tick={{ fontFamily: 'JetBrains Mono', fontSize: 9, fill: '#4a5a6a' }} />
              <Tooltip
                contentStyle={{ background: 'rgba(255,255,255,0.96)', border: '1px solid rgba(2,132,199,0.22)', borderRadius: 8, fontFamily: 'JetBrains Mono', fontSize: 11 }}
                labelStyle={{ color: '#0284c7' }} itemStyle={{ color: '#8b9aaa' }}
              />
              <Area type="monotone" dataKey="normal" stroke="#0284c7" strokeWidth={1.5} fill="url(#gNorm)" name="Normal" />
              <Area type="monotone" dataKey="threats" stroke="#dc2626" strokeWidth={1.5} fill="url(#gThreat)" name="Threats" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-5 mb-5">
        {/* Protocol breakdown */}
        <div className="rounded-xl p-4 bracket-all"
          style={{ background: '#ffffff', border: '1px solid #000000', backdropFilter: 'blur(16px)', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
          <div className="card-header mb-3">
            <span className="card-title">Protocol Mix</span>
          </div>
          <div className="space-y-2">
            {Object.entries(protoCounts).sort(([,a],[,b]) => b - a).map(([proto, cnt]) => {
              const total = flows.length || 1;
              const pct = Math.round(cnt / total * 100);
              const color = PROTO_COLORS[proto] ?? 'var(--text-lo)';
              return (
                <div key={proto}>
                  <div className="flex justify-between mb-1">
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color }}>{proto}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)' }}>{cnt} · {pct}%</span>
                  </div>
                  <div className="track" style={{ height: 3 }}>
                    <div className="track-fill" style={{ width: `${pct}%`, background: color, transition: 'width 0.8s' }} />
                  </div>
                </div>
              );
            })}
            {Object.keys(protoCounts).length === 0 && (
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', textAlign: 'center', paddingTop: 20 }}>
                No flows yet
              </p>
            )}
          </div>
        </div>

        {/* Flow table */}
        <div className="xl:col-span-3 rounded-xl overflow-hidden bracket-all"
          style={{ background: '#ffffff', border: '1px solid #000000', backdropFilter: 'blur(16px)', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-2 px-4 py-3"
            style={{ borderBottom: '1px solid var(--border-dim)', background: 'rgba(0,0,0,0.05)' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="2">
              <circle cx="12" cy="12" r="2"/>
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
            <span className="card-title mr-2">Flow Table</span>
            <div className="flex gap-1 flex-wrap">
              {(['all','allowed','blocked','alerted','quarantined','restricted'] as const).map(s => (
                <button key={s} onClick={() => setFilter(s)}
                  className="tag transition-all"
                  style={{
                    fontSize: 9, cursor: 'pointer',
                    background: filter === s ? 'rgba(2,132,199,0.15)' : 'rgba(0,0,0,0.10)',
                    color: filter === s ? 'var(--cyan)' : 'var(--text-lo)',
                    border: `1px solid ${filter === s ? 'rgba(2,132,199,0.32)' : 'rgba(0,0,0,0.20)'}`,
                  }}>
                  {s.toUpperCase()}
                </button>
              ))}
            </div>
            <div className="flex gap-1 flex-wrap ml-auto">
              {protos.slice(0, 6).map(p => (
                <button key={p} onClick={() => setProtoFilter(p)}
                  className="tag transition-all"
                  style={{
                    fontSize: 9, cursor: 'pointer',
                    background: protoFilter === p ? 'rgba(124,58,237,0.15)' : 'rgba(0,0,0,0.10)',
                    color: protoFilter === p ? 'var(--purple)' : 'var(--text-lo)',
                    border: `1px solid ${protoFilter === p ? 'rgba(124,58,237,0.32)' : 'rgba(0,0,0,0.20)'}`,
                  }}>
                  {p.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', textAlign: 'center' }}>
                {backendError ? 'Backend offline — start Flask server' : 'No flows — start capture from the Overview page'}
              </span>
            </div>
          ) : (
            <div style={{ maxHeight: 520, overflowY: 'auto', overflowX: 'auto' }}>
              <table className="w-full data-table" style={{ minWidth: 760 }}>
                <thead style={{ position: 'sticky', top: 0, background: 'rgba(0,0,0,0.08)', zIndex: 2 }}>
                  <tr>
                    {['Flow ID','Source IP','Dest IP','Proto','Bytes','Attack Type','Action'].map(h => (
                      <th key={h} className="text-left">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((flow, i) => {
                    const sc = STATUS_CFG[flow.status] ?? STATUS_CFG.alerted;
                    const isNew = newIds.has(flow.id);
                    return (
                      <tr key={flow.id}
                        style={{
                          animation: isNew ? 'data-in 0.3s ease both' : 'none',
                          background: isNew ? 'rgba(2,132,199,0.05)' : 'transparent',
                          opacity: i > 40 ? Math.max(0.3, 1 - (i - 40) * 0.02) : 1,
                        }}>
                        <td style={{ color: 'var(--text-lo)', fontFamily: 'var(--font-mono)', fontSize: 10 }}>
                          {isNew && <span style={{ color: 'var(--green)', marginRight: 4 }}>▶</span>}
                          {flow.id}
                        </td>
                        <td style={{ color: 'var(--text-mid)' }}>{flow.srcIP}</td>
                        <td style={{ color: 'var(--text-mid)' }}>{flow.dstIP}</td>
                        <td>
                          <span className="tag" style={{
                            background: 'rgba(0,0,0,0.12)', fontSize: 9,
                            color: PROTO_COLORS[flow.protocol] ?? 'var(--text-lo)',
                            border: '1px solid rgba(0,0,0,0.20)',
                          }}>
                            {flow.protocol}
                          </span>
                        </td>
                        <td style={{ color: 'var(--text-lo)', fontSize: 10 }}>{flow.bytes}</td>
                        <td>
                          <span style={{
                            fontFamily: 'var(--font-mono)', fontSize: 10,
                            color: flow.attackType === 'BENIGN' ? 'var(--green)' : 'var(--amber)',
                          }}>
                            {flow.attackType}
                          </span>
                        </td>
                        <td>
                          <span className="tag" style={{ background: sc.bg, color: sc.color, border: `1px solid ${sc.color}25`, fontSize: 9 }}>
                            {sc.label}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          <div className="flex justify-between px-4 py-2" style={{ borderTop: '1px solid var(--border-dim)', background: 'rgba(0,0,0,0.03)' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
              {filtered.length} of {flows.length} flows shown · 3s refresh
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: flows.length > 0 ? 'var(--green)' : 'var(--text-lo)' }}>
              {flows.length > 0 ? '● LIVE' : '○ IDLE'}
            </span>
          </div>
        </div>
      </div>

      <div style={{ height: 40 }} />
    </>
  );
}
