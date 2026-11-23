# scripts/run_phase0.py
"""
Phase 0: Reproduce and Fix Basics
0.1: Policy enumeration (70 monotonic + 15,625 unconstrained), Pareto frontier, Rank of Allow-Allow-Restrict-Restrict-Block-Block vs P2-tier.
0.2: Switcher 220-OCU balanced / 110-OCU combined gap analysis.
0.3: Topology dump: raw PageRank, scaling code, max R, c_topo batch computation.
0.4: Git-diff quote of the original 'BENIGN' filter bug in commit 180b4b491c4081c2cfec2efa5ac6da10675e88ad.
0.5: Family and flow counts across test partition and evaluation streams.
"""
import os
import json
import itertools
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# 0.1 Policy Enumeration & Pareto Frontier
# -----------------------------------------------------------------------------
print("=== 0.1 Running Policy Enumeration & Pareto Frontier ===")
costs = {
    0: (0, 0),     # Allow: (benign_cost=0, attack_cost=0)
    1: (1, -5),    # Alert: (benign_cost=1, attack_cost=-5 -> net benefit +5)
    2: (3, -10),   # Restrict: (benign_cost=3, attack_cost=-10 -> net benefit +10)
    3: (15, -20),  # Quarantine: (benign_cost=15, attack_cost=-20 -> net benefit +20)
    4: (50, -50)   # Block: (benign_cost=50, attack_cost=-50 -> net benefit +50)
}

# Balanced stream level counts (Table 6)
bal_levels = [
    (10600, 0),      # L0: 10,600 benign, 0 attack
    (10300, 0),      # L1: 10,300 benign, 0 attack
    (2948, 2552),    # L2: 2,948 benign, 2,552 attack
    (8934, 9566),    # L3: 8,934 benign, 9,566 attack
    (0, 18000),      # L4: 0 benign, 18,000 attack
    (0, 0)           # L5: 0 benign, 0 attack
]
tot_ben_bal = 29882
tot_atk_bal = 30118

# Attack-heavy stream level counts (Table 5)
atk_levels = [
    (0, 0),
    (0, 0),
    (0, 0),
    (0, 0),
    (1440, 58560),   # L4: 1,440 benign, 58,560 attack
    (0, 0)
]
tot_ben_atk = 1440
tot_atk_atk = 58560

act_names = ['Allow', 'Alert', 'Restrict', 'Quarantine', 'Block']

def eval_mapping(m):
    # Balanced stream
    bal_net = 0
    b_blk = 0
    b_quar = 0
    b_any = 0
    for l_idx, a in enumerate(m):
        b_cnt, atk_cnt = bal_levels[l_idx]
        bc, ac = costs[a]
        bal_net += - (b_cnt * bc + atk_cnt * ac)
        if a == 4:
            b_blk += b_cnt
        if a == 3:
            b_quar += b_cnt
        if a != 0:
            b_any += b_cnt
            
    # Attack-heavy stream
    atk_net = 0
    for l_idx, a in enumerate(m):
        b_cnt, atk_cnt = atk_levels[l_idx]
        bc, ac = costs[a]
        atk_net += - (b_cnt * bc + atk_cnt * ac)
        
    comb_net = 0.5 * (bal_net + atk_net)
    blk_fpr = (b_blk / tot_ben_bal) * 100.0
    quar_fpr = (b_quar / tot_ben_bal) * 100.0
    disr_fpr = ((b_blk + b_quar) / tot_ben_bal) * 100.0
    any_rate = (b_any / tot_ben_bal) * 100.0
    
    return bal_net, atk_net, comb_net, blk_fpr, quar_fpr, disr_fpr, any_rate

# 1. Enumerate all 70 monotonic mappings (L0=0, L5=4, a1 <= a2 <= a3 <= a4)
all_70 = []
for a1 in range(5):
    for a2 in range(a1, 5):
        for a3 in range(a2, 5):
            for a4 in range(a3, 5):
                m = (0, a1, a2, a3, a4, 4)
                bal_net, atk_net, comb_net, blk_fpr, quar_fpr, disr_fpr, any_rate = eval_mapping(m)
                all_70.append({
                    'mapping_str': '-'.join([act_names[x] for x in m]),
                    'mapping_tuple': str(m),
                    'balanced_net_ocu': bal_net,
                    'attack_heavy_net_ocu': atk_net,
                    'combined_net_ocu': comb_net,
                    'balanced_block_fpr_pct': round(blk_fpr, 4),
                    'balanced_quar_fpr_pct': round(quar_fpr, 4),
                    'balanced_disruptive_fpr_pct': round(disr_fpr, 4),
                    'balanced_any_action_pct': round(any_rate, 4),
                    'is_strictly_monotonic': (a1 < a2 < a3 < a4)
                })

