import numpy as np
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

ax.text(0.445, 30, f"Critical Hub Threshold\ntau_R = 0.75\n(Z = +41.25 sigma)\nP(R_bar >= 0.75) < 10^-300", 
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffebee', edgecolor='#c62828', linewidth=1.5),
        fontsize=9, color='#c62828', fontweight='bold')

ax.legend(loc='upper left')
plt.tight_layout()
plt.savefig('plot.png', dpi=300)
print('Saved E8 plot.png')
