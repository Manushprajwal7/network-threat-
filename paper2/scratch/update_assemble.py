with open('code/assemble_manuscript.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace Table 6b col_widths
old_6b = 'col_widths=[1.8, 1.0, 1.0, 1.3, 0.8, 0.8]'
new_6b = 'col_widths=[1.6, 0.9, 0.8, 0.7, 0.9, 0.9, 0.6]'
assert old_6b in text, "old_6b not found in assemble_manuscript.py"
text = text.replace(old_6b, new_6b)

# Add placeholders for TABLE_12, TABLE_13, TABLE_14
old_target = 'elif stripped == "<<<TABLE_A1>>>":'
new_insert = '''elif stripped == "<<<TABLE_12>>>":
            add_table_booktabs("12", "Operational escalation of core hub nodes into Level L5 under flood saturation versus nominal traffic.",
                               "paper2/tables/tab12_l5_population.csv",
                               col_widths=[0.8, 1.8, 0.9, 0.9, 0.8, 0.8, 0.8])
            continue
        elif stripped == "<<<TABLE_13>>>":
            add_table_booktabs("13", "Dynamic trust component weight sensitivity across seven parameterizations on the 60,000-flow multi-state evaluation stream.",
                               "paper2/tables/tab13_adtm_weight_sensitivity.csv",
                               col_widths=[1.5, 1.8, 1.0, 0.9, 1.0, 1.1])
            continue
        elif stripped == "<<<TABLE_14>>>":
            add_table_booktabs("14", "Posture threshold boundary sensitivity analysis across detection and trust thresholds on the multi-state evaluation stream.",
                               "paper2/tables/tab14_posture_threshold_sensitivity.csv",
                               col_widths=[1.2, 0.8, 1.8, 1.2, 1.4])
            continue
        elif stripped == "<<<TABLE_A1>>>":'''

assert old_target in text, "old_target not found in assemble_manuscript.py"
text = text.replace(old_target, new_insert)

with open('code/assemble_manuscript.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Successfully updated code/assemble_manuscript.py")
