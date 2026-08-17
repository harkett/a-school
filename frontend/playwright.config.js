import { defineConfig } from '@playwright/test'

// Tests bout-en-bout : un vrai navigateur ouvre l'application et parcourt les ecrans.
// Aucun appel a une IA, aucun cout. `BASE_URL` pour viser autre chose que le poste local.
export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  fullyParallel: false,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:5173',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },
})
