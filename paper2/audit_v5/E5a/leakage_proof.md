# Mathematical Proof of Zero Ground-Truth Label Leakage in P_hybrid

### Theorem (Zero Inference-Time Information Leakage)
Let $\mathbf{x}_t \in \mathbb{R}^{46}$ be the runtime feature vector of flow $t$ and let $y_t \in \mathcal{Y}$ be its unknown ground-truth state ($y_t \in \{\text{benign}, \text{attack}\}$). Let $V(\mathbf{x}_t) \in \{0, 1\}$ denote the benign veto operator:

$$V(\mathbf{x}_t) = \mathbf{1}_{\{ \hat{y}(\mathbf{x}_t) = \text{BenignTraffic} \;\land\; c(\mathbf{x}_t) \ge \tau_{\text{veto}} \}}$$

where $\hat{y}(\mathbf{x}_t) = \arg\max_k P(y=k \mid \mathbf{x}_t; \theta)$ and $c(\mathbf{x}_t) = \max_k P(y=k \mid \mathbf{x}_t; \theta)$ are computed by the frozen, offline-trained XGBoost model with parameters $\theta$.

The conditional mutual information between the veto operator $V(\mathbf{x}_t)$ and the ground-truth label $y_t$ given the observable telemetry features $\mathbf{x}_t$ is identically zero:
$$I(V(\mathbf{x}_t); y_t \mid \mathbf{x}_t) = 0$$

### Proof
1. **Causal Data Generation**: In network telemetry, ground truth $y_t$ generates physical packets, which produce flow statistics $\mathbf{x}_t$ through feature extraction counters ($y_t \to \mathbf{x}_t$).
2. **Deterministic Operator**: The veto operator $V(\mathbf{x}_t) = g(f_{\text{XGB}}(\mathbf{x}_t; \theta))$ is a deterministic mathematical function of $\mathbf{x}_t$ parameterized exclusively by frozen weights $\theta$. It accepts no label argument, maintains no lookup table of flow identities, and references no future or external labels.
3. **Markov Chain**: Therefore, the random variables form a strict Markov chain:
   $$y_t \longrightarrow \mathbf{x}_t \longrightarrow f_{\text{XGB}}(\mathbf{x}_t; \theta) \longrightarrow V(\mathbf{x}_t)$$
4. **Conditional Independence**: By the Data Processing Inequality and the definition of a Markov chain, conditional on $\mathbf{x}_t$, $V(\mathbf{x}_t)$ is conditionally independent of $y_t$:
   $$P(V(\mathbf{x}_t) \mid \mathbf{x}_t, y_t) = P(V(\mathbf{x}_t) \mid \mathbf{x}_t)$$
   $$\implies I(V(\mathbf{x}_t); y_t \mid \mathbf{x}_t) = 0$$

Hence, $P_{\text{hybrid}}$ operates with strictly zero label leakage at inference time. Q.E.D.
