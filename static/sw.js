const CACHE_NAME = 'eden-admin-v1';

const STATIC_ASSETS = [
    '/',
    '/manifest.json',
    '/images/icon-192.png',
    '/images/icon-512.png',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(STATIC_ASSETS).catch(() => {});
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys.filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            )
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // ═══ NE PAS INTERCEPTER LES VIDÉOS ═══
    if (
        url.pathname.match(/\.(mp4|webm|mov|avi|mkv|m4v|flv)$/) ||
        url.pathname.includes('/videos/') ||
        url.pathname.includes('/media/videos/')
    ) {
        return;
    }

    // ═══ NE PAS INTERCEPTER les requêtes Range (206) ═══
    if (event.request.headers.get('range')) {
        return;
    }

    // ═══ Ne pas intercepter les non-GET ═══
    if (event.request.method !== 'GET') return;

    // ═══ Ne pas intercepter les autres domaines ═══
    if (url.origin !== self.location.origin && !url.hostname.includes('cdn.jsdelivr.net')) {
        return;
    }

    // ═══ Assets statiques → Cache First ═══
    if (
        url.pathname.match(/\.(css|js|png|jpg|jpeg|gif|svg|woff2?|ico)$/) ||
        url.hostname.includes('cdn.jsdelivr.net')
    ) {
        event.respondWith(
            caches.match(event.request).then(cached => {
                return cached || fetch(event.request).then(response => {
                    if (response && response.status === 200 && response.type === 'basic') {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then(cache => {
                            cache.put(event.request, clone).catch(() => {});
                        });
                    }
                    return response;
                });
            })
        );
        return;
    }

    // ═══ Pages HTML → Network First ═══
    event.respondWith(
        fetch(event.request)
            .then(response => {
                if (response && response.status === 200 && response.type === 'basic') {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, clone).catch(() => {});
                    });
                }
                return response;
            })
            .catch(() => caches.match(event.request))
    );
});

self.addEventListener('message', event => {
    if (event.data === 'skipWaiting') self.skipWaiting();
});