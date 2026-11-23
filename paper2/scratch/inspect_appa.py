import pandas as pd
df = pd.read_csv('tables/tab_appA_experiment_inventory.csv')
for idx, r in df.iterrows():
    print(f"{r['ID']}: {r['Experiment Focus']} | {r['Primary Output Artifact']} | {str(r['Key Empirical Finding / Supported Claim'])[:60]}")
