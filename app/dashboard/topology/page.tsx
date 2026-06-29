'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { getTopology, getNetworks, getRiskyNodes, getCaptureStatus, type TopologyNode, type TopologyEdge, type RiskyNode, type NetworkInfo } from '../../../lib/api';

// ── Types ─────────────────────────────────────────────────────────────────────

interface PhysNode extends TopologyNode {
  x: number; y: number;
  vx: number; vy: number;
}

// ── Constants ─────────────────────────────────────────────────────────────────

const RISK_COL: Record<string, string> = {
  Low: '#059669', Medium: '#d97706', High: '#dc2626', Critical: '#7c3aed',
};
const PROTO_COL: Record<string, string> = {
  HTTPS: '#0284c7', HTTP: '#d97706', DNS: '#059669',
  TCP: '#8888cc', UDP: '#9966cc', ICMP: '#ea6c1a', UNKNOWN: '#555577',
};
function protoColor(protocols: string[]) {
  for (const p of protocols) if (PROTO_COL[p]) return PROTO_COL[p];
  return PROTO_COL.UNKNOWN;
}
function nodeR(n: PhysNode) {
  return Math.max(9, Math.min(28, 9 + Math.log10(n.packet_count + 1) * 7));
}

// ── CIDR helper (IPv4 only) ────────────────────────────────────────────────────

function ipInCidr(ip: string, cidr: string): boolean {
  try {
    const clean = ip.split('%')[0];
    const [range, bitsStr] = cidr.split('/');
    const bits = bitsStr !== undefined ? parseInt(bitsStr, 10) : 32;
    const toNum = (s: string) => s.split('.').reduce((acc, b) => (acc * 256) + parseInt(b, 10), 0);
    if (!/^\d{1,3}(\.\d{1,3}){3}$/.test(clean) || !/^\d{1,3}(\.\d{1,3}){3}$/.test(range)) return false;
    if (bits === 0) return true;
    const mask = bits === 32 ? 0xFFFFFFFF : ~(0xFFFFFFFF >>> bits) >>> 0;
    return (toNum(clean) & mask) === (toNum(range) & mask);
  } catch { return false; }
}

