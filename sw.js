/* PaperChase Service Worker — cache-first for assets, network-first for data */
const CACHE = 'paperchase-v3';
const ASSETS = [
  '/', '/manifest.json',
  '/assets/design-system.css', '/assets/supabase-client.js', '/assets/countdown.js',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  // Data API calls — network first, cache fallback
  if (url.pathname.includes('/data/') || url.hostname === 'raw.githubusercontent.com') {
    e.respondWith(
      fetch(e.request).then(r => caches.open(CACHE).then(c => { c.put(e.request, r.clone()); return r; }))
        .catch(() => caches.match(e.request).then(r => r || new Response('{"error":"offline"}', {headers:{'Content-Type':'application/json'}})))
    );
    return;
  }
  // Everything else — cache first
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request).then(r => { caches.open(CACHE).then(c => c.put(e.request, r.clone())); return r; }))
  );
});
