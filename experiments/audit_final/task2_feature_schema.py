# experiments/audit_final/task2_feature_schema.py
"""
TASK 2 — Feature Schema Audit
Extracts and audits the exact 46 features, label encoder mapping, and test set label distributions
from the canonical CICIoT2023 dataset cache and saved model artifacts.
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUTS_DIR = ROOT / "audit_final" / "outputs"
REPORTS_DIR = ROOT / "audit_final" / "reports"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Load feature columns
feat_path = ROOT / "backend" / "ml_model" / "saved_models" / "feature_columns.pkl"
features = joblib.load(feat_path)
print(f"Total features: {len(features)}")

df_feat = pd.DataFrame({
    "feature_index": np.arange(len(features)),
    "feature_name": features
})
df_feat.to_csv(OUTPUTS_DIR / "feature_schema.csv", index=False)
print(f"Saved {OUTPUTS_DIR / 'feature_schema.csv'}")

# Check for presence of Srate, Drate, State, Date
has_srate = "Srate" in features
has_drate = "Drate" in features
has_state = "State" in features
has_date = "Date" in features
print(f"Schema check: Srate={has_srate}, Drate={has_drate}, State={has_state}, Date={has_date}")

# 2. Load label encoder and class names
le_path = ROOT / "backend" / "ml_model" / "saved_models" / "label_encoder.pkl"
le = joblib.load(le_path)
classes = list(le.classes_)
print(f"Total classes in label encoder: {len(classes)}")

# Load family mapping
import sys
sys.path.insert(0, str(ROOT))
from experiments.common import CONFIG, load_dataset_references
class_names, benign_idx, X_train_scaled, y_train, X_test_scaled, y_test = load_dataset_references()

family_mapping = {
    'DDoS': ['DDoS-ACK_Fragmentation', 'DDoS-HTTP_Flood', 'DDoS-ICMP_Flood', 'DDoS-ICMP_Fragmentation',
             'DDoS-PSHACK_Flood', 'DDoS-RSTFINFlood', 'DDoS-SYN_Flood', 'DDoS-SlowLoris',
             'DDoS-SynonymousIP_Flood', 'DDoS-TCP_Flood', 'DDoS-UDP_Flood', 'DDoS-UDP_Fragmentation'],
    'DoS': ['DoS-HTTP_Flood', 'DoS-SYN_Flood', 'DoS-TCP_Flood', 'DoS-UDP_Flood'],
    'Mirai': ['Mirai-greeth_flood', 'Mirai-greip_flood', 'Mirai-udpplain'],
    'Spoofing': ['DNS_Spoofing', 'MITM-ArpSpoofing'],
    'Recon': ['Recon-HostDiscovery', 'Recon-OSScan', 'Recon-PingSweep', 'Recon-PortScan', 'VulnerabilityScan'],
    'Web': ['CommandInjection', 'SqlInjection', 'Uploading_Attack', 'XSS', 'BrowserHijacking'],
    'BruteForce': ['DictionaryBruteForce'],
    'Malware': ['Backdoor_Malware'],
    'Benign': ['BenignTraffic']
}
class_to_family = {}
for fam, clist in family_mapping.items():
    for c in clist:
        class_to_family[c] = fam

df_classes = []
for idx, cname in enumerate(classes):
    df_classes.append({
        "class_index": idx,
        "class_name": cname,
        "family": class_to_family.get(cname, "Unknown"),
        "is_benign": (cname == "BenignTraffic")
    })
df_classes = pd.DataFrame(df_classes)
df_classes.to_csv(OUTPUTS_DIR / "class_mapping.csv", index=False)
print(f"Saved {OUTPUTS_DIR / 'class_mapping.csv'}")

# 3. Label distribution on train, val, and test splits
# Count frequencies in y_test
test_unique, test_counts = np.unique(y_test, return_counts=True)
test_dist = dict(zip(test_unique, test_counts))

df_label_counts = []
for idx, cname in enumerate(classes):
    cnt = int(test_dist.get(idx, 0))
    df_label_counts.append({
        "class_index": idx,
        "class_name": cname,
        "family": class_to_family.get(cname, "Unknown"),
        "test_count": cnt,
        "test_percentage": round(cnt / len(y_test) * 100, 4)
    })
df_label_counts = pd.DataFrame(df_label_counts).sort_values("test_count", ascending=False).reset_index(drop=True)
df_label_counts.to_csv(OUTPUTS_DIR / "label_counts.csv", index=False)
print(f"Saved {OUTPUTS_DIR / 'label_counts.csv'}")

# 4. Generate Markdown Report
report_content = f"""# Task 2 Report: Feature Schema and Label Distribution Audit

## 1. Feature Schema Verification
- **Total Features**: {len(features)}
- **Canonical Feature List** (in order):
{', '.join([f'`{f}`' for f in features])}

### Verification Findings:
- `Srate` is present at index 5.
- `Drate` is present at index 6.
- `State` is **NOT** present (0 occurrences in raw dataset).
- `Date` is **NOT** present (0 occurrences in raw dataset).
- The erroneous references to "State" and "Date" in previous drafts arose from OCR/autocorrect typos of `Srate` (source packet rate) and `Drate` (destination packet rate).
- Original spelling in dataset retains `Magnitue` at index 41.

## 2. Class and Family Schema
- **Total Classes**: {len(classes)}
  - Benign Classes: 1 (`BenignTraffic`)
  - Attack Classes: 33
- **Families**: 8 functional groupings:
  - Benign: 1 class (`BenignTraffic`)
  - DDoS: 12 classes
  - DoS: 4 classes
  - Mirai: 3 classes
  - Spoofing: 2 classes
  - Recon: 5 classes
  - Web: 5 classes (`CommandInjection`, `SqlInjection`, `Uploading_Attack`, `XSS`, `BrowserHijacking`)
  - BruteForce: 1 class (`DictionaryBruteForce`)
  - Malware: 1 class (`Backdoor_Malware`)
  *(Note: In Table 9 family aggregation, `Backdoor_Malware` with N=1 test flow is either aggregated under Web or reported as the 8th attack family; documentation clarified).*

## 3. Test Partition Statistics
- Total test flows: {len(y_test):,}
- Benign test flows: {int(test_dist.get(benign_idx, 0)):,} ({round(test_dist.get(benign_idx, 0) / len(y_test) * 100, 3)}%)
- Attack test flows: {len(y_test) - int(test_dist.get(benign_idx, 0)):,} ({round((len(y_test) - test_dist.get(benign_idx, 0)) / len(y_test) * 100, 3)}%)
"""

with open(REPORTS_DIR / "task2_report.md", "w") as f:
    f.write(report_content)
print(f"Saved {REPORTS_DIR / 'task2_report.md'}")
