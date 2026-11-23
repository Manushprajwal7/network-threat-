import sys
sys.path.insert(0, ".")

from paper2.draft.sections.sec1_intro import TITLE, ABSTRACT, SEC1_TEXT
from paper2.draft.sections.sec2_related import SEC2_TEXT
from paper2.draft.sections.sec3_method import SEC3_TEXT
from paper2.draft.sections.sec4_results import SEC4_TEXT
from paper2.draft.sections.sec5_discussion import SEC5_TEXT
from paper2.draft.sections.sec6_limitations import SEC6_TEXT
from paper2.draft.sections.sec7_conclusion import SEC7_TEXT

full = " ".join([TITLE, ABSTRACT, SEC1_TEXT, SEC2_TEXT, SEC3_TEXT, SEC4_TEXT, SEC5_TEXT, SEC6_TEXT, SEC7_TEXT])
print("=== TABLES ===")
for t in range(1, 11):
    c = full.count(f"Table {t}")
    print(f"Table {t}: {c}x")

print("\n=== FIGURES ===")
for f in range(1, 11):
    c = full.count(f"Figure {f}") + full.count(f"Fig. {f}")
    print(f"Figure {f}: {c}x")
