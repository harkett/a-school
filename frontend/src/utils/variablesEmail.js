// Les variables qu'un modèle d'e-mail peut contenir — UNE seule liste, partagée par les écrans
// qui rédigent un message (Email, Profs, Mail groupé). Elle était recopiée dans chacun d'eux :
// en ajouter une demandait de penser à trois fichiers, et un oubli se voyait à l'écran.
//
// Le remplacement réel, lui, est fait par le SERVEUR à l'envoi (backend/auth.py) : cette liste
// ne sert qu'à le dire au rédacteur, et à fabriquer l'aperçu.
export const VARIABLES_EMAIL = ['{prenom}', '{email}']

// Aperçu : mêmes remplacements que le serveur, sur TOUTES les occurrences. La version
// précédente utilisait replace() avec une chaîne, qui n'en remplace qu'UNE — un modèle citant
// deux fois {prenom} s'affichait « Marie … {prenom} » alors qu'il partait correctement rempli.
const EXEMPLES = { '{prenom}': 'Marie', '{email}': 'marie@college.fr' }

export function apercuVariables(texte) {
  return VARIABLES_EMAIL.reduce(
    (sortie, variable) => sortie.replaceAll(variable, EXEMPLES[variable]),
    texte || '',
  )
}
