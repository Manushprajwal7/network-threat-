'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { getDashboardStats } from '../lib/api';
import { deriveThreatLevel } from '../lib/threatLevel';

const NAV = [
  { href: '/dashboard', label: 'Overview',       icon: 'M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z', exact: true },
  { href: '/dashboard/monitor', label: 'Net Monitor', icon: 'M22 12h-4l-3 9L9 3l-3 9H2' },
  { href: '/dashboard/threats', label: 'Threats',    icon: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z M12 8v4 M12 16h.01' },
  { href: '/dashboard/trust',   label: 'Trust Engine',icon: 'M12 2L2 7l10 5 10-5-10-5z M2 17l10 5 10-5 M2 12l10 5 10-5' },
  { href: '/dashboard/decisions', label: 'Decisions', icon: 'M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9 M13.73 21a2 2 0 0 1-3.46 0' },
  { href: '/dashboard/models',  label: 'ML Models',  icon: 'M4 4h4v4H4z M10 4h4v4h-4z M16 4h4v4h-4z M4 10h4v4H4z M10 10h4v4h-4z M16 10h4v4h-4z' },
  { href: '/dashboard/topology',   label: 'Topology',   icon: 'M12 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6z M2 18a3 3 0 1 0 6 0 3 3 0 0 0-6 0z M16 18a3 3 0 1 0 6 0 3 3 0 0 0-6 0z M8.59 13.51l6.83 3.98 M15.41 13.51l-6.83 3.98 M12 8v3' },
  { href: '/dashboard/evaluation', label: 'Evaluation', icon: 'M9 11l3 3L22 4 M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11' },
  { href: '/dashboard/simulation',      label: 'Sim Lab',    icon: 'M8 3H5a2 2 0 0 0-2 2v3 M21 8V5a2 2 0 0 0-2-2h-3 M3 16v3a2 2 0 0 0 2 2h3 M16 21h3a2 2 0 0 0 2-2v-3 M12 8v8 M8 12h8' },
  { href: '/dashboard/research-results',label: 'Research',   icon: 'M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 1 1 3-3h7z' },
  { href: '/results', label: 'Results',  icon: 'M3 3v18h18 M18 9l-5 5-2-2-5 5', exact: true },
];


export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [uptime, setUptime] = useState('00:00:00');
  const [startTime] = useState(Date.now());
  const [threatInfo, setThreatInfo] = useState(() => deriveThreatLevel(0, 0));
  const [threatCount, setThreatCount] = useState<number | null>(null);
  const pathname = usePathname();

  useEffect(() => {
    const id = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const h = String(Math.floor(elapsed / 3600)).padStart(2, '0');
      const m = String(Math.floor((elapsed % 3600) / 60)).padStart(2, '0');
      const s = String(elapsed % 60).padStart(2, '0');
      setUptime(`${h}:${m}:${s}`);
    }, 1000);
    return () => clearInterval(id);
  }, [startTime]);

  useEffect(() => {
    let cancelled = false;
    async function fetchThreatLevel() {
      try {
        const stats = await getDashboardStats();
        if (cancelled) return;
        setThreatInfo(deriveThreatLevel(stats.threats_detected, stats.total_packets));
        setThreatCount(stats.threats_detected);
      } catch { /* keep previous value */ }
    }
    fetchThreatLevel();
    const id = setInterval(fetchThreatLevel, 5000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const W = collapsed ? 64 : 240;

  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden"
          style={{ background: 'rgba(0,0,0,0.30)', backdropFilter: 'blur(4px)' }}
          onClick={() => setMobileOpen(false)} />
      )}

      {/* Mobile toggle */}
      <button onClick={() => setMobileOpen(!mobileOpen)}
        className="fixed top-3.5 left-4 z-50 p-2 rounded-md lg:hidden"
        style={{ background: 'rgba(2,132,199,0.08)', border: '1px solid var(--border-mid)', color: 'var(--cyan)' }}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button>

      {/* Sidebar */}
      <aside className={`fixed top-0 left-0 h-full z-50 flex flex-col transition-all duration-300
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
        style={{
          width: W,
          background: '#ffffff',
          borderRight: '1px solid var(--border-dim)',
          boxShadow: '1px 0 0 0 rgba(0,0,0,0.15)',
        }}>

        {/* Top scan line */}
        <div className="absolute top-0 left-0 right-0 h-px"
          style={{ background: 'linear-gradient(90deg, transparent, var(--cyan), transparent)', opacity: 0.6 }} />

        {/* Logo */}
        <div className="flex items-center justify-between px-4 py-4"
          style={{ borderBottom: '1px solid var(--border-dim)', minHeight: 56 }}>
          {!collapsed && (
            <div className="flex items-center gap-2.5">
              <div className="relative w-8 h-8 flex-shrink-0">
                {/* Hex background */}
                <div className="hex-badge w-8 h-8 flex items-center justify-center"
                  style={{ background: 'linear-gradient(135deg, rgba(2,132,199,0.18), rgba(124,58,237,0.18))', border: '1px solid rgba(2,132,199,0.30)' }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                  </svg>
                </div>
              </div>
              <div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 13, fontWeight: 700, letterSpacing: '0.12em', color: 'var(--cyan)' }}>
                  NETSHIELD
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', letterSpacing: '0.1em' }}>
                  v2.4.1 SECURE
                </div>
              </div>
            </div>
          )}
          {collapsed && (
            <div className="mx-auto hex-badge w-8 h-8 flex items-center justify-center"
              style={{ background: 'rgba(2,132,199,0.10)', border: '1px solid rgba(2,132,199,0.28)' }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
            </div>
          )}
          <button onClick={() => setCollapsed(!collapsed)}
            className="hidden lg:flex p-1.5 rounded transition-colors"
            style={{ color: 'var(--text-lo)' }}
            onMouseEnter={e => (e.currentTarget.style.color = 'var(--cyan)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-lo)')}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
              style={{ transform: collapsed ? 'rotate(180deg)' : 'none', transition: 'transform 0.3s' }}>
              <polyline points="15 18 9 12 15 6"/>
            </svg>
          </button>
        </div>

        {/* System status strip */}
        {!collapsed && (
          <div className="mx-3 mt-3 px-3 py-2 rounded-md"
            style={{ background: 'rgba(5,150,105,0.07)', border: '1px solid rgba(5,150,105,0.18)' }}>
            <div className="flex items-center gap-2 mb-0.5">
              <span className="pulse-dot pulse-green" />
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--green)', letterSpacing: '0.1em' }}>
                IDS OPERATIONAL
              </span>
            </div>
            <div className="flex justify-between">
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>UPTIME</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-mid)' }}>{uptime}</span>
            </div>
          </div>
        )}

        {/* Nav */}
        <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
          {NAV.map((item) => {
            const active = item.exact ? pathname === item.href : pathname.startsWith(item.href) && item.href !== '/dashboard';
            const isActive = item.exact ? pathname === item.href : active;
            return (
              <Link key={item.href} href={item.href}
                onClick={() => setMobileOpen(false)}
                className="flex items-center gap-3 px-3 py-2.5 rounded-md transition-all duration-150 group"
                style={{
                  background: isActive ? 'linear-gradient(90deg, rgba(2,132,199,0.10), transparent)' : 'transparent',
                  borderLeft: isActive ? '2px solid var(--cyan)' : '2px solid transparent',
                  color: isActive ? 'var(--cyan)' : 'var(--text-lo)',
                }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"
                  style={{ flexShrink: 0, transition: 'color 0.15s' }}
                  onMouseEnter={e => (e.currentTarget.style.color = 'var(--cyan)')}
                  onMouseLeave={e => (e.currentTarget.style.color = isActive ? 'var(--cyan)' : 'var(--text-lo)')}>
                  {item.icon.split(' M').map((d, i) => (
                    <path key={i} d={i === 0 ? d : 'M' + d} strokeLinecap="round" strokeLinejoin="round"/>
                  ))}
                </svg>
                {!collapsed && (
                  <span style={{ fontFamily: 'var(--font-ui)', fontSize: 12.5, fontWeight: isActive ? 600 : 400, letterSpacing: '0.02em', whiteSpace: 'nowrap' }}>
                    {item.label}
                  </span>
                )}
                {isActive && !collapsed && (
                  <div className="ml-auto w-1 h-1 rounded-full" style={{ background: 'var(--cyan)' }} />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Threat level block */}
        {!collapsed && (
          <div className="p-3" style={{ borderTop: '1px solid var(--border-dim)' }}>
            <div className="px-3 py-3 rounded-md bracket-all"
              style={{ background: threatInfo.bg, border: `1px solid ${threatInfo.border}` }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', letterSpacing: '0.12em', marginBottom: 4 }}>
                // THREAT LEVEL
              </div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700, color: threatInfo.color, letterSpacing: '0.06em' }}>
                {threatInfo.label}
              </div>
              <div className="flex items-center justify-between mt-2">
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
                  {threatCount !== null ? `${threatCount} threats` : '— threats'}
                </span>
                <div className="flex gap-1">
                  {[1,2,3,4,5].map(i => (
                    <div key={i} className="w-1.5 h-4 rounded-sm"
                      style={{
                        background: i <= threatInfo.barCount ? threatInfo.color : 'var(--text-ghost)',
                        opacity: i <= threatInfo.barCount ? 0.8 : 0.15,
                      }} />
                  ))}
                </div>
              </div>
            </div>

            {/* Analyst info */}
            <div className="flex items-center gap-2.5 mt-3 px-1">
              <div className="hex-badge w-8 h-8 flex items-center justify-center flex-shrink-0"
                style={{ background: 'rgba(2,132,199,0.10)', border: '1px solid rgba(2,132,199,0.22)' }}>
                <span style={{ fontFamily: 'var(--font-display)', fontSize: 10, color: 'var(--cyan)' }}>LT</span>
              </div>
              <div>
                <div style={{ fontFamily: 'var(--font-ui)', fontSize: 12, fontWeight: 600, color: 'var(--text-mid)' }}>SOC Analyst</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>L. Thirupathi</div>
              </div>
            </div>
          </div>
        )}
      </aside>
    </>
  );
}
