with open('scripts/run_phase1_ec_ed.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("res_p2['balanced_net_benefit']", "res_p2['bal']['net_benefit']")
text = text.replace("res_p2['attack_heavy_net_benefit']", "res_p2['atk']['net_benefit']")
text = text.replace("res_p2['balanced_block_fpr']", "res_p2['bal']['block_fpr']")
text = text.replace("res_p2['balanced_quarantine_fpr']", "res_p2['bal']['quar_fpr']")
text = text.replace("res_p2['attack_heavy_block_fpr']", "res_p2['atk']['block_fpr']")

with open('scripts/run_phase1_ec_ed.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Fixed keys in run_phase1_ec_ed.py successfully!')
