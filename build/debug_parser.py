"""Debug parser issues on specific entries."""
import json, re, html

# Import parser functions
exec(open(r'C:\Users\abu_y\izoh\build\import_wiktionary_bulk.py', encoding='utf-8').read().split("if __name__")[0])

with open(r'C:\Users\abu_y\izoh\uzbek_pages.json', 'r', encoding='utf-8') as f:
    all_pages = json.load(f)

# Find specific entries
for target in ['eshtmoq', 'yemoq', 'non', 'kitob', 'suv']:
    for p in all_pages:
        if p['title'].lower() == target:
            with open(f'C:\\Users\\abu_y\\izoh\\wt_{target}.txt', 'w', encoding='utf-8') as out:
                out.write(p['text'])
            print(f"Saved {target}: {len(p['text'])} chars")
            
            # Check sections
            text = p['text']
            
            # Find all sections
            sections = re.findall(r'^==[^=].*?==\s*$', text, re.MULTILINE)
            print(f"  Sections: {sections}")
            
            # Find all subsections
            subsections = re.findall(r'^===[^=].*?===\s*$', text, re.MULTILINE)
            print(f"  Subsections: {subsections}")
            
            # Look for category links
            cats = re.findall(r'\[\[Turkum:[^\]]+\]\]', text)
            print(f"  Categories: {cats}")
            
            # Try parse
            parsed = parse_uzbek_wikitext(text, target)
            print(f"  Parsed: meanings={len(parsed.get('meanings', []))}, etymology={bool(parsed.get('etymology'))}")
            
            # Raw etymology section
            et_sec = get_section_wikitext(text, 'Etimologiyasi', ['Maʼnoviy_xususiyatlari', "Ma'noviy_xususiyatlari", 'Aytilishi'])
            if et_sec:
                lines = [l.strip() for l in et_sec.split('\n') if l.strip() and not l.strip().startswith('{{')]
                print(f"  Etymology section lines: {lines[:5]}")
            else:
                print(f"  No etymology section found")
            
            break
    else:
        print(f"{target} not found")
