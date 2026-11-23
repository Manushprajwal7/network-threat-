import os
import sys
import json
import hashlib
import platform
import sklearn
import scipy
import numpy
import pandas
import docx
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def generate_reproducibility_manifest():
    print("=== TASK 8: GENERATING REPRODUCIBILITY MANIFEST & HASH ARCHIVE ===")
    
    # 1. Environment Details
    env_info = {
        "os_platform": platform.platform(),
        "python_version": sys.version,
        "packages": {
            "numpy": numpy.__version__,
            "scipy": scipy.__version__,
            "pandas": pandas.__version__,
            "scikit-learn": sklearn.__version__,
            "python-docx": docx.__version__,
            "pyyaml": yaml.__version__
        }
    }
    
    # 2. Master Seeds Inventory
    seeds_inventory = {
        "primary_evaluation": 42,
        "held_out_test": 99,
        "task2_permutations_seed": 12345,
        "task3_10_seeds": [13, 42, 99, 123, 2024, 7, 77, 101, 2023, 31415],
        "task6_5_seeds": [13, 42, 99, 123, 2024],
        "tarp_graph_seed": 42
    }
    
    # 3. Hash All Audit Scripts & Generated Outputs
    files_to_hash = []
    
    # Audit scripts
    for script_path in (ROOT / "audit").glob("*.py"):
        files_to_hash.append(script_path)
        
    # Audit outputs
    for out_path in (ROOT / "audit" / "outputs").glob("*.csv"):
        files_to_hash.append(out_path)
        
    # Consistency ledgers
    files_to_hash.append(ROOT / "audit" / "consistency.csv")
    
    # Manuscript files
    tex_path = ROOT / "clean_experiments_isolated" / "manuscript" / "paper_v3.tex"
    if tex_path.exists():
        files_to_hash.append(tex_path)
        
    docx_path = ROOT / "draft" / "paper2_manuscript.docx"
    if docx_path.exists():
        files_to_hash.append(docx_path)
        
    for sec_path in (ROOT / "draft" / "sections").glob("*.py"):
        files_to_hash.append(sec_path)
        
    hash_manifest = []
    sha256_lines = []
    
    for f in sorted(files_to_hash):
        if f.is_file():
            sha = compute_sha256(f)
            rel_p = str(f.relative_to(ROOT))
            hash_manifest.append({"file": rel_p, "sha256": sha, "bytes": f.stat().st_size})
            sha256_lines.append(f"{sha}  {rel_p}")
            
    manifest = {
        "timestamp": "2026-11-17T23:23:00Z",
        "environment": env_info,
        "seeds": seeds_inventory,
        "hashes": hash_manifest
    }
    
    # Write JSON manifest and SHA256SUMS.txt
    manifest_path = ROOT / "audit" / "reproducibility_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as fp:
        json.dump(manifest, fp, indent=2)
        
    sha_path = ROOT / "audit" / "SHA256SUMS.txt"
    with open(sha_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(sha256_lines) + "\n")
        
    print(f"Saved reproducibility manifest to {manifest_path}")
    print(f"Saved SHA256 checksums to {sha_path} ({len(sha256_lines)} files)")

if __name__ == "__main__":
    generate_reproducibility_manifest()
