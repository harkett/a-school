// LE CATALOGUE UNIQUE des explications de l'écran « Mes évals → Grilles » — même principe que
// aideEquite.js, aideAmbiguites.js et aideConsigne.js : une explication vit à UNE seule place.
// Le « i » posé derrière un titre lit `court` au survol et `long` au clic ; la fenêtre « Comment
// ça marche » lit les MÊMES entrées. Personne ne réécrit ces textes ailleurs.
//
// L'ordre du tableau EST celui de la fenêtre « Comment ça marche » : il suit l'écran, de la
// demande au tableau rempli.
//
// L'ENTRÉE `descripteur` EST LA PLUS IMPORTANTE DU FICHIER. Tout le reste de l'écran n'est que
// la charpente ; ce qu'un professeur écrit dans ses cases décide si sa grille sert à noter juste
// ou si elle se contente d'habiller une impression. La différence entre « Bon travail » et
// « Cite trois sources et les met en relation » n'est pas une question de style : la première ne
// se constate pas, donc ne se défend pas devant un élève ni devant un parent.

export const GUIDE_GRILLES = [
  {
    cle: 'demande',
    titre: 'Ce que vous voulez évaluer',
    court: "Dites-le dans vos mots — un exposé, un compte rendu, une production. aSchool écrit la grille dessus.",
    long: "Écrivez ce que vos élèves vont rendre et ce que vous voulez y regarder : « un exposé oral de "
      + "cinq minutes sur une œuvre », « un compte rendu d'expérience », « une production écrite "
      + "argumentée ».\n\n"
      + "Plus vous êtes précis sur la TÂCHE, plus les critères tombent juste. Inutile en revanche de "
      + "lister les critères vous-même : c'est le travail que vous confiez à aSchool.\n\n"
      + "Votre demande est conservée avec la grille. L'année suivante, vous la relisez avant de "
      + "regénérer, ou vous la modifiez d'une ligne.",
  },
  {
    cle: 'idee',
    titre: '« Propose-moi une idée »',
    court: "Vous ne savez pas quoi évaluer ? Donnez un thème en deux mots, aSchool écrit la demande à votre place.",
    long: "Le bouton ouvre une fenêtre où vous indiquez seulement le thème ou le support que vous avez "
      + "en tête : « les réseaux », « la Révolution française », « le rapport de stage ».\n\n"
      + "aSchool cherche ce thème dans le programme officiel de votre niveau et vous rend UNE idée de "
      + "production à évaluer, écrite comme vous l'auriez écrite — deux ou trois phrases, pas une "
      + "grille. Elle s'affiche dans la zone : vous la relisez, vous la modifiez, puis vous générez.\n\n"
      + "Si le programme officiel ne dit rien sur ce thème, aSchool vous le dit et n'écrit rien. La "
      + "fenêtre reste ouverte : vous reformulez sur place, autant de fois qu'il le faut.",
  },
  {
    cle: 'referentiel',
    titre: "L'ancrage sur le programme",
    court: "La grille s'appuie sur le référentiel officiel de votre matière et de votre niveau, jamais sur une intuition.",
    long: "aSchool cherche dans le référentiel officiel de votre couple matière × niveau les passages qui "
      + "correspondent à votre demande, et les donne au modèle avant qu'il écrive.\n\n"
      + "C'est ce qui empêche une grille de 4e d'être écrite avec le vocabulaire du lycée, ou une grille "
      + "de spécialité de partir dans une discipline voisine.\n\n"
      + "Si rien d'assez proche n'est trouvé dans le programme, aSchool vous le dit et n'écrit rien — "
      + "plutôt qu'une grille plausible qui ne viendrait de nulle part.",
  },
  {
    cle: 'criteres',
    titre: 'Les critères (les lignes)',
    court: "Ce que l'élève doit démontrer. Quatre à six : au-delà, plus personne ne coche.",
    long: "Un critère dit ce que vous regardez, en une phrase : « Structure son propos », « Appuie ses "
      + "affirmations sur le texte ».\n\n"
      + "Quatre à six suffisent, et c'est une limite pratique plus qu'une règle : une grille de douze "
      + "lignes ne se remplit pas en classe, elle se remplit une fois puis elle est abandonnée.\n\n"
      + "Le POIDS dit l'importance relative d'un critère dans la note. Laissé à 1, tous comptent pareil ; "
      + "mis à 2, ce critère pèse deux fois plus que ses voisins.",
  },
  {
    cle: 'niveaux',
    titre: 'Les niveaux de maîtrise (les colonnes)',
    court: "La même échelle pour tous vos critères — c'est ce qui fait qu'une grille se lit d'un coup d'œil.",
    long: "L'échelle proposée par défaut est celle du socle : Maîtrise insuffisante, fragile, satisfaisante, "
      + "Très bonne maîtrise. Vous pouvez la renommer, en retirer une colonne ou en ajouter une.\n\n"
      + "Elle est LA MÊME pour toutes les lignes, et ce n'est pas une limitation : si chaque critère avait "
      + "sa propre échelle, le tableau cesserait d'être un tableau — plus rien ne s'alignerait, ni à "
      + "l'écran ni sur la feuille que vous donnez à l'élève.\n\n"
      + "Les POINTS de chaque colonne se multiplient au poids du critère. Une colonne à 3 points sur un "
      + "critère de poids 2 vaut donc 6.",
  },
  {
    cle: 'descripteur',
    titre: 'Les descripteurs (les cases)',
    court: "Ce que l'élève doit AVOIR FAIT pour obtenir ce niveau sur ce critère. C'est le cœur de la grille.",
    long: "Une case ne contient pas un jugement, elle contient un CONSTAT : ce que vous devez pouvoir "
      + "observer dans le travail rendu.\n\n"
      + "« Bon travail de recherche » ne se constate pas — deux correcteurs ne mettront pas la même chose. "
      + "« Cite trois sources et les met en relation » se constate : la case est cochée ou elle ne l'est "
      + "pas, et vous pouvez le montrer à l'élève.\n\n"
      + "D'une colonne à l'autre, c'est le DEGRÉ qui change, jamais le sujet : les quatre cases d'une même "
      + "ligne parlent toutes de la même chose, à des niveaux différents.\n\n"
      + "Vous modifiez une case en cliquant dedans. Une case vidée redevient vide, sans laisser de trace.",
  },
  {
    cle: 'enregistrement',
    titre: 'Rien à enregistrer',
    court: "Chaque modification est écrite tout de suite. Il n'y a pas de bouton « Enregistrer », et ce n'est pas un oubli.",
    long: "Ajouter un critère, renommer une colonne, écrire une case : chaque geste part vers aSchool au "
      + "moment où vous le faites.\n\n"
      + "Vous pouvez donc fermer l'onglet, changer d'écran ou perdre votre connexion sans rien perdre de "
      + "ce qui était déjà à l'écran.\n\n"
      + "C'est la règle de toute l'application : votre travail n'attend jamais qu'on pense à le sauver.",
  },
  {
    cle: 'dupliquer',
    titre: 'Dupliquer une grille',
    court: "La même grille pour une autre classe — la copie est complète et indépendante.",
    long: "« Dupliquer » crée une seconde grille avec les mêmes critères, la même échelle et les mêmes "
      + "cases.\n\n"
      + "Les deux vivent ensuite leur vie : retoucher la copie ne touche pas l'originale, et "
      + "inversement. C'est ce qu'on attend quand on adapte une grille à une autre classe sans vouloir "
      + "abîmer celle qui marche.",
  },
]

// Renvoie les props { titre, court, long } à étaler dans <InfoGuide />. Clé inconnue → objet vide.
export function aideGrilles(cle) {
  const e = GUIDE_GRILLES.find(x => x.cle === cle) || {}
  return { titre: e.titre, court: e.court, long: e.long }
}
