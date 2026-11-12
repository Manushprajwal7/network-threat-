import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv('results.csv')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

policies = df['Policy'].values
x = np.arange(len(policies))

nets = df['Combined Net Benefit (OCU)'] / 1e6
ax1.bar(x, nets, color=['#455a64', '#1565c0'], alpha=0.9, width=0.4)
ax1.set_title('Held-Out Test Split Combined Net Benefit (Seed 99)', fontsize=11, fontweight='bold')
ax1.set_ylabel('Net Benefit (Million OCU)')
ax1.set_xticks(x)
ax1.set_xticklabels(policies)
ax1.set_ylim(0, 2.3)
ax1.grid(True, linestyle=':', alpha=0.6)
for i, v in enumerate(nets):
    ax1.text(i, v + 0.05, f"{v:.3f}M OCU", ha='center', fontweight='bold')

fprs = df['Held-Out Balanced Block FPR (%)']
ax2.bar(x, fprs, color=['#455a64', '#1565c0'], alpha=0.9, width=0.4)
ax2.set_title('Held-Out Balanced Stream Block FPR (%)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Block False Positive Rate (%)')
ax2.set_xticks(x)
ax2.set_xticklabels(policies)
ax2.set_ylim(0, 0.5)
ax2.grid(True, linestyle=':', alpha=0.6)
for i, v in enumerate(fprs):
    ax2.text(i, v + 0.02, f"{v:.2f}%", ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig('plot.png', dpi=300)
print('Saved E2 plot.png')
