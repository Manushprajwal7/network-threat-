import os

paths = [
    'tables/tab13_adtm_weight_sensitivity.csv',
    'clean_experiments_isolated/tables/tab13_adtm_weight_sensitivity.csv'
]

for path in paths:
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        if len(lines) > 0 and lines[0].startswith('Configuration,Weights (w_class'):
            lines[0] = 'Configuration,"Weights (w_class, w_anom, w_topo, w_dev)",Dynamic Trust AUC,Critical (<20) %,Very Low (20-40) %,P2-tier Net Benefit (OCU)\n'
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f'Fixed header in {path}')
        else:
            print(f'Header already fixed or different in {path}')
