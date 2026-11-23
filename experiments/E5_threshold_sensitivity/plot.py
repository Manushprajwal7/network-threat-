import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('results.csv')
fig, ax = plt.subplots(figsize=(8, 4.5))

x = range(len(df))
ax.bar(x, df['P2-tier Comb Net (OCU)'] / 1e6, color='#3949ab', alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels([f"{r['Parameter Swept']}\n={r['Value']}" for _, r in df.iterrows()], rotation=30, ha='right', fontsize=9)
ax.set_title('P2-tier Combined Net Benefit under Threshold Variations', fontsize=11, fontweight='bold')
ax.set_ylabel('Combined Net Benefit (Million OCU)')
ax.set_ylim(1.80, 1.95)
ax.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
plt.savefig('plot.png', dpi=300)
print('Saved E5 plot.png')
