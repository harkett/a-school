export const TIMEOUT_AUTH = 8_000   // auth, heartbeat, logout
export const TIMEOUT_STD  = 10_000  // appels standard (profil, activités, admin)
export const TIMEOUT_LONG = 45_000  // opérations longues : génération IA, OCR, mail groupé, purge BDD

export const MSG_TIMEOUT = 'Connexion lente ou indisponible. Vérifiez votre réseau et réessayez.'

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
    if (err.name === 'AbortError') throw new Error(MSG_TIMEOUT)
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
