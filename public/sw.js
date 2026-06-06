/*
  Crypto Analysis AI — Service Worker
  Estrategias:
  - Navegación (páginas): Network First -> Cache -> Offline Fallback
  - Assets estáticos: Cache First -> Network
  - APIs/otros: passthrough (sin interceptar)
*/

const CACHE_STATIC = "crypto-ai-static-v1";
const CACHE_PAGES = "crypto-ai-pages-v1";

const CORE_ASSETS = [
  "/",
  "/manifest.json",
  "/icon-192x192.png",
  "/icon-512x512.png",
];

/* ---------- UTILITIES ---------- */

function isSameOriginGET(request) {
  return (
    request.method === "GET" &&
    new URL(request.url).origin === self.location.origin
  );
}

function isStaticAsset(request) {
  return /\.(?:js|css|png|jpe?g|svg|gif|ico|woff2?|ttf|otf|eot|webp)$/i.test(
    new URL(request.url).pathname
  );
}

function isNavigationRequest(request) {
  return request.mode === "navigate";
}

/* ---------- INSTALL ---------- */

self.addEventListener("install", (event) => {
  console.log("[SW] Install");
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_STATIC);
      await cache.addAll(CORE_ASSETS);
    })()
  );
  self.skipWaiting();
});

/* ---------- ACTIVATE ---------- */

self.addEventListener("activate", (event) => {
  console.log("[SW] Activate");
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(
        keys.map((key) => {
          if (key !== CACHE_STATIC && key !== CACHE_PAGES) {
            return caches.delete(key);
          }
          return null;
        })
      );
      await self.clients.claim();
    })()
  );
});

/* ---------- FETCH ---------- */

self.addEventListener("fetch", (event) => {
  const { request } = event;

  if (!isSameOriginGET(request)) return;

  if (isNavigationRequest(request)) {
    event.respondWith(handleNavigation(request));
  } else if (isStaticAsset(request)) {
    event.respondWith(handleStaticAsset(request));
  }
  // Otros requests (ej. API externa) se dejan pasar sin tocar
});

/* ---------- HANDLERS ---------- */

async function handleNavigation(request) {
  const cache = await caches.open(CACHE_PAGES);

  try {
    const networkResponse = await fetch(request);
    if (networkResponse && networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (err) {
    const cached = await cache.match(request);
    if (cached) return cached;

    // Último recurso: devolver página raíz cacheada (mejor que nada)
    const rootFallback = await caches.match("/");
    if (rootFallback) return rootFallback;

    throw err;
  }
}

async function handleStaticAsset(request) {
  const cache = await caches.open(CACHE_STATIC);

  const cached = await cache.match(request);
  if (cached) return cached;

  try {
    const networkResponse = await fetch(request);
    if (networkResponse && networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (err) {
    // Si no está en caché y falla la red, dejamos que falle naturalmente
    throw err;
  }
}