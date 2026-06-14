"""
Parse the 5-volume "O'zbek tilining izohli lug'ati" (OCR text)
into per-letter JSON files matching the SPA format.

Usage:
    python build/parse_5vol.py
"""

import re
import json
import pathlib
from collections import defaultdict

SRC = pathlib.Path(r"C:\Users\abu_y\Desktop\izohli lug'at.txt")
DATA_DIR = pathlib.Path(r"C:\Users\abu_y\izoh\data")
OUT_DIR = pathlib.Path(r"C:\Users\abu_y\izoh\data")

CYR_MAP = {
    'ё':'yo','Ё':'Yo','ю':'yu','Ю':'Yu','я':'ya','Я':'Ya',
    'ч':'ch','Ч':'Ch','ш':'sh','Ш':'Sh','ў':"o'","Ў":"O'",
    'ғ':"g'","Ғ":"G'",
    'а':'a','А':'A','б':'b','Б':'B','в':'v','В':'V','г':'g','Г':'G',
    'д':'d','Д':'D','е':'e','Е':'E','ж':'j','Ж':'J','з':'z','З':'Z',
    'и':'i','И':'I','й':'y','Й':'Y','к':'k','К':'K','қ':'q','Қ':'Q',
    'л':'l','Л':'L','м':'m','М':'M','н':'n','Н':'N','о':'o','О':'O',
    'п':'p','П':'P','р':'r','Р':'R','с':'s','С':'S','т':'t','Т':'T',
    'у':'u','У':'U','ф':'f','Ф':'F','х':'x','Х':'X','ҳ':'h','Ҳ':'H',
    'ц':'s','Ц':'S','щ':'shch','Щ':'Shch','ъ':"'",'ь':'','ы':'i','Ы':'I',
    'э':'e','Э':'E','\u02bb':"'",
}

CYR_RE = re.compile(r'[Ѐ-ӿ\u02bb]')
CYR_UPPER = set('АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯЎҚҒҲ')
CYR_ALL = set('АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯЎҚҒҲа-яёўқғҳ')

def is_uppercase_word(s: str) -> bool:
    """Check if string starts with 2+ uppercase Cyrillic chars (headword)."""
    if not s:
        return False
    # Headwords are ALL-UPPERCASE for at least 2 chars
    count = 0
    for ch in s:
        if ch in CYR_UPPER:
            count += 1
            if count >= 2:
                return True
        elif ch == '-':
            continue  # Hyphenated words are ok (АБ-ЖАД)
        else:
            return False
    return count >= 2

def starts_with_upper_then_lower(s: str) -> bool:
    """Check if string starts with single uppercase followed by lowercase (idiom/continuation)."""
    if not s or len(s) < 2:
        return False
    return s[0] in CYR_UPPER and len(s) > 1 and s[1] not in CYR_UPPER

def cyr_to_lat(s: str) -> str:
    if not s or not CYR_RE.search(s):
        return s
    return ''.join(CYR_MAP.get(ch, ch) for ch in s)

def letter_of(word: str) -> str:
    w = word.strip()
    if not w:
        return "?"
    for p in ["O'", "G'", "O\u2018", "G\u2018", "O\u2019", "G\u2019",
              "o'", "g'", "o\u2018", "g\u2018", "o\u2019", "g\u2019"]:
        if w.startswith(p):
            return p[0].upper() + "'"
    for p in ["Sh", "Ch", "SH", "CH", "sh", "ch"]:
        if w.startswith(p):
            return p[0].upper() + p[1].lower()
    return w[0].upper()

def join_hyphenated(text: str) -> str:
    return re.sub(r'(\w)-\s*\n\s*', r'\1', text)

POS_ABBR = sorted([
    'от', 'сфт', 'фл', 'рвш', 'юкл', 'кўм', 'боғл', 'мод',
    'сон', 'олм', 'унд', 'тах', 'предл', 'бур',
    'эск.', 'кт.', 'шв.', 'с.т.', 'тар.', 'кам.', 'айн.', 'к.',
    'махс.', 'поэт.', 'диал.',
    'биол.', 'тиб.', 'ким.', 'физ.', 'мат.', 'линг.',
    'фалс.', 'мус.', 'дин.', 'хук.', 'сиёс.', 'иқт.',
    'ад.', 'зоо.', 'бот.', 'геог.', 'геол.', 'тех.', 'хим.',
    'этн.', 'руҳ.', 'наҳ.', 'мун.', 'тил.', 'сан.',
], key=len, reverse=True)

POS_PATTERN = re.compile(r'^\s*(' + '|'.join(re.escape(p) for p in POS_ABBR) + r')\s*')

