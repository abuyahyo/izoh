import re
import json
from pathlib import Path
from statistics import median

OCR_PATH = Path.home() / "Desktop" / "Izohli_Lugat_5jild_OCR.txt"
OUT_DIR = Path.home() / "izoh" / "data"
OUT_RECORDS = Path.home() / "Desktop" / "izoh_parsed_records.json"
LOG_PATH = Path.home() / "Desktop" / "parse_log.txt"

HW_RE = re.compile(r'[А-ЯЁЎҒҚҲ]{2,}(?:-[А-ЯЁЎҒҚҲ]{2,})?')
PAGE_RE = re.compile(r'^--- Page \d+ .+\.jpg\) ---')
ETYM_RE = re.compile(r'\([а-яёўғқҳa-z]+\.\s*[^)]*\)')
EXAMPLE_MARKER = 'шш'

POS_MARKERS = {
    'от', 'феъл', 'сифат', 'рвш', 'кўм', 'богл', 'юкл', 'мод',
    'олм', 'сон', 'унд', 'тақл', 'крш', 'айн',
    'эск', 'кт', 'с.т', 'кўчма', 'кам қўлл',
    'ив', 'шв', 'поэт', 'мус', 'тиб', 'биол', 'ким', 'физ',
    'тех', 'иқт', 'ҳуқ', 'астр', 'дин', 'тар',
}

SKIP_WORDS = {
    'ЎЗБЕКИСТОН', 'ЎЗБЕКИСТОННРЕСПУБПИКАСИ', 'АЛИШЕР', 'ТАҲРИР',
    'ДАВЛАТ', 'БИРИНЧИ', 'ДИРЕКТОР', 'ТИЛ', 'ФАНЛАР',
    'МАЗКУР', 'ЛУҒАТ', 'ШУНДАЙ', 'УШБУ', 'МУАЛЛИФ',
    'ТОШКЕНТ', 'ИСБН', 'ББК', 'АДАДИ', 'ФАКС', 'EMAIL',
    'ИЗОҲЛИ', 'УЗБЕК', 'УЧУН', 'РАҲМАТ', 'НАВОИЙ', 'БОБУР',
    'СБОРНИК', 'РЕСПУБЛИКА', 'МУНДАРИЖА', 'ХАЛҚ', 'МАРКАЗИЙ',
    'КЕЙИНГИ', 'БУНДАН', 'ОЛДИНГИ', 'РУЙХАТДАН',
}

NOISE_RE = re.compile(r'^[\s\d\-\—\|\/\\]+$')
PAGE_NUM_RE = re.compile(r'^\s*\d+\s+\d+.*$')
COL_MARKER_RE = re.compile(r'^[a-zA-Z]\s+\d+\s+\d+')
SINGLE_LETTER_RE = re.compile(r'^\s*[a-zA-Z]\s*$')


def is_noise(line):
    s = line.strip()
    if not s or s.startswith('--- Page') or s in ('—',):
        return True
    if NOISE_RE.match(s):
        return True
    if PAGE_NUM_RE.match(s):
        return True
    if COL_MARKER_RE.match(s):
        return True
    if SINGLE_LETTER_RE.match(s):
        return True
    return False


def find_all_headwords(line):
    results = []
    for m in HW_RE.finditer(line):
        word = m.group()
        if word not in SKIP_WORDS:
            results.append((m.start(), word))
    return results


def is_ocr_junk(word):
    if len(word) <= 1:
        return True
    if word in ('АА', 'АБ', 'АБЗ', 'ҲФ', 'ҲХ', 'ҲЭ'):
        return True
    if len(re.findall(r'[ЁЁё]', word)) >= 3:
        return True
    if len(word) >= 5:
        repeated = max(word.count(c) for c in set(word))
        if repeated >= len(word) - 1:
            return True
    cyrillic = sum(1 for c in word if 0x0400 <= ord(c) <= 0x04FF or c in 'ЎҒҚҲўғқҳ')
    ratio = cyrillic / max(len(word), 1)
    if ratio < 0.5:
        return True
    if any(c in word for c in '{}[];:!@#$%^&*="'):
        return True
    return False


