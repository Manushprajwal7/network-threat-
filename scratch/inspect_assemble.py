with open('paper2/code/assemble_manuscript.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(650, 765):
    line = lines[i].strip()
    if 'add_table_booktabs' in line or 'add_figure_inline' in line:
        print(f'{i+1}: {line}')
