import numpy as np
import joblib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

X_val_scaled = np.load(ROOT / "audit" / "lofo" / "cache" / "X_val_scaled.npy", mmap_mode="r")
y_val = np.load(ROOT / "audit" / "lofo" / "cache" / "y_val.npy")
if_path = ROOT / "backend" / "ml_model" / "saved_models" / "isolation_forest.pkl"
iforest = joblib.load(if_path)

ben_idx = np.where(y_val == 1)[0][:1000]
atk_idx = np.where(y_val != 1)[0][:1000]

raw_ben = iforest.score_samples(X_val_scaled[ben_idx])
raw_atk = iforest.score_samples(X_val_scaled[atk_idx])

print("Raw IF score_samples on Benign: mean =", raw_ben.mean(), "min =", raw_ben.min(), "max =", raw_ben.max())
print("Raw IF score_samples on Attack: mean =", raw_atk.mean(), "min =", raw_atk.min(), "max =", raw_atk.max())
print("Normalised anom (0.5 - raw) on Benign: mean =", np.clip(0.5 - raw_ben, 0, 1).mean())
print("Normalised anom (0.5 - raw) on Attack: mean =", np.clip(0.5 - raw_atk, 0, 1).mean())
