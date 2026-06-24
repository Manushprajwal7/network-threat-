'use client';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, Cell,
} from 'recharts';
import { SH, Box, Note, Spin, TP, MC, MN, MODEL_KEYS, DECISION_COLORS } from './utils';
import type { ResearchLatency } from '../../../lib/api';

// ─── §9 Trust Management ──────────────────────────────────────────────────────
const TRUST_DIM = [
  { key: 'user',       label: 'User Behaviour',  weight: '40%', color: '#0284c7',
    items: ['Login pattern analysis','Failed authentication count','Access time anomaly','Privilege escalation attempts'] },
  { key: 'device',     label: 'Device Health',   weight: '35%', color: '#059669',
    items: ['Endpoint security posture','OS patch compliance','Known-vulnerability score','Certificate validity'] },
  { key: 'behavioral', label: 'Traffic Behaviour', weight: '25%', color: '#7c3aed',
    items: ['Packet-rate deviation','Port-scan signature','Payload entropy','Protocol conformance'] },
];

const TRUST_DECAY = Array.from({ length: 61 }, (_, t) => ({
  t,
  pristine:   +Math.max(100 * Math.exp(-0.005 * t), 20).toFixed(1),
  withAlerts: +Math.max(100 * Math.exp(-0.005 * t) * (1 - 0.01 * Math.min(t, 40)), 15).toFixed(1),
}));

export function S9Trust() {
  return (
    <section style={{ marginBottom: 52 }}>
      <SH n={9} title="TRUST MANAGEMENT" sub="Multi-dimensional trust scoring model: composite score from three behavioural signal classes." />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(240px,1fr))', gap: 14, marginBottom: 16 }}>
        {TRUST_DIM.map(d => (
          <Box key={d.key} title={`${d.label.toUpperCase()} (${d.weight})`} accent={d.color}>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 700, color: d.color, marginBottom: 12 }}>{d.weight}</div>
            <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
              {d.items.map(item => (
                <li key={item} style={{ display: 'flex', gap: 7, marginBottom: 7, fontFamily: 'var(--font-ui)', fontSize: 12, color: 'var(--text-mid)' }}>
                  <span style={{ color: d.color, flexShrink: 0 }}>›</span>{item}
                </li>
              ))}
            </ul>
          </Box>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
        <Box title="COMPOSITE TRUST SCORE FORMULA">
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-hi)', background: 'rgba(2,132,199,0.06)', borderRadius: 8, padding: '14px 16px', lineHeight: 2 }}>
            <div>T<sub>composite</sub> = 0.40 × T<sub>user</sub></div>
            <div style={{ paddingLeft: 88 }}>+ 0.35 × T<sub>device</sub></div>
            <div style={{ paddingLeft: 88 }}>+ 0.25 × T<sub>behavioral</sub></div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 14 }}>
            {[
              { range: '90–100', tier: 'Trusted',         policy: 'Allow',      color: '#059669' },
              { range: '70–89',  tier: 'Low-Risk',        policy: 'Restrict',   color: '#d97706' },
              { range: '50–69',  tier: 'Moderate Risk',   policy: 'Alert',      color: '#0284c7' },
              { range: '30–49',  tier: 'High Risk',       policy: 'Quarantine', color: '#7c3aed' },
              { range: '0–29',   tier: 'Critical',        policy: 'Block',      color: '#dc2626' },
            ].map(t => (
              <div key={t.range} style={{ background: `${t.color}0a`, border: `1px solid ${t.color}30`, borderRadius: 7, padding: '8px 10px' }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', marginBottom: 3 }}>{t.range}</div>
                <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, fontWeight: 600, color: t.color }}>{t.tier}</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', marginTop: 2 }}>→ {t.policy}</div>
              </div>
            ))}
          </div>
        </Box>

        <Box title="TRUST SCORE TEMPORAL DECAY MODEL" caption="Fig 9.1. Simulated trust decay over 60-minute session (no live agent data).">
          <ResponsiveContainer width="100%" height={230}>
            <LineChart data={TRUST_DECAY} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.20)" />
              <XAxis dataKey="t" label={{ value: 'Time (min)', fill: 'var(--text-lo)', fontSize: 9, position: 'insideBottomRight', offset: -5 }}
                tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: '#8da8c0' }} />
              <YAxis domain={[0, 100]} tickFormatter={(v: number) => `${v}`}
                tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: '#8da8c0' }} />
              <Tooltip contentStyle={TP} formatter={(v: unknown) => [`${v as number}`, 'Score']} />
              <Legend wrapperStyle={{ fontFamily: 'var(--font-mono)', fontSize: 9 }} />
              <Line type="monotone" dataKey="pristine"   name="Clean session"   stroke="#059669" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="withAlerts" name="With alerts"      stroke="#dc2626" dot={false} strokeWidth={1.5} strokeDasharray="4 2" />
            </LineChart>
          </ResponsiveContainer>
          <Note>Trust decay model is parameterised. Static trust scoring tables are shown because no live agent stream is connected in this evaluation environment.</Note>
        </Box>
      </div>
    </section>
  );
}

