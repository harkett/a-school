// Santé serveur côté client (option 1) : on n'attend RIEN du serveur pour savoir
// qu'il va mal — c'est le navigateur du prof qui constate que les appels échouent.
// Comme la sonde CPU, on ne réagit pas à un blip : il faut SEUIL_PANNE échecs
// consécutifs (timeout, réseau, 5xx) pour basculer en « dégradé ». Le 1er succès
// remet le compteur à zéro et masque le bandeau (la reprise est une bonne nouvelle).

let _handler = null
let _consecutiveFailures = 0
let _degraded = false

export const SEUIL_PANNE = 3 // nb d'échecs consécutifs avant d'afficher le message

// Message affiché au prof dans la modale d'erreur bloquante quand le serveur ne répond plus.
export const MSG_SERVEUR_INDISPONIBLE =
  'aSchool est temporairement ralenti et certaines actions peuvent mettre du temps à répondre. ' +
  'Nous travaillons déjà à rétablir le service. Réessayez dans quelques minutes — ' +
  'vos activités enregistrées sont en sécurité.'

export function registerServerHealthHandler(fn) {
  _handler = fn
}

function _emit(degraded) {
  if (degraded === _degraded) return // pas de re-rendu inutile
  _degraded = degraded
  if (_handler) _handler(degraded)
}

export function reportApiFailure() {
  _consecutiveFailures++
  if (_consecutiveFailures >= SEUIL_PANNE) _emit(true)
}

export function reportApiSuccess() {
  _consecutiveFailures = 0
  _emit(false)
}

// Réinitialisation de l'état module — réservé aux tests.
export function _resetForTests() {
  _handler = null
  _consecutiveFailures = 0
  _degraded = false
}
