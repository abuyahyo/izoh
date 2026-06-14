// Izoh — O'zbek tilining izohli lug'ati (SPA)
'use strict';

const DATA = 'data/';

let INDEX = [];
let INDEX_LOWER = [];
let LETTER_CACHE = {};
let LOADING_LETTER = {};

const MULTI_PREFIXES = ["Sh", "Ch", "SH", "CH", "sh", "ch"];
const APOST_PREFIXES = ["O'", "G'", "O‘", "G‘", "o'", "g'", "o‘", "g‘"];

function letterOf(word) {
  if (!word) return '?';
  for (const p of APOST_PREFIXES) {
    if (word.startsWith(p)) return p[0].toUpperCase() + "'";
  }
  for (const p of MULTI_PREFIXES) {
    if (word.startsWith(p)) return p[0].toUpperCase() + p[1].toLowerCase();
  }
  return word[0].toUpperCase();
}

function letterToFile(letter) {
  return DATA + letter.replace("'", "_") + '.json';
}

// === Data ===
async function loadIndex() {
  if (INDEX.length) return;
  const r = await fetch(DATA + 'index.json');
  INDEX = await r.json();
  INDEX_LOWER = INDEX.map(w => cyrToLat(w).toLocaleLowerCase('uz'));
}

async function loadLetter(letter) {
  if (LETTER_CACHE[letter]) return LETTER_CACHE[letter];
  if (LOADING_LETTER[letter]) return LOADING_LETTER[letter];
  LOADING_LETTER[letter] = fetch(letterToFile(letter))
    .then(r => r.json())
    .then(data => { LETTER_CACHE[letter] = data; delete LOADING_LETTER[letter]; return data; });
  return LOADING_LETTER[letter];
}

async function findWord(word) {
  const w = cyrToLat(word);
  const letter = letterOf(w);
  const recs = await loadLetter(letter);
  const wLower = w.toLocaleLowerCase('uz');
  return recs.find(r => cyrToLat(r.word || '').toLocaleLowerCase('uz') === wLower) || null;
}

// === Script toggle ===
let SCRIPT = 'lotin'; // 'lotin' or 'kiril'

function getScript() { return SCRIPT; }

// === Latin -> Cyrillic (reverse map) ===
const LAT_CYR_MAP = {
  'shch':'щ', 'Shch':'Щ', 'yo':'ё', 'Yo':'Ё',
  'yu':'ю', 'Yu':'Ю', 'ya':'я', 'Ya':'Я',
  'ch':'ч', 'Ch':'Ч', 'sh':'ш', 'Sh':'Ш',
  'o\'':'ў', 'O\'':'Ў', 'g\'':'ғ', 'G\'':'Ғ',
  'a':'а','A':'А','b':'б','B':'Б','d':'д','D':'Д',
  'e':'е','E':'Е','f':'ф','F':'Ф','g':'г','G':'Г',
  'h':'ҳ','H':'Ҳ','i':'и','I':'И','j':'ж','J':'Ж',
  'k':'к','K':'К','l':'л','L':'Л','m':'м','M':'М',
  'n':'н','N':'Н','o':'о','O':'О','p':'п','P':'П',
  'q':'қ','Q':'Қ','r':'р','R':'Р','s':'с','S':'С',
  't':'т','T':'Т','u':'у','U':'У','v':'в','V':'В',
  'x':'х','X':'Х','y':'й','Y':'Й','z':'з','Z':'З',
  '’':'ъ',"'":'ъ',
};

// Multi-char keys sorted by length desc for greedy matching
const LAT_CYR_KEYS = Object.keys(LAT_CYR_MAP)
  .filter(k => k.length > 1 || (k.length === 1 && k !== k.toLowerCase()))
  .sort((a, b) => b.length - a.length);
const LAT_CYR_SINGLE = Object.fromEntries(
  Object.entries(LAT_CYR_MAP).filter(([k]) => k.length === 1 && k === k.toLowerCase())
);

