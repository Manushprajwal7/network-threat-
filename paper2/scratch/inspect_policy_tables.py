import numpy as np
import pandas as pd
from pathlib import Path
import json

cache_dir = Path("../audit/lofo/cache")
with open(cache_dir / "class_names.json", "r") as f:
    class_names = json.load(f)
benign_idx = class_names.index("BenignTraffic")

# Let's inspect test_policy_table.csv vs val_policy_table.csv if exists
for p in Path("audit_v3").glob("**/*policy*.csv"):
    print(p)
    df = pd.read_csv(p)
    print(df.to_string())
    print("-" * 50)
