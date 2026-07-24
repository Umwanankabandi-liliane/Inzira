/* Inzira PWA — fresh app code + background push alerts */
const CACHE = 'inzira-v24';

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  if (url.origin !== self.location.origin) return;

  const isAppCode =
    url.pathname === '/' ||
    url.pathname.endsWith('.html') ||
    url.pathname.endsWith('.js') ||
    url.pathname.endsWith('.css') ||
    url.pathname === '/sw.js';

  if (!isAppCode) return;

  e.respondWith(
    fetch(e.request, { cache: 'no-store' }).catch(() => caches.match(e.request))
  );
});

self.addEventListener('push', (event) => {
  let payload = {
    title: 'Inzira',
    body: 'Deadline alert on a saved site',
    url: '/#/followed',
    icon: '/assets/icons/icon-192.svg',
  };
  try {
    if (event.data) {
      payload = { ...payload, ...event.data.json() };
    }
  } catch (_) {}

  event.waitUntil(
    self.registration.showNotification(payload.title || 'Inzira', {
      body: payload.body || '',
      icon: payload.icon || '/assets/icons/icon-192.svg',
      badge: '/assets/icons/icon-192.svg',
      tag: payload.url || 'inzira-alert',
      renotify: true,
      data: { url: payload.url || '/#/followed' },
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const target = event.notification.data?.url || '/#/followed';
  const absolute = new URL(target, self.location.origin).href;
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
      for (const client of list) {
        if ('focus' in client) {
          client.navigate(absolute);
          return client.focus();
        }
      }
      if (clients.openWindow) return clients.openWindow(absolute);
      return null;
    })
  );
});
