// Catalogue UNIQUE des ASTUCES, sur le modèle de `aideProfil.js` — une seule source, lue à la
// fois par le petit « a » posé sur l'écran concerné et par le Centre d'aide (partie « Astuces »).
//
// POURQUOI ELLES ONT DÉMÉNAGÉ (16/08/2026). Elles vivaient toutes dans une carte de l'Accueil,
// tirées au hasard une par une, avec un texte coupé net à la 4ᵉ ligne : celles qui n'avaient pas
// de « En savoir plus » ne pouvaient pas être lues jusqu'au bout, et aucune n'était près du geste
// qu'elle explique. Une astuce se lit là où elle sert — donc sur son écran, derrière un « a » qui
// se survole comme le « i » de l'aide — et se retrouve au Centre d'aide quand on la cherche.
//
//  - ecran : la page où le « a » se pose (`null` = Centre d'aide seulement) ;
//  - court : la phrase du survol ; long : la fiche complète, au clic.
export const ASTUCES = [
  {
    cle: 'traduction',
    ecran: 'accueil',
    titre: 'Ne laissez pas le navigateur traduire la page',
    court: "Si votre navigateur propose de traduire cette page, refusez : la traduction perturbe la génération.",
    long: "La traduction automatique modifie le texte source et les consignes — aSchool reçoit alors des mots "
      + "incorrects et génère des activités incohérentes ou vides. La page est entièrement en français : la "
      + "traduction n'apporte rien et perturbe tout.\n\n"
      + "Chrome : icône de traduction dans la barre d'adresse → les trois points → « Ne jamais traduire ce site ».\n"
      + "Edge : icône de traduction dans la barre d'adresse → « Ne jamais traduire ce site ».\n"
      + "Firefox : icône de traduction dans la barre d'adresse → « Ne jamais traduire ce site ».\n"
      + "Safari : menu Affichage → Traduction → « Ne jamais traduire ce site ».",
  },
  {
    cle: 'style',
    ecran: 'accueil',
    titre: 'aSchool apprend votre style',
    court: "Plus vous créez d'activités d'un même type, plus aSchool s'adapte à votre façon d'enseigner.",
    long: "Chaque activité que vous créez est enregistrée automatiquement — elle sert d'exemple à aSchool.\n\n"
      + "À partir de la 3e activité d'un même type et d'un même niveau, il s'en inspire pour adapter le ton, "
      + "la formulation des questions et le niveau de langue.\n\n"
      + "Cela fonctionne par type d'activité ET par classe : vos exemples de résumés n'influencent pas vos "
      + "analyses, et votre 6e n'influence pas votre 3e.",
  },
  {
    cle: 'niveau-defaut',
    ecran: 'profil',
    titre: 'Votre niveau par défaut est mémorisé',
    court: "Votre niveau par défaut est retenu d'une session à l'autre : rien à resélectionner en vous connectant.",
    long: "Le couple matière + niveau enregistré dans votre profil est celui que vous retrouvez à chaque "
      + "connexion. Vous pouvez le changer ponctuellement depuis la barre du haut, sans toucher à votre profil.",
  },
  {
    cle: 'profil-complet',
    ecran: 'profil',
    titre: 'Complétez votre profil',
    court: "Matière et niveau renseignés, aSchool se cale sur votre contexte dès la connexion.",
    long: "La matière et le niveau de votre profil déterminent le programme officiel affiché et calent toutes "
      + "les activités générées. Un profil complet, c'est une génération qui part déjà du bon référentiel.",
  },
  {
    cle: 'correction',
    ecran: 'activite',
    titre: "L'option « Avec correction »",
    court: "« Avec correction » génère automatiquement un corrigé complet sous l'activité.",
    long: "Cochez « Avec correction » avant de générer : le corrigé est produit dans la foulée, sous l'activité, "
      + "et enregistré avec elle. Vous le retrouvez tel quel en rouvrant l'activité depuis Mes contenus.",
  },
  {
    cle: 'melange',
    ecran: 'activite',
    titre: 'La précision « Mélange »',
    court: "« Mélange » demande à aSchool de combiner tous les types disponibles pour cette activité.",
    long: "La précision « Mélange » ne choisit pas un type : elle les combine tous. Le détail des types retenus "
      + "s'affiche sous le sélecteur, avant la génération.",
  },
  {
    cle: 'textes-libres',
    ecran: 'activite',
    titre: 'Où trouver un texte de départ',
    court: "Gallica (gallica.bnf.fr) et Wikisource pour retrouver un texte dont vous avez un souvenir vague.",
    long: "Pour un texte dont vous ne gardez qu'un souvenir vague, cherchez sur Gallica (gallica.bnf.fr) ou "
      + "Wikisource, puis copiez-collez le passage dans la zone de texte source. Les deux sites donnent des "
      + "œuvres libres de droits, utilisables en classe.",
  },
  {
    cle: 'rouvrir',
    ecran: 'contenus',
    titre: 'Tout se rouvre, rien ne se perd',
    court: "Vos créations sont enregistrées automatiquement : rouvrez-en une pour la reprendre telle quelle.",
    long: "Depuis Mes contenus, rouvrez n'importe quelle séquence, séance ou activité : tout est enregistré "
      + "automatiquement, vous la retrouvez telle quelle et pouvez changer son texte de départ pour la faire "
      + "évoluer sans repartir de zéro.",
  },
  {
    cle: 'cookies',
    ecran: null,
    titre: 'Problème de connexion qui persiste',
    court: "Connexion bloquée malgré un bon mot de passe ? Supprimez les cookies du site.",
    long: "Si la connexion échoue alors que vos identifiants sont bons, un ancien cookie de session traîne : "
      + "F12 → onglet Application → Cookies → tout supprimer, puis rechargez la page et reconnectez-vous.",
  },
]

// Toutes les astuces d'un écran, réunies derrière UN seul « a » (deux « a » côte à côte sur le
// même titre se liraient comme deux boutons différents). Renvoie `null` quand l'écran n'en a
// aucune — le composant n'est alors pas rendu du tout.
export function astucesEcran(ecran) {
  const lot = ASTUCES.filter(a => a.ecran === ecran)
  if (!lot.length) return null
  return {
    variante: 'astuce',
    titre: lot.length === 1 ? lot[0].titre : 'Astuces de cet écran',
    court: lot.length === 1 ? lot[0].court : `${lot.length} astuces pour cet écran.`,
    long: lot.map(a => `${a.titre}\n${a.long}`).join('\n\n'),
  }
}

// Accès direct par clé (get) — pour poser une astuce précise ailleurs qu'à l'échelle de l'écran.
export function astuce(cle) {
  const a = ASTUCES.find(e => e.cle === cle)
  return a ? { variante: 'astuce', titre: a.titre, court: a.court, long: a.long } : null
}