function latToCyr(s) {
  if (!s) return '';
  // Apostrophe variants: normalize to simple '
  s = s.replace(/[ʻʼ‘’]/g, "'");
  // Match multi-char sequences first (case-insensitive for some)
  let out = '', i = 0;
  while (i < s.length) {
    let matched = false;
    for (const key of LAT_CYR_KEYS) {
      if (s.slice(i, i + key.length) === key) {
        out += LAT_CYR_MAP[key];
        i += key.length;
        matched = true;
        break;
      }
    }
    if (matched) continue;
    const ch = s[i];
    out += LAT_CYR_MAP[ch] || ch;
    i++;
  }
  return out;
}

// === Cyrillic -> Latin (O'zbek alifbosi) ===
const CYR_MAP = {
  // multi-char first (di-graphs)
  'ё':'yo','Ё':'Yo','ю':'yu','Ю':'Yu','я':'ya','Я':'Ya',
  'ч':'ch','Ч':'Ch','ш':'sh','Ш':'Sh','ў':"o'","Ў":"O'",
  'ғ':"g'","Ғ":"G'",
  // single chars
  'а':'a','А':'A','б':'b','Б':'B','в':'v','В':'V','г':'g','Г':'G',
  'д':'d','Д':'D','е':'e','Е':'E','ж':'j','Ж':'J','з':'z','З':'Z',
  'и':'i','И':'I','й':'y','Й':'Y','к':'k','К':'K','қ':'q','Қ':'Q',
  'л':'l','Л':'L','м':'m','М':'M','н':'n','Н':'N','о':'o','О':'O',
  'п':'p','П':'P','р':'r','Р':'R','с':'s','С':'S','т':'t','Т':'T',
  'у':'u','У':'U','ф':'f','Ф':'F','х':'x','Х':'X','ҳ':'h','Ҳ':'H',
  'ц':'s','Ц':'S','щ':'shch','Щ':'Shch','ъ':"'",'ь':'','ы':'i','Ы':'I',
  'э':'e','Э':'E','ʼ':"'",
};
const CYR_RE = /[Ѐ-ӿʼ]/;

function cyrToLat(s) {
  if (!s || !CYR_RE.test(s)) return s;
  let out = '';
  for (const ch of s) {
    out += (ch in CYR_MAP) ? CYR_MAP[ch] : ch;
  }
  return out;
}

// Expand etymology abbreviations (Latin forms, after Cyrillic->Latin conversion)
const ETYM_ABBR = [
  ['arab.', 'arabcha '], ['a.', 'arabcha '],
  ['fors.', 'forscha '], ['fars.', 'forscha '], ['f.', 'forscha '],
  ['ingliz.', 'inglizcha '], ['ing.', 'inglizcha '],
  ['rus.', 'ruscha '],
  ['lotin.', 'lotincha '], ['lot.', 'lotincha '], ['l.', 'lotincha '],
  ['yunon.', 'yunoncha '], ['yun.', 'yunoncha '],
  ['nemis.', 'nemischa '], ['nem.', 'nemischa '],
  ['fransuz.', 'fransuzcha '], ['fr.', 'fransuzcha '],
  ['italyan.', 'italyancha '], ['ital.', 'italyancha '], ['it.', 'italyancha '],
  ['ispan.', 'ispancha '], ['isp.', 'ispancha '],
  ['portugal.', 'portugalcha '], ['port.', 'portugalcha '],
  ['golland.', 'gollandcha '], ['gol.', 'gollandcha '],
  ['turk.', 'turkcha '],
  ['xitoy.', 'xitoycha '], ['xit.', 'xitoycha '],
  ['yapon.', 'yaponcha '], ['yap.', 'yaponcha '],
  ['sanskrit.', 'sanskritcha '], ['sansk.', 'sanskritcha '],
  ['yevrey.', 'yevreyche '], ['yevr.', 'yevreyche '],
  ['shved.', 'shvedcha '],
  ['polyak.', 'polyakcha '], ['poly.', 'polyakcha '],
  ['chex.', 'chexcha '],
  ['slavyan.', 'slavyancha '], ['slav.', 'slavyancha '],
  ['aramey.', 'arameycha '], ['aram.', 'arameycha '],
  ['norveg.', 'norvegcha '], ['norv.', 'norvegcha '],
  ['dat.', 'datcha '],
  ['majar.', 'majarcha '], ['venger.', 'majarcha '],
  ['mongol.', 'mongolcha '], ['mong.', 'mongolcha '],
  ['pers.', 'perscha '],
  ['tojik.', 'tojikcha '], ['toj.', 'tojikcha '],
  ['qadimgi ', 'qad. '],
  ['somon.', 'somoniy '],
];
function expandEtym(s) {
  if (!s) return '';
  // First convert any remaining Cyrillic to Latin
  s = cyrToLat(s);
  // Sort by length desc to match longer abbrs first
  const sorted = [...ETYM_ABBR].sort((a, b) => b[0].length - a[0].length);
  for (const [abbr, full] of sorted) {
    const escaped = abbr.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    s = s.replace(new RegExp(`(^|[\\s;,(])${escaped}`, 'g'), '$1' + full);
  }
  return s;
}

