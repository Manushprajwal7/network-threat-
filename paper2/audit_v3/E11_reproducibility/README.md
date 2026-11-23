# Cryptographic Reproducibility Package: Network Threat Posture Audit (`audit_v3`)

**Package Version**: 3.0.0 (Audit Verification Release)  
**Generation Date**: 2026-11-18 21:32:47  
**Target Manuscript**: Autonomous Posture Escalation and Cost-Aware Telemetry Response (CICIoT2023)  
**Cryptographic Integrity**: SHA-256 Manifest provided in [`MANIFEST.sha256`](MANIFEST.sha256)  

---

## 1. Verified Hardware and Runtime Environment

| Parameter | Host Specification |
| :--- | :--- |
| **Operating System** | Windows 11 (AMD64) |
| **Python Runtime** | CPython 3.12.10 |
| **GPU Model** | NVIDIA GeForce RTX 3050 6GB Laptop GPU (Compute Capability (8, 6), 6GB VRAM) |
| **CUDA Runtime** | PyTorch CUDA 2.5.1+cu121 (Driver 581.86, CUDA 13.0) |
| **XGBoost Version** | 3.3.0 (with `device='cuda'`, `tree_method='hist'`) |
| **Scikit-Learn Version** | 1.9.0 (Multithreaded CPU backend) |
| **cuML Status** | Fallback to scikit-learn CPU (RAPIDS cuML wheel unavailable on Windows AMD64) |

---

## 2. Experimental Random Seeds Catalog

To ensure strict deterministic replicability, all experiments operate under registered pseudo-random seeds:
- **Validation Split ($D_{\text{val}}$)**: `Seed 42` (60,000 stratified flows)
- **Held-Out Test Split ($D_{\text{test}}$)**: `Seed 99` (60,000 stratified flows)
- **Decoupled Calibration Split ($D_{\text{calib}}$)**: `Seed 2024` (20,000 clean benign flows)
- **Permutation Null Test (E4)**: `Seed 42` (1,000 full-stream permutations)
- **Multi-Seed Evaluation Ensemble (E5, E8)**: 10 independent seeds:
  `[13, 42, 99, 123, 2024, 7, 77, 101, 2023, 31415]`
- **Leave-One-Family-Out Retraining (E6)**: `Seed 42` (3M flows/fold subsample)

---

## 3. Step-by-Step Reproduction Guide

Execute each audit module from the repository workspace (`paper2/`):

```powershell
# Step 0: Verify environment & pre-cache datasets
python audit_v3/env/inference_helper.py

# Step 1: Reproduce MDPI baseline negative results
python run_e1_mdpi_baseline.py

# Step 2: Topology reconciliation (BA m=2 vs MDPI 342-links)
python run_e3_topology.py

# Step 3: Run 1,000-permutation monotonicity test
python run_e4_permutation_v2.py

# Step 4: Formalize P_hybrid & paired Wilcoxon tests across 10 seeds
python run_e5_p_hybrid.py

# Step 5: Regime-shift & Leave-One-Family-Out (LOFO) GPU retraining
python run_e6_regime_and_lofo.py

# Step 6: Decouple calibration split from policy selection
python run_e7_calibration_split.py

# Step 7: Enumerate 70 policies across 50 streams & sensitivity sweep
python run_e8_cost_and_policy.py

# Step 8: Micro-benchmark runtime latency and batched throughput
python run_e9_latency.py

# Step 9: Validate numeric consistency ledger against manuscript
python build_e10_consistency.py
```

---

## 4. Archive Verification & Hash Checking

To verify file integrity:
```bash
sha256sum -c audit_v3/E11_reproducibility/MANIFEST.sha256
```
