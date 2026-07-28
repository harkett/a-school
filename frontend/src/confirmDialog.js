// Canal UNIQUE des confirmations de l'app (même patron que errorDialog.js). Une action qui fait
// PERDRE quelque chose (remplacer une activité non exportée, effacer…) passe par showConfirm() :
// un vrai dialogue pro, pas le window.confirm du navigateur. Le composant ConfirmDialog (monté à
// la racine) écoute ce canal ; showConfirm peut donc être appelé depuis n'importe quel composant.
let _handler = null

export function registerConfirmHandler(fn) {
  _handler = fn
}

// showConfirm({ titre, message, confirmLabel, cancelLabel, onConfirm, danger })
//  - titre        : titre en gras du dialogue.
//  - message      : corps (les \n sont respectés) — dis CE QUI change et CE QUI sera perdu.
//  - confirmLabel : libellé du bouton d'action (défaut « Continuer »).
//  - cancelLabel  : libellé du bouton d'annulation (défaut « Annuler »).
//  - onConfirm    : appelé UNIQUEMENT si le prof confirme.
//  - danger       : true → bouton d'action rouge (action franchement destructrice).
// Filet de sécurité : si le composant n'est pas encore monté, on retombe sur window.confirm pour
// ne jamais exécuter une action à perte sans demander.
export function showConfirm(opts = {}) {
  if (_handler) _handler(opts)
  else if (window.confirm(opts.message || 'Confirmer ?')) opts.onConfirm && opts.onConfirm()
}