// === Utils ===
function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// Split italic-marker prefixes ("aynan ", "ay. ", "kam ishl. " etc.) from definition
const DEF_MARKERS = ['aynan ', 'ay. ', 'kam ishl. ', 'q. ', 'qar. '];
function splitDefMarker(def) {
  for (const m of DEF_MARKERS) {
    if (def.startsWith(m)) {
      return { marker: m.trim(), rest: def.slice(m.length) };
    }
  }
  return { marker: '', rest: def };
}

// === Renderers ===
function renderHome() {
  return '';
}

function renderNotFound(word) {
  return `
    <div class="not-found">
      <div class="icon">📭</div>
      <h1>Topilmadi</h1>
      <p><strong>${esc(word)}</strong> so‘zi lug‘atda mavjud emas.</p>
      <p style="margin-top:24px;"><a href="#/">Bosh sahifa</a></p>
    </div>
  `;
}

function toScript(s) {
  return SCRIPT === 'kiril' ? latToCyr(s) : s;
}

function renderWord(rec) {
  const wd = toScript(rec.word);

  const meanings = rec.meanings || [];
  const multi = meanings.length > 1;
  const meaningsHtml = meanings.map((m, i) => {
    const def = (m.definition || '').replace(/^\s*\d+\.\s*/, '');
    const { marker, rest } = splitDefMarker(def);
    return `<div class="meaning">
      ${multi ? `<span class="meaning-num">${i + 1}</span>` : ''}
      <p class="meaning-def">${marker ? `<span class="marker">${esc(toScript(marker))}</span>` : ''}${esc(toScript(rest))}</p>
    </div>`;
  }).join('');

  const pos = rec.part_of_speech ? toScript(rec.part_of_speech) : '';
  const etym = rec.etymology ? toScript(expandEtym(rec.etymology)) : '';
  const synonyms = rec.synonyms ? toScript(rec.synonyms) : '';
  const antonyms = rec.antonyms ? toScript(rec.antonyms) : '';

  return `
    <article class="word-page">
      <h1>${esc(wd)}</h1>
      ${pos ? `<p class="pos">${esc(pos)}</p>` : ''}
      ${etym ? `<p class="etymology">${esc(etym)}</p>` : ''}
      ${meaningsHtml || '<p style="color:#78716c;">Bu so‘z uchun izoh hali kiritilmagan.</p>'}
      ${synonyms ? `<div class="synonyms"><b>Sinonimlari:</b> ${esc(synonyms)}</div>` : ''}
      ${antonyms ? `<div class="antonyms"><b>Antonimlari:</b> ${esc(antonyms)}</div>` : ''}
    </article>
  `;
}

