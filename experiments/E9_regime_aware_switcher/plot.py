import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv('results.csv')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

controllers = ['Static P1', 'Static P2-tier', 'Static P2', 'Dynamic Switcher (E9)']
x = np.arange(len(controllers))

nets = df['Combined Net (OCU)'] / 1e6
colors = ['#455a64', '#1565c0', '#c62828', '#2e7d32']

ax1.bar(x, nets, color=colors, alpha=0.9)
ax1.set_title('Combined Net Operational Benefit across Controllers', fontsize=11, fontweight='bold')
ax1.set_ylabel('Net Benefit (Million OCU)')
ax1.set_xticks(x)
ax1.set_xticklabels(controllers, rotation=20, ha='right', fontsize=9)
ax1.set_ylim(0, 2.3)
ax1.grid(True, linestyle=':', alpha=0.6)

for i, v in enumerate(nets):
    ax1.text(i, v + 0.05, f"{v:.3f}M", ha='center', fontsize=9, fontweight='bold')

fprs = df['Bal Block FPR (%)']
ax2.bar(x, fprs, color=colors, alpha=0.9)
ax2.set_title('Balanced Stream Benign Block FPR (%)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Block False Positive Rate (%)')
ax2.set_xticks(x)
ax2.set_xticklabels(controllers, rotation=20, ha='right', fontsize=9)
ax2.set_ylim(0, 35)
ax2.grid(True, linestyle=':', alpha=0.6)

for i, v in enumerate(fprs):
    ax2.text(i, v + 0.8, f"{v:.1f}%", ha='center', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig('plot.png', dpi=300)
print('Saved E9 plot.png')
