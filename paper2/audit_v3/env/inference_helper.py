# audit_v3/env/inference_helper.py
"""
GPU-Safe Batched Inference Helpers for Audit Experiments.
Optimized for NVIDIA RTX 3050 6GB VRAM.
Ensures zero CUDA OOM and strict device consistency.
"""
import numpy as np
import xgboost as xgb

def xgb_predict_batched(model, X, batch_size=1024):
    """
    GPU-safe batched prediction for XGBoost on CUDA.
    
    Args:
        model: XGBClassifier or Booster object
        X: numpy array of shape (N, 46) or feature matrix
        batch_size: chunk size for GPU DMatrix transfer (default: 1024)
        
    Returns:
        numpy.ndarray of shape (N, num_classes) containing predicted class probabilities.
    """
    booster = model.get_booster() if hasattr(model, "get_booster") else model
    booster.set_param({"device": "cuda"})
    
    n_samples = len(X)
    probs_list = []
    
    for start_i in range(0, n_samples, batch_size):
        end_i = min(start_i + batch_size, n_samples)
        batch = np.ascontiguousarray(X[start_i:end_i], dtype=np.float32)
        dmat = xgb.DMatrix(batch)
        pred_batch = booster.predict(dmat)
        probs_list.append(pred_batch)
        
    return np.vstack(probs_list)

def if_predict_batched(model, X, batch_size=2048):
    """
    Batched inference helper for Isolation Forest anomaly scoring.
    Evaluates in chunks of 2048 to prevent memory spikes on large datasets.
    
    Args:
        model: IsolationForest model object
        X: numpy array of shape (N, 46)
        batch_size: chunk size for evaluation (default: 2048)
        
    Returns:
        numpy.ndarray of shape (N,) containing raw anomaly scores: -score_samples(X)
    """
    n_samples = len(X)
    scores_list = []
    
    for start_i in range(0, n_samples, batch_size):
        end_i = min(start_i + batch_size, n_samples)
        batch = np.ascontiguousarray(X[start_i:end_i], dtype=np.float32)
        batch_scores = -model.score_samples(batch)
        scores_list.append(batch_scores)
        
    return np.concatenate(scores_list)