POS_MAP = {
    'от': 'ot', 'сфт': 'sifat', 'фл': "fe'l", 'рвш': 'ravish',
    'юкл': 'yuklama', 'кўм': "ko'makchi", 'боғл': "bog'lovchi",
    'мод': "modal so'z", 'сон': 'son', 'олм': 'olmosh',
    'унд': 'undov', 'тах': 'taqlid', 'предл': 'predlog',
    'бур': 'burun',
    'эск': 'eskirgan', 'кт': 'kitobiy', 'шв': 'sheva',
    'с.т': "so'zlashuv tili", 'тар': 'tarixiy', 'айн': 'aynan',
    'кам': 'kam qoʻllanadi', 'к': 'qisqa', 'махс': 'maxsus',
    'поэт': 'poetik', 'диал': 'dialekt',
    'биол': 'biologiya', 'тиб': 'tibbiyot', 'ким': 'kimyo',
    'физ': 'fizika', 'мат': 'matematika', 'линг': 'tilshunoslik',
    'фалс': 'falsafa', 'мус': 'musiqa', 'дин': 'din',
    'хук': 'huquq', 'сиёс': 'siyosiy',
    'иқт': 'iqtisod', 'ад': 'adabiyot',
    'зоо': 'zoologiya', 'бот': 'botanika',
    'геог': 'geografiya', 'геол': 'geologiya',
    'тех': 'texnika', 'хим': 'ximiya',
    'этн': 'etnografiya', 'руҳ': 'ruhshunoslik',
    'наҳ': 'nahv', 'мун': 'munozara',
    'тил': 'tilshunoslik', 'сан': "san'at",
    'тлш': 'tilshunoslik',
}

def normalize_pos(pos: str) -> str:
    p = pos.strip().lower().rstrip('.')
    if p in POS_MAP:
        return POS_MAP[p]
    return p

def extract_etymology(line: str) -> tuple:
    m = re.match(r'^(.*?)\[([^\]]*)\](.*)$', line)
    if m:
        before = m.group(1).strip()
        etymology = m.group(2).strip()
        after = m.group(3).strip()
        return (before + ' ' + after, etymology)
    return (line, None)


def extract_etymology_full(text: str) -> tuple:
    """Extract etymology from full entry text, handling multi-line [...] brackets.
    Falls back to '|' as closing bracket (OCR misread ']' as '|')."""
    # Try standard [...] first
    m = re.match(r'^\s*(\[[\s\S]*?\])\s*(.*)$', text, re.DOTALL)
    if m:
        bracket_content = m.group(1)
        rest = m.group(2)
        etymology = bracket_content[1:-1].strip()
        etymology = ' '.join(etymology.split())
        return (rest, etymology)
    # Try [ ... | as fallback (OCR substitutes '|' for missing ']')
    m = re.match(r'^\s*(\[[\s\S]*?\|)\s*(.*)$', text, re.DOTALL)
    if m:
        bracket_content = m.group(1)
        rest = m.group(2)
        etymology = bracket_content[1:-1].strip()
        etymology = ' '.join(etymology.split())
        return (rest, etymology)
    return (text, None)

def extract_headword(first_line: str) -> tuple:
    # Pattern: 2+ uppercase Cyrillic chars optionally with hyphen
    m = re.match(r'^([А-ЯЁЎҚҒҲ][А-ЯЁЎҚҒҲ\-]+[А-ЯЁЎҚҒҲа-яёўқғҳ]*)', first_line)
    if m:
        hw_cyr = m.group(1).rstrip('-')
        rest = first_line[m.end():].strip()
        hw_lat = cyr_to_lat(hw_cyr)
        # Handle homonyms: БОҒ I -> БОҒ I
        if rest.startswith(('I', 'II', 'III', 'IV', 'V')):
            hw_cyr += ' ' + rest.split()[0]
            hw_lat += ' ' + rest.split()[0]
            rest = rest[len(rest.split()[0]):].strip()
        return (rest, hw_lat, hw_cyr)
    return (first_line, None, None)


