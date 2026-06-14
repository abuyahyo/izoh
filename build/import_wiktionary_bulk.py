"""Parse Wiktionary wikitext to our JSON format and merge into data files."""
import json, re, sys, os, html

# ============================================================
# Cyrillic to Latin converter (sync'd with app.js)
# ============================================================
CYR_TO_LAT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
    'е': 'e', 'ё': 'yo', 'ж': 'j', 'з': 'z', 'и': 'i',
    'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
    'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
    'у': 'u', 'ф': 'f', 'х': 'x', 'ц': 'ts', 'ч': 'ch',
    'ш': 'sh', 'ъ': '\'', 'ы': 'i', 'э': 'e', 'ю': 'yu',
    'я': 'ya', 'ў': 'o‘', 'қ': 'q', 'ҳ': 'h', 'ғ': 'g‘',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D',
    'Е': 'E', 'Ё': 'Yo', 'Ж': 'J', 'З': 'Z', 'И': 'I',
    'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
    'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
    'У': 'U', 'Ф': 'F', 'Х': 'X', 'Ц': 'Ts', 'Ч': 'Ch',
    'Ш': 'Sh', 'Ъ': '\'', 'Ы': 'I', 'Э': 'E', 'Ю': 'Yu',
    'Я': 'Ya', 'Ў': 'O‘', 'Қ': 'Q', 'Ҳ': 'H', 'Ғ': 'G‘',
}

def cyr_to_lat(text):
    result = []
    for ch in text:
        if ch in CYR_TO_LAT:
            result.append(CYR_TO_LAT[ch])
        else:
            result.append(ch)
    return ''.join(result)

# ============================================================
# Letter-of function (sync'd with app.js)
# ============================================================
def letter_of(word):
    w = word.upper()
    for prefix in ['SH', 'CH', "O'", 'Oʻ', "G'", 'Gʻ']:
        if w.startswith(prefix):
            return prefix
    if w and w[0].isalpha():
        return w[0]
    return '#'

# ============================================================
# Wikitext parser
# ============================================================
def normalize_apos(text):
    """Normalize apostrophe variants: U+02BB, U+02BC → ' (U+0027)"""
    return text.replace('\u02bb', "'").replace('\u02bc', "'")

def get_section_wikitext(text, section_name, after_names=None):
    """Extract content of a wikitext section."""
    text = normalize_apos(text)
    section_name = normalize_apos(section_name)
    pat = re.compile(r'^==\s*' + re.escape(section_name) + r'\s*==\s*$', re.MULTILINE)
    m = pat.search(text)
    if not m:
        return ''
    start = m.end()
    
    if after_names:
        next_pat = re.compile(r'^==\s*(?:' + '|'.join(re.escape(n) for n in after_names) + r')\s*==', re.MULTILINE)
    else:
        next_pat = re.compile(r'^(?:={2,5}\s|==+[^=])', re.MULTILINE)
    
    after_m = next_pat.search(text, start)
    if after_m:
        end = after_m.start()
    else:
        end = len(text)
    
    return text[start:end].strip()

def get_subsection_wikitext(text, subsection_name):
    """Extract content of a subsection (=== Subsection ===)."""
    text = normalize_apos(text)
    subsection_name = normalize_apos(subsection_name)
    pat = re.compile(r'^===\s*' + re.escape(subsection_name) + r'\s*===\s*$', re.MULTILINE)
    m = pat.search(text)
    if not m:
        return ''
    start = m.end()
    # Match any heading: standard == Section == or non-standard ==Section==
    next_pat = re.compile(r'^(?:={2,5}\s|==+[^=])', re.MULTILINE)
    after_m = next_pat.search(text, start)
    end = after_m.start() if after_m else len(text)
    return text[start:end].strip()

