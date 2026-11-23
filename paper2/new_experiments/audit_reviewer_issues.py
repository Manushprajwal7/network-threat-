import glob, os, re, sys
sys.path.insert(0, ".")

print("=== CHECKING DRAFT SECTIONS FOR ALL REVIEWER ISSUES ===")

section_files = sorted(glob.glob("paper2/draft/sections/*.py"))
full_text = ""
for f in section_files:
    with open(f, encoding="utf-8") as fp:
        c = fp.read()
        full_text += c + "\n"

# 1. Typos
typos = [
    "ciclot2023", "ton_1ot", "modem iot", "shamel-sendi", "preemption over",
    "gtrdot", "&amp;", "5x6", "5*6"
]
for t in typos:
    if t in full_text.lower():
        print(f"FLAG: Found typo '{t}'")
    else:
        print(f"OK: No '{t}'")

# 2. De-anonymization
names = ["thirupathi", "l.t.", "l. t."]
for n in names:
    if n in full_text.lower():
        print(f"FLAG: Found author reference '{n}'")
    else:
        print(f"OK: No author reference '{n}'")

# 3. Truncated sentences
trunc_patterns = [
    r"whereas exact execution of the archived\s*$",
    r"designed to synthesize diverse analytical\s*$",
    r"preserve the verified 34-class xgboost model from \[1\] as an\s*$",
    r"flags anomalous payload variations\s*$"
]
for p in trunc_patterns:
    if re.search(p, full_text, re.IGNORECASE | re.MULTILINE):
        print(f"FLAG: Found truncated sentence matching '{p}'")

# 4. Check references
from paper2.draft.sections.references import REFERENCES
print(f"\nTotal references: {len(REFERENCES)}")
for r in REFERENCES:
    if "Carna" in r["text"]:
        print(f"FLAG: Ref {r['citation']} mentions Carna!")
    if "Slowivska" in r["text"]:
        print(f"FLAG: Ref {r['citation']} misidentifies Slowinska as Slowivska!")

print("\nAudit script complete.")
