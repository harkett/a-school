import { defineConfig } from '@playwright/test'

// Tests bout-en-bout : un vrai navigateur ouvre l'application et parcourt les ecrans.
// UN SEUL APPEL PAYANT dans toute la recette : la generation d'une grille (grilles.spec.js).
// Tout le reste est gratuit, y compris « Propose-moi une idee », eprouve sans appeler le modele.
// `BASE_URL` pour viser autre chose que le poste local.
// LES SCRIPTS DE NOTE NE TOURNENT QUE POUR LEUR NOTE. `tache-16.spec.js` eprouve UN chantier :
// il est ecrit avant lui, donc rouge tant qu'il n'est pas fait. Le laisser dans le lot commun
// ferait rater la recette de TOUTES les autres notes, pour un travail qu'aucune ne demandait —
// et « ratee » veut dire « le travail de cette note ne tient pas », pas « un chantier voisin
// n'est pas commence ». Le lanceur pose `SCRIPT_DE_NOTE` quand il vise le script d'une note.
const scriptDeNote = !!process.env.SCRIPT_DE_NOTE

export default defineConfig({
  testDir: './e2e',
  testIgnore: scriptDeNote ? [] : ['**/tache-*.spec.js'],
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