// ─── §10 Security Decision Engine ─────────────────────────────────────────────
const POLICY_TIERS = [
  { tier: 'Allow',      trust: '90–100', score: 'Low threat',      timeout: 'Session-scoped', color: '#059669',
    conditions: ['Trust ≥ 90', 'No active threat', 'Normal traffic pattern'],
    actions: ['Full access granted', 'Session logged', 'Passive monitoring'] },
  { tier: 'Restrict',   trust: '70–89',  score: 'Moderate',        timeout: '30 min review', color: '#d97706',
    conditions: ['Trust 70–89', 'Minor anomaly', 'Off-hours access'],
    actions: ['Limit to known resources', 'Elevated audit logging', 'Step-up auth prompt'] },
  { tier: 'Alert',      trust: '50–69',  score: 'Elevated',        timeout: '10 min window', color: '#0284c7',
    conditions: ['Trust 50–69', 'Threat detected', 'Signature match ≥ 0.6'],
    actions: ['SOC notification', 'Session flag', 'Honeypot redirect option'] },
  { tier: 'Quarantine', trust: '30–49',  score: 'High',            timeout: 'Until review', color: '#7c3aed',
    conditions: ['Trust 30–49', 'Multi-stage attack indicator', 'Lateral movement'],
    actions: ['Network isolation', 'Forensic snapshot', 'Block all outbound'] },
  { tier: 'Block',      trust: '0–29',   score: 'Critical',        timeout: 'Immediate', color: '#dc2626',
    conditions: ['Trust < 30', 'Known malicious pattern', 'C2 beacon detected'],
    actions: ['Hard block', 'Session terminated', 'Threat intel feed update'] },
];

export function S10SecurityDecision() {
  return (
    <section style={{ marginBottom: 52 }}>
      <SH n={10} title="SECURITY DECISION ENGINE" sub="Adaptive five-tier security response policy driven by composite trust score and ML threat classification." />

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 16 }}>
        {POLICY_TIERS.map(p => (
          <div key={p.tier} style={{
            background: `${p.color}07`, border: `1px solid ${p.color}25`,
            borderLeft: `3px solid ${p.color}`, borderRadius: '0 10px 10px 0', padding: '14px 18px',
          }}>
            <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', alignItems: 'flex-start' }}>
              <div style={{ minWidth: 110 }}>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700, color: p.color, marginBottom: 3 }}>{p.tier}</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '.08em' }}>TRUST {p.trust}</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '.06em', marginTop: 2 }}>{p.score} risk</div>
              </div>
              <div style={{ flex: 1, minWidth: 200 }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '.1em', marginBottom: 5 }}>TRIGGER CONDITIONS</div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {p.conditions.map(c => (
                    <span key={c} style={{ fontFamily: 'var(--font-ui)', fontSize: 10, color: 'var(--text-mid)', background: 'rgba(0,0,0,0.12)', border: '1px solid #000000', borderRadius: 4, padding: '2px 7px' }}>{c}</span>
                  ))}
                </div>
              </div>
              <div style={{ flex: 1, minWidth: 200 }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '.1em', marginBottom: 5 }}>RESPONSE ACTIONS</div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {p.actions.map(a => (
                    <span key={a} style={{ fontFamily: 'var(--font-ui)', fontSize: 10, color: p.color, background: `${p.color}10`, border: `1px solid ${p.color}25`, borderRadius: 4, padding: '2px 7px' }}>{a}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <Box title="DECISION POLICY DISTRIBUTION (FRAMEWORK)" caption="Fig 10.1. Theoretical distribution across policy tiers assuming typical enterprise traffic composition.">
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={[
            { tier: 'Allow',      pct: 62 },
            { tier: 'Restrict',   pct: 18 },
            { tier: 'Alert',      pct: 12 },
            { tier: 'Quarantine', pct:  5 },
            { tier: 'Block',      pct:  3 },
          ]} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.20)" vertical={false} />
            <XAxis dataKey="tier" tick={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: '#8da8c0' }} />
            <YAxis tickFormatter={(v: number) => `${v}%`} tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: '#8da8c0' }} />
            <Tooltip contentStyle={TP} formatter={(v: unknown) => [`${v as number}%`, 'Decisions']} />
            <Bar dataKey="pct" name="% Decisions" radius={[4, 4, 0, 0]}>
              {POLICY_TIERS.map((p, i) => <Cell key={i} fill={p.color} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <Note>No live decision stream is connected in this evaluation environment. Values above represent theoretical enterprise traffic distribution for framework illustration purposes.</Note>
      </Box>
    </section>
  );
}

