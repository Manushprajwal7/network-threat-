'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { getTopology, getCaptureStatus, type TopologyNode, type TopologyEdge } from '../../../lib/api';

// ── Types ─────────────────────────────────────────────────────────────────────

interface PhysNode extends TopologyNode {
  x: number; y: number;
  vx: number; vy: number;
}

// ── Constants ─────────────────────────────────────────────────────────────────

const RISK_COL: Record<string, string> = {
  Low: '#00ff9d', Medium: '#ffb020', High: '#ff2d55', Critical: '#bf5fff',
};
const PROTO_COL: Record<string, string> = {
  HTTPS: '#00d4ff', HTTP: '#ffb020', DNS: '#00ff9d',
  TCP: '#8888cc', UDP: '#9966cc', ICMP: '#ff8c42', UNKNOWN: '#555577',
};
function protoColor(protocols: string[]) {
  for (const p of protocols) if (PROTO_COL[p]) return PROTO_COL[p];
  return PROTO_COL.UNKNOWN;
}
function nodeR(n: PhysNode) {
  return Math.max(9, Math.min(28, 9 + Math.log10(n.packet_count + 1) * 7));
}

// ── Physics ───────────────────────────────────────────────────────────────────

function simTick(nodes: PhysNode[], edges: TopologyEdge[], W: number, H: number) {
  const n = nodes.length;
  if (n === 0 || W < 10 || H < 10) return;
  const REPULSE = 4500, SPRING_L = 150, SPRING_K = 0.03, CENTRE_K = 0.01, DAMP = 0.80, PAD = 60;
  const fx = new Float64Array(n), fy = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const dx = nodes[j].x - nodes[i].x, dy = nodes[j].y - nodes[i].y;
      const d2 = dx * dx + dy * dy + 1, d = Math.sqrt(d2), f = REPULSE / d2;
      fx[i] -= (f * dx) / d; fy[i] -= (f * dy) / d;
      fx[j] += (f * dx) / d; fy[j] += (f * dy) / d;
    }
  }
  const imap = new Map(nodes.map((nd, i) => [nd.id, i]));
  for (const e of edges) {
    const si = imap.get(e.source), ti = imap.get(e.target);
    if (si === undefined || ti === undefined) continue;
    const dx = nodes[ti].x - nodes[si].x, dy = nodes[ti].y - nodes[si].y;
    const d = Math.sqrt(dx * dx + dy * dy) + 0.1, f = SPRING_K * (d - SPRING_L);
    fx[si] += (f * dx) / d; fy[si] += (f * dy) / d;
    fx[ti] -= (f * dx) / d; fy[ti] -= (f * dy) / d;
  }
  const cx = W / 2, cy = H / 2;
  for (let i = 0; i < n; i++) {
    fx[i] += CENTRE_K * (cx - nodes[i].x);
    fy[i] += CENTRE_K * (cy - nodes[i].y);
    nodes[i].vx = (nodes[i].vx + fx[i]) * DAMP;
    nodes[i].vy = (nodes[i].vy + fy[i]) * DAMP;
    nodes[i].x = Math.max(PAD, Math.min(W - PAD, nodes[i].x + nodes[i].vx));
    nodes[i].y = Math.max(PAD, Math.min(H - PAD, nodes[i].y + nodes[i].vy));
  }
}

function mergeNodes(prev: PhysNode[], fresh: TopologyNode[], W: number, H: number): PhysNode[] {
  const prevMap = new Map(prev.map(n => [n.id, n]));
  return fresh.map(fn => {
    const ex = prevMap.get(fn.id);
    if (ex) return { ...ex, ...fn };
    const a = Math.random() * Math.PI * 2, r = 80 + Math.random() * 100;
    return { ...fn, x: W / 2 + Math.cos(a) * r, y: H / 2 + Math.sin(a) * r, vx: 0, vy: 0 };
  });
}

// ── SVG-only tooltip (avoids foreignObject issues) ────────────────────────────

