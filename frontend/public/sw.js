const CACHE_NAME = 'qiming-pwa-v1'
const APP_SHELL = [
  '/',
  '/chat',
  '/login',
  '/register',
  '/settings',
  '/manifest.webmanifest',
  '/pwa-icon.svg',
  '/pwa-maskable.svg',
  '/favicon.svg'
]

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).catch(() => Promise.resolve())
  )
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
    ))
  )
  self.clients.claim()
})

self.addEventListener('fetch', (event) => {
  const { request } = event
  if (request.method !== 'GET') return

  const url = new URL(request.url)
  if (url.origin !== self.location.origin) return
  if (url.pathname.startsWith('/api') || url.pathname.startsWith('/uploads') || url.pathname.startsWith('/avatars')) return

  const isNavigation = request.mode === 'navigate'

  if (isNavigation) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const cloned = response.clone()
          caches.open(CACHE_NAME).then((cache) => cache.put('/__app_shell__', cloned)).catch(() => {})
          return response
        })
        .catch(async () => {
          const cache = await caches.open(CACHE_NAME)
          return (await cache.match('/__app_shell__')) || (await cache.match('/')) || Response.error()
        })
    )
    return
  }

  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached
      return fetch(request).then((response) => {
        if (!response || response.status !== 200 || response.type !== 'basic') return response
        const cloned = response.clone()
        caches.open(CACHE_NAME).then((cache) => cache.put(request, cloned)).catch(() => {})
        return response
      })
    })
  )
})
