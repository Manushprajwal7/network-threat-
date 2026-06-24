'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import {
  startSimulation, stopSimulation, getSimulationStatus, getSimulationEvents,
  getBlockedEntities, blockEntity, unblockEntity, getResearchReportCsvUrl,
  type SimType, type SimStatus, type SimEvent, type BlockedEntity,
} from '../../../lib/api';

// ── Type helpers ───────────────────────────────────────────────────────────────
type TrustPoint = { time: string; trust: number; risk: string };

// ── Constants ──────────────────────────────────────────────────────────────────
const SIM_CARDS: Array<{
  type: SimType;
  label: string;
  icon: string;
  color: string;
  glow: string;
  desc: string;
  safety: string;
}> = [
  {
    type:   'dos',
    label:  'DoS Simulation',
    icon:   'M13 2L3 14h9l-1 8 10-12h-9l1-8z',
    color:  '#d97706',
    glow:   'rgba(217,119,6,0.24)',
    desc:   'Generates synthetic high-rate request events to localhost test endpoint only.',
    safety: 'Target: 127.0.0.1 only — rate limited',
  },
  {
    type:   'portscan',
    label:  'PortScan Simulation',
    icon:   'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z',
    color:  '#0284c7',
    glow:   'rgba(2,132,199,0.22)',
    desc:   'TCP connect probes to 127.0.0.1 ports 8000–8020. No external scanning.',
    safety: 'Localhost ports 8000–8020 only',
  },
  {
    type:   'bruteforce',
    label:  'Brute Force Simulation',
    icon:   'M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4 M10 17l5-5-5-5 M13.8 12H3',
    color:  '#dc2626',
    glow:   'rgba(220,38,38,0.24)',
    desc:   'Repeated failed-login event generation against a mock local endpoint. No real passwords tested.',
    safety: 'Mock endpoint only — no real credentials',
  },
  {
    type:   'botnet',
    label:  'Botnet Behavior Simulation',
    icon:   'M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2z M12 8v4l3 3',
    color:  '#7c3aed',
    glow:   'rgba(124,58,237,0.24)',
    desc:   'Periodic synthetic beacon events to dummy local addresses. No real C2 traffic.',
    safety: 'Synthetic only — no real network traffic',
  },
  {
    type:   'unknown',
    label:  'Unknown Threat Simulation',
    icon:   'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01 M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2z',
    color:  '#059669',
    glow:   'rgba(5,150,105,0.24)',
    desc:   'Anomalous synthetic feature vectors outside training distribution. Tests unknown threat detection.',
    safety: 'Synthetic anomalous features only',
  },
];

const RISK_COLOR: Record<string, string> = {
  Low: '#059669', Medium: '#d97706', High: '#ea6c1a', Critical: '#dc2626',
};
const ACTION_COLOR: Record<string, string> = {
  Allow: '#059669', Restrict: '#d97706', Alert: '#ea6c1a',
  Quarantine: '#dc2626', Block: '#7c3aed',
};

// ── Sub-components ─────────────────────────────────────────────────────────────

function Badge({ color, children }: { color: string; children: React.ReactNode }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      padding: '2px 8px', borderRadius: 4,
      background: `${color}18`, border: `1px solid ${color}40`,
      color, fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 600,
      letterSpacing: '0.06em',
    }}>
      {children}
    </span>
  );
}

