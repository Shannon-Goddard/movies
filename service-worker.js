const CACHE_NAME  = 'movies-shell-v2';
const VIDEO_CACHE = 'movies-video-v1';
const BASE = '/movies';

const SHELL_ASSETS = [
  `${BASE}/`,
  `${BASE}/index.html`,
  `${BASE}/css/app.css`,
  `${BASE}/js/app.js`,
  `${BASE}/js/player.js`,
  `${BASE}/js/queue.js`,
  `${BASE}/js/scroll.js`,
  `${BASE}/js/library.js`,
  `${BASE}/js/api.js`,
  `${BASE}/js/utils.js`,
  `${BASE}/js/i18n/en.js`,
  `${BASE}/js/views/home.js`,
  `${BASE}/js/views/search.js`,
  `${BASE}/js/views/library.js`,
  `${BASE}/manifest.json`,
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(SHELL_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME && k !== VIDEO_CACHE)
            .map(k => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Video streams from IA — cache first (skip 206 partial)
  if (url.hostname === 'archive.org' || url.hostname.endsWith('.archive.org')) {
    event.respondWith(_cacheFirst(request, VIDEO_CACHE));
    return;
  }

  // API calls — always network
  if (url.hostname.includes('execute-api.amazonaws.com')) {
    event.respondWith(fetch(request));
    return;
  }

  // Shell assets — cache first
  event.respondWith(_cacheFirst(request, CACHE_NAME));
});

async function _cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok && response.status !== 206) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response('Offline', { status: 503 });
  }
}
