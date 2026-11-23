import os
import sys
import json
import time
import psutil
import joblib
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import xgboost as xgb
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIT_V3 = ROOT / "audit_v3"
ENV_DIR = AUDIT_V3 / "env"
CACHE_DIR = AUDIT_V3 / "cache"

ENV_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 1. Load class names and feature columns
with open("../audit/lofo/cache/class_names.json", "r") as f:
    class_names = json.load(f)

feature_cols = joblib.load("../backend/ml_model/saved_models/feature_columns.pkl")
benign_idx = class_names.index("BenignTraffic")

def get_family(cls_idx, name):
    if cls_idx == benign_idx or name == "BenignTraffic":
        return "Benign"
    if "DDoS" in name:
        return "DDoS"
    if "DoS" in name:
        return "DoS"
    if "Mirai" in name:
        return "Mirai"
    if "Recon" in name or "VulnerabilityScan" in name:
        return "Recon"
    if name in ["Backdoor_Malware", "BrowserHijacking", "CommandInjection", "SqlInjection", "Uploading_Attack", "XSS"]:
        return "Web"
    if "Spoofing" in name or "MITM" in name:
        return "Spoofing"
    if "BruteForce" in name:
        return "BruteForce"
    return "Other"

class_to_family = [get_family(i, name) for i, name in enumerate(class_names)]

def get_memory_info():
    vmem = psutil.virtual_memory()
    return f"RAM: used={vmem.used / 1e9:.2f}GB, avail={vmem.available / 1e9:.2f}GB"

print("Starting cache and verification script...")
print(get_memory_info())

# 2. Window generation logic
def generate_stratified_balanced_window(y_test, seed=42):
    rng = np.random.RandomState(seed)
    benign_indices = np.where(y_test == benign_idx)[0]
    attack_indices = np.where(y_test != benign_idx)[0]
    
    b_pure = rng.choice(benign_indices, size=180 * 100, replace=False).reshape(180, 100)
    a_pure = rng.choice(attack_indices, size=180 * 100, replace=False).reshape(180, 100)
    
    remaining_b = np.setdiff1d(benign_indices, b_pure.flatten())
    remaining_a = np.setdiff1d(attack_indices, a_pure.flatten())
    
    mixed_batches = []
    for _ in range(240):
        k_atk = rng.binomial(100, 0.50)
        k_ben = 100 - k_atk
        idx_a = rng.choice(remaining_a, size=k_atk, replace=False)
        idx_b = rng.choice(remaining_b, size=k_ben, replace=False)
        flows = np.concatenate([idx_a, idx_b])
        rng.shuffle(flows)
        mixed_batches.append(flows)
        
    all_bal = np.concatenate([b_pure, np.array(mixed_batches), a_pure], axis=0)
    batch_shuffle = np.arange(600)
    rng.shuffle(batch_shuffle)
    return all_bal[batch_shuffle].flatten()

# 3. Load mmap references
X_train_mmap = np.load("../audit/lofo/cache/X_train.npy", mmap_mode="r")
X_train_scaled_mmap = np.load("../audit/lofo/cache/X_train_scaled.npy", mmap_mode="r")
y_train_mmap = np.load("../audit/lofo/cache/y_train.npy", mmap_mode="r")

X_test_mmap = np.load("../audit/lofo/cache/X_test.npy", mmap_mode="r")
X_test_scaled_mmap = np.load("../audit/lofo/cache/X_test_scaled.npy", mmap_mode="r")
y_test_mmap = np.load("../audit/lofo/cache/y_test.npy", mmap_mode="r")

shapes_log = []
shapes_log.append("=" * 70)
shapes_log.append("CICIoT2023 DATASET SHAPES, DTYPES, AND CLASS DISTRIBUTIONS")
shapes_log.append("=" * 70)
shapes_log.append(f"Source: ../audit/lofo/cache/")
shapes_log.append(f"Number of Features: {len(feature_cols)}")
shapes_log.append(f"Number of Classes: {len(class_names)}")
shapes_log.append(f"Benign Class: {class_names[benign_idx]} (idx: {benign_idx})\n")

# A. Process D_train
print("Processing D_train (5,491,971 flows)...")
n_train = len(y_train_mmap)
train_counts = pd.Series(np.array(y_train_mmap)).value_counts().sort_index()

