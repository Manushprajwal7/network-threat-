import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('results.csv')
fig, ax = plt.subplots(figsize=(8, 5))

ax.plot(df['Lambda_Block'], df['P2-tier Comb Net (OCU)'] / 1e6, marker='o', linewidth=2, color='#1565c0', label='Recommended P2-tier')
ax.plot(df['Lambda_Block'], df['P1 Comb Net (OCU)'] / 1e6, marker='s', linewidth=2, color='#455a64', label='Conservative Baseline P1')
ax.plot(df['Lambda_Block'], df['P2 Comb Net (OCU)'] / 1e6, marker='^', linewidth=2, linestyle='--', color='#c62828', label='Global Optimal P2')

ax.set_xscale('log')
ax.set_title('Policy Net Benefit Across False-Blocking Multiplier Lambda (0.2 to 20.0)', fontsize=11, fontweight='bold')
ax.set_xlabel('False-Blocking Penalty Multiplier Lambda (Log Scale, 10 to 1,000 OCU)')
ax.set_ylabel('Combined Net Operational Benefit (Million OCU)')
ax.grid(True, which='both', linestyle=':', alpha=0.6)
ax.legend(loc='lower left')

plt.tight_layout()
plt.savefig('plot.png', dpi=300)
print('Saved E6 plot.png')
