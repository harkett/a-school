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
      + "8. AMBIGUÏTÉS — la dernière cartouche. Elle écrit UN ÉNONCÉ D'EXEMPLE PAR MATIÈRE : ce sont "
      + "eux que le professeur charge d'un clic, par « Utiliser un exemple », sur l'écran « Détecter les "
      + "ambiguïtés ». Même aller-retour que les étapes précédentes, mais UNE FOIS pour tout le "
      + "référentiel.\n\n"
      + "   a) Ouvrez le référentiel, descendez jusqu'à la cartouche « Ambiguïtés — énoncés d'exemple », "
      + "cliquez « Développer ».\n"
      + "   b) « 👁 Le prompt » : la fenêtre montre le texte rempli pour CE référentiel — toutes ses "
      + "matières, et sous chacune des extraits du document qui disent ce qu'elle recouvre. Une matière "
      + "que le découpage n'éclaire pas est nommée dans un bandeau orange en haut : elle n'est pas dans "
      + "le prompt, et son couple restera vide.\n"
      + "   c) « Sélectionner tout », puis Ctrl+C.\n"
      + "   d) Exécutez-le de votre côté. Il rend un bloc « ### matière » par matière, avec ses blocs "
      + "ENONCE et DEFAUTS, puis un bloc NON TRAITEES à la fin.\n"
      + "   e) Copiez sa réponse ENTIÈRE et collez-la dans « Coller le résultat entier ».\n"
      + "   f) « Enregistrer » : chaque bloc part sur la matière que son titre nomme.\n"
      + "   g) Lisez le compte rendu — entrés, remplacés, laissés de côté.\n"
      + "   h) Vérifiez dans Admin → Exemples → Ambiguïté.\n\n"
      + "   AUCUNE matière n'est écrite si l'une d'elles n'est pas reconnue : vous corrigez le nom et "
      + "vous recollez. Un exemple posé sur la mauvaise matière serait invisible.\n\n"
      + "   PAR L'IA : le bouton « ✨ Générer les exemples € » remplace b) à f). AVANT de l'utiliser, "
      + "montez « max_tokens » de l'outil « Exemples d'énoncés (ambiguïtés) » dans Admin → IA : c'est la "
      + "sortie la plus longue du logiciel, et une valeur trop basse coupe la réponse au milieu d'une "
      + "matière.\n\n"
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
    // Le « i » de la cartouche elle-même : les quatre gestes, dans l'ordre.
    cle: 'ambiguites',
    titre: 'Énoncés d’exemple (ambiguïtés)',
    source: 'ambiguite_exemples.texte, ambiguite_exemples.defauts (une ligne par matière)',
    court: 'Un énoncé d’exemple par matière, pour l’écran prof « Détecter les ambiguïtés ».',
    long: "L'écran prof « Détecter les ambiguïtés » propose un bouton « Utiliser un exemple » : il charge "
      + "un vrai sujet de la matière du professeur, au niveau, avec des défauts glissés dedans. De quoi "
      + "découvrir l'outil sans avoir à chercher un sujet.\n\n"
      + "Ces énoncés ne sont JAMAIS écrits à la volée : ils sont rangés en base, écrits d'avance, et le "
      + "professeur retrouve le même à chaque fois.\n\n"
      + "── LA PROCÉDURE, PAS À PAS (voie gratuite) ──\n\n"
      + "1. Ouvrez le référentiel dans la liste de gauche, puis descendez jusqu'à cette cartouche et "
      + "cliquez « Développer ». Elle affiche combien de matières ont déjà leur énoncé.\n\n"
      + "2. Cliquez « 👁 Le prompt ». La fenêtre montre le texte rempli pour CE référentiel : toutes ses "
      + "matières, et sous chacune des extraits de votre document qui disent ce qu'elle recouvre. Si une "
      + "matière n'est décrite nulle part dans le découpage, un bandeau orange la nomme en haut — elle "
      + "n'est pas dans le prompt, et son couple restera vide.\n\n"
      + "3. « Sélectionner tout », puis Ctrl+C.\n\n"
      + "4. Collez-le à votre agent, sur votre abonnement. Il rend un bloc « ### matière » par matière, "
      + "avec ses deux blocs ENONCE et DEFAUTS, puis un bloc « NON TRAITEES » à la fin.\n\n"
      + "5. Copiez sa réponse ENTIÈRE — les blocs compris — et collez-la dans la zone « Coller le "
      + "résultat entier », ci-dessous.\n\n"
      + "6. « Enregistrer ». Chaque bloc part sur la matière que son titre nomme.\n\n"
      + "7. Lisez le compte rendu : ce qui est entré, ce qui a été remplacé, et ce qui a été laissé de "
      + "côté — nom inconnu, bloc sans énoncé, matière déclarée non traitée, matière absente du texte.\n\n"
      + "8. Vérifiez le résultat dans Admin → Exemples → Ambiguïté : la ligne de chaque matière montre "
      + "son énoncé et ses défauts.\n\n"
      + "── LA VOIE PAYANTE ──\n\n"
      + "Le bouton « ✨ Générer les exemples € » remplace les points 2 à 6 : l'application appelle le "
      + "moteur elle-même et écrit le résultat. AVANT de l'utiliser, montez « max_tokens » de l'outil "
      + "« Exemples d'énoncés (ambiguïtés) » dans Admin → IA : c'est la sortie la plus longue du "
      + "logiciel, et une valeur trop basse coupe la réponse au milieu d'une matière.\n\n"
      + "── CE QUI NE PASSE JAMAIS ──\n\n"
      + "AUCUNE matière n'est écrite si l'une d'elles n'est pas reconnue : un nom mal orthographié est "
      + "signalé, vous le corrigez et vous recollez. Un exemple posé sur la mauvaise matière serait "
      + "invisible — le professeur le lirait sans jamais savoir qu'il n'est pas le sien. Par la voie "
      + "payante, la réponse revient dans la zone de collage au lieu d'être perdue : vous corrigez sans "
      + "repayer.\n\n"
      + "Le bloc « NON TRAITEES » liste les matières dont le modèle n'a pas su de quoi elles parlent : "
      + "leur couple reste vide. Vide plutôt que faux.\n\n"
      + "La pastille passe au vert quand TOUTES les matières du référentiel ont leur énoncé. Les étiquettes "
      + "vertes et rouges au-dessus de la zone de collage disent lesquelles il manque.",
  },
  {
    cle: 'ambiguites_prompt',
    titre: 'Le prompt des exemples',
    source: 'settings.prompt_ambiguite_exemples_referentiel + ambiguite_criteres + referentiel_chunks',
    court: 'Le texte qui génère les exemples — il porte toutes les matières du référentiel.',
    long: "Ce prompt génère les énoncés d'EXEMPLE de CE référentiel : il porte la liste de ses matières, et les types "
      + "d'ambiguïté à glisser dans chaque énoncé — les mêmes que ceux que le professeur peut cocher, "
      + "lus dans la même table.\n\n"
      + "Sous chaque matière figurent des EXTRAITS DE VOTRE RÉFÉRENTIEL, pris dans son découpage : ils "
      + "disent ce que la matière recouvre vraiment. Sans eux, un intitulé court se devine — « Langage » "
      + "avait ainsi donné un exercice de programmation en C pour des enfants de 0 à 3 ans, et personne "
      + "ne l'aurait vu. Ces extraits sont cherchés sur votre machine, par proximité de sens : rien "
      + "n'est facturé.\n\n"
      + "Une matière dont le découpage ne dit rien n'entre PAS dans le prompt : la fenêtre la nomme, et "
      + "son couple reste vide. Vide plutôt que faux.\n\n"
      + "Il s'exécute HORS de l'application : aucun appel n'est fait d'ici, rien n'est facturé.\n\n"
      + "Le texte du prompt lui-même se règle dans Admin → IA → Prompts → Autres fonctionnalités. "
      + "Ce bouton ne fait que l'afficher rempli, en lecture seule.",
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
]

// Renvoie les props { titre, court, long } à étaler dans <InfoGuide />. Clé inconnue → objet vide.
// `vars` remplit les repères {…} des textes (ex. { niveau: 'BTS CIEL Option B' }) : le catalogue
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