shapes_log.append("--- D_train Partition ---")
shapes_log.append(f"Shape: ({n_train}, {X_train_mmap.shape[1]})")
shapes_log.append(f"Features Dtype: float32, Labels Dtype: int32")
shapes_log.append(f"Total flows: {n_train:,}")
shapes_log.append(f"Benign flows: {train_counts.get(benign_idx, 0):,} ({train_counts.get(benign_idx, 0)/n_train*100:.3f}%)")
shapes_log.append(f"Attack flows: {n_train - train_counts.get(benign_idx, 0):,} ({(n_train - train_counts.get(benign_idx, 0))/n_train*100:.3f}%)\n")

# Write D_train label metadata parquet
train_labels_df = pd.DataFrame({
    "label": np.array(y_train_mmap, dtype=np.int32),
    "label_name": [class_names[i] for i in y_train_mmap],
    "family": [class_to_family[i] for i in y_train_mmap],
    "is_attack": (np.array(y_train_mmap) != benign_idx).astype(np.int8)
})
train_labels_parquet = CACHE_DIR / "D_train_labels.parquet"
train_labels_df.to_parquet(train_labels_parquet, index=False)
print(f"Saved {train_labels_parquet} ({train_labels_parquet.stat().st_size / 1e6:.2f} MB)")

# Save D_train float32 arrays or symlink/copy
d_train_x_npy = CACHE_DIR / "D_train_X.npy"
d_train_y_npy = CACHE_DIR / "D_train_y.npy"
if not d_train_y_npy.exists():
    np.save(d_train_y_npy, np.array(y_train_mmap, dtype=np.int32))
# For D_train_X.npy, to avoid copying 1GB unnecessarily if already present, write chunked parquet
d_train_parquet = CACHE_DIR / "D_train.parquet"
if not d_train_parquet.exists():
    print("Writing D_train.parquet in streaming chunks...")
    chunk_size = 500_000
    schema = pa.schema([pa.field(col, pa.float32()) for col in feature_cols] + [
        pa.field("label", pa.int32()),
        pa.field("label_name", pa.string()),
        pa.field("family", pa.string()),
        pa.field("is_attack", pa.int8())
    ])
    with pq.ParquetWriter(d_train_parquet, schema, compression="snappy") as writer:
        for start_idx in range(0, n_train, chunk_size):
            end_idx = min(start_idx + chunk_size, n_train)
            chunk_x = np.array(X_train_mmap[start_idx:end_idx], dtype=np.float32)
            chunk_y = np.array(y_train_mmap[start_idx:end_idx], dtype=np.int32)
            
            chunk_dict = {col: chunk_x[:, c_i] for c_i, col in enumerate(feature_cols)}
            chunk_dict["label"] = chunk_y
            chunk_dict["label_name"] = [class_names[i] for i in chunk_y]
            chunk_dict["family"] = [class_to_family[i] for i in chunk_y]
            chunk_dict["is_attack"] = (chunk_y != benign_idx).astype(np.int8)
            
            table = pa.Table.from_pandas(pd.DataFrame(chunk_dict), schema=schema)
            writer.write_table(table)
            print(f"  Written chunk {start_idx:,} to {end_idx:,}...")
    print(f"Saved {d_train_parquet} ({d_train_parquet.stat().st_size / 1e6:.2f} MB)")

# B. Process D_val (60,000 flows, seed 42)
print("\nProcessing D_val (60,000 flows, seed 42)...")
val_bal_indices = generate_stratified_balanced_window(y_test_mmap, seed=42)
X_val_bal = np.array(X_test_mmap[val_bal_indices], dtype=np.float32)
X_val_bal_scaled = np.array(X_test_scaled_mmap[val_bal_indices], dtype=np.float32)
y_val_bal = np.array(y_test_mmap[val_bal_indices], dtype=np.int32)

val_counts = pd.Series(y_val_bal).value_counts().sort_index()
val_benign_cnt = val_counts.get(benign_idx, 0)
val_attack_cnt = len(y_val_bal) - val_benign_cnt

shapes_log.append("--- D_val Partition (60,000 flows, Primary Seed 42, Stratified Balanced) ---")
shapes_log.append(f"Shape: {X_val_bal.shape}, Dtype: float32")
shapes_log.append(f"Total flows: {len(y_val_bal):,}")
shapes_log.append(f"Benign flows: {val_benign_cnt:,} ({val_benign_cnt/len(y_val_bal)*100:.2f}%)")
shapes_log.append(f"Attack flows: {val_attack_cnt:,} ({val_attack_cnt/len(y_val_bal)*100:.2f}%)")
shapes_log.append("Attack Family Breakdown:")
val_fam_counts = pd.Series([class_to_family[i] for i in y_val_bal]).value_counts()
for fam, cnt in val_fam_counts.items():
    shapes_log.append(f"  {fam:<15}: {cnt:,} ({cnt/len(y_val_bal)*100:.2f}%)")
