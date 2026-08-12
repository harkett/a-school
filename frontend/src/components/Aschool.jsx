// LE NOM DE LA MARQUE, écrit une fois pour toute l'application : `aSchool`, en gras.
//
// LA CASSE SE PERD TOUTE SEULE, et c'est la raison d'être de ce composant. Les libellés de section
// portent `text-transform: uppercase`, qui transforme « Ce qu'aSchool doit chercher » en
// « CE QU'ASCHOOL DOIT CHERCHER » : la marque y perd sa forme sans que personne n'ait mal écrit
// quoi que ce soit. Le `textTransform: 'none'` posé ici la protège, où qu'on la place.
//
// PAS DE COULEUR SUR LE `a` : essayée le 12/08/2026 (bordeaux, puis bordeaux foncé), écartée — un
// caractère teinté au milieu d'un mot se lit comme une coquille, pas comme une identité.
//
// Là où le nom ne peut être qu'une CHAÎNE — bulle au survol (`title`), texte de remplacement d'une
// zone de saisie, message d'erreur, prompt envoyé au modèle — ce composant ne s'emploie pas : on y
// écrit `aSchool` à la main, et seule la casse est en jeu.
export default function Aschool() {
  return <span style={{ textTransform: 'none', fontWeight: 700 }}>aSchool</span>
}
