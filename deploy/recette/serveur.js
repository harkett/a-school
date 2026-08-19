// ============================================================================================
// LE LANCEUR DE RECETTE — un service, un métier.
//
// POURQUOI UN SERVICE À PART. La recette a besoin d'un vrai navigateur et de Node ; le backend
// est une image Python de 800 Mo qui part aussi en production. Y ajouter Chromium et ses
// bibliothèques système, c'est 1,5 Go de plus sur le serveur pour une fonction qui ne s'utilise
// qu'en développement. Le lanceur vit donc dans sa propre boîte, construite sur l'image
// officielle Playwright — celle qui porte déjà les navigateurs et leurs dépendances.
//
// CONTRE QUOI ELLE TOURNE — la question qui a coûté deux passages (18/08/2026). Elle visait le
// serveur de DÉVELOPPEMENT (`http://frontend:5173`). Celui-là recharge la page dès qu'un fichier
// bouge : le robot perdait son écran en pleine saisie et rapportait « Error: locator.fill: Test
// ended ». Un échec qui ne disait rien de l'application, seulement de la manière de la servir.
// Le lanceur CONSTRUIT donc l'application, la sert lui-même, et le navigateur parcourt des
// fichiers figés — exactement ce qu'un utilisateur reçoit en production.
//
// UN PASSAGE, TROIS TEMPS : construire, servir, parcourir. Chacun peut rater, et ces ratés ne
// disent pas la même chose — d'où trois verdicts, pas deux :
//   verte       tout est passé
//   ratee       l'APPLICATION a lâché : un scénario est tombé, ou elle ne se construit même pas
//   impossible  la recette n'a RIEN PARCOURU (l'outillage a manqué) — la note reste intacte
// Confondre les deux derniers marquait « à refaire » un travail que personne n'avait regardé.
//
// CE QU'IL EXPOSE. Trois routes, aucune dépendance : le module `http` de Node suffit.
//   POST /lancer   démarre un passage, refuse s'il y en a déjà un. `?fichier=e2e/….spec.js`
//                  joue LE script d'une note ; sans lui, le lot commun (administration, grilles)
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
const PREVIEW_PORT = Number(process.env.PREVIEW_PORT || 4173)
const BASE_URL = process.env.BASE_URL || `http://localhost:${PREVIEW_PORT}`

// L'état du passage en cours. Il vit en mémoire : un passage dure trois minutes, et le service
// redémarre avec la boîte. Rien à persister ici — la BASE garde le verdict, pas le déroulé.
let passage = null

