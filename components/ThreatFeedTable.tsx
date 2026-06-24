'use client';

import { useState, useEffect, useRef } from 'react';
import { getLiveEvents, type LiveEvent } from '../lib/api';

type Sev = 'benign' | 'low' | 'medium' | 'high' | 'critical';

const SEV: Record<Sev, { color: string; bg: string; border: string; dot: string }> = {
  benign:   { color: 'var(--green)',  bg: 'rgba(5,150,105,0.08)',   border: 'rgba(5,150,105,0.22)',  dot: 'pulse-green' },
  low:      { color: 'var(--cyan)',   bg: 'rgba(2,132,199,0.08)',   border: 'rgba(2,132,199,0.22)',  dot: 'pulse-cyan' },
  medium:   { color: 'var(--amber)',  bg: 'rgba(217,119,6,0.08)',   border: 'rgba(217,119,6,0.22)',  dot: 'pulse-amber' },
  high:     { color: 'var(--red)',    bg: 'rgba(220,38,38,0.08)',   border: 'rgba(220,38,38,0.22)',  dot: 'pulse-red' },
  critical: { color: 'var(--purple)', bg: 'rgba(124,58,237,0.08)',  border: 'rgba(124,58,237,0.22)', dot: 'pulse-purple' },
};

const ACT: Record<string, { color: string; bg: string }> = {
  Allow:      { color: 'var(--green)',  bg: 'rgba(5,150,105,0.08)' },
  Alert:      { color: 'var(--amber)',  bg: 'rgba(217,119,6,0.08)' },
  Restrict:   { color: 'var(--cyan)',   bg: 'rgba(2,132,199,0.08)' },
  Quarantine: { color: '#ea6c1a',       bg: 'rgba(234,108,26,0.08)' },
  Block:      { color: 'var(--red)',    bg: 'rgba(220,38,38,0.09)' },
};

type Row = LiveEvent & { _isNew?: boolean };

