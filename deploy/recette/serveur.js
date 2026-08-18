// ============================================================================================
// LE LANCEUR DE RECETTE — un service, un métier.
//
// POURQUOI UN SERVICE À PART. La recette a besoin d'un vrai navigateur et de Node ; le backend
// est une image Python de 800 Mo qui part aussi en production. Y ajouter Chromium et ses
// bibliothèques système, c'est 1,5 Go de plus sur le serveur pour une fonction qui ne s'utilise
// qu'en développement. Le lanceur vit donc dans sa propre boîte, construite sur l'image
// officielle Playwright — celle qui porte déjà les navigateurs et leurs dépendances.
//
// CE QU'IL EXPOSE. Trois routes, aucune dépendance : le module `http` de Node suffit.
//   POST /lancer   démarre un passage, refuse s'il y en a déjà un
//   GET  /etat     où on en est : combien de scénarios passés sur combien, et le verdict
//   GET  /sante    la boîte répond
//
// UN SEUL PASSAGE À LA FOIS. Deux recettes en parallèle écrivent dans la même base et se
// marchent dessus — c'est exactement la panne qui a fallu corriger dans playwright.config.js.
// La deuxième demande est refusée, elle n'attend pas.
// ============================================================================================
import http from 'node:http'
import { spawn } from 'node:child_process'

const PORT = Number(process.env.PORT || 9100)
const PROJET = '/app/frontend'

// L'état du passage en cours. Il vit en mémoire : un passage dure trois minutes, et le service
// redémarre avec la boîte. Rien à persister ici — la BASE garde le verdict, pas le déroulé.
let passage = null

function neuf() {
  return {
    enCours: true,
    debut: Date.now(),
    total: 0,          // nombre de scénarios annoncés par Playwright
    faits: 0,          // combien sont terminés
    etape: 'Démarrage du navigateur',
    verdict: null,     // 'verte' | 'ratee' une fois fini
    detail: null,      // ce qui a lâché, en clair
    sortie: [],        // les dernières lignes, pour le diagnostic
  }
}

// Playwright annonce « Running 5 tests using 1 worker », puis une ligne par scénario terminé :
//   ok 1 e2e\admin.spec.js:80:1 › toute l administration s ouvre sans casse (1.2m)
//   1) e2e\grilles.spec.js:172:1 › ...  ← un échec
// On lit ça au fil de l'eau : c'est ce qui fait avancer la jauge.
function lire(ligne, p) {
  const annonce = ligne.match(/Running (\d+) test/)
  if (annonce) { p.total = Number(annonce[1]); return }

  const fini = ligne.match(/^\s*(ok|✓|✘|×)\s+(\d+)\s+(.*)$/)
  if (fini) {
    p.faits = Number(fini[2])
    // Le titre du scénario, sans le chemin du fichier ni la durée : c'est ce qu'on affiche.
    const titre = fini[3].split('›').pop().replace(/\s*\([^)]*\)\s*$/, '').trim()
    p.etape = titre || p.etape
  }
}

// CE QUI A LÂCHÉ, en une phrase lisible. La sortie de Playwright fait des centaines de lignes ;
// ce qui compte tient dans les lignes d'échec numérotées et le message d'erreur qui suit.
function motif(lignes) {
  const echecs = lignes.filter(l => /^\s*\d+\)\s+e2e/.test(l))
                       .map(l => l.split('›').pop().trim())
  const message = lignes.find(l => /^\s*(Error:|TimeoutError:)/.test(l.trim()))
  const quoi = echecs.length
    ? echecs.map(e => `« ${e} »`).join(', ')
    : 'un scénario'
  const pourquoi = message ? ` — ${message.trim().slice(0, 200)}` : ''
  return `${echecs.length > 1 ? 'Ont' : 'A'} échoué : ${quoi}${pourquoi}`
}

function lancer() {
  const p = neuf()
  passage = p

  const enfant = spawn('npx', ['playwright', 'test', '--reporter=list'], {
    cwd: PROJET,
    env: { ...process.env, BASE_URL: process.env.BASE_URL || 'http://frontend:5173', CI: '1' },
  })

  const flot = morceau => {
    const texte = morceau.toString()
    for (const ligne of texte.split('\n')) {
      if (!ligne.trim()) continue
      p.sortie.push(ligne)
      if (p.sortie.length > 400) p.sortie.shift()
      lire(ligne, p)
    }
  }
  enfant.stdout.on('data', flot)
  enfant.stderr.on('data', flot)

  enfant.on('close', code => {
    p.enCours = false
    p.verdict = code === 0 ? 'verte' : 'ratee'
    p.etape = code === 0 ? 'Terminé' : 'Terminé avec des échecs'
    if (code !== 0) p.detail = motif(p.sortie)
    if (code === 0 && p.total) p.faits = p.total
  })

  enfant.on('error', err => {
    p.enCours = false
    p.verdict = 'ratee'
    p.detail = `La recette n'a pas pu démarrer : ${err.message}`
  })

  return p
}

function vue(p) {
  if (!p) return { enCours: false, verdict: null, total: 0, faits: 0, etape: null, detail: null }
  return {
    enCours: p.enCours,
    verdict: p.verdict,
    total: p.total,
    faits: p.faits,
    etape: p.etape,
    detail: p.detail,
    secondes: Math.round((Date.now() - p.debut) / 1000),
  }
}

http.createServer((req, res) => {
  const repondre = (code, corps) => {
    res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8' })
    res.end(JSON.stringify(corps))
  }

  if (req.url === '/sante') return repondre(200, { status: 'ok' })

  if (req.url === '/lancer' && req.method === 'POST') {
    if (passage && passage.enCours) return repondre(409, { erreur: 'Une recette est déjà en cours.' })
    return repondre(200, vue(lancer()))
  }

  if (req.url === '/etat') return repondre(200, vue(passage))

  return repondre(404, { erreur: 'Route inconnue.' })
}).listen(PORT, '0.0.0.0', () => console.log(`Lanceur de recette à l'écoute sur ${PORT}`))
