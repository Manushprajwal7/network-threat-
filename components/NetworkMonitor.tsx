'use client';

import { useState, useEffect, useRef } from 'react';
import { getNetworkFlows, getCaptureStatus, type NetworkFlow } from '../lib/api';

const STATUS_CFG: Record<string, { color: string; bg: string; dot: string; label: string }> = {
  allowed:    { color: 'var(--green)',  bg: 'rgba(5,150,105,0.08)',  dot: 'pulse-green',  label: 'ALLOWED' },
  blocked:    { color: 'var(--red)',    bg: 'rgba(220,38,38,0.08)',  dot: 'pulse-red',    label: 'BLOCKED' },
  alerted:    { color: 'var(--amber)',  bg: 'rgba(217,119,6,0.08)',  dot: 'pulse-amber',  label: 'ALERTED' },
  quarantined:{ color: '#ea6c1a',       bg: 'rgba(234,108,26,0.08)', dot: 'pulse-amber',  label: 'QUARANTINE' },
  restricted: { color: 'var(--cyan)',   bg: 'rgba(2,132,199,0.08)',  dot: 'pulse-cyan',   label: 'RESTRICTED' },
};

export default function NetworkMonitor() {
  const [flows, setFlows] = useState<NetworkFlow[]>([]);
  const [stats, setStats] = useState({ pps: 0, mbps: 0, flows: 0, drops: 0 });
  const [backendError, setBackendError] = useState<string | null>(null);
  const [newIds, setNewIds] = useState<Set<string>>(new Set());
  const prevIds = useRef<Set<string>>(new Set());

  useEffect(() => {
    let cancelled = false;

    async function fetchFlows() {
      try {
        const [flowData, statusData] = await Promise.all([
          getNetworkFlows(25),
          getCaptureStatus(),
        ]);
        if (cancelled) return;
        setBackendError(null);

        const incoming = flowData.flows;
        const freshIds = new Set<string>(incoming.map(f => f.id).filter(id => !prevIds.current.has(id)));
        incoming.forEach(f => prevIds.current.add(f.id));

        if (freshIds.size > 0) {
          setNewIds(prev => new Set([...prev, ...freshIds]));
          setTimeout(() => {
            setNewIds(prev => {
              const next = new Set(prev);
              freshIds.forEach(id => next.delete(id));
              return next;
            });
          }, 2000);
        }

        setFlows(incoming);
        setStats({
          pps:   statusData.is_running ? statusData.packets_captured : 0,
          mbps:  0,
          flows: statusData.events_analyzed,
          drops: 0,
        });
      } catch (err) {
        if (!cancelled) setBackendError((err as Error).message);
      }
    }

    fetchFlows();
    const id = setInterval(fetchFlows, 3000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  return (
    <div className="rounded-xl overflow-hidden bracket-all"
      style={{ background: '#ffffff', border: '1px solid #000000', backdropFilter: 'blur(16px)', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>

      {/* Header */}
      <div className="flex flex-wrap items-center gap-4 px-4 py-3"
        style={{ borderBottom: '1px solid var(--border-dim)', background: 'rgba(0,0,0,0.05)' }}>
        <div className="flex items-center gap-2">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="2">
            <circle cx="12" cy="12" r="2"/>
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
          </svg>
          <span className="card-title">Network Flow Monitor</span>
        </div>

        <div className="flex items-center gap-3 ml-auto">
          {[
            { l: 'PKTS',   v: stats.pps.toLocaleString(),   c: 'var(--cyan)' },
            { l: 'FLOWS',  v: stats.flows.toLocaleString(), c: 'var(--green)' },
          ].map(s => (
            <div key={s.l} className="text-center hidden sm:block">
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '0.12em' }}>{s.l}</div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 13, fontWeight: 700, color: s.c }}>{s.v}</div>
            </div>
          ))}
          <div className={`live-indicator ${backendError ? '' : ''}`}
            style={backendError ? { color: 'var(--red)', background: 'rgba(220,38,38,0.07)', borderColor: 'rgba(220,38,38,0.28)' } : undefined}>
            <span className={`pulse-dot ${backendError ? 'pulse-red' : 'pulse-green'}`} style={{ width: 5, height: 5 }} />
            {backendError ? 'OFFLINE' : flows.length > 0 ? 'CAPTURE' : 'WAITING'}
          </div>
        </div>
      </div>

      {/* Content */}
      {flows.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 gap-3">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--text-lo)" strokeWidth="1.5">
            <circle cx="12" cy="12" r="2"/>
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
          </svg>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', textAlign: 'center', maxWidth: 240 }}>
            {backendError ? 'Backend offline — start Flask server' : 'No flows captured yet — start packet capture'}
          </span>
        </div>
      ) : (
        <div style={{ maxHeight: 380, overflowY: 'auto', overflowX: 'auto' }}>
          <table className="w-full data-table" style={{ minWidth: 800 }}>
            <thead style={{ position: 'sticky', top: 0, background: 'rgba(0,0,0,0.08)', zIndex: 2 }}>
              <tr>
                {['Flow ID', 'Source IP', 'Dest IP', 'Protocol', 'Bytes', 'Attack Type', 'Status'].map(h => (
                  <th key={h} className="text-left">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {flows.map((flow, i) => {
                const sc = STATUS_CFG[flow.status] ?? STATUS_CFG.alerted;
                const isNew = newIds.has(flow.id);
                return (
                  <tr key={flow.id}
                    style={{
                      animation: isNew ? 'data-in 0.3s ease both' : 'none',
                      background: isNew ? 'rgba(2,132,199,0.06)' : 'transparent',
                      transition: 'background 0.5s',
                      opacity: i > 18 ? Math.max(0.25, 1 - (i - 18) * 0.06) : 1,
                    }}>
                    <td>
                      <div className="flex items-center gap-1">
                        {isNew && <span style={{ color: 'var(--green)', fontSize: 8 }}>▶</span>}
                        <span style={{ color: 'var(--text-lo)', fontFamily: 'var(--font-mono)', fontSize: 10 }}>{flow.id}</span>
                      </div>
                    </td>
                    <td style={{ whiteSpace: 'nowrap' }}>
                      <div className="flex items-center gap-1">
                        <span style={{ color: 'var(--text-mid)' }}>{flow.srcIP}</span>
                        <span style={{ color: 'var(--text-lo)', fontSize: 10 }}>→</span>
                      </div>
                    </td>
                    <td style={{ color: 'var(--text-mid)' }}>{flow.dstIP}</td>
                    <td>
                      <span className="tag" style={{ background: 'rgba(0,0,0,0.12)', color: 'var(--text-lo)', border: '1px solid rgba(0,0,0,0.20)', padding: '2px 6px', fontSize: 9 }}>
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
                      <span className="tag" style={{ background: sc.bg, color: sc.color, border: `1px solid ${sc.color}25`, fontFamily: 'var(--font-display)', fontSize: 9, letterSpacing: '0.08em' }}>
                        <span className={`pulse-dot ${sc.dot}`} style={{ width: 4, height: 4 }} />
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
          {flows.length} flows · 3s refresh · live inference
        </span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: flows.length > 0 ? 'var(--green)' : 'var(--text-lo)' }}>
          {flows.length > 0 ? '● CAPTURING' : '○ IDLE'}
        </span>
      </div>
    </div>
  );
}