def strip_wiki_markup(text):
    """Remove wiki markup from text."""
    # Remove bold/italic
    text = re.sub(r"'''?", '', text)
    # Remove specific templates cleanly
    text = re.sub(r'{{ajrat\|([^}]+)}}', r'\1', text)
    text = re.sub(r'{{izoh\|([^}]+)}}', r'(\1)', text)
    # Remove other templates (handle nesting crudely)
    while '{{' in text:
        new_text = re.sub(r'{{[^{}]*?}}', '', text)
        if new_text == text:
            break
        text = new_text
    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    # Remove links [[Text|display]] -> display or Text
    text = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', r'\2', text)
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    # Remove references
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'<ref[^>]*/>', '', text)
    # Unescape HTML entities
    text = text.replace('&amp;lt;', '&lt;')
    text = text.replace('&amp;gt;', '&gt;')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = text.replace('&nbsp;', ' ')
    # Remove bullet/list artifacts
    text = re.sub(r'^[#*•]\s*', '', text, flags=re.MULTILINE)
    # Clean up spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def strip_tags(text):
    """Remove HTML tags."""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&#160;', ' ')
    text = text.replace('&#9670;', '◆')
    text = html.unescape(text) if 'html' in sys.modules else text
    return text.strip()

def extract_examples_from_line(line):
    """Extract examples from {{misol|text|source}} templates."""
    # Preprocess: expand inner templates that might contain |
    line = re.sub(r'{{ajrat\|([^}]+)}}', r'\1', line)
    examples = []
    for m in re.finditer(r'{{misol\|([^}]+?)}}', line):
        content = m.group(1)
        # Split by | accounting for [[...]] links (top-level pipes only)
        parts = []
        depth = 0
        current = ''
        i = 0
        while i < len(content):
            if content[i:i+2] == '[[':
                depth += 1
                current += '[['
                i += 2
            elif content[i:i+2] == ']]':
                depth = max(0, depth - 1)
                current += ']]'
                i += 2
            elif content[i] == '|' and depth == 0:
                parts.append(current)
                current = ''
                i += 1
            else:
                current += content[i]
                i += 1
        parts.append(current)
        
        ex_text = parts[0].strip() if len(parts) > 0 else ''
        ex_source = parts[1].strip() if len(parts) > 1 else ''
        
        if ex_text:
            ex_text = strip_wiki_markup(ex_text)
            ex_source = strip_wiki_markup(ex_source) if ex_source else ''
            examples.append({"text": ex_text, "source": ex_source})
    return examples

def extract_definitions_wikitext(text):
    """Extract definitions and idioms from === Ma'nosi === section."""
    text = normalize_apos(text)
    # Also get content before === Ma'nosi === from parent == Ma'noviy xususiyatlari ==
    pre_content = ''
    parent_sec = get_section_wikitext(text, "Ma'noviy xususiyatlari", ['Tarjimalari'])
    if parent_sec:
        # Get everything before === Ma'nosi === (now normalized to regular ')
        m = re.search(r"^=== Ma'nosi ===\s*$", parent_sec, re.MULTILINE)
        if m:
            pre_content = parent_sec[:m.start()].strip()
            section = parent_sec[m.end():].strip()
        else:
            section = parent_sec
    else:
        section = ''
        pre_content = ''
    
    # If no parent section, try just the subsection
    if not section:
        section = get_subsection_wikitext(text, "Ma'nosi")
    if not section:
        return {"meanings": [], "idioms": []}
    
    # Combine pre-content (before === Ma'nosi ===) with the section content
    combined = pre_content + '\n' + section if pre_content else section
    
    # Strip subsections (=== ... ===) that are not the definitions section itself
    combined = re.sub(r'^=== +Sinonimlari +===\s*\n[\s\S]*?(?=^=== |\Z)', '', combined, flags=re.MULTILINE)
    combined = re.sub(r'^=== +Antonimlari +===\s*\n[\s\S]*?(?=^=== |\Z)', '', combined, flags=re.MULTILINE)
    
    # Split by numbered items (1. 2. or newline 1 2 3)
    lines = combined.split('\n')
    
    # Also handle <dd> items from parsed HTML
    dd_items = re.findall(r'<dd>(.*?)</dd>', section, re.DOTALL)
    
    meanings = []
    current_num = None
    current_def = ''
    current_examples = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for numbered definition
        m = re.match(r'(\d+)\s+(.*)', line)
        if m:
            # Save previous meaning
            if current_num is not None and current_def:
                meanings.append({
                    "number": str(current_num),
                    "definition": strip_wiki_markup(current_def).strip(),
                    "examples": current_examples
                })
            current_num = m.group(1)
            content = m.group(2)
            # Extract examples from the line
            examples = extract_examples_from_line(content)
            current_examples = examples
            current_def = content
        else:
            # Continuation of previous definition
            if current_def:
                current_def += ' ' + line
    
    # Save last meaning
    if current_num is not None and current_def:
        meanings.append({
            "number": str(current_num),
            "definition": strip_wiki_markup(current_def).strip(),
            "examples": current_examples
        })
    
    # Also process <dd> items as idioms if present
    idioms = []
    for dd in dd_items:
        dd_text = strip_wiki_markup(dd).strip()
        if dd_text:
            # Split by ◆ to get examples
            parts = dd_text.split('◆')
            def_text = parts[0].strip()
            ex_part = parts[1].strip() if len(parts) > 1 else ''
            
            # First phrase/definition separation
            m2 = re.match(r'(\S+(?:\s+\S+)*?)\s{2,}(.*)', def_text)
            if m2:
                phrase = m2.group(1)
                definition = m2.group(2)
            else:
                phrase = def_text
                definition = ''
            
            ex_obj = {"text": ex_part, "source": ""} if ex_part else {}
            idioms.append({
                "phrase": phrase,
                "definition": definition,
                "examples": [ex_obj] if ex_obj else []
            })
    
    result = {"meanings": meanings}
    if idioms:
        result["idioms"] = idioms
    return result

