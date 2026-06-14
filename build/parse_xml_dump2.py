"""Extract Uzbek pages using byte-level streaming."""
import bz2, json, re

WIKTIONARY_BZ2 = r'C:\Users\abu_y\izoh\wiktionary_pages.xml.bz2'
OUT_TITLES = r'C:\Users\abu_y\izoh\uzbek_page_titles.txt'

# Match both [[Turkum:Oʻzbek tili]] and [[Category:Oʻzbek tili]]
# Turkum is the Uzbek localized word for Category
UZBEK_CAT_RE = re.compile(r'\[\[(?:Turkum|Category)\s*:\s*[OoOʻʻ\']+zbek\s*tili\s*\]\]')
CAT_BYTES = re.compile(b'\\[\\[(?:Turkum|Category)\\s*:\\s*[OoO\xca\xbb\xca\xbb\']+zbek\\s*tili\\s*\\]\\]')

uzbek_titles = []
total_pages = 0
ns0_count = 0
buffer = b''

with bz2.open(WIKTIONARY_BZ2, 'rb') as f:
    in_page = False
    in_ns0 = False
    current_title = b''
    current_text = b''
    in_text = False
    text_depth = 0
    
    while True:
        chunk = f.read(1024 * 1024)  # 1MB
        if not chunk:
            break
        
        buffer += chunk
        
        # Process complete page elements
        while b'<page>' in buffer and b'</page>' in buffer:
            start = buffer.index(b'<page>')
            end = buffer.find(b'</page>', start) + len(b'</page>')
            if end <= start:
                break
            
            page_xml = buffer[start:end]
            buffer = buffer[end:]
            total_pages += 1
            
            # Check namespace
            ns_match = re.search(b'<ns>(\\d+)</ns>', page_xml)
            if not ns_match or ns_match.group(1) != b'0':
                continue
            
            ns0_count += 1
            
            # Extract title
            t_match = re.search(b'<title>(.*?)</title>', page_xml)
            if not t_match:
                continue
            title = t_match.group(1).decode('utf-8', errors='replace')
            
            # Check if Uzbek - look for category in text
            txt_match = re.search(b'<text[^>]*>(.*?)</text>', page_xml, re.DOTALL)
            if not txt_match:
                continue
            text_content = txt_match.group(1)
            
            if CAT_BYTES.search(text_content):
                uzbek_titles.append(title)
                
                if len(uzbek_titles) % 5000 == 0:
                    print(f"  Found {len(uzbek_titles)} Uzbek pages")
                    with open(OUT_TITLES, 'w', encoding='utf-8') as sf:
                        sf.write('\n'.join(uzbek_titles))
        
        if total_pages % 50000 == 0 and total_pages > 0:
            print(f"  Processed {total_pages} pages, NS0={ns0_count}, Uzbek={len(uzbek_titles)}")

print(f"\nTotal: {total_pages}, NS0: {ns0_count}, Uzbek: {len(uzbek_titles)}")

with open(OUT_TITLES, 'w', encoding='utf-8') as f:
    f.write('\n'.join(uzbek_titles))
print("Saved")
