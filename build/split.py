"""
Split C:\\Users\\abu_y\\izoh-uz\\izoh-uz.min.json into per-letter files
under C:\\izoh\\data\\<LETTER>.json, plus a global lightweight index.json
of [{w: word, l: letter}] for fast client-side autocomplete.
"""
import json
import pathlib
from collections import defaultdict

SRC = pathlib.Path(r"C:\Users\abu_y\izoh-uz\izoh-uz.min.json")
DATA_DIR = pathlib.Path(r"C:\izoh\data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Multi-char letter prefixes (must check before single-char)
MULTI = ["O'", "G'", "O‘", "G‘", "Sh", "Ch", "SH", "CH", "sh", "ch", "o'", "g'", "o‘", "g‘"]


def letter_of(word: str) -> str:
    """Return the dictionary-letter bucket for a word (uppercase, normalized)."""
    w = word.strip()
    if not w:
        return "?"
    # check multi-char prefixes
    for m in MULTI:
        if w.startswith(m):
            base = m[0].upper()
            second = m[1]
            # normalize apostrophe variants to "'"
            if second in ("‘", "’", "'"):
                return base + "'"
            return base + second.lower()  # "Sh", "Ch"
    return w[0].upper()


def main():
    print(f"[+] Loading {SRC}")
    data = json.loads(SRC.read_text(encoding="utf-8"))
    print(f"[+] {len(data)} records loaded")

    buckets = defaultdict(list)
    index = []
    for rec in data:
        w = rec.get("word", "")
        if not w:
            continue
        letter = letter_of(w)
        buckets[letter].append(rec)
        index.append(w)

    # write per-letter files (minified)
    for letter, recs in sorted(buckets.items()):
        recs.sort(key=lambda r: (r["word"] or "").casefold())
        safe = letter.replace("'", "_")  # filename-safe (O' -> O_, G' -> G_)
        path = DATA_DIR / f"{safe}.json"
        path.write_text(
            json.dumps(recs, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        print(f"  {letter:>3}  {len(recs):>5} words  ->  {path.name}  ({path.stat().st_size/1024:.1f} KB)")

    # global index — sorted, minified (just words; letter is derived in JS)
    index.sort(key=lambda x: (x or "").casefold())
    idx_path = DATA_DIR / "index.json"
    idx_path.write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"\n[+] Global index: {len(index)} words -> {idx_path.name} ({idx_path.stat().st_size/1024:.1f} KB)")

    # letters manifest (for UI: which letters exist + size info)
    manifest = []
    for letter, recs in sorted(buckets.items()):
        safe = letter.replace("'", "_")
        manifest.append({"letter": letter, "file": f"{safe}.json", "count": len(recs)})
    manifest_path = DATA_DIR / "letters.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[+] Letters manifest -> {manifest_path.name}")


if __name__ == "__main__":
    main()