// Derive the /24 subnet a (IPv4) node belongs to, e.g. "10.0.0.7" → "10.0.0.0/24".
// Returns null for non-IPv4 IDs (IPv6, hostnames) so they can be grouped separately.
function ipv4Slash24(ip: string): string | null {
  const clean = ip.split('%')[0];
  const m = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.\d{1,3}$/.exec(clean);
  return m ? `${m[1]}.${m[2]}.${m[3]}.0/24` : null;
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

const LABEL_COL = 'rgba(71,85,105,0.95)';   // dark slate label text for the light canvas

function NodeTooltip({ node, W, H }: { node: PhysNode; W: number; H: number }) {
  const col = RISK_COL[node.risk_level] ?? '#059669';
  const r = nodeR(node);

  const sent = node.packets_sent ?? 0;
  const recv = node.packets_received ?? node.packet_count;
  const topAttack = node.attacks && node.attacks.length > 0 ? node.attacks[0] : null;

  const rows: Array<{ label: string; value: string; color: string }> = [
    { label: 'IP', value: shortIp(node.id), color: col },
    { label: 'Scope', value: node.is_local ? 'LOCAL' : 'EXTERNAL', color: node.is_local ? '#0284c7' : '#7c3aed' },
    { label: 'Sent', value: sent.toLocaleString(), color: '#0284c7' },
    { label: 'Received', value: recv.toLocaleString(), color: '#0284c7' },
    { label: 'Threats', value: node.threat_count.toString(), color: node.threat_count > 0 ? '#dc2626' : LABEL_COL },
    { label: 'Trust', value: `${node.trust_score}%`, color: node.trust_score >= 80 ? '#059669' : node.trust_score >= 50 ? '#d97706' : '#dc2626' },
    { label: 'Risk', value: node.risk_level, color: col },
    { label: 'Status', value: (node.status ?? 'active').toUpperCase(), color: statusColor(node.status) },
  ];
  if (topAttack) rows.push({ label: 'Attack', value: topAttack, color: '#ea580c' });
  node.protocols.slice(0, 2).forEach(p => rows.push({ label: 'Proto', value: p, color: PROTO_COL[p] ?? '#64748b' }));

  const tipW = 232, lineH = 16, padTop = 14;
  const tipH = padTop + rows.length * lineH + 6;
  const tx = node.x + r + 10 + tipW > W ? node.x - r - 10 - tipW : node.x + r + 10;
  const ty = Math.max(8, Math.min(H - tipH - 8, node.y - tipH / 2));

  return (
    <g style={{ pointerEvents: 'none' }}>
      <rect x={tx} y={ty} width={tipW} height={tipH} rx={8}
        fill="rgba(255,255,255,0.98)" stroke={`${col}88`} strokeWidth={1.25}/>
      {rows.map((row, i) => (
        <g key={i}>
          <text x={tx + 11} y={ty + padTop + 2 + i * lineH}
            style={{ fill: LABEL_COL, fontFamily: 'monospace', fontSize: 9 }}>
            {row.label}
          </text>
          <text x={tx + tipW - 11} y={ty + padTop + 2 + i * lineH}
            textAnchor="end"
            style={{ fill: row.color, fontFamily: 'monospace', fontSize: 9, fontWeight: 700 }}>
            {row.value}
          </text>
        </g>
      ))}
    </g>
  );
}

function shortIp(ip: string) {
  return ip.length > 24 ? ip.slice(0, 11) + '…' + ip.slice(-9) : ip;
}
function statusColor(status?: string) {
  switch (status) {
    case 'blocked':      return '#dc2626';
    case 'quarantined':  return '#7c3aed';
    case 'alerted':      return '#d97706';
    case 'restricted':   return '#d97706';
    default:             return '#059669';
  }
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
  const [riskyNodes,   setRiskyNodes]   = useState<RiskyNode[]>([]);
  const [networks,     setNetworks]     = useState<NetworkInfo[]>([]);

  // Network + subnet selection state — both default to "All" (user picks explicitly).
  const [selectedNetwork, setSelectedNetwork] = useState<string | null>(null);  // null = All Networks
  const [activeSubnet,    setActiveSubnet]    = useState('');                     // '' = All Subnets

  const selectedNetworkInfo = networks.find(n => n.id === selectedNetwork) ?? null;

  // Annotate each configured network with how many *live* nodes actually fall in
  // it, so the user never picks an empty network and blanks the map.
  const networksWithCounts = networks.map(net => ({
    ...net,
    count: displayNodes.filter(n => ipInCidr(n.id, net.subnet)).length,
  }));

  // Subnets the user can pick from are derived from the ACTUAL nodes present
  // (their /24 buckets), not from static config — guaranteeing every option has
  // nodes. When a network is selected, only show /24s that fall within it.
  const availableSubnets = (() => {
    const counts = new Map<string, number>();
    for (const n of displayNodes) {
      if (selectedNetworkInfo && !ipInCidr(n.id, selectedNetworkInfo.subnet)) continue;
      const s = ipv4Slash24(n.id);
      if (s) counts.set(s, (counts.get(s) ?? 0) + 1);
    }
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .map(([subnet, count]) => ({
        subnet,
        label: `${subnet} · ${count} node${count === 1 ? '' : 's'}`,
      }));
  })();

  // Picking a network does NOT auto-apply a subnet — it just narrows the subnet
  // options and clears any previously chosen subnet so the user selects again.
  function handleNetworkChange(netId: string | null) {
    setSelectedNetwork(netId);
    setActiveSubnet('');
  }

  // User explicitly selects the subnet to filter by ('' = All Subnets).
  function handleSubnetChange(cidr: string) {
    setActiveSubnet(cidr);
  }

  // Clear back to "All Networks, All Subnets".
  function clearFilters() {
    setSelectedNetwork(null);
    setActiveSubnet('');
  }

  // Fetch networks on mount — default is "All Networks" (null)
  useEffect(() => {
    getNetworks().then(data => {
      setNetworks(data.networks);
    }).catch(() => {
      setNetworks([]);
    });
  }, []);

  // Always fetch ALL topology — filtering is done client-side via activeSubnet
  const fetchData = useCallback(async () => {
    try {
      const [topo, status, risky] = await Promise.all([
        getTopology(), getCaptureStatus(), getRiskyNodes().catch(() => null),
      ]);
      setFetchError(null);
      setCapturing(status.is_running);
      setTotalEvents(topo.total_events);
      setLastUpdate(new Date().toLocaleTimeString());
      if (risky) setRiskyNodes(risky.risky_nodes);
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
  }, []); // no deps — always fetches all topology

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

  // Effective CIDR to filter by: an explicitly chosen subnet wins; otherwise
  // fall back to the selected network's own subnet. Empty = no spatial filter.
  const filterCidr = activeSubnet || selectedNetworkInfo?.subnet || '';

  const visibleNodes = displayNodes.filter(n => {
    if (filterCidr && !ipInCidr(n.id, filterCidr)) return false;
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
            background: capturing ? 'rgba(5,150,105,0.09)' : 'rgba(0,0,0,0.10)',
            color: capturing ? 'var(--green)' : 'var(--text-lo)',
            border: `1px solid ${capturing ? 'rgba(5,150,105,0.28)' : 'rgba(0,0,0,0.25)'}`,
            fontFamily: 'var(--font-display)', fontSize: 9, letterSpacing: '0.1em', padding: '5px 10px',
          }}>
            <span className={`pulse-dot ${capturing ? 'pulse-green' : 'pulse-amber'}`} style={{ width: 4, height: 4 }} />
            {capturing ? 'LIVE' : 'IDLE'}
          </div>
          <button onClick={() => { setLoading(true); fetchData(); }}
            style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--cyan)',
              background: 'rgba(2,132,199,0.08)', border: '1px solid rgba(2,132,199,0.22)',
              borderRadius: 6, padding: '5px 10px', cursor: 'pointer', letterSpacing: '0.1em' }}>
            ↻ REFRESH
          </button>
        </div>
      </div>

      {/* Network & Subnet Selector Panel */}
      <div className="rounded-xl mb-4 p-4"
        style={{ background: 'rgba(255,255,255,0.97)', border: '1px solid #000000', boxShadow: '0 1px 4px rgba(0,0,0,0.12)' }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)',
          letterSpacing: '0.12em', marginBottom: 12 }}>
          NETWORK &amp; SUBNET FILTER
        </div>
        <div className="flex flex-wrap items-end gap-4">

          {/* Network dropdown */}
          <div style={{ flex: '1 1 200px', minWidth: 180 }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)',
              letterSpacing: '0.1em', marginBottom: 5 }}>NETWORK</div>
            <select
              value={selectedNetwork ?? ''}
              onChange={e => handleNetworkChange(e.target.value || null)}
              style={{
                width: '100%',
                fontFamily: 'var(--font-ui)', fontSize: 12,
                padding: '8px 12px', borderRadius: 8,
                background: 'rgba(2,132,199,0.06)',
                border: '1px solid rgba(2,132,199,0.30)',
                color: 'var(--text-hi)',
                cursor: 'pointer', outline: 'none',
                appearance: 'none',
                backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%230284c7' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E")`,
                backgroundRepeat: 'no-repeat',
                backgroundPosition: 'right 10px center',
                paddingRight: 32,
              }}
            >
              <option value="">All Networks (unfiltered)</option>
              {networksWithCounts.map(net => (
                <option key={net.id} value={net.id} disabled={net.count === 0}>
                  {net.name} · {net.count} node{net.count === 1 ? '' : 's'}
                  {net.count === 0 ? ' (none live)' : ''}
                </option>
              ))}
            </select>
            {selectedNetworkInfo && (
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', marginTop: 4 }}>
                {selectedNetworkInfo.description} · {selectedNetworkInfo.type}
              </div>
            )}
          </div>

          {/* Subnet dropdown */}
          <div style={{ flex: '1 1 200px', minWidth: 180 }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)',
              letterSpacing: '0.1em', marginBottom: 5 }}>SUBNET</div>
            <select
              value={activeSubnet}
              onChange={e => handleSubnetChange(e.target.value)}
              style={{
                width: '100%',
                fontFamily: 'var(--font-mono)', fontSize: 11,
                padding: '8px 12px', borderRadius: 8,
                background: 'rgba(2,132,199,0.06)',
                border: '1px solid rgba(2,132,199,0.30)',
                color: 'var(--text-hi)',
                cursor: 'pointer', outline: 'none',
                appearance: 'none',
                backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%230284c7' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E")`,
                backgroundRepeat: 'no-repeat',
                backgroundPosition: 'right 10px center',
                paddingRight: 32,
              }}
            >
              <option value="">All Subnets</option>
              {availableSubnets.map(s => (
                <option key={s.subnet} value={s.subnet}>
                  {s.label}
                </option>
              ))}
            </select>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', marginTop: 4 }}>
              {filterCidr
                ? `${visibleNodes.length} node${visibleNodes.length === 1 ? '' : 's'} in ${filterCidr}`
                : 'No subnet filter — showing all nodes'}
            </div>
          </div>

          {/* Clear button */}
          <div className="flex gap-2" style={{ paddingBottom: 22 }}>
            <button
              onClick={clearFilters}
              disabled={selectedNetwork === null && activeSubnet === ''}
              style={{
                fontFamily: 'var(--font-display)', fontSize: 9, letterSpacing: '0.1em',
                padding: '8px 14px', borderRadius: 7,
                cursor: selectedNetwork === null && activeSubnet === '' ? 'default' : 'pointer',
                opacity: selectedNetwork === null && activeSubnet === '' ? 0.45 : 1,
                background: 'rgba(0,0,0,0.05)', border: '1px solid var(--border-dim)',
                color: 'var(--text-lo)',
              }}
            >
              CLEAR
            </button>
          </div>
        </div>

        {/* Network quick-select chips */}
        {networks.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3" style={{ borderTop: '1px solid rgba(0,0,0,0.06)', paddingTop: 10 }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)',
              letterSpacing: '0.1em', alignSelf: 'center' }}>QUICK SELECT:</span>
            <button
              onClick={() => handleNetworkChange(null)}
              style={{
                fontFamily: 'var(--font-mono)', fontSize: 8, padding: '3px 9px', borderRadius: 5,
                cursor: 'pointer', transition: 'all 0.15s',
                background: selectedNetwork === null ? 'rgba(2,132,199,0.12)' : 'transparent',
                border: `1px solid ${selectedNetwork === null ? 'rgba(2,132,199,0.40)' : 'var(--border-dim)'}`,
                color: selectedNetwork === null ? 'var(--cyan)' : 'var(--text-lo)',
              }}
            >
              ALL
            </button>
            {networksWithCounts.map(net => (
              <button
                key={net.id}
                onClick={() => net.count > 0 && handleNetworkChange(net.id)}
                disabled={net.count === 0}
                style={{
                  fontFamily: 'var(--font-mono)', fontSize: 8, padding: '3px 9px', borderRadius: 5,
                  cursor: net.count === 0 ? 'not-allowed' : 'pointer', transition: 'all 0.15s',
                  opacity: net.count === 0 ? 0.4 : 1,
                  background: selectedNetwork === net.id ? 'rgba(2,132,199,0.12)' : 'transparent',
                  border: `1px solid ${selectedNetwork === net.id ? 'rgba(2,132,199,0.40)' : 'var(--border-dim)'}`,
                  color: selectedNetwork === net.id ? 'var(--cyan)' : 'var(--text-lo)',
                }}
                title={`${net.subnet} · ${net.count} live node${net.count === 1 ? '' : 's'}`}
              >
                {net.name} ({net.count})
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Error banner */}
      {fetchError && (
        <div className="rounded-xl px-4 py-3 mb-4"
          style={{ background: 'rgba(220,38,38,0.08)', border: '1px solid rgba(220,38,38,0.28)' }}>
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
            style={{ background: '#ffffff', border: '1px solid #000000', boxShadow: '0 1px 4px rgba(0,0,0,0.15)', backdropFilter: 'blur(12px)' }}>
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
              background: active ? `${col}18` : 'rgba(0,0,0,0.10)',
              color: active ? col : 'var(--text-lo)',
              border: `1px solid ${active ? `${col}50` : 'var(--border-dim)'}`,
            }}>{r === 'all' ? 'ALL' : r.toUpperCase()}</button>
          );
        })}
        <div className="w-px h-5 hidden sm:block" style={{ background: 'var(--border-dim)' }} />
        <button onClick={() => setShowExternal(v => !v)} style={{
          fontFamily: 'var(--font-display)', fontSize: 9, letterSpacing: '0.08em',
          padding: '4px 10px', borderRadius: 6, cursor: 'pointer', transition: 'all 0.15s',
          background: showExternal ? 'rgba(124,58,237,0.10)' : 'rgba(0,0,0,0.10)',
          color: showExternal ? 'var(--purple)' : 'var(--text-lo)',
          border: `1px solid ${showExternal ? 'rgba(124,58,237,0.32)' : 'var(--border-dim)'}`,
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
            background: 'linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%)',
            border: '1px solid #000000',
            boxShadow: 'inset 0 1px 6px rgba(15,23,42,0.06)',
            minHeight: 560,
            overflow: 'hidden',
          }}>

          {/* Grid background */}
          <div className="absolute inset-0 pointer-events-none" style={{
            backgroundImage:
              'linear-gradient(rgba(2,132,199,0.08) 1px, transparent 1px),' +
              'linear-gradient(90deg, rgba(2,132,199,0.08) 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }} />

          {/* Empty / loading overlay — only shown when there are no nodes to render */}
          {displayNodes.length === 0 && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3"
              style={{ pointerEvents: 'none' }}>
              <svg width="44" height="44" viewBox="0 0 24 24" fill="none"
                stroke="rgba(2,132,199,0.28)" strokeWidth="1">
                <circle cx="12" cy="5" r="3"/><circle cx="5" cy="19" r="3"/>
                <circle cx="19" cy="19" r="3"/>
                <line x1="12" y1="8" x2="7" y2="16"/>
                <line x1="12" y1="8" x2="17" y2="16"/>
              </svg>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-lo)', textAlign: 'center', lineHeight: 1.7 }}>
                {loading
                  ? 'Loading topology…'
                  : fetchError
                    ? 'API error — see banner above'
                    : capturing
                      ? 'Building topology from live traffic…'
                      : <>
                          No nodes detected yet.<br/>
                          <span style={{ fontSize: 10, opacity: 0.7 }}>
                            Start live capture or run a simulation to generate traffic.
                          </span>
                        </>}
              </div>
            </div>
          )}

          {/* Filter matched nothing — distinct from "no data at all" so the user
              understands the blank canvas is a filter, not a broken graph. */}
          {displayNodes.length > 0 && visibleNodes.length === 0 && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3"
              style={{ pointerEvents: 'none' }}>
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none"
                stroke="rgba(217,119,6,0.55)" strokeWidth="1.4">
                <circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/>
                <line x1="8" y1="11" x2="14" y2="11"/>
              </svg>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-mid)',
                textAlign: 'center', lineHeight: 1.7 }}>
                No nodes match this filter.<br/>
                <span style={{ fontSize: 10, color: 'var(--text-lo)' }}>
                  {filterCidr
                    ? `Nothing in ${filterCidr}${filterRisk !== 'all' ? ` at ${filterRisk} risk` : ''}.`
                    : 'Adjust the risk / external filters.'}
                </span>
              </div>
              <button
                onClick={() => { clearFilters(); setFilterRisk('all'); setShowExternal(true); }}
                style={{
                  pointerEvents: 'auto',
                  fontFamily: 'var(--font-display)', fontSize: 9, letterSpacing: '0.1em',
                  padding: '6px 14px', borderRadius: 7, cursor: 'pointer',
                  background: 'rgba(2,132,199,0.08)', border: '1px solid rgba(2,132,199,0.30)',
                  color: 'var(--cyan)',
                }}>
                CLEAR FILTERS
              </button>
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
              {/* Directional arrowheads (src → dst) */}
              <marker id="arrow-normal" viewBox="0 0 10 10" refX="9" refY="5"
                markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M0,0 L10,5 L0,10 z" fill="rgba(71,85,105,0.85)" />
              </marker>
              <marker id="arrow-threat" viewBox="0 0 10 10" refX="9" refY="5"
                markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
                <path d="M0,0 L10,5 L0,10 z" fill="rgba(220,38,38,0.95)" />
              </marker>
            </defs>

            {/* Edges (directed src → dst, arrowhead stops at target node edge) */}
            {visibleEdges.map((e, i) => {
              const sn = displayNodes.find(n => n.id === e.source);
              const tn = displayNodes.find(n => n.id === e.target);
              if (!sn || !tn) return null;
              const lit = selected === e.source || selected === e.target
                       || hovered === e.source || hovered === e.target;
              const col = e.has_threat ? 'rgba(220,38,38,0.75)' : protoColor(e.protocols);
              const sw  = Math.max(0.6, Math.min(3.5, Math.log10(e.count + 1) * 1.5));
              // Pull the line endpoints back to each node's rim so the arrow is visible
              const dx = tn.x - sn.x, dy = tn.y - sn.y;
              const dist = Math.sqrt(dx * dx + dy * dy) || 1;
              const ux = dx / dist, uy = dy / dist;
              const sr = nodeR(sn) + 2, tr = nodeR(tn) + 7;
              const x1 = sn.x + ux * sr, y1 = sn.y + uy * sr;
              const x2 = tn.x - ux * tr, y2 = tn.y - uy * tr;
              return (
                <line key={i}
                  x1={x1} y1={y1} x2={x2} y2={y2}
                  stroke={col}
                  strokeWidth={lit ? sw + 1.5 : sw}
                  strokeOpacity={lit ? 1 : 0.45}
                  strokeDasharray={e.has_threat ? '5 4' : '4 9'}
                  strokeDashoffset={dashOffset}
                  markerEnd={`url(#${e.has_threat ? 'arrow-threat' : 'arrow-normal'})`}
                />
              );
            })}

            {/* Nodes */}
            {visibleNodes.map(node => {
              const r   = nodeR(node);
              const col = RISK_COL[node.risk_level] ?? '#059669';
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

                  {/* Enforcement-status ring (blocked / quarantined) */}
                  {(node.status === 'blocked' || node.status === 'quarantined') && (
                    <circle cx={node.x} cy={node.y} r={r + 5}
                      fill="none"
                      stroke={node.status === 'blocked' ? '#dc2626' : '#7c3aed'}
                      strokeWidth={2}
                      strokeDasharray={node.status === 'quarantined' ? '3 3' : undefined}
                      strokeOpacity={0.95}/>
                  )}

                  {/* Glow halo */}
                  {(lit || node.threat_count > 0) && (
                    <circle cx={node.x} cy={node.y} r={r + 4}
                      fill={`${col}10`} stroke="none"/>
                  )}

                  {/* Body */}
                  <circle cx={node.x} cy={node.y} r={r}
                    fill={`${col}${node.is_local ? '26' : '14'}`}
                    stroke={col}
                    strokeWidth={lit ? 2.5 : 1.5}
                    strokeOpacity={lit ? 1 : 0.8}
                    filter={lit || node.threat_count > 0 ? `url(#g-${node.risk_level})` : undefined}
                  />

                  {/* Inner dot */}
                  <circle cx={node.x} cy={node.y} r={node.is_local ? 3.5 : 2}
                    fill={col} opacity={node.is_local ? 0.9 : 0.45}/>

                  {/* Threat badge */}
                  {node.threat_count > 0 && (
                    <g>
                      <circle cx={node.x + r * 0.68} cy={node.y - r * 0.68} r={5.5}
                        fill="#dc2626" stroke="rgba(255,255,255,0.95)" strokeWidth={1.5}/>
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
                        fill: lit ? col : 'rgba(51,65,85,0.92)',
                        fontFamily: 'monospace',
                        fontSize: lit ? 10 : 8,
                        fontWeight: lit ? 700 : 500,
                        paintOrder: 'stroke',
                        stroke: 'rgba(255,255,255,0.92)',
                        strokeWidth: 2.6,
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
            color: 'rgba(2,132,199,0.30)', pointerEvents: 'none', letterSpacing: '0.1em',
          }}>
            NETSHIELD · FORCE GRAPH
          </div>
        </div>

        {/* Right panel */}
        <div className="flex flex-col gap-3" style={{ width: 216, flexShrink: 0 }}>

          {/* Selected node */}
          {selectedNode ? (
            <div className="rounded-xl p-4 bracket-all"
              style={{ background: 'rgba(255,255,255,0.96)',
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
                color: RISK_COL[selectedNode.risk_level] ?? '#059669',
                wordBreak: 'break-all', lineHeight: 1.5, marginBottom: 10, fontWeight: 700 }}>
                {selectedNode.id}
              </div>
              <div className="space-y-2">
                {[
                  { l: 'Pkts Sent',  v: (selectedNode.packets_sent ?? 0).toLocaleString(), c: 'var(--cyan)' },
                  { l: 'Pkts Recv',  v: (selectedNode.packets_received ?? selectedNode.packet_count).toLocaleString(), c: 'var(--cyan)' },
                  { l: 'Threats',  v: selectedNode.threat_count.toString(),        c: selectedNode.threat_count > 0 ? 'var(--red)' : 'var(--text-lo)' },
                  { l: 'Trust',    v: `${selectedNode.trust_score}%`,             c: selectedNode.trust_score >= 80 ? 'var(--green)' : selectedNode.trust_score >= 50 ? 'var(--amber)' : 'var(--red)' },
                  { l: 'Risk',     v: selectedNode.risk_level,                    c: RISK_COL[selectedNode.risk_level] },
                  { l: 'Status',   v: (selectedNode.status ?? 'active').toUpperCase(), c: statusColor(selectedNode.status) },
                  ...(selectedNode.fanout ? [{ l: 'Fan-out', v: `${selectedNode.fanout} hosts`, c: selectedNode.fanout >= 15 ? 'var(--red)' : 'var(--text-mid)' }] : []),
                ].map(m => (
                  <div key={m.l} className="flex justify-between items-center">
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>{m.l}</span>
                    <span style={{ fontFamily: 'var(--font-display)', fontSize: 11, color: m.c, fontWeight: 700 }}>{m.v}</span>
                  </div>
                ))}
              </div>

              {/* Risk reasons (topology-aware) */}
              {selectedNode.risk_reasons && selectedNode.risk_reasons.length > 0 && (
                <div className="mt-3 px-2 py-2 rounded"
                  style={{ background: `${RISK_COL[selectedNode.risk_level] ?? '#dc2626'}0e`,
                    border: `1px solid ${RISK_COL[selectedNode.risk_level] ?? '#dc2626'}30` }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)',
                    letterSpacing: '0.1em', marginBottom: 3 }}>RISK REASONS</div>
                  {selectedNode.risk_reasons.map((rr, i) => (
                    <div key={i} style={{ fontFamily: 'var(--font-mono)', fontSize: 9,
                      color: RISK_COL[selectedNode.risk_level] ?? 'var(--red)', lineHeight: 1.5 }}>
                      • {rr}
                    </div>
                  ))}
                </div>
              )}

              {/* Detected attacks */}
              {selectedNode.attacks && selectedNode.attacks.length > 0 && (
                <div className="mt-3">
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)',
                    letterSpacing: '0.1em', marginBottom: 4 }}>DETECTED ATTACKS</div>
                  <div className="flex flex-wrap gap-1">
                    {selectedNode.attacks.map(a => (
                      <span key={a} style={{
                        fontFamily: 'var(--font-mono)', fontSize: 8, borderRadius: 4, padding: '2px 5px',
                        background: 'rgba(220,38,38,0.10)', color: '#dc2626',
                        border: '1px solid rgba(220,38,38,0.30)',
                      }}>{a}</span>
                    ))}
                  </div>
                </div>
              )}
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
              style={{ background: '#ffffff', border: '1px solid #000000', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)',
                letterSpacing: '0.1em', marginBottom: 6 }}>// CLICK A NODE</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', lineHeight: 1.6 }}>
                Select any node to inspect traffic stats, trust scores and connections.
              </div>
            </div>
          )}

          {/* Legend */}
          <div className="rounded-xl p-4 bracket-all"
            style={{ background: '#ffffff', border: '1px solid #000000', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
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
                <div style={{ width: 14, height: 2, background: 'rgba(220,38,38,0.80)', borderRadius: 1 }} />
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
                  background: 'rgba(2,132,199,0.38)', border: '1px solid rgba(2,132,199,0.50)' }} />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-mid)' }}>◎ External</span>
              </div>
            </div>
          </div>

          {/* Risky nodes — topology-aware intelligence */}
          {riskyNodes.length > 0 && (
            <div className="rounded-xl p-4 bracket-all"
              style={{ background: '#ffffff', border: '1px solid #000000', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
              <div className="flex items-center justify-between mb-2">
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', letterSpacing: '0.1em' }}>
                  // RISKY NODES
                </div>
                <span style={{ fontFamily: 'var(--font-display)', fontSize: 11, color: 'var(--red)', fontWeight: 700 }}>
                  {riskyNodes.length}
                </span>
              </div>
              <div className="space-y-2" style={{ maxHeight: 240, overflowY: 'auto' }}>
                {riskyNodes.slice(0, 12).map(n => (
                  <div key={n.id} className="rounded-lg p-2 cursor-pointer"
                    onClick={() => setSelected(p => p === n.id ? null : n.id)}
                    style={{ background: `${RISK_COL[n.risk_level] ?? '#888'}10`,
                      border: `1px solid ${RISK_COL[n.risk_level] ?? '#888'}30` }}>
                    <div className="flex items-center justify-between mb-1">
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9,
                        color: RISK_COL[n.risk_level] ?? 'var(--text-mid)', fontWeight: 700,
                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 120 }}>
                        {n.id}
                      </span>
                      <span className="tag" style={{ fontSize: 7,
                        background: `${RISK_COL[n.risk_level] ?? '#888'}20`,
                        color: RISK_COL[n.risk_level] ?? '#888',
                        border: `1px solid ${RISK_COL[n.risk_level] ?? '#888'}40` }}>
                        {n.status?.toUpperCase() ?? n.risk_level.toUpperCase()}
                      </span>
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', lineHeight: 1.4 }}>
                      {n.reasons[0]}
                    </div>
                    <div className="flex gap-2 mt-1">
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--red)' }}>
                        ⚠ {n.threat_count}
                      </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)' }}>
                        trust {n.trust_score}%
                      </span>
                      {n.fanout > 0 && (
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--amber)' }}>
                          fan-out {n.fanout}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Top traffic */}
          {displayNodes.length > 0 && (
            <div className="rounded-xl p-4 bracket-all"
              style={{ background: '#ffffff', border: '1px solid #000000', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
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
