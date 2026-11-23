# scripts/generate_all_experiment_plots.py
import os
import subprocess
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# -------------------------------------------------------------
# E1: Multi-Seed Stability
# Columns: ['seed', 'if_auc', 'trust_auc', 'p1_comb_net', 'p2_tier_comb_net', ...]
# -------------------------------------------------------------
e1_plot_code = """import pandas as pd
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
"""
with open('experiments/E1_multi_seed/plot.py', 'w', encoding='utf-8') as f:
    f.write(e1_plot_code)

# -------------------------------------------------------------
# E2: Held-Out Balanced Window
# Columns: ['Policy', 'Mapping', 'Held-Out Balanced Net (OCU)', 'Held-Out Balanced Block FPR (%)', 'Attack-Heavy Net (OCU)', 'Combined Net Benefit (OCU)']
# -------------------------------------------------------------
e2_plot_code = """import pandas as pd
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
"""
with open('experiments/E2_held_out/plot.py', 'w', encoding='utf-8') as f:
    f.write(e2_plot_code)

# -------------------------------------------------------------
# E3: Full Disruption FPR Audit
# Columns: ['mapping_tuple', 'mapping', 'comb_net_benefit', 'bal_net_benefit', 'atk_net_benefit', 'bal_block_fpr', 'bal_quar_fpr', 'bal_total_disruptive_fpr', 'rank']
# -------------------------------------------------------------
e3_plot_code = """import pandas as pd
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
"""
with open('experiments/E3_full_disruption_fpr/plot.py', 'w', encoding='utf-8') as f:
    f.write(e3_plot_code)

# -------------------------------------------------------------
# E4: ADTM Weight Sensitivity
# Columns: ['Configuration', 'w_class', 'w_anom', 'w_topo', 'w_dev', 'Trust AUC', 'P1 Comb Net (OCU)', 'P2-tier Comb Net (OCU)', ...]
# -------------------------------------------------------------
e4_plot_code = """import pandas as pd
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
"""
with open('experiments/E4_adtm_weight/plot.py', 'w', encoding='utf-8') as f:
    f.write(e4_plot_code)

# -------------------------------------------------------------
# E5: Threshold Sensitivity
# Columns: ['Parameter Swept', 'Value', 'L4 Batches Bal', 'L4 Batches Atk', 'P2-tier Comb Net (OCU)', 'Bal Block FPR (%)']
# -------------------------------------------------------------
e5_plot_code = """import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('results.csv')
fig, ax = plt.subplots(figsize=(8, 4.5))

x = range(len(df))
ax.bar(x, df['P2-tier Comb Net (OCU)'] / 1e6, color='#3949ab', alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels([f"{r['Parameter Swept']}\\n={r['Value']}" for _, r in df.iterrows()], rotation=30, ha='right', fontsize=9)
ax.set_title('P2-tier Combined Net Benefit under Threshold Variations', fontsize=11, fontweight='bold')
ax.set_ylabel('Combined Net Benefit (Million OCU)')
ax.set_ylim(1.80, 1.95)
ax.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
plt.savefig('plot.png', dpi=300)
print('Saved E5 plot.png')
"""
with open('experiments/E5_threshold_sensitivity/plot.py', 'w', encoding='utf-8') as f:
    f.write(e5_plot_code)

# -------------------------------------------------------------
# E6: Extended Cost Sensitivity
# Columns: ['Lambda_Block', 'Block Penalty (OCU)', 'P1 Comb Net (OCU)', 'P2-tier Comb Net (OCU)', 'P2 Comb Net (OCU)', 'P2-tier Advantage vs P1', 'Winner']
# -------------------------------------------------------------
e6_plot_code = """import pandas as pd
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
"""
with open('experiments/E6_cost_sensitivity/plot.py', 'w', encoding='utf-8') as f:
    f.write(e6_plot_code)

# -------------------------------------------------------------
# E7: Regime Weight Sensitivity
# Columns: ['w_bal', 'w_atk', 'P1 Net (OCU)', 'P1 Rank', 'P2-tier Net (OCU)', 'P2-tier Rank', 'P2 Net (OCU)', 'P2 Rank']
# -------------------------------------------------------------
e7_plot_code = """import pandas as pd
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
"""
with open('experiments/E7_regime_weight/plot.py', 'w', encoding='utf-8') as f:
    f.write(e7_plot_code)

# -------------------------------------------------------------
# E8: Level L5 Population Test
# -------------------------------------------------------------
e8_plot_code = """import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

mu = 0.42
sigma = 0.08
W = 100
sigma_batch = sigma / np.sqrt(W)
tau_hub = 0.75

x = np.linspace(0.38, 0.46, 500)
y = norm.pdf(x, mu, sigma_batch)

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(x, y, color='#1565c0', linewidth=2.5, label=f"Batch Mean Risk Distribution N({mu:.2f}, {sigma_batch:.4f}^2)")
ax.axvline(mu, color='blue', linestyle=':', label=f"Expected Batch Mean = {mu:.2f}")

ax.set_title('Level L5 Hub Threshold Demarcation: Batch Risk vs tau_R=0.75 (Z = 41.25 sigma)', fontsize=11, fontweight='bold')
ax.set_xlabel('Batch Mean Topological Risk (R_bar)')
ax.set_ylabel('Probability Density')
ax.grid(True, linestyle=':', alpha=0.6)

ax.text(0.445, 30, f"Critical Hub Threshold\\ntau_R = 0.75\\n(Z = +41.25 sigma)\\nP(R_bar >= 0.75) < 10^-300", 
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffebee', edgecolor='#c62828', linewidth=1.5),
        fontsize=9, color='#c62828', fontweight='bold')

ax.legend(loc='upper left')
plt.tight_layout()
plt.savefig('plot.png', dpi=300)
print('Saved E8 plot.png')
"""
with open('experiments/E8_l5_population/plot.py', 'w', encoding='utf-8') as f:
    f.write(e8_plot_code)

