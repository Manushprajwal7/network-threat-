with open("CHANGELOG.md", "r", encoding="utf-8") as f:
    text = f.read()

tier3_log = """

---

## 5. Tier-3 Writing, Copy-Editing, and Presentation Changes (`file:line — before — after — reason`)

| File & Line | Before | After | Editorial Reason | Artifact / Verification |
| :--- | :--- | :--- | :--- | :--- |
| `paper2/draft/sections/sec1_intro.py:ABSTRACT`, `paper/paper_v3.tex:abstract` | Verbose 493-word abstract reciting redundant explanations | Tightened 229-word abstract strictly retaining all 12 numerical anchors (`0.008`, `0.952`, `0.866`, `100.0`, `0.044`, `0.986`, `79.44`, `10.17`, `70`, `1,909,843`, `786,643`, `2.43`), mentioning both Regime 1 and Regime 2, and explicitly noting L5 core-hub condition | Tier 3 critique: abstract length and punchiness; Check 12 passed | `sec1_intro.py`, `paper_v3.tex`, Check 12 |
| `sec1_intro.py`, `sec4_results.py`, `sec7_conclusion.py`, `assemble_manuscript.py`, `paper_v3.tex` | Formulaic chain `0.00% <= 0.00% <= 46.40% <= 51.71% <= 100.00%` repeated 8+ times across text, captions, and contributions | Formulaic chain eliminated across text, captions, and front matter; retained exactly once in §4.2.2 where posture attack density is defined | Tier 3 critique: eliminate repetitive formulaic chaining | `sec1_intro.py`, `sec4_results.py`, `sec7_conclusion.py`, `paper_v3.tex` |
| `sec1_intro.py`, `sec5_discussion.py`, `sec6_limitations.py`, `sec7_conclusion.py`, `paper_v3.tex` | Mechanical repetition of `(at the cost of 29.9% benign Quarantine)` across dozens of sentences | Replaced with natural, varied scholarly phrasing (`with 29.9% quarantine disruption`, `subjecting 29.9% of benign flows to quarantine containment`, `avoiding collateral quarantine penalty`) | Tier 3 critique: eliminate mechanical patching of identical clause | `sec1_intro.py`, `sec5_discussion.py`, `sec6_limitations.py`, `sec7_conclusion.py` |
| Across all section files and `paper_v3.tex` | Overclaim words: `proves`, `conclusively`, `rigorously`, `decisively`, `Crucially` (25+ occurrences) | Replaced with measured scholarly language: `demonstrates`, `indicates`, `systematically`, `consistently`, `specifically`, `importantly`, `inverts completely` (zero overclaim words remaining) | Tier 3 critique: tone down hype and aggressive overclaim language | All files under `paper2/draft/sections/`, `paper/paper_v3.tex` |
| `paper2/tables/tab1_paper_comparison.csv` | Marketing-style Column 4: "Validation Outcome" with self-congratulatory entries ("Repaired & Empirically Validated", "Rigorously Established") | Replaced with objective, neutral `Metric / Quantitative Comparison` column documenting exact quantitative deltas | Tier 3 critique: eliminate self-congratulatory table column | `paper2/tables/tab1_paper_comparison.csv` |
| `paper2/tables/tab3_if_controlled.csv`, `assemble_manuscript.py`, `paper_v3.tex` | 14-column wide table with redundant constant columns (`KS p-value` = 0.0, `Pearson r`, `Spearman rho`, `Fit Time`) | Streamlined to 8 essential columns: `Configuration`, `Trees (M)`, `Training Data`, `ROC AUC`, `KS D`, `Anomaly Gap`, `Benign Mean`, `Attack Mean` | Tier 3 critique: Table 3 horizontal readability in standard IEEE layout | `paper2/tables/tab3_if_controlled.csv`, Table 3 |
| `paper2/tables/tab8_master_policy.csv`, `assemble_manuscript.py`, `paper_v3.tex` | 12-column table with truncated action strings (`Allo-Aler-Rest-Quar-Quar-Bloc`) and redundant penalty columns | Streamlined to 9 clean columns with full action names (`[Allow, Alert, Restrict, Quarantine, Block, Block]`) and explicit FPR breakdown | Tier 3 critique: Table 8 unreadable abbreviations and layout | `paper2/tables/tab8_master_policy.csv`, Table 8 |
| `assemble_manuscript.py`, `paper_v3.tex` | Paragraph-length captions across all 10 tables and 10 figures verbatim reciting results and numerical findings | Replaced with concise, standard IEEE descriptive titles across all 10 tables and 10 figures | Tier 3 critique: captions should describe content rather than restate results | `assemble_manuscript.py`, `paper_v3.tex` |
| `sec3_method.py`, `paper_v3.tex` | §3.1 mixed adversary threat model, dataset features, batch abstraction, and trust assumptions into one sprawling subsection | Cleanly separated into §3.1 (Threat Model and Operational Assumptions) and §3.2 (Dataset Telemetry and Evaluation Protocol), renumbering subsequent subsections | Tier 3 critique: decouple threat model from dataset/telemetry protocols | `sec3_method.py`, `paper_v3.tex` |
| `assemble_manuscript.py:582`, `paper_v3.tex:IEEEkeywords` | Index term `Isolation Forest Contamination` or `Contamination` | Updated to `Training Data Purity`, eliminating ambiguity with scikit-learn's `contamination=0.05` hyperparameter | Tier 3 critique: index term ambiguity | `assemble_manuscript.py`, `paper_v3.tex` |
| Full manuscript package (`docx`, `pdf`, `tex`) | Verified against all 16 automated quality checks; Word page count constraint ($\le 30$ pages) | Passed all 16 quality verification checks; Word COM compile produced exactly 30 pages (estimated 28.9 pages); exported 30-page PDF successfully | Reproducibility and submission page budget constraints | `paper2/draft/paper2_manuscript.docx`, `paper2_manuscript.pdf` |
"""

if "## 5. Tier-3 Writing" not in text:
    with open("CHANGELOG.md", "a", encoding="utf-8") as f:
        f.write(tier3_log)
    print("Appended Section 5 to CHANGELOG.md successfully!")
else:
    print("Section 5 already present in CHANGELOG.md")
