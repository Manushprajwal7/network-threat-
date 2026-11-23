with open('scripts/run_phase1_ec_ed.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("res_p2['bal']['quar_fpr']", "res_p2['bal']['quarantine_fpr']")

with open('scripts/run_phase1_ec_ed.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated quarantine_fpr key!')
