// Tests du bon réflexe sur 401 (P3.5) : renouveler en silence d'abord,
// ne rediriger vers /login QUE si le « pass long » (refresh token) est mort,
// et ne jamais lancer deux renouvellements en parallèle (single-flight partagé).
// Lance avec :  node --test src/utils/api.test.js   (depuis frontend/)
import test, { beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import {
  apiFetch, refreshSession, setSessionExpiredHandler, _resetForTests,
  lireReponse, messagePourEcran, MSG_SERVEUR,
} from './api.js'

const ok200 = () => ({ ok: true,  status: 200, json: async () => ({}) })
const r401  = () => ({ ok: false, status: 401, json: async () => ({}) })

beforeEach(() => {
  _resetForTests()
  setSessionExpiredHandler(() => {})   // neutre par défaut ; surchargé dans les tests concernés
})

test('1. 200 → passe tel quel, aucun renouvellement, aucune redirection', async () => {
  let refreshHits = 0, redirects = 0
  setSessionExpiredHandler(() => { redirects++ })
  global.fetch = async (url) => {
    if (url === '/api/auth/refresh') { refreshHits++; return r401() }
    return ok200()
  }
  const res = await apiFetch('/api/x')
  assert.equal(res.status, 200)
  assert.equal(refreshHits, 0)
  assert.equal(redirects, 0)
})

test('2. 401 → renouvellement OK → rejeu 200, PAS de redirection', async () => {
  let refreshHits = 0, redirects = 0, xHits = 0
  setSessionExpiredHandler(() => { redirects++ })
  global.fetch = async (url) => {
    if (url === '/api/auth/refresh') { refreshHits++; return ok200() }
    xHits++
    return xHits === 1 ? r401() : ok200()   // appel initial 401, rejeu 200
  }
  const res = await apiFetch('/api/x')
  assert.equal(res.status, 200)
  assert.equal(refreshHits, 1)
  assert.equal(xHits, 2)                     // appel initial + un seul rejeu
  assert.equal(redirects, 0)
})

test('3. 401 → renouvellement 401 (pass long mort) → UNE redirection', async () => {
  let refreshHits = 0, redirects = 0
  setSessionExpiredHandler(() => { redirects++ })
  global.fetch = async (url) => {
    if (url === '/api/auth/refresh') { refreshHits++; return r401() }
    return r401()
  }
  const res = await apiFetch('/api/x')
  assert.equal(res.status, 401)
  assert.equal(refreshHits, 1)
  assert.equal(redirects, 1)
})

test('4. deux 401 simultanés → UN SEUL renouvellement, UNE SEULE redirection', async () => {
  let refreshHits = 0, redirects = 0
  setSessionExpiredHandler(() => { redirects++ })
  global.fetch = async (url) => {
    if (url === '/api/auth/refresh') {
      refreshHits++
      await new Promise(r => setTimeout(r, 20))   // lent → garantit le partage de la promesse
      return r401()
    }
    return r401()
  }
  const [a, b] = await Promise.all([apiFetch('/api/x'), apiFetch('/api/x')])
  assert.equal(a.status, 401)
  assert.equal(b.status, 401)
  assert.equal(refreshHits, 1)   // single-flight : un seul POST /api/auth/refresh
  assert.equal(redirects, 1)     // verrou : une seule sortie vers /login
})

test('5. refresh « façon AuthContext » + apiFetch au même instant → UN SEUL renouvellement', async () => {
  let refreshHits = 0
  global.fetch = async (url) => {
    if (url === '/api/auth/refresh') {
      refreshHits++
      await new Promise(r => setTimeout(r, 20))   // lent → l'in-flight est encore vivant quand apiFetch arrive
      return r401()
    }
    return r401()
  }
  // AuthContext (proactif) appelle refreshSession() directement ;
  // apiFetch (réactif) prend un 401 exactement au même moment.
  await Promise.all([ refreshSession(), apiFetch('/api/x') ])
  assert.equal(refreshHits, 1)   // PROUVE la coordination — pas « par construction »
})

test('6. appel multipart (FormData) → 401 terminal → UNE redirection + corps FormData intact', async () => {
  let redirects = 0, sentBody = 'pas-passé'
  setSessionExpiredHandler(() => { redirects++ })
  global.fetch = async (url, opts) => {
    if (url === '/api/auth/refresh') return r401()
    sentBody = opts.body          // corps réellement transmis à fetch (OCR/dictée)
    return r401()
  }
  const form = new FormData()
  form.append('file', new Blob(['x']), 'dictee.webm')
  const res = await apiFetch('/api/ocr', { method: 'POST', body: form })
  assert.equal(res.status, 401)
  assert.equal(redirects, 1)                 // sortie propre, une seule fois
  assert.ok(sentBody instanceof FormData)    // multipart transmis tel quel, jamais JSON.stringify
})

// ---------------------------------------------------------------------------
// lireReponse / messagePourEcran (règle « deux publics, deux langages ») :
// AUCUN message technique ne doit jamais atteindre l'écran d'un prof — même
// quand le serveur crashe et répond « Internal Server Error » en texte brut.
// ---------------------------------------------------------------------------

test('7. lireReponse : réponse 200 JSON → l’objet, tel quel', async () => {
  const data = await lireReponse({ ok: true, status: 200, json: async () => ({ texte: 'bonjour' }) })
  assert.deepEqual(data, { texte: 'bonjour' })
})

test('8. lireReponse : erreur avec detail TEXTE → le message backend (déjà humain) est levé', async () => {
  await assert.rejects(
    lireReponse({ ok: false, status: 400, json: async () => ({ detail: 'Type d’activité inconnu.' }) }),
    (e) => e.pourEcran === true && e.message === 'Type d’activité inconnu.',
  )
})

test('9. lireReponse : 500 en texte brut (corps illisible) → MSG_SERVEUR, jamais l’erreur de parsing', async () => {
  await assert.rejects(
    lireReponse({ ok: false, status: 500, json: async () => { throw new SyntaxError("Unexpected token 'I'") } }),
    (e) => e.pourEcran === true && e.message === MSG_SERVEUR,
  )
})

test('10. lireReponse : detail NON-texte (tableau de validation 422) → MSG_SERVEUR, jamais le tableau brut', async () => {
  await assert.rejects(
    lireReponse({ ok: false, status: 422, json: async () => ({ detail: [{ loc: ['body', 'niveau'], msg: 'field required' }] }) }),
    (e) => e.pourEcran === true && e.message === MSG_SERVEUR,
  )
})

test('11. messagePourEcran : erreur marquée pourEcran → son message ; technique → MSG_SERVEUR', () => {
  const humaine = new Error('Message écrit pour le prof.')
  humaine.pourEcran = true
  assert.equal(messagePourEcran(humaine), 'Message écrit pour le prof.')
  assert.equal(messagePourEcran(new SyntaxError("Unexpected token 'I'")), MSG_SERVEUR)
  assert.equal(messagePourEcran(new TypeError('Failed to fetch')), MSG_SERVEUR)
  assert.equal(messagePourEcran(null), MSG_SERVEUR)
})
