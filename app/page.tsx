'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';

/* ─── DATA ──────────────────────────────────────────────────── */
const MODULES = [
  { title: 'Authentication Layer', color: 'var(--cyan)',   desc: 'Zero-trust MFA with certificate-based identity binding across all network segments.', badge: 'LAYER 1',
    icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg> },
  { title: 'Access Control Layer', color: 'var(--purple)', desc: 'RBAC + ABAC policy enforcement at perimeter, application, and data-store boundaries.', badge: 'LAYER 2',
    icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="8" r="4"/><path d="M20 21a8 8 0 1 0-16 0"/></svg> },
  { title: 'Data Protection Layer', color: 'var(--green)',  desc: 'AES-256 E2E encryption, DLP rules, and behavioral anomaly detection for data exfil prevention.', badge: 'LAYER 3',
    icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> },
  { title: 'AI Threat Detection', color: 'var(--amber)',   desc: 'Random Forest classifier on CICIDS2017 achieving 98.1% accuracy across 13 attack categories.', badge: 'CORE',
    icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/></svg> },
  { title: 'Trust Management', color: 'var(--cyan)',     desc: 'Continuous trust scoring: T = α·U + β·D + γ·B with real-time weight adaptation.', badge: 'ENGINE',
    icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg> },
  { title: 'Decision Engine', color: 'var(--red)',      desc: 'Five-tier adaptive response: Allow → Restrict → Alert → Quarantine → Block, feedback-tuned.', badge: 'RESPONSE',
    icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> },
];

const PIPELINE = [
  { label: 'Packet Capture',     detail: 'pcap · tap',           color: 'var(--cyan)' },
  { label: 'Feature Extraction', detail: '78 features',          color: 'var(--purple)' },
  { label: 'ML Detection',       detail: 'RFC 98.1%',            color: 'var(--green)' },
  { label: 'Trust Score',        detail: 'α·U+β·D+γ·B',         color: 'var(--amber)' },
  { label: 'Security Decision',  detail: '5-tier response',      color: 'var(--red)' },
];

const ATTACKS = ['BENIGN','DoS Hulk','PortScan','DDoS','DoS GoldenEye','Brute Force – FTP','Brute Force – SSH','DoS Slowloris','Web Attack – Brute Force','Web Attack – XSS','Infiltration','Web Attack – SQLi','Botnet'];
const ATTACK_COLORS = ['var(--green)','var(--red)','var(--cyan)','var(--purple)','var(--amber)','#be185d','#6b7c2d','#d97706','#dc2626','#1e40af','#059669','#8b5cf6','#b45309'];

