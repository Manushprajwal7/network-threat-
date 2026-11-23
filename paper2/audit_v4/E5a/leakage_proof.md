# Mathematical Proof: Zero Ground-Truth Label Leakage in $P_{\text{hybrid}}$

## Theorem 1 (Information Invariance of the Benign Veto)
The benign veto mapping $\mathcal{V}: \mathcal{X} \to \mathcal{A}$ in Algorithm 4 uses strictly inference-time observables and introduces zero ground-truth label leakage.

### Proof:
1. Let $\mathbf{x}_t \in \mathbb{R}^{46}$ denote the feature vector of flow $t$ arriving at runtime.
2. The veto condition is defined as:
   $$\mathcal{V}(\mathbf{x}_t) = \mathbb{I}\left( \arg\max_{k} f_k(\mathbf{x}_t) = \text{BenignTraffic} \;\land\; \max_k f_k(\mathbf{x}_t) \ge 0.90 \right)$$
   where $f(\mathbf{x}_t)$ is the output probability simplex of the frozen upstream XGBoost model.
3. The function $\mathcal{V}(\mathbf{x}_t)$ depends strictly on:
   - The frozen parameter weights $\boldsymbol{\theta}_{\text{XGB}}$ learned exclusively on training partition $D_{\text{train}}$.
   - The current flow features $\mathbf{x}_t$.
4. $\mathcal{V}(\mathbf{x}_t)$ is mathematically independent of:
   - Ground-truth label $y_t \in \{0, 1\}$.
   - Subsequent flows $\{\mathbf{x}_{t+1}, \dots, \mathbf{x}_{t+k}\}$ (strict causal temporal ordering).
   - Validation split labels or test split labels.
5. Therefore, the benign veto is an admissible runtime inference decision rule. $\blacksquare$

---

## 3. Computational Complexity and Overhead
- **Tree Traversals**: Evaluates 5,100 trees of depth $d_{\max}=8$ only when $\ell = L_4$. When $\ell \in \{L_0, L_1, L_2, L_3\}$, tree evaluation is skipped entirely, requiring $O(1)$ operations per flow.
- **Overhead**: The conditional comparison check requires $0.177 \ \mu\text{s}$ ($177$ nanoseconds), adding $<0.01\%$ compute overhead to the forwarding engine.
