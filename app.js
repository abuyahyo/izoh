// Izoh — O'zbek tilining izohli lug'ati (SPA)
'use strict';

const DATA = 'data/';
const SHARE_BASE = location.origin + location.pathname;

let INDEX = [];
let INDEX_LOWER = [];
let LETTERS = [];
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

async function loadLetters() {
  if (LETTERS.length) return;
  const r = await fetch(DATA + 'letters.json');
  LETTERS = await r.json();
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
  const letter = letterOf(word);
  const recs = await loadLetter(letter);
  const wLower = word.toLocaleLowerCase('uz');
  return recs.find(r => (r.word || '').toLocaleLowerCase('uz') === wLower) || null;
}

// === Utils ===
function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function fmtNum(n) {
  return n.toLocaleString('uz').replace(/,/g, ' ');
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
  const idiomCount = 7791; // from stats; harmless static
  return `
    <div class="home-hero">
      <h1>O‘zbek tilining izohli lug‘ati</h1>
      <p>So‘zlarni qidiring, ma'nolarini va misollarini o‘rganing</p>
    </div>
    <div class="home-stats">
      <div class="stat-card">
        <span class="num">${fmtNum(35491)}</span>
        <span class="lbl">so‘z</span>
      </div>
      <div class="stat-card">
        <span class="num">${fmtNum(50932)}</span>
        <span class="lbl">izoh</span>
      </div>
      <div class="stat-card">
        <span class="num">${fmtNum(idiomCount)}</span>
        <span class="lbl">ibora</span>
      </div>
    </div>
    <p class="home-tip">
      Yuqoridagi maydondan so‘z qidiring yoki pastdagi <strong>Alifbo</strong> bo‘yicha ko‘ring.
    </p>
  `;
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

function renderExamplesList(examples) {
  if (!examples || !examples.length) return '';
  return `<ul class="meaning-examples">${examples.map(ex =>
    `<li>${esc(ex.text)}${ex.source ? ` <span class="example-source">— ${esc(ex.source)}</span>` : ''}</li>`
  ).join('')}</ul>`;
}

function renderWord(rec) {
  const wd = rec.word;
  const shareUrl = SHARE_BASE + '#/word/' + encodeURIComponent(wd);
  const shareText = `${wd} — Izoh`;

  const meaningsHtml = (rec.meanings || []).map(m => {
    const { marker, rest } = splitDefMarker(m.definition || '');
    return `<div class="meaning">
      <p class="meaning-def">${marker ? `<span class="marker">${esc(marker)}</span>` : ''}${esc(rest)}</p>
      ${renderExamplesList(m.examples)}
    </div>`;
  }).join('');

  const idiomsHtml = (rec.idioms && rec.idioms.length) ? `
    <div class="idioms-section">
      <h2>${esc(wd.toUpperCase())} so‘zi qatnashgan iboralar</h2>
      ${rec.idioms.map(id => {
        const { marker, rest } = splitDefMarker(id.definition || '');
        return `<div class="idiom">
          <p class="idiom-phrase">${esc(id.phrase)}</p>
          ${rest ? `<p class="idiom-def">${marker ? `<span class="marker" style="font-style:italic;color:#78716c;">${esc(marker)} </span>` : ''}${esc(rest)}</p>` : ''}
          ${renderExamplesList(id.examples)}
        </div>`;
      }).join('')}
    </div>` : '';

  return `
    <article class="word-page">
      <div class="word-header">
        <strong>Izoh</strong> · ${esc(wd)} so‘zining izohi va ma'nolari
      </div>
      <h1>${esc(wd)}</h1>
      ${rec.part_of_speech ? `<p class="pos">${esc(rec.part_of_speech)}</p>` : ''}
      ${meaningsHtml || '<p style="color:#78716c;">Bu so‘z uchun izoh hali kiritilmagan.</p>'}
      ${idiomsHtml}
      <div class="share">
        <a class="tg" href="https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(shareText)}" target="_blank" rel="noopener">Telegram</a>
        <a class="wa" href="https://wa.me/?text=${encodeURIComponent(shareText + ' ' + shareUrl)}" target="_blank" rel="noopener">WhatsApp</a>
        <button class="copy" id="copy-link" type="button">Linkni nusxalash</button>
        ${rec.url ? `<a class="source" href="${esc(rec.url)}" target="_blank" rel="noopener">Manba (izoh.uz)</a>` : ''}
      </div>
    </article>
  `;
}

function renderLetterPage(letter, recs) {
  return `
    <div>
      <div class="letter-page-header">
        <h1>${esc(letter)}</h1>
        <span class="count">${fmtNum(recs.length)} ta so‘z</span>
      </div>
      <div class="letter-list">
        ${recs.map(r => `<a href="#/word/${encodeURIComponent(r.word)}">${esc(r.word)}</a>`).join('')}
      </div>
    </div>
  `;
}

function renderAllLetters() {
  return `
    <h1 style="margin:0 0 20px;font-size:24px;">Alifbo bo‘yicha</h1>
    <div class="all-letters">
      ${LETTERS.map(l =>
        `<a href="#/letter/${encodeURIComponent(l.letter)}">
          <span class="big">${esc(l.letter)}</span>
          <span class="small">${fmtNum(l.count)} so‘z</span>
        </a>`
      ).join('')}
    </div>
  `;
}

// === Router ===
async function route() {
  const hash = location.hash || '#/';
  const view = document.getElementById('view');
  view.innerHTML = '<p class="loading">Yuklanmoqda…</p>';

  highlightActiveLetter(null);
  highlightBottomNav(hash);

  try {
    if (hash === '#/' || hash === '') {
      view.innerHTML = renderHome();
      document.title = "Izoh — O‘zbek tilining izohli lug‘ati";
      window.scrollTo(0, 0);
      return;
    }

    if (hash === '#/letters') {
      view.innerHTML = renderAllLetters();
      document.title = "Alifbo — Izoh";
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
      const copyBtn = document.getElementById('copy-link');
      if (copyBtn) {
        copyBtn.addEventListener('click', () => {
          const url = SHARE_BASE + '#/word/' + encodeURIComponent(rec.word);
          navigator.clipboard?.writeText(url).then(() => {
            copyBtn.textContent = 'Nusxalandi ✓';
            setTimeout(() => copyBtn.textContent = 'Linkni nusxalash', 1500);
          });
        });
      }
      return;
    }

    if (hash.startsWith('#/letter/')) {
      const letter = decodeURIComponent(hash.slice(9));
      highlightActiveLetter(letter);
      const recs = await loadLetter(letter);
      view.innerHTML = renderLetterPage(letter, recs);
      document.title = `${letter} harfi — Izoh`;
      window.scrollTo(0, 0);
      return;
    }

    view.innerHTML = renderHome();
  } catch (e) {
    view.innerHTML = `<p class="loading">Xato: ${esc(e.message)}</p>`;
  }
}

function highlightActiveLetter(letter) {
  document.querySelectorAll('#letters a').forEach(a => {
    a.classList.toggle('active', a.dataset.letter === letter);
  });
}

function highlightBottomNav(hash) {
  document.querySelectorAll('.bottom-bar a').forEach(a => {
    const nav = a.dataset.nav;
    let active = false;
    if (nav === 'home' && (hash === '#/' || hash === '' || hash.startsWith('#/word/'))) active = true;
    if (nav === 'letters' && (hash === '#/letters' || hash.startsWith('#/letter/'))) active = true;
    a.classList.toggle('active', active);
  });
}

async function buildLettersNav() {
  await loadLetters();
  const nav = document.getElementById('letters');
  nav.innerHTML = LETTERS.map(l =>
    `<a href="#/letter/${encodeURIComponent(l.letter)}" data-letter="${esc(l.letter)}" title="${l.count} so'z">${esc(l.letter)}</a>`
  ).join('');
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
    const q = query.trim().toLocaleLowerCase('uz');
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

function setupRandom() {
  document.getElementById('random-btn').addEventListener('click', () => {
    if (!INDEX.length) return;
    const w = INDEX[Math.floor(Math.random() * INDEX.length)];
    location.hash = '#/word/' + encodeURIComponent(w);
  });
}

// === Init ===
async function init() {
  setupRandom();
  setupSearch();
  await Promise.all([loadIndex(), buildLettersNav()]);
  window.addEventListener('hashchange', route);
  route();
}

init();
