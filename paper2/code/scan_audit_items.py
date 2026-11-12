import os
import glob
import re

items = [
    (r"strictly monotonic", "phrase 'strictly monotonic' (should be non-decreasing)"),
    (r"mathematical guarantee", "unsupported mathematical guarantee claim"),
    (r"sub-second response in gigabit", "unsupported sub-second response claim"),
    (r"100% attack recall", "unsupported 100% attack recall claim"),
    (r"30% benign / 40% mixed", "entity vs flow composition confusion"),
    (r"non-disruptive attention tier", "Restrict called non-disruptive attention tier"),
    (r"critical trust band to 63\.71%", "critical trust band to 63.71% claim"),
    (r"component signals compose effectively", "unsupported interaction claim"),
    (r"primary discriminator", "TARP called primary discriminator on attack-heavy"),
    (r"preemption", "preemption typo"),
    (r"\bmodem\b", "modem typo"),
    (r"CICloT", "CICloT typo"),
    (r"TON_1oT", "TON_1oT typo"),
    (r"Shamel-Sendi", "Shamel-Sendi typo"),
    (r"gtrdot", "gtrdot typo"),
    (r"6\.77", "old 6.77 headline"),
    (r"2,802,480", "old 2,802,480 number"),
    (r"0\.0296", "old 0.0296 AUC"),
    (r"0\.7843", "old 0.7843 AUC"),
    (r"0\.9644", "old 0.9644 AUC"),
    (r"Thirupathi", "author name Thirupathi"),
    (r"\bL\.T\.\b", "author initial L.T.")
]

section_files = sorted(glob.glob("paper2/draft/sections/*.py") + ["paper2/code/assemble_manuscript.py"])

found_any = False
for fpath in section_files:
    with open(fpath, "r", encoding="utf-8") as fp:
        lines = fp.readlines()
    for idx, line in enumerate(lines):
        for pattern, desc in items:
            if pattern == r"Thirupathi" and "references.py" in fpath:
                continue # Allowed in bibliography for published paper [1] per reviewer Issue 34
            if re.search(pattern, line, re.IGNORECASE):
                print(f"[{desc}] in {fpath}:{idx+1} -> {line.strip()[:100]}")
                found_any = True

if not found_any:
    print("ALL TARGET CHECKS PASSED: Zero flagged phrases or typos exist in the draft!")