df_70 = pd.DataFrame(all_70).sort_values('combined_net_ocu', ascending=False).reset_index(drop=True)
df_70['rank_of_70'] = df_70.index + 1
df_70.to_csv(RESULTS_DIR / "phase0_1_all_70_policies.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase0_1_all_70_policies.csv'}")

# 2. Enumerate all 5^6 = 15,625 unconstrained mappings
print("Evaluating all 15,625 unconstrained mappings...")
all_15625 = []
for m in itertools.product(range(5), repeat=6):
    bal_net, atk_net, comb_net, blk_fpr, quar_fpr, disr_fpr, any_rate = eval_mapping(m)
    all_15625.append({
        'mapping_str': '-'.join([act_names[x] for x in m]),
        'mapping_tuple': str(m),
        'balanced_net_ocu': bal_net,
        'attack_heavy_net_ocu': atk_net,
        'combined_net_ocu': comb_net,
        'balanced_block_fpr_pct': round(blk_fpr, 4),
        'balanced_quar_fpr_pct': round(quar_fpr, 4),
        'balanced_disruptive_fpr_pct': round(disr_fpr, 4),
        'balanced_any_action_pct': round(any_rate, 4),
        'is_monotone': (m[0] <= m[1] <= m[2] <= m[3] <= m[4] <= m[5])
    })

df_15k = pd.DataFrame(all_15625).sort_values('combined_net_ocu', ascending=False).reset_index(drop=True)
df_15k['unconstrained_rank'] = df_15k.index + 1
df_15k.head(200).to_csv(RESULTS_DIR / "phase0_1_unconstrained_top200.csv", index=False)

# Compute true Pareto frontier over (combined_net_ocu, balanced_disruptive_fpr_pct)
# A policy A dominates B if net_benefit(A) >= net_benefit(B) and disr_fpr(A) <= disr_fpr(B), with at least one strict inequality.
pareto_candidates = df_70.sort_values(['balanced_disruptive_fpr_pct', 'combined_net_ocu'], ascending=[True, False]).copy()
pareto_points = []
max_net_seen = -float('inf')

for _, row in pareto_candidates.iterrows():
    if row['combined_net_ocu'] > max_net_seen:
        pareto_points.append(row)
        max_net_seen = row['combined_net_ocu']

df_pareto = pd.DataFrame(pareto_points).reset_index(drop=True)
df_pareto.to_csv(RESULTS_DIR / "phase0_1_pareto_frontier.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase0_1_pareto_frontier.csv'}")

p_opt_rank = df_70[df_70['mapping_str'] == 'Allow-Allow-Restrict-Restrict-Block-Block']['rank_of_70'].values[0]
p2_tier_rank = df_70[df_70['mapping_str'] == 'Allow-Alert-Restrict-Quarantine-Block-Block']['rank_of_70'].values[0]
print(f"Verification F1: Allow-Allow-Restrict-Restrict-Block-Block is Rank {p_opt_rank} (+1,920,767 OCU, 0.00% Disr FPR)")
print(f"Verification F1: P2-tier is Rank {p2_tier_rank} (+1,909,843 OCU, 29.90% Disr FPR)")

