// Catalogue UNIQUE des aides « i » de l'écran Créer une activité. Même
// principe que utils/aideProfil.js : le petit « i » derrière chaque titre lit ces textes, et la
// future fenêtre « Comment ça marche » lira EXACTEMENT les mêmes — une seule source, zéro doublon.
//  - court : bulle affichée au SURVOL du « i » (une phrase) ;
//  - long  : carte affichée au CLIC (l'aide complète, épinglée).
// Textes honnêtes (règle des deux publics) : on ne décrit que ce que l'écran fait vraiment.
export const GUIDE_ACTIVITE = [
  {
    cle: 'parametres',
    titre: "Paramètres de l'activité",
    court: "Choisissez le type d'activité et ses options.",
    long: "Première étape de la création. Vous choisissez le type d'activité, sa précision quand elle existe, et les options (nombre de questions, correction jointe). Ces réglages, avec votre texte source, décident de ce qu'aSchool produit. La pastille de l'étape passe au vert dès qu'un type est choisi.",
  },
  {
    cle: 'type',
    titre: "Type d'activité",
    court: "La nature de l'activité qu'aSchool va produire.",
    long: "C'est le premier choix de la création : il décide de la nature de l'activité qu'aSchool produit (dictée, exercice, questionnaire…). Quand le type choisi propose des variantes, le menu « Précision » apparaît juste en dessous. La pastille de l'étape passe au vert dès qu'un type est choisi.",
  },
  {
    cle: 'correction',
    titre: 'Inclure une proposition de correction',
    court: 'Une réponse-type est ajoutée après chaque question.',
    long: "Quand cette option est cochée, aSchool ajoute une réponse-type après chaque question. Vous la relisez et l'adaptez à votre classe avant de la donner aux élèves.",
  },
  {
    cle: 'precision',
    titre: 'Précision',
    court: "Affine le type d'activité choisi.",
    long: "La précision affine le type choisi (par exemple la forme de la dictée ou de l'exercice). L'option « Mélange » réunit plusieurs précisions en une seule activité ; la liste de ce qu'elle contient s'affiche alors sous le menu.",
  },
  {
    cle: 'texte_source',
    titre: 'Texte source',
    court: "Le contenu à partir duquel aSchool génère l'activité.",
    long: "C'est la matière première de l'activité : le texte, le document ou la consigne à partir duquel aSchool génère. Vous pouvez le saisir, le coller, l'importer (fichier TXT, image, PDF), le dicter, ou laisser aSchool proposer un document d'exemple ou une idée. Le document d'exemple et l'idée proposés s'appuient sur le référentiel officiel de votre niveau. La pastille de l'étape passe au vert dès qu'il y a du texte.",
    // Variante affichée quand ce prof a déposé un cahier des charges (choix fait PAR LE CODE selon la
    // base, pas une tournure « au cas où ») : la provenance mentionne alors le référentiel ET le
    // cahier des charges. Textes honnêtes (règle des deux publics).
    cahier: {
      court: "La matière première de l'activité — l'exemple et l'idée suivent le référentiel officiel et votre cahier des charges.",
      long: "C'est la matière première de l'activité : le texte, le document ou la consigne à partir duquel aSchool génère. Vous pouvez le saisir, le coller, l'importer (fichier TXT, image, PDF), le dicter, ou laisser aSchool proposer un document d'exemple ou une idée. Le document d'exemple et l'idée proposés s'appuient sur le référentiel officiel de votre niveau et sur le cahier des charges de votre établissement. La pastille de l'étape passe au vert dès qu'il y a du texte.",
    },
  },
  {
    cle: 'generer',
    titre: "Générer l'activité",
    court: "Deux tons au choix — le clic lance la génération dans ce ton.",
    long: "Deux boutons, deux tons : vous choisissez en cliquant, et le clic lance la génération. « Ton académique » = formel, phrases longues, style « documents officiels ». « Ton opérationnel » = clair, phrases courtes, consignes directes, style « prof en classe ». Cette activité tiendra compte du référentiel officiel de votre niveau. Le résultat s'affiche à droite ; vous pourrez ensuite basculer l'autre ton avec « Changer votre ton ». La pastille de l'étape passe au vert dès qu'une activité est produite.",
    // Variante affichée quand ce prof a déposé un cahier des charges (choix fait PAR LE CODE selon la
    // base) : la génération s'appuie alors AUSSI sur son cahier. Texte honnête (règle des deux publics).
    cahier: {
      court: "Deux tons au choix — référentiel officiel ET cahier des charges pris en compte.",
      long: "Deux boutons, deux tons : vous choisissez en cliquant, et le clic lance la génération. « Ton académique » = formel, phrases longues, style « documents officiels ». « Ton opérationnel » = clair, phrases courtes, consignes directes, style « prof en classe ». Cette activité tiendra compte du référentiel officiel de votre niveau et du cahier des charges de votre établissement. Le résultat s'affiche à droite ; vous pourrez ensuite basculer l'autre ton avec « Changer votre ton ». La pastille de l'étape passe au vert dès qu'une activité est produite.",
    },
  },
  {
    cle: 'resultat',
    titre: 'Résultat généré',
    court: "L'activité produite par aSchool, prête à récupérer.",
    long: "C'est l'activité générée par aSchool à partir de vos réglages et de votre texte, dans le ton choisi. Vous pouvez la télécharger (TXT, Word, PDF), en voir la mise en forme (aperçu HTML), l'imprimer ou l'envoyer par e-mail. Si elle ne vous convient pas : « Changer votre texte » rouvre votre texte pour l'ajuster, « Changer votre ton » la régénère dans l'autre ton (académique ↔ opérationnel).",
    // Variante affichée quand ce prof a déposé un cahier des charges : la génération s'appuie
    // alors sur le programme officiel ET sur son cahier. Texte honnête (règle des deux publics).
    cahier: {
      court: "L'activité produite par aSchool à partir du programme officiel et de votre cahier des charges.",
      long: "C'est l'activité générée par aSchool à partir de vos réglages et de votre texte, dans le ton choisi, en s'appuyant sur le programme officiel de votre niveau ET sur le cahier des charges de votre établissement (déposé dans votre profil). Vous pouvez la télécharger (TXT, Word, PDF), en voir la mise en forme (aperçu HTML), l'imprimer ou l'envoyer par e-mail. Si elle ne vous convient pas : « Changer votre texte » rouvre votre texte pour l'ajuster, « Changer votre ton » la régénère dans l'autre ton (académique ↔ opérationnel).",
    },
  },
  {
    cle: 'analyses',
    titre: 'Vérifier le résultat',
    court: "Contrôle l'activité générée et signale ce qui doit être corrigé.",
    long: "« Vérifier » relit l'activité générée et signale les points à corriger. Le rapport s'affiche en cartes : pour chaque point, l'extrait concerné et une suggestion. Pour l'instant il détecte les ambiguïtés ; d'autres contrôles (cohérence avec votre demande, conformité au type, correction…) s'ajouteront progressivement. L'amélioration du résultat, elle, arrivera dans une étape dédiée.",
  },
]

// Accès direct par clé (get) — utilisé par le « i » de chaque titre. `opts.cahier` (booléen lu de
// l'état du prof : a-t-il déposé un cahier des charges ?) sélectionne la variante « avec cahier »
// quand l'entrée en propose une ; sinon on renvoie les textes de base. Une seule source, deux voix.
export function aideActivite(cle, opts = {}) {
  const e = GUIDE_ACTIVITE.find(x => x.cle === cle) || null
  if (!e) return null
  if (opts.cahier && e.cahier) return { ...e, court: e.cahier.court, long: e.cahier.long }
  return e
}
