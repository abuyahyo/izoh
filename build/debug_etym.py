"""Debug etymology extraction."""
import re

with open(r'C:\Users\abu_y\izoh\wt_yemoq.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Get etymology section
## First, find section bounds
start_pat = re.compile(r'^==\s*Etimologiyasi\s*==\s*$', re.MULTILINE)
m = start_pat.search(text)
start = m.end()

next_pat = re.compile(r'^==\s*Maʼnoviy xususiyatlari\s*==', re.MULTILINE)
next_m = next_pat.search(text, start)
end = next_m.start() if next_m else len(text)

section = text[start:end].strip()
out = []
out.append(f"Section length: {len(section)}")
out.append(f"Section content:")
out.append(repr(section[:500]))
out.append("")

# Check OʻTEL regex
o_tel_pattern = r'{{OʻTEL\|([^}]+)}}'
matches = re.findall(o_tel_pattern, section, re.DOTALL)
out.append(f"OʻTEL matches: {len(matches)}")
for i, m in enumerate(matches):
    out.append(f"  Match {i}: {repr(m[:200])}")

# Check what character is between O and T
if 'O' in section:
    idx = section.index('O')
    if idx + 1 < len(section) and section[idx+1] == 'ʻ':
        pass
    out.append(f"Char after 'O' in OTEL: U+{ord(section[idx+1]):04X} = {repr(section[idx+1])}")

# Also check the OʻTEL character encoding
o_tel_in_section = section[section.index('O'):section.index('O')+5]
out.append(f"OʻTEL chars: {' '.join(f'U+{ord(c):04X}' for c in o_tel_in_section)}")

# Try O'TEL variant
o_tel_pattern2 = r"{{O'TEL\|([^}]+)}}"
matches2 = re.findall(o_tel_pattern2, section, re.DOTALL)
out.append(f"O'TEL matches: {len(matches2)}")

# Try generic OTEL
for variant in ['OʻTEL', 'O\'TEL', 'OTEL']:
    pat = r'{{' + variant + r'\|([^}]+)}}'
    mlist = re.findall(pat, section, re.DOTALL)
    if mlist:
        out.append(f"  {variant}: {len(mlist)} matches")

with open(r'C:\Users\abu_y\izoh\etym_debug.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print("Done")
