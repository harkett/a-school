import { defineConfig } from '@playwright/test'

// Tests bout-en-bout : un vrai navigateur ouvre l'application et parcourt les ecrans.
// Aucun appel a une IA, aucun cout. `BASE_URL` pour viser autre chose que le poste local.
export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  fullyParallel: false,
  // UN SEUL TRAVAILLEUR. `fullyParallel: false` ne garde l'ordre qu'A L'INTERIEUR d'un fichier :
  // les fichiers, eux, tournent en parallele. Deux navigateurs qui ecrivent dans la meme base au
  // meme moment se marchent dessus — la recette des grilles echouait des qu'elle partageait la
  // machine avec celle de l'administration, et passait seule.
  workers: 1,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:5173',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },
})
