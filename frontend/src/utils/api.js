export const TIMEOUT_AUTH = 8_000   // auth, heartbeat, logout
export const TIMEOUT_STD  = 10_000  // appels standard (profil, activités, admin)
export const TIMEOUT_LONG = 45_000  // opérations longues : génération IA, OCR, mail groupé, purge BDD
// Validation d'un référentiel : épuration du texte + détection des matières par l'IA en un seul
// appel — mesuré à ~3 min sur un vrai dépôt (24/07). L'écran doit attendre le serveur, pas
// l'inverse : abandonner avant lui fabrique des reclics sur un jeton déjà consommé.
export const TIMEOUT_XLONG = 300_000

export const MSG_TIMEOUT = 'Connexion lente ou indisponible. Vérifiez votre réseau et réessayez.'

// Message humain unique quand le serveur est en panne ou répond n'importe quoi (crash base,
// redémarrage, « Internal Server Error » en texte brut). Jamais de détail technique à l'écran.
export const MSG_SERVEUR = "Le serveur aSchool n'a pas pu répondre.\n\nRéessayez dans une minute — si le problème persiste, prévenez votre administrateur."

// Fabrique une erreur DESTINÉE À L'ÉCRAN : son message est écrit pour un prof, il peut être
// affiché tel quel. Toute erreur SANS cette marque est technique → l'écran affiche MSG_SERVEUR.
function erreurEcran(message) {
  const e = new Error(message)
  e.pourEcran = true
  return e
}

// Le message d'une erreur, filtré pour l'écran : humain si marqué pourEcran, sinon MSG_SERVEUR.
// À utiliser dans TOUT catch qui alimente showError — jamais err.message brut.
export function messagePourEcran(err) {
  return err && err.pourEcran ? err.message : MSG_SERVEUR
}

// Le `detail` d'un corps d'erreur déjà lu, filtré EXACTEMENT comme le fait lireReponse :
// on ne rend que ce qui est un vrai message texte (nos messages backend sont écrits pour le
// prof). Un 422 FastAPI renvoie un TABLEAU d'objets : le passer à showError casserait le
// rendu React (« Objects are not valid as a React child »). Renvoie null quand il n'y a rien
// de montrable — l'appelant affiche alors son propre message.
// À utiliser partout où la réponse est lue à la main (flux SSE, corps déjà consommé).
export function detailPourEcran(data) {
  return data && typeof data.detail === 'string' && data.detail.trim() ? data.detail : null
}

// Lit le corps JSON d'une réponse sans JAMAIS laisser fuiter un message technique :
//  - réponse OK → l'objet JSON (ou {} si le corps est vide) ;
//  - réponse en erreur → lève le `detail` du backend SEULEMENT si c'est un vrai message texte
//    (nos messages backend sont écrits pour le prof), sinon MSG_SERVEUR ;
//  - corps illisible (serveur en panne qui répond en texte brut) → MSG_SERVEUR aussi.
export async function lireReponse(res) {
  let data = null
  try { data = await res.json() } catch { /* corps non-JSON = serveur en difficulté */ }
  if (!res.ok) {
    const detail = data && typeof data.detail === 'string' ? data.detail : null
    throw erreurEcran(detail || MSG_SERVEUR)
  }
  return data || {}
}

import { reportApiSuccess, reportApiFailure } from '../serverHealth.js'

export async function fetchWithTimeout(url, options = {}, timeout = TIMEOUT_STD) {
  const controller = new AbortController()
  const id = setTimeout(() => controller.abort(), timeout)
  try {
    const res = await fetch(url, { ...options, signal: controller.signal })
    // Santé serveur : 5xx = serveur en difficulté ; <500 (y compris 4xx auth/saisie)
    // = serveur joignable, donc « sain » de son point de vue.
    if (res.status >= 500) reportApiFailure()
    else reportApiSuccess()
    return res
  } catch (err) {
    reportApiFailure() // timeout ou réseau : le serveur ne répond pas
    if (err.name === 'AbortError') throw erreurEcran(MSG_TIMEOUT)
    throw err
  } finally {
    clearTimeout(id)
  }
}

// ---------------------------------------------------------------------------
// Session : renouvellement partagé + sortie propre quand la session est morte (P3.5)
// ---------------------------------------------------------------------------

// Renouvellement du « pass court » (access token) partagé par TOUTE l'appli :
// apiFetch (réactif, sur 401) ET AuthContext (proactif, démarrage + toutes les 10 min).
// Single-flight : si un renouvellement est déjà en cours, tout le monde attend LA MÊME
// promesse — jamais deux POST /api/auth/refresh en parallèle. C'est vital car le backend
// RÉVOQUE l'ancien refresh token à chaque rotation (auth.py) : deux appels concurrents
// partiraient avec le même token et le second échouerait, éjectant le prof à tort.
// Résout true (renouvelé) / false (échec) ; ne rejette jamais. La promesse est relâchée
// dans `finally` (succès ET échec) pour ne jamais rester coincé sur un refresh raté.
let _refreshInFlight = null
export function refreshSession() {
  if (!_refreshInFlight) {
    _refreshInFlight = fetchWithTimeout(
      '/api/auth/refresh',
      { method: 'POST', credentials: 'include' },
      TIMEOUT_AUTH,
    )
      .then(r => r.ok)
      .catch(() => false)
      .finally(() => { _refreshInFlight = null })
  }
  return _refreshInFlight
}

// Sortie propre quand le « pass long » (refresh token) est mort : on ramène le prof à la
// connexion. Par défaut = redirection plein écran (reset complet de l'app). Surchargeable
// pour les tests via setSessionExpiredHandler.
let _onSessionExpired = () => {
  if (typeof window === 'undefined') return
  if (window.location.pathname.startsWith('/login')) return   // déjà sur la connexion → ne pas boucler
  window.location.replace('/login?raison=session_expiree')
}
export function setSessionExpiredHandler(fn) { _onSessionExpired = fn }

// Verrou : une seule redirection même si plusieurs appels tombent en 401 en même temps.
// En prod la redirection recharge la page → ce module est réinitialisé de toute façon.
let _redirecting = false

// Appel authentifié avec le BON réflexe sur 401 :
//  1) 401 → on tente UN renouvellement partagé (jamais de redirection prématurée) ;
//  2) renouvelé → on rejoue l'appel UNE fois (le prof ne voit rien) ;
//  3) renouvellement raté OU rejeu encore 401 = pass long mort → /login (une seule fois).
export async function apiFetch(url, options = {}, timeout = TIMEOUT_STD) {
  const opts = { credentials: 'include', ...options }
  let res = await fetchWithTimeout(url, opts, timeout)
  if (res.status !== 401) return res

  const renouvele = await refreshSession()
  if (renouvele) {
    res = await fetchWithTimeout(url, opts, timeout)
    if (res.status !== 401) return res
  }

  if (!_redirecting) {
    _redirecting = true
    _onSessionExpired()
  }
  return res
}

// Réinitialisation de l'état module — réservé aux tests.
export function _resetForTests() {
  _refreshInFlight = null
  _redirecting = false
}