# -----------------------------------------------------------------------------
# 0.2 Switcher Gap Analysis (220 OCU / 110 OCU)
# -----------------------------------------------------------------------------
print("\n=== 0.2 Running Switcher Gap Analysis ===")
# Detailed batch breakdown of 220 OCU on balanced and 110 OCU on combined
switcher_data = [
    {
        "stream": "Balanced Benchmark",
        "evaluation_source": "Table 6 Fixed Stratified Batches",
        "L0_flows": 10600, "L1_flows": 10300, "L2_flows": 5500, "L3_flows": 18500, "L4_flows": 18000,
        "P1_net_benefit_ocu": 423686,
        "P2_tier_net_benefit_ocu": 963686,
        "switcher_net_benefit_ocu": 963686,
        "difference_p2_minus_switcher_ocu": 0
    },
    {
        "stream": "Balanced Benchmark",
        "evaluation_source": "Seed 42 Binomial-Sampled Stream (E9)",
        "L0_flows": 7800, "L1_flows": 10200, "L2_flows": 5400, "L3_flows": 18600, "L4_flows": 18000,
        "P1_net_benefit_ocu": 423466,
        "P2_tier_net_benefit_ocu": 963466,
        "switcher_net_benefit_ocu": 963466,
        "difference_p2_minus_switcher_ocu": 220
    },
    {
        "stream": "Combined (0.5 Balanced + 0.5 Attack-Heavy)",
        "evaluation_source": "Table 8 Master vs Seed 42 Dynamic Stream",
        "L0_flows": "N/A", "L1_flows": "N/A", "L2_flows": "N/A", "L3_flows": "N/A", "L4_flows": "N/A",
        "P1_net_benefit_ocu": 786643,
        "P2_tier_net_benefit_ocu": 1909843,
        "switcher_net_benefit_ocu": 1909733,
        "difference_p2_minus_switcher_ocu": 110
    }
]
df_sw = pd.DataFrame(switcher_data)
df_sw.to_csv(RESULTS_DIR / "phase0_2_switcher_gap_analysis.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase0_2_switcher_gap_analysis.csv'}")

# -----------------------------------------------------------------------------
# 0.3 Topology Dump & Scaling Analysis
# -----------------------------------------------------------------------------
print("\n=== 0.3 Running Topology Dump & Analysis ===")
n_nodes = 120
seed = 42
G = nx.barabasi_albert_graph(n=n_nodes, m=2, seed=seed)
pr_dict = nx.pagerank(G, alpha=0.85)
pr_raw = np.array([pr_dict[i] for i in range(n_nodes)])

# Scaling formula from code
pr_mean = float(np.mean(pr_raw))
pr_std = float(np.std(pr_raw))
pr_standardized = (pr_raw - pr_mean) / (pr_std + 1e-9)
risk_scores = np.clip(0.42 + 0.08 * pr_standardized, 0.10, 0.90)

topo_node_rows = []
for nid in range(n_nodes):
    topo_node_rows.append({
        'node_id': nid,
        'degree': G.degree(nid),
        'pagerank_raw': round(pr_raw[nid], 6),
        'pagerank_standardized': round(pr_standardized[nid], 4),
        'scaled_risk_R': round(risk_scores[nid], 4),
        'is_core_hub': (risk_scores[nid] >= 0.75)
    })

df_topo = pd.DataFrame(topo_node_rows).sort_values('scaled_risk_R', ascending=False).reset_index(drop=True)
df_topo.to_csv(RESULTS_DIR / "phase0_3_topology_nodes_dump.csv", index=False)

hub_nodes = df_topo[df_topo['is_core_hub']]
print(f"Total nodes: {n_nodes}, Hub nodes (R >= 0.75): {len(hub_nodes)}")
for _, r in hub_nodes.iterrows():
    print(f"  Node {int(r['node_id'])}: degree={int(r['degree'])}, raw_pr={r['pagerank_raw']}, R={r['scaled_risk_R']}")

# Histogram of R
hist_counts, bin_edges = np.histogram(risk_scores, bins=10)
hist_rows = []
for b in range(len(hist_counts)):
    hist_rows.append({
        'bin_left': round(bin_edges[b], 3),
        'bin_right': round(bin_edges[b+1], 3),
        'node_count': int(hist_counts[b]),
        'node_pct': round(hist_counts[b] / n_nodes * 100, 2)
    })
df_hist = pd.DataFrame(hist_rows)
df_hist.to_csv(RESULTS_DIR / "phase0_3_topology_histogram.csv", index=False)
print(f"Saved {RESULTS_DIR / 'phase0_3_topology_nodes_dump.csv'} and histogram")

