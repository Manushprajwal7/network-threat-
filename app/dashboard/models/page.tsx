'use client';

import { useState, useEffect } from 'react';
import { getHealth, getModelComparison, getCaptureStatus, getDebugInfo, type HealthStatus, type ModelComparisonRow, type CaptureStatus, type DebugInfo } from '../../../lib/api';

const MODEL_DESC: Record<string, string> = {
  xgboost:             'GPU-accelerated gradient boosting — BEST PERFORMER (71.51% Macro F1)',
  random_forest:       'Ensemble of 200 decision trees — fast ensemble model',
  decision_tree:       'CART tree — fastest inference (266ms)',
  logistic_regression: 'Linear probabilistic classifier',
  svm:                 'Support Vector Machine with RBF kernel',
  knn:                 'K-Nearest Neighbours — distance-based classifier',
  naive_bayes:         'Gaussian Naive Bayes — probabilistic baseline',
};

const MODEL_COLOR: Record<string, string> = {
  xgboost: '#7c3aed', random_forest: '#0284c7', decision_tree: '#059669', logistic_regression: '#7c3aed',
  svm: '#d97706', knn: '#ea6c1a', naive_bayes: '#8b5cf6',
};

function MetricBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="track flex-1" style={{ height: 4, minWidth: 60 }}>
        <div className="track-fill" style={{ width: `${value * 100}%`, background: color, transition: 'width 0.8s' }} />
      </div>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color, minWidth: 42, textAlign: 'right' }}>
        {(value * 100).toFixed(2)}%
      </span>
    </div>
  );
}

