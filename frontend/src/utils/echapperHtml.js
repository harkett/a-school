// L'ÉCHAPPEUR HTML DE LA MAISON — une seule place, lue par tous les écrans qui composent une
// page à imprimer.
//
// POURQUOI IL EST ICI. Il était recopié à l'identique dans cinq fichiers : Ambiguites.jsx,
// Consigne.jsx, Equite.jsx, GrilleEcran.jsx et GuideDemos.jsx. Quatre copies étaient les mêmes ;
// la cinquième (GuideDemos) n'échappait PAS les guillemets — la divergence était déjà là, sans
// que personne l'ait décidée. C'est exactement ce qu'une copie finit toujours par produire.
//
// CE QU'IL FAIT, ET CE QU'IL N'EST PAS. Il neutralise les caractères qui feraient prendre du
// texte pour du balisage. Ce n'est PAS le filet de sécurité : le nettoyage de sortie (DOMPurify,
// dans apercuHtml.js) reste le dernier rempart. On échappe à l'écriture, on nettoie à la sortie,
// et on ne compte jamais sur l'un pour dispenser de l'autre.
export function ech(v) {
  return String(v ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}
