import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("experiments/E16_dynamic_switcher/results.csv")

plt.figure(figsize=(8, 4.5), dpi=300)
x = np.arange(len(df))
width = 0.35
plt.bar(x - width/2, df["Balanced NB"]/1e3, width, label="Balanced Benchmark (kOCU)", color="#0284c7")
plt.bar(x + width/2, df["Combined NB"]/1e3, width, label="Combined Net Benefit (kOCU)", color="#16a34a")
plt.xticks(x, [p.split("(")[0].strip() for p in df["Policy"]], fontsize=9.5, fontweight="bold")
plt.ylabel("Operational Benefit (kOCU)", fontsize=10.5, fontweight="bold")
plt.title("Comparative Performance: Static Policies vs. Dynamic Adaptive Switcher", fontsize=11.5, fontweight="bold", pad=12)
plt.legend(loc="upper left", fontsize=9)
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("experiments/E16_dynamic_switcher/plot.png", dpi=300)
plt.close()
print("Saved experiments/E16_dynamic_switcher/plot.png")
