// LE CATALOGUE UNIQUE des explications de l'écran « Équité d'une évaluation » — même principe
// que aideAmbiguites.js et aideConsigne.js : une explication vit à UNE seule place. Le « i »
// posé derrière un titre lit `court` au survol et `long` au clic ; la fenêtre « Comment ça
// marche » lit les MÊMES entrées. Personne ne réécrit ces textes ailleurs.
//
// L'ordre du tableau EST celui de la fenêtre « Comment ça marche » : il suit l'écran, de la
// zone de saisie au rapport.
//
// L'ENTRÉE `correcteur` EST LA PLUS IMPORTANTE DU FICHIER. Un professeur qui connaît l'effet de
// halo, l'écart entre deux correcteurs ou la dérive de sévérité viendra les chercher ici : ce
// sont les biais les mieux connus de l'évaluation. L'outil ne les traite pas — il ne PEUT pas,
// un énoncé seul ne les montre pas — et un silence sur ce point se lirait comme un oubli.
// L'aide le dit, explique pourquoi, et dit ce qui les corrige réellement.

export const GUIDE_EQUITE = [
  {
    cle: 'evaluation',
    titre: 'Votre évaluation',
    court: "Collez le sujet à relire — ou apportez-le par un des cinq boutons, aSchool peut même l'écrire pour vous.",
    long: "Un devoir, un contrôle, une série d'exercices : c'est ce texte-là qui sera relu, et lui seul.\n\n"
      + "Six façons de remplir la zone : au clavier, ou par les boutons en haut à droite — Fichier TXT, "
      + "Image/Scan (une photo de votre sujet papier), PDF, Dicter (vous parlez, aSchool écrit), et "
      + "« Propose-moi un exemple ».\n\n"
      + "Quand le texte ne vient pas du clavier, une ligne sous la zone rappelle d'où il vient.",
  },
  {
    cle: 'bareme',
    titre: 'Votre barème (facultatif)',
    court: "Collez-le si vous en avez un : trois des neuf biais ne se voient que là. Sans lui, l'analyse tourne quand même.",
    long: "Le barème est facultatif, mais il change ce que l'analyse peut voir. Trois biais s'y cachent et "
      + "nulle part ailleurs : un barème qui ne suit pas ce que l'énoncé demande, une même erreur qui coûte "
      + "des points deux fois, et une question dont l'échec bloque toutes les suivantes.\n\n"
      + "Collez-le tel qu'il est — points par question, critères, ou les deux.\n\n"
      + "Sans barème, aSchool ne suppose aucune répartition de points : il vous le dit une fois et travaille "
      + "sur le reste. Il ne notera jamais un barème qu'il aurait imaginé à votre place.",
  },
  {
    cle: 'exemple',
    titre: '« Propose-moi un exemple »',
    court: "aSchool écrit sur-le-champ une évaluation de votre matière, avec de vrais défauts d'équité dedans.",
    long: "Ce bouton écrit une évaluation de VOTRE matière et de VOTRE niveau, tirée du programme officiel, "
      + "dans laquelle des défauts d'équité ont été glissés volontairement. De quoi découvrir l'outil sans "
      + "avoir à chercher un sujet.\n\n"
      + "Il l'écrit à chaque clic : deux clics donnent deux évaluations différentes. Rien n'est rangé "
      + "d'avance — un texte de démonstration n'a aucune raison d'être le même deux fois.\n\n"
      + "L'évaluation est ancrée sur le programme officiel de votre niveau : elle ne peut pas partir dans "
      + "une autre discipline ni dans un autre âge.",
  },
  {
    cle: 'criteres',
    titre: "Ce qu'aSchool doit chercher",
    court: "Cochez les biais à faire chercher : aSchool ne remonte QUE ceux-là. Rien n'est coché au départ.",
    long: "Les neuf biais sont des cases à cocher, et aucune n'est cochée au départ : c'est vous qui dites ce "
      + "que vous voulez faire relire. Survolez-en une pour lire ce qu'elle repère.\n\n"
      + "Ils ont tous la même forme : l'évaluation demande quelque chose EN PLUS de ce qu'elle veut mesurer, "
      + "et ce quelque chose n'est pas également disponible à tous vos élèves. Un savoir qui n'a pas été "
      + "enseigné, une expérience de vie que tous n'ont pas, un ordinateur à la maison, une longueur de "
      + "lecture qui prend le pas sur la matière.\n\n"
      + "aSchool ne remonte QUE les biais demandés, et il les traite un par un au lieu de s'arrêter au "
      + "premier vu. La liste vient du catalogue de l'application, à la même source que celle sur laquelle "
      + "l'analyse travaille.",
  },
  {
    cle: 'correcteur',
    titre: "Et l'effet de halo ? Les écarts entre correcteurs ?",
    court: "Ce sont des biais du CORRECTEUR : ils ne se voient pas dans un sujet. aSchool ne les cherche pas, et vous dit pourquoi.",
    long: "Les biais les mieux établis de l'évaluation scolaire ne sont pas dans le sujet, ils sont dans la "
      + "correction. La recherche française en décrit plusieurs, tous solidement documentés :\n\n"
      + "• L'EFFET DE HALO — ce que vous savez déjà de l'élève (son niveau habituel, son comportement, son "
      + "écriture) colore la note que vous mettez à cette copie-ci.\n"
      + "• L'ÉCART ENTRE CORRECTEURS — la même copie, notée par deux professeurs, obtient deux notes "
      + "différentes.\n"
      + "• LA DÉRIVE DE SÉVÉRITÉ — on ne corrige pas la trentième copie comme la première.\n"
      + "• L'EFFET DE CONTRASTE — une copie moyenne paraît bonne après une mauvaise, faible après une "
      + "excellente.\n\n"
      + "AUCUN ne se voit dans un sujet collé : ils demandent plusieurs copies, plusieurs correcteurs, ou "
      + "du temps. aSchool ne les cherche donc pas, et ne prétendra jamais les avoir trouvés — un outil qui "
      + "les annoncerait à partir d'un énoncé seul inventerait.\n\n"
      + "Ce qui les réduit vraiment est connu, et ne demande pas d'outil : corriger sans voir le nom de "
      + "l'élève, mélanger les copies avant de commencer, corriger exercice par exercice plutôt que copie "
      + "par copie, et surtout écrire des critères précis AVANT de corriger — c'est la recommandation "
      + "constante des travaux sur le sujet, et le seul de ces gestes qui protège aussi vos élèves de la "
      + "comparaison entre eux.",
  },
  {
    cle: 'rapport',
    titre: 'Le rapport',
    court: "Une carte par biais trouvé : le passage en cause, qui est pénalisé, et ce qu'il faut changer.",
    long: "Chaque carte porte le nom du biais, le passage exact de votre sujet qui le déclenche, quels élèves "
      + "il pénalise, et une correction concrète.\n\n"
      + "Certains biais ne citent aucun passage : un temps trop court ou un barème absent portent sur "
      + "l'ensemble de l'évaluation, pas sur une phrase. La carte s'affiche alors sans citation.\n\n"
      + "Les corrections proposées retirent l'obstacle SANS baisser l'exigence : il ne s'agit jamais de "
      + "simplifier la tâche, mais d'enlever ce qui pénalise certains élèves pour une raison étrangère à ce "
      + "que vous évaluez. Une évaluation difficile n'est pas une évaluation injuste.\n\n"
      + "Aucun biais trouvé ne veut pas dire « évaluation parfaite » : cela veut dire que sur les biais "
      + "cochés, rien n'a été repéré.",
  },
  {
    cle: 'sortie',
    titre: 'Sortir le rapport, ou le mettre de côté',
    court: "« HTML » montre le rapport mis en forme, prêt à imprimer. « Cacher le rapport » rend toute la largeur à votre sujet.",
    long: "« HTML », en haut du rapport, ouvre l'aperçu mis en forme sans quitter aSchool : la page telle "
      + "qu'elle s'imprime, couleurs comprises — chaque biais garde sa teinte, la correction son cadre vert. "
      + "Le bouton « Imprimer » de cette fenêtre envoie la version mise en forme, pas le texte brut.\n\n"
      + "« Cacher le rapport » replie la colonne de droite : votre évaluation prend toute la largeur, "
      + "pratique pour la retravailler avec les remarques en tête. Le bouton redevient « Afficher le "
      + "rapport », et lancer une nouvelle analyse rouvre la colonne de lui-même.\n\n"
      + "Ces deux boutons n'apparaissent qu'une fois le rapport là : avant, ils ne désigneraient rien.",
  },
]

// Renvoie les props { titre, court, long } à étaler dans <InfoGuide />. Clé inconnue → objet vide.
export function aideEquite(cle) {
  const e = GUIDE_EQUITE.find(x => x.cle === cle) || {}
  return { titre: e.titre, court: e.court, long: e.long }
}
