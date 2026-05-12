import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      cleanupOutdatedCaches: true,
      includeAssets: ['icon-192.png', 'icon-512.png', 'apple-touch-icon.png'],
      manifest: {
        name: 'aSchool',
        short_name: 'aSchool',
        description: 'Générateur d\'activités pédagogiques',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        orientation: 'portrait',
        background_color: '#ffffff',
        theme_color: '#6b001d',
        lang: 'fr',
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any maskable' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
        ],
      },
      workbox: {
        skipWaiting: true,
        clientsClaim: true,
        navigateFallback: '/index.html',
        navigateFallbackDenylist: [/^\/api\//],
        runtimeCaching: [
          {
            // CRITIQUE : cookies httpOnly + rotation token → jamais mis en cache
            urlPattern: ({ url }) => url.pathname.startsWith('/api/'),
            handler: 'NetworkOnly',
          },
          {
            // Assets statiques immuables au build → CacheFirst 30 jours
            urlPattern: /\.(?:js|css|woff2?|png|jpg|svg|ico)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'aschool-static-v1',
              expiration: { maxEntries: 80, maxAgeSeconds: 2592000 },
            },
          },
        ],
      },
    }),
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: false,
        cookieDomainRewrite: 'localhost',
      },
    },
  },
})
