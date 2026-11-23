import time
import json
import torch
import numpy as np
import xgboost as xgb
from pathlib import Path

cache_dir = Path("../audit/lofo/cache")
with open(cache_dir / "class_names.json", "r") as f:
    class_names = json.load(f)

print("Reading X_train, y_train...")
y_train = np.load(cache_dir / "y_train.npy", mmap_mode="r")
print(f"y_train shape: {y_train.shape}, classes: {len(class_names)}")

# Test with a small family exclusion: BruteForce
brute_idx = [class_names.index("DictionaryBruteForce")]
mask = ~np.isin(y_train, brute_idx)
n_train = np.sum(mask)
print(f"Masked train flows: {n_train}")

# Load X_train
X_train = np.load(cache_dir / "X_train.npy", mmap_mode="r")

# Subsample test: test on 500k flows first to benchmark speed and VRAM
n_sub = 500000
sub_indices = np.random.RandomState(42).choice(np.where(mask)[0], size=n_sub, replace=False)
X_sub = np.array(X_train[sub_indices], dtype=np.float32)
y_sub = np.array(y_train[sub_indices], dtype=np.int32)

# Remap classes
unique_classes = np.unique(y_sub)
class_map = {c: i for i, c in enumerate(unique_classes)}
y_sub_mapped = np.array([class_map[c] for c in y_sub], dtype=np.int32)

print(f"Fitting XGBoost on {n_sub} flows with {len(unique_classes)} classes on CUDA...")
t0 = time.time()
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
fit_time = time.time() - t0
print(f"Done in {fit_time:.2f}s!")
print(f"VRAM allocated: {torch.cuda.memory_allocated() / (1024**2):.2f} MB, max: {torch.cuda.max_memory_allocated() / (1024**2):.2f} MB")