function NodeTooltip({ node, W, H }: { node: PhysNode; W: number; H: number }) {
  const col = RISK_COL[node.risk_level] ?? '#00ff9d';
  const r = nodeR(node);
  const tipW = 220, lineH = 16, lines = 5 + node.protocols.length;
  const tipH = 20 + lines * lineH;
  const tx = node.x + r + 10 + tipW > W ? node.x - r - 10 - tipW : node.x + r + 10;
  const ty = Math.max(8, Math.min(H - tipH - 8, node.y - tipH / 2));

  const rows: Array<{ label: string; value: string; color: string }> = [
    { label: 'IP', value: node.id, color: col },
    { label: node.is_local ? 'LOCAL' : 'EXTERNAL', value: '', color: 'rgba(255,255,255,0.35)' },
    { label: 'Packets', value: node.packet_count.toLocaleString(), color: '#00d4ff' },
    { label: 'Threats', value: node.threat_count.toString(), color: node.threat_count > 0 ? '#ff2d55' : 'rgba(255,255,255,0.3)' },
    { label: 'Trust', value: `${node.trust_score}%`, color: node.trust_score >= 80 ? '#00ff9d' : '#ffb020' },
    { label: 'Risk', value: node.risk_level, color: col },
    ...node.protocols.slice(0, 3).map(p => ({ label: 'Proto', value: p, color: PROTO_COL[p] ?? '#888' })),
  ];

  return (
    <g style={{ pointerEvents: 'none' }}>
      <rect x={tx} y={ty} width={tipW} height={tipH} rx={8}
        fill="rgba(0,4,14,0.97)" stroke={`${col}40`} strokeWidth={1}/>
      {rows.map((row, i) => (
        <g key={i}>
          <text x={tx + 10} y={ty + 16 + i * lineH}
            style={{ fill: 'rgba(255,255,255,0.35)', fontFamily: 'monospace', fontSize: 9 }}>
            {row.label}
          </text>
          <text x={tx + tipW - 10} y={ty + 16 + i * lineH}
            textAnchor="end"
            style={{ fill: row.color, fontFamily: 'monospace', fontSize: 9, fontWeight: 700 }}>
            {row.value}
          </text>
        </g>
      ))}
    </g>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function TopologyPage() {
  // ── Dimensions – guarded to never be 0 ──────────────────────────────────────
  const containerRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ W: 860, H: 560 });
  const dimsRef = useRef({ W: 860, H: 560 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const update = () => {
      const w = el.clientWidth, h = el.clientHeight;
      if (w > 50 && h > 50) {
        const next = { W: w, H: h };
        dimsRef.current = next;
        setDims(next);
      }
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // ── Physics state ────────────────────────────────────────────────────────────
  const nodesRef = useRef<PhysNode[]>([]);
  const edgesRef = useRef<TopologyEdge[]>([]);
  const rafRef   = useRef<number>(0);
  const frameRef = useRef(0);

  const [displayNodes, setDisplayNodes] = useState<PhysNode[]>([]);
  const [edges, setEdges]               = useState<TopologyEdge[]>([]);
  const [dashOffset, setDashOffset]     = useState(0);

  // Physics loop — depends only on dimsRef (not state) so it never restarts
  useEffect(() => {
    function loop() {
      const { W, H } = dimsRef.current;
      simTick(nodesRef.current, edgesRef.current, W, H);
      frameRef.current++;
      if (frameRef.current % 2 === 0) setDisplayNodes([...nodesRef.current]);
      if (frameRef.current % 4 === 0) setDashOffset(o => (o - 0.7 + 24) % 24);
      rafRef.current = requestAnimationFrame(loop);
    }
    rafRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafRef.current);
  }, []); // empty deps — runs once, reads dims via ref

  // ── Data fetching ────────────────────────────────────────────────────────────
  const [capturing,    setCapturing]    = useState(false);
  const [totalEvents,  setTotalEvents]  = useState(0);
  const [lastUpdate,   setLastUpdate]   = useState('—');
  const [fetchError,   setFetchError]   = useState<string | null>(null);
  const [loading,      setLoading]      = useState(true);

  // stable — no state/dims deps, reads dims via ref
  const fetchData = useCallback(async () => {
    try {
      const [topo, status] = await Promise.all([getTopology(), getCaptureStatus()]);
      setFetchError(null);
      setCapturing(status.is_running);
      setTotalEvents(topo.total_events);
      setLastUpdate(new Date().toLocaleTimeString());
      const { W, H } = dimsRef.current;
      const merged = mergeNodes(nodesRef.current, topo.nodes, W, H);
      nodesRef.current = merged;
      edgesRef.current = topo.edges;
      setEdges(topo.edges);
    } catch (err) {
      const msg = (err as Error).message ?? 'Unknown error';
      setFetchError(msg.includes('404') ? '/api/topology not found — restart Flask server' : msg);
    } finally {
      setLoading(false);
    }
  }, []); // stable — empty deps

  useEffect(() => {
    fetchData();
    const id = setInterval(fetchData, 5000);
    return () => clearInterval(id);
  }, [fetchData]);

  // ── Interaction ──────────────────────────────────────────────────────────────
  const [hovered,  setHovered]  = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  const selectedNode = displayNodes.find(n => n.id === selected) ?? null;

  // ── Filters ──────────────────────────────────────────────────────────────────
  const [filterRisk,    setFilterRisk]    = useState('all');
  const [showExternal, setShowExternal]  = useState(true);

  const visibleNodes = displayNodes.filter(n => {
    if (!showExternal && !n.is_local) return false;
    if (filterRisk !== 'all' && n.risk_level !== filterRisk) return false;
    return true;
  });
  const visibleIds   = new Set(visibleNodes.map(n => n.id));
  const visibleEdges = edges.filter(e => visibleIds.has(e.source) && visibleIds.has(e.target));

  const localCount  = displayNodes.filter(n => n.is_local).length;
  const extCount    = displayNodes.filter(n => !n.is_local).length;
  const threatNodes = displayNodes.filter(n => n.threat_count > 0).length;
  const maxPkts     = Math.max(...displayNodes.map(n => n.packet_count), 1);

  const hoveredNode = hovered ? displayNodes.find(n => n.id === hovered) ?? null : null;

  // ─────────────────────────────────────────────────────────────────────────────

  return (
    <>
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <div className="section-label mb-2">Network Intelligence</div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 800,
            color: 'var(--text-hi)', letterSpacing: '0.03em', lineHeight: 1 }}>
            Network Topology
          </h1>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', marginTop: 4 }}>
            Force-directed graph · live capture · {visibleNodes.length} nodes · {visibleEdges.length} edges
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="tag" style={{
            background: capturing ? 'rgba(0,255,157,0.07)' : 'rgba(255,255,255,0.03)',
            color: capturing ? 'var(--green)' : 'var(--text-lo)',
            border: `1px solid ${capturing ? 'rgba(0,255,157,0.25)' : 'rgba(255,255,255,0.08)'}`,
            fontFamily: 'var(--font-display)', fontSize: 9, letterSpacing: '0.1em', padding: '5px 10px',
          }}>
            <span className={`pulse-dot ${capturing ? 'pulse-green' : 'pulse-amber'}`} style={{ width: 4, height: 4 }} />
            {capturing ? 'LIVE' : 'IDLE'}
          </div>
          <button onClick={() => { setLoading(true); fetchData(); }}
            style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--cyan)',
              background: 'rgba(0,212,255,0.06)', border: '1px solid rgba(0,212,255,0.2)',
              borderRadius: 6, padding: '5px 10px', cursor: 'pointer', letterSpacing: '0.1em' }}>
            ↻ REFRESH
          </button>
        </div>
      </div>

      {/* Error banner */}
      {fetchError && (
        <div className="rounded-xl px-4 py-3 mb-4"
          style={{ background: 'rgba(255,45,85,0.06)', border: '1px solid rgba(255,45,85,0.25)' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--red)' }}>
            ⚠ {fetchError}
          </span>
          {fetchError.includes('restart') && (
            <code style={{ display: 'block', fontFamily: 'var(--font-mono)', fontSize: 10,
              color: 'var(--cyan)', marginTop: 4 }}>
              cd backend && python api/app.py
            </code>
          )}
        </div>
      )}

      {/* Stats strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        {[
          { l: 'Total Nodes',    v: displayNodes.length, c: 'var(--cyan)' },
          { l: 'Local Devices',  v: localCount,          c: 'var(--green)' },
          { l: 'External Hosts', v: extCount,            c: 'var(--purple)' },
          { l: 'Threat Nodes',   v: threatNodes,         c: threatNodes > 0 ? 'var(--red)' : 'var(--text-lo)' },
        ].map(s => (
          <div key={s.l} className="rounded-xl px-4 py-3 bracket-all"
            style={{ background: 'rgba(3,10,22,0.90)', border: '1px solid var(--border-dim)', backdropFilter: 'blur(12px)' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)',
              letterSpacing: '0.1em', marginBottom: 3 }}>{s.l}</div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 800,
              color: s.c, letterSpacing: '-0.02em', lineHeight: 1 }}>{s.v}</div>
          </div>
        ))}
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', letterSpacing: '0.1em' }}>RISK:</span>
        {(['all', 'Low', 'Medium', 'High', 'Critical'] as const).map(r => {
          const active = filterRisk === r;
          const col = r === 'all' ? 'var(--cyan)' : RISK_COL[r];
          return (
            <button key={r} onClick={() => setFilterRisk(r)} style={{
              fontFamily: 'var(--font-display)', fontSize: 9, letterSpacing: '0.08em',
              padding: '4px 10px', borderRadius: 6, cursor: 'pointer', transition: 'all 0.15s',
              background: active ? `${col}18` : 'rgba(255,255,255,0.03)',
              color: active ? col : 'var(--text-lo)',
              border: `1px solid ${active ? `${col}50` : 'var(--border-dim)'}`,
            }}>{r === 'all' ? 'ALL' : r.toUpperCase()}</button>
          );
        })}
        <div className="w-px h-5 hidden sm:block" style={{ background: 'var(--border-dim)' }} />
        <button onClick={() => setShowExternal(v => !v)} style={{
          fontFamily: 'var(--font-display)', fontSize: 9, letterSpacing: '0.08em',
          padding: '4px 10px', borderRadius: 6, cursor: 'pointer', transition: 'all 0.15s',
          background: showExternal ? 'rgba(191,95,255,0.08)' : 'rgba(255,255,255,0.03)',
          color: showExternal ? 'var(--purple)' : 'var(--text-lo)',
          border: `1px solid ${showExternal ? 'rgba(191,95,255,0.3)' : 'var(--border-dim)'}`,
        }}>{showExternal ? '◎ HIDE EXTERNAL' : '◎ SHOW EXTERNAL'}</button>
        <span className="ml-auto" style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
          {lastUpdate !== '—' ? `Updated ${lastUpdate} · ${totalEvents.toLocaleString()} events` : 'Fetching…'}
        </span>
      </div>

      {/* Main area */}
      <div className="flex gap-4" style={{ minHeight: 580 }}>

        {/* Graph canvas */}
        <div
          ref={containerRef}
          className="flex-1 rounded-xl relative"
          style={{
            background: 'rgba(0,4,12,0.97)',
            border: '1px solid var(--border-dim)',
            minHeight: 560,
            overflow: 'hidden',
          }}>

          {/* Grid background */}
          <div className="absolute inset-0 pointer-events-none" style={{
            backgroundImage:
              'linear-gradient(rgba(0,212,255,0.025) 1px, transparent 1px),' +
              'linear-gradient(90deg, rgba(0,212,255,0.025) 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }} />

          {/* Empty / loading overlay */}
          {(loading || displayNodes.length === 0) && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3"
              style={{ pointerEvents: 'none' }}>
              {loading ? (
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-lo)' }}>
                  Loading topology…
                </div>
              ) : (
                <>
                  <svg width="44" height="44" viewBox="0 0 24 24" fill="none"
                    stroke="rgba(0,212,255,0.25)" strokeWidth="1">
                    <circle cx="12" cy="5" r="3"/><circle cx="5" cy="19" r="3"/>
                    <circle cx="19" cy="19" r="3"/>
                    <line x1="12" y1="8" x2="7" y2="16"/>
                    <line x1="12" y1="8" x2="17" y2="16"/>
                  </svg>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-lo)', textAlign: 'center' }}>
                    {fetchError
                      ? 'API error — see banner above'
                      : capturing
                        ? 'Building topology from live traffic…'
                        : 'Start packet capture to build the graph'}
                  </div>
                </>
              )}
            </div>
          )}

          {/* SVG — always rendered so ResizeObserver measurement is accurate */}
          <svg
            width={dims.W}
            height={dims.H}
            style={{ display: 'block', position: 'absolute', top: 0, left: 0 }}>
            <defs>
              {(['Low', 'Medium', 'High', 'Critical'] as const).map(r => (
                <filter key={r} id={`g-${r}`} x="-60%" y="-60%" width="220%" height="220%">
                  <feGaussianBlur stdDeviation="4" result="b"/>
                  <feFlood floodColor={RISK_COL[r]} floodOpacity={0.6} result="c"/>
                  <feComposite in="c" in2="b" operator="in" result="s"/>
                  <feMerge><feMergeNode in="s"/><feMergeNode in="SourceGraphic"/></feMerge>
                </filter>
              ))}
            </defs>

            {/* Edges */}
            {visibleEdges.map((e, i) => {
              const sn = displayNodes.find(n => n.id === e.source);
              const tn = displayNodes.find(n => n.id === e.target);
              if (!sn || !tn) return null;
              const lit = selected === e.source || selected === e.target
                       || hovered === e.source || hovered === e.target;
              const col = e.has_threat ? 'rgba(255,45,85,0.7)' : protoColor(e.protocols);
              const sw  = Math.max(0.5, Math.min(3.5, Math.log10(e.count + 1) * 1.5));
              return (
                <line key={i}
                  x1={sn.x} y1={sn.y} x2={tn.x} y2={tn.y}
                  stroke={col}
                  strokeWidth={lit ? sw + 1.5 : sw}
                  strokeOpacity={lit ? 1 : 0.3}
                  strokeDasharray={e.has_threat ? '5 4' : '4 9'}
                  strokeDashoffset={dashOffset}
                />
              );
            })}

            {/* Nodes */}
            {visibleNodes.map(node => {
              const r   = nodeR(node);
              const col = RISK_COL[node.risk_level] ?? '#00ff9d';
              const isH = hovered === node.id;
              const isS = selected === node.id;
              const lit = isH || isS;
              return (
                <g key={node.id}
                  style={{ cursor: 'pointer' }}
                  onMouseEnter={() => setHovered(node.id)}
                  onMouseLeave={() => setHovered(null)}
                  onClick={() => setSelected(p => p === node.id ? null : node.id)}>

                  {/* Selection ring */}
                  {isS && (
                    <circle cx={node.x} cy={node.y} r={r + 8}
                      fill="none" stroke={col} strokeWidth={1.5}
                      strokeOpacity={0.6} strokeDasharray="4 3"/>
                  )}

                  {/* Glow halo */}
                  {(lit || node.threat_count > 0) && (
                    <circle cx={node.x} cy={node.y} r={r + 4}
                      fill={`${col}10`} stroke="none"/>
                  )}

                  {/* Body */}
                  <circle cx={node.x} cy={node.y} r={r}
                    fill={`${col}${node.is_local ? '20' : '10'}`}
                    stroke={col}
                    strokeWidth={lit ? 2.5 : 1.5}
                    strokeOpacity={lit ? 1 : 0.65}
                    filter={lit || node.threat_count > 0 ? `url(#g-${node.risk_level})` : undefined}
                  />

                  {/* Inner dot */}
                  <circle cx={node.x} cy={node.y} r={node.is_local ? 3.5 : 2}
                    fill={col} opacity={node.is_local ? 0.9 : 0.45}/>

                  {/* Threat badge */}
                  {node.threat_count > 0 && (
                    <g>
                      <circle cx={node.x + r * 0.68} cy={node.y - r * 0.68} r={5.5}
                        fill="#ff2d55" stroke="rgba(0,4,12,0.9)" strokeWidth={1.5}/>
                      <text x={node.x + r * 0.68} y={node.y - r * 0.68 + 4}
                        textAnchor="middle"
                        style={{ fill: '#fff', fontFamily: 'monospace', fontSize: 7, fontWeight: 700,
                          pointerEvents: 'none' }}>
                        {node.threat_count > 9 ? '9+' : node.threat_count}
                      </text>
                    </g>
                  )}

                  {/* Label */}
                  {(node.is_local || lit) && (
                    <text x={node.x} y={node.y + r + 13}
                      textAnchor="middle"
                      style={{
                        fill: lit ? col : 'rgba(255,255,255,0.35)',
                        fontFamily: 'monospace',
                        fontSize: lit ? 10 : 8,
                        pointerEvents: 'none',
                      }}>
                      {node.id.length > 20
                        ? node.id.slice(0, 8) + '…' + node.id.slice(-6)
                        : node.id}
                    </text>
                  )}
                </g>
              );
            })}

            {/* Hover tooltip (pure SVG, no foreignObject) */}
            {hoveredNode && selected !== hoveredNode.id && (
              <NodeTooltip node={hoveredNode} W={dims.W} H={dims.H} />
            )}
          </svg>

          {/* Watermark */}
          <div className="absolute bottom-2 left-3" style={{
            fontFamily: 'monospace', fontSize: 8,
            color: 'rgba(0,212,255,0.15)', pointerEvents: 'none', letterSpacing: '0.1em',
          }}>
            NETSHIELD · FORCE GRAPH
          </div>
        </div>

        {/* Right panel */}
        <div className="flex flex-col gap-3" style={{ width: 216, flexShrink: 0 }}>

          {/* Selected node */}
          {selectedNode ? (
            <div className="rounded-xl p-4 bracket-all"
              style={{ background: 'rgba(3,10,22,0.95)',
                border: `1px solid ${RISK_COL[selectedNode.risk_level] ?? 'var(--border-mid)'}35`,
                backdropFilter: 'blur(16px)' }}>
              <div className="flex items-center justify-between mb-3">
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)',
                  letterSpacing: '0.1em' }}>
                  {selectedNode.is_local ? '◉ LOCAL' : '◎ EXTERNAL'}
                </span>
                <button onClick={() => setSelected(null)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--text-lo)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>✕</button>
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10,
                color: RISK_COL[selectedNode.risk_level] ?? '#00ff9d',
                wordBreak: 'break-all', lineHeight: 1.5, marginBottom: 10, fontWeight: 700 }}>
                {selectedNode.id}
              </div>
              <div className="space-y-2">
                {[
                  { l: 'Packets',  v: selectedNode.packet_count.toLocaleString(), c: 'var(--cyan)' },
                  { l: 'Threats',  v: selectedNode.threat_count.toString(),        c: selectedNode.threat_count > 0 ? 'var(--red)' : 'var(--text-lo)' },
                  { l: 'Trust',    v: `${selectedNode.trust_score}%`,             c: selectedNode.trust_score >= 80 ? 'var(--green)' : 'var(--amber)' },
                  { l: 'Risk',     v: selectedNode.risk_level,                    c: RISK_COL[selectedNode.risk_level] },
                ].map(m => (
                  <div key={m.l} className="flex justify-between items-center">
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>{m.l}</span>
                    <span style={{ fontFamily: 'var(--font-display)', fontSize: 11, color: m.c, fontWeight: 700 }}>{m.v}</span>
                  </div>
                ))}
              </div>
              {selectedNode.protocols.length > 0 && (
                <div className="mt-3">
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)',
                    letterSpacing: '0.1em', marginBottom: 4 }}>PROTOCOLS</div>
                  <div className="flex flex-wrap gap-1">
                    {selectedNode.protocols.map(p => (
                      <span key={p} style={{
                        fontFamily: 'var(--font-mono)', fontSize: 8, borderRadius: 4, padding: '2px 5px',
                        background: `${PROTO_COL[p] ?? '#555'}18`,
                        color: PROTO_COL[p] ?? '#888',
                        border: `1px solid ${PROTO_COL[p] ?? '#555'}35`,
                      }}>{p}</span>
                    ))}
                  </div>
                </div>
              )}
              {/* Connections */}
              {(() => {
                const conn = edges.filter(e => e.source === selectedNode.id || e.target === selectedNode.id);
                if (!conn.length) return null;
                return (
                  <div className="mt-3">
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)',
                      letterSpacing: '0.1em', marginBottom: 4 }}>CONNECTIONS ({conn.length})</div>
                    <div style={{ maxHeight: 110, overflowY: 'auto' }}>
                      {conn.slice(0, 8).map((e, i) => {
                        const peer = e.source === selectedNode.id ? e.target : e.source;
                        return (
                          <div key={i} className="flex items-center justify-between gap-1 py-0.5">
                            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8,
                              color: 'var(--text-lo)', overflow: 'hidden', textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap', flex: 1 }}>
                              {peer.length > 14 ? peer.slice(0, 6) + '…' + peer.slice(-5) : peer}
                            </div>
                            <div style={{ fontFamily: 'var(--font-display)', fontSize: 9,
                              color: e.has_threat ? 'var(--red)' : 'var(--text-lo)', flexShrink: 0 }}>
                              {e.count}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })()}
            </div>
          ) : (
            <div className="rounded-xl p-4 bracket-all"
              style={{ background: 'rgba(3,10,22,0.90)', border: '1px solid var(--border-dim)' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)',
                letterSpacing: '0.1em', marginBottom: 6 }}>// CLICK A NODE</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', lineHeight: 1.6 }}>
                Select any node to inspect traffic stats, trust scores and connections.
              </div>
            </div>
          )}

          {/* Legend */}
          <div className="rounded-xl p-4 bracket-all"
            style={{ background: 'rgba(3,10,22,0.90)', border: '1px solid var(--border-dim)' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)',
              letterSpacing: '0.1em', marginBottom: 8 }}>// RISK LEVEL</div>
            <div className="space-y-2 mb-4">
              {(['Low', 'Medium', 'High', 'Critical'] as const).map(r => {
                const count = displayNodes.filter(n => n.risk_level === r).length;
                return (
                  <div key={r} className="flex items-center gap-2">
                    <div style={{ width: 9, height: 9, borderRadius: '50%',
                      background: RISK_COL[r], flexShrink: 0,
                      boxShadow: `0 0 5px ${RISK_COL[r]}` }} />
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9,
                      color: 'var(--text-mid)', flex: 1 }}>{r}</span>
                    <span style={{ fontFamily: 'var(--font-display)', fontSize: 11,
                      color: RISK_COL[r], fontWeight: 700 }}>{count}</span>
                  </div>
                );
              })}
            </div>

            <div style={{ borderTop: '1px solid var(--border-dim)', paddingTop: 10, marginBottom: 8 }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)',
                letterSpacing: '0.1em', marginBottom: 6 }}>// EDGE PROTOCOL</div>
              {Object.entries(PROTO_COL).slice(0, 5).map(([p, col]) => (
                <div key={p} className="flex items-center gap-2 mb-1.5">
                  <div style={{ width: 14, height: 2, background: col, borderRadius: 1 }} />
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-mid)' }}>{p}</span>
                </div>
              ))}
              <div className="flex items-center gap-2">
                <div style={{ width: 14, height: 2, background: 'rgba(255,45,85,0.8)', borderRadius: 1 }} />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--red)' }}>THREAT</span>
              </div>
            </div>

            <div style={{ borderTop: '1px solid var(--border-dim)', paddingTop: 10 }}>
              <div className="flex items-center gap-2 mb-1">
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--cyan)' }} />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-mid)' }}>◉ Local</span>
              </div>
              <div className="flex items-center gap-2">
                <div style={{ width: 8, height: 8, borderRadius: '50%',
                  background: 'rgba(0,212,255,0.35)', border: '1px solid rgba(0,212,255,0.5)' }} />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-mid)' }}>◎ External</span>
              </div>
            </div>
          </div>

          {/* Top traffic */}
          {displayNodes.length > 0 && (
            <div className="rounded-xl p-4 bracket-all"
              style={{ background: 'rgba(3,10,22,0.90)', border: '1px solid var(--border-dim)' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)',
                letterSpacing: '0.1em', marginBottom: 8 }}>// TOP TRAFFIC</div>
              <div className="space-y-2">
                {[...displayNodes]
                  .sort((a, b) => b.packet_count - a.packet_count)
                  .slice(0, 5)
                  .map(n => (
                    <div key={n.id} className="cursor-pointer"
                      onClick={() => setSelected(p => p === n.id ? null : n.id)}>
                      <div className="flex items-center justify-between mb-0.5">
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 8,
                          color: RISK_COL[n.risk_level],
                          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 130 }}>
                          {n.id.length > 14 ? n.id.slice(0, 6) + '…' + n.id.slice(-6) : n.id}
                        </span>
                        <span style={{ fontFamily: 'var(--font-display)', fontSize: 9,
                          color: 'var(--text-mid)', flexShrink: 0 }}>
                          {n.packet_count.toLocaleString()}
                        </span>
                      </div>
                      <div className="track" style={{ height: 2 }}>
                        <div className="track-fill"
                          style={{ width: `${(n.packet_count / maxPkts) * 100}%`,
                            background: RISK_COL[n.risk_level] }} />
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div style={{ height: 32 }} />
    </>
  );
}
