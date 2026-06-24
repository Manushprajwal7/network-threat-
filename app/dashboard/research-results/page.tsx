"use client";

import { useState, useEffect, useCallback } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Cell,
} from "recharts";
import {
  getResearchComparison,
  getResearchPerClass,
  getResearchLatency,
  getResearchConfusionMatrix,
  getResearchConfusionMatrixList,
  researchExportUrls,
  type ResearchModelRow,
  type ResearchPerClassRow,
  type ResearchLatencyRow,
  type ResearchComparison,
  type ResearchPerClass,
  type ResearchLatency,
} from "../../../lib/api";

// ── Palette ────────────────────────────────────────────────────────────────────
const MODEL_COLOR: Record<string, string> = {
  // CICIoT2023 ensemble + baselines (plain model names)
  xgboost: "#7c3aed",
  random_forest: "#0284c7",
  decision_tree: "#059669",
  logistic_regression: "#8b5cf6",
  svm: "#d97706",
  knn: "#ea6c1a",
  naive_bayes: "#ec4899",
  // Legacy research keys (kept for back-compat)
  xgboost_research: "#0284c7",
  random_forest_research: "#059669",
  cnn_research: "#7c3aed",
  lstm_research: "#d97706",
};
const MODEL_SHORT: Record<string, string> = {
  xgboost: "XGBoost",
  random_forest: "Random Forest",
  decision_tree: "Decision Tree",
  logistic_regression: "Logistic Reg.",
  svm: "SVM",
  knn: "KNN",
  naive_bayes: "Naive Bayes",
  xgboost_research: "XGBoost",
  random_forest_research: "Random Forest",
  cnn_research: "CNN",
  lstm_research: "LSTM",
};
const RANK_COLOR = ["#d97706", "#8da8c0", "#cd7f32", "#6b7280"];

// ── Helpers ────────────────────────────────────────────────────────────────────
const pct = (v: number | null | undefined) =>
  v != null ? `${(v * 100).toFixed(2)}%` : "—";
const pct4 = (v: number | null | undefined) =>
  v != null ? `${(v * 100).toFixed(4)}%` : "—";
const fmt3 = (v: number | null | undefined) => (v != null ? v.toFixed(3) : "—");
const secs = (v: number | null | undefined) =>
  v != null ? `${v.toFixed(1)}s` : "—";

