with open('draft/sections/sec4_results.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'Under pure volumetric flood saturation, $P_{\\text{hybrid}}$ yields'
replacement = 'Under pure volumetric flood saturation, $P_{\\text{hybrid}}$ (Algorithm 4) yields'

assert target in text, "Target string for Algorithm 4 citation not found"
text = text.replace(target, replacement)

with open('draft/sections/sec4_results.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Added Algorithm 4 citation in Sec 4.3.5")
