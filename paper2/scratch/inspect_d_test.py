import numpy as np
import json
from pathlib import Path

cache_dir = Path("../audit/lofo/cache")
with open(cache_dir / "class_names.json", "r") as f:
    class_names = json.load(f)
benign_idx = class_names.index("BenignTraffic")

d_val_dir = Path("audit_v3/cache")
y_test = np.load(d_val_dir / "D_test_y.npy")
print("len y_test:", len(y_test))
n_ben = int(np.sum(y_test == benign_idx))
n_atk = int(np.sum(y_test != benign_idx))
print(f"y_test benign: {n_ben:,} ({n_ben/len(y_test)*100:.2f}%), attack: {n_atk:,} ({n_atk/len(y_test)*100:.2f}%)")

y_val = np.load(d_val_dir / "D_val_y.npy")
print("len y_val:", len(y_val))
n_ben_val = int(np.sum(y_val == benign_idx))
n_atk_val = int(np.sum(y_val != benign_idx))
print(f"y_val benign: {n_ben_val:,} ({n_ben_val/len(y_val)*100:.2f}%), attack: {n_atk_val:,} ({n_atk_val/len(y_val)*100:.2f}%)")
