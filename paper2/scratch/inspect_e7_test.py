import numpy as np
import pandas as pd
from pathlib import Path

# Load test predictions and levels from E7
d_val_dir = Path("audit_v3/cache")
X_test_scaled = np.load(d_val_dir / "D_test_X_scaled.npy")
y_test = np.load(d_val_dir / "D_test_y.npy")

import json
cache_dir = Path("../audit/lofo/cache")
with open(cache_dir / "class_names.json", "r") as f:
    class_names = json.load(f)
benign_idx = class_names.index("BenignTraffic")
y_test_bin = (y_test != benign_idx).astype(int)

# Load test_policy_table.csv
df_test = pd.read_csv("audit_v3/E7_calibration_split/test_policy_table.csv")
print("=== test_policy_table.csv ===")
print(df_test)