// === Router ===
async function route() {
  const hash = location.hash || '#/';
  const view = document.getElementById('view');
  view.innerHTML = '<p class="loading">Yuklanmoqda…</p>';

  try {
    if (hash === '#/' || hash === '') {
      view.innerHTML = renderHome();
      document.title = "Izoh — O‘zbek tilining izohli lug‘ati";
      window.scrollTo(0, 0);
      return;
    }

    if (hash.startsWith('#/word/')) {
      const w = decodeURIComponent(hash.slice(7));
      const rec = await findWord(w);
      if (!rec) {
        view.innerHTML = renderNotFound(w);
        document.title = `${w} — topilmadi — Izoh`;
        return;
      }
      view.innerHTML = renderWord(rec);
      document.title = `${rec.word} — Izoh`;
      window.scrollTo(0, 0);
      return;
    }

    view.innerHTML = renderHome();
  } catch (e) {
    view.innerHTML = `<p class="loading">Xato: ${esc(e.message)}</p>`;
  }
}

// === Search / autocomplete ===
function setupSearch() {
  const input = document.getElementById('search');
  const list = document.getElementById('suggestions');
  const btn = document.getElementById('search-btn');
  let activeIdx = -1;
  let currentSuggestions = [];

  function hide() {
    list.hidden = true;
    list.innerHTML = '';
    activeIdx = -1;
  }

  function show(matches) {
    if (!matches.length) { hide(); return; }
    currentSuggestions = matches;
    list.innerHTML = matches.map((w, i) =>
      `<li data-word="${esc(w)}" data-idx="${i}">${esc(w)}</li>`
    ).join('');
    list.hidden = false;
    activeIdx = -1;
  }

  function search(query) {
    if (!INDEX.length) return [];
    const q = cyrToLat(query.trim()).toLocaleLowerCase('uz');
    if (!q) return [];
    const exact = [];
    const prefix = [];
    const contains = [];
    for (let i = 0; i < INDEX_LOWER.length; i++) {
      const lw = INDEX_LOWER[i];
      if (lw === q) exact.push(INDEX[i]);
      else if (lw.startsWith(q)) {
        if (prefix.length < 20) prefix.push(INDEX[i]);
      } else if (lw.includes(q) && contains.length < 10) {
        contains.push(INDEX[i]);
      }
    }
    return [...exact, ...prefix, ...contains].slice(0, 20);
  }

  input.addEventListener('input', e => show(search(e.target.value)));
  input.addEventListener('focus', e => {
    if (e.target.value) show(search(e.target.value));
  });

  input.addEventListener('keydown', e => {
    if (list.hidden) {
      if (e.key === 'Enter' && input.value.trim()) {
        const matches = search(input.value);
        if (matches.length) go(matches[0]);
      }
      return;
    }
    const items = list.querySelectorAll('li');
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      activeIdx = (activeIdx + 1) % items.length;
      updateActive(items);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      activeIdx = (activeIdx - 1 + items.length) % items.length;
      updateActive(items);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIdx >= 0) go(currentSuggestions[activeIdx]);
      else if (currentSuggestions.length) go(currentSuggestions[0]);
    } else if (e.key === 'Escape') {
      hide();
      input.blur();
    }
  });

  function updateActive(items) {
    items.forEach((li, i) => li.classList.toggle('active', i === activeIdx));
    if (activeIdx >= 0) items[activeIdx].scrollIntoView({ block: 'nearest' });
  }

  list.addEventListener('mousedown', e => {
    const li = e.target.closest('li');
    if (li && li.dataset.word) {
      e.preventDefault();
      go(li.dataset.word);
    }
  });

  btn.addEventListener('click', () => {
    const matches = search(input.value);
    if (matches.length) go(matches[0]);
  });

  document.addEventListener('click', e => {
    if (!e.target.closest('.search-wrap')) hide();
  });

  function go(word) {
    input.value = '';
    hide();
    input.blur();
    location.hash = '#/word/' + encodeURIComponent(word);
  }
}

// === Service Worker (PWA) ===
function setupSW() {
  if (!('serviceWorker' in navigator)) return;
  // Auto-reload when a new SW takes control (after deploy)
  let reloading = false;
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (reloading) return;
    reloading = true;
    location.reload();
  });
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('sw.js').then(reg => {
      // If an update is found, ask it to activate immediately
      reg.addEventListener('updatefound', () => {
        const nw = reg.installing;
        if (!nw) return;
        nw.addEventListener('statechange', () => {
          if (nw.state === 'installed' && navigator.serviceWorker.controller) {
            nw.postMessage('skipWaiting');
          }
        });
      });
    }).catch(err => console.warn('SW register failed:', err));
  });
}