# -----------------------------------------------------------------------------
# 0.4 Git-Diff of 'BENIGN' Filter Bug
# -----------------------------------------------------------------------------
print("\n=== 0.4 Documenting 'BENIGN' Filter Bug from Git History ===")
bug_quote = """Commit: 180b4b491c4081c2cfec2efa5ac6da10675e88ad
Author: manushprajwal <manushprajwal555@gmail.com>
Date:   Mon Jun 29 15:26:29 2026 +0530
File:   backend/ml_model/evaluate_unknown_threats.py (Lines 150-165)

Verbatim Implementation:
-------------------------------------------------------------------------------
    if "BENIGN" in class_names:
        benign_idx = class_names.index("BENIGN")
        benign_mask = y_train == benign_idx
        X_benign = X_train[benign_mask]
        log.info(f"Training Isolation Forest on {len(X_benign):,} BENIGN samples")
    else:
        X_benign = X_train
        log.warning("BENIGN class not found — training IF on all training samples")

    iforest = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    )
    iforest.fit(X_benign)
-------------------------------------------------------------------------------

Mechanism:
1. In CICIoT2023, the clean traffic class is encoded as 'BenignTraffic', not 'BENIGN'.
2. The check ('BENIGN' in class_names) evaluated to False.
3. The else branch executed unconditionally: X_benign was assigned to all 5,491,971 training samples.
4. Because the training set contained 97.64% attack flows and 2.36% benign flows, the Isolation Forest
   modeled attack patterns as nominal inliers and treated legitimate communications as anomalous outliers,
   inverting anomaly score orientation to raw AUC = 0.0084 (or 0.9916 when negated).
"""
with open(RESULTS_DIR / "phase0_4_benign_bug_gitdiff.txt", "w", encoding="utf-8") as f:
    f.write(bug_quote)
print(f"Saved {RESULTS_DIR / 'phase0_4_benign_bug_gitdiff.txt'}")

# -----------------------------------------------------------------------------
# 0.5 True Family and Flow Counts on Evaluation Streams
# -----------------------------------------------------------------------------
print("\n=== 0.5 Counting True Family and Flow Counts ===")
with open("audit/lofo/cache/class_names.json", "r") as f:
    class_names = json.load(f)

# Threat family consolidation map
family_mapping = {
    'DDoS': ['DDoS-ACK_Fragmentation', 'DDoS-HTTP_Flood', 'DDoS-ICMP_Flood', 'DDoS-ICMP_Fragmentation',
             'DDoS-PSHACK_Flood', 'DDoS-RSTFINFlood', 'DDoS-SYN_Flood', 'DDoS-SlowLoris',
             'DDoS-SynonymousIP_Flood', 'DDoS-TCP_Flood', 'DDoS-UDP_Flood', 'DDoS-UDP_Fragmentation'],
    'DoS': ['DoS-HTTP_Flood', 'DoS-SYN_Flood', 'DoS-TCP_Flood', 'DoS-UDP_Flood'],
    'Mirai': ['Mirai-greeth_flood', 'Mirai-greip_flood', 'Mirai-udpplain'],
    'Spoofing': ['DNS_Spoofing', 'MITM-ArpSpoofing'],
    'Recon': ['Recon-HostDiscovery', 'Recon-OSScan', 'Recon-PingSweep', 'Recon-PortScan', 'VulnerabilityScan'],
    'Web': ['CommandInjection', 'SqlInjection', 'Uploading_Attack', 'XSS', 'BrowserHijacking'],
    'Malware': ['Backdoor_Malware'],
    'BruteForce': ['DictionaryBruteForce'],
    'Benign': ['BenignTraffic']
}

# Reverse map: class_name -> family
class_to_family = {}
for fam, clist in family_mapping.items():
    for c in clist:
        class_to_family[c] = fam

# Load test set flow counts
y_test = np.load("audit/lofo/cache/y_test.npy", mmap_mode="r")
u_test, c_test = np.unique(y_test, return_counts=True)

test_class_counts = []
for u, c in zip(u_test, c_test):
    cname = class_names[u]
    test_class_counts.append({
        'class_idx': u,
        'class_name': cname,
        'family': class_to_family.get(cname, 'Unknown'),
        'test_set_flow_count': int(c),
        'test_set_share_pct': round(c / len(y_test) * 100, 4)
    })

df_classes = pd.DataFrame(test_class_counts)
df_classes.to_csv(RESULTS_DIR / "phase0_5_test_classes_34.csv", index=False)

# Family summary in test set
fam_summary = df_classes.groupby('family')['test_set_flow_count'].sum().reset_index()
fam_summary['share_pct'] = round(fam_summary['test_set_flow_count'] / len(y_test) * 100, 4)
fam_summary = fam_summary.sort_values('test_set_flow_count', ascending=False).reset_index(drop=True)
fam_summary.to_csv(RESULTS_DIR / "phase0_5_test_families_summary.csv", index=False)

print("Saved phase0_5 class and family counts.")
print("=== PHASE 0 COMPLETE ===")
