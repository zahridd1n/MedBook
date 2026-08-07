// BookFlow PWA Service Worker
// Versiyani o'zgartirish barcha keshni tozalaydi
const CACHE_VERSION = 'v3';
const CACHE_NAME = `bookflow-pwa-${CACHE_VERSION}`;

// O'rnatishda keshlanadigan asosiy resurslar
const PRECACHE_URLS = [];

// Install — eskisini o'chirmasdan yangi versiyani yoq
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(PRECACHE_URLS);
        }).then(() => {
            // Eski service worker kutmasdan yanisi faollashsin
            return self.skipWaiting();
        })
    );
});

// Activate — eski keshlarni tozala
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name.startsWith('bookflow-pwa-') && name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        }).then(() => {
            // Barcha ochiq tablarni yangi service worker boshqarsin
            return self.clients.claim();
        })
    );
});

// Fetch — Network First strategiyasi
// Tarmoq mavjud bo'lsa undan, bo'lmasa keshdan
self.addEventListener('fetch', (event) => {
    // Faqat GET so'rovlarini keshla
    if (event.request.method !== 'GET') return;

    // Chrome extension so'rovlarini o'tkazib yubor
    if (event.request.url.startsWith('chrome-extension://')) return;

    // Cross-origin so'rovlarni to'g'ridan-to'g'ri yuborish
    const url = new URL(event.request.url);
    if (url.origin !== self.location.origin) return;

    // API va admin sahifalarni keshlamaslik
    const skipPaths = ['/admin/', '/dashboard/', '/api/', '/telegram/', '/superadmin/'];
    if (skipPaths.some(p => url.pathname.startsWith(p))) return;

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Muvaffaqiyatli javobni keshla
                if (response && response.status === 200 && response.type === 'basic') {
                    const responseToCache = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseToCache);
                    });
                }
                return response;
            })
            .catch(() => {
                // Tarmoq yo'q — keshdan qaytarish
                return caches.match(event.request).then((cached) => {
                    if (cached) return cached;
                    // Offline sahifani qaytarish (agar bo'lmasa — so'rov xatosi)
                    return new Response(
                        '<html><body style="font-family:sans-serif;text-align:center;padding:40px">'
                        + '<h2>📵 Internet aloqasi yo\'q</h2>'
                        + '<p>Iltimos, internet aloqangizni tekshiring va qaytadan urinib ko\'ring.</p>'
                        + '<button onclick="location.reload()">🔄 Qayta urinish</button>'
                        + '</body></html>',
                        { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
                    );
                });
            })
    );
});