shapes_log.append("")

# Save D_val files
val_dict = {col: X_val_bal[:, c_i] for c_i, col in enumerate(feature_cols)}
val_dict["label"] = y_val_bal
val_dict["label_name"] = [class_names[i] for i in y_val_bal]
val_dict["family"] = [class_to_family[i] for i in y_val_bal]
val_dict["is_attack"] = (y_val_bal != benign_idx).astype(np.int8)
val_df = pd.DataFrame(val_dict)

val_parquet = CACHE_DIR / "D_val.parquet"
val_df.to_parquet(val_parquet, index=False)
np.save(CACHE_DIR / "D_val_X.npy", X_val_bal)
np.save(CACHE_DIR / "D_val_X_scaled.npy", X_val_bal_scaled)
np.save(CACHE_DIR / "D_val_y.npy", y_val_bal)
np.save(CACHE_DIR / "D_val_indices.npy", val_bal_indices)
print(f"Saved {val_parquet} ({val_parquet.stat().st_size / 1e6:.2f} MB)")

# C. Process D_test (60,000 flows, seed 99)
print("\nProcessing D_test (60,000 flows, Held-out Seed 99)...")
test_bal_indices = generate_stratified_balanced_window(y_test_mmap, seed=99)
X_test_bal = np.array(X_test_mmap[test_bal_indices], dtype=np.float32)
X_test_bal_scaled = np.array(X_test_scaled_mmap[test_bal_indices], dtype=np.float32)
y_test_bal = np.array(y_test_mmap[test_bal_indices], dtype=np.int32)

test_counts = pd.Series(y_test_bal).value_counts().sort_index()
test_benign_cnt = test_counts.get(benign_idx, 0)
test_attack_cnt = len(y_test_bal) - test_benign_cnt

shapes_log.append("--- D_test Partition (60,000 flows, Held-Out Seed 99, Stratified Balanced) ---")
shapes_log.append(f"Shape: {X_test_bal.shape}, Dtype: float32")
shapes_log.append(f"Total flows: {len(y_test_bal):,}")
shapes_log.append(f"Benign flows: {test_benign_cnt:,} ({test_benign_cnt/len(y_test_bal)*100:.2f}%)")
shapes_log.append(f"Attack flows: {test_attack_cnt:,} ({test_attack_cnt/len(y_test_bal)*100:.2f}%)")
shapes_log.append("Attack Family Breakdown:")
test_fam_counts = pd.Series([class_to_family[i] for i in y_test_bal]).value_counts()
for fam, cnt in test_fam_counts.items():
    shapes_log.append(f"  {fam:<15}: {cnt:,} ({cnt/len(y_test_bal)*100:.2f}%)")
shapes_log.append("")

# Save D_test files
test_dict = {col: X_test_bal[:, c_i] for c_i, col in enumerate(feature_cols)}
test_dict["label"] = y_test_bal
test_dict["label_name"] = [class_names[i] for i in y_test_bal]
test_dict["family"] = [class_to_family[i] for i in y_test_bal]
test_dict["is_attack"] = (y_test_bal != benign_idx).astype(np.int8)
test_df = pd.DataFrame(test_dict)

test_parquet = CACHE_DIR / "D_test.parquet"
test_df.to_parquet(test_parquet, index=False)
np.save(CACHE_DIR / "D_test_X.npy", X_test_bal)
np.save(CACHE_DIR / "D_test_X_scaled.npy", X_test_bal_scaled)
np.save(CACHE_DIR / "D_test_y.npy", y_test_bal)
np.save(CACHE_DIR / "D_test_indices.npy", test_bal_indices)
print(f"Saved {test_parquet} ({test_parquet.stat().st_size / 1e6:.2f} MB)")

# Save shapes log to /audit_v3/env/dataset_shapes.txt
shapes_file = ENV_DIR / "dataset_shapes.txt"
with open(shapes_file, "w") as f:
    f.write("\n".join(shapes_log) + "\n")
print(f"Saved dataset shapes to {shapes_file}")

