import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('results.csv')
bal_df = df[df['Stream'].str.contains('Balanced')].copy()

fig, ax = plt.subplots(figsize=(8, 4.5))

levels = bal_df['Level']
comp_floats = bal_df['Attack Pct'].str.rstrip('%').astype(float)

ax.plot(levels, comp_floats, marker='o', color='#1565c0', linewidth=2.5, markersize=8)

ax.set_title('Attack Density Escalation with Wilson 95% CIs (Balanced Stream)', fontsize=11, fontweight='bold')
ax.set_xlabel('Security Posture Level')
ax.set_ylabel('Empirical Attack Composition (%)')
ax.set_ylim(-5, 105)
ax.grid(True, linestyle=':', alpha=0.6)

for i in range(len(bal_df)):
    txt = bal_df['Attack Pct'].iloc[i]
    ci_txt = bal_df['Wilson 95% CI (Paper Format)'].iloc[i]
    ax.annotate(f"{txt}\n{ci_txt}", (levels.iloc[i], comp_floats.iloc[i] + 4), ha='center', fontsize=8, fontweight='bold')

plt.tight_layout()
plt.savefig('plot.png', dpi=300)
print('Saved E11 plot.png')
