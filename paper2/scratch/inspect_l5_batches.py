import numpy as np
import pandas as pd
from pathlib import Path
import json

ROOT = Path(".").resolve()
d_val_dir = ROOT / "audit_v3" / "cache"

# Load Table 6 data: D_val
X_val_unscaled = np.load(d_val_dir / "D_val_X.npy")
X_val_scaled = np.load(d_val_dir / "D_val_X_scaled.npy")
y_val = np.load(d_val_dir / "D_val_y.npy")

cache_dir = ROOT.parent / "audit" / "lofo" / "cache"
with open(cache_dir / "class_names.json", "r") as f:
    class_names = json.load(f)
benign_idx = class_names.index("BenignTraffic")

# Let's inspect how Table 6 was generated in run_e1_mdpi_baseline.py or similar
# Let's search where tab6_posture_balanced.csv was generated
for p in Path(".").glob("**/*posture_balanced*.py"):
    print(p)