def extract_etymology_wikitext(text):
    """Extract etymology from wikitext."""
    text = normalize_apos(text)
    section = get_section_wikitext(text, "Etimologiyasi", ["Ma'noviy xususiyatlari", 'Tarjimalari'])
    if not section:
        return ''
    
    # Expand OʻTEL templates - they contain etymology text
    # Format: {{OʻTEL|I|text}} or {{OʻTEL|I|text}} where text may contain |
    def expand_otel(m):
        content = m.group(1)
        pipe_idx = content.find('|')
        if pipe_idx >= 0:
            return content[pipe_idx+1:]
        return m.group(0)
    
    # Match both apostrophe variants: U+02BB (ʻ) and U+02BC (ʼ)
    section = re.sub(r'{{O[ʻʼ\']TEL\|([^}]+)}}', expand_otel, section)
    section = re.sub(r"{{O'[ʻʼ']TEL\|([^}]+)}}", expand_otel, section)
    
    # Clean up
    lines = []
    for line in section.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Skip reference lines
        if line.startswith('<ref') or line.startswith('</ref'):
            continue
        # Skip lines that look like definitions (numbered)
        if re.match(r'^\d+\s', line) or re.match(r'^:\S', line):
            continue
        stripped = strip_wiki_markup(line)
        if stripped:
            lines.append(stripped)
    
    return ' '.join(lines)

def extract_synonyms_wikitext(text):
    """Extract synonyms from wikitext."""
    text = normalize_apos(text)
    section = get_subsection_wikitext(text, 'Sinonimlari')
    if not section:
        return ''
    return strip_wiki_markup(section).strip()

def extract_antonyms_wikitext(text):
    """Extract antonyms from wikitext."""
    text = normalize_apos(text)
    section = get_subsection_wikitext(text, 'Antonimlari')
    if not section:
        return ''
    return strip_wiki_markup(section).strip()

