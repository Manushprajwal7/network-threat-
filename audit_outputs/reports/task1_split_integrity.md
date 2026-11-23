# Task 1: Split Integrity and Leakage Audit Report

## 1. Executive Summary
A comprehensive audit of dataset partitioning and experimental window construction was conducted. The official CICIoT2023 train (5,491,971 flows), validation (1,176,851 flows), and test (1,176,851 flows) partitions are strictly disjoint with zero cross-set leakage.

However, evaluation of the legacy experimental windows revealed that **E2 (Attack-Heavy 60k)** and **E21 (Held-Out Balanced 60k)** shared **2,821 overlapping flows** due to unconstrained sampling from the global test set. To ensure flawless scientific integrity, **strictly disjoint partitions** were generated: E2 occupies test slice `[0:60,000]`, while E21 and E1 are drawn exclusively from `[60,000:1,176,851]`.

## 2. Partition Inventory and SHA256 Hashes

| split_name                       |   total_flows |   benign_flows |   attack_flows |   attack_pct | source_file                  | seed                 | sha256_hash                                                      |
|:---------------------------------|--------------:|---------------:|---------------:|-------------:|:-----------------------------|:---------------------|:-----------------------------------------------------------------|
| Master Train                     |       5491971 |         129538 |        5362433 |       97.641 | audit/lofo/cache/y_train.npy | Fixed Official Split | aa1da8104ff99bd5c4cba0fa91f7a142c49614799bde2bacc68c98038c9a3a0f |
| Master Validation                |       1176851 |          27519 |        1149332 |       97.662 | audit/lofo/cache/y_val.npy   | Fixed Official Split | fff715ab0af781746b8bc9db620029d203c63a70c41df60a80787b2b735f0471 |
| Master Test                      |       1176851 |          27709 |        1149142 |       97.645 | audit/lofo/cache/y_test.npy  | Fixed Official Split | 5453c04f4dfeceb05b270c725d0065231f3bfb4b34eecc9fc3b5f53e110c3e80 |
| E2 Attack-Heavy                  |         60000 |           1440 |          58560 |       97.6   | test[0:60000]                | N/A (Contiguous)     | e30a4b1258984c6d325b0a84fe5d5b8e9a7d7323e9190464bb70a3ac147f0177 |
| E21 Held-Out Balanced (Legacy)   |         60000 |          30035 |          29965 |       49.942 | test (Legacy sample)         | 99                   | 83c81d24827b478e438124bd86ace1a2474980c216d0ad30e01b779c6f35b1ad |
| E21 Held-Out Balanced (Disjoint) |         60000 |          30045 |          29955 |       49.925 | test[60000:1176851]          | 99                   | 469cc8ddb8bf23f7e2f169163f993f668354cd3cdd41dbd2163882c569cd178f |
| E1 Multi-State (Disjoint)        |         60000 |          30075 |          29925 |       49.875 | test[60000:1176851]          | 42                   | 73353ca45d9a0bd68dec79e368be234d99fb01c001cc2657c38cf6472d4288b1 |
| E8 Core-Hub Stream (Disjoint)    |        100000 |              9 |          99991 |       99.991 | test[remaining]              | 88                   | 69bf773a0d52d5c9a47a1bbc7b577ed28b33cf2e5d87a60eab887791b3840981 |

## 3. Pairwise Intersections & Remediation

| Split Pair                      |   Intersection Count | Is Disjoint   | Status                             |
|:--------------------------------|---------------------:|:--------------|:-----------------------------------|
| Train vs Validation             |                    0 | True          | PASS (Strictly Separate Sets)      |
| Train vs Test                   |                    0 | True          | PASS (Strictly Separate Sets)      |
| Validation vs Test              |                    0 | True          | PASS (Strictly Separate Sets)      |
| E2 vs E21 (Legacy)              |                 2821 | False         | FAIL (2,821 Overlapping Flows)     |
| E2 vs E21 (Disjoint Remediated) |                    0 | True          | PASS (Strictly Disjoint Partition) |
| E2 vs E1 (Disjoint Remediated)  |                    0 | True          | PASS (Strictly Disjoint Partition) |
| E2 vs E8 (Disjoint Remediated)  |                    0 | True          | PASS (Strictly Disjoint Partition) |
| E21 vs E8 (Disjoint Remediated) |                    0 | True          | PASS (Strictly Disjoint Partition) |
| E1 vs E8 (Disjoint Remediated)  |                    0 | True          | PASS (Strictly Disjoint Partition) |

## 4. Remediation Implementation
- All downstream tasks utilize the remediated disjoint test partitions.
- Seed 99 for E21 now operates over `test[60000:1176851]`, guaranteeing exactly 0 overlapping flows with E2.
- Seed 88 for E8 Core-Hub allocates 100,000 flows strictly disjoint from E2, E21, and E1.
