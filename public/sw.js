/* Basic, no-dependency PWA service worker */

// Versioned cache to allow updates
const CACHE_NAME = "pwa-cache-v1";

// Minimal core assets. For full offline coverage you can expand this list.
const CORE_ASSETS = [
  "/", // Next app entry
  "/manifest.json",
  "/icon-192x192.png",
  "/icon-512x512.png",
];

self.addEventListener("install", (event) => {
  console.log("[sw] install");
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      await cache.addAll(CORE_ASSETS);
      self.skipWaiting();
    })()
  );
});

self.addEventListener("activate", (event) => {
  console.log("[sw] activate");
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(
        keys.map((key) => (key === CACHE_NAME ? null : caches.delete(key)))
      );
      self.clients.claim();
    })()
  );
});

function isSameOriginGET(request) {
  return (
    request.method === "GET" &&
    new URL(request.url).origin === self.location.origin
  );
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (!isSameOriginGET(request)) return;

  event.respondWith(
    (async () => {
      const cached = await caches.match(request);
      if (cached) return cached;

      try {
        const fresh = await fetch(request);

        // Cache only successful responses
        if (fresh && fresh.ok) {
          const cache = await caches.open(CACHE_NAME);
          cache.put(request, fresh.clone());
        }

        return fresh;
      } catch (err) {
        // Offline fallback: return cached root if available
        const fallback = await caches.match("/");
        if (fallback) return fallback;
        throw err;
      }
    })()
  );
});
