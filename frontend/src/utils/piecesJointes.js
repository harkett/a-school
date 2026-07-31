// Fonctions PURES autour des pièces jointes d'un retour.
// Testées avec :  node --test src/utils/piecesJointes.test.js   (depuis frontend/)
//
// Séparées du crochet useLimitesPiecesJointes (qui, lui, parle au serveur et à React) pour
// pouvoir être prouvées — même découpage que utils/profil.js face à utils/useMatieres.js.

// « PNG, JPEG, PDF ou TXT » — la phrase construite depuis les formats que le SERVEUR déclare
// accepter, jamais réécrite à la main dans un libellé d'écran. Rien de chargé → chaîne vide :
// l'appelant n'annonce alors rien du tout, plutôt qu'une liste devinée.
export function listeFormats(limites, liaison = 'ou') {
  const f = limites?.formats_lisibles || []
  if (f.length === 0) return ''
  if (f.length === 1) return f[0]
  return `${f.slice(0, -1).join(', ')} ${liaison} ${f[f.length - 1]}`
}