function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl p-4 ${className}`} style={{
      background: '#ffffff', border: '1px solid #000000', boxShadow: '0 1px 4px rgba(0,0,0,0.15)',
      backdropFilter: 'blur(16px)',
    }}>
      {children}
    </div>
  );
}

function SLabel({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)',
      letterSpacing: '0.14em', marginBottom: 8, textTransform: 'uppercase',
    }}>
      {children}
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function SimulationPage() {
  const [status, setStatus]           = useState<SimStatus | null>(null);
  const [events, setEvents]           = useState<SimEvent[]>([]);
  const [blocked, setBlocked]         = useState<BlockedEntity[]>([]);
  const [trustHistory, setTrustHistory] = useState<TrustPoint[]>([]);
  const [alert, setAlert]             = useState<{ msg: string; color: string } | null>(null);
  const [loading, setLoading]         = useState<SimType | null>(null);
  const [duration, setDuration]       = useState(30);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const showAlert = (msg: string, color = '#059669') => {
    setAlert({ msg, color });
    setTimeout(() => setAlert(null), 4000);
  };

  const refreshBlocked = useCallback(async () => {
    try {
      const r = await getBlockedEntities();
      setBlocked(r.entities);
    } catch { /* ignore */ }
  }, []);

  const refreshStatus = useCallback(async () => {
    try {
      const [s, e] = await Promise.all([
        getSimulationStatus(),
        getSimulationEvents(60),
      ]);
      setStatus(s);
      setEvents(e.events.slice().reverse());

      // Build trust history from events
      if (e.events.length > 0) {
        setTrustHistory(prev => {
          const latest = e.events.slice(-1)[0];
          if (!latest) return prev;
          const pt: TrustPoint = {
            time:  new Date(latest.timestamp).toLocaleTimeString(),
            trust: typeof latest.trust_score === 'number' ? latest.trust_score : 50,
            risk:  latest.risk_level ?? 'Low',
          };
          const updated = [...prev, pt].slice(-40);
          return updated;
        });

        // Auto-block logic: block the attacker if Critical events pile up
        const critEvents = e.events.filter(ev => ev.risk_level === 'Critical');
        const attackerIp = critEvents.slice(-1)[0]?.source_ip;
        if (critEvents.length >= 5 && attackerIp && !blocked.find(b => b.ip === attackerIp)) {
          try {
            await blockEntity(attackerIp, `Auto-block: ${critEvents.length} critical simulation events`);
            await refreshBlocked();
            showAlert(`Entity blocked by decision engine — ${attackerIp}`, '#dc2626');
          } catch { /* ignore */ }
        }
      }
    } catch { /* ignore */ }
  }, [blocked, refreshBlocked]);

  useEffect(() => {
    refreshStatus();
    refreshBlocked();
  }, [refreshStatus, refreshBlocked]);

  useEffect(() => {
    if (status?.running) {
      pollRef.current = setInterval(() => {
        refreshStatus();
        refreshBlocked();
      }, 1000);
    } else {
      if (pollRef.current) clearInterval(pollRef.current);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [status?.running, refreshStatus, refreshBlocked]);

  const handleStart = async (type: SimType) => {
    setLoading(type);
    try {
      const r = await startSimulation(type, duration);
      if (r.ok) {
        showAlert(`${type.toUpperCase()} simulation started — ${duration}s`);
        await refreshStatus();
      } else {
        showAlert(r.error ?? 'Failed to start', '#dc2626');
      }
    } catch (e: unknown) {
      showAlert(String(e), '#dc2626');
    } finally {
      setLoading(null);
    }
  };

  const handleStop = async () => {
    try {
      const r = await stopSimulation();
      showAlert(`Simulation stopped — ${r.events_generated} events generated`);
      await refreshStatus();
    } catch { /* ignore */ }
  };

  const handleUnblock = async (ip: string) => {
    try {
      await unblockEntity(ip);
      await refreshBlocked();
      showAlert(`${ip} unblocked`);
    } catch { /* ignore */ }
  };

  const latestEvent = events[0];
  const criticalEvents = events.filter(e => e.risk_level === 'Critical').length;
  const unknownEvents  = events.filter(e => e.known_or_unknown === 'Unknown').length;

  return (
    <div style={{ color: 'var(--text-hi)' }}>

      {/* ── Alert banner ─────────────────────────────────────────────── */}
      {alert && (
        <div style={{
          position: 'fixed', top: 72, right: 24, zIndex: 100,
          padding: '12px 20px', borderRadius: 10,
          background: `${alert.color}15`,
          border: `1px solid ${alert.color}50`,
          color: alert.color,
          fontFamily: 'var(--font-mono)', fontSize: 12,
          backdropFilter: 'blur(16px)',
          animation: 'pulse 0.3s ease',
          boxShadow: `0 0 24px ${alert.color}20`,
        }}>
          {alert.msg}
        </div>
      )}

      {/* ── Page header ───────────────────────────────────────────────── */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', letterSpacing: '0.14em', marginBottom: 4 }}>
            // CONTROLLED LOCAL SIMULATION ONLY
          </div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 700, color: 'var(--cyan)', letterSpacing: '0.06em' }}>
            ATTACK SIMULATION LAB
          </h1>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 12, color: 'var(--text-mid)', marginTop: 2 }}>
            Topology-Aware Multi-Level Protection · scored live by the CICIoT2023 ensemble (RF + XGBoost) + unknown detection
          </div>
        </div>
        <div className="flex items-center gap-3">
          {status?.running && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '8px 14px', borderRadius: 8,
              background: 'rgba(220,38,38,0.10)',
              border: '1px solid rgba(220,38,38,0.32)',
            }}>
              <span className="pulse-dot" style={{ background: '#dc2626', animation: 'pulse-red 1s infinite' }} />
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#dc2626' }}>
                {status.sim_type?.toUpperCase()} ACTIVE — {status.remaining_seconds}s
              </span>
            </div>
          )}
          <a
            href={getResearchReportCsvUrl()}
            download="research-report.csv"
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '8px 16px', borderRadius: 8,
              background: 'rgba(2,132,199,0.10)',
              border: '1px solid rgba(2,132,199,0.28)',
              color: 'var(--cyan)',
              fontFamily: 'var(--font-mono)', fontSize: 11,
              textDecoration: 'none', cursor: 'pointer',
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4 M7 10l5 5 5-5 M12 15V3"/>
            </svg>
            Export Research Results
          </a>
        </div>
      </div>

      {/* ── Safety notice ─────────────────────────────────────────────── */}
      <div style={{
        marginBottom: 20, padding: '10px 16px', borderRadius: 8,
        background: 'rgba(217,119,6,0.07)',
        border: '1px solid rgba(217,119,6,0.24)',
        display: 'flex', alignItems: 'center', gap: 10,
      }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#d97706" strokeWidth="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z M12 9v4 M12 17h.01"/>
        </svg>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#d97706' }}>
          SAFETY: Events are synthetic — no real packets are sent to any host (attacker/victim IPs are documentation-range labels only; the sole real action is a safe localhost port probe). Each event is scored by the live ensemble and appears across the Dashboard, Threat Feed, Topology, Trust and Decisions in real time.
        </span>
      </div>

      {/* ── KPI strip ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-4 gap-3 mb-5">
        {[
          { label: 'Events Generated', value: status?.events_generated ?? 0, color: 'var(--cyan)' },
          { label: 'Critical Events',  value: criticalEvents, color: '#dc2626' },
          { label: 'Unknown Threats',  value: unknownEvents,  color: '#059669' },
          { label: 'Blocked Entities', value: blocked.length, color: '#7c3aed' },
        ].map(k => (
          <Card key={k.label}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', letterSpacing: '0.12em', marginBottom: 4 }}>
              {k.label.toUpperCase()}
            </div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 700, color: k.color }}>
              {k.value}
            </div>
          </Card>
        ))}
      </div>

      {/* ── Simulation cards + live panels ────────────────────────────── */}
      <div className="grid grid-cols-3 gap-4 mb-5">

        {/* Left column: simulation cards */}
        <div className="col-span-1 space-y-3">
          <SLabel>// SIMULATION CONTROLS</SLabel>

          {/* Duration selector */}
          <Card>
            <SLabel>Duration</SLabel>
            <div className="flex gap-2">
              {[15, 30, 45, 60].map(d => (
                <button key={d} onClick={() => setDuration(d)}
                  style={{
                    flex: 1, padding: '6px 0', borderRadius: 6, cursor: 'pointer',
                    fontFamily: 'var(--font-mono)', fontSize: 11,
                    background: duration === d ? 'rgba(2,132,199,0.18)' : 'transparent',
                    border: duration === d ? '1px solid rgba(2,132,199,0.40)' : '1px solid var(--border-dim)',
                    color: duration === d ? 'var(--cyan)' : 'var(--text-mid)',
                  }}
                >
                  {d}s
                </button>
              ))}
            </div>
          </Card>

          {SIM_CARDS.map(card => {
            const isActive = status?.running && status.sim_type === card.type;
            const isLoading = loading === card.type;
            return (
              <div key={card.type} style={{
                borderRadius: 10, padding: 14,
                background: isActive ? `${card.glow}` : '#ffffff',
                border: `1px solid ${isActive ? card.color + '50' : 'var(--border-dim)'}`,
                transition: 'all 0.2s',
                boxShadow: isActive ? `0 0 16px ${card.glow}` : 'none',
              }}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div style={{
                      width: 30, height: 30, borderRadius: 6, display: 'flex',
                      alignItems: 'center', justifyContent: 'center',
                      background: `${card.color}18`, border: `1px solid ${card.color}30`,
                    }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={card.color} strokeWidth="1.8">
                        {card.icon.split(' M').map((d, i) => (
                          <path key={i} d={i === 0 ? d : 'M' + d} strokeLinecap="round" strokeLinejoin="round"/>
                        ))}
                      </svg>
                    </div>
                    <span style={{ fontFamily: 'var(--font-ui)', fontSize: 12, fontWeight: 600, color: 'var(--text-hi)' }}>
                      {card.label}
                    </span>
                  </div>
                  {isActive && (
                    <span className="pulse-dot" style={{ background: card.color, width: 8, height: 8, borderRadius: '50%' }} />
                  )}
                </div>

                <p style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: 'var(--text-mid)', marginBottom: 6, lineHeight: 1.5 }}>
                  {card.desc}
                </p>

                <div style={{
                  marginBottom: 10, padding: '4px 8px', borderRadius: 4,
                  background: 'rgba(5,150,105,0.07)',
                  border: '1px solid rgba(0,255,157,0.15)',
                  fontFamily: 'var(--font-mono)', fontSize: 9, color: '#059669',
                }}>
                  SAFETY: {card.safety}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleStart(card.type)}
                    disabled={!!status?.running || isLoading}
                    style={{
                      flex: 1, padding: '7px 0', borderRadius: 6, cursor: status?.running ? 'not-allowed' : 'pointer',
                      fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 600,
                      background: status?.running ? 'rgba(0,0,0,0.10)' : `${card.color}18`,
                      border: `1px solid ${status?.running ? 'var(--border-dim)' : card.color + '50'}`,
                      color: status?.running ? 'var(--text-lo)' : card.color,
                      transition: 'all 0.15s',
                    }}
                  >
                    {isLoading ? 'STARTING...' : 'START'}
                  </button>
                  {isActive && (
                    <button onClick={handleStop}
                      style={{
                        flex: 1, padding: '7px 0', borderRadius: 6, cursor: 'pointer',
                        fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 600,
                        background: 'rgba(255,45,85,0.12)',
                        border: '1px solid rgba(255,45,85,0.4)',
                        color: '#dc2626',
                      }}
                    >
                      STOP
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Right columns: live data */}
        <div className="col-span-2 space-y-4">

          {/* ML Detection Result panel */}
          {latestEvent && (
            <Card>
              <SLabel>// LATEST ML DETECTION RESULT</SLabel>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', marginBottom: 4 }}>PREDICTED ATTACK</div>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700, color: 'var(--cyan)' }}>
                    {latestEvent.predicted_attack ?? latestEvent.attack_type ?? '—'}
                  </div>
                </div>
                <div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', marginBottom: 4 }}>KNOWN / UNKNOWN</div>
                  <div style={{
                    fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700,
                    color: latestEvent.known_or_unknown === 'Unknown' ? '#dc2626' : '#059669',
                  }}>
                    {latestEvent.known_or_unknown ?? '—'}
                  </div>
                </div>
                <div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', marginBottom: 4 }}>SECURITY ACTION</div>
                  <div style={{
                    fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700,
                    color: ACTION_COLOR[latestEvent.security_action ?? ''] ?? 'var(--text-mid)',
                  }}>
                    {latestEvent.security_action ?? '—'}
                  </div>
                </div>
                <div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', marginBottom: 4 }}>CONFIDENCE</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--text-hi)' }}>
                    {latestEvent.confidence != null ? `${(latestEvent.confidence * 100).toFixed(1)}%` : '—'}
                  </div>
                </div>
                <div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', marginBottom: 4 }}>ANOMALY SCORE</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: latestEvent.anomaly_score && latestEvent.anomaly_score > 0.5 ? '#dc2626' : 'var(--text-hi)' }}>
                    {latestEvent.anomaly_score != null ? latestEvent.anomaly_score.toFixed(3) : '—'}
                  </div>
                </div>
                <div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', marginBottom: 4 }}>TRUST SCORE</div>
                  <div style={{
                    fontFamily: 'var(--font-mono)', fontSize: 13,
                    color: (latestEvent.trust_score ?? 100) < 40 ? '#dc2626' : (latestEvent.trust_score ?? 100) < 70 ? '#d97706' : '#059669',
                  }}>
                    {latestEvent.trust_score ?? '—'} / 100
                  </div>
                </div>
              </div>

              {/* Risk badge row */}
              <div className="flex gap-2 mt-3">
                <Badge color={RISK_COLOR[latestEvent.risk_level] ?? '#d97706'}>
                  RISK: {latestEvent.risk_level}
                </Badge>
                <Badge color="#0284c7">
                  SIM: {latestEvent.sim_type?.toUpperCase()}
                </Badge>
                <Badge color="#059669">
                  LOCAL SIMULATION ONLY
                </Badge>
              </div>
            </Card>
          )}

          {/* Trust score timeline */}
          {trustHistory.length > 1 && (
            <Card>
              <SLabel>// TRUST SCORE DEGRADATION TIMELINE</SLabel>
              <ResponsiveContainer width="100%" height={130}>
                <AreaChart data={trustHistory} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="trustGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#0284c7" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#0284c7" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(2,132,199,0.08)" />
                  <XAxis dataKey="time" tick={{ fontSize: 9, fill: 'var(--text-lo)', fontFamily: 'var(--font-mono)' }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: 'var(--text-lo)', fontFamily: 'var(--font-mono)' }} />
                  <Tooltip
                    contentStyle={{ background: '#f8fafc', border: '1px solid var(--border-mid)', borderRadius: 6, fontSize: 11 }}
                    labelStyle={{ color: 'var(--text-mid)', fontFamily: 'var(--font-mono)' }}
                  />
                  <Area type="monotone" dataKey="trust" stroke="#0284c7" fill="url(#trustGrad)" strokeWidth={1.5} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </Card>
          )}

          {/* Live event feed */}
          <Card>
            <div className="flex items-center justify-between mb-3">
              <SLabel>// LIVE SIMULATION EVENTS</SLabel>
              <Badge color="var(--cyan)">{events.length} events</Badge>
            </div>
            <div style={{ maxHeight: 260, overflowY: 'auto' }}>
              {events.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-lo)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                  No events yet. Start a simulation to see live data.
                </div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--font-mono)', fontSize: 10 }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-dim)' }}>
                      {['Time', 'Type', 'Attack', 'Risk', 'Action', 'Trust'].map(h => (
                        <th key={h} style={{ padding: '4px 8px', color: 'var(--text-lo)', textAlign: 'left', letterSpacing: '0.08em', fontSize: 9 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {events.slice(0, 40).map((evt, i) => (
                      <tr key={evt.id} style={{ borderBottom: '1px solid rgba(2,132,199,0.06)', background: i % 2 === 0 ? 'transparent' : 'rgba(0,212,255,0.015)' }}>
                        <td style={{ padding: '4px 8px', color: 'var(--text-lo)' }}>{new Date(evt.timestamp).toLocaleTimeString()}</td>
                        <td style={{ padding: '4px 8px', color: 'var(--cyan)' }}>{evt.sim_type?.toUpperCase()}</td>
                        <td style={{ padding: '4px 8px', color: 'var(--text-hi)' }}>{evt.predicted_attack ?? evt.attack_type}</td>
                        <td style={{ padding: '4px 8px' }}>
                          <span style={{ color: RISK_COLOR[evt.risk_level] ?? '#d97706' }}>{evt.risk_level}</span>
                        </td>
                        <td style={{ padding: '4px 8px' }}>
                          <span style={{ color: ACTION_COLOR[evt.security_action ?? ''] ?? 'var(--text-mid)' }}>
                            {evt.security_action ?? '—'}
                          </span>
                        </td>
                        <td style={{ padding: '4px 8px', color: (evt.trust_score ?? 100) < 40 ? '#dc2626' : 'var(--text-mid)' }}>
                          {evt.trust_score ?? '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* ── Blocked entities panel ─────────────────────────────────────── */}
      <Card>
        <div className="flex items-center justify-between mb-3">
          <div>
            <SLabel>// BLOCKED ENTITIES TABLE</SLabel>
            <div style={{ fontFamily: 'var(--font-ui)', fontSize: 13, fontWeight: 600, color: 'var(--text-hi)' }}>
              Decision Engine — Quarantine & Block Register
            </div>
          </div>
          <Badge color="#7c3aed">SIMULATION MODE</Badge>
        </div>
        {blocked.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '20px 0', color: 'var(--text-lo)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            No entities blocked. Run a simulation to trigger automatic blocking.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-dim)' }}>
                {['IP Address', 'Reason', 'Action', 'Count', 'Timestamp', 'Mode', ''].map(h => (
                  <th key={h} style={{ padding: '6px 10px', color: 'var(--text-lo)', textAlign: 'left', fontSize: 9, letterSpacing: '0.08em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {blocked.map(b => (
                <tr key={b.ip} style={{ borderBottom: '1px solid rgba(2,132,199,0.06)' }}>
                  <td style={{ padding: '8px 10px', color: '#dc2626', fontWeight: 600 }}>{b.ip}</td>
                  <td style={{ padding: '8px 10px', color: 'var(--text-mid)', maxWidth: 280 }}>{b.reason}</td>
                  <td style={{ padding: '8px 10px' }}>
                    <Badge color={ACTION_COLOR[b.action] ?? '#dc2626'}>{b.action}</Badge>
                  </td>
                  <td style={{ padding: '8px 10px', color: 'var(--text-hi)' }}>{b.count}</td>
                  <td style={{ padding: '8px 10px', color: 'var(--text-lo)' }}>{new Date(b.timestamp).toLocaleString()}</td>
                  <td style={{ padding: '8px 10px' }}>
                    <Badge color="#7c3aed">{b.mode}</Badge>
                  </td>
                  <td style={{ padding: '8px 10px' }}>
                    <button onClick={() => handleUnblock(b.ip)}
                      style={{
                        padding: '4px 10px', borderRadius: 4, cursor: 'pointer',
                        background: 'rgba(5,150,105,0.10)',
                        border: '1px solid rgba(5,150,105,0.28)',
                        color: '#059669', fontSize: 10,
                      }}
                    >
                      Unblock
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* ── Attack timeline chart ─────────────────────────────────────── */}
      {events.length > 2 && (() => {
        const timeline = events.slice(0, 50).map((e, i) => ({
          seq:  e.sequence ?? i,
          conf: typeof e.confidence === 'number' ? +(e.confidence * 100).toFixed(1) : 50,
          risk: e.risk_level === 'Critical' ? 4 : e.risk_level === 'High' ? 3 : e.risk_level === 'Medium' ? 2 : 1,
        })).reverse();

        return (
          <Card className="mt-4">
            <SLabel>// ATTACK TIMELINE — CONFIDENCE & RISK LEVEL</SLabel>
            <ResponsiveContainer width="100%" height={120}>
              <LineChart data={timeline} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(2,132,199,0.08)" />
                <XAxis dataKey="seq" tick={{ fontSize: 9, fill: 'var(--text-lo)', fontFamily: 'var(--font-mono)' }} />
                <YAxis yAxisId="conf" domain={[0, 100]} tick={{ fontSize: 9, fill: 'var(--text-lo)' }} />
                <YAxis yAxisId="risk" orientation="right" domain={[0, 4]} tick={{ fontSize: 9, fill: 'var(--text-lo)' }} />
                <Tooltip
                  contentStyle={{ background: '#f8fafc', border: '1px solid var(--border-mid)', borderRadius: 6, fontSize: 10 }}
                />
                <Line yAxisId="conf" type="monotone" dataKey="conf" stroke="#0284c7" strokeWidth={1.5} dot={false} name="Confidence %" />
                <Line yAxisId="risk" type="monotone" dataKey="risk" stroke="#dc2626" strokeWidth={1.5} dot={false} name="Risk Level" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        );
      })()}
    </div>
  );
}
