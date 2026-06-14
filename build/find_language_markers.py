"""Check actual text for language markers."""
import bz2, re

WIKTIONARY_BZ2 = r'C:\Users\abu_y\izoh\wiktionary_pages.xml.bz2'

buffer = b''
o_til_bytes = 'OʻTIL'.encode('utf-8')  # OʻTIL
stats = {b'{{-uz-}}': 0, o_til_bytes: 0, b'[[': 0, b'Turkum': 0, b'Category': 0}
match_showing = {b'{{-uz-}}': [], b'Turkum': [], b'Category': [], o_til_bytes: [], b'[[': []}
checked = 0

with bz2.open(WIKTIONARY_BZ2, 'rb') as f:
    while checked < 500:
        chunk = f.read(1024 * 1024)
        if not chunk:
            break
        buffer += chunk
        
        while b'<page>' in buffer and b'</page>' in buffer:
            start = buffer.index(b'<page>')
            end = buffer.find(b'</page>', start) + len(b'</page>')
            if end <= start:
                break
            page_xml = buffer[start:end]
            buffer = buffer[end:]
            
            ns_match = re.search(b'<ns>(\\d+)</ns>', page_xml)
            if not ns_match or ns_match.group(1) != b'0':
                continue
            
            checked += 1
            t_match = re.search(b'<title>(.*?)</title>', page_xml)
            title = t_match.group(1).decode('utf-8', errors='replace') if t_match else '?'
            
            txt_match = re.search(b'<text[^>]*>(.*?)</text>', page_xml, re.DOTALL)
            if not txt_match:
                continue
            text = txt_match.group(1)
            
            for pat in stats:
                if pat in text:
                    stats[pat] += 1
                    if len(match_showing.get(pat, [])) < 3:
                        # Extract lines around match
                        idx = text.index(pat)
                        start_line = max(0, text.rfind(b'\n', 0, idx))
                        end_line = text.find(b'\n', idx)
                        if end_line == -1:
                            end_line = len(text)
                        context = text[start_line:end_line].decode('utf-8', errors='replace').strip()
                        match_showing[pat].append(f"  [{title}]: {context}")

with open(r'C:\Users\abu_y\izoh\xml_language_markers.txt', 'w', encoding='utf-8') as of:
    of.write(f"Checked {checked} NS0 pages\n\n")
    for pat, count in sorted(stats.items(), key=lambda x: -x[1]):
        try:
            label = pat.decode('utf-8', errors='replace')
        except:
            label = str(pat)
        of.write(f"  {label}: {count}\n")
    of.write("\n\nExamples:\n")
    for pat, examples in match_showing.items():
        try:
            label = pat.decode('utf-8', errors='replace')
        except:
            label = str(pat)
        of.write(f"\n--- {label}:\n")
        for ex in examples:
            of.write(ex + '\n')
print("Done")
