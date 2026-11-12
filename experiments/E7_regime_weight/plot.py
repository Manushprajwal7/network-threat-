import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('results.csv')
fig, ax = plt.subplots(figsize=(8, 4.5))

ax.plot(df['w_bal'], df['P2-tier Rank'], marker='o', linewidth=2.5, color='#1565c0', label='Recommended P2-tier Rank')
ax.plot(df['w_bal'], df['P1 Rank'], marker='s', linewidth=2, color='#455a64', label='Conservative P1 Rank')
ax.plot(df['w_bal'], df['P2 Rank'], marker='^', linewidth=2, linestyle='--', color='#c62828', label='Cost-Optimal P2 Rank')

ax.set_title('Policy Search Rank across Regime Mixture Weight w_bal in [0.0, 1.0]', fontsize=11, fontweight='bold')
ax.set_xlabel('Balanced Stream Mixture Weight w_bal')
ax.set_ylabel('Optimization Rank (1 = Best of 70)')
ax.set_ylim(0, 72)
ax.invert_yaxis()
ax.grid(True, linestyle=':', alpha=0.6)
ax.legend(loc='center right')

plt.tight_layout()
plt.savefig('plot.png', dpi=300)
print('Saved E7 plot.png')
