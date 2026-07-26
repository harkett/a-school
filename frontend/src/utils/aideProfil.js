// Catalogue UNIQUE des aides de la page profil. Le petit « i » derrière chaque titre lit ces
// textes, et la future fenêtre « Comment ça marche » lira EXACTEMENT les mêmes : une seule source,
// zéro doublon (si un jour on change une phrase, elle change partout).
//  - court : bulle affichée au SURVOL du « i » (une phrase) ;
//  - long  : carte affichée au CLIC (l'aide complète, épinglée).
// Textes honnêtes (règle des deux publics), en langage prof (« aSchool », jamais « IA »). Le cahier
// des charges est décrit comme alimentant la génération (décision produit : on le considère branché).
export const GUIDE_PROFIL = [
  {
    cle: 'profil',
    titre: 'Mon profil',
    court: 'Vos infos, votre niveau et votre matière.',
    long: "Renseignez votre identité, votre niveau et votre matière. Ce couple niveau + matière est la clé de l'application : il détermine le programme officiel affiché et cale toutes les activités que vous générez. « Valider » enregistre, « Annuler » revient sans rien changer.",
  },
  {
    cle: 'programme',
    titre: 'Programme officiel de votre niveau',
    court: "Le référentiel national de votre niveau, déposé par l'administration.",
    long: "C'est le programme officiel (national) de votre niveau, déposé par l'administration — vous ne le modifiez pas. Cliquez « Ouvrir le PDF d'origine » pour le consulter tel quel dans un nouvel onglet.",
  },
  {
    cle: 'cahier',
    titre: 'Mon cahier des charges',
    court: "Le document interne de votre école — aSchool s'en sert pour adapter vos activités à ses attentes.",
    long: "Déposez ici le cahier des charges de votre établissement : ses attentes, sa pédagogie, ses formats, ses exigences maison.\n\nIl complète le programme officiel : le programme dit ce qu'il faut enseigner, votre cahier des charges dit comment votre école veut qu'on l'enseigne.\n\nQuand vous créez une activité, aSchool s'appuie donc sur le programme officiel et sur votre cahier des charges — vos activités arrivent déjà calées sur le référentiel officiel et sur les règles de votre établissement.",
  },
]

// Accès direct par clé (get) — utilisé par le « i » de chaque titre.
export function aideProfil(cle) {
  return GUIDE_PROFIL.find(e => e.cle === cle) || null
}
