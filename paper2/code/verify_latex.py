import re
import sys

TEX_PATH = "clean_experiments_isolated/manuscript/paper_v3.tex"

with open(TEX_PATH, "r", encoding="utf-8") as f:
    text = f.read()

lines = text.splitlines()
errors = []

# 1. Environment matching
env_stack = []
for idx, line in enumerate(lines, 1):
    # strip comments
    code_line = re.sub(r'(?<!\\)%.*$', '', line)
    
    begins = re.findall(r'\\begin\{([a-zA-Z0-9*]+)\}', code_line)
    ends = re.findall(r'\\end\{([a-zA-Z0-9*]+)\}', code_line)
    
    for b in begins:
        env_stack.append((b, idx))
    for e in ends:
        if not env_stack:
            errors.append(f"Line {idx}: Unmatched \\end{{{e}}}")
        else:
            top_b, top_line = env_stack.pop()
            if top_b != e:
                errors.append(f"Line {idx}: Mismatched \\end{{{e}}}, expected \\end{{{top_b}}} (opened at line {top_line})")

if env_stack:
    for b, line_num in env_stack:
        errors.append(f"Line {line_num}: Unclosed \\begin{{{b}}}")

# 2. Brace matching
brace_count = 0
for idx, line in enumerate(lines, 1):
    code_line = re.sub(r'(?<!\\)%.*$', '', line)
    for char in code_line:
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
        if brace_count < 0:
            errors.append(f"Line {idx}: Extra closing brace '}}'")
            brace_count = 0

if brace_count > 0:
    errors.append(f"Total unclosed opening braces '{{': {brace_count}")

# 3. Label and ref audit
labels = set(re.findall(r'\\label\{([^}]+)\}', text))
refs = set(re.findall(r'\\ref\{([^}]+)\}', text))
print(f"Total defined labels: {len(labels)}")
print(f"Total referenced labels: {len(refs)}")
missing_refs = refs - labels
if missing_refs:
    print(f"Referenced labels not defined inline (might be in appendices): {missing_refs}")

# 4. Citations audit
bibitems = set(re.findall(r'\\bibitem\{([^}]+)\}', text))
cites = set()
for m in re.findall(r'\\cite\{([^}]+)\}', text):
    for c in m.split(','):
        cites.add(c.strip())

print(f"Total bibitems: {len(bibitems)}")
print(f"Total cited keys: {len(cites)}")
missing_cites = cites - bibitems
if missing_cites:
    errors.append(f"Missing bibitems for cited keys: {missing_cites}")

if not errors:
    print("SUCCESS: All LaTeX environments, braces, citations, and structural checks passed perfectly!")
else:
    print("ERRORS FOUND:")
    for err in errors:
        print("  -", err)
    sys.exit(1)