def extract_pos_wikitext(text):
    """Extract part of speech from category links."""
    text = normalize_apos(text)
    pos_map = {
        "ot so'zlar": 'ot',
        "fe'l so'zlar": "fe'l",
        'sifat': 'sifat',
        'son': 'son',
        'olmosh': 'olmosh',
        'ravish': 'ravish',
        'koʻmakchi': 'koʻmakchi',
        "ko'makchi": 'koʻmakchi',
        'bogʻlovchi': 'bogʻlovchi',
        "bog'lovchi": 'bogʻlovchi',
        'yuklama': 'yuklama',
        'taqlid': 'taqlid',
        'modal': 'modal',
        'nido': 'undov',
        'hol': 'hol',
    }
    # Find [[Turkum:O'zbekchada ...]] (text already normalized)
    for m in re.finditer(r"\[\[Turkum:O'zbekchada\s+([^\]]+)\]\]", text):
        cat = m.group(1).lower()
        for key, pos in pos_map.items():
            if key in cat:
                return pos
    return ''

def parse_uzbek_wikitext(wikitext, title):
    """Parse Uzbek Wiktionary wikitext into our JSON format."""
    result = {
        "word": title,
        "part_of_speech": extract_pos_wikitext(wikitext),
    }
    
    # Check if redirect
    if re.search(r'^#(?:REDIRECT|YO[\u02bb\u02bc\']+NALTIRISH)\b', wikitext, re.MULTILINE):
        result["redirect"] = True
        return result
    
    # Etymology
    etymology = extract_etymology_wikitext(wikitext)
    if etymology:
        result["etymology"] = etymology
    
    # Definitions
    defs = extract_definitions_wikitext(wikitext)
    if defs.get("meanings"):
        result["meanings"] = defs["meanings"]
    if defs.get("idioms"):
        result["idioms"] = defs["idioms"]
    
    # Synonyms/antonyms
    syn = extract_synonyms_wikitext(wikitext)
    if syn:
        result["synonyms"] = syn
    ant = extract_antonyms_wikitext(wikitext)
    if ant:
        result["antonyms"] = ant
    
    return result

# ============================================================
# Conversion to Latin
# ============================================================
def convert_entry_to_latin(entry):
    """Convert Cyrillic text in an entry to Latin."""
    if not entry:
        return entry
    
    entry = dict(entry)
    
    if 'etymology' in entry and entry['etymology']:
        entry['etymology'] = cyr_to_lat(entry['etymology'])
    
    if 'meanings' in entry:
        entry['meanings'] = [dict(m) for m in entry['meanings']]
        for m in entry['meanings']:
            if 'definition' in m and m['definition']:
                m['definition'] = cyr_to_lat(m['definition'])
            if 'examples' in m:
                for ex in m['examples']:
                    if 'text' in ex and ex['text']:
                        ex['text'] = cyr_to_lat(ex['text'])
                    if 'source' in ex and ex['source']:
                        ex['source'] = cyr_to_lat(ex['source'])
    
    if 'idioms' in entry:
        entry['idioms'] = [dict(i) for i in entry['idioms']]
        for idiom in entry['idioms']:
            for field in ('phrase', 'definition'):
                if field in idiom and idiom[field]:
                    idiom[field] = cyr_to_lat(idiom[field])
            if 'examples' in idiom:
                for ex in idiom['examples']:
                    if 'text' in ex and ex['text']:
                        ex['text'] = cyr_to_lat(ex['text'])
                    if 'source' in ex and ex['source']:
                        ex['source'] = cyr_to_lat(ex['source'])
    
    if 'synonyms' in entry and entry['synonyms']:
        entry['synonyms'] = cyr_to_lat(entry['synonyms'])
    if 'antonyms' in entry and entry['antonyms']:
        entry['antonyms'] = cyr_to_lat(entry['antonyms'])
    
    return entry

# ============================================================
# Merge into data files
# ============================================================
DATA_DIR = r'C:\Users\abu_y\izoh\data'

def read_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def write_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def get_letter_file(letter):
    letter_map = {
        'SH': 'Sh.json', 'CH': 'Ch.json', "O'": 'O_.json',
        'Oʻ': 'O_.json', "G'": 'G_.json', 'Gʻ': 'G_.json',
    }
    filename = letter_map.get(letter, f'{letter}.json')
    return os.path.join(DATA_DIR, filename)

