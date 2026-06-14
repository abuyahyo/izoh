"""Extract pages with {{-uz-}} marker (Uzbek language entries) from the XML dump."""
import bz2, re, json

WIKTIONARY_BZ2 = r'C:\Users\abu_y\izoh\wiktionary_pages.xml.bz2'
OUT_PAGES = r'C:\Users\abu_y\izoh\uzbek_pages.json'
OUT_TITLES = r'C:\Users\abu_y\izoh\uzbek_page_titles.txt'

UZBEK_MARKER = b'{{-uz-}}'
O_TIL_MARKER = 'OʻTIL'.encode('utf-8')

uzbek_pages = []
total = 0
ns0_total = 0
buffer = b''

print("Scanning XML dump...")
with bz2.open(WIKTIONARY_BZ2, 'rb') as f:
    while True:
        chunk = f.read(4 * 1024 * 1024)  # 4 MB chunks
        if not chunk:
            break
        buffer += chunk
        
        while b'<page>' in buffer and b'</page>' in buffer:
            start = buffer.index(b'<page>')
            end = buffer.find(b'</page>', start) + len(b'</page>')
            if end <= start:
                break
            page_bytes = buffer[start:end]
            buffer = buffer[end:]
            total += 1
            
            ns_match = re.search(b'<ns>(\\d+)</ns>', page_bytes)
            if not ns_match or ns_match.group(1) != b'0':
                continue
            
            ns0_total += 1
            
            t_match = re.search(b'<title>(.*?)</title>', page_bytes)
            if not t_match:
                continue
            title = t_match.group(1).decode('utf-8', errors='replace')
            
            txt_match = re.search(b'<text[^>]*>(.*?)</text>', page_bytes, re.DOTALL)
            if not txt_match:
                continue
            text = txt_match.group(1)
            
            # Check if Uzbek entry (has {{-uz-}} or OʻTIL)
            if UZBEK_MARKER in text or O_TIL_MARKER in text:
                uzbek_pages.append({
                    'title': title,
                    'text': text.decode('utf-8', errors='replace')
                })
            
            if total % 50000 == 0:
                print(f"  pages={total}, ns0={ns0_total}, uzbek={len(uzbek_pages)}")

print(f"\nTOTAL: pages={total}, ns0={ns0_total}, uzbek={len(uzbek_pages)}")

# Save
with open(OUT_PAGES, 'w', encoding='utf-8') as f:
    json.dump(uzbek_pages, f, ensure_ascii=False)

with open(OUT_TITLES, 'w', encoding='utf-8') as f:
    for p in uzbek_pages:
        f.write(p['title'] + '\n')

print(f"Saved: {len(uzbek_pages)} Uzbek pages")
