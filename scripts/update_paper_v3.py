import sys
import re

sys.path.insert(0, ".")
from paper2.draft.sections.references import REFERENCES

bib_lines = ["\\begin{thebibliography}{46}\n"]
for r in REFERENCES:
    cit_num = r["citation"].strip("[]")
    text = r["text"]
    doi = r.get("doi", "")
    text_latex = text.replace("“", "``").replace("”", "''")
    # fix standard double quotes
    parts = text_latex.split('"')
    if len(parts) >= 3:
        text_latex = parts[0] + "``" + parts[1] + "''" + "".join(parts[2:])
    
    if doi:
        bib_lines.append(f"\\bibitem{{{cit_num}}} {text_latex} Available: \\url{{{doi}}}\n")
    else:
        bib_lines.append(f"\\bibitem{{{cit_num}}} {text_latex}\n")

bib_lines.append("\\end{thebibliography}")
new_bib = "\n".join(bib_lines)

with open("paper/paper_v3.tex", "r", encoding="utf-8") as f:
    tex = f.read()

# Replace the bibliography
start_idx = tex.find(r"\begin{thebibliography}{41}")
end_idx = tex.find(r"\end{thebibliography}") + len(r"\end{thebibliography}")
if start_idx != -1 and end_idx != -1:
    tex_updated = tex[:start_idx] + new_bib + tex[end_idx:]
    with open("paper/paper_v3.tex", "w", encoding="utf-8") as f:
        f.write(tex_updated)
    print("Updated bibliography in paper_v3.tex successfully!")
else:
    print("Could not find thebibliography block!")
