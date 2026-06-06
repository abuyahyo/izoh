# Izoh — O'zbek tilining izohli lug'ati (SPA)

GitHub Pages'da statik veb-ilova. **abuyahyo/izoh** repoga deploy qilinadi.

## Loyiha tuzilishi

```
C:\izoh\
├── index.html          # SPA entrypoint
├── style.css           # mobile-first stillar
├── app.js              # router + search + render
├── data/               # bo'lingan ma'lumotlar (build natijasi)
│   ├── index.json      # 35,491 so'z ro'yxati (autocomplete uchun, 401 KB)
│   ├── letters.json    # harflar manifesti
│   └── <LETTER>.json   # har bir harf bo'yicha to'liq yozuvlar (28 fayl)
├── build/
│   └── split.py        # izoh-uz.min.json'ni harf bo'yicha bo'lish
└── CLAUDE.md
```

## Ma'lumot manbai

- Asl manba: **izoh.uz** sayti (sitemap orqali skraping)
- Skraping skripti: `C:\Users\abu_y\izoh-uz\scrape.py`
- Birlashtirilgan natija: `C:\Users\abu_y\izoh-uz\izoh-uz.min.json` (17 MB)
- `build/split.py` ushbu faylni harf bo'yicha bo'ladi va `data/` ichiga yozadi

## Ma'lumotni yangilash

```bash
# 1. izoh.uz dan qayta skraping (agar yangi so'zlar qo'shilgan bo'lsa)
cd /c/Users/abu_y/izoh-uz
python scrape.py        # resume-safe
python finalize.py      # JSONL -> izoh-uz.min.json

# 2. SPA data fayllarini qayta qurish
cd /c/izoh
python build/split.py
git add data/ && git commit -m "Update dictionary data" && git push
```

## Yozuv strukturasi (har so'z uchun)

```json
{
  "url": "https://izoh.uz/word/non",
  "word": "non",
  "part_of_speech": "ot",
  "meanings": [
    { "definition": "...", "examples": [{"text": "...", "source": "..."}] }
  ],
  "idioms": [
    { "phrase": "Non yemoq", "definition": "...", "examples": [...] }
  ]
}
```

## Routing (hash-based)

- `#/` — bosh sahifa
- `#/word/<word>` — so'z sahifasi
- `#/letter/<letter>` — harf bo'yicha so'zlar ro'yxati

## Harf aniqlash mantig'i

Multi-character prefikslar: `Sh`, `Ch`, `O'`, `G'` (apostrof variantlari: `'`, `‘`, `’`).
Mantiq Python (`split.py: letter_of`) va JS (`app.js: letterOf`) da bir xil bo'lishi shart.

## Lokal sinash

```bash
cd /c/izoh
python -m http.server 8765
# Brauzerda: http://127.0.0.1:8765/
```

## Til

UI faqat o'zbek tilida. Texnik bo'lmagan sodda til (masalan, "Iboralar" emas "frazeologizm").
