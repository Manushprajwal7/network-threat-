import glob, re, sys
sys.path.insert(0, ".")

files = sorted(glob.glob("paper2/draft/sections/*.py"))
for f in files:
    with open(f, encoding="utf-8") as fp:
        lines = fp.readlines()
    for idx, l in enumerate(lines):
        s = l.strip()
        # Check headings
        if re.match(r'^\d+(\.\d+)*\s+', s):
            print(f"{f}:{idx+1} HEADING: {s}")
        # Check truncated sentences (ends with lowercase word and no punctuation, but not code)
        if s and not s.startswith("#") and not s.startswith("```") and not s.startswith("$$") and not s.startswith("Algorithm") and not s.startswith("Table") and not s.startswith("Figure") and not re.match(r'^\d+(\.\d+)*\s+', s) and not s.startswith("-"):
            if s.endswith(" an") or s.endswith(" the") or s.endswith(" of") or s.endswith(" and") or s.endswith(" with") or s.endswith(" from") or s.endswith(" archived"):
                print(f"FLAG TRUNCATION in {f}:{idx+1} -> {s}")
