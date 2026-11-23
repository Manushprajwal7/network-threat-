with open('code/update_paper_v3_tex.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Total lines:", len(lines))
for i, l in enumerate(lines, 1):
    if l.startswith(r'\section{') or l.startswith(r'\subsection{') or l.startswith(r'\begin{table'):
        print(f"Line {i}: {l.strip()[:80]}")
