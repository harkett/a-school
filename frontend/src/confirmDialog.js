// Canal UNIQUE des confirmations de l'app (même patron que errorDialog.js). Une action qui fait
// PERDRE quelque chose (remplacer une activité non exportée, effacer…) passe par showConfirm() :
// un vrai dialogue pro, pas le window.confirm du navigateur. Le composant ConfirmDialog (monté à
// la racine) écoute ce canal ; showConfirm peut donc être appelé depuis n'importe quel composant.
let _handler = null

export function registerConfirmHandler(fn) {
  _handler = fn
}

// showConfirm({ titre, message, confirmLabel, cancelLabel, onConfirm, onCancel, danger })
//  - titre        : titre en gras du dialogue.
//  - message      : corps (les \n sont respectés) — dis CE QUI change et CE QUI sera perdu.
//  - confirmLabel : libellé du bouton d'action (défaut « Continuer »).
//  - cancelLabel  : libellé du bouton d'annulation (défaut « Annuler »).
//  - onConfirm    : appelé UNIQUEMENT si le prof confirme.
//  - onCancel     : appelé si le prof renonce (bouton, Échap, clic dehors). Facultatif pour un
//                   appel classique ; INDISPENSABLE à `demanderConfirmation` ci-dessous.
//  - danger       : true → bouton d'action rouge (action franchement destructrice).
// Filet de sécurité : si le composant n'est pas encore monté, on retombe sur window.confirm pour
// ne jamais exécuter une action à perte sans demander.
export function showConfirm(opts = {}) {
  if (_handler) {
    _handler(opts)
  } else if (window.confirm(opts.message || 'Confirmer ?')) {
    opts.onConfirm && opts.onConfirm()
  } else {
    opts.onCancel && opts.onCancel()   // le repli doit répondre AUSSI quand on renonce
  }
}

// La même chose, en PROMESSE : `if (!await demanderConfirmation({…})) return`.
//
// Pourquoi cette variante existe. Les confirmations du navigateur (`window.confirm`) sont
// SYNCHRONES et rendent un booléen, donc tous les appels ont la forme « si le prof refuse, je
// m'arrête ici » — la suite de la fonction vient derrière. `showConfirm` est à rappel : pour le
// convertir tel quel, il faudrait déplacer tout ce qui suit dans `onConfirm`, à quinze endroits,
// dans des fonctions qui enchaînent parfois plusieurs appels réseau. C'est là qu'on fabrique des
// bugs. Avec cette variante, chaque site change d'UNE ligne et garde sa structure ; la seule
// contrainte est que la fonction appelante soit `async`.
//
// Le canal reste unique (elle passe par `showConfirm`, donc par le même dialogue et le même filet
// de sécurité) : ce n'est pas une seconde façon de demander, c'est la même, dite autrement.
export function demanderConfirmation(opts = {}) {
  return new Promise(resolve => {
    showConfirm({ ...opts, onConfirm: () => resolve(true), onCancel: () => resolve(false) })
  })
}
