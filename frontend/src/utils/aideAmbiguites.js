// LE CATALOGUE UNIQUE des explications de l'écran « Analyser un texte pour détecter les
// ambiguïtés » — même principe que aideCreer.js : une explication vit à UNE seule place.
// Le « i » posé derrière un titre lit `court` au survol et `long` au clic ; la fenêtre
// « Comment ça marche » lit les MÊMES entrées. Personne ne réécrit ces textes ailleurs :
// une phrase corrigée ici l'est partout du même geste.
//
// L'ordre du tableau EST celui de la fenêtre « Comment ça marche » : il suit l'écran, de la
// zone de saisie au rapport.

export const GUIDE_AMBIGUITES = [
  {
    cle: 'enonce',
    titre: 'Votre exercice ou énoncé',
    court: "Collez l'énoncé à relire — ou apportez-le par un des cinq boutons, aSchool peut même l'écrire pour vous.",
    long: "Un exercice, une série de questions ou une consigne isolée : c'est ce texte-là qui sera relu, et lui seul.\n\n"
      + "Six façons de remplir la zone : au clavier, ou par les boutons en haut à droite — Fichier TXT, "
      + "Image/Scan (une photo de votre sujet papier), PDF, Dicter (vous parlez, aSchool écrit), et "
      + "« Propose-moi un exemple ».\n\n"
      + "Quand le texte ne vient pas du clavier, une ligne sous la zone rappelle d'où il vient.",
  },
  {
    cle: 'exemple',
    titre: '« Propose-moi un exemple »',
    court: "aSchool écrit sur-le-champ un énoncé de votre matière, avec de vrais défauts dedans — de quoi voir ce que l'outil trouve.",
    long: "Ce bouton écrit un énoncé de VOTRE matière et de VOTRE niveau, tiré du programme officiel, dans "
      + "lequel des défauts ont été glissés volontairement. De quoi découvrir l'outil sans avoir à chercher "
      + "un sujet.\n\n"
      + "Il l'écrit à chaque clic : deux clics donnent deux énoncés différents. Rien n'est rangé d'avance — "
      + "un texte de démonstration n'a aucune raison d'être le même deux fois.\n\n"
      + "L'énoncé est ancré sur le programme officiel de votre niveau : il ne peut pas partir dans une autre "
      + "discipline ni dans un autre âge.",
  },
  {
    cle: 'criteres',
    titre: "Ce qu'aSchool doit chercher",
    court: "Cochez les types à faire relire : aSchool ne remonte QUE ceux-là. Rien n'est coché au départ.",
    long: "Les types d'ambiguïté sont des cases à cocher, et aucune n'est cochée au départ : c'est vous qui "
      + "dites ce que vous voulez faire relire. Survolez-en une pour lire ce qu'elle repère.\n\n"
      + "C'est ce qui distingue cet outil d'une relecture tous azimuts : aSchool ne remonte QUE les types "
      + "demandés — aucune remarque hors sujet à écarter — et il les traite un par un au lieu de s'arrêter "
      + "au premier défaut vu.\n\n"
      + "La liste elle-même n'est pas écrite dans l'écran : elle vient du catalogue de l'application, à la "
      + "même source que celle sur laquelle l'analyse travaille.",
  },
  {
    cle: 'autre',
    titre: '« Autre » — votre propre point de vigilance',
    court: "La dernière case ouvre un champ libre : écrivez en une ligne ce que vous voulez faire vérifier en plus.",
    long: "Par exemple : « vérifie le vocabulaire inclusif », « repère les références culturelles supposées "
      + "connues ». aSchool le traite comme un point de vigilance supplémentaire, jamais comme une consigne "
      + "qui remplacerait les autres.\n\n"
      + "Ce qu'il trouve à ce titre revient dans le rapport sous l'étiquette « Autre ».\n\n"
      + "Case cochée mais champ vide, le bouton « Analyser » reste gris : sa bulle dit lequel des trois "
      + "motifs bloque.",
  },
  {
    cle: 'analyser',
    titre: "Lancer l'analyse",
    court: "Le bouton reste gris tant qu'il manque quelque chose — sa bulle dit quoi.",
    long: "« Analyser l'énoncé », en haut à droite, reste gris tant qu'il manque une des trois conditions : "
      + "rien de coché, « Autre » coché sans texte, ou zone vide. Survolez-le, sa bulle dit laquelle.\n\n"
      + "La matière et le niveau, eux, ne se choisissent pas ici : ce sont ceux de votre profil (ou le couple "
      + "de travail que vous avez posé), affichés dans le bandeau du haut.\n\n"
      + "Rien n'est enregistré : cet outil rend un rapport, c'est tout.",
  },
  {
    cle: 'rapport',
    titre: "Le rapport d'analyse",
    court: "Il s'affiche dans la colonne de droite : un verdict, puis une carte par ambiguïté avec sa reformulation.",
    long: "L'écran est en deux colonnes, comme l'écran Activité : votre énoncé à gauche, le rapport à droite. "
      + "La poignée du milieu s'attrape pour élargir l'une ou l'autre, et la largeur choisie revient à votre "
      + "prochaine visite (double-clic pour rééquilibrer).\n\n"
      + "Le rapport donne un verdict global sur la clarté de l'énoncé, puis une carte par ambiguïté : "
      + "l'extrait exact en cause, son type, le risque concret pour l'élève, et une reformulation corrigée "
      + "prête à copier dans votre exercice.\n\n"
      + "Un type coché qui ne donne aucune carte, c'est qu'il n'y avait rien à signaler.\n\n"
      + "« Nouvel énoncé », sous le formulaire, repart de zéro.",
  },
  {
    cle: 'sortie',
    titre: 'Sortir le rapport, ou le mettre de côté',
    court: "« HTML » montre le rapport mis en forme, prêt à imprimer. « Cacher le rapport » rend toute la largeur à votre énoncé.",
    long: "« HTML », en haut du rapport, ouvre l'aperçu mis en forme sans quitter aSchool : la page telle "
      + "qu'elle s'imprime, couleurs comprises — chaque type garde sa teinte, la reformulation son cadre "
      + "vert. Le bouton « Imprimer » de cette fenêtre envoie la version mise en forme, pas le texte brut.\n\n"
      + "« Cacher le rapport » replie la colonne de droite : votre énoncé prend toute la largeur, pratique "
      + "pour retravailler le texte avec les remarques en tête. Le bouton redevient « Afficher le rapport », "
      + "et lancer une nouvelle analyse rouvre la colonne de lui-même.\n\n"
      + "Ces deux boutons n'apparaissent qu'une fois le rapport là : avant, ils ne désigneraient rien.",
  },
]

// Renvoie les props { titre, court, long } à étaler dans <InfoGuide />. Clé inconnue → objet vide.
export function aideAmbiguites(cle) {
  const e = GUIDE_AMBIGUITES.find(x => x.cle === cle) || {}
  return { titre: e.titre, court: e.court, long: e.long }
}
