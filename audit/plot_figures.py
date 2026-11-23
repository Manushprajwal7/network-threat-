"""
Regenerate Figures 11-14 with only the four valid supervised classifiers
(XGBoost, Random Forest, Decision Tree, Naive Bayes).

Logistic Regression, KNN, and SVM are excluded — their recomputed accuracies
fell below the majority-class baseline for this 34-class problem, indicating
a preprocessing incompatibility (see audit/discrepancy_report.txt).

Data source: audit/Table_15_corrected.csv (cross-checked against
audit/recomputed_metrics.csv — both contain the same values).

No original figure-generation script or prior Figure_11-14 image files were
found in this repository, so this script uses matplotlib defaults with
plt.rcParams['font.size'] = 11, per the fallback style rule.
"""

import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "Table_15_corrected.csv")
OUT_DIR = os.path.join(HERE, "figures")
os.makedirs(OUT_DIR, exist_ok=True)

MODELS = ["XGBoost", "Random Forest", "Decision Tree", "Naive Bayes"]

plt.rcParams["font.size"] = 11
plt.rcParams["figure.facecolor"] = "white"
plt.rcParams["axes.facecolor"] = "white"
plt.rcParams["savefig.facecolor"] = "white"

# Distinct, stable per-model colors (matplotlib tab10 palette).
COLORS = {
    "XGBoost": "#1f77b4",
    "Random Forest": "#2ca02c",
    "Decision Tree": "#ff7f0e",
    "Naive Bayes": "#d62728",
}


def load_metrics():
    rows = {}
    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows[row["Model"]] = row
    missing = [m for m in MODELS if m not in rows]
    if missing:
        raise SystemExit(
            f"STOP: required model rows missing from {CSV_PATH}: {missing}"
        )
    metrics = {}
    for m in MODELS:
        r = rows[m]
        metrics[m] = {
            "Accuracy (%)": float(r["Accuracy (%)"]),
            "Macro-F1 (%)": float(r["Macro-F1 (%)"]),
            "ADR (%)": float(r["ADR/Macro-Recall (%)"]),
            "FPR (%)": float(r["FPR (%)"]),
            "Weighted-F1 (%)": float(r["Weighted-F1 (%)"]),
        }
    return metrics


def bar_chart(models, values, ylabel, ylim, title, fname, decimals=1, rotate=30):
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = [COLORS[m] for m in models]
    bars = ax.bar(models, values, color=colors)
    ax.set_ylabel(ylabel)
    ax.set_ylim(*ylim)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(False)
    plt.setp(ax.get_xticklabels(), rotation=rotate, ha="right")

    for bar, val in zip(bars, values):
        ax.annotate(
            f"{val:.{decimals}f}",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    fig.tight_layout()
    png_path = os.path.join(OUT_DIR, f"{fname}.png")
    pdf_path = os.path.join(OUT_DIR, f"{fname}.pdf")
    fig.savefig(png_path, dpi=300)
    fig.savefig(pdf_path)
    plt.close(fig)
    return png_path, pdf_path


def radar_chart(models, metrics, fname):
    axes_labels = ["Accuracy", "Macro-F1", "ADR", "FPR"]
    num_axes = len(axes_labels)
    angles = np.linspace(0, 2 * np.pi, num_axes, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 5), subplot_kw=dict(polar=True))

    for m in models:
        acc = metrics[m]["Accuracy (%)"]
        f1 = metrics[m]["Macro-F1 (%)"]
        adr = metrics[m]["ADR (%)"]
        fpr_inv = 100.0 - metrics[m]["FPR (%)"]
        values = [acc, f1, adr, fpr_inv]
        values += values[:1]
        ax.plot(angles, values, label=m, color=COLORS[m], linewidth=1.8)
        ax.fill(angles, values, color=COLORS[m], alpha=0.08)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(axes_labels)
    ax.set_ylim(0, 100)
    ax.set_rlabel_position(0)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=9)

    fig.tight_layout()
    png_path = os.path.join(OUT_DIR, f"{fname}.png")
    pdf_path = os.path.join(OUT_DIR, f"{fname}.pdf")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)
    return png_path, pdf_path


def main():
    metrics = load_metrics()

    print("Verification")
    print("=============")
    print(f"Model order (all figures): {MODELS}")

    # Figure 11 - Macro-F1
    f1_vals = [metrics[m]["Macro-F1 (%)"] for m in MODELS]
    print("\nFigure 11 (Macro-F1 %):")
    for m, v in zip(MODELS, f1_vals):
        print(f"  {m}: {v:.1f}")
    fig11_png, fig11_pdf = bar_chart(
        MODELS, f1_vals, "Macro-F1 (%)", (0, 100), "Macro-F1 Comparison",
        "fig11_macro_f1", decimals=1,
    )

    # Figure 12 - ADR
    adr_vals = [metrics[m]["ADR (%)"] for m in MODELS]
    print("\nFigure 12 (ADR / Macro-Recall %):")
    for m, v in zip(MODELS, adr_vals):
        print(f"  {m}: {v:.1f}")
    fig12_png, fig12_pdf = bar_chart(
        MODELS, adr_vals, "ADR / Macro-Recall (%)", (0, 100),
        "Attack Detection Rate (ADR) Comparison", "fig12_adr", decimals=1,
    )

    # Figure 13 - FPR
    fpr_vals = [metrics[m]["FPR (%)"] for m in MODELS]
    print("\nFigure 13 (FPR %):")
    for m, v in zip(MODELS, fpr_vals):
        print(f"  {m}: {v:.2f}")
    fig13_png, fig13_pdf = bar_chart(
        MODELS, fpr_vals, "FPR (%)", (0, 5),
        "False Positive Rate Comparison", "fig13_fpr", decimals=2,
    )

    # Figure 14 - Radar
    print("\nFigure 14 (radar axes: Accuracy, Macro-F1, ADR, 100-FPR):")
    for m in MODELS:
        acc = metrics[m]["Accuracy (%)"]
        f1v = metrics[m]["Macro-F1 (%)"]
        adr = metrics[m]["ADR (%)"]
        fpr_inv = 100.0 - metrics[m]["FPR (%)"]
        print(f"  {m}: Accuracy={acc:.2f}, Macro-F1={f1v:.2f}, ADR={adr:.2f}, 100-FPR={fpr_inv:.2f}")
    fig14_png, fig14_pdf = radar_chart(MODELS, metrics, "fig14_radar")

    print("\nOutput file sizes:")
    for path in [fig11_png, fig11_pdf, fig12_png, fig12_pdf,
                 fig13_png, fig13_pdf, fig14_png, fig14_pdf]:
        size = os.path.getsize(path)
        print(f"  {os.path.relpath(path, HERE)}: {size} bytes")


if __name__ == "__main__":
    main()
