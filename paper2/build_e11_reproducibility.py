import os
import sys
import time
import json
import hashlib
import tarfile
import platform
import subprocess
import torch
import sklearn
import xgboost as xgb
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "audit_v3" / "E11_reproducibility"
OUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("EXPERIMENT E11: REPRODUCIBILITY PACKAGE GENERATION")
print("=" * 70)

# 1. Environment Details
env_info = {
    "os": f"{platform.system()} {platform.release()} ({platform.machine()})",
    "python": sys.version.split()[0],
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A",
    "cuda_capability": str(torch.cuda.get_device_capability(0)) if torch.cuda.is_available() else "N/A",
    "xgboost": xgb.__version__,
    "sklearn": sklearn.__version__,
    "cuml": "Fallback to scikit-learn CPU (RAPIDS cuML wheel unavailable on Windows AMD64)",
}
print("Environment Metadata:")
for k, v in env_info.items():
    print(f"  {k}: {v}")

# 2. Experimental Seeds
seeds_catalog = {
    "D_val_split_seed": 42,
    "D_test_split_seed": 99,
    "D_calib_split_seed": 2024,
    "E4_permutation_seed": 42,
    "E5_E8_multi_seeds": [13, 42, 99, 123, 2024, 7, 77, 101, 2023, 31415],
    "E6_lofo_sampling_seed": 42,
}

# 3. Compute SHA-256 Hashes of Target Files
def compute_sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

manifest_lines = []
target_dirs = [
    ROOT / "audit_v3" / "env",
    ROOT / "audit_v3" / "E1_mdpi_baseline",
    ROOT / "audit_v3" / "E2_defect_trace",
    ROOT / "audit_v3" / "E3_topology",
    ROOT / "audit_v3" / "E4_permutation_v2",
    ROOT / "audit_v3" / "E5_p_hybrid",
    ROOT / "audit_v3" / "E6_regime_shift",
    ROOT / "audit_v3" / "E7_calibration_split",
    ROOT / "audit_v3" / "E8_cost_and_policy",
    ROOT / "audit_v3" / "E9_latency",
    ROOT / "audit_v3" / "E10_consistency",
]

script_files = [
    ROOT / "run_e1_mdpi_baseline.py",
    ROOT / "run_e3_topology.py",
    ROOT / "run_e4_permutation_v2.py",
    ROOT / "run_e5_p_hybrid.py",
    ROOT / "run_e6_regime_and_lofo.py",
    ROOT / "run_e7_calibration_split.py",
    ROOT / "run_e8_cost_and_policy.py",
    ROOT / "run_e9_latency.py",
    ROOT / "build_e10_consistency.py",
]

all_files_to_hash = []
for d in target_dirs:
    if d.exists():
        for p in d.rglob("*"):
            if p.is_file() and not p.name.endswith(".npy") and not p.name.endswith(".parquet") and not p.name.endswith(".tar.gz"):
                all_files_to_hash.append(p)

for s in script_files:
    if s.exists():
        all_files_to_hash.append(s)

# Also hash models
model_files = [
    ROOT.parent / "backend" / "ml_model" / "saved_models" / "xgboost.pkl",
    ROOT.parent / "backend" / "ml_model" / "saved_models" / "isolation_forest_corrected.pkl",
]
for m in model_files:
    if m.exists():
        all_files_to_hash.append(m)

print(f"\nComputing SHA-256 hashes for {len(all_files_to_hash)} key artifacts...")
for fpath in sorted(all_files_to_hash):
    sha = compute_sha256(fpath)
    rel_path = fpath.relative_to(ROOT) if fpath.is_relative_to(ROOT) else fpath.relative_to(ROOT.parent)
    manifest_lines.append(f"{sha}  {rel_path.as_posix()}")

manifest_path = OUT_DIR / "MANIFEST.sha256"
with open(manifest_path, "w") as f:
    f.write("\n".join(manifest_lines) + "\n")
print(f"Saved manifest to {manifest_path}")

# 4. Write README.md
readme_content = f"""# Cryptographic Reproducibility Package: Network Threat Posture Audit (`audit_v3`)

**Package Version**: 3.0.0 (Audit Verification Release)  
**Generation Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}  
**Target Manuscript**: Autonomous Posture Escalation and Cost-Aware Telemetry Response (CICIoT2023)  
**Cryptographic Integrity**: SHA-256 Manifest provided in [`MANIFEST.sha256`](MANIFEST.sha256)  

---

## 1. Verified Hardware and Runtime Environment

| Parameter | Host Specification |
| :--- | :--- |
| **Operating System** | {env_info['os']} |
| **Python Runtime** | CPython {env_info['python']} |
| **GPU Model** | {env_info['cuda_device']} (Compute Capability {env_info['cuda_capability']}, 6GB VRAM) |
| **CUDA Runtime** | PyTorch CUDA {env_info['torch']} (Driver 581.86, CUDA 13.0) |
| **XGBoost Version** | {env_info['xgboost']} (with `device='cuda'`, `tree_method='hist'`) |
| **Scikit-Learn Version** | {env_info['sklearn']} (Multithreaded CPU backend) |
| **cuML Status** | {env_info['cuml']} |

---

## 2. Experimental Random Seeds Catalog

To ensure strict deterministic replicability, all experiments operate under registered pseudo-random seeds:
- **Validation Split ($D_{{\\text{{val}}}}$)**: `Seed 42` (60,000 stratified flows)
- **Held-Out Test Split ($D_{{\\text{{test}}}}$)**: `Seed 99` (60,000 stratified flows)
- **Decoupled Calibration Split ($D_{{\\text{{calib}}}}$)**: `Seed 2024` (20,000 clean benign flows)
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
"""

readme_path = OUT_DIR / "README.md"
with open(readme_path, "w") as f:
    f.write(readme_content)
print(f"Saved README to {readme_path}")

# 5. Build Self-Contained Tarball ready for Zenodo / OSF upload
tar_path = OUT_DIR / "artifact.tar.gz"
print(f"\nBuilding {tar_path.name}...")
with tarfile.open(tar_path, "w:gz") as tar:
    # Add all audit_v3 directories (excluding huge parquet/npy files to keep tarball lightweight and shareable)
    for p in OUT_DIR.parent.rglob("*"):
        if p.is_file() and not p.name.endswith(".npy") and not p.name.endswith(".parquet") and p != tar_path:
            rel = p.relative_to(OUT_DIR.parent)
            tar.add(p, arcname=f"audit_v3/{rel.as_posix()}")
            
    # Add script files
    for s in script_files:
        if s.exists():
            tar.add(s, arcname=f"scripts/{s.name}")

tar_size_mb = tar_path.stat().st_size / (1024 * 1024)
print(f"Created self-contained tarball: {tar_path} ({tar_size_mb:.2f} MB)")
print("=" * 70)
print("EXPERIMENT E11 COMPLETED SUCCESSFULLY!")
print("=" * 70)
