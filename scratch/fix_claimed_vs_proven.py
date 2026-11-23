with open("paper/claimed_vs_proven.md", "r", encoding="utf-8") as f:
    text = f.read()

pos_split = text.find("\n---\n\n## 2. Summary Status Breakdown")
if pos_split != -1:
    before = text[:pos_split]
    rest = text[pos_split:]
    # Find Claim 21 in rest
    pos21 = rest.find("| **Claim 21:")
    if pos21 != -1:
        claims21_25 = rest[pos21:].strip()
        summary_section = rest[:pos21].strip()

        new_table_part = before.strip() + "\n" + claims21_25 + "\n"
        new_summary = """---

## 2. Summary Status Breakdown

- **Total Assessed Headline Claims**: 25
- **PROVEN**: 17 (68.0%)
- **PARTIALLY SUPPORTED (Downgraded & Reconciled)**: 4 (16.0%)
- **DISPROVEN / REFUTED / REMOVED**: 4 (16.0%) (Claims 3, 5, 8 removed; Claim 21 refuted pure flow baseline)
- **Unverified Claims Remaining**: **0 (0.0%)**

> [!IMPORTANT]
> Zero headline claims marked "Not supported" or "Unverified" remain in the abstract, title, or core contributions of either the LaTeX (`paper_v3.tex`) or Word (`paper2_manuscript.docx`) manuscripts. All availability trade-offs, flood blocking rates, and topological hub requirements are fully and transparently disclosed.
"""
        new_full_text = new_table_part + "\n" + new_summary
        with open("paper/claimed_vs_proven.md", "w", encoding="utf-8") as f_out:
            f_out.write(new_full_text)
        print("Updated paper/claimed_vs_proven.md successfully!")
    else:
        print("Could not find Claim 21 in rest")
else:
    print("Could not find split point")
