// LE CATALOGUE UNIQUE des explications de l'écran « Analyser une consigne » — même principe que
// aideAmbiguites.js : une explication vit à UNE seule place. Le « i » posé derrière un titre lit
// `court` au survol et `long` au clic ; la fenêtre « Comment ça marche » lit les MÊMES entrées.
// Personne ne réécrit ces textes ailleurs : une phrase corrigée ici l'est partout du même geste.
//
// L'ordre du tableau EST celui de la fenêtre « Comment ça marche » : il suit l'écran, de la zone
// de saisie au rapport.

export const GUIDE_CONSIGNE = [
  {
    cle: 'consigne',
    titre: 'Votre consigne',
    court: "Collez UNE consigne isolée — ou apportez-la par un des cinq boutons, aSchool peut même l'écrire pour vous.",
    long: "Une consigne = une instruction adressée à l'élève, pas un exercice entier ni une série de "
      + "questions. Par exemple : « Analysez le personnage en faisant référence au texte. »\n\n"
      + "Six façons de remplir la zone : au clavier, ou par les boutons en haut à droite — Fichier TXT, "
      + "Image/Scan (une photo de votre sujet papier), PDF, Dicter (vous parlez, aSchool écrit), et "
      + "« Propose-moi un exemple ».\n\n"
      + "Quand le texte ne vient pas du clavier, une ligne sous la zone rappelle d'où il vient.",
  },
  {
    cle: 'exemple',
    titre: '« Propose-moi un exemple »',
    court: "aSchool écrit sur-le-champ une consigne de votre matière, avec de vrais défauts dedans — de quoi voir ce que l'outil trouve.",
    long: "Ce bouton écrit une consigne de VOTRE matière et de VOTRE niveau, tirée du programme officiel, "
      + "dans laquelle des défauts ont été glissés volontairement. De quoi découvrir l'outil sans avoir "
      + "à chercher une consigne.\n\n"
      + "Il l'écrit à chaque clic : deux clics donnent deux consignes différentes. Rien n'est rangé "
      + "d'avance — un texte de démonstration n'a aucune raison d'être le même deux fois.\n\n"
      + "La consigne est ancrée sur le programme officiel de votre niveau : elle ne peut pas partir dans "
      + "une autre discipline ni dans un autre âge. Et si les extraits du programme ne suffisent pas à "
      + "savoir ce que votre matière recouvre, aSchool ne devine pas : il vous dit ce qui manque plutôt "
      + "que d'écrire une consigne plausible.",
  },
  {
    cle: 'axes',
    titre: 'Les cinq axes examinés',
    court: 'Les cinq axes sont examinés à chaque analyse. Ils ne se décochent pas.',
    long: "Contrairement aux types du détecteur d'ambiguïtés, les cinq axes ne sont pas des cases à "
      + "cocher : ils sont tous examinés, à chaque fois.\n\n"
      + "La raison est dans ce que rend l'outil. L'analyse ne se contente pas de lister des remarques : "
      + "elle réécrit votre consigne. Un axe mis de côté produirait une « consigne optimisée » qui "
      + "laisse passer un défaut connu, sans que rien ne vous le signale — les cinq axes sont les "
      + "dimensions d'un même diagnostic, pas un filtre à régler.\n\n"
      + "Un axe qui ne donne aucune carte dans le rapport, c'est qu'il n'y avait rien à signaler.",
  },
  {
    cle: 'analyser',
    titre: "Lancer l'analyse",
    court: "Le bouton reste gris tant qu'il manque quelque chose — sa bulle dit quoi.",
    long: "« Analyser la consigne », en haut à droite, reste gris tant que la zone est vide ou que son "
      + "contenu ne ressemble pas à une consigne. Survolez-le, sa bulle dit ce qui bloque.\n\n"
      + "La matière et le niveau, eux, ne se choisissent pas ici : ce sont ceux de votre profil (ou le "
      + "couple de travail que vous avez posé), affichés dans le bandeau du haut.\n\n"
      + "Rien n'est enregistré : cet outil rend un rapport, c'est tout.",
  },
  {
    cle: 'rapport',
    titre: "Le rapport d'analyse",
    court: "Il s'affiche dans la colonne de droite : un verdict, une carte par point à améliorer, puis la consigne réécrite.",
    long: "L'écran est en deux colonnes, comme l'écran Activité : votre consigne à gauche, le rapport à "
      + "droite. La poignée du milieu s'attrape pour élargir l'une ou l'autre, et la largeur choisie "
      + "revient à votre prochaine visite (double-clic pour rééquilibrer).\n\n"
      + "Le rapport donne un verdict global, puis une carte par point à améliorer : l'axe concerné, sa "
      + "gravité, l'extrait exact en cause, le problème et une suggestion concrète.\n\n"
      + "Il se termine par la CONSIGNE OPTIMISÉE : votre consigne entièrement réécrite, tous les "
      + "défauts corrigés, prête à copier dans votre exercice.\n\n"
      + "« Nouvelle consigne », sous le formulaire, repart de zéro.",
  },
  {
    cle: 'sortie',
    titre: 'Sortir le rapport, ou le mettre de côté',
    court: "« HTML » montre le rapport mis en forme, prêt à imprimer. « Cacher le rapport » rend toute la largeur à votre consigne.",
    long: "« HTML », en haut du rapport, ouvre l'aperçu mis en forme sans quitter aSchool : la page telle "
      + "qu'elle s'imprime, couleurs comprises — chaque axe garde sa teinte, la consigne réécrite son "
      + "cadre. Le bouton « Imprimer » de cette fenêtre envoie la version mise en forme, pas le texte "
      + "brut.\n\n"
      + "« Cacher le rapport » replie la colonne de droite : votre consigne prend toute la largeur, "
      + "pratique pour la retravailler avec les remarques en tête. Le bouton redevient « Afficher le "
      + "rapport », et lancer une nouvelle analyse rouvre la colonne de lui-même.\n\n"
      + "Ces deux boutons n'apparaissent qu'une fois le rapport là : avant, ils ne désigneraient rien.",
  },
]

// Renvoie les props { titre, court, long } à étaler dans <InfoGuide />. Clé inconnue → objet vide.
export function aideConsigne(cle) {
  const e = GUIDE_CONSIGNE.find(x => x.cle === cle) || {}
  return { titre: e.titre, court: e.court, long: e.long }
}