def merge_new_entries(new_entries):
    """Merge Wiktionary entries into existing letter files."""
    # Read existing index
    index_path = os.path.join(DATA_DIR, 'index.json')
    existing_indices = read_json(index_path)
    existing_word_set = {w.lower() if isinstance(w, str) else w.get('word', '').lower() for w in existing_indices}
    
    added = 0
    skipped = 0
    letter_updates = {}  # letter -> list of new entries
    
    # Process each new entry
    for entry in new_entries:
        word = entry.get('word', '')
        word_lower = word.lower()
        
        # Skip if already exists
        if word_lower in existing_word_set:
            skipped += 1
            continue
        
        # Get letter
        letter = letter_of(word)
        
        # Add to index
        if isinstance(existing_indices, list) and existing_indices and isinstance(existing_indices[0], str):
            existing_indices.append(word)
        else:
            existing_indices.append({"word": word, "url": f"https://izoh.uz/word/{word}"})
        
        existing_word_set.add(word_lower)
        
        # Group by letter for file updates
        if letter not in letter_updates:
            letter_updates[letter] = []
        letter_updates[letter].append(entry)
        added += 1
        
        if added % 1000 == 0:
            print(f"  Processed {added} entries...")
    
    # Write updated index
    write_json(index_path, existing_indices)
    print(f"Index updated: {added} added, {skipped} skipped")
    
    # Update per-letter files
    for letter, entries in letter_updates.items():
        letter_path = get_letter_file(letter)
        existing = read_json(letter_path)
        
        # Create a word lookup for existing entries
        existing_dict = {e.get('word', '').lower(): e for e in existing if isinstance(e, dict) and 'word' in e}
        
        for entry in entries:
            word_lower = entry.get('word', '').lower()
            if word_lower not in existing_dict:
                existing.append(entry)
                existing_dict[word_lower] = entry
        
        write_json(letter_path, existing)
        safe_letter = letter.replace('\u02bb', "'").replace('\u02bc', "'")
        safe_path = letter_path.replace('\u02bb', "'").replace('\u02bc', "'")
        print(f"  {safe_letter}: added {len(entries)} entries to {safe_path}")
    
    return added, skipped

# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    import sys
    import html  # for strip_tags
    
    # Load new entries
    with open(r'C:\Users\abu_y\izoh\uzbek_new_entries.json', 'r', encoding='utf-8') as f:
        new_entries_raw = json.load(f)
    
    print(f"Loaded {len(new_entries_raw)} new entries from Wiktionary")
    
    # Parse each entry from wikitext
    parsed_entries = []
    for i, entry in enumerate(new_entries_raw):
        title = entry['title']
        wikitext = entry['text']
        
        # Skip redirects
        if re.search(r'^#(?:REDIRECT|YO[\u02bb\u02bc\']+NALTIRISH)\b', wikitext, re.MULTILINE):
            continue
        
        # Skip suffixes/prefixes
        if title.startswith('-') or (len(title) > 1 and title.endswith('-')):
            continue
        
        # Skip entries starting with uppercase that aren't O'/G'
        if re.match(r"^[A-Z]", title) and not title.startswith("O'") and not title.startswith('Oʻ') and not title.startswith("G'") and not title.startswith('Gʻ'):
            continue
        
        # Skip multi-word entries
        if ' ' in title:
            continue
        
        try:
            parsed = parse_uzbek_wikitext(wikitext, title)
            
            # Skip entries with no meaningful content
            if not parsed.get('meanings') and not parsed.get('etymology'):
                continue
            
            # Convert to Latin
            converted = convert_entry_to_latin(parsed)
            parsed_entries.append(converted)
        except Exception as e:
            safe_title = title.replace('\u02bb', "'").replace('\u02bc', "'")
            print(f"  Error parsing '{safe_title}': {e}")
        
        if (i + 1) % 2000 == 0:
            print(f"  Parsed {i + 1}/{len(new_entries_raw)}...")
    
    print(f"\nParsed {len(parsed_entries)} useful entries out of {len(new_entries_raw)}")
    
    # Merge into data files
    print("\nMerging into data files...")
    added, skipped = merge_new_entries(parsed_entries)
    print(f"\nDone! Added {added}, skipped {skipped}")
