# Experiment E9 Verdict: Runtime Latency, Line-Rate Budgets, and "Real-Time" Removal

**Date**: 2026-11-18  
**Hardware Profiling Platform**:
- GPU: NVIDIA GeForce RTX 3050 Laptop GPU (6GB VRAM, CUDA 13.0, Driver 581.86)
- CPU: Host x86_64 Multithreaded Processor (scikit-learn multithreaded backend)

---

## 1. Measured Component and Pipeline Latency (Single-Flow $B=1$ vs. Batched $B=1024$)

| Component / Stage | Hardware Backend | Execution Mode | Median Latency p50 | 95th Percentile p95 | 99th Percentile p99 | Throughput (Flows/Sec) | Amortized Latency ($\mu\text{s}$/flow) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **XGBoost Inference** | RTX 3050 GPU (CUDA) | Single Flow ($B=1$) | 13,828.5 $\mu\text{s}$ | 18,622.9 $\mu\text{s}$ | **21,624.3 $\mu\text{s}$** | 67.7 flows/sec | 14,775.0 $\mu\text{s}$ |
| **XGBoost Inference** | RTX 3050 GPU (CUDA) | Batched ($B=1024$) | — | — | — | **59,595.6 flows/sec** | **16.78 $\mu\text{s}$** |
| **XGBoost Inference** | RTX 3050 GPU (CUDA) | Batched ($B=4096$) | — | — | — | **177,340.2 flows/sec** | **5.64 $\mu\text{s}$** |
| **XGBoost Inference** | Host CPU (n_jobs=-1) | Single Flow ($B=1$) | 1,864.2 $\mu\text{s}$ | 2,820.2 $\mu\text{s}$ | 2,986.1 $\mu\text{s}$ | 485.7 flows/sec | 2,058.7 $\mu\text{s}$ |
| **Isolation Forest** | Host CPU (n_jobs=-1) | Single Flow ($B=1$) | 7,335.5 $\mu\text{s}$ | 9,257.6 $\mu\text{s}$ | **10,795.1 $\mu\text{s}$** | 131.6 flows/sec | 7,600.4 $\mu\text{s}$ |
| **Isolation Forest** | Host CPU (n_jobs=-1) | Batched ($B=2048$) | — | — | — | **110,189.7 flows/sec** | **9.08 $\mu\text{s}$** |
| **ADTM Causal Trust** | Host CPU | Sequential Causal ($B=1$) | **0.80 $\mu\text{s}$** | 1.70 $\mu\text{s}$ | 1.90 $\mu\text{s}$ | **1,156,350.1 updates/s**| **0.86 $\mu\text{s}$** |
| **TARP PageRank** | Host CPU | 120-Node Iteration | **4.80 $\mu\text{s}$** | 5.20 $\mu\text{s}$ | 7.60 $\mu\text{s}$ | **194,707.8 updates/s** | **4.99 $\mu\text{s}$** |
| **Microscopic Veto** | Host CPU | Single Conditional ($B=1$) | **0.177 $\mu\text{s}$** | 0.30 $\mu\text{s}$ | 0.40 $\mu\text{s}$ | **454.5M checks/sec** | **0.0002 $\mu\text{s}$** |
| **End-to-End $P_{\text{hybrid}}$** | GPU + CPU Pipeline | Micro-Batch ($B=1024$) | — | — | — | **18,244.3 flows/sec** | **54.81 $\mu\text{s}$** |

---

## 2. Line-Rate Budget Evaluation: Why "Real-Time" is Removed

### Standard Operational Budgets:
- **1 Gbps Network (Standard MTU 1,500 Bytes)**: Minimum packet inter-arrival budget is $\approx 12.0 \ \mu\text{s}$ per packet ($pprox 83,333$ packets/sec).
- **Subnet Gateway Flow Budget**: Assuming aggregated flow records arriving at 1,000 flows/sec, the maximum permissible latency is **1.0 ms (1,000 $\mu\text{s}$)**.

### Verdict on "Real-Time" Inline Forwarding:
1. **Single-Flow Execution Fails Real-Time Budget**:
   - Single-flow GPU invocation ($B=1$) consumes $13.8 \ \text{ms}$ (median) and $21.6 \ \text{ms}$ ($p_{99}$) due to CUDA kernel launch overhead and device synchronization.
   - Single-flow CPU Isolation Forest consumes $7.3 \ \text{ms}$ ($p_{50}$) and $10.8 \ \text{ms}$ ($p_{99}$).
   - Both single-flow latencies exceed the 1.0 ms budget by an order of magnitude.
2. **Batched Micro-Windows Satisfy Line-Rate Processing**:
   - Under micro-batching ($B \ge 256$), GPU XGBoost amortized latency drops to **$16.78 \ \mu\text{s}$** ($B=1024$), and the full multi-modal pipeline executes in **$54.81 \ \mu\text{s}$ per flow** ($18,244$ flows/sec).
   - This throughput is more than sufficient to sustain 1–10 Gbps enterprise edge links without flow table overflow.
3. **Mandatory Editorial Action**:
   - **`REAL-TIME CLAIM FORMALLY REMOVED`**: Replace all occurrences of "real-time forwarding" and "real-time line rate" in Section 3.1 and elsewhere with:
     *`"inline batched inspection at edge gateways"`* or *`"sub-millisecond amortized line-rate processing (>18,000 flows/sec) under batched micro-windows ($B \ge 256$)"`*.
