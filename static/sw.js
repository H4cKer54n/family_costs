const CACHE_NAME = 'familycosts-v1';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(clients.claim());
});

self.addEventListener('fetch', (event) => {
  // Network first con fallback básico
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
