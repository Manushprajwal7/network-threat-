with open('scripts/run_phase1_ec_ed.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_code = """    b_pool = rng_d.choice(benign_test_indices, size=n_ben, replace=False)
    a_pool = rng_d.choice(attack_test_indices, size=n_atk, replace=False)"""

new_code = """    b_replace = (n_ben > len(benign_test_indices))
    a_replace = (n_atk > len(attack_test_indices))
    b_pool = rng_d.choice(benign_test_indices, size=n_ben, replace=b_replace)
    a_pool = rng_d.choice(attack_test_indices, size=n_atk, replace=a_replace)"""

text = text.replace(old_code, new_code)

with open('scripts/run_phase1_ec_ed.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Fixed replacement sampling in run_phase1_ec_ed.py!')