function cleanClass(name: string): string {
  return name
    .replace(/[^\x20-\x7E]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

// ── Reusable UI pieces ─────────────────────────────────────────────────────────

function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl p-5 ${className}`}
      style={{
        background: "rgba(255,255,255,0.94)",
        border: "1px solid #000000",
        backdropFilter: "blur(16px)",
      }}
    >
      {children}
    </div>
  );
}

function SLabel({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        fontFamily: "var(--font-mono)",
        fontSize: 9,
        color: "var(--text-lo)",
        letterSpacing: "0.14em",
        marginBottom: 10,
        textTransform: "uppercase",
      }}
    >
      {children}
    </div>
  );
}

function SectionTitle({
  icon,
  title,
  sub,
}: {
  icon: React.ReactNode;
  title: string;
  sub?: string;
}) {
  return (
    <div className="flex items-center gap-3 mb-5">
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: 8,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "rgba(2,132,199,0.12)",
          border: "1px solid rgba(2,132,199,0.28)",
          flexShrink: 0,
        }}
      >
        {icon}
      </div>
      <div>
        <div
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 14,
            fontWeight: 700,
            color: "var(--cyan)",
            letterSpacing: "0.06em",
          }}
        >
          {title}
        </div>
        {sub && (
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 9,
              color: "var(--text-lo)",
              letterSpacing: "0.1em",
              marginTop: 2,
            }}
          >
            {sub}
          </div>
        )}
      </div>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div
      style={{
        textAlign: "center",
        padding: "40px 20px",
        color: "var(--text-lo)",
        fontFamily: "var(--font-mono)",
        fontSize: 11,
        border: "1px dashed rgba(2,132,199,0.15)",
        borderRadius: 10,
      }}
    >
      <svg
        width="32"
        height="32"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.2"
        style={{ margin: "0 auto 12px", display: "block", opacity: 0.4 }}
      >
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8" />
      </svg>
      {message}
      <div style={{ marginTop: 8, fontSize: 10, color: "rgba(2,132,199,0.40)" }}>
        Run: cd backend &amp;&amp; python ml_model/train_ciciot2023_models.py &amp;&amp; python ml_model/make_research_reports.py
      </div>
    </div>
  );
}

function Badge({
  color,
  children,
}: {
  color: string;
  children: React.ReactNode;
}) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        padding: "2px 8px",
        borderRadius: 4,
        background: `${color}15`,
        border: `1px solid ${color}35`,
        color,
        fontFamily: "var(--font-mono)",
        fontSize: 10,
        fontWeight: 600,
        letterSpacing: "0.04em",
      }}
    >
      {children}
    </span>
  );
}

function ExportBtn({
  href,
  label,
  icon,
}: {
  href: string;
  label: string;
  icon: string;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      style={{
        display: "flex",
        alignItems: "center",
        gap: 7,
        padding: "8px 14px",
        borderRadius: 7,
        cursor: "pointer",
        background: "rgba(2,132,199,0.08)",
        border: "1px solid rgba(2,132,199,0.22)",
        color: "var(--cyan)",
        fontFamily: "var(--font-mono)",
        fontSize: 10,
        fontWeight: 600,
        textDecoration: "none",
        letterSpacing: "0.05em",
        transition: "all 0.15s",
      }}
    >
      <svg
        width="13"
        height="13"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d={icon} />
      </svg>
      {label}
    </a>
  );
}

// ── Chart tooltip ─────────────────────────────────────────────────────────────
const ChartTooltip = ({
  active,
  payload,
  label,
  isPercent = true,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
  isPercent?: boolean;
}) => {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "#f8fafc",
        border: "1px solid var(--border-mid)",
        borderRadius: 8,
        padding: "10px 14px",
        fontFamily: "var(--font-mono)",
        fontSize: 11,
      }}
    >
      <div style={{ color: "var(--text-mid)", marginBottom: 6 }}>{label}</div>
      {payload.map((p) => (
        <div key={p.name} style={{ color: p.color, marginBottom: 2 }}>
          {p.name}: <strong>{isPercent ? pct(p.value) : fmt3(p.value)}</strong>
        </div>
      ))}
    </div>
  );
};

// ── Main page ──────────────────────────────────────────────────────────────────

export default function ResearchResultsPage() {
  const [comparison, setComparison] = useState<ResearchComparison | null>(null);
  const [perClass, setPerClass] = useState<ResearchPerClass | null>(null);
  const [latency, setLatency] = useState<ResearchLatency | null>(null);
  const [cmImages, setCmImages] = useState<Record<string, string | null>>({});
  const [cmAvail, setCmAvail] = useState<string[]>([]);
  const [activeModel, setActiveModel] = useState<string>("xgboost");
  const [pcModel, setPcModel] = useState<string>("xgboost");
  const [activeTab, setActiveTab] = useState<"table" | "charts" | "radar">(
    "table"
  );
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState<string[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    const errs: string[] = [];

    await Promise.allSettled([
      getResearchComparison()
        .then(setComparison)
        .catch(() => errs.push("model-comparison")),
      getResearchPerClass()
        .then(setPerClass)
        .catch(() => errs.push("per-class")),
      getResearchLatency()
        .then(setLatency)
        .catch(() => errs.push("latency")),
      getResearchConfusionMatrixList()
        .then((r) => {
          const avail = r.matrices
            .filter((m) => m.available)
            .map((m) => m.model);
          setCmAvail(avail);
          if (avail.length > 0) setActiveModel(avail[0]);
        })
        .catch(() => errs.push("cm-list")),
    ]);

    setErrors(errs);
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Lazy-load confusion matrix image when tab/model changes
  useEffect(() => {
    if (!activeModel || cmImages[activeModel] !== undefined) return;
    getResearchConfusionMatrix(activeModel)
      .then((r) =>
        setCmImages((prev) => ({
          ...prev,
          [activeModel]: r.image_base64 ?? null,
        }))
      )
      .catch(() => setCmImages((prev) => ({ ...prev, [activeModel]: null })));
  }, [activeModel, cmImages]);

  // ── Derived chart data ──────────────────────────────────────────────────────
  const models = comparison?.models ?? [];

  const barData = models.map((m) => ({
    name: MODEL_SHORT[m.model_name] ?? m.display_name,
    key: m.model_name,
    accuracy: m.accuracy,
    macro_f1: m.macro_f1,
    adr: m.attack_detection_rate,
    fpr: m.false_positive_rate,
    w_f1: m.f1_score,
  }));

  const radarData = [
    {
      metric: "Accuracy",
      ...Object.fromEntries(
        models.map((m) => [MODEL_SHORT[m.model_name], m.accuracy])
      ),
    },
    {
      metric: "Macro-F1",
      ...Object.fromEntries(
        models.map((m) => [MODEL_SHORT[m.model_name], m.macro_f1])
      ),
    },
    {
      metric: "ADR",
      ...Object.fromEntries(
        models.map((m) => [MODEL_SHORT[m.model_name], m.attack_detection_rate])
      ),
    },
    {
      metric: "1-FPR",
      ...Object.fromEntries(
        models.map((m) => [
          MODEL_SHORT[m.model_name],
          1 - m.false_positive_rate,
        ])
      ),
    },
    {
      metric: "W-F1",
      ...Object.fromEntries(
        models.map((m) => [MODEL_SHORT[m.model_name], m.f1_score])
      ),
    },
    {
      metric: "Bal. Acc.",
      ...Object.fromEntries(
        models.map((m) => [MODEL_SHORT[m.model_name], m.balanced_accuracy])
      ),
    },
  ];

  // Per-class rows for selected model
  const pcRows: ResearchPerClassRow[] = (
    perClass?.models_data?.[pcModel]?.rows ?? []
  )
    .map((r) => ({ ...r, class: cleanClass(r.class) }))
    .sort((a, b) => {
      if (a.class === "BENIGN") return 1;
      if (b.class === "BENIGN") return -1;
      return b.f1 - a.f1;
    });

  const pcSummary = perClass?.models_data?.[pcModel]?.summary;

  if (loading)
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: 400,
        }}
      >
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 12,
            color: "var(--text-lo)",
            letterSpacing: "0.1em",
          }}
        >
          LOADING RESEARCH REPORTS…
        </div>
      </div>
    );

  return (
    <div style={{ color: "var(--text-hi)" }}>
      {/* ── Page header ─────────────────────────────────────────────── */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 9,
              color: "var(--text-lo)",
              letterSpacing: "0.14em",
              marginBottom: 4,
            }}
          >
            // TOPOLOGY-AWARE MULTI-LEVEL PROTECTION FRAMEWORK
          </div>
          <h1
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 22,
              fontWeight: 700,
              color: "var(--cyan)",
              letterSpacing: "0.06em",
            }}
          >
            RESEARCH RESULTS & MODEL EVALUATION
          </h1>
          <div
            style={{
              fontFamily: "var(--font-ui)",
              fontSize: 12,
              color: "var(--text-mid)",
              marginTop: 2,
            }}
          >
            Dataset: {comparison?.dataset ?? "CICIoT2023"} · Split: {comparison?.split_mode ?? "Train/Val/Test"} · Publication-ready metrics
          </div>
        </div>

        {/* Export buttons */}
        <div
          className="flex flex-wrap gap-2 justify-end"
          style={{ maxWidth: 420 }}
        >
          <ExportBtn
            href={researchExportUrls.modelComparisonCsv()}
            label="Model Comparison CSV"
            icon="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4 M7 10l5 5 5-5 M12 15V3"
          />
          <ExportBtn
            href={researchExportUrls.perClassCsv()}
            label="Per-Class Metrics CSV"
            icon="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4 M7 10l5 5 5-5 M12 15V3"
          />
          <ExportBtn
            href={researchExportUrls.summaryTxt()}
            label="Research Summary TXT"
            icon="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6"
          />
          {cmAvail.slice(0, 2).map((m) => (
            <ExportBtn
              key={m}
              href={researchExportUrls.confusionMatrix(m)}
              label={`${MODEL_SHORT[m] ?? m} CM PNG`}
              icon="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4 M7 10l5 5 5-5 M12 15V3"
            />
          ))}
        </div>
      </div>

      {/* ── Summary cards ───────────────────────────────────────────── */}
      <div className="grid grid-cols-7 gap-3 mb-6">
        {[
          { label: "Dataset", value: comparison?.dataset ?? "CICIoT2023", color: "var(--cyan)" },
          { label: "Split", value: comparison?.split_mode ?? "Train/Val/Test", color: "var(--cyan)" },
          { label: "Features", value: String(comparison?.num_features ?? 46), color: "#059669" },
          { label: "Classes", value: String(comparison?.num_classes ?? 34), color: "#059669" },
          {
            label: "Best Model",
            value: comparison
              ? MODEL_SHORT[comparison.best_model] ?? comparison.best_model
              : "—",
            color: "#d97706",
          },
          {
            label: "Best Macro-F1",
            value: comparison ? pct(comparison.best_macro_f1) : "—",
            color: "#d97706",
          },
          {
            label: "Best ADR",
            value: comparison ? pct(comparison.best_adr) : "—",
            color: "#d97706",
          },
        ].map((k) => (
          <div
            key={k.label}
            style={{
              borderRadius: 10,
              padding: "12px 14px",
              background: "rgba(255,255,255,0.94)",
              border: "1px solid #000000",
            }}
          >
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 8,
                color: "var(--text-lo)",
                letterSpacing: "0.12em",
                marginBottom: 4,
              }}
            >
              {k.label.toUpperCase()}
            </div>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 15,
                fontWeight: 700,
                color: k.color,
                letterSpacing: "0.02em",
              }}
            >
              {k.value}
            </div>
          </div>
        ))}
      </div>

      {/* ── Research Interpretation ─────────────────────────────────── */}
      <Card className="mb-5">
        <SectionTitle
          title="RESEARCH INTERPRETATION"
          sub="// PUBLICATION-READY ANALYSIS"
          icon={
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--cyan)"
              strokeWidth="1.8"
            >
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 1 1 3-3h7z" />
            </svg>
          }
        />

        {/* Metric note callout */}
        <div
          style={{
            marginBottom: 16,
            padding: "10px 14px",
            borderRadius: 8,
            background: "rgba(217,119,6,0.07)",
            border: "1px solid rgba(217,119,6,0.24)",
            display: "flex",
            gap: 10,
            alignItems: "flex-start",
          }}
        >
          <svg
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#d97706"
            strokeWidth="2"
            style={{ flexShrink: 0, marginTop: 1 }}
          >
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z M12 9v4 M12 17h.01" />
          </svg>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              color: "#d97706",
              lineHeight: 1.6,
            }}
          >
            <strong>Primary metrics for CICIoT2023:</strong> Macro-F1 and Attack
            Detection Rate (ADR). Accuracy is inflated by the dominant DDoS/BENIGN
            classes and should not be used as the sole evaluation criterion.
            Macro-F1 treats every one of the 34 classes equally regardless of
            support, giving a fair view of minority attack-class detection.
          </span>
        </div>

        <p
          style={{
            fontFamily: "var(--font-ui)",
            fontSize: 13,
            color: "var(--text-mid)",
            lineHeight: 1.75,
            marginBottom: 12,
          }}
        >
          Macro-F1 and Attack Detection Rate were considered the most reliable
          indicators of model generalization across the 34 IoT attack classes.
          XGBoost (GPU-accelerated) achieved the best Macro-F1 of{" "}
          <strong style={{ color: "#7c3aed" }}>71.51%</strong> and ADR of{" "}
          <strong style={{ color: "#7c3aed" }}>70.35%</strong> at{" "}
          <strong style={{ color: "var(--cyan)" }}>98.99%</strong> accuracy,
          followed by Decision Tree (Macro-F1{" "}
          <strong style={{ color: "#059669" }}>66.23%</strong>) and Random Forest
          (Macro-F1 <strong style={{ color: "#0284c7" }}>63.95%</strong>). This
          confirms that ensemble-based tree models are the most effective and
          efficient choice for flow-based IoT intrusion detection — XGBoost forms
          the core of the live ensemble alongside Random Forest.
        </p>
        <p
          style={{
            fontFamily: "var(--font-ui)",
            fontSize: 13,
            color: "var(--text-mid)",
            lineHeight: 1.75,
          }}
        >
          The distance- and probability-based baselines underperform sharply on
          this 34-class problem (Naive Bayes Macro-F1{" "}
          <strong style={{ color: "#ec4899" }}>17.13%</strong>; KNN, Logistic
          Regression and SVM below <strong style={{ color: "#d97706" }}>1%</strong>{" "}
          Macro-F1). These were trained on aggressively sub-sampled data for
          tractability and do not generalise to the full distribution. SVM is
          additionally impractical at inference (~18&nbsp;min over the test set),
          whereas Decision Tree predicts in <strong>267&nbsp;ms</strong>. The
          results justify deploying a Random&nbsp;Forest&nbsp;+&nbsp;XGBoost
          ensemble for the live pipeline.
        </p>
      </Card>

      {/* ── Model Comparison ────────────────────────────────────────── */}
      <Card className="mb-5">
        <SectionTitle
          title="MODEL COMPARISON"
          sub="// RANKED BY MACRO-F1 (HONEST MULTI-CLASS METRIC)"
          icon={
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--cyan)"
              strokeWidth="1.8"
            >
              <path d="M18 20V10 M12 20V4 M6 20v-6" />
            </svg>
          }
        />

        {/* Tab switcher */}
        <div className="flex gap-2 mb-4">
          {(["table", "charts", "radar"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setActiveTab(t)}
              style={{
                padding: "6px 16px",
                borderRadius: 6,
                cursor: "pointer",
                fontFamily: "var(--font-mono)",
                fontSize: 10,
                fontWeight: 600,
                background:
                  activeTab === t ? "rgba(2,132,199,0.18)" : "transparent",
                border:
                  activeTab === t
                    ? "1px solid rgba(2,132,199,0.40)"
                    : "1px solid var(--border-dim)",
                color: activeTab === t ? "var(--cyan)" : "var(--text-lo)",
                transition: "all 0.15s",
              }}
            >
              {t.toUpperCase()}
            </button>
          ))}
        </div>

        {models.length === 0 ? (
          <EmptyState message="model_comparison_ciciot2023.csv not found." />
        ) : activeTab === "table" ? (
          /* ── Table view ── */
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontFamily: "var(--font-mono)",
                fontSize: 11,
                whiteSpace: "nowrap",
              }}
            >
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-mid)" }}>
                  {[
                    "Rank",
                    "Model",
                    "Accuracy",
                    "W-F1",
                    "Macro-F1 ★",
                    "ADR ★",
                    "FPR",
                    "FNR",
                    "ROC-AUC",
                    "Bal. Acc.",
                    "Train(s)",
                  ].map((h) => (
                    <th
                      key={h}
                      style={{
                        padding: "8px 12px",
                        textAlign: h === "Rank" ? "center" : "right",
                        color: h.includes("★")
                          ? "var(--cyan)"
                          : "var(--text-lo)",
                        fontSize: 9,
                        letterSpacing: "0.08em",
                        fontWeight: 600,
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {models.map((m, i) => {
                  const color = MODEL_COLOR[m.model_name] ?? "var(--text-hi)";
                  return (
                    <tr
                      key={m.model_name}
                      style={{
                        borderBottom: "1px solid rgba(2,132,199,0.07)",
                        background:
                          i % 2 === 0 ? "transparent" : "rgba(0,212,255,0.015)",
                      }}
                    >
                      <td style={{ padding: "10px 12px", textAlign: "center" }}>
                        <span
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            justifyContent: "center",
                            width: 24,
                            height: 24,
                            borderRadius: 6,
                            background: `${RANK_COLOR[i] ?? "#6b7280"}20`,
                            border: `1px solid ${RANK_COLOR[i] ?? "#6b7280"}40`,
                            color: RANK_COLOR[i] ?? "#6b7280",
                            fontWeight: 700,
                            fontSize: 11,
                          }}
                        >
                          {m.rank}
                        </span>
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "left" }}>
                        <div
                          style={{
                            fontWeight: 700,
                            color,
                            letterSpacing: "0.02em",
                          }}
                        >
                          {m.display_name}
                        </div>
                        <div
                          style={{
                            fontSize: 9,
                            color: "var(--text-lo)",
                            marginTop: 1,
                          }}
                        >
                          {m.split_mode}
                        </div>
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "right",
                          color: "var(--text-mid)",
                        }}
                      >
                        {pct(m.accuracy)}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "right",
                          color: "var(--text-mid)",
                        }}
                      >
                        {pct(m.f1_score)}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "right",
                          fontWeight: 700,
                          color,
                        }}
                      >
                        {pct(m.macro_f1)}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "right",
                          fontWeight: 700,
                          color,
                        }}
                      >
                        {pct(m.attack_detection_rate)}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "right",
                          color:
                            m.false_positive_rate > 0.1 ? "#dc2626" : "#059669",
                        }}
                      >
                        {pct4(m.false_positive_rate)}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "right",
                          color: "var(--text-mid)",
                        }}
                      >
                        {pct4(m.false_negative_rate)}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "right",
                          color: "var(--text-mid)",
                        }}
                      >
                        {m.roc_auc != null ? m.roc_auc.toFixed(4) : "—"}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "right",
                          color: "var(--text-mid)",
                        }}
                      >
                        {pct(m.balanced_accuracy)}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "right",
                          color: "var(--text-lo)",
                        }}
                      >
                        {secs(m.train_time_s)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <div
              style={{
                marginTop: 10,
                fontFamily: "var(--font-mono)",
                fontSize: 9,
                color: "var(--text-lo)",
                textAlign: "right",
              }}
            >
              ★ Primary publication metrics &nbsp;|&nbsp; ADR = Attack Detection
              Rate &nbsp;|&nbsp; FPR = False Positive Rate &nbsp;|&nbsp; FNR =
              False Negative Rate
            </div>
          </div>
        ) : activeTab === "charts" ? (
          /* ── Charts view ── */
          <div className="grid grid-cols-2 gap-5">
            {[
              {
                key: "macro_f1",
                label: "Macro-F1 ★",
                note: "Primary metric — higher is better",
              },
              {
                key: "adr",
                label: "Attack Detection Rate ★",
                note: "Mean recall over attack classes",
              },
              {
                key: "accuracy",
                label: "Accuracy",
                note: "Inflated by BENIGN class — use with caution",
              },
              {
                key: "fpr",
                label: "False Positive Rate",
                note: "Lower is better",
              },
            ].map((chart) => (
              <div key={chart.key}>
                <div
                  style={{
                    fontFamily: "var(--font-ui)",
                    fontSize: 12,
                    fontWeight: 600,
                    color: "var(--text-hi)",
                    marginBottom: 2,
                  }}
                >
                  {chart.label}
                </div>
                <div
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 9,
                    color: "var(--text-lo)",
                    marginBottom: 10,
                  }}
                >
                  {chart.note}
                </div>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart
                    data={barData}
                    margin={{ top: 4, right: 12, left: -20, bottom: 0 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="rgba(2,132,199,0.08)"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="name"
                      tick={{
                        fontSize: 10,
                        fill: "var(--text-lo)",
                        fontFamily: "var(--font-mono)",
                      }}
                    />
                    <YAxis
                      domain={chart.key === "fpr" ? [0, 0.35] : [0, 1]}
                      tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                      tick={{
                        fontSize: 9,
                        fill: "var(--text-lo)",
                        fontFamily: "var(--font-mono)",
                      }}
                    />
                    <Tooltip content={<ChartTooltip isPercent />} />
                    <Bar
                      dataKey={chart.key}
                      radius={[4, 4, 0, 0]}
                      maxBarSize={48}
                    >
                      {barData.map((entry) => (
                        <Cell
                          key={entry.key}
                          fill={MODEL_COLOR[entry.key] ?? "var(--cyan)"}
                          fillOpacity={0.85}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ))}
          </div>
        ) : (
          /* ── Radar view ── */
          <div style={{ display: "flex", justifyContent: "center" }}>
            <ResponsiveContainer width="100%" height={340}>
              <RadarChart
                data={radarData}
                margin={{ top: 10, right: 40, bottom: 10, left: 40 }}
              >
                <PolarGrid stroke="rgba(2,132,199,0.15)" />
                <PolarAngleAxis
                  dataKey="metric"
                  tick={{
                    fontSize: 11,
                    fill: "var(--text-mid)",
                    fontFamily: "var(--font-mono)",
                  }}
                />
                <PolarRadiusAxis
                  angle={90}
                  domain={[0, 1]}
                  tick={{ fontSize: 9, fill: "var(--text-lo)" }}
                  tickCount={4}
                />
                {models.map((m) => (
                  <Radar
                    key={m.model_name}
                    name={MODEL_SHORT[m.model_name] ?? m.display_name}
                    dataKey={MODEL_SHORT[m.model_name] ?? m.display_name}
                    stroke={MODEL_COLOR[m.model_name] ?? "var(--cyan)"}
                    fill={MODEL_COLOR[m.model_name] ?? "var(--cyan)"}
                    fillOpacity={0.08}
                    strokeWidth={1.8}
                  />
                ))}
                <Legend
                  wrapperStyle={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 11,
                  }}
                />
                <Tooltip
                  contentStyle={{
                    background: "#f8fafc",
                    border: "1px solid var(--border-mid)",
                    borderRadius: 8,
                    fontSize: 11,
                  }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>

      {/* ── Confusion Matrix Viewer ──────────────────────────────────── */}
      <Card className="mb-5">
        <SectionTitle
          title="CONFUSION MATRIX VIEWER"
          sub="// PER-MODEL CLASSIFICATION PERFORMANCE"
          icon={
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--cyan)"
              strokeWidth="1.8"
            >
              <rect x="3" y="3" width="7" height="7" />
              <rect x="14" y="3" width="7" height="7" />
              <rect x="14" y="14" width="7" height="7" />
              <rect x="3" y="14" width="7" height="7" />
            </svg>
          }
        />
        {/* Model tab selector */}
        <div className="flex gap-2 mb-4 flex-wrap">
          {(cmAvail.length > 0
            ? cmAvail
            : ["xgboost", "random_forest", "decision_tree", "naive_bayes"]
          ).map((m) => {
            const avail = cmAvail.includes(m);
            return (
              <button
                key={m}
                onClick={() => avail && setActiveModel(m)}
                disabled={!avail}
                style={{
                  padding: "7px 16px",
                  borderRadius: 7,
                  cursor: avail ? "pointer" : "not-allowed",
                  fontFamily: "var(--font-mono)",
                  fontSize: 10,
                  fontWeight: 600,
                  background:
                    activeModel === m
                      ? `${MODEL_COLOR[m] ?? "var(--cyan)"}18`
                      : "transparent",
                  border:
                    activeModel === m
                      ? `1px solid ${MODEL_COLOR[m] ?? "var(--cyan)"}50`
                      : "1px solid var(--border-dim)",
                  color:
                    activeModel === m
                      ? MODEL_COLOR[m] ?? "var(--cyan)"
                      : avail
                      ? "var(--text-mid)"
                      : "var(--text-lo)",
                  opacity: avail ? 1 : 0.4,
                  transition: "all 0.15s",
                }}
              >
                {MODEL_SHORT[m] ?? m}
                {!avail && (
                  <span style={{ fontSize: 8, marginLeft: 4 }}>(missing)</span>
                )}
              </button>
            );
          })}
        </div>

        {cmImages[activeModel] === undefined ? (
          <div
            style={{
              textAlign: "center",
              padding: 24,
              color: "var(--text-lo)",
              fontFamily: "var(--font-mono)",
              fontSize: 11,
            }}
          >
            Loading…
          </div>
        ) : cmImages[activeModel] === null ? (
          <EmptyState
            message={`confusion_matrix_${activeModel}.png not found.`}
          />
        ) : (
          <div style={{ textAlign: "center" }}>
            <img
              src={`data:image/png;base64,${cmImages[activeModel]}`}
              alt={`Confusion matrix for ${
                MODEL_SHORT[activeModel] ?? activeModel
              }`}
              style={{
                maxWidth: "100%",
                borderRadius: 8,
                border: "1px solid #000000",
              }}
            />
            <div
              style={{
                marginTop: 8,
                fontFamily: "var(--font-mono)",
                fontSize: 9,
                color: "var(--text-lo)",
              }}
            >
              {MODEL_SHORT[activeModel] ?? activeModel} — Confusion Matrix ·
              CICIoT2023 Train/Val/Test · 34 Classes
            </div>
          </div>
        )}
      </Card>

      {/* ── Per-Class Metrics ────────────────────────────────────────── */}
      <Card className="mb-5">
        <SectionTitle
          title="PER-CLASS DETECTION METRICS"
          sub="// PRECISION · RECALL · F1 PER ATTACK CLASS"
          icon={
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--cyan)"
              strokeWidth="1.8"
            >
              <path d="M9 11l3 3L22 4 M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
            </svg>
          }
        />

        {/* Model selector */}
        <div className="flex gap-2 mb-4 flex-wrap">
          {(perClass?.model_list ?? []).map((m) => (
            <button
              key={m}
              onClick={() => setPcModel(m)}
              style={{
                padding: "6px 14px",
                borderRadius: 6,
                cursor: "pointer",
                fontFamily: "var(--font-mono)",
                fontSize: 10,
                background:
                  pcModel === m
                    ? `${MODEL_COLOR[m] ?? "var(--cyan)"}18`
                    : "transparent",
                border:
                  pcModel === m
                    ? `1px solid ${MODEL_COLOR[m] ?? "var(--cyan)"}50`
                    : "1px solid var(--border-dim)",
                color:
                  pcModel === m
                    ? MODEL_COLOR[m] ?? "var(--cyan)"
                    : "var(--text-lo)",
                transition: "all 0.15s",
              }}
            >
              {MODEL_SHORT[m] ?? m}
            </button>
          ))}
        </div>

        {/* Summary row */}
        {pcSummary && (
          <div className="grid grid-cols-3 gap-3 mb-4">
            <div
              style={{
                padding: "8px 12px",
                borderRadius: 8,
                background: "rgba(5,150,105,0.07)",
                border: "1px solid rgba(0,255,157,0.15)",
              }}
            >
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 8,
                  color: "var(--text-lo)",
                  marginBottom: 4,
                }}
              >
                BEST ATTACK CLASS
              </div>
              <div
                style={{
                  color: "#059669",
                  fontWeight: 700,
                  fontSize: 12,
                  fontFamily: "var(--font-mono)",
                }}
              >
                {pcSummary.best_class}
              </div>
              <div
                style={{
                  color: "var(--text-lo)",
                  fontSize: 10,
                  fontFamily: "var(--font-mono)",
                  marginTop: 2,
                }}
              >
                F1 = {pct(pcSummary.best_f1)}
              </div>
            </div>
            <div
              style={{
                padding: "8px 12px",
                borderRadius: 8,
                background: "rgba(220,38,38,0.07)",
                border: "1px solid rgba(220,38,38,0.18)",
              }}
            >
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 8,
                  color: "var(--text-lo)",
                  marginBottom: 4,
                }}
              >
                WEAKEST ATTACK CLASS
              </div>
              <div
                style={{
                  color: "#dc2626",
                  fontWeight: 700,
                  fontSize: 12,
                  fontFamily: "var(--font-mono)",
                }}
              >
                {pcSummary.worst_class}
              </div>
              <div
                style={{
                  color: "var(--text-lo)",
                  fontSize: 10,
                  fontFamily: "var(--font-mono)",
                  marginTop: 2,
                }}
              >
                F1 = {pct(pcSummary.worst_f1)}
              </div>
            </div>
            <div
              style={{
                padding: "8px 12px",
                borderRadius: 8,
                background: "rgba(2,132,199,0.07)",
                border: "1px solid rgba(2,132,199,0.18)",
              }}
            >
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 8,
                  color: "var(--text-lo)",
                  marginBottom: 4,
                }}
              >
                ATTACK DETECTION RATE
              </div>
              <div
                style={{
                  color: "var(--cyan)",
                  fontWeight: 700,
                  fontSize: 16,
                  fontFamily: "var(--font-display)",
                }}
              >
                {pct(pcSummary.adr)}
              </div>
              <div
                style={{
                  color: "var(--text-lo)",
                  fontSize: 9,
                  fontFamily: "var(--font-mono)",
                  marginTop: 2,
                }}
              >
                Mean recall over attack classes
              </div>
            </div>
          </div>
        )}

        {pcRows.length === 0 ? (
          <EmptyState message="per_class_metrics.csv not found." />
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontFamily: "var(--font-mono)",
                fontSize: 11,
              }}
            >
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-mid)" }}>
                  {[
                    "Attack Class",
                    "Precision",
                    "Recall",
                    "F1-Score",
                    "Support",
                    "Perf.",
                  ].map((h) => (
                    <th
                      key={h}
                      style={{
                        padding: "8px 12px",
                        textAlign: h === "Attack Class" ? "left" : "right",
                        color: "var(--text-lo)",
                        fontSize: 9,
                        letterSpacing: "0.08em",
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pcRows.map((r, i) => {
                  const isWeak =
                    r.f1 < 0.6 && r.class.toUpperCase() !== "BENIGN";
                  const isBest =
                    r.f1 >= 0.95 && r.class.toUpperCase() !== "BENIGN";
                  const isBenign = r.class.toUpperCase() === "BENIGN";
                  return (
                    <tr
                      key={r.class + i}
                      style={{
                        borderBottom: "1px solid rgba(2,132,199,0.06)",
                        background: isWeak
                          ? "rgba(220,38,38,0.05)"
                          : isBest
                          ? "rgba(5,150,105,0.05)"
                          : i % 2 === 0
                          ? "transparent"
                          : "rgba(0,212,255,0.015)",
                      }}
                    >
                      <td
                        style={{
                          padding: "9px 12px",
                          color: isBenign ? "var(--text-lo)" : "var(--text-hi)",
                          fontWeight: isBenign ? 400 : 600,
                        }}
                      >
                        {r.class}
                      </td>
                      <td
                        style={{
                          padding: "9px 12px",
                          textAlign: "right",
                          color: "var(--text-mid)",
                        }}
                      >
                        {pct(r.precision)}
                      </td>
                      <td
                        style={{
                          padding: "9px 12px",
                          textAlign: "right",
                          color: r.recall < 0.5 ? "#dc2626" : "var(--text-mid)",
                        }}
                      >
                        {pct(r.recall)}
                      </td>
                      <td
                        style={{
                          padding: "9px 12px",
                          textAlign: "right",
                          fontWeight: 700,
                          color:
                            r.f1 >= 0.9
                              ? "#059669"
                              : r.f1 >= 0.6
                              ? "var(--cyan)"
                              : "#dc2626",
                        }}
                      >
                        {pct(r.f1)}
                      </td>
                      <td
                        style={{
                          padding: "9px 12px",
                          textAlign: "right",
                          color: "var(--text-lo)",
                        }}
                      >
                        {r.support.toLocaleString()}
                      </td>
                      <td style={{ padding: "9px 12px", textAlign: "right" }}>
                        {isWeak ? (
                          <Badge color="#dc2626">Weak</Badge>
                        ) : isBest ? (
                          <Badge color="#059669">Strong</Badge>
                        ) : isBenign ? (
                          <Badge color="var(--text-lo)">Ref</Badge>
                        ) : (
                          <Badge color="var(--cyan)">OK</Badge>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* ── Latency Report ───────────────────────────────────────────── */}
      <Card className="mb-5">
        <SectionTitle
          title="LATENCY & TRAINING TIME REPORT"
          sub="// INFERENCE SUITABILITY ANALYSIS"
          icon={
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--cyan)"
              strokeWidth="1.8"
            >
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
          }
        />

        {latency?.note && (
          <div
            style={{
              marginBottom: 14,
              padding: "8px 12px",
              borderRadius: 6,
              background: "rgba(2,132,199,0.06)",
              border: "1px solid rgba(2,132,199,0.15)",
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              color: "var(--text-mid)",
            }}
          >
            {latency.note}
          </div>
        )}

        {!latency || latency.latency.length === 0 ? (
          <EmptyState message="latency_report.csv not found." />
        ) : (
          <>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontFamily: "var(--font-mono)",
                fontSize: 11,
                marginBottom: 16,
              }}
            >
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-mid)" }}>
                  {[
                    "Model",
                    "Training Time",
                    "Batch Pred. Time",
                    "Est. Per-Sample (μs)",
                    "Real-time",
                    "Inference Use",
                  ].map((h) => (
                    <th
                      key={h}
                      style={{
                        padding: "8px 12px",
                        textAlign: h === "Model" ? "left" : "right",
                        color: "var(--text-lo)",
                        fontSize: 9,
                        letterSpacing: "0.08em",
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {latency.latency.map((row, i) => {
                  const color = MODEL_COLOR[row.model] ?? "var(--text-mid)";
                  return (
                    <tr
                      key={row.model}
                      style={{
                        borderBottom: "1px solid rgba(2,132,199,0.06)",
                        background:
                          i % 2 === 0 ? "transparent" : "rgba(0,212,255,0.015)",
                      }}
                    >
                      <td
                        style={{ padding: "10px 12px", fontWeight: 700, color }}
                      >
                        {row.display_name}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "right",
                          color: "var(--text-mid)",
                        }}
                      >
                        {secs(row.train_time_s)}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "right",
                          color: "var(--text-mid)",
                        }}
                      >
                        {row.pred_time_ms != null
                          ? `${row.pred_time_ms.toFixed(1)} ms`
                          : "—"}
                      </td>
                      <td
                        style={{
                          padding: "10px 12px",
                          textAlign: "right",
                          color: "var(--text-mid)",
                        }}
                      >
                        {row.per_sample_us != null
                          ? `${row.per_sample_us} μs`
                          : "—"}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right" }}>
                        {row.train_time_s < 60 ? (
                          <Badge color="#059669">Fast</Badge>
                        ) : row.train_time_s < 300 ? (
                          <Badge color="#d97706">Moderate</Badge>
                        ) : (
                          <Badge color="#dc2626">Slow</Badge>
                        )}
                      </td>
                      <td style={{ padding: "10px 12px", textAlign: "right" }}>
                        {row.model === "random_forest_research" ||
                        row.model === "xgboost_research" ? (
                          <Badge color="#059669">Real-time capable</Badge>
                        ) : (
                          <Badge color="#d97706">Batch / offline</Badge>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* Mini bar chart */}
            <div>
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 9,
                  color: "var(--text-lo)",
                  marginBottom: 8,
                  letterSpacing: "0.1em",
                }}
              >
                TRAINING TIME (SECONDS)
              </div>
              <ResponsiveContainer width="100%" height={110}>
                <BarChart
                  data={latency.latency.map((r) => ({
                    name: MODEL_SHORT[r.model] ?? r.model,
                    model: r.model,
                    train: r.train_time_s,
                  }))}
                  margin={{ top: 4, right: 8, left: -20, bottom: 0 }}
                  layout="vertical"
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(2,132,199,0.08)"
                    horizontal={false}
                  />
                  <XAxis
                    type="number"
                    tick={{
                      fontSize: 9,
                      fill: "var(--text-lo)",
                      fontFamily: "var(--font-mono)",
                    }}
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    width={100}
                    tick={{
                      fontSize: 10,
                      fill: "var(--text-lo)",
                      fontFamily: "var(--font-mono)",
                    }}
                  />
                  <Tooltip
                    formatter={(v) => [
                      `${Number(v).toFixed(1)}s`,
                      "Train time",
                    ]}
                    contentStyle={{
                      background: "#f8fafc",
                      border: "1px solid var(--border-mid)",
                      borderRadius: 6,
                      fontSize: 11,
                    }}
                  />
                  <Bar dataKey="train" radius={[0, 4, 4, 0]} maxBarSize={22}>
                    {latency.latency.map((r) => (
                      <Cell
                        key={r.model}
                        fill={MODEL_COLOR[r.model] ?? "var(--cyan)"}
                        fillOpacity={0.8}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </Card>

      {/* ── Accuracy vs Macro-F1 Scatter ─────────────────────────────── */}
      {models.length > 0 && (
        <Card className="mb-5">
          <SectionTitle
            title="ACCURACY vs MACRO-F1 GAP"
            sub="// REVEALS CLASS-IMBALANCE EFFECT ON ACCURACY"
            icon={
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="var(--cyan)"
                strokeWidth="1.8"
              >
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            }
          />
          <div
            style={{
              marginBottom: 12,
              fontFamily: "var(--font-ui)",
              fontSize: 12,
              color: "var(--text-mid)",
              lineHeight: 1.6,
            }}
          >
            The gap between Accuracy and Macro-F1 reveals class-imbalance
            impact. A large gap indicates the model scores high on dominant
            classes (BENIGN) but underperforms on rare attack classes. Smaller
            gap = more balanced generalization.
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart
              data={barData}
              margin={{ top: 4, right: 12, left: -20, bottom: 0 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(2,132,199,0.08)"
                vertical={false}
              />
              <XAxis
                dataKey="name"
                tick={{
                  fontSize: 10,
                  fill: "var(--text-lo)",
                  fontFamily: "var(--font-mono)",
                }}
              />
              <YAxis
                domain={[0.6, 1]}
                tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                tick={{
                  fontSize: 9,
                  fill: "var(--text-lo)",
                  fontFamily: "var(--font-mono)",
                }}
              />
              <Tooltip content={<ChartTooltip isPercent />} />
              <Legend
                wrapperStyle={{ fontFamily: "var(--font-mono)", fontSize: 10 }}
              />
              <Bar
                dataKey="accuracy"
                name="Accuracy"
                fill="rgba(2,132,199,0.50)"
                radius={[4, 4, 0, 0]}
                maxBarSize={30}
              />
              <Bar
                dataKey="macro_f1"
                name="Macro-F1"
                fill="rgba(0,255,157,0.7)"
                radius={[4, 4, 0, 0]}
                maxBarSize={30}
              />
            </BarChart>
          </ResponsiveContainer>
          <div
            style={{
              marginTop: 8,
              fontFamily: "var(--font-mono)",
              fontSize: 9,
              color: "var(--text-lo)",
              textAlign: "right",
            }}
          >
            Y-axis starts at 60% to highlight differences
          </div>
        </Card>
      )}

      {/* ── Evaluation Integrity ─────────────────────────────────────── */}
      <Card>
        <SectionTitle
          title="EVALUATION INTEGRITY NOTE"
          sub="// RESEARCH-GRADE PIPELINE DESCRIPTION"
          icon={
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--cyan)"
              strokeWidth="1.8"
            >
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          }
        />
        <div className="grid grid-cols-3 gap-4">
          {[
            {
              label: "Split Strategy",
              value:
                "Temporal (train on early traffic, test on later — prevents temporal leakage)",
              color: "var(--cyan)",
            },
            {
              label: "Deduplication",
              value:
                "Class-aware: BENIGN deduped; attack rows preserved (repetitive by nature)",
              color: "#059669",
            },
            {
              label: "BENIGN Sampling",
              value:
                "Undersampled to 2× attack count for honest per-class evaluation",
              color: "#059669",
            },
            {
              label: "Outlier Clipping",
              value:
                "1st/99th percentile clipping fit on train only — no test data leakage",
              color: "var(--cyan)",
            },
            {
              label: "Scaling",
              value:
                "StandardScaler fit on train only, applied to test without data leakage",
              color: "var(--cyan)",
            },
            {
              label: "Regularisation",
              value:
                "RF max_depth=15, XGBoost max_depth=7 + L1/L2 — prevents memorisation",
              color: "#d97706",
            },
          ].map((item) => (
            <div
              key={item.label}
              style={{
                padding: "12px 14px",
                borderRadius: 8,
                background: "rgba(2,132,199,0.05)",
                border: "1px solid rgba(2,132,199,0.12)",
              }}
            >
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 9,
                  color: "var(--text-lo)",
                  letterSpacing: "0.1em",
                  marginBottom: 5,
                }}
              >
                {item.label.toUpperCase()}
              </div>
              <div
                style={{
                  fontFamily: "var(--font-ui)",
                  fontSize: 11,
                  color: "var(--text-mid)",
                  lineHeight: 1.55,
                }}
              >
                {item.value}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
