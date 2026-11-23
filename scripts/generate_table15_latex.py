import pandas as pd

df = pd.read_csv('paper2/tables/tab_appA_experiment_inventory.csv')

lines = []
lines.append(r'''\begin{table*}[t]
\caption{Comprehensive Experiment Inventory and Artifact Traceability Matrix across all twenty-five executed experiments (E1 to E25).}
\label{tab:experiment_inventory}
\centering
\scriptsize
\begin{tabular}{lp{2.8cm}p{1.8cm}p{2.6cm}p{3.8cm}p{4.2cm}}
\toprule
\textbf{ID} & \textbf{Experiment Focus} & \textbf{Seeds} & \textbf{Traffic Split} & \textbf{Primary Output Artifact} & \textbf{Key Empirical Finding / Supported Claim} \\
\midrule''')

for _, row in df.iterrows():
    e_id = f"\\textbf{{{row['ID']}}}"
    focus = row['Experiment Focus']
    seeds = str(row['Seeds']).replace('{', '\\{').replace('}', '\\}')
    split = row['Split / Dataset']
    art = '\\texttt{' + row['Primary Artifact'].replace('_', '\\_') + '}'
    claim = (str(row['Key Finding / Supported Claim'])
             .replace('_', '\\_')
             .replace('<=', '$\\le$')
             .replace('>=', '$\\ge$')
             .replace('+/-', '$\\pm$')
             .replace('%', '\\%'))
    lines.append(f'{e_id} & {focus} & {seeds} & {split} & {art} & {claim} \\\\')

lines.append(r'''\bottomrule
\end{tabular}
\end{table*}''')

table15_latex = '\n'.join(lines)
with open('paper/table15_latex.txt', 'w', encoding='utf-8') as f:
    f.write(table15_latex)
print('Generated paper/table15_latex.txt with', len(lines), 'lines.')