// === Settings panel ===
function setupSettings() {
  const btn = document.getElementById('settings-btn');
  const panel = document.getElementById('settings-panel');
  if (!btn || !panel) return;

  // Toggle panel
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = !panel.hidden;
    panel.hidden = isOpen;
    btn.classList.toggle('active', !isOpen);
  });

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (panel.hidden) return;
    const wrap = document.querySelector('.settings-wrap');
    if (wrap && !wrap.contains(e.target)) {
      panel.hidden = true;
      btn.classList.remove('active');
    }
  });
}

// === Theme (tungi/tongi rejim) ===
function setupTheme() {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;
  const mq = window.matchMedia('(prefers-color-scheme: dark)');
  mq.addEventListener('change', e => {
    if (localStorage.getItem('theme') !== 'light' && localStorage.getItem('theme') !== 'dark') {
      document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
    }
  });
  btn.addEventListener('click', () => {
    const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('theme', next); } catch (e) {}
  });
}

// === Script toggle ===
function setupScript() {
  const btn = document.getElementById('script-toggle');
  const label = document.getElementById('script-label');
  const indicator = document.getElementById('scr-indicator');
  if (!btn) return;

  function apply() {
    document.documentElement.setAttribute('data-script', SCRIPT);
    const isKiril = SCRIPT === 'kiril';
    if (label) label.textContent = isKiril ? 'Kirill' : 'Lotin';
    if (indicator) indicator.textContent = isKiril ? 'Ў' : "O'";
    route();
  }

  try {
    const saved = localStorage.getItem('script');
    if (saved === 'kiril' || saved === 'lotin') SCRIPT = saved;
  } catch (e) {}

  document.documentElement.setAttribute('data-script', SCRIPT);
  apply();

  btn.addEventListener('click', () => {
    SCRIPT = SCRIPT === 'kiril' ? 'lotin' : 'kiril';
    try { localStorage.setItem('script', SCRIPT); } catch (e) {}
    apply();
  });
}

// === Font size ===
const SIZES = ['small', 'medium', 'large'];
const SIZE_LABELS = { small: 'Kichik', medium: "O'rtacha", large: 'Katta' };
let FONT_SIZE = 'medium';

function setupSize() {
  const dec = document.getElementById('size-dec');
  const inc = document.getElementById('size-inc');
  const label = document.getElementById('size-label');
  if (!dec || !inc) return;

  try {
    const saved = localStorage.getItem('fontSize');
    if (SIZES.includes(saved)) FONT_SIZE = saved;
  } catch (e) {}

  function apply() {
    document.documentElement.setAttribute('data-font-size', FONT_SIZE);
    if (label) label.textContent = SIZE_LABELS[FONT_SIZE] || FONT_SIZE;
  }

  apply();

  dec.addEventListener('click', () => {
    const idx = SIZES.indexOf(FONT_SIZE);
    if (idx > 0) {
      FONT_SIZE = SIZES[idx - 1];
      try { localStorage.setItem('fontSize', FONT_SIZE); } catch (e) {}
      apply();
    }
  });

  inc.addEventListener('click', () => {
    const idx = SIZES.indexOf(FONT_SIZE);
    if (idx < SIZES.length - 1) {
      FONT_SIZE = SIZES[idx + 1];
      try { localStorage.setItem('fontSize', FONT_SIZE); } catch (e) {}
      apply();
    }
  });
}

// === Random word ===
function setupRandom() {
  const btn = document.getElementById('random-btn');
  if (!btn) return;
  btn.addEventListener('click', () => {
    if (!INDEX.length) return;
    const word = INDEX[Math.floor(Math.random() * INDEX.length)];
    location.hash = '#/word/' + encodeURIComponent(word);
  });
}

// === Init ===
async function init() {
  setupTheme();
  setupScript();
  setupSize();
  setupSettings();
  setupSearch();
  setupRandom();
  setupSW();
  await loadIndex();
  window.addEventListener('hashchange', route);
  route();
}

init();
