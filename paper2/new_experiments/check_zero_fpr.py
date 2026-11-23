import glob, re, sys
sys.path.insert(0, ".")

files = sorted(glob.glob("paper2/draft/sections/*.py"))
for f in files:
    with open(f, encoding="utf-8") as fp:
        lines = fp.readlines()
    for idx, l in enumerate(lines):
        if re.search(r'(0\.00%|zero)\s+(false|blocking)', l, re.IGNORECASE):
            print(f"{f}:{idx+1} -> {l.strip()}")
