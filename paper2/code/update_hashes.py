import os
import hashlib

root_dir = "paper2/clean_experiments_isolated"
lines = []

for root, dirs, files in os.walk(root_dir):
    for f in sorted(files):
        if f == "checksums.sha256":
            continue
        full_path = os.path.join(root, f)
        with open(full_path, "rb") as fp:
            data = fp.read()
        sha = hashlib.sha256(data).hexdigest()
        rel_path = os.path.relpath(full_path, root_dir).replace("\\", "/")
        lines.append(f"{sha}  {rel_path}")

out_path = os.path.join(root_dir, "checksums.sha256")
with open(out_path, "w", encoding="utf-8") as fp:
    fp.write("\n".join(lines) + "\n")

print(f"Generated SHA256 checksums for {len(lines)} files in {out_path}")
