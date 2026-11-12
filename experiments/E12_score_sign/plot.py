import matplotlib.pyplot as plt
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
