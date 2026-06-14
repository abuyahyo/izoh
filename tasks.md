# Izoh — Vazifalar

## Maqsad
Desktop'dagi "izohli lug'at.txt" (5 jildlik O'zbek tilining izohli lug'ati, 80 000+ so'z) faylidagi so'zlarni mavjud SPA ilovaga qo'shish.

## Loyiha tuzilishi
```
C:\Users\abu_y\izoh\
├── index.html          # SPA entrypoint
├── app.js              # router + search + render
├── style.css           # mobile-first stillar
├── data/               # bo'lingan ma'lumotlar
│   ├── index.json      # 35,491 so'z ro'yxati (autocomplete uchun)
│   ├── letters.json    # harflar manifesti
│   └── <HARF>.json     # har bir harf bo'yicha to'liq yozuvlar (28 fayl)
├── build/
│   ├── split.py        # JSON -> harf bo'yicha bo'lish
│   └── build_sw.py     # Service Worker qurish
├── icons/
├── manifest.json
├── style.css
├── sw.js
└── tasks.md            # BU FAYL
```

## Manba fayl
- `C:\Users\abu_y\Desktop\izohli lug'at.txt`
- 410,470 qator, ~12.7 MB
- Kirill alifbosida, UTF-8
- 5 jildlik "O'zbek tilining izohli lug'ati" (2006)
- So'z yozuvlari taxminan 1677-qatordan boshlanadi
- Format: SO'Z [etimologiya] so'z_turkumi 1 Ta'rif... [misol...]

## Mavjud ilova formati (JSON)
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

## Natija
- **OCR faylda**: 32,702 ta sarlavhali so'z (80,000+ deyilgani sub-entry + iboralar bilan)
- **Parser chiqardi**: 32,658 entry (44 ta abbreviaturalar filtrlangan)
- **Merged**: ~15,650 yangi so'z qo'shildi (dublikatlar chiqarib tashlandi)
- **Jami**: **51,137 so'z** (mavjud 35,491 → yangi 51,137)
- **Format**: mavjud SPA formatiga mos (28 harf fayli + index + letters)
- **app.js**: `renderWord()` ga etymology ko'rsatish qo'shildi
- **style.css**: `.etymology` klassi (light + dark mode)

## Bosqichlar

### [x] 1. Manba faylni chuqur tahlil qilish
- [x] Fayl hajmi va qatorlar soni aniqlandi
- [x] Kirill so'zlarini ajratib olish (headword extraction)
- [x] So'z turkumlarini aniqlash
- [x] Ta'rif va misollarni ajratish
- [x] So'zlar sonini hisoblash
- [x] OCR xatolarini aniqlash va tuzatish (qisman: join_hyphenated, vowel filter, `|`→`]`)

### [x] 2. Mavjud ma'lumotlar bilan solishtirish
- [x] Mavjud index.json dagi 35,491 so'z ro'yxatini olish
- [x] Manba fayldan olingan so'zlarni Latin alifbosiga o'tkazish
- [x] Ikki ro'yxatni solishtirish (qaysi so'zlar bor, qaysilari yo'q)
- [x] Yangi so'zlar ro'yxatini tuzish

### [x] 3. JSON formatga o'tkazish (parser yozish)
- [x] Kirill -> Lotin konvertori (app.js dagi cyrToLat ga mos)
- [x] Headword, POS, definition, examples, idioms ni ajratuvchi parser
- [x] Mavjud JSON formatiga moslab chiqarish
- [x] Yangi so'zlarni tegishli harf fayllariga qo'shish

### [/] 4. Ko'p ma'noli so'zlar (Omonimlar)
- [x] Riman raqamlari bilan ajratilgan omonimlarni aniqlash (BOG I, BOG II)
- [x] Alohida yozuv sifatida qo'shish
- [ ] Idiomlarni alohida ajratish logikasi (hali to'liq emas)

### [x] 5. index.json va letters.json yangilash
- [x] Yangi so'zlar bilan index.json ni qayta qurish
- [x] letters.json ni yangilash
- [x] Harf fayllarini minify qilish

### [x] 6. Service Worker
- [x] build_sw.py ishga tushirildi (CACHE_VERSION yangilandi)
- [ ] Lokal test qilish (python -m http.server)
- [ ] Git commit va push

## Qoldiq ishlar / Kamchiliklar
- OCR `]` belgisini `|` (pipe) deb noto'g'ri tanigan → `extract_etymology_full()` da `|` ham qabul qilindi
- ~73 ta entryda `]` ham `|` ham yo'q (OCR butunlay yo'qotgan) — etimologiyasiz qoladi
- `ъ` (Cyrillic hard sign) → `'` (apostrophe) konvertatsiyasi ishlaydi
- Mavjud data da `ъ` ishlatilgan (aъlo), OCR esa `аъло` → `a'lo` — bu ikki xil yozuv dublikat bo'lishi mumkin (kam sonli)
- Idiomlarni alohida ajratish logikasi hali to'liq emas

## Eslatmalar
- CLAUDE.md dagi ko'rsatmalarga amal qilish
- Harf aniqlash mantig'i Python (split.py) va JS (app.js) da bir xil
- Kyrill->Lotin konvertori app.js:55-79 dagi CYR_MAP ga mos bo'lishi kerak
- SW yangilanishi uchun build_sw.py ishga tushirilishi shart
