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
  INDEX_LOWER = INDEX.map(w => w.toLocaleLowerCase('uz'));
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
  return recs.find(r => (r.word || '').toLocaleLowerCase('uz') === wLower) || null;
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

function renderWord(rec) {
  const wd = rec.word;

  const meaningsHtml = (rec.meanings || []).map(m => {
    const { marker, rest } = splitDefMarker(m.definition || '');
    return `<div class="meaning">
      <p class="meaning-def">${marker ? `<span class="marker">${esc(marker)}</span>` : ''}${esc(rest)}</p>
    </div>`;
  }).join('');

  return `
    <article class="word-page">
      <h1>${esc(wd)}</h1>
      ${rec.part_of_speech ? `<p class="pos">${esc(rec.part_of_speech)}</p>` : ''}
      ${meaningsHtml || '<p style="color:#78716c;">Bu so‘z uchun izoh hali kiritilmagan.</p>'}
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

// === Init ===
async function init() {
  setupSearch();
  setupSW();
  await loadIndex();
  window.addEventListener('hashchange', route);
  route();
}

init();
