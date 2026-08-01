// Catalogue UNIQUE des aides « i » de la page « Mes contenus → Séances ». Même principe que
// utils/aideHistorique.js : le petit « i » derrière un titre lit ces textes, jamais réécrits dans le JSX.
//  - court : bulle affichée au SURVOL du « i » (une phrase) ;
//  - long  : carte affichée au CLIC (l'aide complète, épinglée).
// Textes honnêtes (règle des deux publics) : on ne décrit que ce que l'écran fait vraiment.
const GUIDE_SEANCES = [
  {
    cle: 'ecran',
    titre: 'Mes séances',
    court: "Toutes vos séances générées et enregistrées.",
    long: "Cette page réunit toutes les séances que vous avez générées et enregistrées. Retrouvez-les, ouvrez leur détail, ou reprenez-en une dans le formulaire pour la faire évoluer. La liste est à gauche, le détail de la séance choisie à droite.\n\nSUPPRIMER : la corbeille, à droite de chaque ligne, retire définitivement la séance et son historique de versions — mais JAMAIS ses activités. Celles-ci restent dans vos contenus : elles repassent simplement en « non rangées », comme si vous les aviez détachées. La fenêtre de confirmation vous dit ce qui part et ce qui reste, avec les nombres exacts.",
  },
  {
    cle: 'onglets',
    titre: 'Les deux onglets',
    court: "Niveau en cours = votre couple du moment ; Toutes = tout, regroupé par couple.",
    long: "« Niveau en cours » n'affiche que les séances de votre matière et de votre niveau actuels. « Toutes mes séances » affiche l'ensemble de vos séances, regroupées par matière-niveau, votre couple courant épinglé en haut.",
  },
  {
    cle: 'contexte',
    titre: 'Contexte',
    court: "Le contexte que vous aviez fourni pour générer cette séance.",
    long: "C'est le contexte rapide que vous aviez donné au moment de générer la séance (état de la classe, séance précédente…). Il est conservé pour que vous sachiez toujours dans quelles conditions cette séance a été pensée.",
  },
  {
    cle: 'resultat',
    titre: 'Déroulé généré',
    court: "Le déroulé de séance produit par aSchool.",
    long: "C'est le déroulé produit par aSchool à partir de votre thème, du cadre et de vos choix. C'est ce que vous consultez ici (aperçu HTML, impression) ou que vous reprenez dans le formulaire pour le régénérer ou le faire évoluer.",
  },
  {
    cle: 'historique',
    titre: 'Historique des versions',
    court: 'Toutes les versions précédentes, relisibles et restaurables.',
    long: "Chaque génération fige une version de votre séance : l'historique s'empile, rien n'est jamais écrasé. Vous ouvrez une version pour relire son déroulé en entier, et « Revenir à cette version » la remet en place. Ce retour ne supprime rien non plus : la version que vous quittez reste dans la liste, vous pouvez donc revenir en arrière d'un retour en arrière.",
  },
  {
    cle: 'activites',
    titre: 'Activités de cette séance',
    court: "Les activités rattachées à la séance sélectionnée.",
    long: "Une séance peut porter des activités : créées depuis l'écran Séance (« Créer une activité ici ») ou rattachées ensuite (« Ajouter une activité existante »). « Ouvrir » recharge l'activité dans son écran. Pour rattacher ou détacher, reprenez la séance : tout se gère dans son écran. Détacher ne supprime jamais l'activité — elle reste dans vos contenus.",
  },
]

// Renvoie les props { titre, court, long } à étaler dans <InfoGuide />. Clé inconnue → objet vide.
export function aideSeances(cle) {
  const e = GUIDE_SEANCES.find(x => x.cle === cle) || {}
  return { titre: e.titre, court: e.court, long: e.long }
}
