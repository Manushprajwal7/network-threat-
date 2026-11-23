# Experiment E3: Topology Reconciliation & Mathematical Audit
**Target**: Reconcile BA($m=2$) (236 edges) vs MDPI anchor (342 edges), resolve $\sigma_R$ discrepancies, and correct $Z$-score / $p$-value reporting.  
**Execution Timestamp**: 2026-11-18 20:56:03  

---

## 1. Discrepancy Resolution: 236 Edges vs 342 Edges

### Forensic Origin of Edge Discrepancy
- **MDPI Anchor Architecture**: The anchor paper (*J. Cybersecur. Priv.* 6(5), 181) specifies a scale-free network of $N = 120$ nodes with $E = 342$ links (mean degree $\bar{k} = 2E/N = 5.70$).
  $$\text{Edges} = m \times (N - m_0) = 3 \times (120 - 6) = 3 \times 114 = 342$$
  This topology was constructed by attaching $m=3$ edges per arriving node over an initial seed core of $m_0 = 6$ nodes.
- **Proposed Framework Implementation**: In the rewritten paper, the graph generator was instantiated as `nx.barabasi_albert_graph(n=120, m=2, seed=42)`.
  $$\text{Edges} = m \times (N - m) = 2 \times (120 - 2) = 236$$
  The paper text erroneously repeated the MDPI edge count ($342$ links) while executing code that produced $236$ links.

### Structural Comparison Table

| Metric / Attribute | MDPI Anchor Topology | Proposed Framework BA($m=2$) | Mathematical Origin |
| :--- | :---: | :---: | :--- |
| **Number of Nodes ($N$)** | 120 | 120 | Standard IoT gateway topology |
| **Edge Count ($E$)** | **342** | **236** | $m=3$ vs $m=2$ preferential attachment |
| **Mean Degree ($\bar{k}$)** | 5.70 | 3.93 | $\bar{k} = 2E/N$ |
| **Degree Standard Deviation** | 6.84 | 4.88 | Degree dispersion under scale-free growth |
| **Maximum Degree ($k_{\max}$)** | 48 | 41 | Highly connected core backbone hub |
| **Mean Propagated Risk ($\mu_R$)** | **0.4200** | **0.4189** | Close empirical match ($\Delta = 0.0011$) |
| **Risk Standard Deviation ($\sigma_R$)** | **0.1583** | **0.0721** | Empirical standard deviation of scaled risk |
| **Target Distribution ($\mu, \sigma$)** | **(0.42, 0.08)** | **(0.42, 0.08)** | Target normal distribution in `paper.yaml` |
| **Critical Hub Nodes ($R \ge 0.75$)** | **8 nodes** (Nodes 0–7) | **2 nodes** (Node 0, Node 4) | $R \in [0.76, 0.92]$ vs clipped $[0.81, 0.90]$ |
| **High-Risk Nodes ($R \ge 0.60$)** | **14 nodes** | **3 nodes** | Gateway cluster risk concentration |

---

## 2. Mathematical Audit of $\sigma_R$, $Z$-Scores, and $p$-Values

### Analysis of the Published Claims
The manuscript contained three mutually contradictory statements:
1. "$\mu_R = 0.4189, \sigma_R = 0.0721$, yielding $Z = 4.59\sigma$ with $p = 2.2 \times 10^{-6}$"
2. "Target theoretical formulation: $\mu = 0.42, \sigma = 0.08$, yielding $Z = 4.125\sigma$"
3. "Batch-level risk escalation: $Z = 41.25\sigma$"

### Comprehensive Reconciliation Ledger

| Formulation Scope | Assumed $\mu_R$ | Assumed $\sigma_R$ | Threshold ($R_{\text{hub}}$) | Computed $Z$ | One-Tailed $p$ | Correct Two-Tailed $p$ | Audit Finding & Forensic Origin |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Target Formulation** | 0.4200 | 0.0800 | 0.75 | **4.1250$\sigma$** | $1.854 \times 10^{-5}$ | **$3.707 \times 10^{-5}$** | Derived from $(0.75 - 0.42)/0.08 = 4.125$. Target specification in `paper.yaml`. |
| **Empirical BA($m=2$)** | 0.4189 | 0.0721 | 0.75 | **4.5931$\sigma$** | **$2.184 \times 10^{-6}$** | **$4.368 \times 10^{-6}$** | Paper reported one-tailed $p = 2.2 \times 10^{-6}$ as $p$-value. Must report two-tailed $4.4 \times 10^{-6}$. |
| **Batch Artifact** | 0.4200 | $0.08 / \sqrt{100}$ | 0.75 | **41.250$\sigma$** | $\approx 0.0$ | $\approx 0.0$ | **Arithmetic Defect**: Divided $\sigma$ by $\sqrt{100}$ assuming 100 independent nodes, but batch $b$ uses uniform node assignment $R = R[b \pmod{120}]$. |

### Individual Hub Node $Z$-Scores
The threshold $Z$-score ($4.59\sigma$) was frequently conflated with individual hub nodes' $Z$-scores:
- **Node 0**: $R = 0.9000$ (maximum clip boundary)
  $$Z_{\text{Node 0}} = \frac{0.9000 - 0.4189}{0.0721} = \mathbf{6.6739\sigma}$$
- **Node 4**: $R = 0.8089$
  $$Z_{\text{Node 4}} = \frac{0.8089 - 0.4189}{0.0721} = \mathbf{5.4106\sigma}$$
Both individual node $Z$-scores significantly exceed the threshold $Z$-score of $4.59\sigma$.

---

## 3. Policy for Manuscript & Downstream Experiments
1. **Definitive $\sigma_R$ Standard**:
   - The theoretical configuration parameter is fixed at **$\mu_R = 0.42, \sigma_R = 0.08$** ($Z = 4.125\sigma$, two-tailed $p = 3.71 \times 10^{-5}$).
   - The empirical realized sample on the 120-node BA($m=2$) graph is explicitly reported as **$\mu_R = 0.4189, \sigma_R = 0.0721$** ($Z = 4.59\sigma$, two-tailed $p = 4.37 \times 10^{-6}$).
2. **Topology Role Allocation**:
   - The **MDPI topology (120 nodes, 342 edges)** serves as the canonical contextual routing baseline, maintaining parity with the published literature.
   - The **BA($m=2$) graph (120 nodes, 236 edges)** serves as the topological sensitivity test.
3. **Artifacts Generated**:
   - [`mdpi_topology.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/audit_v3/E3_topology/mdpi_topology.csv)
   - [`ba_topology.csv`](file:///c:/Users/Manus/OneDrive/Desktop/thirupati/network-threat/network-threat-/paper2/audit_v3/E3_topology/ba_topology.csv)