def parse_entries(text: str) -> list:
    """Parse dictionary entries from OCR text.
    
    Returns list of dicts with keys: word, part_of_speech, meanings, idioms
    """
    text = join_hyphenated(text)
    lines = text.split('\n')
    
    # Find where actual entries start (first headword)
    start = 0
    for i in range(1600, min(2000, len(lines))):
        l = lines[i].strip()
        if is_uppercase_word(l) and '[' in l:
            start = i
            break
    
    entries = []
    current_entry = None
    current_text_lines = []
    
    def flush_entry():
        nonlocal current_entry, current_text_lines
        if current_entry is None:
            return
        # Process all accumulated text
        full_text = '\n'.join(current_text_lines)
        # Try to extract multi-line etymology from full text
        if not current_entry.get('etymology'):
            cleaned_text, etymology = extract_etymology_full(full_text)
            if etymology:
                current_entry['etymology'] = etymology
                full_text = cleaned_text
        meanings, idioms = parse_meanings_idioms(full_text, current_entry['hw_lat'])
        current_entry['meanings'] = meanings
        current_entry['idioms'] = idioms
        entries.append(current_entry)
        current_entry = None
        current_text_lines = []
    
    for i in range(start, len(lines)):
        line = lines[i]
        stripped = line.strip()
        
        if not stripped:
            continue
        
        if is_uppercase_word(stripped):
            # New headword entry
            flush_entry()
            
            rest, hw_lat, hw_cyr = extract_headword(stripped)
            if hw_lat is None:
                continue
            # Skip very short abbreviations
            # These are likely OCR noise within example text
            CYR_VOWELS = set('АОУИЕЭЁЮЯЎ')
            vowel_count = sum(1 for ch in hw_cyr.split()[0] if ch in CYR_VOWELS)
            if len(hw_cyr.split()[0]) <= 4 and vowel_count == 0:
                continue
            
            # Extract etymology
            rest, etymology = extract_etymology(rest)
            
            # Extract POS
            pos = ''
            m = POS_PATTERN.match(rest)
            if m:
                pos = normalize_pos(m.group(1))
                rest = rest[m.end():].strip()
            
            # Remove leading number (def count)
            rest = re.sub(r'^\d+\s*\)?\s*', '', rest).strip()
            
            current_entry = {
                'word': hw_lat.lower(),
                'hw_lat': hw_lat,
                'hw_cyr': hw_cyr,
                'part_of_speech': pos,
                'meanings': [],
                'idioms': [],
                'etymology': etymology or '',
                'text_start': rest,
            }
            current_text_lines = [rest] if rest else []
        elif current_entry is not None:
            # Continuation or idiom
            current_text_lines.append(stripped)
    
    flush_entry()
    return entries


def parse_meanings_idioms(text: str, word_lat: str) -> tuple:
    """Parse definitions and idioms from entry text.
    Returns (meanings, idioms).
    """
    if not text or not text.strip():
        return ([{"definition": "", "examples": []}], [])
    
    # Convert Cyrillic to Latin
    text = cyr_to_lat(text)
    
    # Try to split into numbered definitions
    # Pattern: number at start of line (1, 2, 3...)
    def_parts = re.split(r'(?:^|\n)\s*(\d+)\s*\)?\s*(?=[A-Za-z])', text)
    
    if len(def_parts) < 3:
        # Single definition
        def_text, examples = extract_examples(text.strip())
        if def_text:
            return ([{"definition": def_text, "examples": examples}], [])
        return ([{"definition": text.strip(), "examples": []}], [])
    
    meanings = []
    idioms = []
    
    i = 1
    while i < len(def_parts):
        num = def_parts[i]
        i += 1
        content = def_parts[i].strip() if i < len(def_parts) else ''
        i += 1
        
        if not content:
            continue
        
        def_text, examples = extract_examples(content)
        
        if def_text:
            # Check if this is an idiom (starts with lowercase or specific pattern)
            if def_text[0].islower() and ' ' in def_text[:30]:
                # Looks like an idiom: "to abad Abadiy suratda..."
                meanings.append({"definition": def_text, "examples": examples})
            else:
                meanings.append({"definition": def_text, "examples": examples})
    
    if not meanings:
        meanings.append({"definition": text.strip(), "examples": []})
    
    return (meanings, idioms)


def extract_examples(text: str) -> tuple:
    """Extract examples from definition text.
    Returns (definition_text, [{text, source}]).
    """
    if not text:
        return ('', [])
    
    # Text is already in Latin at this point.
    # ' n ' marker (originally Cyrillic 'н') separates def from examples
    parts = re.split(r'\s+n\s+', text, maxsplit=1)
    
    if len(parts) == 1:
        return (text.strip(), [])
    
    def_text = parts[0].strip()
    example_text = parts[1].strip()
    
    examples = []
    if example_text:
        ex_parts = re.split(r'\s+n\s+', example_text)
        for ep in ex_parts:
            ep = ep.strip()
            if ep:
                ex, source = extract_source(ep)
                examples.append({"text": ex, "source": source})
    
    return (def_text, examples)


def extract_source(text: str) -> tuple:
    """Extract source citation from end of example text."""
    if not text:
        return ('', '')
    
    text = text.strip().rstrip('.')
    
    # Match Latin-ized source patterns (text already converted to Latin)
    # "Example text. A. Qahhor, Sarob" or "Example text. Oybek, Navoiy"
    LATIN_UPPER = r'[A-Z\u0100-\u017f]'
    LATIN_LOWER = r'[a-z\u0100-\u017f]'
    
    # "Example text. Author Surname, Work"
    m = re.match(r'^(.+?)\.\s+(' + LATIN_UPPER + LATIN_LOWER + r'+\..*?)$', text)
    if m:
        return (m.group(1).strip(), m.group(2).strip())
    
    # "Example text. A. Surname" (initial)
    m = re.match(r'^(.+?)\.\s+(' + LATIN_UPPER + r'\.' + LATIN_UPPER + LATIN_LOWER + r'+\s+[A-Za-z\u0100-\u017f\-]+)$', text)
    if m:
        return (m.group(1).strip(), m.group(2).strip())
    
    if text.endswith('Gazetadan'):
        return (text[:-9].strip(), 'Gazetadan')
    
    return (text, '')