def is_junk_text(text):
    """Check if DEFINITION TEXT looks like OCR garbage."""
    clean_chars = sum(1 for c in text if c.isalpha() or c.isspace())
    if clean_chars < len(text) * 0.4:
        return True
    return False


def separate_columns(page_lines, default_split=33):
    left_parts, right_parts = [], []
    current_split = default_split

    for line in page_lines:
        if is_noise(line):
            continue

        hws = find_all_headwords(line)
        n = len(line)

        if len(hws) >= 2:
            current_split = hws[1][0]
            left_parts.append(line[:current_split].strip())
            right_parts.append(line[current_split:].strip())
        elif len(hws) == 1:
            pos, hw = hws[0]
            if pos < current_split:
                left_parts.append(line.strip())
                right_parts.append(line[current_split:].strip() if n > current_split else '')
            else:
                left_parts.append(line[:current_split].strip() if n > current_split else '')
                right_parts.append(line.strip())
        else:
            if n > current_split:
                left_parts.append(line[:current_split].strip())
                right_parts.append(line[current_split:].strip())
            else:
                left_parts.append(line.strip())
                right_parts.append(line.strip())

    return '\n'.join(left_parts), '\n'.join(right_parts)


def extract_entries(text):
    if not text.strip():
        return []
    entries = []
    lines = text.split('\n')
    current_hw = None
    current_text = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if is_noise(line):
            continue

        hws = find_all_headwords(line)

        if not hws:
            if current_text and current_text[-1].endswith('-'):
                current_text[-1] = current_text[-1].rstrip('-').strip()
                if line.startswith('-'):
                    line = line[1:].strip()
            current_text.append(line)
        else:
            for i, (pos, hw) in enumerate(hws):
                if i == 0:
                    before = line[:pos].strip()
                    if current_hw:
                        if before:
                            current_text.append(before)
                        entries.append((current_hw, ' '.join(current_text)))
                    elif before:
                        current_text.append(before)

                    current_hw = hw
                    current_text = [line[pos:].strip()]
                else:
                    pass

    if current_hw and (' '.join(current_text)).strip():
        entries.append((current_hw, ' '.join(current_text)))

    return entries


def clean_ocr_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)
    text = text.replace('  ', ' ').replace('..', '…').strip()
    return text


def extract_source(text):
    m = re.search(r'\(([^)]+)\)\s*$', text)
    return m.group(1) if m else ''


def split_definitions(text, headword):
    parts = re.split(r'[.)]\s+(?=[1-9]\s(?!\d))', text)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) <= 1:
        return [text.strip()]
    # Merge fragments: if a part starts with ( and has no sentence-ending period, merge with next
    merged = []
    for p in parts:
        if merged and p.startswith('(') and '.' not in p:
            merged[-1] += ' ' + p
        elif merged and not p.startswith(('А', 'Б', 'В', 'И', 'Қ', 'Ў', 'Ҳ')) and len(p) < 40 and '.' not in p:
            merged[-1] += ' ' + p
        else:
            merged.append(p)
    return merged if merged else [text.strip()]


def parse_entry(headword, text):
    if is_ocr_junk(headword):
        return None

    text = clean_ocr_text(text)
    if not text or len(text) < 3:
        return None
    if is_junk_text(text):
        return None

    etymology = ''
    et_m = ETYM_RE.search(text)
    if et_m:
        etymology = et_m.group()

    main_text = text[len(headword):].strip()
    if etymology and etymology in main_text:
        main_text = main_text.replace(etymology, '').strip()
    main_text = main_text.lstrip(' .,;:—')

    examples = []
    if EXAMPLE_MARKER in main_text:
        parts = main_text.split(EXAMPLE_MARKER)
        def_text = parts[0].strip()
        for ex in parts[1:]:
            ex = ex.strip()
            if ex:
                examples.append({
                    "text": ex,
                    "source": extract_source(ex)
                })
    else:
        def_text = main_text

    pos = ''
    pos_match = re.match(r'(\S+)\s+', def_text)
    if pos_match:
        candidate = pos_match.group(1).lower().rstrip('.')
        if candidate in POS_MARKERS or candidate.rstrip('.') in POS_MARKERS:
            pos = candidate.rstrip('.')
            def_text = def_text[len(pos_match.group()):].strip()
        elif re.match(r'^\d', candidate):
            pass

    defs = split_definitions(def_text, headword)
    meanings_list = []
    for d in defs:
        if d and len(d) > 2:
            meanings_list.append({
                "definition": d.lstrip('1. ').strip(),
                "examples": examples if len(defs) == 1 else []
            })

    if not meanings_list:
        return None

    return {
        "url": "https://lugat.uz/word/{}".format(headword.lower()),
        "word": headword,
        "part_of_speech": pos,
        "meanings": meanings_list,
        "idioms": []
    }


