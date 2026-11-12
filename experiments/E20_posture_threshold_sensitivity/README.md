# Experiment E20: Posture Threshold Sensitivity (Table 14, Appendix D)

## Monotonicity Boundaries
- Strict non-decreasing attack density is preserved across tau_anom in [0.40, 0.70], tau_T in [40, 70], tau_conf in [0.80, 0.95], and tau_topo in [0.30, 0.60].
- Monotonicity breaks when tau_T >= 80 (premature trust degradation invert L1/L2) or tau_topo >= 0.75 (premature escalation to L5 on edge streams).
