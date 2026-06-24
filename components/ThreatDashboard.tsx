'use client';

import { useState, useEffect } from 'react';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
} from 'recharts';
import { getThreatDistribution, getTrafficTrend, type ThreatDistItem, type TrafficPoint } from '../lib/api';

function ChartTip({ active, payload, label }: { active?: boolean; payload?: Array<{name:string;value:number;color:string}>; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg px-3 py-2"
      style={{ background: 'rgba(255,255,255,0.97)', border: '1px solid rgba(0,0,0,0.20)', backdropFilter: 'blur(12px)' }}>
      {label && <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--cyan)', letterSpacing: '0.1em', marginBottom: 4 }}>{label}</div>}
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-2" style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-mid)' }}>
          <span style={{ color: p.color }}>■</span>
          {p.name}: <strong style={{ color: 'var(--text-hi)' }}>{p.value.toLocaleString()}</strong>
        </div>
      ))}
    </div>
  );
}

function PieTip({ active, payload }: { active?: boolean; payload?: Array<{name:string;value:number;payload:{color:string;percentage:number}}> }) {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <div className="rounded-lg px-3 py-2"
      style={{ background: 'rgba(255,255,255,0.97)', border: `1px solid ${d.payload.color}40`, backdropFilter: 'blur(12px)' }}>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: 10, color: d.payload.color, letterSpacing: '0.1em', marginBottom: 2 }}>{d.name}</div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-mid)' }}>
        Count: <strong style={{ color: 'var(--text-hi)' }}>{d.value.toLocaleString()}</strong>
      </div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: d.payload.color }}>{d.payload.percentage}%</div>
    </div>
  );
}

function EmptyChart({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-2" style={{ minHeight: 170 }}>
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--text-lo)" strokeWidth="1.5">
        <circle cx="12" cy="12" r="10"/><path d="M8 12h8"/><path d="M12 8v8"/>
      </svg>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', textAlign: 'center', maxWidth: 180 }}>{message}</span>
    </div>
  );
}

export default function ThreatDashboard() {
  const [distribution, setDistribution] = useState<ThreatDistItem[]>([]);
  const [trend, setTrend] = useState<TrafficPoint[]>([]);
  const [backendError, setBackendError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchAll() {
      try {
        const [distData, trendData] = await Promise.all([
          getThreatDistribution(),
          getTrafficTrend(),
        ]);
        if (cancelled) return;
        setBackendError(null);
        setDistribution(distData.distribution);
        setTrend(trendData.trend);
      } catch (err) {
        if (!cancelled) setBackendError((err as Error).message);
      }
    }

    fetchAll();
    const id = setInterval(fetchAll, 5000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const noData = distribution.length === 0;
  const noTrend = trend.length === 0 || trend.every(t => t.normal === 0 && t.threats === 0);

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">

      {/* Attack Distribution */}
      <div className="rounded-xl p-4 bracket-all"
        style={{ background: '#ffffff', border: '1px solid #000000', backdropFilter: 'blur(16px)', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
        <div className="card-header">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--purple)" strokeWidth="2">
            <path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>
          </svg>
          <span className="card-title">Attack Distribution</span>
          <span className="ml-auto" style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
            {backendError ? 'offline' : noData ? 'awaiting data' : `${distribution.length} classes`}
          </span>
        </div>

        {noData ? (
          <EmptyChart message={backendError ? 'Backend offline — start Flask server' : 'No events yet — start packet capture'} />
        ) : (
          <div className="flex gap-4 items-start">
            <div style={{ width: 170, height: 170, flexShrink: 0, minHeight: 170 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={distribution} cx="50%" cy="50%" innerRadius={48} outerRadius={76} dataKey="count" nameKey="name" paddingAngle={2}>
                    {distribution.map((e, i) => (
                      <Cell key={i} fill={e.color} stroke="rgba(255,255,255,0.8)" strokeWidth={1}/>
                    ))}
                  </Pie>
                  <Tooltip content={<PieTip />}/>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex-1 space-y-2 overflow-y-auto" style={{ maxHeight: 170 }}>
              {distribution.map(item => (
                <div key={item.name} className="flex items-center gap-2">
                  <div style={{ width: 6, height: 6, borderRadius: '50%', background: item.color, flexShrink: 0 }} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-mid)', whiteSpace: 'nowrap' }}>{item.name}</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: item.color, marginLeft: 8, flexShrink: 0 }}>{item.percentage}%</span>
                    </div>
                    <div className="track mt-0.5" style={{ height: 3 }}>
                      <div className="track-fill" style={{ width: `${item.percentage}%`, background: item.color }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Traffic Trend */}
      <div className="rounded-xl p-4 bracket-all"
        style={{ background: '#ffffff', border: '1px solid #000000', backdropFilter: 'blur(16px)', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
        <div className="card-header">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
          <span className="card-title">Live Traffic Trend</span>
          <span className="ml-auto" style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>rolling 12-min window</span>
        </div>

        {noTrend ? (
          <EmptyChart message={backendError ? 'Backend offline — start Flask server' : 'No traffic data yet — start packet capture'} />
        ) : (
          <>
            <div style={{ width: '100%', height: 188 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trend} margin={{ top: 4, right: 8, left: -24, bottom: 0 }}>
                  <defs>
                    <linearGradient id="gNormal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--cyan)" stopOpacity="0.25"/>
                      <stop offset="100%" stopColor="var(--cyan)" stopOpacity="0"/>
                    </linearGradient>
                    <linearGradient id="gThreat" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--red)" stopOpacity="0.45"/>
                      <stop offset="100%" stopColor="var(--red)" stopOpacity="0"/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.20)" vertical={false}/>
                  <XAxis dataKey="time" tick={{ fill: 'var(--text-lo)', fontSize: 9, fontFamily: 'var(--font-mono)' }} axisLine={false} tickLine={false}/>
                  <YAxis tick={{ fill: 'var(--text-lo)', fontSize: 9, fontFamily: 'var(--font-mono)' }} axisLine={false} tickLine={false}/>
                  <Tooltip content={<ChartTip/>}/>
                  <Area type="monotone" dataKey="normal" name="Normal" stroke="var(--cyan)" strokeWidth={1.5} fill="url(#gNormal)"/>
                  <Area type="monotone" dataKey="threats" name="Threats" stroke="var(--red)" strokeWidth={1.5} fill="url(#gThreat)"/>
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="flex gap-4 mt-1">
              {[{ c: 'var(--cyan)', l: 'Normal Traffic' }, { c: 'var(--red)', l: 'Threats' }].map(x => (
                <div key={x.l} className="flex items-center gap-1.5">
                  <div style={{ width: 12, height: 2, background: x.c, borderRadius: 1 }} />
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>{x.l}</span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
