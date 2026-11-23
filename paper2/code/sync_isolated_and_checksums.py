# paper2/code/sync_isolated_and_checksums.py
import os
import shutil
import hashlib

iso_root = "paper2/clean_experiments_isolated"

# 1. Copy updated manuscript
shutil.copy("paper2/draft/paper2_manuscript.docx", os.path.join(iso_root, "manuscript/paper2_manuscript.docx"))
shutil.copy("paper2/draft/paper2_manuscript.pdf", os.path.join(iso_root, "manuscript/paper2_manuscript.pdf"))
if os.path.exists("paper/paper_v2.tex"):
    shutil.copy("paper/paper_v2.tex", os.path.join(iso_root, "manuscript/paper_v2.tex"))
if os.path.exists("paper/paper_v3.tex"):
    shutil.copy("paper/paper_v3.tex", os.path.join(iso_root, "manuscript/paper_v3.tex"))
if os.path.exists("paper/revision_notes.md"):
    shutil.copy("paper/revision_notes.md", os.path.join(iso_root, "manuscript/revision_notes.md"))
if os.path.exists("paper/revision_notes_round2.md"):
    shutil.copy("paper/revision_notes_round2.md", os.path.join(iso_root, "manuscript/revision_notes_round2.md"))
if os.path.exists("paper/claimed_vs_proven.md"):
    shutil.copy("paper/claimed_vs_proven.md", os.path.join(iso_root, "manuscript/claimed_vs_proven.md"))
if os.path.exists("paper/math_audit.md"):
    shutil.copy("paper/math_audit.md", os.path.join(iso_root, "manuscript/math_audit.md"))

# Copy appendices
os.makedirs(os.path.join(iso_root, "manuscript/appendices"), exist_ok=True)
if os.path.exists("paper/appendices"):
    for f in os.listdir("paper/appendices"):
        if f.endswith(".tex"):
            shutil.copy(os.path.join("paper/appendices", f), os.path.join(iso_root, "manuscript/appendices", f))

# 2. Copy audit report and changelog
if os.path.exists("audit_report.md"):
    shutil.copy("audit_report.md", os.path.join(iso_root, "AUDIT_REPORT.md"))
if os.path.exists("audit_round2.md"):
    shutil.copy("audit_round2.md", os.path.join(iso_root, "AUDIT_ROUND2.md"))
if os.path.exists("AUDIT_REMEDIATION_REPORT.md"):
    shutil.copy("AUDIT_REMEDIATION_REPORT.md", os.path.join(iso_root, "AUDIT_REMEDIATION_REPORT.md"))
shutil.copy("CHANGELOG.md", os.path.join(iso_root, "CHANGELOG.md"))

# 3. Copy tables
os.makedirs(os.path.join(iso_root, "tables"), exist_ok=True)
for f in os.listdir("paper2/tables"):
    if f.endswith(".csv"):
        shutil.copy(os.path.join("paper2/tables", f), os.path.join(iso_root, "tables", f))

# 4. Copy figures
os.makedirs(os.path.join(iso_root, "figures"), exist_ok=True)
if os.path.exists("paper2/figures"):
    for f in os.listdir("paper2/figures"):
        if f.endswith(".png") or f.endswith(".pdf"):
            shutil.copy(os.path.join("paper2/figures", f), os.path.join(iso_root, "figures", f))

# 5. Copy scripts
os.makedirs(os.path.join(iso_root, "scripts"), exist_ok=True)
shutil.copy("paper2/code/assemble_manuscript.py", os.path.join(iso_root, "scripts/assemble_manuscript.py"))

# 6. Copy configs and experiments
os.makedirs(os.path.join(iso_root, "configs"), exist_ok=True)
shutil.copy("configs/paper.yaml", os.path.join(iso_root, "configs/paper.yaml"))

os.makedirs(os.path.join(iso_root, "experiments"), exist_ok=True)
os.makedirs(os.path.join(iso_root, "experiments/outputs"), exist_ok=True)
for f in os.listdir("experiments"):
    if f.endswith(".py"):
        shutil.copy(os.path.join("experiments", f), os.path.join(iso_root, "experiments", f))
for f in os.listdir("experiments/outputs"):
    shutil.copy(os.path.join("experiments/outputs", f), os.path.join(iso_root, "experiments/outputs", f))

# 7. Generate SHA256 checksums
lines = []
for root, dirs, files in os.walk(iso_root):
    for f in sorted(files):
        if f == "checksums.sha256":
            continue
        full_path = os.path.join(root, f)
        with open(full_path, "rb") as fp:
            data = fp.read()
        sha = hashlib.sha256(data).hexdigest()
        rel_path = os.path.relpath(full_path, iso_root).replace("\\", "/")
        lines.append(f"{sha}  {rel_path}")

out_path = os.path.join(iso_root, "checksums.sha256")
with open(out_path, "w", encoding="utf-8") as fp:
    fp.write("\n".join(lines) + "\n")

# Copy to root checksums.sha256
shutil.copy(out_path, "checksums.sha256")

print(f"Synchronized isolated package and generated {len(lines)} SHA256 checksums in {out_path} and root checksums.sha256!")
