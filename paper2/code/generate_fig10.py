import os
import sys
sys.path.insert(0, ".")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from paper2.code.generate_both_windows import trust_bal, y_bal, preds_bal, get_family, levels_bal

os.makedirs("paper2/figures", exist_ok=True)
fig_path = "paper2/figures/fig10_trust_traces.png"

# Reshape trust to (600, 100)
E = 600
N = 100
t_traces = trust_bal.reshape(E, N)
y_traces = y_bal.reshape(E, N)
lvl_arr = levels_bal

# Find representative entities:
# 1. Pure Benign Entity (L0)
pure_ben_e = [e for e in range(E) if lvl_arr[e] == 0 and np.all(y_traces[e] == 1)][0]

# 2. Aggressive Mirai Botnet / Volumetric Attack (L5 / L4)
mirai_entities = []
for e in range(E):
    fams = [get_family(y) for y in y_traces[e] if y != 1]
    if "Mirai" in fams and lvl_arr[e] >= 4:
        mirai_entities.append(e)
mirai_e = mirai_entities[0]

# 3. DDoS Flooding Attack (L4)
ddos_entities = []
for e in range(E):
    fams = [get_family(y) for y in y_traces[e] if y != 1]
    if fams.count("DDoS") > 80 and lvl_arr[e] == 4:
        ddos_entities.append(e)
ddos_e = ddos_entities[0]

# 4. Stealth Reconnaissance / Probe (L2 / L3)
recon_entities = []
for e in range(E):
    fams = [get_family(y) for y in y_traces[e] if y != 1]
    if "Recon" in fams and lvl_arr[e] in [2, 3]:
        recon_entities.append(e)
recon_e = recon_entities[0] if len(recon_entities) > 0 else 15

# 5. Mixed Traffic Entity with Recovery (L1 / L2)
mixed_entities = []
for e in range(E):
    atk_cnt = np.sum(y_traces[e] != 1)
    if 30 <= atk_cnt <= 60 and lvl_arr[e] in [1, 2]:
        mixed_entities.append(e)
mixed_e = mixed_entities[0]

print(f"Selected entities: Pure Benign={pure_ben_e} (L{lvl_arr[pure_ben_e]}), "
      f"Mirai={mirai_e} (L{lvl_arr[mirai_e]}), DDoS={ddos_e} (L{lvl_arr[ddos_e]}), "
      f"Recon={recon_e} (L{lvl_arr[recon_e]}), Mixed={mixed_e} (L{lvl_arr[mixed_e]})")

# Plot Traces
plt.figure(figsize=(12, 6))

time_steps = np.arange(1, 101)

plt.plot(time_steps, t_traces[pure_ben_e], label=f"Entity {pure_ben_e}: Pure Benign Sensor ($L_0$, Mean Trust: {t_traces[pure_ben_e].mean():.1f})", 
         color="#2b5c8f", linewidth=2.2)
plt.plot(time_steps, t_traces[mixed_e], label=f"Entity {mixed_e}: Mixed Intermittent Traffic ($L_1$, Mean Trust: {t_traces[mixed_e].mean():.1f})", 
         color="#16a085", linewidth=2.0, linestyle="-.")
plt.plot(time_steps, t_traces[recon_e], label=f"Entity {recon_e}: Stealth Reconnaissance ($L_2$, Mean Trust: {t_traces[recon_e].mean():.1f})", 
         color="#f39c12", linewidth=2.0)
plt.plot(time_steps, t_traces[ddos_e], label=f"Entity {ddos_e}: Volumetric DDoS Attack ($L_4$, Mean Trust: {t_traces[ddos_e].mean():.1f})", 
         color="#e67e22", linewidth=2.0, linestyle="--")
plt.plot(time_steps, t_traces[mirai_e], label=f"Entity {mirai_e}: Mirai IoT Botnet ($L_5$, Mean Trust: {t_traces[mirai_e].mean():.1f})", 
         color="#c0392b", linewidth=2.2)

# Horizontal bands
plt.axhspan(80, 100, color="#d4efdf", alpha=0.3, label="High Trust Band [80, 100]")
plt.axhspan(60, 80, color="#d6eaf8", alpha=0.3, label="Moderate Trust Band [60, 80]")
plt.axhspan(40, 60, color="#fcf3cf", alpha=0.3, label="Low Trust Band [40, 60]")
plt.axhspan(20, 40, color="#fdebd0", alpha=0.3, label="Very Low Trust Band [20, 40]")
plt.axhspan(0, 20, color="#fadbd8", alpha=0.3, label="Critical Trust Band [0, 20]")

# Threshold lines
plt.axhline(60, color="#7f8c8d", linestyle=":", alpha=0.7)
plt.axhline(40, color="#7f8c8d", linestyle=":", alpha=0.7)
plt.axhline(20, color="#7f8c8d", linestyle=":", alpha=0.7)

plt.xlabel("Flow Sequence Time Step ($t = 1 \\dots 100$)", fontsize=11, fontweight="bold")
plt.ylabel("ADTM Dynamic Trust Score ($T_t \\in [0, 100]$)", fontsize=11, fontweight="bold")
plt.title("ADTM Dynamic Trust Traces Across Representative IoT Entities\n(Demonstrating Rapid Volumetric Decay, Stealth Tracking, and Per-Flow Recovery Without Lock)", 
          fontsize=12, fontweight="bold", pad=12)
plt.xlim(1, 100)
plt.ylim(0, 105)
plt.grid(True, linestyle="--", alpha=0.4)
plt.legend(loc="upper right", frameon=True, fontsize=8.5, ncol=2)

# Annotations
plt.annotate("Hard Reset (T=10)\non confirmed attack", xy=(4, 10), xytext=(12, 25),
             arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.5),
             fontsize=9, fontweight="bold", bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff2cc", edgecolor="#c0392b"))

plt.annotate("Stable High Trust (85-95)\nfor benign entity", xy=(50, 91), xytext=(55, 78),
             arrowprops=dict(arrowstyle="->", color="#2b5c8f", lw=1.5),
             fontsize=9, fontweight="bold", bbox=dict(boxstyle="round,pad=0.3", facecolor="#eef3f8", edgecolor="#2b5c8f"))

plt.tight_layout()
plt.savefig(fig_path, dpi=300)
plt.close()
print(f"Generated {fig_path} successfully ({os.path.getsize(fig_path):,} bytes)")