export default function ModelsPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [comparison, setComparison] = useState<ModelComparisonRow[] | null>(null);
  const [captureStatus, setCaptureStatus] = useState<CaptureStatus | null>(null);
  const [debugInfo, setDebugInfo] = useState<DebugInfo | null>(null);
  const [compError, setCompError] = useState<string | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchData() {
      try {
        const [h, cs, d] = await Promise.all([
          getHealth(),
          getCaptureStatus(),
          getDebugInfo().catch(() => null),
        ]);
        if (cancelled) return;
        setBackendError(null);
        setHealth(h);
        setCaptureStatus(cs);
        setDebugInfo(d);
      } catch (err) {
        if (!cancelled) setBackendError((err as Error).message);
      }
    }
    async function fetchComparison() {
      try {
        const c = await getModelComparison();
        if (!cancelled) { setComparison(c.models); setCompError(null); }
      } catch (err) {
        if (!cancelled) setCompError((err as Error).message);
      }
    }
    fetchData();
    fetchComparison();
    const id = setInterval(fetchData, 5000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const models = health?.available_models ?? [];
  const primary = health?.primary_model ?? 'xgboost';

  const METRIC_COLS = ['accuracy','f1_score','macro_f1','attack_detection_rate'];

  return (
    <>
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="section-label mb-2">Machine Learning Pipeline</div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 800, color: 'var(--text-hi)', letterSpacing: '0.03em', lineHeight: 1 }}>
            ML Models — CICIoT2023
          </h1>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)', marginTop: 4 }}>
            CICIoT2023 · 46 features · 34 attack classes · 7 models · XGBoost GPU-accelerated
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="tag"
            style={{
              background: health?.models_loaded ? 'rgba(5,150,105,0.09)' : 'rgba(220,38,38,0.09)',
              color: health?.models_loaded ? 'var(--green)' : 'var(--red)',
              border: `1px solid ${health?.models_loaded ? 'rgba(5,150,105,0.28)' : 'rgba(220,38,38,0.28)'}`,
              fontFamily: 'var(--font-display)', fontSize: 9, letterSpacing: '0.1em', padding: '5px 12px',
            }}>
            <span className={`pulse-dot ${health?.models_loaded ? 'pulse-green' : 'pulse-red'}`} style={{ width: 4, height: 4 }} />
            {health?.models_loaded ? 'MODELS LOADED' : 'NOT LOADED'}
          </div>
        </div>
      </div>

      {backendError && (
        <div className="rounded-xl p-4 mb-5"
          style={{ background: 'rgba(220,38,38,0.07)', border: '1px solid rgba(220,38,38,0.24)' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--red)' }}>
            ⚠ Backend offline: {backendError} — start Flask server with: python backend/api/app.py
          </span>
        </div>
      )}

      {/* Live inference stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
        {[
          { l: 'Models Available',  v: models.length.toString(),                  c: 'var(--cyan)' },
          { l: 'Events Analyzed',   v: captureStatus?.events_analyzed.toLocaleString() ?? '—', c: 'var(--purple)' },
          { l: 'Pipeline Errors',   v: captureStatus?.packets_failed?.toLocaleString() ?? '—', c: captureStatus?.packets_failed ? 'var(--red)' : 'var(--green)' },
          { l: 'ML Ready',          v: captureStatus?.ml_ready ? 'YES' : 'NO',   c: captureStatus?.ml_ready ? 'var(--green)' : 'var(--red)' },
        ].map(s => (
          <div key={s.l} className="rounded-xl p-4 bracket-all"
            style={{ background: '#ffffff', border: '1px solid #000000', backdropFilter: 'blur(16px)', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '0.12em', marginBottom: 4 }}>{s.l}</div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 800, color: s.c, lineHeight: 1 }}>{s.v}</div>
          </div>
        ))}
      </div>

      {/* Debug panel — show if there are pipeline errors */}
      {debugInfo && (debugInfo.packets_failed > 0 || debugInfo.last_error) && (
        <div className="rounded-xl p-4 bracket-all mb-5"
          style={{ background: 'rgba(220,38,38,0.05)', border: '1px solid rgba(220,38,38,0.24)', backdropFilter: 'blur(16px)' }}>
          <div className="card-header mb-3">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--red)" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <span className="card-title" style={{ color: 'var(--red)' }}>Pipeline Diagnostics</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-3">
            {[
              { l: 'Events in queue', v: debugInfo.events_in_queue },
              { l: 'Packets captured', v: debugInfo.packets_captured },
              { l: 'Events analyzed', v: debugInfo.events_analyzed },
              { l: 'Packets failed', v: debugInfo.packets_failed },
            ].map(s => (
              <div key={s.l}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '0.1em' }}>{s.l}</div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700, color: 'var(--text-hi)' }}>{s.v}</div>
              </div>
            ))}
          </div>
          {debugInfo.last_error && (
            <div className="px-3 py-2 rounded"
              style={{ background: 'rgba(220,38,38,0.08)', border: '1px solid rgba(220,38,38,0.24)', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--red)', wordBreak: 'break-all' }}>
              Last error: {debugInfo.last_error}
            </div>
          )}
        </div>
      )}

      {/* Available models grid */}
      <div className="rounded-xl p-4 bracket-all mb-5"
        style={{ background: '#ffffff', border: '1px solid #000000', backdropFilter: 'blur(16px)', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
        <div className="card-header mb-4">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2">
            <rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/>
          </svg>
          <span className="card-title">Available Models</span>
          <span className="ml-auto tag" style={{ background: 'rgba(2,132,199,0.10)', color: 'var(--cyan)', border: '1px solid rgba(2,132,199,0.22)', fontSize: 9 }}>
            {models.length} loaded
          </span>
        </div>

        {models.length === 0 ? (
          <div className="py-8 text-center">
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)' }}>
              {backendError ? 'Backend offline' : 'No models found — run: python ml_model/train_models.py'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {models.map(model => {
              const color = MODEL_COLOR[model] ?? 'var(--text-mid)';
              const isPrimary = model === primary;
              return (
                <div key={model} className="rounded-lg p-3 transition-all"
                  style={{
                    background: isPrimary ? `${color}0f` : 'rgba(0,0,0,0.08)',
                    border: `1px solid ${isPrimary ? `${color}40` : 'rgba(0,0,0,0.20)'}`,
                  }}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 rounded-full" style={{ background: color, boxShadow: `0 0 6px ${color}` }} />
                    <span style={{ fontFamily: 'var(--font-display)', fontSize: 10, fontWeight: 700, color, letterSpacing: '0.08em' }}>
                      {model.replace(/_/g, ' ').toUpperCase()}
                    </span>
                    {isPrimary && (
                      <span className="ml-auto tag" style={{ fontSize: 8, background: `${color}15`, color, border: `1px solid ${color}30` }}>
                        PRIMARY
                      </span>
                    )}
                  </div>
                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)', lineHeight: 1.5 }}>
                    {MODEL_DESC[model] ?? 'scikit-learn classifier'}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Model comparison table */}
      <div className="rounded-xl overflow-hidden bracket-all mb-5"
        style={{ background: '#ffffff', border: '1px solid #000000', backdropFilter: 'blur(16px)', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
        <div className="flex items-center gap-3 px-4 py-3"
          style={{ borderBottom: '1px solid var(--border-dim)', background: 'rgba(0,0,0,0.05)' }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--purple)" strokeWidth="2">
            <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
          </svg>
          <span className="card-title">Model Performance Comparison — CICIoT2023</span>
          <span className="tag ml-auto" style={{ background: 'rgba(124,58,237,0.10)', color: 'var(--purple)', border: '1px solid rgba(124,58,237,0.24)', fontSize: 9 }}>
            7 models evaluated
          </span>
        </div>

        {compError ? (
          <div className="px-4 py-8 text-center">
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)' }}>
              No comparison data — run model evaluation:
            </p>
            <code style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--cyan)', marginTop: 8, display: 'block' }}>
              python ml_model/train_models.py
            </code>
          </div>
        ) : !comparison ? (
          <div className="flex items-center justify-center py-8">
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-lo)' }}>Loading…</div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="w-full data-table" style={{ minWidth: 700 }}>
              <thead style={{ position: 'sticky', top: 0, background: 'rgba(0,0,0,0.08)', zIndex: 2 }}>
                <tr>
                  <th className="text-left">Model</th>
                  {METRIC_COLS.map(c => (
                    <th key={c} className="text-left">{c.replace(/_/g, ' ').toUpperCase()}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {comparison
                  .sort((a, b) => ((b.macro_f1 as number) ?? 0) - ((a.macro_f1 as number) ?? 0))
                  .map((row, i) => {
                    const modelName = String(row.model_name ?? '');
                    const color = MODEL_COLOR[modelName] ?? 'var(--text-mid)';
                    const isPrimary = modelName === primary;
                    return (
                      <tr key={modelName || `row-${i}`}
                        style={{ background: isPrimary ? `${color}06` : 'transparent' }}>
                        <td>
                          <div className="flex items-center gap-2">
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>#{i + 1}</span>
                            <div className="w-2 h-2 rounded-full" style={{ background: color }} />
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: isPrimary ? 700 : 400, color }}>{modelName}</span>
                            {isPrimary && <span className="tag" style={{ fontSize: 8, background: `${color}15`, color, border: `1px solid ${color}25` }}>LIVE</span>}
                          </div>
                        </td>
                        {METRIC_COLS.map(col => {
                          const val = Number(row[col] ?? 0);
                          return (
                            <td key={col}>
                              <MetricBar value={isNaN(val) ? 0 : val} color={color} />
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        )}

        <div className="px-4 py-2" style={{ borderTop: '1px solid var(--border-dim)', background: 'rgba(0,0,0,0.03)' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
            CICIoT2023 dataset · 5.4M train, 1.2M val/test samples · 46 features · 34 attack classes · XGBoost GPU-accelerated (Macro F1: 71.51%)
          </span>
        </div>
      </div>

      {/* tshark info */}
      <div className="rounded-xl p-4 bracket-all mb-5"
        style={{ background: '#ffffff', border: '1px solid #000000', backdropFilter: 'blur(16px)', boxShadow: '0 1px 4px rgba(0,0,0,0.15)' }}>
        <div className="card-header mb-3">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" strokeWidth="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
          <span className="card-title">Capture Infrastructure</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { l: 'tshark Available', v: health?.tshark_available ? 'YES' : 'NO', c: health?.tshark_available ? 'var(--green)' : 'var(--red)' },
            { l: 'tshark Path', v: health?.tshark_info ?? '—', c: 'var(--text-mid)' },
            { l: 'Capture Backend', v: health?.backend ?? '—', c: 'var(--cyan)' },
          ].map(s => (
            <div key={s.l} className="px-3 py-2 rounded"
              style={{ background: 'rgba(0,0,0,0.08)', border: '1px solid rgba(0,0,0,0.12)' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-lo)', letterSpacing: '0.1em', marginBottom: 4 }}>{s.l}</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: s.c, wordBreak: 'break-all' }}>{s.v}</div>
            </div>
          ))}
        </div>
        <div className="mt-3 px-3 py-2 rounded"
          style={{ background: 'rgba(2,132,199,0.05)', border: '1px solid rgba(2,132,199,0.10)' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-lo)' }}>
            // Feature extraction is a per-packet approximation of CICFlowMeter flow-level statistics.
            For production accuracy, integrate full CICFlowMeter pipeline. Live inference latency is dominated by Random Forest predict_proba() call.
          </span>
        </div>
      </div>

      <div style={{ height: 40 }} />
    </>
  );
}
