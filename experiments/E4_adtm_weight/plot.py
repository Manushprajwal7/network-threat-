import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('results.csv')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

ax1.barh(df['Configuration'], df['P2-tier Comb Net (OCU)'] / 1e6, color='#00838f', alpha=0.85)
ax1.set_title('P2-tier Combined Net Benefit across Allocations', fontsize=11, fontweight='bold')
ax1.set_xlabel('Net Operational Benefit (Million OCU)')
ax1.set_xlim(1.85, 1.95)
ax1.grid(True, linestyle=':', alpha=0.6)

ax2.plot(df['Trust AUC'], df['Configuration'], marker='o', color='#c2185b', linewidth=2, markersize=7)
ax2.set_title('ADTM Dynamic Trust ROC AUC', fontsize=11, fontweight='bold')
ax2.set_xlabel('ROC AUC')
ax2.set_xlim(0.998, 1.000)
ax2.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
plt.savefig('plot.png', dpi=300)
print('Saved E4 plot.png')
