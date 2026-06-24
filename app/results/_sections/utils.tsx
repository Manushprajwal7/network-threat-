'use client';
import React from 'react';

// ─── Design-token-aligned tooltip style for Recharts ─────────────────────────
export const TP: React.CSSProperties = {
  background: 'rgba(1,12,24,.97)',
  border: '1px solid rgba(2,132,199,0.22)',
  borderRadius: 8,
  fontFamily: 'var(--font-mono)',
  fontSize: 11,
  color: 'var(--text-hi)',
};

// ─── Model constants (CICIoT2023 — representative subset of the 7 models) ──────
export const MODEL_KEYS = [
  'xgboost','random_forest','decision_tree','naive_bayes',
];
export const MC: Record<string,string> = {
  xgboost: '#7c3aed',
  random_forest: '#0284c7',
  decision_tree: '#059669',
  naive_bayes: '#ec4899',
  logistic_regression: '#8b5cf6',
  knn: '#ea6c1a',
  svm: '#d97706',
};
export const MN: Record<string,string> = {
  xgboost: 'XGBoost',
  random_forest: 'Random Forest',
  decision_tree: 'Decision Tree',
  naive_bayes: 'Naive Bayes',
  logistic_regression: 'Logistic Reg.',
  knn: 'KNN',
  svm: 'SVM',
};

// ─── Formatters ───────────────────────────────────────────────────────────────
export const pct = (v: number | null | undefined, d = 2) =>
  v == null ? '—' : (v * 100).toFixed(d) + '%';

// ─── Attack category config ───────────────────────────────────────────────────
// CICIoT2023 attack families (exact class-name membership)
export const ATTACK_CATS = [
  { label:'DDoS', color:'#dc2626', cls:[
    'DDoS-ICMP_Flood','DDoS-UDP_Flood','DDoS-TCP_Flood','DDoS-PSHACK_Flood',
    'DDoS-SYN_Flood','DDoS-RSTFINFlood','DDoS-SynonymousIP_Flood',
    'DDoS-ICMP_Fragmentation','DDoS-UDP_Fragmentation','DDoS-ACK_Fragmentation',
    'DDoS-HTTP_Flood','DDoS-SlowLoris'] },
  { label:'DoS', color:'#d97706', cls:[
    'DoS-UDP_Flood','DoS-TCP_Flood','DoS-SYN_Flood','DoS-HTTP_Flood'] },
  { label:'Mirai', color:'#7c3aed', cls:[
    'Mirai-greeth_flood','Mirai-greip_flood','Mirai-udpplain'] },
  { label:'Recon', color:'#0284c7', cls:[
    'Recon-HostDiscovery','Recon-OSScan','Recon-PortScan','Recon-PingSweep','VulnerabilityScan'] },
  { label:'Spoofing', color:'#3b82f6', cls:[
    'DNS_Spoofing','MITM-ArpSpoofing'] },
  { label:'Web/Injection', color:'#10b981', cls:[
    'BrowserHijacking','CommandInjection','SqlInjection','XSS','Uploading_Attack','Backdoor_Malware'] },
  { label:'Brute Force', color:'#ec4899', cls:[
    'DictionaryBruteForce'] },
];

export const DECISION_COLORS: Record<string,string> = {
  Allow: '#059669', Restrict: '#d97706', Alert: '#0284c7',
  Quarantine: '#7c3aed', Block: '#dc2626',
};

// ─── Shared UI components ─────────────────────────────────────────────────────
export function SH({ n, title, sub }: { n: number; title: string; sub?: string }) {
  return (
    <div id={`s${n}`} style={{ marginBottom: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 5 }}>
        <span style={{
          background: 'linear-gradient(135deg,rgba(2,132,199,0.16),rgba(124,58,237,0.12))',
          border: '1px solid rgba(2,132,199,0.28)', borderRadius: 5,
          padding: '2px 10px', fontFamily: 'var(--font-mono)', fontSize: 9,
          color: 'var(--cyan)', letterSpacing: '.14em',
        }}>§{n}</span>
        <h2 style={{
          fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700,
          color: 'var(--text-hi)', letterSpacing: '.03em', margin: 0,
        }}>{title}</h2>
      </div>
      {sub && (
        <p style={{
          fontFamily: 'var(--font-ui)', fontSize: 13,
          color: 'var(--text-mid)', margin: '0 0 0 32px',
        }}>{sub}</p>
      )}
    </div>
  );
}

export function Box({
  children, title, caption, accent, style,
}: {
  children: React.ReactNode; title?: string; caption?: string;
  accent?: string; style?: React.CSSProperties;
}) {
  return (
    <div style={{
      background: '#ffffff',
      border: `1px solid ${accent ? accent + '20' : 'var(--border-dim)'}`,
      borderRadius: 12, padding: 20,
      borderTop: accent ? `2px solid ${accent}` : undefined,
      ...style,
    }}>
      {title && (
        <div style={{
          fontFamily: 'var(--font-display)', fontSize: 11, fontWeight: 700,
          color: accent || 'var(--cyan)', letterSpacing: '.08em', marginBottom: 14,
        }}>{title}</div>
      )}
      {children}
      {caption && (
        <p style={{
          fontFamily: 'var(--font-ui)', fontSize: 11, color: 'var(--text-lo)',
          marginTop: 14, fontStyle: 'italic', lineHeight: 1.6, margin: '14px 0 0',
        }}>{caption}</p>
      )}
    </div>
  );
}

export function Note({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      background: 'rgba(2,132,199,0.06)', borderLeft: '3px solid var(--cyan)',
      borderRadius: '0 8px 8px 0', padding: '9px 13px', marginTop: 12,
    }}>
      <span style={{
        fontFamily: 'var(--font-ui)', fontSize: 12, color: 'var(--text-mid)', lineHeight: 1.65,
      }}>
        <strong style={{ color: 'var(--cyan)' }}>Research Note: </strong>
        {children}
      </span>
    </div>
  );
}

export function Warn() {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      background: 'rgba(255,176,32,.1)', border: '1px solid rgba(255,176,32,.35)',
      borderRadius: 5, padding: '1px 6px', fontFamily: 'var(--font-mono)',
      fontSize: 8, color: '#d97706', letterSpacing: '.07em',
    }}>
      ⚠ INTERPRET WITH CAUTION
    </span>
  );
}

export function Spin() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 48 }}>
      <div style={{
        width: 28, height: 28,
        border: '2px solid rgba(2,132,199,0.18)', borderTop: '2px solid var(--cyan)',
        borderRadius: '50%', animation: 'spin .7s linear infinite',
      }} />
    </div>
  );
}

export function Empty({ msg }: { msg: string }) {
  return (
    <div style={{
      padding: 32, textAlign: 'center',
      color: 'var(--text-lo)', fontFamily: 'var(--font-mono)', fontSize: 11,
    }}>{msg}</div>
  );
}
