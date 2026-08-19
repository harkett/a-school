import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'
import pkg from './package.json' with { type: 'json' }

// LE RELAIS VERS LE BACKEND, écrit une fois pour les DEUX serveurs de Vite : `server` (le
// développement) et `preview` (l'application construite, celle que la recette parcourt).
const PROXY_API = {
  '/api': {
    target: `http://${process.env.VITE_API_HOST || 'localhost'}:${process.env.VITE_API_PORT || 8000}`,
    changeOrigin: false,
    cookieDomainRewrite: 'localhost',
  },
}

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      // AUTOUPDATE, sur TOUTES les pages — prof comme admin (07/08/2026).
      //
      // En 'prompt', la version neuve restait derrière : elle attendait qu'on clique. Un
      // utilisateur qui ne voit pas le bandeau, ou qui l'ignore, continue d'utiliser l'ancienne
      // page indéfiniment — et ce qu'il voit à l'écran contredit ce que le serveur lui répond.
      // C'est le pire des états : l'application a l'air de mentir alors qu'elle est correcte.
      //
      // En 'autoUpdate', le nouveau service worker prend la main dès qu'il est installé
      // (skipWaiting) et reprend les onglets déjà ouverts (clientsClaim, plus bas), puis la page
      // se recharge. Ce n'est pas un contournement : `sw.js` est le seul fichier que le
      // navigateur revalide toujours, par obligation de la spécification. Il ne peut donc pas
      // rester bloqué sur une vieille version comme les autres fichiers.
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
  // LA VERSION AFFICHÉE EST LA VRAIE (16/08/2026). Le bas du menu admin annonçait
  // « v1.3 · 02/05/2026 », écrit en dur : trois versions et trois mois de retard. Une version
  // recopiée à la main finit toujours par mentir — celle-ci est lue dans `package.json` au
  // moment de la construction, elle ne peut plus diverger.
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version),
  },
  server: {
    // Docker/Windows : les événements de fichiers ne traversent pas la frontière hôte→conteneur.
    // Sans polling, Vite ne voit jamais les éditions du code → pas de hot-reload (il sert l'ancien
    // module en cache). Le polling force la surveillance → toute modif se recharge toute seule.
    watch: { usePolling: true },
    proxy: PROXY_API,
  },
  // LE SERVEUR DE L'APPLICATION CONSTRUITE — celui que la recette parcourt (18/08/2026).
  //
  // POURQUOI PAS `server`. En développement, Vite recharge la page dès qu'un fichier bouge. Un
  // robot qui remplit un formulaire pendant ce rechargement perd son écran en pleine saisie et
  // rapporte « Error: locator.fill: Test ended » — un échec qui ne dit rien de l'application.
  // `preview` sert `dist/` : des fichiers figés, aucun rechargement, aucune surveillance.
  //
  // LE PROXY EST À REDIRE ICI. Vite ne partage pas les options de `server` avec `preview` :
  // posé sur `server` seul, `/api` n'a plus de destination une fois construit et l'écran de
  // connexion tombe en 404. D'où `PROXY_API`, écrit une fois et donné aux deux.
  preview: {
    host: true,
    port: Number(process.env.PREVIEW_PORT || 4173),
    strictPort: true,
    proxy: PROXY_API,
  },
})
