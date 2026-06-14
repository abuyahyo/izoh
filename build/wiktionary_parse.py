"""Improved Wiktionary parser for Uzbek words.
Usage: python wiktionary_parse.py <word>
Outputs JSON to stdout or to a file.

Fixes:
- Definition number bleeding (stops at ◆)
- Antonyms/synonyms section boundary detection
- Part of speech from categories only
- Idiom detection
"""

import json, re, sys, time, urllib.request, urllib.parse, urllib.error, html as html_mod

API_URL = "https://uz.wiktionary.org/w/api.php"


def fetch_page(title, max_retries=3):
    params = {
        "action": "parse",
        "page": title,
        "format": "json",
        "prop": "text|categories",
        "utf8": 1,
        "redirects": 1,
    }
    url = API_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "IzohDict/1.0"})

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            return None, f"HTTP {e.code}: {e.reason}"
        except Exception as e:
            return None, str(e)
        break

    parse = data.get("parse")
    if not parse:
        error = data.get("error", {})
        return None, error.get("info", "Unknown error")
    return parse, None


def strip_tags(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&#160;", " ")
    text = text.replace("&#9670;", "◆")
    text = html_mod.unescape(text)
    return text.strip()


def get_section_html(html, section_id, after_ids=None):
    """Get HTML content of a section by its heading id."""
    # Try various id formats
    id_variants = [
        section_id,
        section_id.replace("'", "&#39;"),
        section_id.replace("ʻ", "ʽ"),
        section_id.replace("ʻ", "'"),
    ]
    id_variants = list(set(id_variants))

    match = None
    match_end = 0
    for vid in id_variants:
        m = re.search(
            rf'<h[234][^>]*\s+id="{re.escape(vid)}"[^>]*>.*?</h[234]>',
            html, re.DOTALL
        )
        if m:
            match = m
            match_end = m.end()
            break

    if not match:
        return ""

    # Build next heading pattern
    if after_ids:
        # Match any of the after_ids at same heading level
        escaped = []
        for aid in after_ids:
            escaped.append(re.escape(aid))
        next_pat = rf'<h[234][^>]*\s+id="(?:{"|".join(escaped)})"[^>]*>'
    else:
        next_pat = r'<h[234][^>]*(?:\s+id=")[^>]*>'

    rest = html[match_end:]
    next_m = re.search(next_pat, rest)
    if next_m:
        end = match_end + next_m.start()
    else:
        end = len(html)

    return html[match_end:end].strip()


def extract_etymology(html):
    section = get_section_html(html, "Etimologiyasi",
        ["Maʼnoviy_xususiyatlari", "Ma'noviy_xususiyatlari"])
    if not section:
        return ""

    # Get <p> text
    paras = []
    for p in re.findall(r'<p[^>]*>(.*?)</p>', section, re.DOTALL):
        text = strip_tags(p)
        if text:
            paras.append(text)

    # Filter out boilerplate
    result = []
    for line in paras:
        if re.match(r"Oʻzbek tilining.*foydalanilgan", line):
            continue
        if re.match(r"O'zbek tilining.*foydalanilgan", line):
            continue
        result.append(line)

    return " ".join(result).strip()


def extract_definitions(html):
    section = get_section_html(html, "Maʼnosi",
        ["Sinonimlari", "Antonimlari", "Tarjimalari", "Ot_2"])
    if not section:
        return {"meanings": [], "idioms": []}

    # Get all paragraphs
    paras = []
    for p in re.findall(r'<p[^>]*>(.*?)</p>', section, re.DOTALL):
        text = strip_tags(p)
        if text:
            paras.append(text)

    # Also get <dd> content (idioms)
    dd_items = []
    for dd_match in re.finditer(r'<dd>(.*?)</dd>', section, re.DOTALL):
        text = strip_tags(dd_match.group(1))
        if text:
            dd_items.append(text)

    full_text = "\n".join(paras)

    # Split by definition number (1. 2. 3. at line start or after newline)
    # Pattern: number followed by space and content
    blocks = re.split(r'(?:^|\n)\s*(\d+)\s+(?=\S)', full_text, flags=re.MULTILINE)
    # Also handle inline: "1 " at start
    if len(blocks) <= 1:
        blocks = re.split(r'(?:(?:^|\n)\s*)(\d+)\s+', full_text)

    meanings = []
    i = 0
    while i < len(blocks):
        block_text = blocks[i].strip()
        if not block_text:
            i += 1
            continue

        # Check if this block is a definition number or part of content
        if block_text.isdigit() and i + 1 < len(blocks):
            num = block_text
            i += 1
            content = blocks[i].strip() if i < len(blocks) else ""
        else:
            # Try to extract number from start
            m = re.match(r'(\d+)\s+(.*)', block_text)
            if m:
                num = m.group(1)
                content = m.group(2)
            else:
                # Continuation of previous definition or idiom
                if i > 0 and meanings:
                    meanings[-1]["definition"] += " " + block_text
                i += 1
                continue

        # Split content by ◆ to get examples
        parts = content.split("◆", 1)
        def_text = parts[0].strip()
        examples = []

        # Get all examples (there may be multiple ◆)
        all_examples = content.split("◆")[1:]  # skip the definition part before first ◆
        for ex in all_examples:
            ex = ex.strip()
            if ex:
                # Try to extract source from the end: "Text.  Source" or "Text (Source)"
                ex = re.sub(r'\s+', ' ', ex)
                # Try pattern: Text.  Source (where Source has capitalization)
                m = re.match(r'(.+?)\s{2,}(.+)$', ex)
                if m:
                    examples.append({"text": m.group(1).strip(), "source": m.group(2).strip()})
                else:
                    examples.append({"text": ex, "source": ""})

        # Remove trailing continuation of next definition
        # Check if def_text ends with a digit that's actually the next definition number
        def_text = re.sub(r'\s+\d+\s*$', '', def_text).strip()

        meanings.append({
            "number": num,
            "definition": def_text,
            "examples": examples
        })
        i += 1

    # Also process <dd> items as idioms
    idioms = []
    for dd in dd_items:
        parts = dd.split("◆", 1)
        phrase_def = parts[0].strip()
        ex_text = parts[1].strip() if len(parts) > 1 else ""

        # First space or newline separates phrase from definition
        m = re.match(r'(\S+(?:\s+\S+)*?)\s{2,}(.*)', phrase_def)
        if m:
            phrase = m.group(1)
            definition = m.group(2)
        else:
            phrase = phrase_def
            definition = ""

        examples = []
        if ex_text:
            m2 = re.match(r'(.+?)\s{2,}(.+)$', ex_text)
            if m2:
                examples.append({"text": m2.group(1), "source": m2.group(2)})
            else:
                examples.append({"text": ex_text, "source": ""})

        idioms.append({
            "phrase": phrase,
            "definition": definition,
            "examples": examples
        })

    result = {"meanings": meanings}
    if idioms:
        result["idioms"] = idioms
    return result


def clean_section_text(text):
    """Remove edit links and boilerplate from section text."""
    text = re.sub(r'\[tahrirlash\]', '', text)
    text = re.sub(r'\[\s*tahrirlash\s*\]', '', text)
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if re.match(r"[A-ZА-ЯЁ]+['ʻ]?\s*\.\s*O['ʻ]?zbek tilining", line):
            continue
        lines.append(line)
    return "; ".join(lines)


def extract_synonyms_antonyms(html):
    """Extract synonyms and antonyms."""
    synonyms = ""
    syn_section = get_section_html(html, "Sinonimlari",
        ["Antonimlari", "Tarjimalari", "Ot_2"])
    if syn_section:
        synonyms = clean_section_text(strip_tags(syn_section))

    antonyms = ""
    ant_section = get_section_html(html, "Antonimlari",
        ["Tarjimalari", "Ot_2"])
    if ant_section:
        antonyms = clean_section_text(strip_tags(ant_section))

    return synonyms, antonyms


def extract_part_of_speech(categories):
    """Extract part of speech from category names."""
    pos_map = {
        "ot": "ot",
        "feʼl": "feʼl",
        "sifat": "sifat",
        "son": "son",
        "olmosh": "olmosh",
        "ravish": "ravish",
        "koʻmakchi": "koʻmakchi",
        "bogʻlovchi": "bogʻlovchi",
        "yuklama": "yuklama",
        "taqlid": "taqlid",
        "modal": "modal",
        "undov": "undov",
    }
    for cat in categories:
        cat_lower = cat.lower()
        for key, pos in pos_map.items():
            if key in cat_lower:
                return pos
    return ""


def parse_word(title):
    parse, error = fetch_page(title)
    if error:
        return {"word": title, "error": error}

    html = parse["text"]["*"]
    categories_raw = parse.get("categories", [])
    categories = []
    for c in categories_raw:
        if isinstance(c, dict):
            categories.append(c.get("*", ""))
        elif isinstance(c, str):
            categories.append(c)

    result = {
        "word": title,
        "pageid": parse.get("pageid"),
        "part_of_speech": extract_part_of_speech(categories),
    }

    etymology = extract_etymology(html)
    if etymology:
        result["etymology"] = etymology

    defs = extract_definitions(html)
    if defs.get("meanings"):
        result["meanings"] = defs["meanings"]
    if defs.get("idioms"):
        result["idioms"] = defs["idioms"]

    syn, ant = extract_synonyms_antonyms(html)
    if syn:
        result["synonyms"] = syn
    if ant:
        result["antonyms"] = ant

    return result


if __name__ == "__main__":
    word = sys.argv[1] if len(sys.argv) > 1 else "non"
    result = parse_word(word)
    out_path = f"C:\\Users\\abu_y\\izoh\\wiktionary_{word}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps({"word": word, "status": "ok" if "error" not in result else "error",
                       "keys": list(result.keys())}, ensure_ascii=False))
