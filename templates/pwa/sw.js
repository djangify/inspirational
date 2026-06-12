{% load static %}// Inspirational Guidance — service worker (keep-it-simple PWA + offline article reading)
// Bump CACHE_VERSION whenever you want every installed app to refresh its caches.
const CACHE_VERSION = 'ig-pwa-v2';
const ARTICLE_CACHE = 'ig-articles-v1';
const OFFLINE_URL = '/offline/';

// How many article pages to keep on the device before evicting the oldest.
const ARTICLE_LIMIT = 100;

// Files cached on install so the offline page always works.
const PRECACHE_URLS = [
  OFFLINE_URL,
  '{% static "css/output.css" %}',
  '{% static "images/android-chrome-192x192.png" %}',
  '{% static "images/android-chrome-512x512.png" %}'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  const keep = [CACHE_VERSION, ARTICLE_CACHE];
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((key) => !keep.includes(key)).map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

// Keep the article cache from growing without bound (oldest entries evicted first).
function trimCache(cacheName, maxEntries) {
  caches.open(cacheName).then((cache) => {
    cache.keys().then((keys) => {
      if (keys.length > maxEntries) {
        cache.delete(keys[0]).then(() => trimCache(cacheName, maxEntries));
      }
    });
  });
}

self.addEventListener('fetch', (event) => {
  const req = event.request;

  // Only handle GET requests.
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Ignore anything off-site (Stripe, analytics, CDNs, external article images) — let it hit the network.
  if (url.origin !== self.location.origin) return;

  // Never cache dynamic / logged-in / payment areas. Always go to the network.
  const BYPASS = ['/accounts', '/shop', '/admin', '/sw.js'];
  if (BYPASS.some((path) => url.pathname.startsWith(path))) return;

  // Uploaded article images: serve cache-first so cached articles show their pictures offline.
  if (url.pathname.startsWith('/media/news/')) {
    event.respondWith(
      caches.match(req).then((cached) => {
        const fetched = fetch(req).then((res) => {
          if (res && res.ok) {
            const copy = res.clone();
            caches.open(ARTICLE_CACHE).then((cache) => cache.put(req, copy));
          }
          return res;
        }).catch(() => cached);
        return cached || fetched;
      })
    );
    return;
  }

  // Static assets: serve from cache first for speed, refresh in the background.
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(req).then((cached) => {
        const fetched = fetch(req).then((res) => {
          if (res && res.ok) {
            const copy = res.clone();
            caches.open(CACHE_VERSION).then((cache) => cache.put(req, copy));
          }
          return res;
        }).catch(() => cached);
        return cached || fetched;
      })
    );
    return;
  }

  // Page navigations: network-first (always fresh when online).
  // If the page opted in with the X-PWA-Cacheable header (articles only), store a
  // copy for offline reading. Pages without that header are never cached.
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const cacheable =
            res &&
            res.ok &&
            res.type === 'basic' &&
            res.headers.get('X-PWA-Cacheable') === '1';
          if (cacheable) {
            const copy = res.clone();
            caches.open(ARTICLE_CACHE).then((cache) => {
              cache.put(req, copy).then(() => trimCache(ARTICLE_CACHE, ARTICLE_LIMIT));
            });
          }
          return res;
        })
        .catch(() =>
          // Offline: serve the cached article if we have it, otherwise the offline page.
          caches.match(req).then((cached) => cached || caches.match(OFFLINE_URL))
        )
    );
    return;
  }
});
