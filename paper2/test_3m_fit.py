import time
import json
import torch
import numpy as np
import xgboost as xgb
from pathlib import Path

cache_dir = Path("../audit/lofo/cache")
with open(cache_dir / "class_names.json", "r") as f:
    class_names = json.load(f)

y_train = np.load(cache_dir / "y_train.npy", mmap_mode="r")
brute_idx = [class_names.index("DictionaryBruteForce")]
mask = ~np.isin(y_train, brute_idx)
valid_idx = np.where(mask)[0]

print(f"Testing full 5M fit on GPU...")
X_train = np.load(cache_dir / "X_train.npy", mmap_mode="r")

# Take 3M sorted indices first to test memory
n_sub = 3000000
sub_idx = np.sort(np.random.RandomState(42).choice(valid_idx, size=n_sub, replace=False))
print("Loading 3M slice into RAM...")
t0 = time.time()
X_sub = np.array(X_train[sub_idx], dtype=np.float32)
y_sub = np.array(y_train[sub_idx], dtype=np.int32)
print(f"Loaded in {time.time() - t0:.2f}s")

unique_classes = np.unique(y_sub)
class_map = {c: i for i, c in enumerate(unique_classes)}
y_sub_mapped = np.array([class_map[c] for c in y_sub], dtype=np.int32)

print("Fitting on GPU (n_estimators=100, max_bin=128)...")
t0 = time.time()
try:
    clf = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        tree_method="hist",
        device="cuda",
        max_bin=128,
        random_state=42
    )
    clf.fit(X_sub, y_sub_mapped)
    print(f"Success! 3M fit took {time.time() - t0:.2f}s")
except Exception as e:
    print(f"Error: {e}")