def compute_global_split_point(lines, page_starts):
    positions = []
    for idx in range(len(page_starts)):
        start = page_starts[idx][0]
        end = page_starts[idx + 1][0] if idx + 1 < len(page_starts) else len(lines)
        pm = PAGE_RE.match(page_starts[idx][1])
        pg = int(pm.group().split()[2]) if pm else 0
        if pg < 29 or pg > 3200:
            continue
        for l in lines[start:end]:
            hws = find_all_headwords(l)
            if len(hws) >= 2:
                positions.append(hws[1][0])
    return int(median(positions)) if positions else 33


def main():
    print("Reading OCR file...")
    with open(OCR_PATH, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
    print("Total lines: {}".format(len(all_lines)))

    page_starts = [(i, all_lines[i]) for i in range(len(all_lines)) if PAGE_RE.match(all_lines[i])]
    print("Pages found: {}".format(len(page_starts)))

    print("Computing global split point...")
    split_pos = compute_global_split_point(all_lines, page_starts)
    print("Global median split: {}".format(split_pos))

    all_entries = []
    seen_headwords = set()
    dup_count = 0
    junk_count = 0

    for pi, (start_idx, page_line) in enumerate(page_starts):
        if pi + 1 < len(page_starts):
            end_idx = page_starts[pi + 1][0]
        else:
            end_idx = len(all_lines)
        page_lines = all_lines[start_idx:end_idx]

        pm = PAGE_RE.match(page_line.strip())
        page_num = int(pm.group().split()[2]) if pm else 0
        if page_num < 29 or page_num > 3200:
            continue

        left_text, right_text = separate_columns(page_lines[1:], split_pos)

        for col_text in [left_text, right_text]:
            entries = extract_entries(col_text)
            for hw, txt in entries:
                if hw not in seen_headwords:
                    record = parse_entry(hw, txt)
                    if record:
                        all_entries.append(record)
                        seen_headwords.add(hw)
                    else:
                        junk_count += 1
                else:
                    dup_count += 1

        if (pi + 1) % 100 == 0:
            print("  Processed {}/{} pages, entries: {}".format(pi+1, len(page_starts), len(all_entries)))

    print("\nTotal unique entries: {}".format(len(all_entries)))
    print("Duplicates skipped: {}".format(dup_count))
    print("Junk filtered: {}".format(junk_count))

    all_entries.sort(key=lambda r: (r['word'] or '').casefold())

    with open(OUT_RECORDS, 'w', encoding='utf-8') as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)

    min_path = OUT_DIR / "izoh_ocr.min.json"
    with open(min_path, 'w', encoding='utf-8') as f:
        json.dump(all_entries, f, ensure_ascii=False, separators=(",", ":"))

    word_list = [r['word'] for r in all_entries]
    idx_path = OUT_DIR / "index_ocr.json"
    with open(idx_path, 'w', encoding='utf-8') as f:
        json.dump(word_list, f, ensure_ascii=False, separators=(",", ":"))

    print("\nOutput written to:")
    print("  {}".format(OUT_RECORDS))
    print("  {}".format(min_path))
    print("  {}".format(idx_path))

    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        f.write("Total lines: {}\n".format(len(all_lines)))
        f.write("Pages: {}\n".format(len(page_starts)))
        f.write("Global split pos: {}\n".format(split_pos))
        f.write("Unique entries: {}\n".format(len(all_entries)))
        f.write("Duplicates skipped: {}\n".format(dup_count))
        f.write("Junk filtered: {}\n".format(junk_count))


if __name__ == '__main__':
    main()
