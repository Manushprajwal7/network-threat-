"""
Leave-One-Family-Out (LOFO) evaluation of Isolation Forest unknown-threat
detection on CICIoT2023, replacing the manuscript's single-split 679-unknown
result (Table 17).

Reads only from audit/lofo/cache/ (base preprocessed arrays, cached once from
an unmodified run of backend/ml_model/preprocess_ciciot2023.py) and from the
existing, unmodified backend/ml_model/saved_models/xgboost.pkl.

Writes only under audit/lofo/. Does not touch saved_models/, does not retrain
XGBoost, does not refit scaler/clip bounds/label encoder, does not retune
Isolation Forest hyperparameters or the anomaly decision boundary per fold.

Run from repo root:
    python audit/lofo/run_lofo.py
"""

import json
import time
from pathlib import Path

import numpy as np
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = REPO_ROOT / "audit" / "lofo" / "cache"
MODELS_DIR = REPO_ROOT / "audit" / "lofo" / "models"
OUT_DIR = REPO_ROOT / "audit" / "lofo"
XGB_PATH = REPO_ROOT / "backend" / "ml_model" / "saved_models" / "xgboost.pkl"

CONFIDENCE_THRESHOLD = 0.60

IF_PARAMS = dict(
    n_estimators=200,
    contamination=0.05,
    random_state=42,
    n_jobs=-1,
    bootstrap=False,
    max_features=1.0,
    max_samples="auto",
)

FAMILIES = {
    "F1": ("DDoS", [
        "DDoS-ACK_Fragmentation", "DDoS-HTTP_Flood", "DDoS-ICMP_Flood",
        "DDoS-ICMP_Fragmentation", "DDoS-PSHACK_Flood", "DDoS-RSTFINFlood",
        "DDoS-SYN_Flood", "DDoS-SlowLoris", "DDoS-SynonymousIP_Flood",
        "DDoS-TCP_Flood", "DDoS-UDP_Flood", "DDoS-UDP_Fragmentation",
    ]),
    "F2": ("DoS", ["DoS-HTTP_Flood", "DoS-SYN_Flood", "DoS-TCP_Flood", "DoS-UDP_Flood"]),
    "F3": ("Mirai", ["Mirai-greeth_flood", "Mirai-greip_flood", "Mirai-udpplain"]),
    "F4": ("Recon", [
        "Recon-HostDiscovery", "Recon-OSScan", "Recon-PingSweep",
        "Recon-PortScan", "VulnerabilityScan",
    ]),
    "F5": ("Web", [
        "SqlInjection", "XSS", "CommandInjection", "BrowserHijacking",
        "Uploading_Attack", "Backdoor_Malware",
    ]),
    "F6": ("Spoofing", ["DNS_Spoofing", "MITM-ArpSpoofing"]),
    "F7": ("BruteForce", ["DictionaryBruteForce"]),
}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def safe_div(a, b):
    return a / b if b else 0.0


