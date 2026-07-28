// Catalogue UNIQUE des aides « i » de l'écran « Mes activités » (Historique). Même principe que
// utils/aideActivite.js : le petit « i » derrière un titre lit ces textes, jamais réécrits dans le JSX.
//  - court : bulle affichée au SURVOL du « i » (une phrase) ;
//  - long  : carte affichée au CLIC (l'aide complète, épinglée).
// Textes honnêtes (règle des deux publics) : on ne décrit que ce que l'écran fait vraiment.
export const GUIDE_HISTORIQUE = [
  {
    cle: 'ecran',
    titre: 'Mes activités',
    court: "Toutes vos activités générées et enregistrées.",
    long: "Cet écran réunit toutes les activités que vous avez générées et enregistrées. Retrouvez-les, ouvrez leur détail, reprenez-en une dans le formulaire pour la faire évoluer, ou partagez-la avec vos collègues. La liste est à gauche, le détail de l'activité choisie à droite.",
  },
  {
    cle: 'onglets',
    titre: 'Les deux onglets',
    court: "Niveau en cours = votre couple du moment ; Toutes = tout, regroupé par couple.",
    long: "« Niveau en cours » n'affiche que les activités de votre matière et de votre niveau actuels. « Toutes mes activités » affiche l'ensemble de vos activités, regroupées par matière-niveau, votre couple courant épinglé en haut.",
  },
  {
    cle: 'texte_source',
    titre: 'Texte source',
    court: "Le texte que vous aviez fourni pour générer cette activité.",
    long: "C'est la matière première de cette activité : le texte, le document ou la consigne que vous aviez fourni au moment de la générer. Il est conservé pour que vous sachiez toujours d'où vient l'activité.",
  },
  {
    cle: 'resultat',
    titre: 'Résultat généré',
    court: "L'activité produite par aSchool à partir de ce texte source.",
    long: "C'est l'activité produite par aSchool à partir du texte source. C'est ce que vous exportez (aperçu HTML, impression) ou que vous reprenez dans le formulaire pour la régénérer ou la faire évoluer.",
  },
  {
    cle: 'stats',
    titre: 'Sur la plateforme',
    court: "Ce que la communauté a produit pour votre couple.",
    long: "Un aperçu anonyme de l'activité de la communauté pour votre matière et votre niveau : nombre total d'activités créées, nombre de profs, et les types d'activités les plus utilisés.",
  },
]

// Renvoie les props { titre, court, long } à étaler dans <InfoGuide />. Clé inconnue → objet vide.
export function aideHistorique(cle) {
  const e = GUIDE_HISTORIQUE.find(x => x.cle === cle) || {}
  return { titre: e.titre, court: e.court, long: e.long }
}
