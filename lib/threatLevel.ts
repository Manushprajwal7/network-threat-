export interface ThreatLevelInfo {
  label: string;
  color: string;
  border: string;
  bg: string;
  barCount: number; // 1–5 bars to fill in sidebar indicator
}

export function deriveThreatLevel(threats: number, total: number): ThreatLevelInfo {
  if (total === 0 || threats === 0)
    return { label: 'LOW',      color: 'var(--green)',  border: 'rgba(0,255,157,0.25)',  bg: 'rgba(0,255,157,0.07)',  barCount: 1 };
  const pct = threats / total;
  if (pct < 0.01)
    return { label: 'MODERATE', color: 'var(--cyan)',   border: 'rgba(0,212,255,0.25)',  bg: 'rgba(0,212,255,0.06)',  barCount: 2 };
  if (pct < 0.05)
    return { label: 'ELEVATED', color: 'var(--amber)',  border: 'rgba(255,176,32,0.25)', bg: 'rgba(255,176,32,0.07)', barCount: 3 };
  if (pct < 0.15)
    return { label: 'HIGH',     color: '#ff8c42',       border: 'rgba(255,140,66,0.25)', bg: 'rgba(255,140,66,0.06)', barCount: 4 };
  return   { label: 'CRITICAL', color: 'var(--red)',    border: 'rgba(255,45,85,0.25)',  bg: 'rgba(255,45,85,0.07)',  barCount: 5 };
}
