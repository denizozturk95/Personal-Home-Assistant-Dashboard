// Minimal service worker — required for iOS "Add to Home Screen" as a real PWA.
// We deliberately don't cache API responses; the frontend shell is trivial and
// every tap should hit the Pi live.

const SHELL = ["/", "/index.html", "/app.js", "/style.css", "/manifest.webmanifest"];
const CACHE = "shell-v1";

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.pathname.startsWith("/api/")) return;
  event.respondWith(
    caches.match(event.request).then((hit) => hit || fetch(event.request))
  );
});