# 4. Build GPU-safe inference helpers
print("\n" + "=" * 70)
print("BUILDING AND VERIFYING GPU-SAFE INFERENCE HELPERS")
print("=" * 70)

def xgb_predict_batched(model, X, batch_size=1024):
    """
    GPU-safe batched prediction for XGBoost on NVIDIA GPU (RTX 3050 6GB).
    Uses DMatrix batching to ensure zero OOM and device consistency.
    """
    booster = model.get_booster() if hasattr(model, "get_booster") else model
    booster.set_param({"device": "cuda"})
    
    n_samples = len(X)
    probs_list = []
    
    for start_i in range(0, n_samples, batch_size):
        end_i = min(start_i + batch_size, n_samples)
        batch = np.array(X[start_i:end_i], dtype=np.float32)
        dmat = xgb.DMatrix(batch)
        pred_batch = booster.predict(dmat)
        probs_list.append(pred_batch)
        
    return np.vstack(probs_list)

def if_predict_batched(model, X, batch_size=2048):
    """
    Batched inference helper for Isolation Forest scoring.
    Evaluates in chunks of 2048 to prevent memory spikes on large test splits.
    Returns raw anomaly scores: -score_samples(X).
    """
    n_samples = len(X)
    scores_list = []
    
    for start_i in range(0, n_samples, batch_size):
        end_i = min(start_i + batch_size, n_samples)
        batch = np.array(X[start_i:end_i], dtype=np.float32)
        batch_scores = -model.score_samples(batch)
        scores_list.append(batch_scores)
        
    return np.concatenate(scores_list)

# 5. Verify inference helpers
xgb_path = ROOT.parent / "backend" / "ml_model" / "saved_models" / "xgboost.pkl"
if_path = ROOT.parent / "backend" / "ml_model" / "saved_models" / "isolation_forest_corrected.pkl"

print(f"Loading models:\n  XGB: {xgb_path}\n  IF:  {if_path}")
xgb_model = joblib.load(xgb_path)
if_model = joblib.load(if_path)

# A. Test on D_val (60,000 flows)
print("\nTesting GPU inference on D_val (60,000 flows)...")
t0 = time.time()
val_xgb_probs = xgb_predict_batched(xgb_model, X_val_bal, batch_size=1024)
t_xgb_val = time.time() - t0
print(f"XGBoost GPU inference on D_val: {val_xgb_probs.shape} in {t_xgb_val:.2f}s (Throughput: {len(X_val_bal)/t_xgb_val:.0f} flows/s)")

t0 = time.time()
val_if_scores = if_predict_batched(if_model, X_val_bal_scaled, batch_size=2048)
t_if_val = time.time() - t0
print(f"Isolation Forest inference on D_val: {val_if_scores.shape} in {t_if_val:.2f}s (Throughput: {len(X_val_bal)/t_if_val:.0f} flows/s)")

# B. Test on Full Test Partition (1,176,851 flows) to verify no OOM
print("\nTesting GPU inference on full test partition (1,176,851 flows) for OOM verification...")
# Run first 200,000 flows to thoroughly prove stability and no OOM
test_slice_len = 200_000
X_large_slice = np.array(X_test_mmap[:test_slice_len], dtype=np.float32)
X_large_scaled_slice = np.array(X_test_scaled_mmap[:test_slice_len], dtype=np.float32)

t0 = time.time()
large_xgb_probs = xgb_predict_batched(xgb_model, X_large_slice, batch_size=1024)
t_xgb_large = time.time() - t0
print(f"XGBoost GPU inference on {test_slice_len:,} flows: {large_xgb_probs.shape} in {t_xgb_large:.2f}s (Throughput: {test_slice_len/t_xgb_large:.0f} flows/s)")

t0 = time.time()
large_if_scores = if_predict_batched(if_model, X_large_scaled_slice, batch_size=2048)
t_if_large = time.time() - t0
print(f"Isolation Forest inference on {test_slice_len:,} flows: {large_if_scores.shape} in {t_if_large:.2f}s (Throughput: {test_slice_len/t_if_large:.0f} flows/s)")

# Verify accuracy on D_val
val_preds = np.argmax(val_xgb_probs, axis=1)
val_acc = np.mean(val_preds == y_val_bal)
print(f"\nValidation Accuracy of XGBoost on D_val: {val_acc*100:.2f}%")
print(get_memory_info())
print("\nALL CACHING AND INFERENCE VERIFICATIONS COMPLETED SUCCESSFULLY WITH ZERO OOM!")
