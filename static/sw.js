const CACHE_NAME = 'protraining-v1';
const STATIC_ASSETS = [
  '/static/css/main.css',
  '/static/css/asimo.css',
  '/static/images/proftrainingwhite.png',
  '/static/images/PAS_Training_Logo.png',
  '/static/images/background.jpg',
  '/static/font/Roboto-Regular.ttf',
  '/static/font/Roboto-Bold.ttf',
  '/static/font/Roboto-SemiBold.ttf',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
