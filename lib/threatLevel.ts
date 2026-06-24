export interface ThreatLevelInfo {
  label: string;
  color: string;
  border: string;
  bg: string;
  barCount: number; // 1–5 bars to fill in sidebar indicator
}

export function deriveThreatLevel(threats: number, total: number): ThreatLevelInfo {
  if (total === 0 || threats === 0)
    return { label: 'LOW',      color: 'var(--green)',  border: 'rgba(5,150,105,0.28)',  bg: 'rgba(5,150,105,0.08)',  barCount: 1 };
  const pct = threats / total;
  if (pct < 0.01)
    return { label: 'MODERATE', color: 'var(--cyan)',   border: 'rgba(2,132,199,0.28)',  bg: 'rgba(2,132,199,0.08)',  barCount: 2 };
  if (pct < 0.05)
    return { label: 'ELEVATED', color: 'var(--amber)',  border: 'rgba(217,119,6,0.28)',  bg: 'rgba(217,119,6,0.09)',  barCount: 3 };
  if (pct < 0.15)
    return { label: 'HIGH',     color: '#ea6c1a',       border: 'rgba(234,108,26,0.28)', bg: 'rgba(234,108,26,0.08)', barCount: 4 };
  return   { label: 'CRITICAL', color: 'var(--red)',    border: 'rgba(220,38,38,0.28)',  bg: 'rgba(220,38,38,0.09)',  barCount: 5 };
}
