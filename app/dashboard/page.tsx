'use client';

import { useState, useEffect, useCallback } from 'react';
import KPICard from '../../components/KPICard';
import ThreatFeedTable from '../../components/ThreatFeedTable';
import ThreatDashboard from '../../components/ThreatDashboard';
import TrustScore from '../../components/TrustScore';
import NetworkMonitor from '../../components/NetworkMonitor';
import SecurityDecisionPanel from '../../components/SecurityDecisionPanel';
import ArchitectureFlow from '../../components/ArchitectureFlow';
import {
  getDashboardStats,
  getCaptureStatus,
  getInterfaces,
  startCapture,
  stopCapture,
  type DashboardStats,
  type CaptureStatus,
  type NetworkInterface,
} from '../../lib/api';

/* ─── KPI icon helpers ──────────────────────────────────────── */
const IcoPackets   = <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>;
const IcoFlows     = <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>;
const IcoThreats   = <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>;
const IcoTrust     = <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>;
const IcoBlocked   = <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>;
const IcoConf      = <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/></svg>;

function formatNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}K`;
  return n.toString();
}

/* ─── Capture control panel ────────────────────────────────── */
function CapturePanel({
  status, interfaces, selectedIface, onSelectIface, onStart, onStop, loading, actionError,
}: {
  status: CaptureStatus | null;
  interfaces: NetworkInterface[];
  selectedIface: string;
  onSelectIface: (v: string) => void;
  onStart: () => void;
  onStop: () => void;
  loading: boolean;
  actionError?: string | null;
}) {
  const running = status?.is_running ?? false;
  const tsharkOk = status?.tshark_available ?? false;

  return (
    <div className="rounded-xl p-4 bracket-all mb-5"
      style={{ background: 'rgba(3,10,22,0.90)', border: '1px solid var(--border-dim)', backdropFilter: 'blur(16px)' }}>
      <div className="flex flex-wrap items-center gap-4">

        {/* tshark status */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', letterSpacing: '0.1em' }}>TSHARK</span>
          <span className="tag"
            style={{
              background: tsharkOk ? 'rgba(0,255,157,0.07)' : 'rgba(255,45,85,0.07)',
              color: tsharkOk ? 'var(--green)' : 'var(--red)',
              border: `1px solid ${tsharkOk ? 'rgba(0,255,157,0.25)' : 'rgba(255,45,85,0.25)'}`,
              fontSize: 9,
            }}>
            <span className={`pulse-dot ${tsharkOk ? 'pulse-green' : 'pulse-red'}`} style={{ width: 4, height: 4 }} />
            {tsharkOk ? 'AVAILABLE' : 'NOT FOUND'}
          </span>
        </div>

        <div className="hidden md:block w-px h-6" style={{ background: 'var(--border-dim)' }} />

        {/* Interface selector */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', letterSpacing: '0.1em' }}>INTERFACE</span>
          <select
            value={selectedIface}
            onChange={e => onSelectIface(e.target.value)}
            disabled={running || !tsharkOk}
            style={{
              fontFamily: 'var(--font-mono)', fontSize: 10,
              background: 'rgba(0,5,14,0.95)', color: 'var(--text-mid)',
              border: '1px solid var(--border-mid)', borderRadius: 6,
              padding: '4px 10px', outline: 'none', minWidth: 140,
              cursor: running ? 'not-allowed' : 'pointer',
              opacity: (running || !tsharkOk) ? 0.5 : 1,
            }}>
            {interfaces.length === 0 ? (
              <option value="">— no interfaces —</option>
            ) : (
              interfaces.map(i => (
                <option key={i.index} value={i.index}>#{i.index} {i.name}</option>
              ))
            )}
          </select>
        </div>

        {/* Start / Stop buttons */}
        <div className="flex items-center gap-2">
          <button
            disabled={running || !tsharkOk || !selectedIface || loading}
            onClick={onStart}
            className="transition-all"
            style={{
              fontFamily: 'var(--font-display)', fontSize: 10, fontWeight: 700, letterSpacing: '0.1em',
              padding: '6px 18px', borderRadius: 8,
              background: running ? 'rgba(0,255,157,0.04)' : 'rgba(0,255,157,0.1)',
              color: running ? 'var(--text-lo)' : 'var(--green)',
              border: `1px solid ${running ? 'rgba(255,255,255,0.05)' : 'rgba(0,255,157,0.3)'}`,
              cursor: (running || !tsharkOk || !selectedIface || loading) ? 'not-allowed' : 'pointer',
              opacity: (running || !tsharkOk || !selectedIface) ? 0.45 : 1,
            }}>
            ▶ START CAPTURE
          </button>
          <button
            disabled={!running || loading}
            onClick={onStop}
            className="transition-all"
            style={{
              fontFamily: 'var(--font-display)', fontSize: 10, fontWeight: 700, letterSpacing: '0.1em',
              padding: '6px 18px', borderRadius: 8,
              background: !running ? 'rgba(255,45,85,0.04)' : 'rgba(255,45,85,0.1)',
              color: !running ? 'var(--text-lo)' : 'var(--red)',
              border: `1px solid ${!running ? 'rgba(255,255,255,0.05)' : 'rgba(255,45,85,0.3)'}`,
              cursor: (!running || loading) ? 'not-allowed' : 'pointer',
              opacity: !running ? 0.45 : 1,
            }}>
            ■ STOP
          </button>
        </div>

        {/* Status + counters */}
        <div className="flex items-center gap-4 ml-auto flex-wrap">
          <div className="live-indicator"
            style={running
              ? undefined
              : { color: 'var(--text-lo)', borderColor: 'rgba(255,255,255,0.08)' }}>
            <span className={`pulse-dot ${running ? 'pulse-green' : 'pulse-amber'}`} style={{ width: 5, height: 5 }} />
            {running ? 'CAPTURING' : 'STOPPED'}
          </div>

          {status && (
            <>
              {[
                { l: 'RAW',      v: (status.raw_packets_seen ?? 0).toLocaleString(), c: 'var(--text-mid)', title: 'Total lines from tshark (all protocols)' },
                { l: 'PACKETS',  v: status.packets_captured.toLocaleString(),         c: 'var(--cyan)',     title: 'IP packets through ML pipeline' },
                { l: 'ANALYZED', v: status.events_analyzed.toLocaleString(),          c: 'var(--purple)',   title: 'Successfully classified events' },
                { l: 'FAILED',   v: status.packets_failed.toLocaleString(),           c: status.packets_failed > 0 ? 'var(--amber)' : 'var(--text-lo)', title: 'ML pipeline errors' },
              ].map(s => (
                <div key={s.l} className="text-center hidden sm:block" title={s.title}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '0.1em' }}>{s.l}</div>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 13, fontWeight: 700, color: s.c }}>{s.v}</div>
                </div>
              ))}
              {running && status.uptime_seconds > 0 && (
                <div className="text-center hidden sm:block">
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '0.1em' }}>UPTIME</div>
                  <div style={{ fontFamily: 'var(--font-display)', fontSize: 13, fontWeight: 700, color: 'var(--green)' }}>
                    {status.uptime_seconds}s
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Error / warning messages */}
      {actionError && (
        <div className="mt-3 px-3 py-2 rounded-lg"
          style={{ background: 'rgba(255,45,85,0.06)', border: '1px solid rgba(255,45,85,0.2)' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--red)' }}>
            ✕ {actionError}
          </span>
        </div>
      )}
      {status?.error && (
        <div className="mt-3 px-3 py-2 rounded-lg"
          style={{ background: 'rgba(255,45,85,0.06)', border: '1px solid rgba(255,45,85,0.2)' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--red)' }}>
            ⚠ {status.error}
          </span>
        </div>
      )}
      {status?.last_packet_error && !status.error && (
        <div className="mt-3 px-3 py-2 rounded-lg"
          style={{ background: 'rgba(255,176,32,0.05)', border: '1px solid rgba(255,176,32,0.2)' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--amber)' }}>
            ▲ Last packet error: {status.last_packet_error}
          </span>
        </div>
      )}
      {status && !status.ml_ready && (
        <div className="mt-3 px-3 py-2 rounded-lg"
          style={{ background: 'rgba(191,95,255,0.05)', border: '1px solid rgba(191,95,255,0.2)' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--purple)' }}>
            ✕ ML pipeline not loaded — check Flask server logs (python backend/api/app.py)
          </span>
        </div>
      )}
      {/* Warn if capture is running but no raw output from tshark after 5+ seconds */}
      {running && (status?.raw_packets_seen ?? 0) === 0 && (status?.uptime_seconds ?? 0) >= 5 && !status?.error && (
        <div className="mt-3 px-3 py-2 rounded-lg"
          style={{ background: 'rgba(255,176,32,0.05)', border: '1px solid rgba(255,176,32,0.2)' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--amber)' }}>
            ▲ No packets from tshark yet (interface #{selectedIface}). Try a different interface number — check which adapters have traffic using: tshark -D
          </span>
        </div>
      )}
      {/* Warn if raw packets seen but none passed IP filter */}
      {running && (status?.raw_packets_seen ?? 0) > 0 && status?.packets_captured === 0 && (
        <div className="mt-3 px-3 py-2 rounded-lg"
          style={{ background: 'rgba(0,212,255,0.04)', border: '1px solid rgba(0,212,255,0.12)' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--cyan)' }}>
            ◉ tshark is running ({status.raw_packets_seen} raw frames) — waiting for IP packets. Non-IP frames (ARP, 802.11) are filtered out.
          </span>
        </div>
      )}
    </div>
  );
}

/* ─── Main page ─────────────────────────────────────────────── */
export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [captureStatus, setCaptureStatus] = useState<CaptureStatus | null>(null);
  const [interfaces, setInterfaces] = useState<NetworkInterface[]>([]);
  const [selectedIface, setSelectedIface] = useState('');
  const [captureLoading, setCaptureLoading] = useState(false);
  const [captureActionError, setCaptureActionError] = useState<string | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  // Fetch interfaces once on mount
  useEffect(() => {
    getInterfaces()
      .then(data => {
        setInterfaces(data.interfaces);
        // Use the recommended default (Wi-Fi / Ethernet) rather than first in list
        const preferred = data.default_index ?? (data.interfaces[0]?.index ?? '');
        setSelectedIface(preferred);
        setBackendOnline(true);
      })
      .catch(() => setBackendOnline(false));
  }, []);

  // Poll stats + capture status every 3s
  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const [s, cs] = await Promise.all([getDashboardStats(), getCaptureStatus()]);
        if (!cancelled) {
          setStats(s);
          setCaptureStatus(cs);
          setBackendOnline(true);
        }
      } catch {
        if (!cancelled) setBackendOnline(false);
      }
    }

    poll();
    const id = setInterval(poll, 3000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const handleStart = useCallback(async () => {
    if (!selectedIface) return;
    setCaptureLoading(true);
    setCaptureActionError(null);
    try {
      await startCapture(selectedIface);
    } catch (e) {
      setCaptureActionError(`Failed to start capture: ${(e as Error).message}`);
    } finally {
      setCaptureLoading(false);
    }
  }, [selectedIface]);

  const handleStop = useCallback(async () => {
    setCaptureLoading(true);
    setCaptureActionError(null);
    try {
      await stopCapture();
    } catch (e) {
      setCaptureActionError(`Failed to stop capture: ${(e as Error).message}`);
    } finally {
      setCaptureLoading(false);
    }
  }, []);

  /* ── KPI data derived from live stats ── */
  const hasLiveData = stats?.source === 'live';

  function deriveThreatLevel(stats: DashboardStats | null): { label: string; color: string; border: string; bg: string } {
    if (!stats || stats.total_packets === 0) return { label: 'UNKNOWN', color: 'var(--text-lo)', border: 'rgba(255,255,255,0.08)', bg: 'rgba(255,255,255,0.03)' };
    const ratio = stats.threats_detected / Math.max(stats.total_packets, 1);
    if (ratio === 0)          return { label: 'LOW',      color: 'var(--green)',  border: 'rgba(0,255,157,0.25)',  bg: 'rgba(0,255,157,0.07)' };
    if (ratio < 0.01)         return { label: 'MODERATE', color: 'var(--cyan)',   border: 'rgba(0,212,255,0.25)',  bg: 'rgba(0,212,255,0.06)' };
    if (ratio < 0.05)         return { label: 'ELEVATED', color: 'var(--amber)',  border: 'rgba(255,176,32,0.25)', bg: 'rgba(255,176,32,0.07)' };
    if (ratio < 0.15)         return { label: 'HIGH',     color: '#ff8c42',       border: 'rgba(255,140,66,0.25)', bg: 'rgba(255,140,66,0.06)' };
    return                     { label: 'CRITICAL',  color: 'var(--red)',    border: 'rgba(255,45,85,0.25)',  bg: 'rgba(255,45,85,0.07)' };
  }
  const threatLevel = deriveThreatLevel(stats);

  const KPIS = [
    {
      title: 'Total Packets',
      value: stats ? formatNum(stats.total_packets) : '—',
      subtitle: hasLiveData ? 'Live captured' : 'Start capture',
      trend: undefined,
      accentColor: 'var(--cyan)', dimColor: 'var(--cyan-dim)',
      icon: IcoPackets,
    },
    {
      title: 'Active Flows',
      value: stats ? stats.active_flows.toLocaleString() : '—',
      subtitle: hasLiveData ? 'Unique sources' : 'No flows yet',
      accentColor: 'var(--purple)', dimColor: 'var(--purple-dim)',
      icon: IcoFlows,
    },
    {
      title: 'Threats Detected',
      value: stats ? stats.threats_detected.toString() : '—',
      subtitle: hasLiveData ? 'Non-benign events' : 'No detections',
      trend: hasLiveData && stats!.threats_detected > 0 ? `${stats!.threats_detected}` : undefined,
      trendUp: true,
      accentColor: 'var(--red)', dimColor: 'var(--red-dim)',
      icon: IcoThreats,
    },
    {
      title: 'Avg Trust Score',
      value: stats ? `${(stats.average_trust_score * 100).toFixed(1)}%` : '—',
      subtitle: hasLiveData ? 'T=α·U+β·D+γ·B' : 'No trust data',
      accentColor: 'var(--green)', dimColor: 'var(--green-dim)',
      icon: IcoTrust,
    },
    {
      title: 'Blocked',
      value: stats ? stats.blocked_connections.toString() : '—',
      subtitle: hasLiveData ? 'Block + Quarantine' : 'No blocks',
      accentColor: 'var(--amber)', dimColor: 'var(--amber-dim)',
      icon: IcoBlocked,
    },
    {
      title: 'Model Confidence',
      value: stats?.model_confidence && stats.model_confidence > 0
        ? `${(stats.model_confidence * 100).toFixed(1)}%`
        : '—',
      subtitle: 'Random Forest · live',
      accentColor: 'var(--cyan)', dimColor: 'var(--cyan-dim)',
      icon: IcoConf,
    },
  ];

  return (
    <>
        {/* Page header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="section-label mb-2">Security Operations Center</div>
            <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 800, color: 'var(--text-hi)', letterSpacing: '0.03em', lineHeight: 1 }}>
              SOC Dashboard
            </h1>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', marginTop: 4 }}>
              CICIDS2017 · Random Forest · Live tshark capture · Multi-level protection
            </p>
          </div>
          <div className="hidden md:flex items-center gap-2">
            {/* Backend connection badge */}
            <div className="tag"
              style={{
                background: backendOnline === null ? 'rgba(255,255,255,0.03)' : backendOnline ? 'rgba(0,255,157,0.07)' : 'rgba(255,45,85,0.07)',
                color: backendOnline === null ? 'var(--text-lo)' : backendOnline ? 'var(--green)' : 'var(--red)',
                border: `1px solid ${backendOnline === null ? 'rgba(255,255,255,0.06)' : backendOnline ? 'rgba(0,255,157,0.25)' : 'rgba(255,45,85,0.25)'}`,
                fontFamily: 'var(--font-display)', fontSize: 9, letterSpacing: '0.1em', padding: '5px 10px',
              }}>
              <span className={`pulse-dot ${backendOnline === null ? 'pulse-amber' : backendOnline ? 'pulse-green' : 'pulse-red'}`} style={{ width: 4, height: 4 }} />
              {backendOnline === null ? 'CONNECTING…' : backendOnline ? 'BACKEND ONLINE' : 'BACKEND OFFLINE'}
            </div>
            {captureStatus?.is_running && (
              <div className="tag"
                style={{ background: threatLevel.bg, color: threatLevel.color, border: `1px solid ${threatLevel.border}`, fontFamily: 'var(--font-display)', fontSize: 10, letterSpacing: '0.12em', padding: '5px 12px' }}>
                ⚠ THREAT LEVEL: {threatLevel.label}
              </div>
            )}
          </div>
        </div>

        {/* Capture control panel */}
        <CapturePanel
          status={captureStatus}
          interfaces={interfaces}
          selectedIface={selectedIface}
          onSelectIface={setSelectedIface}
          onStart={handleStart}
          onStop={handleStop}
          loading={captureLoading}
          actionError={captureActionError}
        />

        {/* KPI Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3 mb-5">
          {KPIS.map((k, i) => <KPICard key={k.title} {...k} delay={i * 70} />)}
        </div>

        {/* Architecture pipeline */}
        <div className="mb-5"><ArchitectureFlow /></div>

        {/* Charts */}
        <div className="mb-5"><ThreatDashboard /></div>

        {/* Live threat feed */}
        <div className="mb-5"><ThreatFeedTable /></div>

        {/* Trust engine + entity registry */}
        <div className="mb-5"><TrustScore /></div>

        {/* Network flow monitor */}
        <div className="mb-5"><NetworkMonitor /></div>

        {/* Decision engine + alerts */}
        <div className="mb-5"><SecurityDecisionPanel /></div>

        {/* ML model info footer */}
        <div className="rounded-xl p-4 bracket-all"
          style={{ background: 'rgba(3,10,22,0.85)', border: '1px solid var(--border-dim)', backdropFilter: 'blur(16px)' }}>
          <div className="card-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2">
              <rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/>
            </svg>
            <span className="card-title">ML Model — Random Forest Classifier</span>
            <span className="ml-auto" style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
              CICIDS2017 trained · 78 features · live inference
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { l: 'Dataset',     v: 'CICIDS2017',  c: 'var(--cyan)' },
              { l: 'Classes',     v: '13 attacks',  c: 'var(--purple)' },
              { l: 'Features',    v: '78 flow',     c: 'var(--green)' },
              { l: 'Estimators',  v: 'n=200 trees', c: 'var(--amber)' },
            ].map(m => (
              <div key={m.l} className="text-center p-3 rounded-lg"
                style={{ background: 'rgba(255,255,255,0.018)', border: `1px solid ${m.c}18` }}>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 800, color: m.c, letterSpacing: '-0.01em' }}>
                  {m.v}
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '0.1em', marginTop: 3 }}>
                  {m.l}
                </div>
              </div>
            ))}
          </div>
          <div className="mt-3 px-3 py-2 rounded"
            style={{ background: 'rgba(0,212,255,0.03)', border: '1px solid rgba(0,212,255,0.08)' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
              // Live feature extraction is a per-packet approximation of CICFlowMeter flow-level statistics.
              For production accuracy, replace with full CICFlowMeter integration. Model confidence shown is live inference average.
            </span>
          </div>
        </div>

        <div style={{ height: 40 }} />
    </>
  );
}
