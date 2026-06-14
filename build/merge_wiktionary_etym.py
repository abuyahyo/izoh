"""Merge Wiktionary etymology into existing data files.

Reads each letter file once, applies all etymology updates,
then saves. This avoids re-read bugs where a file is opened
fresh for each word and earlier in-file modifications are lost.
"""
import json, re, os, glob, sys
sys.stdout.reconfigure(encoding='utf-8')

# Load combined Wiktionary results
with open(r'C:\Users\abu_y\izoh\wiktionary_43_combined.json', 'r', encoding='utf-8') as f:
    wiktionary_data = json.load(f)

# Cyrillic → Latin mapping (from parse_5vol.py / cyr_to_lat)
CYR_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
    'е': 'e', 'ё': 'yo', 'ж': 'j', 'з': 'z', 'и': 'i',
    'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
    'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
    'у': 'u', 'ф': 'f', 'х': 'x', 'ц': 'ts', 'ч': 'ch',
    'ш': 'sh', 'щ': 'sh', 'ъ': '', 'ы': 'i', 'ь': '',
    'э': 'e', 'ю': 'yu', 'я': 'ya', 'ў': 'o', 'қ': 'q',
    'ғ': 'g', 'ҳ': 'h',
}
for k, v in list(CYR_MAP.items()):
    CYR_MAP[k.upper()] = v.upper() if v else v
CYR_MAP['Ў'] = "O"
CYR_MAP['Ё'] = "Yo"

def cyr_to_lat(text):
    result = []
    for ch in text:
        result.append(CYR_MAP.get(ch, ch))
    return ''.join(result)

ABBR_CYR = {
    'а.': 'арабча', 'б.': 'башқа', 'в.': 'ва',
    'г.': 'гуман', 'ғ.': 'ғарб', 'д.': 'демак',
    'ж.': 'жануб', 'з.': 'зоҳиран', 'и.': 'исм',
    'й.': 'йўналиш', 'к.': 'каби', 'л.': 'лол',
    'м.': 'масалан', 'н.': 'наҳв', 'о.': 'оят',
    'п.': 'панжа', 'р.': 'рад', 'с.': 'саналмоқ',
    'т.': 'тур', 'у.': 'умум', 'ф.': 'форсча',
    'х.': 'хусусан', 'ц.': 'цензор', 'ч.': 'чунончи',
    'ш.': 'шарқ', 'ъ.': 'айн', 'ы.': 'ырым',
    'ь.': 'белги', 'э.': 'эски', 'ю.': 'юнонча',
    'я.': 'яъни',
    'ў.': 'ўзбекча', 'қ.': 'қаранг',
    'а .': 'арабча',
    'инг.': 'инглизча', 'лот.': 'лотинча',
    'нем.': 'немисча', 'фр.': 'французча',
    'ит.': 'италянча', 'исп.': 'испанча',
}

def expand_abbr_cyr(text):
    result = text
    for abbr, full in sorted(ABBR_CYR.items(), key=lambda x: -len(x[0])):
        result = result.replace(abbr, full)
    return result

def clean_etymology(text):
    if not text:
        return ""
    text = text.lstrip('|\\/')
    text = text.replace('\n', ' ').replace('\r', '')
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()
    text = expand_abbr_cyr(text)
    text = cyr_to_lat(text)
    return text


def main():
    data_dir = r'C:\Users\abu_y\izoh\data'

    # Build lookup: word_lower -> (wiktionary_word, etymology)
    word_map = {}
    for word, wdata in wiktionary_data.items():
        etymology = wdata.get('etymology')
        if etymology:
            word_map[word.lower()] = (word, etymology)

    # Process each letter file once
    updated_count = 0
    saved_count = 0

    for filepath in sorted(glob.glob(os.path.join(data_dir, '*.json'))):
        fname = os.path.basename(filepath)
        if fname in ('index.json', 'letters.json'):
            continue

        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        modified = False
        for entry in data:
            w = entry.get('word', '').lower()
            if w in word_map:
                orig_word, etymology = word_map[w]
                if not entry.get('etymology'):
                    cleaned = clean_etymology(etymology)
                    if cleaned:
                        entry['etymology'] = cleaned
                        print(f'  {orig_word}: ADDED -> {fname}')
                        updated_count += 1
                        modified = True
                    else:
                        print(f'  {orig_word}: cleaned etymology is empty')
                else:
                    print(f'  {orig_word}: already has etymology, skipping')

        # Save if modified
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=None, separators=(',', ':'))
            saved_count += 1
            print(f'  Saved {fname}')

    print(f'\n=== SUMMARY ===')
    print(f'Total etymology words from Wiktionary: {len(word_map)}')
    print(f'Updated in data: {updated_count}')
    print(f'Files saved: {saved_count}')


if __name__ == "__main__":
    main()
