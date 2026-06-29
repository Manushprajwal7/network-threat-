"""
Generate class-wise Precision / Recall / F1 figures for the research paper,
STRICTLY from reports/per_class_metrics_ciciot2023.csv (no fabricated numbers).

Model: XGBoost (best Macro-F1, core of the live ensemble).

Writes (small, journal-sized, NO figure numbers in the image):
  <OUT_DIR>/Class-wise Precision.png
  <OUT_DIR>/Class-wise Recall.png
  <OUT_DIR>/Class-wise F1 Score.png
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "reports" / "per_class_metrics_ciciot2023.csv"
OUT_DIR = Path(r"C:\Users\Manus\OneDrive\Desktop\L-thirupathi\images")
MODEL = "xgboost"

BAR_COLOR = "#0284c7"
DPI = 300

plt.rcParams.update({
    "font.size": 7,
    "axes.titlesize": 10,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 6,
    "font.family": "serif",
})


def load_rows(model: str):
    rows = []
    with open(CSV_PATH, newline="") as f:
        for r in csv.DictReader(f):
            if r["model"] == model:
                rows.append({
                    "class": r["class"],
                    "precision": float(r["precision"]),
                    "recall": float(r["recall"]),
                    "f1": float(r["f1"]),
                })
    return rows


def plot_metric(rows, key, title, filename):
    data = sorted(rows, key=lambda r: r[key])  # ascending -> best on top
    classes = [r["class"] for r in data]
    vals = [r[key] for r in data]

    fig, ax = plt.subplots(figsize=(5.0, 6.2))
    y = range(len(classes))
    ax.barh(list(y), vals, color=BAR_COLOR, height=0.72)
    ax.set_yticks(list(y))
    ax.set_yticklabels(classes)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel(title.split(" ", 1)[1] if " " in title else title)
    ax.set_title(title)
    ax.grid(True, axis="x", linestyle="--", linewidth=0.4, alpha=0.5)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    # value labels
    for yi, v in zip(y, vals):
        ax.text(min(v + 0.01, 0.995), yi, f"{v:.2f}",
                va="center", ha="left", fontsize=5.5, color="#334155")

    fig.tight_layout(pad=0.4)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / filename
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"[ok] wrote {out}")


def main():
    rows = load_rows(MODEL)
    if not rows:
        print(f"[error] no rows for model '{MODEL}' in {CSV_PATH}")
        return
    plot_metric(rows, "precision", "Class-wise Precision", "Class-wise Precision.png")
    plot_metric(rows, "recall", "Class-wise Recall", "Class-wise Recall.png")
    plot_metric(rows, "f1", "Class-wise F1 Score", "Class-wise F1 Score.png")


if __name__ == "__main__":
    main()