/* ─── PARTICLE CANVAS ──────────────────────────────────────── */
function ParticleNet() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const c = ref.current; if (!c) return;
    const ctx = c.getContext('2d'); if (!ctx) return;
    const resize = () => { c.width = c.offsetWidth; c.height = c.offsetHeight; };
    resize();
    window.addEventListener('resize', resize);
    const N = 55;
    const nodes = Array.from({ length: N }, () => ({
      x: Math.random() * c.width, y: Math.random() * c.height,
      vx: (Math.random() - 0.5) * 0.35, vy: (Math.random() - 0.5) * 0.35,
      r: Math.random() * 1.8 + 0.5,
      hue: Math.random() > 0.8 ? 280 : 193, // mix cyan and purple
    }));
    let raf: number;
    const draw = () => {
      ctx.clearRect(0, 0, c.width, c.height);
      for (const n of nodes) {
        n.x += n.vx; n.y += n.vy;
        if (n.x < 0 || n.x > c.width) n.vx *= -1;
        if (n.y < 0 || n.y > c.height) n.vy *= -1;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${n.hue}, 100%, 65%, 0.7)`;
        ctx.fill();
      }
      for (let i = 0; i < N; i++) {
        for (let j = i + 1; j < N; j++) {
          const dx = nodes[i].x - nodes[j].x, dy = nodes[i].y - nodes[j].y;
          const d = Math.sqrt(dx*dx + dy*dy);
          if (d < 130) {
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            const alpha = 0.18 * (1 - d / 130);
            ctx.strokeStyle = `rgba(2, 132, 199, ${alpha})`;
            ctx.lineWidth = 0.6;
            ctx.stroke();
          }
        }
      }
      raf = requestAnimationFrame(draw);
    };
    draw();
    return () => { window.removeEventListener('resize', resize); cancelAnimationFrame(raf); };
  }, []);
  return <canvas ref={ref} className="absolute inset-0 w-full h-full" style={{ opacity: 0.55 }} />;
}

/* ─── MAIN ──────────────────────────────────────────────────── */
export default function LandingPage() {
  const [pipeStep, setPipeStep] = useState(0);
  const [bootText, setBootText] = useState('');

  const BOOT = 'NETSHIELD IDS v2.4.1 // INITIALIZING MULTI-LEVEL PROTECTION FRAMEWORK...';
  useEffect(() => {
    let i = 0;
    const t = setInterval(() => {
      setBootText(BOOT.slice(0, ++i));
      if (i >= BOOT.length) clearInterval(t);
    }, 28);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const id = setInterval(() => setPipeStep(p => (p + 1) % PIPELINE.length), 1100);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-void)', color: 'var(--text-hi)' }}>

      {/* ─── TOP NAV ─────────────────────────────────── */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-3"
        style={{ background: '#ffffff', borderBottom: '1px solid var(--border-dim)', backdropFilter: 'blur(20px)', boxShadow: '0 1px 0 0 rgba(0,0,0,0.15)' }}>
        {/* Top glow line */}
        <div className="absolute top-0 left-0 right-0 h-px"
          style={{ background: 'linear-gradient(90deg, transparent, var(--cyan), var(--purple), transparent)', opacity: 0.6 }} />

        <div className="flex items-center gap-2.5">
          <div className="hex-badge w-8 h-8 flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, rgba(2,132,199,0.18), rgba(124,58,237,0.18))', border: '1px solid rgba(2,132,199,0.30)' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </div>
          <span style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 700, letterSpacing: '0.15em', color: 'var(--cyan)' }}>NETSHIELD</span>
        </div>

        <div className="hidden md:flex items-center gap-6">
          {[['#modules','Modules'],['#architecture','Architecture'],['#dataset','Dataset']].map(([h, l]) => (
            <a key={h} href={h} style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-lo)', letterSpacing: '0.06em', textDecoration: 'none', transition: 'color 0.15s' }}
              onMouseEnter={e => (e.currentTarget.style.color = 'var(--cyan)')}
              onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-lo)')}>
              {l}
            </a>
          ))}
        </div>

        <Link href="/dashboard" className="tag transition-all"
          style={{ background: 'rgba(2,132,199,0.08)', color: 'var(--cyan)', border: '1px solid var(--border-mid)', fontFamily: 'var(--font-mono)', fontSize: 11, padding: '6px 14px', textDecoration: 'none' }}
          onMouseEnter={e => { e.currentTarget.style.background = 'var(--cyan-dim)'; e.currentTarget.style.boxShadow = '0 0 16px rgba(2,132,199,0.20)'; }}
          onMouseLeave={e => { e.currentTarget.style.background = 'rgba(2,132,199,0.08)'; e.currentTarget.style.boxShadow = 'none'; }}>
          ENTER SOC →
        </Link>
      </nav>

      {/* ─── HERO ────────────────────────────────────── */}
      <section className="relative min-h-screen flex flex-col items-center justify-center text-center px-6 overflow-hidden hex-grid"
        style={{ paddingTop: 80 }}>
        <ParticleNet />

        {/* radial spotlight */}
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: 'radial-gradient(ellipse 70% 55% at 50% 50%, rgba(2,132,199,0.08) 0%, transparent 75%)' }} />

        {/* Boot text */}
        <div className="relative z-10 mb-6 px-4 py-2 rounded"
          style={{ background: 'rgba(2,132,199,0.06)', border: '1px solid rgba(2,132,199,0.18)', maxWidth: 640 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', letterSpacing: '0.06em' }}>
            {bootText}
            <span style={{ animation: 'threat-blink 0.7s step-end infinite', color: 'var(--cyan)' }}>█</span>
          </span>
        </div>

        {/* Title */}
        <h1 className="relative z-10 gradient-text-cyber font-black leading-tight mb-5"
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'clamp(26px, 4.5vw, 54px)',
            maxWidth: 880,
            letterSpacing: '-0.02em',
          }}>
          Topology-Aware Multi-Level Network Protection Framework
        </h1>

        <p className="relative z-10 mb-8 max-w-xl"
          style={{ fontFamily: 'var(--font-ui)', fontSize: 16, color: 'var(--text-lo)', lineHeight: 1.75 }}>
          AI-powered intrusion detection, dynamic trust propagation, and adaptive security decisions
          for heterogeneous network topologies.
        </p>

        {/* CTA buttons */}
        <div className="relative z-10 flex flex-wrap gap-3 justify-center mb-12">
          <Link href="/dashboard"
            className="bracket-all transition-all duration-200"
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              padding: '12px 28px', borderRadius: 10,
              background: 'linear-gradient(135deg, rgba(2,132,199,0.12), rgba(124,58,237,0.12))',
              border: '1px solid rgba(2,132,199,0.35)',
              fontFamily: 'var(--font-display)', fontSize: 12, fontWeight: 700,
              letterSpacing: '0.1em', color: 'var(--cyan)',
              textDecoration: 'none',
            }}
            onMouseEnter={e => { e.currentTarget.style.background = 'linear-gradient(135deg, rgba(2,132,199,0.22), rgba(124,58,237,0.22))'; e.currentTarget.style.boxShadow = '0 0 32px rgba(2,132,199,0.18)'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'linear-gradient(135deg, rgba(2,132,199,0.12), rgba(124,58,237,0.12))'; e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'none'; }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
              <rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>
            </svg>
            OPEN DASHBOARD
          </Link>
          <a href="#architecture"
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              padding: '12px 24px', borderRadius: 10,
              background: 'rgba(0,0,0,0.10)', border: '1px solid rgba(0,0,0,0.25)',
              fontFamily: 'var(--font-display)', fontSize: 12, fontWeight: 600,
              letterSpacing: '0.1em', color: 'var(--text-mid)',
              textDecoration: 'none', transition: 'all 0.2s',
            }}
            onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-hi)'; e.currentTarget.style.borderColor = 'rgba(0,0,0,0.35)'; e.currentTarget.style.transform = 'translateY(-2px)'; }}
            onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-mid)'; e.currentTarget.style.borderColor = 'rgba(0,0,0,0.25)'; e.currentTarget.style.transform = 'none'; }}>
            VIEW ARCHITECTURE
          </a>
        </div>

        {/* Pipeline preview */}
        <div className="relative z-10 flex flex-wrap items-center justify-center gap-1.5 md:gap-0">
          {PIPELINE.map((s, i) => (
            <div key={s.label} className="flex items-center">
              <div className="px-3 py-2 rounded-lg transition-all duration-300 cursor-default"
                style={{
                  background: pipeStep === i ? `${s.color}14` : 'rgba(0,0,0,0.10)',
                  border: `1px solid ${pipeStep === i ? s.color + '50' : 'rgba(0,0,0,0.20)'}`,
                  boxShadow: pipeStep === i ? `0 0 16px ${s.color}20` : 'none',
                }}>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 9, color: pipeStep === i ? s.color : 'var(--text-lo)', letterSpacing: '0.08em' }}>{s.label}</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: pipeStep === i ? `${s.color}` : 'var(--text-ghost)', marginTop: 1, opacity: 0.8 }}>{s.detail}</div>
              </div>
              {i < PIPELINE.length - 1 && (
                <div className="mx-1.5 text-xs hidden md:block" style={{ color: 'rgba(2,132,199,0.35)' }}>──▶</div>
              )}
            </div>
          ))}
        </div>

        {/* Scroll cue */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1.5 anim-float">
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '0.15em' }}>SCROLL</div>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--text-lo)" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/>
          </svg>
        </div>
      </section>

      {/* ─── STATS BAR ───────────────────────────────── */}
      <section style={{ background: '#ffffff', borderTop: '1px solid var(--border-dim)', borderBottom: '1px solid var(--border-dim)', padding: '32px 24px' }}>
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { v: '2.83M+', l: 'Records', sub: 'Training dataset' },
            { v: '13',     l: 'Attack Classes', sub: 'CICIDS2017 taxonomy' },
            { v: '98.1%',  l: 'ML Accuracy', sub: 'Random Forest RFC' },
            { v: '78',     l: 'Features', sub: 'Flow-level statistics' },
          ].map(s => (
            <div key={s.l} className="text-center">
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 36, fontWeight: 800, color: 'var(--cyan)', letterSpacing: '-0.03em', textShadow: '0 0 24px rgba(2,132,199,0.25)' }}>{s.v}</div>
              <div style={{ fontFamily: 'var(--font-ui)', fontSize: 13, fontWeight: 600, color: 'var(--text-hi)', marginTop: 4 }}>{s.l}</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', marginTop: 2 }}>{s.sub}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── MODULES ─────────────────────────────────── */}
      <section id="modules" style={{ padding: '80px 24px' }}>
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <div className="section-label justify-center mb-3">Protection Modules</div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(22px,3vw,36px)', fontWeight: 800, color: 'var(--text-hi)', letterSpacing: '0.02em' }}>
              Multi-Level Security Architecture
            </h2>
            <p style={{ fontFamily: 'var(--font-ui)', fontSize: 15, color: 'var(--text-lo)', marginTop: 10, maxWidth: 480, margin: '10px auto 0' }}>
              Six interlocking protection layers forming a comprehensive defense-in-depth strategy.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {MODULES.map((m, i) => (
              <div key={m.title}
                className="rounded-xl p-5 bracket-all transition-all duration-300 cursor-default"
                style={{ background: '#ffffff', border: '1px solid rgba(0,0,0,0.18)', backdropFilter: 'blur(12px)', boxShadow: '0 1px 3px rgba(0,0,0,0.15)', animationDelay: `${i * 80}ms` }}
                onMouseEnter={e => { e.currentTarget.style.border = `1px solid ${m.color}45`; e.currentTarget.style.boxShadow = `0 4px 20px ${m.color}15`; e.currentTarget.style.transform = 'translateY(-3px)'; }}
                onMouseLeave={e => { e.currentTarget.style.border = '1px solid rgba(0,0,0,0.18)'; e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.15)'; e.currentTarget.style.transform = 'none'; }}>
                <div className="flex items-start justify-between mb-4">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center"
                    style={{ background: `${m.color}14`, color: m.color, border: `1px solid ${m.color}30` }}>
                    {m.icon}
                  </div>
                  <span className="tag" style={{ background: `${m.color}10`, color: m.color, border: `1px solid ${m.color}25`, fontSize: 8, letterSpacing: '0.1em' }}>
                    {m.badge}
                  </span>
                </div>
                <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 12, fontWeight: 700, color: 'var(--text-hi)', letterSpacing: '0.06em', marginBottom: 8 }}>
                  {m.title}
                </h3>
                <p style={{ fontFamily: 'var(--font-ui)', fontSize: 13, color: 'var(--text-lo)', lineHeight: 1.65 }}>{m.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── ARCHITECTURE ────────────────────────────── */}
      <section id="architecture" style={{ padding: '80px 24px', background: '#ffffff', borderTop: '1px solid var(--border-dim)', borderBottom: '1px solid var(--border-dim)' }}>
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <div className="section-label justify-center mb-3">System Pipeline</div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(22px,3vw,36px)', fontWeight: 800, color: 'var(--text-hi)' }}>
              Processing Architecture
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {PIPELINE.map((step, i) => (
              <div key={step.label}
                className="flex flex-col items-center text-center p-4 rounded-xl bracket-all"
                style={{ background: '#ffffff', border: `1px solid ${step.color}30`, boxShadow: '0 1px 3px rgba(0,0,0,0.15)' }}>
                <div className="w-12 h-12 rounded-2xl flex items-center justify-center mb-3"
                  style={{ background: `${step.color}14`, border: `1px solid ${step.color}35`, color: step.color }}>
                  <span style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 800 }}>{i + 1}</span>
                </div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 10, fontWeight: 700, color: step.color, letterSpacing: '0.08em', marginBottom: 4 }}>
                  {step.label}
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>{step.detail}</div>
              </div>
            ))}
          </div>

          {/* Trust formula callout */}
          <div className="mt-8 rounded-xl p-6 bracket-all"
            style={{ background: 'rgba(124,58,237,0.06)', border: '1px solid rgba(124,58,237,0.20)' }}>
            <div className="text-center">
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', letterSpacing: '0.15em', marginBottom: 8 }}>// CORE TRUST FORMULA</div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(20px, 4vw, 36px)', fontWeight: 800, color: 'var(--purple)', letterSpacing: '0.04em' }}>
                T = α·U + β·D + γ·B
              </div>
              <div className="flex flex-wrap justify-center gap-6 mt-6">
                {[
                  { var: 'U', label: 'User Trust', val: 'α = 0.35', color: 'var(--cyan)' },
                  { var: 'D', label: 'Device Trust', val: 'β = 0.40', color: 'var(--purple)' },
                  { var: 'B', label: 'Behavior Trust', val: 'γ = 0.25', color: 'var(--amber)' },
                ].map(f => (
                  <div key={f.var} className="text-center">
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 800, color: f.color }}>{f.var}</div>
                    <div style={{ fontFamily: 'var(--font-ui)', fontSize: 12, color: 'var(--text-mid)' }}>{f.label}</div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: f.color }}>{f.val}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── DATASET ─────────────────────────────────── */}
      <section id="dataset" style={{ padding: '80px 24px' }}>
        <div className="max-w-5xl mx-auto">
          <div className="rounded-2xl p-8 md:p-10 relative overflow-hidden bracket-all"
            style={{ background: '#ffffff', border: '1px solid var(--border-mid)', boxShadow: '0 1px 4px rgba(0,0,0,0.18)' }}>
            {/* BG decor */}
            <div className="absolute top-0 right-0 w-72 h-72 pointer-events-none"
              style={{ background: 'radial-gradient(circle at top right, rgba(124,58,237,0.07), transparent 70%)' }} />
            <div className="absolute bottom-0 left-0 w-48 h-48 pointer-events-none"
              style={{ background: 'radial-gradient(circle at bottom left, rgba(2,132,199,0.06), transparent 70%)' }} />

            <div className="relative z-10">
              <div className="section-label mb-4">Training Dataset</div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(20px,3vw,32px)', fontWeight: 800, color: 'var(--text-hi)', marginBottom: 12 }}>
                CICIDS2017 Benchmark
              </h2>
              <p style={{ fontFamily: 'var(--font-ui)', fontSize: 14, color: 'var(--text-lo)', lineHeight: 1.75, maxWidth: 600, marginBottom: 28 }}>
                The Canadian Institute for Cybersecurity IDS Evaluation Dataset spans Mon–Fri with
                labeled benign traffic and 12 attack families covering DoS/DDoS, Brute Force,
                XSS, SQL Injection, Infiltration, PortScan, and Botnet variants.
              </p>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
                {[
                  { v: '2.83M', l: 'Total Records', c: 'var(--cyan)' },
                  { v: '13',    l: 'Attack Classes', c: 'var(--purple)' },
                  { v: '78',    l: 'Features/Flow', c: 'var(--green)' },
                  { v: '5',     l: 'Days Captured', c: 'var(--amber)' },
                ].map(x => (
                  <div key={x.l} className="rounded-xl p-4 text-center bracket-all"
                    style={{ background: 'rgba(0,0,0,0.10)', border: `1px solid ${x.c}35` }}>
                    <div style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 800, color: x.c }}>{x.v}</div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', marginTop: 4, letterSpacing: '0.08em' }}>{x.l}</div>
                  </div>
                ))}
              </div>

              {/* Attack class tags */}
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', letterSpacing: '0.12em', marginBottom: 10 }}>// ATTACK TAXONOMY</div>
              <div className="flex flex-wrap gap-2">
                {ATTACKS.map((cls, i) => (
                  <span key={cls} className="tag"
                    style={{ background: `${ATTACK_COLORS[i]}12`, color: ATTACK_COLORS[i], border: `1px solid ${ATTACK_COLORS[i]}28`, fontSize: 10 }}>
                    {cls}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── CTA ─────────────────────────────────────── */}
      <section style={{ padding: '80px 24px', background: '#ffffff', borderTop: '1px solid var(--border-dim)', textAlign: 'center' }}>
        <div className="max-w-xl mx-auto">
          <div className="section-label justify-center mb-4">Ready to Explore</div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(22px,3vw,34px)', fontWeight: 800, color: 'var(--text-hi)', marginBottom: 12 }}>
            Enter the SOC Dashboard
          </h2>
          <p style={{ fontFamily: 'var(--font-ui)', fontSize: 14, color: 'var(--text-lo)', marginBottom: 32, lineHeight: 1.7 }}>
            Monitor threats in real-time, inspect trust scores, and observe the ML decision engine classifying live network flows.
          </p>
          <Link href="/dashboard"
            className="bracket-all"
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 10,
              padding: '14px 36px', borderRadius: 12,
              background: 'linear-gradient(135deg, rgba(2,132,199,0.14), rgba(124,58,237,0.14))',
              border: '1px solid rgba(2,132,199,0.35)',
              fontFamily: 'var(--font-display)', fontSize: 13, fontWeight: 700,
              letterSpacing: '0.12em', color: 'var(--cyan)',
              textDecoration: 'none', transition: 'all 0.25s',
            }}
            onMouseEnter={e => { e.currentTarget.style.background = 'linear-gradient(135deg, rgba(2,132,199,0.24), rgba(124,58,237,0.24))'; e.currentTarget.style.boxShadow = '0 0 48px rgba(2,132,199,0.18)'; e.currentTarget.style.transform = 'translateY(-3px)'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'linear-gradient(135deg, rgba(2,132,199,0.14), rgba(124,58,237,0.14))'; e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.transform = 'none'; }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
              <rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>
            </svg>
            LAUNCH SOC DASHBOARD
          </Link>
        </div>
      </section>

      {/* ─── FOOTER ──────────────────────────────────── */}
      <footer style={{ padding: '24px', borderTop: '1px solid var(--border-dim)', background: 'var(--bg-void)' }}>
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="hex-badge w-7 h-7 flex items-center justify-center"
              style={{ background: 'rgba(2,132,199,0.10)', border: '1px solid rgba(2,132,199,0.22)' }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
            </div>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 12, fontWeight: 700, color: 'var(--cyan)', letterSpacing: '0.12em' }}>NETSHIELD</span>
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', textAlign: 'center', lineHeight: 1.7 }}>
            <div>Developing a Multi-Level Protection Framework in Network Topologies</div>
            <div>PhD Research · L. Thirupathi · CICIDS2017 · 2024</div>
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-ghost)' }}>v2.4.1-research</div>
        </div>
      </footer>
    </div>
  );
}
