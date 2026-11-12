import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

actions = ["Allow", "Alert", "Restrict", "Quarantine", "Block"]
labels = ["True Benign", "True Attack"]

# Cost matrix: shape (5, 2)
# row: action, col: label
mat = np.array([
    [0, 100],
    [1, -5],
    [3, -10],
    [15, -20],
    [50, -50],
])

fig, ax = plt.subplots(figsize=(6, 5))
cax = ax.imshow(mat, cmap="coolwarm_r", aspect="auto", vmin=-50, vmax=100)

for i in range(len(actions)):
    for j in range(len(labels)):
        val = mat[i, j]
        color = "white" if abs(val) > 40 else "black"
        sign = "+" if val > 0 else ""
        ax.text(j, i, f"{sign}{val}", ha="center", va="center", color=color, fontweight="bold", fontsize=14)

ax.set_xticks(np.arange(len(labels)))
ax.set_yticks(np.arange(len(actions)))
ax.set_xticklabels(labels, fontweight="bold", fontsize=11)
ax.set_yticklabels(actions, fontweight="bold", fontsize=11)
plt.title("Unitless Operational Enforcement Cost Matrix", fontsize=12, fontweight="bold", pad=15)
cbar = plt.colorbar(cax)
cbar.set_label("Operational Cost (Negative = Containment Benefit)", fontsize=10, fontweight="bold")
plt.tight_layout()
plt.savefig("paper2/figures/O3_cost_matrix_heatmap.png", dpi=300)
plt.close()
print("Saved paper2/figures/O3_cost_matrix_heatmap.png")