export default function ThreatFeedTable() {
  const [rows, setRows] = useState<Row[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [newIds, setNewIds] = useState<Set<string>>(new Set());
  const [backendError, setBackendError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const prevIds = useRef<Set<string>>(new Set());

  useEffect(() => {
    let cancelled = false;

    async function fetchEvents() {
      try {
        const data = await getLiveEvents(60);
        if (cancelled) return;

        setBackendError(null);
        setLoading(false);

        const incoming = data.events;
        const freshIds = new Set<string>();
        incoming.forEach(e => {
          if (!prevIds.current.has(e.id)) freshIds.add(e.id);
        });

        if (freshIds.size > 0) {
          setNewIds(prev => new Set([...prev, ...freshIds]));
          setTimeout(() => {
            setNewIds(prev => {
              const next = new Set(prev);
              freshIds.forEach(id => next.delete(id));
              return next;
            });
          }, 2500);
        }

        prevIds.current = new Set(incoming.map(e => e.id));
        setRows(incoming);
      } catch (err) {
        if (!cancelled) {
          setBackendError((err as Error).message);
          setLoading(false);
        }
      }
    }

    fetchEvents();
    const interval = setInterval(fetchEvents, 3000);
    return () => { cancelled = true; clearInterval(interval); };
  }, []);

  const filtered = filter === 'all'
    ? rows
    : rows.filter(r => {
        if (filter === 'benign') return r.predicted_label.toUpperCase() === 'BENIGN';
        return r.severity === filter;
      });

  return (
    <div className="rounded-xl overflow-hidden bracket-all"
      style={{ background: '#ffffff', border: '1px solid #000000', backdropFilter: 'blur(16px)', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>

      {/* Header */}
      <div className="flex flex-wrap items-center gap-3 px-4 py-3"
        style={{ borderBottom: '1px solid var(--border-dim)', background: 'rgba(0,0,0,0.05)' }}>
        <div className="flex items-center gap-2.5">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
          </svg>
          <span className="card-title">Live Threat Feed</span>
          {!backendError && !loading && (
            <div className="live-indicator">
              <span className="pulse-dot pulse-green" style={{ width: 5, height: 5 }} />
              {rows.length > 0 ? 'STREAMING' : 'WAITING'}
            </div>
          )}
          {backendError && (
            <div className="live-indicator" style={{ color: 'var(--red)', background: 'rgba(220,38,38,0.07)', borderColor: 'rgba(220,38,38,0.28)' }}>
              <span className="pulse-dot pulse-red" style={{ width: 5, height: 5 }} />
              OFFLINE
            </div>
          )}
        </div>
        <div className="flex items-center gap-1 ml-auto flex-wrap">
          {(['all', 'critical', 'high', 'medium', 'low', 'benign'] as const).map(f => {
            const s = f !== 'all' ? SEV[f as Sev] : null;
            const active = filter === f;
            return (
              <button key={f} onClick={() => setFilter(f)}
                className="px-2 py-1 rounded transition-all text-xs"
                style={{
                  fontFamily: 'var(--font-mono)', fontSize: 9, letterSpacing: '0.1em', textTransform: 'uppercase',
                  background: active ? (s ? s.bg : 'var(--cyan-dim)') : 'transparent',
                  color: active ? (s ? s.color : 'var(--cyan)') : 'var(--text-lo)',
                  border: `1px solid ${active ? (s ? s.border : 'rgba(2,132,199,0.30)') : 'transparent'}`,
                }}>
                {f}
              </button>
            );
          })}
        </div>
      </div>

      {/* Body */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-16 gap-3">
          <div className="pulse-dot pulse-cyan" style={{ width: 12, height: 12 }} />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-lo)' }}>Connecting to backend…</span>
        </div>
      ) : backendError ? (
        <div className="flex flex-col items-center justify-center py-16 gap-3">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--red)" strokeWidth="1.5">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 12, color: 'var(--red)', letterSpacing: '0.1em' }}>
            BACKEND OFFLINE
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', maxWidth: 300, textAlign: 'center' }}>
            Start the Flask server: <code style={{ color: 'var(--cyan)' }}>python backend/api/app.py</code>
          </div>
        </div>
      ) : rows.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 gap-3">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--text-lo)" strokeWidth="1.5">
            <circle cx="12" cy="12" r="10"/><polyline points="8 12 12 16 16 12"/><line x1="12" y1="8" x2="12" y2="16"/>
          </svg>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 12, color: 'var(--text-lo)', letterSpacing: '0.1em' }}>
            NO LIVE PACKETS CAPTURED YET
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)' }}>
            Select an interface above and click Start Capture
          </div>
        </div>
      ) : (
        <div style={{ maxHeight: 400, overflowY: 'auto', overflowX: 'auto' }}>
          <table className="w-full data-table" style={{ minWidth: 900 }}>
            <thead style={{ position: 'sticky', top: 0, background: 'rgba(0,0,0,0.08)', zIndex: 2 }}>
              <tr>
                {['Timestamp', 'Source IP', 'Destination IP', 'Proto', 'Attack Type', 'Confidence', 'Trust Score', 'Decision'].map(h => (
                  <th key={h} className="text-left">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((row, i) => {
                const sevKey = (row.predicted_label.toUpperCase() === 'BENIGN' ? 'benign' : row.severity) as Sev;
                const sev = SEV[sevKey] ?? SEV.low;
                const act = ACT[row.action] ?? ACT.Alert;
                const isNew = newIds.has(row.id);
                const trustNorm = row.trust_score / 100;
                return (
                  <tr key={row.id}
                    style={{
                      background: isNew ? 'rgba(2,132,199,0.06)' : 'transparent',
                      transition: 'background 0.6s ease',
                      animation: isNew ? 'data-in 0.3s ease both' : 'none',
                      opacity: i > 20 ? Math.max(0.3, 1 - (i - 20) * 0.05) : 1,
                    }}>
                    <td>
                      <div className="flex items-center gap-1.5">
                        {isNew && <span style={{ color: 'var(--green)', fontSize: 9 }}>▶</span>}
                        <span style={{ color: 'var(--text-lo)', fontSize: 11, whiteSpace: 'nowrap' }}>{row.timestamp}</span>
                      </div>
                    </td>
                    <td style={{ color: 'var(--text-mid)', fontWeight: 500 }}>{row.source_ip ?? '?'}</td>
                    <td style={{ color: 'var(--text-mid)' }}>{row.dest_ip ?? '?'}</td>
                    <td>
                      <span className="tag" style={{ background: 'rgba(0,0,0,0.12)', color: 'var(--text-lo)', border: '1px solid rgba(0,0,0,0.20)', padding: '2px 6px' }}>
                        {row.protocol}
                      </span>
                    </td>
                    <td>
                      <span className="tag" style={{ background: sev.bg, color: sev.color, border: `1px solid ${sev.border}` }}>
                        <span className={`pulse-dot ${sev.dot}`} style={{ width: 4, height: 4 }} />
                        {row.predicted_label}
                      </span>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="track" style={{ width: 44, height: 4 }}>
                          <div className="track-fill" style={{
                            width: `${row.confidence * 100}%`,
                            background: row.confidence > 0.92 ? 'var(--green)' : 'var(--amber)',
                          }} />
                        </div>
                        <span style={{ color: 'var(--text-mid)', fontSize: 11 }}>{(row.confidence * 100).toFixed(1)}%</span>
                      </div>
                    </td>
                    <td>
                      <span style={{
                        fontFamily: 'var(--font-display)', fontSize: 12, fontWeight: 700,
                        color: trustNorm < 0.3 ? 'var(--red)' : trustNorm < 0.6 ? 'var(--amber)' : 'var(--green)',
                      }}>
                        {trustNorm.toFixed(3)}
                      </span>
                    </td>
                    <td>
                      <span className="tag" style={{ background: act.bg, color: act.color, border: `1px solid ${act.color}25`, fontFamily: 'var(--font-display)', fontSize: 9, letterSpacing: '0.1em' }}>
                        {row.action.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between px-4 py-2"
        style={{ borderTop: '1px solid var(--border-dim)', background: 'rgba(0,0,0,0.03)' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
          {filtered.length} events · 4s refresh · CICIoT2023
        </span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--cyan)' }}>
          Ensemble (RF + XGBoost) · live inference
        </span>
      </div>
    </div>
  );
}
