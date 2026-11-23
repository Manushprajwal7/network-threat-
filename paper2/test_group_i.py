import re

with open('clean_experiments_isolated/manuscript/paper_v3.tex', 'r', encoding='utf-8') as f:
    tex = f.read()

# Normalize latex escapes for text checking
tex_plain = tex.replace(r'\%', '%').replace(r'$', '')

abstract_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', tex, re.DOTALL)
abstract = abstract_match.group(1) if abstract_match else ""
abstract_plain = abstract.replace(r'\%', '%').replace(r'$', '')

print("--- ABSTRACT REQUIRED STRINGS (PLAIN) ---")
checks = [
    'p = 1.000',
    'L5 was never populated',
    'inverting the contaminated detector gives 0.9916',
    '70.98% balanced accuracy',
    'cannot be attributed specifically to posture or trust mechanics'
]
for c in checks:
    print(f'Abstract contains "{c}":', c in abstract_plain)

print("\n--- BANNED STRINGS IN PAPER_V3.TEX ---")
print('1. P_{2\\text{text}-tier}:', len(re.findall(r'P_\{2\\text\{text\}-tier\}', tex)))
print('2. \\text{text}:', len(re.findall(r'\\text\{text\}', tex)))
print('3. \\backslash:', len(re.findall(r'\\backslash', tex)))
print('4. leak-free:', len(re.findall(r'leak-free', tex, re.IGNORECASE)))
print('4b. zero label leakage:', len(re.findall(r'zero label leakage', tex, re.IGNORECASE)))
print('5. cost-optimal (unqualified):', len(re.findall(r'cost-optimal', tex, re.IGNORECASE)))
print('6. statistically indistinguishable:', len(re.findall(r'statistically indistinguishable', tex, re.IGNORECASE)))
print('7. confirms (applied to monotonicity / permutation):', len(re.findall(r'confirms?\s+that\s+.*?(?:monotonic|permutation|L_1|L_5)', tex, re.IGNORECASE)))
print('8. authoritative:', len(re.findall(r'authoritative', tex, re.IGNORECASE)))

print("\n--- §1.5 ADDITIONAL LIMITATIONS BLOCK ---")
print("Contains Additional limitations block:", "Additional limitations arising from the reported results" in tex)

print("\n--- §2.5 P-VALUE vs SIGMA ---")
print("Reads p = 2.18 x 10^-6:", "p = 2.18 \\times 10^{-6}" in tex)
print("No sigma_R = 2.18 x 10^-6:", "\\sigma_R = 2.18 \\times 10^{-6}" not in tex)

print("\n--- TABLE 1 REQUIRED STRINGS (PLAIN) ---")
print("assumed loss matrix:", "assumed loss matrix" in tex_plain.lower())
print("L2/L3 near 50.20% base rate:", "l2/l3 near 50.20% base rate" in tex_plain.lower())
print("permutation check p = 1.000:", "permutation check p = 1.000" in tex_plain)

print("\n--- NUMERIC RESULTS PRESERVED (PLAIN) ---")
nums = ["0.9523", "0.9858", "0.0084", "1,439,948", "1,404,974", "786,643", "2,974,176", "2,960,105", "27.42%", "0.33%", "310", "0.945", "4.5931"]
for n in nums:
    print(f'Contains {n}:', n in tex_plain)

print("\n--- L5 ACTION CONSISTENTLY BLOCK ---")
print("L_5 = Block in Contribution 3:", "L_5 = Block" in tex_plain or "L_5 = \\text{Block}" in tex)
print("No L_5 = Allow:", "L_5 = Allow" not in tex_plain and "L_5 = \\text{Allow}" not in tex)