def binary_confusion(pred_unknown_flags_on_unknown, pred_unknown_flags_on_known):
    tp = int(np.sum(pred_unknown_flags_on_unknown))
    fn = int(len(pred_unknown_flags_on_unknown) - tp)
    fp = int(np.sum(pred_unknown_flags_on_known))
    tn = int(len(pred_unknown_flags_on_known) - fp)
    utdr = safe_div(tp, tp + fn)
    precision = safe_div(tp, tp + fp)
    f1 = safe_div(2 * precision * utdr, precision + utdr) if (precision + utdr) else 0.0
    fpr = safe_div(fp, fp + tn)
    return {
        "TP": tp, "FN": fn, "FP": fp, "TN": tn,
        "UTDR": utdr, "precision": precision, "F1": f1, "FPR": fpr,
    }


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    log("Loading base cached arrays...")
    X_train = np.load(CACHE_DIR / "X_train.npy")
    X_train_scaled = np.load(CACHE_DIR / "X_train_scaled.npy")
    y_train = np.load(CACHE_DIR / "y_train.npy")
    X_test = np.load(CACHE_DIR / "X_test.npy")
    X_test_scaled = np.load(CACHE_DIR / "X_test_scaled.npy")
    y_test = np.load(CACHE_DIR / "y_test.npy")
    class_names = json.loads((CACHE_DIR / "class_names.json").read_text())
    name_to_idx = {n: i for i, n in enumerate(class_names)}
    log(f"Loaded. X_train={X_train.shape} X_test={X_test.shape}")

    log(f"Loading fixed XGBoost model from {XGB_PATH} ...")
    if not XGB_PATH.exists():
        raise SystemExit(f"FATAL: XGBoost model not found at {XGB_PATH}. Stopping — no fallback.")
    xgb = joblib.load(XGB_PATH)
    log("XGBoost loaded.")

    per_fold_rows = []
    per_class_rows = []
    fold_failures = []

    for fk, (family_name, members) in FAMILIES.items():
        log(f"=== Fold {fk} ({family_name}) ===")
        try:
            member_idx = [name_to_idx[m] for m in members]

            train_mask = ~np.isin(y_train, member_idx)
            test_unknown_mask = np.isin(y_test, member_idx)
            test_known_mask = ~test_unknown_mask

            X_train_fold = X_train_scaled[train_mask]
            X_test_unknown_scaled = X_test_scaled[test_unknown_mask]
            X_test_unknown_unscaled = X_test[test_unknown_mask]
            X_test_known_scaled = X_test_scaled[test_known_mask]
            X_test_known_unscaled = X_test[test_known_mask]
            y_test_unknown = y_test[test_unknown_mask]

            n_train = X_train_fold.shape[0]
            n_unknown = X_test_unknown_scaled.shape[0]
            n_known = X_test_known_scaled.shape[0]

            if n_unknown == 0:
                fold_failures.append(f"{fk}: zero test-unknown samples — fold excluded from aggregate")
                log(f"  FAILURE: {fk} has zero test-unknown samples. Skipping fold.")
                continue

            log(f"  Training samples: {n_train:,} | test-unknown: {n_unknown:,} | test-known: {n_known:,}")

            t0 = time.perf_counter()
            iforest = IsolationForest(**IF_PARAMS)
            iforest.fit(X_train_fold)
            train_time = time.perf_counter() - t0

            if iforest.offset_ is None or np.isnan(iforest.offset_):
                fold_failures.append(f"{fk}: Isolation Forest offset_ is NaN/None — invalid fit")
                log(f"  FAILURE: {fk} offset_ invalid ({iforest.offset_}). Skipping fold.")
                continue

            model_path = MODELS_DIR / f"if_fold_{fk}.pkl"
            joblib.dump(iforest, model_path)

            log(f"  Trained in {train_time:.2f}s. offset_={iforest.offset_:.6f} (valid). Saved -> {model_path.name}")

            # --- Method A: Isolation Forest alone ---
            if_pred_unknown = iforest.predict(X_test_unknown_scaled)
            if_pred_known = iforest.predict(X_test_known_scaled)
            flags_unknown_A = (if_pred_unknown == -1)
            flags_known_A = (if_pred_known == -1)
            metrics_A = binary_confusion(flags_unknown_A, flags_known_A)

            # --- Method B: Hybrid XGBoost confidence OR Isolation Forest ---
            proba_unknown = xgb.predict_proba(X_test_unknown_unscaled)
            proba_known = xgb.predict_proba(X_test_known_unscaled)
            conf_unknown = proba_unknown.max(axis=1)
            conf_known = proba_known.max(axis=1)
            flags_unknown_B = (conf_unknown < CONFIDENCE_THRESHOLD) | flags_unknown_A
            flags_known_B = (conf_known < CONFIDENCE_THRESHOLD) | flags_known_A
            metrics_B = binary_confusion(flags_unknown_B, flags_known_B)

            for method_name, m, flags_unknown in [
                ("IsolationForest_alone", metrics_A, flags_unknown_A),
                ("Hybrid_XGB_confidence_OR_IF", metrics_B, flags_unknown_B),
            ]:
                if m["TP"] == 0:
                    log(f"  NOTE: {fk} method={method_name} produced ZERO true positives (TP=0).")

                per_fold_rows.append({
                    "fold_id": fk,
                    "family": family_name,
                    "method": method_name,
                    "UTDR": round(m["UTDR"], 4),
                    "precision": round(m["precision"], 4),
                    "F1": round(m["F1"], 4),
                    "FPR": round(m["FPR"], 4),
                    "TP": m["TP"], "FP": m["FP"], "FN": m["FN"], "TN": m["TN"],
                    "known_samples": n_known,
                    "unknown_samples": n_unknown,
                    "benign_samples_in_known": int(np.sum(y_test[test_known_mask] == name_to_idx["BenignTraffic"])),
                })

                # Per-class breakdown within this fold's held-out family
                for cls in members:
                    cls_idx = name_to_idx[cls]
                    cls_mask_in_unknown = (y_test_unknown == cls_idx)
                    n_cls = int(np.sum(cls_mask_in_unknown))
                    if n_cls == 0:
                        correctly_flagged = 0
                        flag_rate = 0.0
                    else:
                        correctly_flagged = int(np.sum(flags_unknown[cls_mask_in_unknown]))
                        flag_rate = round(safe_div(correctly_flagged, n_cls), 4)
                    per_class_rows.append({
                        "fold_id": fk,
                        "family": family_name,
                        "class_name": cls,
                        "method": method_name,
                        "n_samples": n_cls,
                        "correctly_flagged": correctly_flagged,
                        "flag_rate": flag_rate,
                    })

            log(f"  Method A (IF alone):  UTDR={metrics_A['UTDR']:.4f} P={metrics_A['precision']:.4f} F1={metrics_A['F1']:.4f} FPR={metrics_A['FPR']:.4f}")
            log(f"  Method B (Hybrid):    UTDR={metrics_B['UTDR']:.4f} P={metrics_B['precision']:.4f} F1={metrics_B['F1']:.4f} FPR={metrics_B['FPR']:.4f}")

        except Exception as e:
            fold_failures.append(f"{fk}: EXCEPTION during processing — {type(e).__name__}: {e}")
            log(f"  FAILURE: {fk} raised {type(e).__name__}: {e}")
            continue

    if fold_failures:
        log("=== FOLD FAILURES DETECTED ===")
        for f in fold_failures:
            log(f"  {f}")

    # ---------------- Aggregation ----------------
    per_fold_df = pd.DataFrame(per_fold_rows)
    per_fold_df.to_csv(OUT_DIR / "per_fold_metrics.csv", index=False)
    log(f"Wrote per_fold_metrics.csv ({len(per_fold_df)} rows)")

    per_class_df = pd.DataFrame(per_class_rows)
    per_class_df.to_csv(OUT_DIR / "per_class_breakdown.csv", index=False)
    log(f"Wrote per_class_breakdown.csv ({len(per_class_df)} rows)")

    agg_rows = []
    for method_name in per_fold_df["method"].unique():
        sub = per_fold_df[per_fold_df["method"] == method_name]

        # Macro: mean/std/min/max of per-fold metric values
        macro = {"method": method_name, "aggregation": "macro"}
        for metric in ["UTDR", "precision", "F1", "FPR"]:
            vals = sub[metric].values.astype(float)
            macro[f"{metric}_mean"] = round(float(np.mean(vals)), 4)
            macro[f"{metric}_std"] = round(float(np.std(vals, ddof=0)), 4)
            macro[f"{metric}_min"] = round(float(np.min(vals)), 4)
            macro[f"{metric}_max"] = round(float(np.max(vals)), 4)
        agg_rows.append(macro)

        # Micro: pool TP/FP/FN/TN across folds, compute one point estimate.
        # This is a single pooled number, not a distribution over folds —
        # std/min/max are reported equal to the pooled value itself (std=0)
        # to satisfy the required schema without fabricating fold-to-fold
        # variance that does not exist for a pooled statistic.
        tp = int(sub["TP"].sum()); fp = int(sub["FP"].sum())
        fn = int(sub["FN"].sum()); tn = int(sub["TN"].sum())
        m_pooled = binary_confusion(
            np.array([True] * tp + [False] * fn),
            np.array([True] * fp + [False] * tn),
        )
        micro = {"method": method_name, "aggregation": "micro"}
        for metric_key, pooled_key in [("UTDR", "UTDR"), ("precision", "precision"), ("F1", "F1"), ("FPR", "FPR")]:
            v = round(float(m_pooled[pooled_key]), 4)
            micro[f"{metric_key}_mean"] = v
            micro[f"{metric_key}_std"] = 0.0
            micro[f"{metric_key}_min"] = v
            micro[f"{metric_key}_max"] = v
        agg_rows.append(micro)

    agg_df = pd.DataFrame(agg_rows)
    col_order = ["method", "aggregation",
                 "UTDR_mean", "UTDR_std", "UTDR_min", "UTDR_max",
                 "precision_mean", "precision_std", "precision_min", "precision_max",
                 "F1_mean", "F1_std", "F1_min", "F1_max",
                 "FPR_mean", "FPR_std", "FPR_min", "FPR_max"]
    agg_df = agg_df[col_order]
    agg_df.to_csv(OUT_DIR / "aggregate_metrics.csv", index=False)
    log(f"Wrote aggregate_metrics.csv ({len(agg_df)} rows)")

    return per_fold_df, per_class_df, agg_df, fold_failures, class_names, name_to_idx


if __name__ == "__main__":
    main()
