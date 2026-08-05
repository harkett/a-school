// Catalogue UNIQUE des aides « i » de l'écran admin Référentiels. Même principe que
// utils/aideActivite.js : le petit « i » lit ces textes, et rien n'est réécrit dans l'écran.
//  - court : bulle affichée au SURVOL du « i » (une phrase) ;
//  - long  : carte affichée au CLIC (l'aide complète, épinglée).
// Textes honnêtes : on ne décrit que ce que le bouton fait vraiment.
const GUIDE_REFERENTIELS = [
  {
    cle: 'valider_document',
    titre: 'Valider le référentiel',
    court: 'Range le document, lit son texte, écrit sa fiche en base. Aucune IA.',
    long: "Trois tâches, affichées une par une pendant qu'elles se font — aucune IA n'est appelée.\n\n"
      + "1. Rangement du document — le PDF quitte la zone d'attente pour le dossier du cycle et du "
      + "niveau, sous le nom referentiel.pdf, avec une copie sous son nom d'origine à côté.\n\n"
      + "2. Lecture du document — ses pages sont comptées, son texte est extrait puis nettoyé "
      + "(numéros de page, texte des marges) et figé : c'est lui que liront toutes les étapes suivantes.\n\n"
      + "3. Enregistrement en base — la fiche du référentiel est écrite pour ce couple : le vrai nom "
      + "du document et sa provenance (dépôt ou lien). Si ce couple avait déjà une fiche, elle est "
      + "mise à jour : l'ancien prompt de découpe et les morceaux découpés sont effacés, les matières "
      + "seulement proposées disparaissent, celles que vous aviez retenues restent.",
  },

  // ── Les explications des cartouches. Elles occupaient l'écran en permanence sous chaque titre ;
  //    elles sont maintenant DERRIÈRE le « i », mot pour mot, et l'écran respire. ──
  {
    cle: 'couple',
    titre: 'Cycle et niveau',
    court: 'Le couple décide où le document est rangé.',
    long: "Choisissez le cycle et le niveau du document que vous allez déposer. C’est ce couple qui "
      + "décide où le document est rangé.\n\n"
      + "Le dépôt ne propose que des niveaux qui existent déjà : pour en créer un, passez par l’écran "
      + "Programmes & contenu (bouton « + Niveau »).",
  },
  {
    cle: 'document_pdf',
    titre: 'Document PDF',
    court: 'Fournir le référentiel officiel du couple, par dépôt ou par lien.',
    long: "Fournissez le référentiel officiel du couple choisi ci-dessus (dépôt ou lien), puis "
      + "vérifiez et validez le document.\n\n"
      + "Le document déposé attend d’être validé : rien n’est enregistré tant que vous n’avez pas "
      + "cliqué « Valider le référentiel ».",
  },
  {
    cle: 'referentiel_pdf',
    titre: 'Référentiel au format PDF',
    court: 'Le document enregistré pour ce couple : le relire, le remplacer, le supprimer.',
    long: "La fiche du référentiel de ce couple, telle qu’elle est en base : le PDF d’origine, le "
      + "texte de travail épuré que l’IA lit, et les preuves du contrôle fait au dépôt.\n\n"
      + "« Voir le référentiel » ouvre le PDF tel qu’il a été reçu. « Mettre à jour le référentiel » "
      + "le remplace et relance le traitement (texte, prompt, découpe) — les matières ne bougent pas.\n\n"
      + "« Supprimer » efface la fiche et le PDF, après confirmation. C’est refusé si ce référentiel "
      + "a déjà servi (unités ingérées). Les matières et le couple ne sont pas touchés.",
  },
  {
    cle: 'pdf_original',
    titre: 'Fichier PDF original',
    court: 'La pièce téléchargée, conservée telle quelle.',
    long: "Téléchargé — pièce d’origine consultable, matière première du dépôt, réserve pour l’avenir.\n\n"
      + "Ce fichier n’est jamais modifié : c’est le document tel qu’il est arrivé. Le texte que l’IA "
      + "lit, lui, est le document épuré, plus bas.",
  },
  {
    cle: 'matieres',
    titre: 'Matières de ce référentiel',
    court: 'Ce référentiel a ses propres matières : cochez celles que vous retenez.',
    long: "Ce référentiel possède ses propres matières, avec l’orthographe de son document.\n\n"
      + "Cochez les propositions que vous retenez, puis « Récupérer » : elles entrent au programme et "
      + "apparaissent aux profs de « {niveau} ».\n\n"
      + "Les matières appartiennent à ce référentiel : un autre niveau ne partage jamais les siennes, "
      + "même si l’une d’elles porte le même nom.",
  },
  {
    cle: 'prompt_matieres',
    titre: 'Prompt de lecture des matières',
    court: 'Le texte qui lit les matières — rangé sur le cycle, il sert à tous ses référentiels.',
    long: "Ce prompt est écrit par l’IA au premier « Proposer les matières » de ce cycle, à partir du "
      + "référentiel déposé, puis réutilisé par tous les référentiels du cycle.\n\n"
      + "Vous pouvez le corriger et le valider, ou le faire réécrire. Il doit garder le marqueur "
      + "{texte} — c’est là que le document est inséré.\n\n"
      + "Il vit en base, sur le cycle. Le même réglage se retrouve dans Prompts → Matières par cycle.",
  },
  {
    cle: 'prompt_decoupe',
    titre: 'Prompt de découpe',
    court: 'L’IA propose le prompt qui découpe CE document ; vous le relisez et le validez.',
    long: "L’IA lit le PDF et propose le prompt qui découpe CE document. Lisez-le, corrigez-le si "
      + "besoin, validez-le, puis déclenchez la découpe.\n\n"
      + "Rien n’est écrit en dur : le prompt vit en base, sur le référentiel de ce couple.",
  },
  {
    cle: 'decoupe',
    titre: 'Découpe',
    court: 'Découper le document en unités avec le prompt validé, puis valider le découpage.',
    long: "Lancez la découpe avec le prompt validé, contrôlez les unités produites, puis validez le "
      + "découpage — l’étape Types d’activité s’ouvre ensuite.",
  },
  {
    cle: 'types_activite',
    titre: 'Types d’activité de ce couple',
    court: 'L’IA propose les types du couple ; vous faites le ménage.',
    long: "L’IA se lance toute seule : elle lit le document épuré avec la table des types sous les "
      + "yeux, retient les types de ce couple (prompts et précisions générés dans la foulée).\n\n"
      + "Vous faites le ménage : ✕ pour retirer un type, le champ du bas pour en ajouter un.",
  },
]

// Renvoie les props { titre, court, long } à étaler dans <InfoGuide />. Clé inconnue → objet vide.
// `vars` remplit les repères {…} des textes (ex. { niveau: 'BTS CIEL Option B' }) : le catalogue
// reste la seule source, l'écran n'y réécrit rien — il ne fait que donner la valeur du moment.
export function aideReferentiels(cle, vars) {
  const e = GUIDE_REFERENTIELS.find(x => x.cle === cle) || {}
  const remplir = t => (typeof t === 'string' && vars)
    ? t.replace(/\{(\w+)\}/g, (brut, nom) => (nom in vars ? vars[nom] : brut))
    : t
  return { titre: e.titre, court: remplir(e.court), long: remplir(e.long) }
}
