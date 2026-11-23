import sys, re
sys.path.insert(0, ".")

from paper2.draft.sections.sec1_intro import TITLE, ABSTRACT, SEC1_TEXT
from paper2.draft.sections.sec2_related import SEC2_TEXT
from paper2.draft.sections.sec3_method import SEC3_TEXT
from paper2.draft.sections.sec4_results import SEC4_TEXT
from paper2.draft.sections.sec5_discussion import SEC5_TEXT
from paper2.draft.sections.sec6_limitations import SEC6_TEXT
from paper2.draft.sections.sec7_conclusion import SEC7_TEXT
from paper2.draft.sections.references import REFERENCES

full = " ".join([TITLE, ABSTRACT, SEC1_TEXT, SEC2_TEXT, SEC3_TEXT, SEC4_TEXT, SEC5_TEXT, SEC6_TEXT, SEC7_TEXT])

# Check references cited
uncited_refs = []
for ref in REFERENCES:
    cit = ref["citation"]
    if cit not in full:
        uncited_refs.append(cit)

# Check text citations exist in references
text_cits = set(re.findall(r'\[\d+\]', full))
ref_cits = set(ref["citation"] for ref in REFERENCES)
orphan_cits = text_cits - ref_cits

print(f"Total references in bibliography: {len(REFERENCES)}")
print(f"Uncited references: {uncited_refs}")
print(f"Orphan text citations: {orphan_cits}")
