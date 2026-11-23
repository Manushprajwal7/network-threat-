import os
import sys
import subprocess
import shutil

print("=== SYSTEM OPTIMIZATION AUDIT ===", flush=True)

# 1. Drive space
total, used, free = shutil.disk_usage("C:\\")
print(f"C: Drive -> Total: {total / (1024**3):.1f} GB | Used: {used / (1024**3):.1f} GB | Free: {free / (1024**3):.1f} GB ({free/total*100:.1f}% free)", flush=True)

def quick_dir_size(path, max_depth=3):
    if not os.path.exists(path):
        return None, 0
    total = 0
    file_count = 0
    try:
        for root, dirs, files in os.walk(path):
            # check depth
            rel = os.path.relpath(root, path)
            depth = 0 if rel == '.' else len(rel.split(os.sep))
            if depth > max_depth:
                dirs.clear() # don't go deeper
                continue
            for f in files:
                try:
                    fp = os.path.join(root, f)
                    total += os.path.getsize(fp)
                    file_count += 1
                except (OSError, PermissionError):
                    pass
    except (OSError, PermissionError):
        pass
    return total, file_count

targets = [
    ("User Temp Files", os.environ.get("TEMP", r"C:\Users\Manus\AppData\Local\Temp")),
    ("Windows Temp Files", r"C:\Windows\Temp"),
    ("Windows Update Cache", r"C:\Windows\SoftwareDistribution\Download"),
    ("Recycle Bin (Drive C)", r"C:\$Recycle.Bin"),
    ("Downloads Folder", r"C:\Users\Manus\Downloads"),
    ("Desktop Folder", r"C:\Users\Manus\Desktop"),
    ("Videos Folder", r"C:\Users\Manus\Videos"),
    ("Ollama AI Models", r"C:\Users\Manus\.ollama"),
    ("Docker Cache / Images", r"C:\Users\Manus\.docker"),
    ("Gradle Cache", r"C:\Users\Manus\.gradle"),
    ("Maven (.m2) Cache", r"C:\Users\Manus\.m2"),
    ("Pip Cache", r"C:\Users\Manus\AppData\Local\pip\cache"),
    ("npm Cache", r"C:\Users\Manus\AppData\Local\npm-cache"),
    ("General User .cache", r"C:\Users\Manus\.cache"),
    ("Chrome Cache", r"C:\Users\Manus\AppData\Local\Google\Chrome\User Data\Default\Cache"),
    ("Android SDK/Cache", r"C:\Users\Manus\.android"),
    ("Antigravity / Gemini Brain", r"C:\Users\Manus\.gemini"),
    ("OneDrive Folder", r"C:\Users\Manus\OneDrive"),
]

print("\n--- FOLDER SIZE BREAKDOWN ---", flush=True)
for label, p in targets:
    sz, count = quick_dir_size(p, max_depth=4)
    if sz is not None:
        gb = sz / (1024**3)
        mb = sz / (1024**2)
        if gb >= 1.0:
            print(f"{label:26s}: {gb:8.2f} GB  ({count:,} files) -> {p}", flush=True)
        else:
            print(f"{label:26s}: {mb:8.1f} MB  ({count:,} files) -> {p}", flush=True)
    else:
        print(f"{label:26s}: Not found", flush=True)

# 2. Large files in Downloads (> 100 MB)
print("\n--- LARGE FILES IN DOWNLOADS (> 100 MB) ---", flush=True)
dl_path = r"C:\Users\Manus\Downloads"
large_downloads = []
if os.path.exists(dl_path):
    for root, dirs, files in os.walk(dl_path):
        for f in files:
            try:
                fp = os.path.join(root, f)
                sz = os.path.getsize(fp)
                if sz > 100 * 1024 * 1024:
                    large_downloads.append((f, sz, fp))
            except (OSError, PermissionError):
                pass
large_downloads.sort(key=lambda x: x[1], reverse=True)
if large_downloads:
    for name, sz, fp in large_downloads[:15]:
        print(f"  {sz / (1024**3):6.2f} GB : {name}", flush=True)
else:
    print("  No files > 100 MB found in Downloads.", flush=True)

# 3. Check AppData Local for other giant folders
print("\n--- TOP FOLDERS IN AppData\\Local (> 500 MB) ---", flush=True)
local_appdata = r"C:\Users\Manus\AppData\Local"
if os.path.exists(local_appdata):
    for item in os.listdir(local_appdata):
        subp = os.path.join(local_appdata, item)
        if os.path.isdir(subp):
            sz, _ = quick_dir_size(subp, max_depth=3)
            if sz and sz > 500 * 1024 * 1024:
                print(f"  {sz / (1024**3):6.2f} GB : {item}", flush=True)

print("\n--- AUDIT COMPLETE ---", flush=True)
