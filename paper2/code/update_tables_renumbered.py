# paper2/code/update_tables_renumbered.py
import os
import shutil
import pandas as pd

tables_dir = "paper2/tables"

# 1. Update tab7_master_policy with 521,820
df_master = pd.read_csv(os.path.join(tables_dir, "tab7_master_policy.csv"))
df_master.loc[df_master["Policy"].str.startswith("P2 (Cost-Optimal)"), "Balanced Benign Penalty (OCU)"] = "521,820"
df_master.to_csv(os.path.join(tables_dir, "tab7_master_policy.csv"), index=False)
print("Updated tab7_master_policy.csv with 521,820")

# Renumbering map:
# Old -> New
# tab10_cost_matrix.csv -> tab2_cost_matrix.csv
# tab2_if_controlled.csv -> tab3_if_controlled.csv
# tab3_trust_neutral.csv -> tab4_trust_neutral.csv
# tab4_posture_attack_heavy.csv -> tab5_posture_attack_heavy.csv
# tab5_posture_balanced.csv -> tab6_posture_balanced.csv
# tab6_action_precision.csv -> tab7_action_precision.csv
# tab7_master_policy.csv -> tab8_master_policy.csv
# tab8_per_family.csv -> tab9_per_family.csv
# tab9_cost_sensitivity.csv -> tab10_cost_sensitivity.csv

shutil.copy(os.path.join(tables_dir, "tab10_cost_matrix.csv"), os.path.join(tables_dir, "tab2_cost_matrix.csv"))
shutil.copy(os.path.join(tables_dir, "tab2_if_controlled.csv"), os.path.join(tables_dir, "tab3_if_controlled.csv"))
shutil.copy(os.path.join(tables_dir, "tab3_trust_neutral.csv"), os.path.join(tables_dir, "tab4_trust_neutral.csv"))
shutil.copy(os.path.join(tables_dir, "tab4_posture_attack_heavy.csv"), os.path.join(tables_dir, "tab5_posture_attack_heavy.csv"))
shutil.copy(os.path.join(tables_dir, "tab5_posture_balanced.csv"), os.path.join(tables_dir, "tab6_posture_balanced.csv"))
shutil.copy(os.path.join(tables_dir, "tab6_action_precision.csv"), os.path.join(tables_dir, "tab7_action_precision.csv"))
df_master.to_csv(os.path.join(tables_dir, "tab8_master_policy.csv"), index=False)
shutil.copy(os.path.join(tables_dir, "tab8_per_family.csv"), os.path.join(tables_dir, "tab9_per_family.csv"))
shutil.copy(os.path.join(tables_dir, "tab9_cost_sensitivity.csv"), os.path.join(tables_dir, "tab10_cost_sensitivity.csv"))

print("Successfully copied and created all renumbered tables 1-10 in paper2/tables!")
