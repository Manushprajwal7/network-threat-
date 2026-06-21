'use client';

import { useEffect, useState, useRef } from 'react';

interface KPICardProps {
  title: string;
  value: string;
  subtitle?: string;
  trend?: string;
  trendUp?: boolean;
  icon: React.ReactNode;
  accentColor?: string;
  dimColor?: string;
  delay?: number;
  sparkData?: number[];
}

function MiniSparkline({ data, color }: { data: number[]; color: string }) {
  if (!data || data.length < 2) return null;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const w = 72, h = 24;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((v - min) / range) * h;
    return `${x},${y}`;
  });
  const path = `M ${pts.join(' L ')}`;
  const area = `M 0,${h} L ${pts.join(' L ')} L ${w},${h} Z`;
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <defs>
        <linearGradient id={`sg-${color.replace('#','')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3"/>
          <stop offset="100%" stopColor={color} stopOpacity="0"/>
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#sg-${color.replace('#','')})`}/>
      <path d={path} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}

export default function KPICard({
  title, value, subtitle, trend, trendUp,
  icon, accentColor = 'var(--cyan)', dimColor = 'var(--cyan-dim)',
  delay = 0, sparkData,
}: KPICardProps) {
  const [visible, setVisible] = useState(false);
  const [hovered, setHovered] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), delay);
    return () => clearTimeout(t);
  }, [delay]);

  return (
    <div ref={ref}
      className="relative overflow-hidden rounded-xl bracket-all"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered
          ? 'linear-gradient(135deg, rgba(8,22,48,0.98), rgba(5,15,35,0.98))'
          : 'linear-gradient(135deg, rgba(5,15,35,0.90), rgba(3,10,22,0.90))',
        border: `1px solid ${hovered ? accentColor + '35' : 'rgba(0,212,255,0.07)'}`,
        backdropFilter: 'blur(16px)',
        boxShadow: hovered ? `0 0 32px ${accentColor}12, inset 0 1px 0 ${accentColor}15` : 'inset 0 1px 0 rgba(255,255,255,0.03)',
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(14px)',
        transition: `opacity 0.45s ease ${delay}ms, transform 0.45s ease ${delay}ms, border-color 0.2s, box-shadow 0.2s, background 0.2s`,
        padding: '14px 16px 12px',
        cursor: 'default',
      }}>

      {/* Radial glow behind value */}
      <div className="absolute top-0 right-0 w-24 h-24 pointer-events-none"
        style={{ background: `radial-gradient(circle at 80% 20%, ${accentColor}10, transparent 70%)`, transition: 'opacity 0.3s', opacity: hovered ? 1 : 0.4 }} />

      {/* Icon + trend row */}
      <div className="flex items-start justify-between mb-2">
        <div className="p-2 rounded-lg flex-shrink-0"
          style={{ background: dimColor, color: accentColor, border: `1px solid ${accentColor}20` }}>
          {icon}
        </div>
        {trend && (
          <div className="flex items-center gap-1 px-2 py-0.5 rounded-md"
            style={{
              background: trendUp ? 'rgba(0,255,157,0.07)' : 'rgba(255,45,85,0.07)',
              border: `1px solid ${trendUp ? 'rgba(0,255,157,0.18)' : 'rgba(255,45,85,0.18)'}`,
              fontFamily: 'var(--font-mono)',
              fontSize: 10,
              color: trendUp ? 'var(--green)' : 'var(--red)',
            }}>
            {trendUp ? '▲' : '▼'} {trend}
          </div>
        )}
      </div>

      {/* Value */}
      <div className="mt-2 mb-0.5"
        style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 700, color: accentColor, letterSpacing: '-0.02em', lineHeight: 1, textShadow: hovered ? `0 0 20px ${accentColor}60` : 'none', transition: 'text-shadow 0.3s' }}>
        {value}
      </div>

      {/* Title */}
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--text-lo)', marginTop: 4 }}>
        {title}
      </div>

      {/* Subtitle or sparkline */}
      <div className="mt-2 flex items-end justify-between">
        {subtitle && (
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
            {subtitle}
          </div>
        )}
        {sparkData && (
          <div className="ml-auto opacity-60" style={{ opacity: hovered ? 1 : 0.5, transition: 'opacity 0.3s' }}>
            <MiniSparkline data={sparkData} color={accentColor} />
          </div>
        )}
      </div>

      {/* Bottom shimmer line */}
      <div className="absolute bottom-0 left-0 h-px transition-all duration-500"
        style={{ right: hovered ? '0%' : '100%', background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)` }} />
    </div>
  );
}
