"""Cross-reference Uzbek Wiktionary pages with our index."""
import json, re

# Read our index
with open(r'C:\Users\abu_y\izoh\data\index.json', 'r', encoding='utf-8') as f:
    our_words = {w.lower() for w in json.load(f)}
print(f"Our index: {len(our_words)} words")

# Read Uzbek page titles
with open(r'C:\Users\abu_y\izoh\uzbek_pages.json', 'r', encoding='utf-8') as f:
    pages = json.load(f)

# Normalize titles for comparison
def normalize_word(w):
    """Normalize for comparison: lowercase, normalize apostrophes."""
    w = w.lower()
    w = w.replace('ʼ', "'")  # modifier letter apostrophe
    w = w.replace('ʻ', "'")  # modifier letter turned comma
    w = w.replace('ʽ', "'")  # modifier letter reversed comma
    w = w.replace('ʿ', "'")  # modifier letter half ring
    return w

wiktionary_words = set()
for p in pages:
    wiktionary_words.add(normalize_word(p['title']))

print(f"Wiktionary Uzbek pages: {len(wiktionary_words)}")

# Find new words (in Wiktionary but not in our data)
new_words = wiktionary_words - our_words
overlap = our_words & wiktionary_words

print(f"Overlap: {len(overlap)}")
print(f"New words: {len(new_words)}")

# Find new word entries (the full data)
new_entries = []
for p in pages:
    if normalize_word(p['title']) in new_words:
        new_entries.append(p)

print(f"New entries with text: {len(new_entries)}")

# Sort and show sample
new_titles_sorted = sorted([p['title'] for p in new_entries])
with open(r'C:\Users\abu_y\izoh\uzbek_new_words.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total new: {len(new_entries)}\n")
    f.write(f"Overlap: {len(overlap)}\n\n")
    for t in new_titles_sorted:
        f.write(t + '\n')

# Save full new entries
with open(r'C:\Users\abu_y\izoh\uzbek_new_entries.json', 'w', encoding='utf-8') as f:
    json.dump(new_entries, f, ensure_ascii=False)

print(f"\nSample new words:")
for t in new_titles_sorted[:30]:
    print(f"  {t}")
print("...")
print(f"Saved new words list")
