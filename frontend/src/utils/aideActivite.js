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
    long: "C'est la matière première de l'activité : le texte, le document ou la consigne à partir duquel aSchool génère. Vous pouvez le saisir, le coller, l'importer (fichier TXT, image, PDF), le dicter, ou laisser aSchool proposer un document d'exemple ou une idée. La pastille de l'étape passe au vert dès qu'il y a du texte.",
  },
  {
    cle: 'resultat',
    titre: 'Résultat généré',
    court: "L'activité produite par aSchool, prête à récupérer.",
    long: "C'est l'activité générée par aSchool à partir de vos réglages et de votre texte. Vous pouvez la télécharger (TXT, Word, PDF), l'imprimer ou l'envoyer par e-mail. Si elle ne vous convient pas : « Régénérer » en produit une autre version, « Changer votre demande » rouvre votre texte pour l'ajuster.",
  },
]

// Accès direct par clé (get) — utilisé par le « i » de chaque titre.
export function aideActivite(cle) {
  return GUIDE_ACTIVITE.find(e => e.cle === cle) || null
}
