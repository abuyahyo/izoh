"""Test the wikitext parser on a few sample entries."""
import json, re, html

# Import from the main script
exec(open(r'C:\Users\abu_y\izoh\build\import_wiktionary_bulk.py', encoding='utf-8').read().split("if __name__")[0])

# Load a few entries and test parse them
with open(r'C:\Users\abu_y\izoh\uzbek_pages.json', 'r', encoding='utf-8') as f:
    all_pages = json.load(f)

with open(r'C:\Users\abu_y\izoh\data\index.json', 'r', encoding='utf-8') as f:
    existing = {w.lower() for w in json.load(f)}

# Find a few test entries that are NOT in our data
test_pages = []
for p in all_pages:
    if p['title'].lower() not in existing and not p['title'].startswith('-') and not re.search(r'^[A-Z]', p['title']):
        test_pages.append(p)
        if len(test_pages) >= 10:
            break

print(f"Testing {len(test_pages)} sample entries\n")

for p in test_pages:
    title = p['title']
    wikitext = p['text']
    
    # Skip redirects
    if re.search(r'^#(?:REDIRECT|YOʻNALTIRISH)\b', wikitext, re.MULTILINE):
        print(f"[{title}] SKIP - redirect")
        continue
    
    parsed = parse_uzbek_wikitext(wikitext, title)
    converted = convert_entry_to_latin(parsed)
    
    print(f"\n=== {title} ===")
    print(f"POS: {converted.get('part_of_speech', '')}")
    print(f"Etymology: {converted.get('etymology', '')[:200]}")
    print(f"Meanings: {len(converted.get('meanings', []))}")
    for m in converted.get('meanings', []):
        print(f"  {m.get('number')}. {m.get('definition', '')[:100]}")
        for ex in m.get('examples', []):
            print(f"     ◆ {ex.get('text', '')[:50]}")
    print(f"Idioms: {len(converted.get('idioms', []))}")
    print(f"Synonyms: {converted.get('synonyms', '')[:100]}")
    print(f"Antonyms: {converted.get('antonyms', '')[:100]}")
