// Catalogue UNIQUE des aides « i » de l'écran admin Référentiels. Même principe que
// utils/aideActivite.js : le petit « i » lit ces textes, et rien n'est réécrit dans l'écran.
//  - court  : bulle affichée au SURVOL du « i » (une phrase) ;
//  - long   : carte affichée au CLIC (l'aide complète, épinglée) ;
//  - source : d'où vient la donnée EN BASE, en clair — `table.champ` (06/08/2026). Ajouté à la
//             demande de l'admin : quand il signale quelque chose au développeur, les deux
//             parlent enfin du même objet, sans avoir à deviner. Il est affiché en pied de la
//             carte longue, jamais dans la bulle de survol (une phrase doit rester une phrase).
// Textes honnêtes : on ne décrit que ce que le bouton fait vraiment.
const GUIDE_REFERENTIELS = [
  {
    // Les DEUX façons de monter un référentiel, côte à côte. Elles mènent au même résultat en
    // base : ce qui change est QUI appelle le moteur d'IA. Rien ici n'est une intention — chaque
    // ligne décrit un bouton qui existe, ou dit clairement qu'il n'existe pas encore.
    cle: 'procedures',
    titre: 'Comment monter un référentiel',
    source: 'referentiels + matieres + referentiel_chunks + types_activite',
    court: 'Les deux façons de monter un référentiel : par l’IA, ou par vos soins.',
    long: "Un référentiel se monte toujours dans le même ordre : le document, les matières, la découpe, "
      + "les types d'activité. Ce qui change d'une voie à l'autre, c'est QUI appelle le moteur d'IA — "
      + "l'application, ou vous.\n\n"
      + "── PAR L'IA (l'application appelle ; les appels sont facturés) ──\n\n"
      + "1. Déposez le PDF et cliquez « Vérifier le référentiel ». Aucune IA.\n"
      + "2. « Proposer les matières » : si ce référentiel n'a pas encore son prompt des matières, l'IA "
      + "l'écrit d'abord, puis le lit sur le document — deux appels pour un clic. Vous cochez ce que "
      + "vous gardez.\n"
      + "3. « Découper » : même schéma. Le prompt de découpe s'écrit s'il manque, puis l'IA découpe. "
      + "Les unités sont écrites en base dans la foulée.\n"
      + "4. « Valider le découpage » : un enregistrement, aucun appel.\n"
      + "5. « Détecter les types » : même schéma que les matières.\n"
      + "6. « Générer les précisions » : un appel par type retenu.\n\n"
      + "── PAR VOS SOINS (aucun appel depuis l'application) ──\n\n"
      + "Le principe est le même à chaque étape, et il tient en un aller-retour : le MÉTA-PROMPT fait "
      + "écrire le PROMPT, le prompt fait sortir le RÉSULTAT. C'est VOUS qui exécutez les deux de votre "
      + "côté, sur votre abonnement, et qui rapportez ce qui en sort ; le développeur le pose en base ; "
      + "vous relisez et vous validez à l'écran.\n\n"
      + "1. Déposez le PDF et cliquez « Vérifier le référentiel ». Identique à l'autre voie.\n\n"
      + "2. MATIÈRES — a) Prenez le méta-prompt des matières (Prompts → Référentiels, ligne "
      + "prompt_meta_matieres) avec le texte du document, exécutez-le : il rend le prompt des matières. "
      + "Rapportez-le. b) Il est posé ligne prompt_matieres ; vous le relisez et vous le validez. "
      + "c) Exécutez CE prompt : il rend la liste des matières. d) Saisissez ces noms dans la carte "
      + "Matières — un nom saisi est retenu d'emblée.\n\n"
      + "3. DÉCOUPE — a) Même aller-retour avec le méta-prompt de découpe : vous obtenez le prompt de "
      + "découpe, il est posé, vous le validez. b) Exécutez-le : il rend la liste des titres. "
      + "c) Rapportez-la : le texte est tranché sur ces titres et les unités sont écrites en base. Il "
      + "n'existe pas encore d'endroit où coller cette liste vous-même — cette étape passe aujourd'hui "
      + "par le développeur.\n\n"
      + "4. VALIDATION — relisez les unités et cliquez « Valider le découpage ».\n\n"
      + "5. TYPES D'ACTIVITÉ — a) Même aller-retour avec le méta-prompt des types : vous l'exécutez, "
      + "vous rapportez le prompt des types, il est posé ligne prompt_types, vous le validez. "
      + "b) Exécutez CE prompt : il rend la liste des types. c) Saisissez-les dans la carte Types "
      + "d'activité.\n\n"
      + "6. LE ✎ PROMPT DE CHAQUE TYPE — c'est lui qui écrira l'activité que le professeur recevra "
      + "quand il choisira ce type. Par l'IA, il se remplit tout seul à la détection, à partir d'un "
      + "modèle commun où seul le nom du type change : les lignes reçoivent alors toutes le même texte. "
      + "Par vos soins, vous avez le choix — le rapporter vous-même en même temps que la liste des "
      + "types, ou demander au développeur de l'écrire, un texte par type. Dans les deux cas vous le "
      + "relisez derrière le ✎ Prompt de la ligne. Un type dont le ✎ Prompt est vide n'est pas "
      + "générable : le professeur reçoit « Ce type d'activité n'est pas encore prêt pour ce niveau ». "
      + "Le ✎ Prompt de la ligne est en LECTURE SEULE : un prompt ne s'écrit qu'à un endroit, "
      + "Admin → IA → Prompts → Référentiels, groupe « Génération ».\n\n"
      + "7. PRÉCISIONS — même aller-retour, un prompt par type retenu. Pas encore d'endroit où coller "
      + "le résultat vous-même.\n\n"
      + "Dans les deux voies, c'est vous qui validez chaque étape à l'écran : rien ne se valide seul.",
  },
  {
    cle: 'valider_document',
    titre: 'Valider le référentiel',
    source: 'referentiels.fichier, referentiels.source, referentiels.texte_epure',
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
    source: 'cycles.nom + niveaux.nom → referentiels.niveau_id (un référentiel par niveau)',
    court: 'Le couple décide où le document est rangé.',
    long: "Choisissez le cycle et le niveau du document que vous allez déposer. C’est ce couple qui "
      + "décide où le document est rangé.\n\n"
      + "Le dépôt ne propose que des niveaux qui existent déjà : pour en créer un, passez par l’écran "
      + "Formations (bouton « + Niveau »).",
  },
  {
    cle: 'document_pdf',
    titre: 'Document PDF',
    source: 'referentiels.fichier (nom d’origine) + referentiels.source (dépôt ou lien)',
    court: 'Fournir le référentiel officiel du couple, par dépôt ou par lien.',
    long: "Fournissez le référentiel officiel du couple choisi ci-dessus (dépôt ou lien), puis "
      + "vérifiez et validez le document.\n\n"
      + "Le document déposé attend d’être validé : rien n’est enregistré tant que vous n’avez pas "
      + "cliqué « Valider le référentiel ».",
  },
  {
    cle: 'referentiel_pdf',
    source: 'fichier sur disque : REFERENTIELS/<cycle>/<niveau>/referentiel.pdf',
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
    source: 'fichier sur disque, à côté du précédent, sous le nom lu dans referentiels.fichier',
    titre: 'Fichier PDF original',
    court: 'La pièce téléchargée, conservée telle quelle.',
    long: "Téléchargé — pièce d’origine consultable, matière première du dépôt, réserve pour l’avenir.\n\n"
      + "Ce fichier n’est jamais modifié : c’est le document tel qu’il est arrivé. Le texte que l’IA "
      + "lit, lui, est le document épuré, plus bas.",
  },
  {
    cle: 'matieres',
    titre: 'Matières de ce référentiel',
    source: 'matieres.nom, matieres.validee (cochée = au programme), matieres.referentiel_id',
    court: 'Ce référentiel a ses propres matières : cochez celles que vous retenez.',
    long: "Ce référentiel possède ses propres matières, avec l’orthographe de son document.\n\n"
      + "Cochez les propositions que vous retenez, puis « Récupérer » : elles entrent au programme et "
      + "apparaissent aux profs de « {niveau} ».\n\n"
      + "Les matières appartiennent à ce référentiel : un autre niveau ne partage jamais les siennes, "
      + "même si l’une d’elles porte le même nom.",
  },
  {
    cle: 'matieres_sans_payer',
    titre: 'Obtenir les matières sans rien payer',
    source: 'aucun appel IA — le méta-prompt et le prompt se lisent dans Prompts → Référentiels',
    court: 'Fable écrit le prompt, Sonnet l’exécute ; l’application ne paie rien.',
    long: "Le moteur d’IA de l’application n’est pas la seule façon de lire un document : le même travail se fait chez un agent extérieur, qui ne coûte rien à aSchool. Un abonnement Max donne accès à plusieurs modèles — et les deux tours ne demandent pas le même.\n\n"
      + "En deux tours, et le document épuré sert aux DEUX :\n\n"
      + "1. AVEC FABLE — donnez-lui le MÉTA-PROMPT des matières et le document épuré (repère {document}) : il vous rend le PROMPT. Écrire un prompt est un travail de conception, fait UNE fois, dont le résultat resservira à chaque lecture : on y met le modèle le plus capable.\n"
      + "2. Déposez ce prompt dans Prompts → Référentiels, et validez-le.\n"
      + "3. AVEC SONNET, DANS UNE CONVERSATION NEUVE — redonnez-lui ce prompt-là avec le document épuré (repère {texte}) : il vous rend les MATIÈRES, en JSON. C’est du repérage dans un texte, Sonnet suffit ; et c’est ce tour-là qui pèse sur le quota, puisqu’il repasse le document entier.\n"
      + "4. Contrôlez-les contre le document, puis saisissez-les ici.\n\n"
      + "La conversation NEUVE du point 3 n’est pas un détail : dans le fil où il vient d’écrire le prompt, le modèle a déjà lu le document et répondrait de mémoire. On croirait le prompt bon alors qu’on n’aurait éprouvé que sa mémoire.\n\n"
      + "Un méta-prompt hérité d’un autre diplôme porte les repères de CET autre diplôme : relisez-le avant de le lancer.",
  },
  {
    cle: 'proposer_matieres',
    titre: 'Proposer les matières — appel IA PAYANT',
    source: 'lit referentiels.texte_epure + referentiels.prompt_matieres → écrit dans matieres',
    court: 'Ce clic envoie le référentiel au moteur d’IA : il est facturé à chaque fois.',
    long: "Ce bouton n’est pas une lecture locale : le texte épuré du référentiel part chez le "
      + "fournisseur d’IA, et l’appel est FACTURÉ. Le prix dépend de la taille du document — un "
      + "référentiel entier en entrée, ce n’est pas gratuit.\n\n"
      + "Un seul clic peut coûter DEUX appels : si ce référentiel n’a pas encore son prompt de "
      + "lecture des matières, l’IA l’écrit d’abord, puis s’en sert pour lire le document.\n\n"
      + "Ce qui revient : des propositions, cochées par personne. Rien n’entre au programme tant "
      + "que vous n’avez pas coché puis cliqué « Récupérer ».\n\n"
      + "Le bouton se grise dès qu’il y a des propositions à l’écran : c’est voulu, pour qu’on ne "
      + "repaye pas une lecture déjà faite. Pour relire, videz d’abord la liste (« Supprimer tout »).",
  },
  {
    cle: 'meta_prompt_matieres',
    titre: 'Méta-prompt des matières',
    source: 'table settings, ligne key = prompt_meta_matieres (une seule pour toute l’application)',
    court: 'La consigne qui sert à ÉCRIRE le prompt des matières — pas à lire le document.',
    long: "Il y a deux prompts, et il ne faut pas les confondre.\n\n"
      + "Le MÉTA-prompt (celui-ci) est une consigne adressée à l’IA : « voici un document, écris-moi "
      + "le prompt qui saura lire les matières de ce genre de document ». Son repère {document} reçoit "
      + "le référentiel pris en exemple.\n\n"
      + "Le PROMPT DE LECTURE est ce que l’IA rend en réponse. C’est lui qui lira ensuite les "
      + "matières, et il porte le repère {texte}.\n\n"
      + "Conséquence sur la dépense : faire écrire le prompt est un appel PAYANT. Le même texte "
      + "écrit à la main coûte zéro. Le méta-prompt vit dans les réglages généraux (Prompts → admin), "
      + "il est le même pour tous les cycles.",
  },
  {
    cle: 'prompt_matieres',
    titre: 'Prompt de lecture des matières',
    source: 'referentiels.prompt_matieres, referentiels.prompt_matieres_valide',
    court: 'Le texte qui lit les matières de CE référentiel — il ne sert qu’à lui.',
    long: "Ce prompt est écrit par l’IA au premier « Proposer les matières » de ce référentiel, à "
      + "partir de son propre document.\n\n"
      + "Vous pouvez le corriger et le valider, ou le faire réécrire. Il doit garder le marqueur "
      + "{texte} — c’est là que le document est inséré.\n\n"
      + "Il vit en base, sur le référentiel : un autre niveau ne partage jamais le sien, même dans le même cycle.",
  },
  {
    cle: 'declencher_decoupe',
    titre: 'Découper — appel IA PAYANT',
    source: 'lit referentiels.texte_epure + referentiels.prompt_decoupe → aperçu, aucune écriture',
    court: 'Ce clic envoie le référentiel au moteur d’IA : il est facturé à chaque fois.',
    long: "Ce bouton n’est pas une découpe locale : le texte épuré du référentiel part chez le "
      + "fournisseur d’IA, et l’appel est FACTURÉ. Le prix dépend de la taille du document — un "
      + "référentiel entier en entrée, ce n’est pas gratuit.\n\n"
      + "Un seul clic peut coûter DEUX appels : si ce référentiel n’a pas encore son prompt de "
      + "découpe, l’IA l’écrit d’abord, puis s’en sert pour découper le document.\n\n"
      + "Ce qui revient est un APERÇU : rien n’est écrit en base tant que vous n’avez pas cliqué "
      + "« Valider le découpage ». C’est là seulement que les unités sont enregistrées.",
  },
  {
    cle: 'meta_prompt_decoupe',
    titre: 'Méta-prompt de la découpe',
    source: 'referentiels.prompt_meta_decoupe, sinon settings, ligne key = prompt_meta_decoupe',
    court: 'La consigne qui sert à ÉCRIRE le prompt de découpe — pas à découper le document.',
    long: "Il y a deux prompts, et il ne faut pas les confondre.\n\n"
      + "Le MÉTA-prompt (celui-ci) est une consigne adressée à l’IA : « voici un document, écris-moi "
      + "le prompt qui saura découper ce genre de document ». Son repère {document} reçoit le "
      + "référentiel pris en exemple.\n\n"
      + "Le PROMPT DE DÉCOUPE est ce que l’IA rend en réponse. C’est lui qui découpera ensuite, et "
      + "il porte le repère {texte}.\n\n"
      + "Deux endroits possibles, dans cet ordre : la case de CE niveau (Prompts → Référentiels), "
      + "et à défaut le réglage général (Prompts → admin), le même pour tous. La fenêtre dit lequel "
      + "des deux est réellement servi ici.\n\n"
      + "Conséquence sur la dépense : faire écrire le prompt de découpe est un appel PAYANT. Le "
      + "même texte écrit à la main coûte zéro.",
  },
  {
    cle: 'prompt_decoupe',
    titre: 'Prompt de découpe',
    source: 'referentiels.prompt_decoupe, referentiels.prompt_decoupe_valide',
    court: 'Le texte qui découpe CE référentiel — il ne sert qu’à lui.',
    long: "Le texte qui découpe CE référentiel en unités. Il ne sert qu’à lui : un autre niveau "
      + "ne partage jamais le sien, même dans le même cycle.\n\n"
      + "Vous pouvez l’écrire ou le corriger vous-même dans cette fenêtre — c’est gratuit. Si vous "
      + "le laissez vide, l’IA l’écrira au premier « Découper », ce qui fait un appel payant de "
      + "plus.\n\n"
      + "Il doit garder le marqueur {texte} : c’est là que le document est inséré.",
  },
  {
    cle: 'detecter_types',
    titre: 'Détecter les types — appel IA PAYANT',
    source: 'lit referentiels.texte_epure + referentiels.prompt_types → écrit dans types_activite',
    court: 'Ce clic envoie le référentiel au moteur d’IA : il est facturé à chaque fois.',
    long: "Ce bouton n’est pas une lecture locale : le texte épuré du référentiel part chez le "
      + "fournisseur d’IA, et l’appel est FACTURÉ. Le prix dépend de la taille du document.\n\n"
      + "Un seul clic peut coûter DEUX appels : si ce référentiel n’a pas encore son prompt des "
      + "types, l’IA l’écrit d’abord, puis s’en sert pour lire le document.\n\n"
      + "Ce qui revient : des propositions, cochées par personne. Rien n’entre au programme du "
      + "niveau tant que vous n’avez pas coché la ligne vous-même.",
  },
  {
    cle: 'meta_prompt_precisions',
    titre: 'Méta-prompt des précisions',
    source: 'referentiels.prompt_meta_precisions, sinon settings, ligne key = prompt_meta_precisions',
    court: 'La consigne qui sert à ÉCRIRE le prompt des précisions — pas à les proposer.',
    long: "Il y a deux prompts, et il ne faut pas les confondre.\n\n"
      + "Le MÉTA-prompt (celui-ci) est une consigne adressée à l’IA : « voici un document, écris-moi "
      + "le prompt qui saura proposer les précisions d’un type d’activité ». Son repère {document} "
      + "reçoit le référentiel pris en exemple.\n\n"
      + "Le PROMPT DES PRÉCISIONS est ce que l’IA rend en réponse. C’est lui qui travaillera au "
      + "bouton ✎ Précisions d’une ligne, et il porte DEUX repères : {texte} (le document) et "
      + "{label} (le type dont on veut les précisions).\n\n"
      + "Deux endroits possibles, dans cet ordre : la case de CE niveau (Prompts → Référentiels), "
      + "et à défaut le réglage général (Prompts → admin), le même pour tous. La fenêtre dit lequel "
      + "des deux est réellement servi ici.",
  },
  {
    cle: 'meta_prompt_types',
    titre: 'Méta-prompt des types d’activité',
    source: 'referentiels.prompt_meta_types, sinon settings, ligne key = prompt_meta_types',
    court: 'La consigne qui sert à ÉCRIRE le prompt des types — pas à lire le document.',
    long: "Il y a deux prompts, et il ne faut pas les confondre.\n\n"
      + "Le MÉTA-prompt (celui-ci) est une consigne adressée à l’IA : « voici un document, écris-moi "
      + "le prompt qui saura y relever les types d’activité ». Son repère {document} reçoit le "
      + "référentiel pris en exemple.\n\n"
      + "Le PROMPT DES TYPES est ce que l’IA rend en réponse. C’est lui qui lira ensuite le "
      + "document, et il porte le repère {texte}.\n\n"
      + "Deux endroits possibles, dans cet ordre : la case de CE niveau (Prompts → Référentiels), "
      + "et à défaut le réglage général (Prompts → admin), le même pour tous. La fenêtre dit lequel "
      + "des deux est réellement servi ici.\n\n"
      + "Conséquence sur la dépense : faire écrire le prompt des types est un appel PAYANT. Le "
      + "même texte écrit à la main coûte zéro.",
  },
  {
    cle: 'prompt_types',
    titre: 'Prompt de lecture des types d’activité',
    source: 'referentiels.prompt_types, referentiels.prompt_types_valide',
    court: 'Le texte qui lit les types d’activité de CE référentiel — il ne sert qu’à lui.',
    long: "Le texte qui relève, dans ce document, les formats de travail qu’il met en œuvre. Il ne "
      + "sert qu’à ce référentiel : un autre niveau ne partage jamais le sien.\n\n"
      + "Vous pouvez l’écrire ou le corriger vous-même dans cette fenêtre — c’est gratuit. Si vous "
      + "le laissez vide, l’IA l’écrira au premier « Détecter les types », ce qui fait un appel "
      + "payant de plus.\n\n"
      + "Il doit garder le marqueur {texte} : c’est là que le document est inséré.",
  },
  {
    cle: 'prompt_precisions',
    titre: 'Prompt des précisions',
    source: 'referentiels.prompt_precisions, referentiels.prompt_precisions_valide',
    court: 'Le texte qui lit les précisions d’un type dans CE référentiel — consultation seule ici.',
    long: "UN SEUL prompt pour tout le référentiel, et non un par type. Le logiciel l’appelle "
      + "autant de fois qu’il y a de types, en remplaçant à chaque fois son repère {label} par le "
      + "nom du type dont il veut les précisions. Son autre repère, {texte}, reçoit le document.\n\n"
      + "Ne le confondez pas avec le ✎ Prompt d’une ligne de type : celui-là GÉNÈRE ce que le "
      + "professeur reçoit quand il clique, et il y en a un par type. Celui-ci ne sert qu’une fois, "
      + "côté administration, pour remplir le menu des précisions.\n\n"
      + "Cette fenêtre est en LECTURE SEULE : un prompt ne s’écrit qu’à un seul endroit, "
      + "Prompts → onglet Référentiels, ligne « prompt_precisions » de ce niveau.",
  },
  {
    cle: 'decoupe',
    titre: 'Découpe',
    source: 'referentiel_chunks (une ligne par unité) + referentiels.decoupe_valide',
    court: 'Découper le document en unités avec le prompt validé, puis valider le découpage.',
    long: "Lancez la découpe avec le prompt validé, contrôlez les unités produites, puis validez le "
      + "découpage — l’étape Types d’activité s’ouvre ensuite.",
  },
  {
    cle: 'types_activite',
    titre: 'Types d’activité de ce référentiel',
    source: 'types_activite.label, types_activite.validee, types_activite.referentiel_id',
    court: 'L’IA propose les types de ce référentiel ; vous gardez ce que vous voulez.',
    long: "L’IA ne part JAMAIS toute seule : il faut cliquer « Détecter les types », et cet appel "
      + "est facturé. Elle lit le document épuré — sans aucun catalogue commun sous les yeux, "
      + "puisque chaque référentiel nomme ses types comme LUI les nomme.\n\n"
      + "Ce qui revient est proposé, pas retenu : cochez ce que vous gardez. ✕ supprime la ligne, "
      + "le champ du bas en ajoute une à la main (gratuit).",
  },
  {
    cle: 'precisions',
    titre: 'Précisions des types d’activité',
    source: 'referentiel_type_precisions.libelle, rattachée à types_activite.id',
    court: 'Décliner chaque type au programme en formes concrètes, adaptées à ce niveau.',
    long: "Une précision est une déclinaison du type pour CE niveau : « activités écrites » donne "
      + "« copie » et « dictée » en primaire, « dissertation » dans le supérieur. C’est elle que le "
      + "professeur choisira au moment de préparer sa séance.\n\n"
      + "Seuls les types AU PROGRAMME figurent ici : une proposition non cochée n’a rien à "
      + "décliner, et le serveur refuserait d’y travailler.\n\n"
      + "Rien ne part tout seul (15/08/2026). « Préparer les précisions » traite d’un coup tous "
      + "les types qui n’en ont pas, et annonce le nombre d’appels facturés avant de commencer ; "
      + "« Proposer les précisions » n’en fait qu’un. Les écrire à la main reste gratuit.",
  },
]

// Renvoie les props { titre, court, long } à étaler dans <InfoGuide />. Clé inconnue → objet vide.
// `vars` remplit les repères {…} des textes (ex. { niveau: 'Collège · 4e' }) : le catalogue
// reste la seule source, l'écran n'y réécrit rien — il ne fait que donner la valeur du moment.
//
// La `source` est collée en pied du texte long, jamais du court : c'est le nom exact de la donnée
// en base, pour que l'admin et le développeur désignent la même chose quand ils s'en parlent.
export function aideReferentiels(cle, vars) {
  const e = GUIDE_REFERENTIELS.find(x => x.cle === cle) || {}
  const remplir = t => (typeof t === 'string' && vars)
    ? t.replace(/\{(\w+)\}/g, (brut, nom) => (nom in vars ? vars[nom] : brut))
    : t
  const long = e.source ? `${e.long}\n\nEn base : ${e.source}` : e.long
  return { titre: e.titre, court: remplir(e.court), long: remplir(long) }
}
