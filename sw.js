// Izoh — Service Worker
// Strategy:
//   - APP_SHELL (HTML, CSS, JS, manifest, icons): network-first
//     -> online: always fresh code, no "stuck on old version" problem
//     -> offline: cached fallback
//   - small DATA (index.json, letters.json): stale-while-revalidate
//   - per-letter DATA (data/<L>.json): cache-first (rarely change, 28 files)
// When a new SW activates, page is auto-reloaded (controllerchange in app.js).
//
// CACHE_VERSION is replaced at build time by build/build_sw.py from content hash.
// Any change to index.html / app.js / style.css / manifest.json → new version → new cache.

const CACHE_VERSION = '45e9392b63ff';
const SHELL_CACHE = `izoh-shell-${CACHE_VERSION}`;
const DATA_CACHE  = `izoh-data-${CACHE_VERSION}`;

const APP_SHELL = [
  './',
  './index.html',
  './style.css',
  './app.js',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/apple-touch-icon.png',
  './data/index.json',
  './data/letters.json',
];

// === Install ===
self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const cache = await caches.open(SHELL_CACHE);
    await cache.addAll(APP_SHELL);
    await self.skipWaiting();   // activate immediately
  })());
});

// === Activate: cleanup old caches + claim clients ===
self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys.filter(k => !k.endsWith(CACHE_VERSION)).map(k => caches.delete(k))
    );
    await self.clients.claim();
  })());
});

// === Fetch routing ===
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;  // only same-origin

  const path = url.pathname;

  // Per-letter data: cache-first
  if (/\/data\/[^/]+\.json$/.test(path) &&
      !path.endsWith('/data/index.json') &&
      !path.endsWith('/data/letters.json')) {
    e.respondWith(cacheFirst(req, DATA_CACHE));
    return;
  }

  // Small data: stale-while-revalidate
  if (path.endsWith('/data/index.json') || path.endsWith('/data/letters.json')) {
    e.respondWith(staleWhileRevalidate(req, DATA_CACHE));
    return;
  }

  // Everything else (app shell, icons): network-first
  e.respondWith(networkFirst(req, SHELL_CACHE));
});

async function networkFirst(req, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const fresh = await fetch(req);
    if (fresh && fresh.ok) cache.put(req, fresh.clone());
    return fresh;
  } catch {
    const cached = await cache.match(req);
    if (cached) return cached;
    // For HTML navigations, fall back to cached index
    if (req.mode === 'navigate') {
      const fallback = await cache.match('./index.html');
      if (fallback) return fallback;
    }
    throw new Error('offline and no cache');
  }
}

async function cacheFirst(req, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(req);
  if (cached) return cached;
  const fresh = await fetch(req);
  if (fresh && fresh.ok) cache.put(req, fresh.clone());
  return fresh;
}

async function staleWhileRevalidate(req, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(req);
  const fetchPromise = fetch(req).then(res => {
    if (res && res.ok) cache.put(req, res.clone());
    return res;
  }).catch(() => null);
  return cached || fetchPromise;
}

// Allow client to force activation (skipWaiting from page)
self.addEventListener('message', e => {
  if (e.data === 'skipWaiting') self.skipWaiting();
});
