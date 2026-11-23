'use client';
import React from 'react';
import { LATENCY_DATA, THROUGHPUT_DATA } from './data';

export function P2Latency() {
  return (
    <section id="p2-s11" style={{ marginBottom: 48, scrollMarginTop: 80 }}>
      {/* Section Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <span style={{
          display: 'inline-block', padding: '3px 8px', borderRadius: 4,
          background: 'rgba(2,132,199,0.12)', border: '1px solid rgba(2,132,199,0.3)',
          fontFamily: 'var(--font-mono)', fontSize: 10, color: '#0284c7', fontWeight: 700, letterSpacing: '0.05em'
        }}>
          §P2.11
        </span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: 'var(--text-hi)', margin: 0 }}>
          Hardware Profiling, Microsecond Latencies &amp; Line-Rate Throughput
        </h2>
      </div>

      <p style={{ fontFamily: 'var(--font-ui)', fontSize: 13, color: 'var(--text-mid)', lineHeight: 1.7, maxWidth: 900, marginBottom: 20 }}>
        In response to peer-review critique on real-time execution feasibility (Audit Issue 31), Paper 2 provides rigorous microsecond-level
        hardware execution profiling. Every subsystem—XGBoost classifier, Isolation Forest, ADTM trust manager, TARP topology spreader, and benign
        veto filter—was profiled on dedicated hardware across single-flow (B=1) and amortized batched (B=32 to 4,096) streams.
      </p>

      {/* KPI Cards */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 14, marginBottom: 24
      }}>
        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 18px', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#64748b', letterSpacing: '0.1em', marginBottom: 6 }}>
            MAX GPU PIPELINE THROUGHPUT
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 700, color: '#0284c7' }}>177,340</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#64748b' }}>flows/sec</span>
          </div>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#0284c7', marginTop: 4, fontWeight: 600 }}>
            5.64 µs amortized latency (B=4,096)
          </div>
        </div>

        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 18px', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#64748b', letterSpacing: '0.1em', marginBottom: 6 }}>
            END-TO-END P_HYBRID THROUGHPUT
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 700, color: '#059669' }}>18,244</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#64748b' }}>flows/sec</span>
          </div>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#059669', marginTop: 4, fontWeight: 600 }}>
            54.81 µs end-to-end total budget
          </div>
        </div>

        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 18px', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#64748b', letterSpacing: '0.1em', marginBottom: 6 }}>
            ADTM TRUST UPDATE LATENCY
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 700, color: '#7c3aed' }}>0.86 µs</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#64748b' }}>/ flow</span>
          </div>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#7c3aed', marginTop: 4, fontWeight: 600 }}>
            1,156,350 updates / sec (CPU)
          </div>
        </div>

        <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 18px', boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#64748b', letterSpacing: '0.1em', marginBottom: 6 }}>
            BENIGN VETO OVERHEAD
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 700, color: '#ea580c' }}>0.0022 µs</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#64748b' }}>/ check</span>
          </div>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, color: '#ea580c', marginTop: 4, fontWeight: 600 }}>
            454.5M checks / sec (Zero penalty)
          </div>
        </div>
      </div>

      {/* Grid: Component Latency Budget + Throughput Scaling */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 20, marginBottom: 24 }}>
        {/* Table: Component Latencies */}
        <div style={{
          background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden',
          boxShadow: '0 1px 4px rgba(0,0,0,0.05)'
        }}>
          <div style={{
            padding: '12px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
          }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#334155' }}>
              TABLE 14A: PER-COMPONENT MICROSECOND LATENCY PROFILING (B=1)
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#0284c7', background: 'rgba(2,132,199,0.1)', padding: '2px 8px', borderRadius: 4 }}>
              HARDWARE MEASURED
            </span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11, textAlign: 'left' }}>
              <thead>
                <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Component</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Execution Hardware</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>P50 (µs)</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>P95 (µs)</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Mean (µs)</th>
                </tr>
              </thead>
              <tbody>
                {LATENCY_DATA.map((row: any, idx: number) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #e2e8f0', background: idx % 2 === 0 ? '#ffffff' : '#f8fafc' }}>
                    <td style={{ padding: '8px 10px', fontWeight: 600, color: '#1e293b' }}>{row.component}</td>
                    <td style={{ padding: '8px 10px', color: '#64748b' }}>{row.hardware}</td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)' }}>{parseFloat(row.p50_us).toFixed(1)} µs</td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)' }}>{parseFloat(row.p95_us).toFixed(1)} µs</td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#0284c7' }}>
                      {parseFloat(row.mean_us).toFixed(2)} µs
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Table: Batch Scaling Throughput */}
        <div style={{
          background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'hidden',
          boxShadow: '0 1px 4px rgba(0,0,0,0.05)'
        }}>
          <div style={{
            padding: '12px 18px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
          }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700, color: '#334155' }}>
              TABLE 14B: AMORTIZED BATCH THROUGHPUT SCALING (FPS)
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#059669', background: 'rgba(5,150,105,0.1)', padding: '2px 8px', borderRadius: 4 }}>
              LINE-RATE VERIFIED
            </span>
          </div>

          <div style={{ overflowX: 'auto', maxHeight: 270 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11, textAlign: 'left' }}>
              <thead>
                <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', color: '#475569', position: 'sticky', top: 0 }}>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Pipeline Stage</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600 }}>Batch (B)</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600, color: '#059669' }}>Throughput (FPS)</th>
                  <th style={{ padding: '8px 10px', fontWeight: 600, color: '#0284c7' }}>Amortized Latency</th>
                </tr>
              </thead>
              <tbody>
                {THROUGHPUT_DATA.slice(0, 12).map((row: any, idx: number) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #e2e8f0', background: idx % 2 === 0 ? '#ffffff' : '#f8fafc' }}>
                    <td style={{ padding: '8px 10px', fontWeight: 600, color: '#1e293b' }}>{row.component}</td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)' }}>B = {row.batch_size}</td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#059669', fontWeight: 600 }}>
                      {parseFloat(row.throughput_fps).toLocaleString(undefined, { maximumFractionDigits: 1 })} fps
                    </td>
                    <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: '#0284c7' }}>
                      {parseFloat(row.amortized_latency_us).toFixed(2)} µs
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Engineering Feasibility Callout */}
      <div style={{
        padding: '14px 18px', background: 'rgba(5,150,105,0.05)', border: '1px solid rgba(5,150,105,0.2)',
        borderRadius: 8, display: 'flex', alignItems: 'flex-start', gap: 12
      }}>
        <div style={{
          width: 24, height: 24, borderRadius: '50%', background: '#059669', color: '#ffffff',
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, fontSize: 12, fontWeight: 700
        }}>
          ⚡
        </div>
        <div style={{ fontSize: 12, color: '#334155', lineHeight: 1.6 }}>
          <strong>Real-Time Edge Gateway Feasibility:</strong> With end-to-end throughput exceeding <strong>18,244 flows/sec</strong> and an amortized latency budget of <strong>54.81 µs</strong>, the complete hybrid pipeline comfortably sustains gigabit-class edge traffic rates without packet dropping. At the sliding-window inspection tier (W=100 flows), posture escalation decisions occur within <strong>5.48 milliseconds</strong>, delivering near line-rate reactive defense.
        </div>
      </div>
    </section>
  );
}
