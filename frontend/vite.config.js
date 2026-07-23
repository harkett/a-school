import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'prompt',
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
    // Docker/Windows : les événements de fichiers ne traversent pas la frontière hôte→conteneur.
    // Sans polling, Vite ne voit jamais les éditions du code → pas de hot-reload (il sert l'ancien
    // module en cache). Le polling force la surveillance → toute modif se recharge toute seule.
    watch: { usePolling: true },
    proxy: {
      '/api': {
        target: `http://${process.env.VITE_API_HOST || 'localhost'}:${process.env.VITE_API_PORT || 8000}`,
        changeOrigin: false,
        cookieDomainRewrite: 'localhost',
      },
    },
  },
})
