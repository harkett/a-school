let _handler = null
let _feedbackOpener = null

export function registerErrorHandler(fn) {
  _handler = fn
}

// L'ouverture du feedback vit dans App (état showFeedback). ErrorDialog est monté ailleurs dans
// l'arbre : on passe par ce canal enregistré, comme registerErrorHandler, pour que « cliquez ici »
// ouvre le feedback existant depuis n'importe quelle modale d'erreur.
export function registerFeedbackOpener(fn) {
  _feedbackOpener = fn
}

export function openFeedbackFromError() {
  if (_feedbackOpener) _feedbackOpener()
}

// opts.feedback = true → la modale ajoute le lien « cliquez ici » qui ouvre le feedback.
export function showError(msg, opts = {}) {
  if (_handler) _handler(msg, opts)
}
