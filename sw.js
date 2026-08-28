// Service worker minimal : suffisant pour rendre le site "installable"
// (icône dans la barre d'adresse). Met juste la page en cache pour un
// démarrage plus rapide / un minimum de résilience hors-ligne.

const CACHE_NAME = 'netflox-cache-v1';
const CORE_ASSETS = ['./index.html'];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(CORE_ASSETS))
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
    // Ne touche qu'aux requêtes de navigation (la page elle-même) ;
    // tout le reste (API TMDB, images, polices) passe directement au réseau.
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request).catch(() => caches.match('./index.html'))
        );
    }
});
