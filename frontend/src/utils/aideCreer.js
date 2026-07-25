// LE CATALOGUE UNIQUE des explications de l'écran Créer (décision du 25/07).
// Une explication = UNE place : la bulle de la visite guidée lit `phrase`, la fenêtre
// « Comment ça marche » lit `phrase`, la fiche du centre d'aide lit `phrase` + `detail`.
// Personne ne réécrit ces textes ailleurs — zéro copie, comme pour les données en base.
// `cible` = l'ancre data-guide posée sur le VRAI élément de l'écran : un élément qui
// bouge emmène sa bulle, un élément supprimé fait sauter son étape (jamais un texte
// qui décrit un écran disparu). L'ordre du tableau EST l'ordre de la visite guidée.

export const GUIDE_CREER = [
  {
    cle: 'couple',
    cible: 'couple',
    titre: 'Votre classe et votre matière',
    phrase: "Tout se génère pour CE couple, affiché ici. « Changer niveau et/ou matière » l'ajuste sans toucher votre profil, et il est retenu même si vous fermez l'application.",
    detail: [
      "Le bandeau bleu affiche la matière et le niveau sur lesquels vous travaillez — c'est LE seul endroit qui les montre, et c'est pour ce couple que toutes les activités se génèrent.",
      "« Changer niveau et/ou matière » (juste en dessous) vous fait travailler ponctuellement pour une autre classe de votre cycle ou une autre matière, sans modifier votre profil. Ce choix est enregistré : il tient d'une connexion à l'autre, jusqu'à ce que vous cliquiez « Revenir à mon profil ».",
    ],
  },
  {
    cle: 'type',
    cible: 'type',
    titre: "Le type d'activité",
    phrase: "Choisissez d'abord ce que vous voulez créer — la liste dépend de votre matière et de votre niveau.",
    detail: [
      "Questions de compréhension, analyse, résumé, production d'écrit… la liste est celle de VOTRE couple matière × niveau : chaque type produit un format différent.",
      "Selon le type choisi, l'écran s'adapte : un menu « Précision » peut apparaître pour affiner (par exemple inférence, lexique, mélange), et un champ « Nombre de questions » quand le type en a besoin.",
    ],
  },
  {
    cle: 'corrige',
    cible: 'corrige',
    titre: 'La proposition de correction',
    phrase: "Cochez pour recevoir le corrigé complet — il arrive à la fin du document, après toutes les questions.",
    detail: [
      "Case cochée, aSchool ajoute une réponse-type pour chaque question, regroupées à la fin du document généré. Vous les adaptez librement à votre classe.",
    ],
  },
  {
    cle: 'boutons',
    cible: 'boutons',
    titre: 'Les 6 façons de fournir votre demande',
    // Cette phrase s'affiche AUSSI en clair à côté du titre « Texte source » (TexteSource) —
    // la bulle, la fenêtre, la fiche d'aide et l'écran disent le même texte.
    phrase: "Apportez votre demande comme vous voulez : un fichier TXT, une image scannée, un PDF, un document d'exemple fabriqué par aSchool, la dictée au micro, ou une idée qu'aSchool rédige pour vous — tout arrive dans la zone de texte.",
    detail: [
      "Les 4 premiers boutons apportent un DOCUMENT : Fichier TXT, Image/Scan (photo convertie en texte), PDF, et « Document d'exemple » — un texte fabriqué par aSchool depuis le programme officiel de votre niveau, pour essayer sans rien avoir sous la main.",
      "Les 2 derniers formulent votre DEMANDE : « Dicter » transcrit votre voix, et « Propose-moi une idée » écrit pour vous une idée d'activité tirée de votre type d'activité et du programme — vous la retouchez librement.",
    ],
  },
  {
    cle: 'texte',
    cible: 'texte',
    titre: 'La zone de texte : la base de tout',
    phrase: "Décrivez votre demande ou collez votre document : ce texte guide la génération et la recherche dans le programme officiel. L'Objet donne son nom à l'activité.",
    detail: [
      "Tapé, dicté, scanné ou proposé par aSchool — c'est CE texte qui mène la génération et sert de requête au référentiel officiel. Plus il est précis, plus l'activité colle à votre intention.",
      "Le champ « Objet » nomme votre activité (il se remplit tout seul quand aSchool vous propose une idée) — c'est sous ce nom qu'elle apparaîtra dans « Mes activités ».",
    ],
  },
  {
    cle: 'generer',
    cible: 'generer',
    titre: 'Générer',
    phrase: "Quand le texte est prêt : Générer. aSchool lit le programme officiel de votre classe et rédige l'activité sous vos yeux.",
    detail: [
      "Au clic, aSchool lit le programme officiel de votre classe et rédige l'activité en direct. Une jauge accompagne l'attente ; si le corrigé est coché, il arrive en toute fin de document, après toutes les questions.",
    ],
  },
  {
    cle: 'resultat',
    cible: 'resultat',
    titre: 'Le résultat : déjà sauvegardé, à vous de jouer',
    phrase: "L'activité est déjà enregistrée toute seule dans « Mes activités ». Elle ne se retouche pas directement ici : pour une autre version, « Régénérer » ; pour corriger un mot vous-même, téléchargez-la en .txt ou Word. Vous pouvez aussi l'imprimer, l'envoyer par e-mail ou analyser ses ambiguïtés.",
    detail: [
      "Dès la fin de la génération, l'activité est enregistrée automatiquement dans « Mes activités » — rien à faire pour la garder, vous la rechargerez en un clic à tout moment.",
      "Au-dessus du résultat : Télécharger en fichier texte (.txt) ou en Word (.docx), Imprimer, Envoyer par e-mail à un collègue, Analyser les ambiguïtés cognitives de l'activité. « Régénérer » relance une nouvelle version — chaque génération est différente, et l'actuelle est alors remplacée (déjà sauvegardée, elle reste dans « Mes activités »).",
      "Le texte affiché ne s'édite pas directement sur cette page. Pour changer une question ou corriger une coquille, deux chemins : « Régénérer » pour une autre version, ou télécharger l'activité en .txt / Word et la retoucher dans votre traitement de texte habituel.",
    ],
  },
]