def split_into_idioms(text: str) -> tuple:
    """Split text into definition part and idiom part.
    
    Idioms are lines that start with an uppercase+lowercase word
    that is NOT the same as the headword.
    """
    lines = text.split('\n')
    def_lines = []
    idiom_lines = []
    in_idioms = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if starts_with_upper_then_lower(stripped):
            in_idioms = True
        if in_idioms:
            idiom_lines.append(stripped)
        else:
            def_lines.append(stripped)
    
    return ('\n'.join(def_lines), '\n'.join(idiom_lines))


def merge_with_existing(new_entries: list, existing_data: dict) -> dict:
    result = defaultdict(list, {k: list(v) for k, v in existing_data.items()})
    
    existing_words = set()
    for letter, recs in result.items():
        for rec in recs:
            w = rec.get('word', '').lower().strip()
            if w:
                existing_words.add(w)
    
    added = 0
    skipped = 0
    for entry in new_entries:
        w = entry.get('word', '').lower().strip()
        if not w:
            skipped += 1
            continue
        if w in existing_words:
            skipped += 1
            continue
        
        letter = letter_of(w)
        # Remove internal fields
        out_entry = {
            'word': entry['word'],
            'part_of_speech': entry['part_of_speech'],
            'meanings': entry['meanings'],
            'idioms': entry['idioms'],
        }
        result[letter].append(out_entry)
        existing_words.add(w)
        added += 1
    
    return dict(result), added, skipped


VALID_LETTERS = {'A','B','Ch','D','E','F','G',"G'",'H','I','J','K','L','M','N','O',"O'",'P','Q','R','S','Sh','T','U','V','X','Y','Z'}

def write_data_files(merged: dict):
    index = []
    
    for letter, recs in sorted(merged.items()):
        if letter not in VALID_LETTERS:
            print(f"  [!] Skipping unknown letter: {letter}")
            continue
        recs.sort(key=lambda r: (r.get('word', '') or '').casefold())
        safe = letter.replace("'", "_")
        path = OUT_DIR / f"{safe}.json"
        path.write_text(
            json.dumps(recs, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        words_in_letter = [rec.get('word', '') for rec in recs]
        index.extend(words_in_letter)
        print(f"  {letter:>3}  {len(recs):>5} words  ->  {path.name}")
    
    index.sort(key=lambda x: (x or '').casefold())
    idx_path = OUT_DIR / "index.json"
    idx_path.write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"\n[+] Global index: {len(index)} words")
    
    manifest = []
    for letter, recs in sorted(merged.items()):
        safe = letter.replace("'", "_")
        manifest.append({"letter": letter, "file": f"{safe}.json", "count": len(recs)})
    manifest_path = OUT_DIR / "letters.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[+] Letters manifest")


def main():
    print("[*] Reading source file...")
    text = SRC.read_text(encoding="utf-8")
    print(f"    {len(text)} chars, ~{text.count(chr(10))} lines")
    
    print("[*] Parsing dictionary entries...")
    entries = parse_entries(text)
    print(f"    Parsed {len(entries)} entries")
    
    if len(entries) == 0:
        print("[!] No entries parsed!")
        return
    
    # Save parsed entries for inspection
    sample = entries[:20]
    sample_path = pathlib.Path(r'C:\Users\abu_y\Desktop\parsed_sample.json')
    sample_path.write_text(
        json.dumps(sample, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"    Sample saved to {sample_path}")
    
    # Load existing data
    print("[*] Loading existing data...")
    existing = defaultdict(list)
    for letter_file in sorted(DATA_DIR.glob("[A-Z]*.json")):
        stem = letter_file.stem
        if stem in ('index', 'index_ocr', 'letters', 'C') or stem.startswith('izoh_ocr'):
            continue
        data = json.loads(letter_file.read_text(encoding="utf-8"))
        if data:
            letter = stem.replace('_', "'")
            existing[letter] = data
            print(f"    Loaded {len(data)} existing records for letter {letter}")
    
    print(f"\n[*] Merging...")
    merged, added, skipped = merge_with_existing(entries, existing)
    print(f"    Added: {added}, Skipped (exists): {skipped}")
    
    print("\n[*] Writing data files...")
    write_data_files(merged)
    
    print("\n[+] Done!")


if __name__ == "__main__":
    main()
