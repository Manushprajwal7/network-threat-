import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('results.csv')
fig, ax = plt.subplots(figsize=(8, 5))

ax.scatter(df['bal_total_disruptive_fpr'], df['comb_net_benefit'] / 1e6,
           c='#546e7a', alpha=0.6, edgecolors='none', s=45, label='All 70 Monotonic Policies')

p1 = df[df['mapping'] == 'Allo-Aler-Rest-Quar-Quar-Bloc'].iloc[0]
p2_tier = df[df['mapping'] == 'Allo-Aler-Rest-Quar-Bloc-Bloc'].iloc[0]
p2 = df[df['mapping'] == 'Allo-Rest-Quar-Bloc-Bloc-Bloc'].iloc[0]

ax.scatter(p1['bal_total_disruptive_fpr'], p1['comb_net_benefit'] / 1e6, color='#2e7d32', s=120, zorder=5, label='P1: Safe Baseline (Rank 44)')
ax.scatter(p2_tier['bal_total_disruptive_fpr'], p2_tier['comb_net_benefit'] / 1e6, color='#1565c0', s=140, marker='^', zorder=5, label='P2-tier: Recommended (Rank 9)')
ax.scatter(p2['bal_total_disruptive_fpr'], p2['comb_net_benefit'] / 1e6, color='#c62828', s=120, marker='s', zorder=5, label='P2: Aggressive (Rank 28)')

ax.set_title('Policy Optimization Trade-off: Combined Net Benefit vs Disruptive FPR', fontsize=11, fontweight='bold')
ax.set_xlabel('Balanced Stream Disruptive False Positive Rate (%) [Quarantine + Block]')
ax.set_ylabel('Combined Net Operational Benefit (Million OCU)')
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(loc='lower right')

plt.tight_layout()
plt.savefig('plot.png', dpi=300)
print('Saved E3 plot.png')
