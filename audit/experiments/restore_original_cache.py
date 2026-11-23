import numpy as np
import joblib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "audit"))
from topology_loader import load_tarp_risks
from trust_loader import compute_dynamic_trust_all

# Load original scratch
orig = np.load(ROOT / "audit" / "scratch_60k_eval.npz")
indices = orig["indices"]
y_sub = orig["y_sub"]
conf = orig["conf"]
anom = orig["anom"]
orig_preds = orig["preds"]

print(f"Original indices: shape={indices.shape}, min={indices.min()}, max={indices.max()}")
print(f"Original y_sub:   total={len(y_sub):,}, benign={(y_sub==1).sum():,} ({(y_sub==1).mean()*100:.2f}%), attack={(y_sub!=1).sum():,} ({(y_sub!=1).mean()*100:.2f}%)")
print(f"Original anom:    mean={anom.mean():.4f}, std={anom.std():.4f}, min={anom.min():.4f}, max={anom.max():.4f}, %>=0.90={(anom>=0.90).mean()*100:.2f}%")
print(f"Original conf:    mean={conf.mean():.4f}, std={conf.std():.4f}, min={conf.min():.4f}, max={conf.max():.4f}")

# XGBoost predictions on original indices
X_test = np.load(ROOT / "audit" / "lofo" / "cache" / "X_test.npy", mmap_mode="r")
xgb = joblib.load(ROOT / "backend" / "ml_model" / "saved_models" / "xgboost.pkl")
preds = xgb.predict(X_test[indices])

# TARP risks (600 entities x 100 samples)
tarp, _ = load_tarp_risks(n_samples=60000, chunk_size=100)

# Dynamic trust update
is_atk_pred = (preds != 1)
trust, _ = compute_dynamic_trust_all(anom, is_atk_pred, tarp, n_entities=600, chunk_size=100)

# Save to scratch_60k_eval_fixed.npz
fixed_path = ROOT / "audit" / "scratch_60k_eval_fixed.npz"
np.savez(
    fixed_path,
    indices=indices,
    y_sub=y_sub,
    preds=preds,
    conf=conf,
    anom=anom,
    tarp=tarp,
    trust=trust
)
print(f"\nRESTORED {fixed_path} successfully!")
print(f"  indices match: {(indices == orig['indices']).all()}")
print(f"  y_sub match:   {(y_sub == orig['y_sub']).all()}")
print(f"  anom match:    {(anom == orig['anom']).all()}")
print(f"  conf match:    {(conf == orig['conf']).all()}")
