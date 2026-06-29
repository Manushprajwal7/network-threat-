"""
Generate CNN/LSTM learning-curve figures for the research paper STRICTLY from
the real per-epoch training history produced by train_deep_curves.py.

Reads:
  reports/training_history_cnn_research.json
  reports/training_history_lstm_research.json

Writes (small, journal-sized, NO figure numbers in the image):
  <OUT_DIR>/CNN Accuracy Curve.png
  <OUT_DIR>/CNN Loss Curve.png
  <OUT_DIR>/LSTM Accuracy Curve.png
  <OUT_DIR>/LSTM Loss Curve.png

No data is fabricated. If a history file is missing, that figure is skipped
with a clear message.
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).parent
REPORTS_DIR = BASE_DIR / "reports"
OUT_DIR = Path(r"C:\Users\Manus\OneDrive\Desktop\L-thirupathi\images")

# Journal-friendly: small physical size + high DPI for crisp print.
FIGSIZE = (4.2, 3.0)   # inches
DPI = 300

TRAIN_COLOR = "#0284c7"
VAL_COLOR = "#d97706"

plt.rcParams.update({
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "legend.fontsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "font.family": "serif",
})


def load_history(model_key: str):
    path = REPORTS_DIR / f"training_history_{model_key}.json"
    if not path.exists():
        print(f"[skip] {path} not found — run train_deep_curves.py first.")
        return None
    with open(path) as f:
        return json.load(f)["history"]


def plot_curve(hist, train_key, val_key, ylabel, title, filename):
    if hist is None or train_key not in hist:
        print(f"[skip] '{train_key}' missing — cannot make {filename}")
        return
    train = hist[train_key]
    val = hist.get(val_key)
    epochs = list(range(1, len(train) + 1))

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(epochs, train, color=TRAIN_COLOR, marker="o", markersize=3,
            linewidth=1.6, label="Training")
    if val:
        ax.plot(epochs, val, color=VAL_COLOR, marker="s", markersize=3,
                linewidth=1.6, label="Validation")
    ax.set_xlabel("Epoch")
    ax.set_ylabel(ylabel)
    ax.set_title(title)          # descriptive name only — NO figure number
    ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)
    ax.legend(frameon=False)
    fig.tight_layout(pad=0.4)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / filename
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"[ok] wrote {out}")


def main():
    cnn = load_history("cnn_research")
    lstm = load_history("lstm_research")

    plot_curve(cnn, "accuracy", "val_accuracy", "Accuracy",
               "CNN Accuracy Curve", "CNN Accuracy Curve.png")
    plot_curve(cnn, "loss", "val_loss", "Loss",
               "CNN Loss Curve", "CNN Loss Curve.png")
    plot_curve(lstm, "accuracy", "val_accuracy", "Accuracy",
               "LSTM Accuracy Curve", "LSTM Accuracy Curve.png")
    plot_curve(lstm, "loss", "val_loss", "Loss",
               "LSTM Loss Curve", "LSTM Loss Curve.png")


if __name__ == "__main__":
    main()