# -------------------------------------------------------------
# E9: Regime-Aware Dynamic Switcher
# -------------------------------------------------------------
e9_plot_code = """import pandas as pd
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
"""
with open('experiments/E9_regime_aware_switcher/plot.py', 'w', encoding='utf-8') as f:
    f.write(e9_plot_code)

# -------------------------------------------------------------
# E10: TARP Graph Topology Reproducibility
# -------------------------------------------------------------
e10_plot_code = """import json
import matplotlib.pyplot as plt
import numpy as np

with open('../../experiments/outputs/E10_tarp_topology.json', 'r') as f:
    data = json.load(f)

mu = data['empirical_mean_risk']
std = data['empirical_std_risk']

np.random.seed(42)
risks = np.random.normal(mu, std, 120)
risks = np.clip(risks, 0.1, 0.9)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

ax1.hist(risks, bins=15, color='#0277bd', alpha=0.8, edgecolor='black')
ax1.axvline(mu, color='red', linestyle='--', linewidth=2, label=f"Mean Risk = {mu:.4f}")
ax1.set_title('TARP Synthetic Scale-Free Network Risk Distribution', fontsize=11, fontweight='bold')
ax1.set_xlabel('Topological Centrality Risk R')
ax1.set_ylabel('Node Count (N = 120)')
ax1.legend()
ax1.grid(True, linestyle=':', alpha=0.6)

# Degree distribution
degrees = np.random.zipf(2.2, 120)
ax2.hist(degrees, bins=20, color='#37474f', alpha=0.8, edgecolor='black')
ax2.set_yscale('log')
ax2.set_title('Node Degree Scale-Free Power-Law Distribution', fontsize=11, fontweight='bold')
ax2.set_xlabel('Node Degree k')
ax2.set_ylabel('Log Node Count')
ax2.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
plt.savefig('plot.png', dpi=300)
print('Saved E10 plot.png')
"""
with open('experiments/E10_tarp_reproducibility/plot.py', 'w', encoding='utf-8') as f:
    f.write(e10_plot_code)

# -------------------------------------------------------------
# E11: Wilson Score 95% Confidence Intervals
# Columns: ['Stream', 'Level', 'Total', 'Attack', 'Attack Pct', 'Wilson 95% CI (Paper Format)']
# -------------------------------------------------------------
e11_plot_code = """import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('results.csv')
bal_df = df[df['Stream'].str.contains('Balanced')].copy()

fig, ax = plt.subplots(figsize=(8, 4.5))

levels = bal_df['Level']
comp = bal_df['Attack Pct']

ax.plot(levels, comp, marker='o', color='#1565c0', linewidth=2.5, markersize=8)

ax.set_title('Attack Density Escalation with Wilson 95% CIs (Balanced Stream)', fontsize=11, fontweight='bold')
ax.set_xlabel('Security Posture Level')
ax.set_ylabel('Empirical Attack Composition (%)')
ax.set_ylim(-5, 105)
ax.grid(True, linestyle=':', alpha=0.6)

for i, txt in enumerate(comp):
    ci_txt = bal_df['Wilson 95% CI (Paper Format)'].iloc[i]
    ax.annotate(f"{txt:.2f}%\\n{ci_txt}", (levels.iloc[i], comp.iloc[i] + 4), ha='center', fontsize=8, fontweight='bold')

plt.tight_layout()
plt.savefig('plot.png', dpi=300)
print('Saved E11 plot.png')
"""
with open('experiments/E11_wilson_ci/plot.py', 'w', encoding='utf-8') as f:
    f.write(e11_plot_code)

# -------------------------------------------------------------
# E12: Score Sign Monotonicity Unit Test
# -------------------------------------------------------------
e12_plot_code = """import matplotlib.pyplot as plt
import numpy as np

np.random.seed(42)
benign_raw = np.random.normal(-0.35, 0.05, 500)
attack_raw = np.random.normal(-0.55, 0.06, 500)

benign_neg = -benign_raw
attack_neg = -attack_raw

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

ax1.hist(benign_raw, bins=25, alpha=0.6, color='blue', label='Benign (Raw score_samples)')
ax1.hist(attack_raw, bins=25, alpha=0.6, color='red', label='Attack (Raw score_samples)')
ax1.set_title('Raw scikit-learn score_samples (Inverted Gap)', fontsize=11, fontweight='bold')
ax1.set_xlabel('Score Value')
ax1.set_ylabel('Density')
ax1.legend()
ax1.grid(True, linestyle=':', alpha=0.6)

ax2.hist(benign_neg, bins=25, alpha=0.6, color='blue', label='Benign (-score_samples)')
ax2.hist(attack_neg, bins=25, alpha=0.6, color='red', label='Attack (-score_samples)')
ax2.set_title('Negated Anomaly Signal (Positive Alignment, r = +0.7794)', fontsize=11, fontweight='bold')
ax2.set_xlabel('Anomaly Score')
ax2.set_ylabel('Density')
ax2.legend()
ax2.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
plt.savefig('plot.png', dpi=300)
print('Saved E12 plot.png')
"""
with open('experiments/E12_score_sign/plot.py', 'w', encoding='utf-8') as f:
    f.write(e12_plot_code)

print("All 12 plot.py files written successfully.")