// ─── §11 Latency Analysis ─────────────────────────────────────────────────────
export function S11Latency({ lat, busy }: { lat: ResearchLatency | null; busy: boolean }) {
  if (busy) return <section style={{ marginBottom: 52 }}><SH n={11} title="LATENCY ANALYSIS" /><Spin /></section>;

  const latRows = lat?.latency ?? [];
  const barData = latRows.map(r => ({
    name: MN[r.model] ?? r.display_name,
    train: +r.train_time_s.toFixed(1),
    inference: +r.pred_time_s.toFixed(3),
    inferencMs: +r.pred_time_ms.toFixed(0),
    realtime: r.realtime_ok,
    color: MC[r.model] ?? '#0284c7',
  }));

  return (
    <section style={{ marginBottom: 52 }}>
      <SH n={11} title="LATENCY ANALYSIS" sub="Training time and batch inference latency across the model set." />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 14 }}>
        <Box title="TRAINING TIME (SECONDS)" caption="Fig 11.1. Wall-clock training time on the CICIoT2023 training set (XGBoost on GPU).">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={barData} margin={{ top: 5, right: 15, bottom: 5, left: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.20)" vertical={false} />
              <XAxis dataKey="name" tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: '#8da8c0' }} />
              <YAxis tickFormatter={(v: number) => `${v}s`} tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: '#8da8c0' }} />
              <Tooltip contentStyle={TP} formatter={(v: unknown) => [`${v as number}s`, 'Training']} />
              <Bar dataKey="train" name="Train (s)" radius={[4, 4, 0, 0]}>
                {barData.map((d, i) => <Cell key={i} fill={d.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Box>

        <Box title="INFERENCE LATENCY (ms)" caption="Fig 11.2. Batch inference over ~48K test samples. ✓ = real-time capable.">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={barData} margin={{ top: 5, right: 15, bottom: 5, left: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.20)" vertical={false} />
              <XAxis dataKey="name" tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: '#8da8c0' }} />
              <YAxis tickFormatter={(v: number) => `${v}ms`} tick={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: '#8da8c0' }} />
              <Tooltip contentStyle={TP} formatter={(v: unknown) => [`${v as number}ms`, 'Latency']} />
              <Bar dataKey="inferencMs" name="Inference (ms)" radius={[4, 4, 0, 0]}>
                {barData.map((d, i) => <Cell key={i} fill={d.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Box>
      </div>

      {/* Latency table */}
      <Box title="LATENCY COMPARISON TABLE" caption="All times from the same evaluation run. Inference measured over the full held-out test partition.">
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--font-mono)', fontSize: 10 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(2,132,199,0.22)' }}>
                {['Model', 'Train Time (s)', 'Pred Time (s)', 'Pred Time (ms)', 'Real-time OK?', 'Notes'].map(h => (
                  <th key={h} style={{ padding: '7px 10px', textAlign: 'left', color: 'var(--cyan)', fontSize: 9, letterSpacing: '.07em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {latRows.map(r => {
                const col = MC[r.model] ?? '#0284c7';
                return (
                  <tr key={r.model} style={{ borderBottom: '1px solid var(--border-dim)' }}>
                    <td style={{ padding: '8px 10px', color: col, fontWeight: 700 }}>{r.display_name}</td>
                    <td style={{ padding: '8px 10px', color: 'var(--text-mid)' }}>{r.train_time_s.toFixed(3)}s</td>
                    <td style={{ padding: '8px 10px', color: 'var(--text-mid)' }}>{r.pred_time_s.toFixed(3)}s</td>
                    <td style={{ padding: '8px 10px', color: 'var(--text-mid)' }}>{r.pred_time_ms.toFixed(0)}ms</td>
                    <td style={{ padding: '8px 10px' }}>
                      <span style={{ color: r.realtime_ok ? '#059669' : '#dc2626', fontWeight: 700 }}>
                        {r.realtime_ok ? '✓ Yes' : '✗ No'}
                      </span>
                    </td>
                    <td style={{ padding: '8px 10px', color: 'var(--text-lo)', fontSize: 9 }}>
                      {r.realtime_ok ? 'Suitable for per-flow classification' : 'Requires GPU or batching pipeline'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <Note>
          Decision Tree, XGBoost and the linear baselines satisfy real-time flow classification requirements.
          SVM batch inference (~18 min over the test set) is impractical for live deployment without major optimisation.
        </Note>
      </Box>
    </section>
  );
}
