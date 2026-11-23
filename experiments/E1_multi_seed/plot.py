import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('results.csv')
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(14, 4))

ax1.bar(df['seed'].astype(str), df['if_auc'], color='#2b5c8f', alpha=0.85)
ax1.axhline(df['if_auc'].mean(), color='red', linestyle='--', label=f"Mean: {df['if_auc'].mean():.4f}")
ax1.set_title('Clean IF Anomaly AUC across Seeds', fontsize=11, fontweight='bold')
ax1.set_xlabel('Random Seed')
ax1.set_ylabel('ROC AUC')
ax1.set_ylim(0.90, 0.96)
ax1.legend(loc='lower right')
ax1.grid(True, linestyle=':', alpha=0.6)

ax2.bar(df['seed'].astype(str), df['trust_auc'], color='#2e7d32', alpha=0.85)
ax2.axhline(df['trust_auc'].mean(), color='red', linestyle='--', label=f"Mean: {df['trust_auc'].mean():.4f}")
ax2.set_title('ADTM Dynamic Trust AUC across Seeds', fontsize=11, fontweight='bold')
ax2.set_xlabel('Random Seed')
ax2.set_ylabel('ROC AUC')
ax2.set_ylim(0.995, 1.000)
ax2.legend(loc='lower right')
ax2.grid(True, linestyle=':', alpha=0.6)

ax3.bar(df['seed'].astype(str), df['p2_tier_comb_net'] / 1e6, color='#d32f2f', alpha=0.85)
ax3.axhline(df['p2_tier_comb_net'].mean() / 1e6, color='black', linestyle='--', label=f"Mean: {df['p2_tier_comb_net'].mean()/1e6:.3f}M")
ax3.set_title('P2-tier Combined Net Benefit (M OCU)', fontsize=11, fontweight='bold')
ax3.set_xlabel('Random Seed')
ax3.set_ylabel('Net Benefit (Million OCU)')
ax3.set_ylim(1.85, 1.95)
ax3.legend(loc='lower right')
ax3.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
plt.savefig('plot.png', dpi=300)
print('Saved E1 plot.png')
