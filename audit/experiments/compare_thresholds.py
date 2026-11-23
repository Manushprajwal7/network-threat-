import numpy as np

d = np.load("audit/scratch_60k_eval_fixed.npz")
anom = d["anom"].reshape(600, 100)
conf = d["conf"].reshape(600, 100)
preds = d["preds"].reshape(600, 100)
tarp = d["tarp"].reshape(600, 100)[:, 0]
trust = d["trust"].reshape(600, 100)
y_sub = d["y_sub"].reshape(600, 100)

is_benign = (y_sub == 1)
is_atk_pred = (preds != 1)

total_benign = is_benign.sum()
print(f"Total true benign in 60k: {total_benign} ({total_benign/60000*100:.2f}%)")

def compute_table(a_rate, c_rate, name=""):
    c_topo = (tarp >= 0.42).astype(int)
    c_trust = (trust.min(axis=1) <= 60.0).astype(int)
    c_anom = ((anom >= 0.90).mean(axis=1) >= a_rate).astype(int)
    c_conf = (((conf >= 0.95) & is_atk_pred).mean(axis=1) >= c_rate).astype(int)
    
    S = c_topo + c_trust + c_anom + c_conf
    
    lvl = np.zeros(600, dtype=int)
    for e in range(600):
        if S[e] >= 3: lvl[e] = 3
        elif S[e] == 2: lvl[e] = 2
        elif S[e] == 1: lvl[e] = 1
        else: lvl[e] = 0
        
    print(f"\n--- {name} (anom_rate={a_rate}, conf_rate={c_rate}) ---")
    cum_benign_escalated = 0
    for l in range(4):
        mask_e = (lvl == l)
        cnt_e = mask_e.sum()
        cnt_s = cnt_e * 100
        share = cnt_e / 600.0 * 100.0
        
        # Benign stats
        benign_cnt = is_benign[mask_e].sum()
        pct_benign = (benign_cnt / cnt_s * 100.0) if cnt_s > 0 else 0.0
        
        # FPR of benign: fraction of total benign that reached this level
        benign_share_of_all = (benign_cnt / total_benign * 100.0)
        
        m_t = tarp[mask_e].mean() if cnt_e > 0 else 0
        m_tr = trust.mean(axis=1)[mask_e].mean() if cnt_e > 0 else 0
        m_a = anom.mean(axis=1)[mask_e].mean() if cnt_e > 0 else 0
        
        print(f"L{l}: Entities={cnt_e:<3} ({share:5.1f}%) | TARP={m_t:.4f} | Trust={m_tr:.2f} | Anom={m_a:.4f} | Benign={benign_cnt:<4} ({pct_benign:.2f}% of level, {benign_share_of_all:.1f}% of all benign)")

compute_table(0.28, 0.26, "Current Formulation (0.28 / 0.26)")
compute_table(0.50, 0.50, "Majority Rule (0.50 / 0.50)")