function neuf(fichier = null) {
  return {
    enCours: true,
    debut: Date.now(),
    fichier,           // le script de la note, ou null pour le lot commun
    total: 0,          // nombre de scénarios annoncés par Playwright
    faits: 0,          // combien sont terminés
    etape: 'Construction de l’application',
    verdict: null,     // 'verte' | 'ratee' | 'impossible' une fois fini
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
//
// LE NETTOYAGE N'EST PAS COSMÉTIQUE. Playwright encadre chaque échec de filets de tirets, et le
// titre du scénario se retrouvait avec « ──────────── » collé au bout : la phrase affichée à
// l'administrateur devenait illisible là où elle devait être la plus claire.
const DECOR = /[─═━–—\-]{3,}/g

function propre(texte) {
  return texte.replace(DECOR, ' ').replace(/\s+/g, ' ').trim()
}

function motif(lignes) {
  const echecs = lignes.filter(l => /^\s*\d+\)\s+e2e/.test(l))
                       .map(l => propre(l.split('›').pop()))
                       .filter(Boolean)
  const message = lignes.find(l => /^\s*(Error:|TimeoutError:)/.test(l.trim()))
  const quoi = echecs.length
    ? echecs.map(e => `« ${e} »`).join(', ')
    : 'un scénario'
  const pourquoi = message ? ` — ${propre(message).slice(0, 200)}` : ''
  return `${echecs.length > 1 ? 'Ont' : 'A'} échoué : ${quoi}${pourquoi}`
}

// CE QUI A LÂCHÉ À LA CONSTRUCTION. Vite dit la faute en une ligne (« [vite]: Rollup failed to
// resolve import… », « error during build ») ; le reste est du bruit. À défaut, les dernières
// lignes valent mieux qu'un « code 1 » sec.
function motifConstruction(lignes) {
  const faute = lignes.find(l => /(^|\s)(error|Error|ERROR)\b/.test(l) && !/\b0 error/.test(l))
  const bout = lignes.slice(-3).map(propre).filter(Boolean).join(' · ')
  return propre(faute || bout || 'aucun message').slice(0, 300)
}

// ── LE DÉROULÉ : construire, servir, parcourir ───────────────────────────────────────────────

// LA JAUGE NE LIT QUE PLAYWRIGHT (`suivre`). La construction affiche « ✓ 412 modules
// transformed », que le motif des scénarios terminés reconnaissait : la jauge annonçait
// 412 scénarios faits avant même que le navigateur ait ouvert quoi que ce soit.
function flot(p, suivre) {
  return morceau => {
    const texte = morceau.toString()
    for (const ligne of texte.split('\n')) {
      if (!ligne.trim()) continue
      p.sortie.push(ligne)
      if (p.sortie.length > 400) p.sortie.shift()
      if (suivre) lire(ligne, p)
    }
  }
}

// Un programme, du début à la fin. Rend `{ code }`, ou `{ erreur }` si la commande n'a même pas
// pu démarrer — les deux ne se soignent pas pareil : l'une accuse l'application, l'autre la boîte.
function tourner(commande, args, p, suivre, env = {}) {
  return new Promise(resolve => {
    const enfant = spawn(commande, args, {
      cwd: PROJET,
      env: { ...process.env, BASE_URL, CI: '1', ...env },
    })
    enfant.stdout.on('data', flot(p, suivre))
    enfant.stderr.on('data', flot(p, suivre))
    enfant.on('close', code => resolve({ code }))
    enfant.on('error', err => resolve({ erreur: err.message }))
  })
}

// LE SERVEUR DE L'APPLICATION CONSTRUITE. DÉTACHÉ pour être tuable EN GROUPE : `npx` lance
// `vite`, qui est un autre process — tuer le premier laisserait le second sur le port, et le
// passage suivant trouverait la place prise (`strictPort` refuse alors de démarrer).
function servir() {
  return spawn('npx', ['vite', 'preview', '--port', String(PREVIEW_PORT)], {
    cwd: PROJET,
    detached: true,
    env: { ...process.env, CI: '1' },
    stdio: ['ignore', 'pipe', 'pipe'],
  })
}

function eteindre(serveur) {
  if (!serveur || serveur.killed) return
  try {
    process.kill(-serveur.pid, 'SIGTERM')
  } catch {
    try { serveur.kill('SIGTERM') } catch { /* déjà éteint */ }
  }
}

// ATTENDRE QU'IL RÉPONDE. `vite preview` rend la main avant d'écouter : lancer le navigateur
// aussitôt donnait un ERR_CONNECTION_REFUSED sur le premier scénario — un faux échec de
// l'application, le genre même que ce chantier élimine.
async function attendre(url, secondes = 60) {
  for (let i = 0; i < secondes * 2; i++) {
    try {
      const r = await fetch(url, { redirect: 'manual' })
      if (r.status < 500) return true
    } catch { /* pas encore à l'écoute */ }
    await new Promise(r => setTimeout(r, 500))
  }
  return false
}

function fin(p, verdict, etape, detail) {
  p.enCours = false
  p.verdict = verdict
  p.etape = etape
  p.detail = detail
}

async function deroule(p) {
  let serveur = null
  try {
    // 1. CONSTRUIRE — le code du moment, jamais un `dist/` qui traîne d'hier.
    p.etape = 'Construction de l’application'
    const bati = await tourner('npm', ['run', 'build'], p, false)
    if (bati.erreur) {
      return fin(p, 'impossible', 'La construction n’a pas pu démarrer',
                 `La commande de construction n’a pas pu être lancée : ${bati.erreur}`)
    }
    if (bati.code !== 0) {
      // PAS « impossible » : une application qui ne se construit pas est cassée, et la note le
      // mérite. Aucun scénario n'était nécessaire pour le voir.
      return fin(p, 'ratee', 'La construction a échoué',
                 `L’application ne se construit pas — ${motifConstruction(p.sortie)}`)
    }

    // 2. SERVIR — dans cette boîte-ci, d'où `localhost` du point de vue du navigateur.
    p.etape = 'Démarrage de l’application'
    serveur = servir()
    serveur.stdout.on('data', flot(p, false))
    serveur.stderr.on('data', flot(p, false))
    if (!(await attendre(BASE_URL))) {
      return fin(p, 'impossible', 'L’application n’a pas répondu',
                 `L’application construite n’a pas répondu sur ${BASE_URL} en une minute : ` +
                 'rien n’a été parcouru. Le journal du service dit pourquoi — ' +
                 'docker compose logs recette')
    }

    // 3. PARCOURIR. UNE NOTE JOUE SON SCRIPT, PAS CELUI DES AUTRES. Sans fichier, on parcourt le
    // lot commun — l'administration, les grilles ; avec un fichier, ce script-là et lui seul,
    // et `SCRIPT_DE_NOTE` lève le filtre qui écarte les scripts de note du lot commun.
    p.etape = 'Démarrage du navigateur'
    const passe = await tourner(
      'npx',
      ['playwright', 'test', '--reporter=list', ...(p.fichier ? [p.fichier] : [])],
      p, true,
      p.fichier ? { SCRIPT_DE_NOTE: '1' } : {})
    if (passe.erreur) {
      return fin(p, 'impossible', 'Le navigateur n’a pas pu démarrer',
                 `Playwright n’a pas pu être lancé : ${passe.erreur}`)
    }
    if (passe.code === 0) {
      if (p.total) p.faits = p.total
      return fin(p, 'verte', 'Terminé', null)
    }
    return fin(p, 'ratee', 'Terminé avec des échecs', motif(p.sortie))
  } catch (err) {
    fin(p, 'impossible', 'Le passage s’est interrompu',
        `Le lanceur s’est arrêté en route : ${err.message}. Rien n’a été parcouru.`)
  } finally {
    // LE SERVEUR MEURT AVEC LE PASSAGE, quelle qu'en soit la fin. Un `vite preview` oublié garde
    // le port et sert l'application d'AVANT : le passage suivant éprouverait du vieux code.
    eteindre(serveur)
  }
}

function lancer(fichier) {
  const p = neuf(fichier)
  passage = p
  // Rend la main tout de suite : l'écran suit l'avancement par `/etat`, il n'attend pas ici.
  deroule(p)
  return p
}

function vue(p) {
  if (!p) return { enCours: false, verdict: null, total: 0, faits: 0, etape: null, detail: null, fichier: null }
  return {
    enCours: p.enCours,
    fichier: p.fichier,
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

  const adresse = new URL(req.url, 'http://recette')

  if (adresse.pathname === '/sante') return repondre(200, { status: 'ok' })

  if (adresse.pathname === '/lancer' && req.method === 'POST') {
    if (passage && passage.enCours) return repondre(409, { erreur: 'Une recette est déjà en cours.' })
    // LE NOM DU SCRIPT EST VÉRIFIÉ, JAMAIS RELAYÉ TEL QUEL. Il part en argument d'une commande :
    // un chemin libre y ferait entrer n'importe quel fichier de la machine. Un script de recette
    // vit dans `e2e/`, s'appelle `.spec.js`, et son nom ne porte que des lettres, chiffres,
    // points et tirets — tout le reste est refusé.
    const demande = adresse.searchParams.get('fichier')
    if (demande && !/^e2e\/[a-zA-Z0-9._-]+\.spec\.js$/.test(demande)) {
      return repondre(400, { erreur: 'Nom de script refusé.' })
    }
    return repondre(200, vue(lancer(demande || null)))
  }

  if (adresse.pathname === '/etat') return repondre(200, vue(passage))

  return repondre(404, { erreur: 'Route inconnue.' })
}).listen(PORT, '0.0.0.0', () => console.log(`Lanceur de recette à l'écoute sur ${PORT}`))
