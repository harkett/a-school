# -*- coding: utf-8 -*-
"""Référentiel d'éveil 0-3 ans — aSchool. Génère le document complet, en une seule mise en page.

CONTRAINTE QUI COMMANDE TOUT : ce PDF sera ÉPURÉ, et son texte servira de matière aux prompts.
D'où :
  - une seule colonne (le multi-colonnes casse l'ordre de lecture à l'extraction) ;
  - un titre par ligne, jamais collé à son contenu ;
  - des rubriques toujours écrites de la même façon (« Âge : », « Matériel : », « Objectifs : »,
    « Déroulé : », « À observer : », « Sécurité : ») pour que la découpe les reconnaisse ;
  - aucun texte décoratif qui n'aurait pas de sens une fois le PDF réduit à du texte brut.
"""
from fpdf import FPDF

TTF = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
TTF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

VIOLET = (91, 33, 182)
VIOLET_CLAIR = (243, 240, 255)
VIOLET_TRAIT = (196, 181, 253)
ENCRE = (17, 24, 39)
GRIS = (100, 116, 139)
GRIS_CLAIR = (248, 250, 252)
GRIS_TRAIT = (226, 232, 240)
AMBRE_FOND = (255, 251, 235)
AMBRE_TRAIT = (252, 211, 77)
AMBRE_TEXTE = (120, 53, 15)

# =============================================================================================
# PARTIE 1 — LES ACTIVITÉS D'ÉVEIL (texte repris du document d'origine, sans reformulation)
# =============================================================================================
D1 = [
 {"t": "Imagier",
  "age": "Bébés (0-1) · 1-3 ans", "mat": "imagier (livre d'images cartonné)",
  "obj": "éveil du langage et de la curiosité ; l'enfant se détend physiquement et émotionnellement "
         "et échange avec l'adulte.",
  "der": [("Bébés", "parler le plus possible, écouter les sons du bébé et y répondre, commenter les "
                    "images, aider à tourner les pages, changer souvent d'image (les 1-3 mois voient "
                    "mieux à 20-30 cm)."),
          ("1-3 ans", "regarder l'imagier ensemble, poser des questions simples sur les images, "
                      "montrer du doigt en nommant, faire chercher/nommer des objets, parler des "
                      "couleurs, compter les objets.")],
  "obs": "curiosité en éveil, l'enfant tourne des pages, communique et prend plaisir à parler de ce "
         "qu'il voit."},

 {"t": "Sons familiers", "nodiff": True, "mat": "aucun", "age": "Bébés-3 ans",
  "obj": "apprentissage du langage par l'imitation des sons ; développe aussi le lien affectif "
         "(regard, sourire).",
  "der": "parler beaucoup ; répéter un son que l'enfant aime (ba-ba, ma-ma) et attendre qu'il le "
         "reproduise ; varier le son (doux/fort, vite/lentement, grave/aigu) ; observer son visage.",
  "obs": "le visage change selon les sons, l'enfant gazouille, copie un son, rit.",
  "sec": "ne jamais chanter ou émettre de sons trop forts (cela effraie)."},

 {"t": "Je vois quelque chose", "nodiff": True, "mat": "aucun", "age": "Bébés-3 ans",
  "obj": "reconnaître et nommer des objets familiers ; analyser son environnement.",
  "der": "montrer et désigner des objets autour de soi (« Qu'est-ce que je vois ? ») ; marcher dans "
         "la pièce, encourager à toucher différentes textures et les nommer.",
  "obs": "l'enfant reconnaît et tente de nommer des objets familiers."},

 {"t": "Une petite parlotte", "obs": "les jeunes enfants disent quelques mots et ont l'impression d'être quelqu'un de spécial.", "nodiff": True, "mat": "aucun", "age": "Bébés-3 ans",
  "obj": "dire quelques mots, se sentir « quelqu'un de spécial » ; développe aussi la confiance en soi.",
  "der": "réserver un temps calme pour parler avec l'enfant, le laisser sur ses genoux, parler "
         "doucement de tout ce qui l'intéresse, rebondir sur ce qu'il dit."},

 {"t": "Puzzle à encastrer", "nodiff": True, "age": "Bébés (0-1) · 1-3 ans", "mat": "plateau et pièces à encastrer",
  "obj": "se servir de ses yeux pour atteindre et attraper des objets de formes et de tailles "
         "différentes ; réfléchir et raisonner. Développe aussi la motricité fine.",
  "der": "laisser sortir, tenir, taper les pièces, explorer les contours des trous ; nommer couleurs "
         "et formes ; cacher une pièce sous un tissu et la faire retrouver ; demander de faire le "
         "puzzle et de mémoriser où va chaque pièce.",
  "obs": "l'enfant est calme et concentré, le cerveau travaille à fond.",
  "sec": "veiller à ce que le bébé ne porte pas les pièces à la bouche."},

 {"t": "Puzzle à anneaux", "nodiff": True, "age": "Bébés (0-1) · 1-3 ans",
  "mat": "anneaux de bois de couleurs différentes",
  "obj": "attraper et tenir des objets, démonter et remonter, commencer à compter et à montrer les "
         "couleurs du doigt.",
  "der": "laisser attraper et frapper les pièces, parler des couleurs, cacher une pièce sous un "
         "tissu à retrouver ; faire des chaînettes en comptant, inventer une comptine à compter.",
  "obs": "l'enfant démonte et remonte, comprend « un » et « deux », essaie de compter, montre les "
         "couleurs nommées."},

 {"t": "Trieur de formes", "obs": "les bébés améliorent leur coordination œil-main et leur motricité en manipulant les objets ; les 1-3 ans apprennent le nom des couleurs et des formes et comprennent mieux l'orientation spatiale et les relations de cause à effet.", "nodiff": True, "age": "Bébés (0-1) · 1-3 ans",
  "mat": "boîte à formes et formes colorées",
  "obj": "coordination œil-main, noms des couleurs et des formes, orientation spatiale et relations "
         "de cause à effet.",
  "der": "laisser manipuler librement, ouvrir, vider et remplir la boîte, nommer la forme manipulée "
         "et faire trouver le trou correspondant, apprendre à tourner main et poignet.",
  "sec": "ne jamais laisser un bébé seul, surveiller la mise en bouche."},

 {"t": "Ensemble d'objets à trier et empiler", "nodiff": True, "age": "Bébés (0-1) · 1-3 ans",
  "mat": "objets de tailles, couleurs et formes différentes à empiler",
  "obj": "empiler ; comparer plus grand et plus petit ; trier ; comprendre « un » et « beaucoup ».",
  "der": "poser un objet, en empiler un dessus pendant que l'enfant regarde, lui en donner un ; "
         "laisser explorer et empiler à sa façon ; parler couleur, taille et forme ; faire trouver "
         "tous les objets d'une même couleur.",
  "obs": "l'enfant imite, remarque les tailles, compare, trie quand c'est facile."},

 {"t": "Dominos", "age": "1-3 ans", "mat": "dominos à points",
  "obj": "reconnaître et compter les points, suivre une règle simple, s'intéresser aux nombres.",
  "der": "laisser jouer librement (empiler, aligner, faire des formes) ; reproduire une forme de "
         "dominos ; compter les points et faire trouver le même nombre ailleurs.",
  "obs": "l'enfant reproduit une forme, compte les points, nomme des chiffres."},

 {"t": "Cubes puzzle", "age": "1-3 ans", "mat": "cubes portant une image sur chaque face",
  "obj": "réflexion et raisonnement.",
  "der": "expliquer que les cubes assemblés forment une image, laisser un enfant ou un groupe "
         "assembler, encourager à terminer ensemble.",
  "obs": "l'enfant est calme et concentré, le cerveau travaille."},

 {"t": "Jeu de mémoire", "age": "1-3 ans", "mat": "cartes à paires d'images",
  "obj": "reconnaître similarités, différences et catégories, réfléchir de façon logique, aiguiser "
         "l'imagination.",
  "der": "laisser manipuler et trier les cartes qui vont ensemble, parler des images, demander les "
         "cartes préférées et pourquoi.",
  "obs": "l'enfant s'intéresse aux cartes, veut en savoir plus, rapproche les images."},

 {"t": "Récit et invention d'histoires", "st": "source Doc 1 — expression / lecture",
  "age": "dès environ 2 ans (dans notre bande 1-3)", "mat": "imagier, voix de l'adulte",
  "obj": "utiliser son imagination, entrer en relation avec l'adulte, s'initier à sa culture ; se détendre.",
  "der": "s'asseoir parmi les enfants et raconter une histoire familière, traditionnelle ou "
         "inventée ; inviter une personne âgée à raconter une histoire de la communauté ; prolonger "
         "par du dessin ou du théâtre reprenant les personnages.",
  "obs": "l'enfant écoute, participe, reformule à sa manière."},

 {"t": "Créer ses propres livres de lecture", "st": "source Doc 1",
  "age": "dès environ 2 ans", "mat": "papier, crayons, colle ou papier adhésif",
  "der": "choisir ou inventer un conte court avec les enfants ; sélectionner 5 ou 6 images "
         "d'événements clés ; faire dessiner les images ; écrire une phrase courte sous chaque "
         "image ; assembler les pages."},
]

D2 = [
 {"t": "Balles en éponge", "nodiff": True, "age": "Bébés (0-1) · 1-3 ans", "mat": "balles en éponge",
  "obj": "motricité, curiosité, concentration et précision (poursuivre et attraper).",
  "der": "faire rouler la balle vers l'enfant, le laisser toucher et tenir la balle molle ; cacher "
         "partiellement puis totalement la balle à retrouver ; faire renvoyer la balle, taper, "
         "lancer, rattraper.",
  "obs": "l'enfant se baisse pour ramasser, améliore sa motricité, joue avec l'adulte."},

 {"t": "Papier et crayons", "age": "Bébés (0-1) · 1-3 ans",
  "mat": "papier, gros crayons pour les petits, crayons de couleur",
  "obj": "créativité, dextérité, reconnaissance des couleurs et des formes ; développe aussi "
         "l'expression de soi.",
  "der": [("Bébés", "découper des formes de couleur, les suspendre au-dessus du bébé, parler des "
                    "couleurs pendant qu'il les regarde bouger."),
          ("1-3 ans", "donner de grands crayons et du papier, laisser explorer la prise et dessiner "
                      "librement, afficher les dessins.")],
  "obs": "l'enfant s'exprime par le dessin, aiguise créativité et dextérité."},

 {"t": "Perles à enfiler", "obs": "les bébés aiguisent leur curiosité, cherchent à toucher, attraper ou tirer les objets quand la cordelette glisse ou se balance, expriment leur joie, sourient et gazouillent ; les 1-3 ans distinguent les couleurs et affinent motricité et dextérité.", "nodiff": True, "age": "Bébés (0-1) · 1-3 ans",
  "mat": "perles de tailles et de couleurs différentes, cordelettes",
  "obj": "coordination œil-main, motricité fine, distinguer les couleurs, commencer à compter.",
  "der": "nouer des perles au bout de cordelettes, montrer au bébé à tirer pour approcher le "
         "jouet ; faire enfiler par couleur ou par forme, compter les perles, faire un collier ou "
         "un bracelet.",
  "sec": "supervision d'un adulte indispensable (perles = risque d'ingestion)."},

 {"t": "Cubes de construction", "obs": "les enfants apprennent le nom des couleurs, améliorent leur coordination œil-main et affinent leur motricité et leur dextérité en manipulant les objets.", "age": "1-3 ans", "mat": "cubes de couleur",
  "obj": "coordination œil-main, dextérité, concepts de taille et de forme ; développe aussi la "
         "coopération.",
  "der": "laisser jouer librement ; parler couleur et forme, faire choisir un cube de même couleur "
         "ou forme ; pour coopérer, donner un cube à chacun pour construire ensemble à tour de rôle."},

 {"t": "Pâte à modeler", "obs": "les enfants apprennent le nom des couleurs, améliorent leur coordination œil-main et affinent leur dextérité, leur créativité et leur motricité.", "age": "1-3 ans", "mat": "pâte à modeler multicolore",
  "obj": "créativité, dextérité, coordination œil-main, orientation spatiale.",
  "der": "laisser créer des formes librement ; combiner avec des éléments naturels (coquillages, "
         "feuilles, brindilles) ; mettre une histoire en scène avec des personnages en pâte.",
  "sec": "pour les bébés, seulement tâter la pâte ; veiller à ce qu'ils ne la portent pas à la bouche."},

 {"t": "Nous pouvons bouger / Le tunnel", "obs": "les enfants améliorent leur aptitude à reconnaître et analyser situations et objets, améliorent leur équilibre, apprennent à s'asseoir, se mettre à genoux et ramper en se servant des différentes parties de leur corps.", "nodiff": True, "mat": "aucun", "age": "Bébés-3 ans",
  "obj": "équilibre ; apprendre à s'asseoir, se mettre à genoux, ramper ; développe aussi la confiance.",
  "der": "deux enfants se tiennent les mains pour former un tunnel, les tout-petits rampent dessous "
         "(variantes : arbre, montagne, pont) ; se mettre à leur niveau, sourire.",
  "sec": "supervision permanente, pas d'activité dangereuse, jamais de punition."},

 {"t": "Peux-tu m'imiter ? / Jeu d'imitation", "obs": "les enfants écoutent quand ils entendent des mots familiers, imitent vos gestes et apprennent à bouger leur corps.", "nodiff": True, "mat": "aucun", "age": "Bébés-3 ans",
  "obj": "imiter les gestes, apprendre à bouger son corps ; développe aussi l'écoute.",
  "der": "faire des gestes simples à imiter (frapper des mains, se tapoter la tête, pencher la "
         "tête) ; montrer les parties du corps (yeux, nez, bouche) ; demander des postures "
         "(« grand comme un arbre », « aussi petit que possible »)."},

 {"t": "Nous pouvons faire de la musique", "obs": "les enfants imaginent diverses façons de produire des sons avec leur corps et répètent les mouvements et le langage.", "nodiff": True, "mat": "aucun", "age": "Bébés-3 ans",
  "obj": "produire des sons avec son corps, répéter mouvements et langage.",
  "der": "montrer à faire des sons avec le corps (frapper des mains, claquer des doigts, taper sur "
         "les cuisses ou le sol) ; créer une comptine en suivant l'enfant ; bercer en fredonnant.",
  "sec": "jamais de sons trop forts."},

 {"t": "Déplacement en ronde", "nodiff": True, "st": "source Doc 1", "age": "Bébés-3 ans",
  "mat": "aucun",
  "obj": "coordonner ses mouvements, exécuter des consignes simples.",
  "der": "se donner la main pour faire une ronde, chanter, et glisser dans la chanson des consignes "
         "(s'asseoir, se lever, sauter en avant, tourner) selon les capacités."},

 {"t": "Dessin par thème et à partir d'images", "st": "source Doc 1",
  "age": "tout-petits (dans notre bande)",
  "mat": "imagier ou cubes-images, papier, gros crayons cire",
  "obj": "imagination, capacité à dessiner et colorier.",
  "der": "exposer un imagier ou une image, demander ce qu'on y voit, faire décrire, faire raconter "
         "une histoire, puis faire raconter l'histoire par un dessin ; possibilité d'un thème par "
         "semaine (saisons, animaux, famille…)."},
]

D3 = [
 {"t": "Marionnettes", "age": "Bébés (0-1) · 1-3 ans",
  "mat": "marionnettes à main ou à doigts (animaux)",
  "obj": "exprimer ses sentiments, s'identifier, surmonter une peur, imaginer ; développe aussi le "
         "langage et le lien social. Idéal, avec un adulte attentif, pour aborder des sujets difficiles.",
  "der": [("Bébés", "enfiler une marionnette, la faire parler au bébé (changer de voix), le laisser "
                    "la toucher et jouer."),
          ("1-3 ans", "marionnettes animales pour parler et chanter, poser des questions simples "
                      "(nom, vêtements, parties du corps), laisser inventer histoires et chansons.")],
  "obs": "le bébé se sent en sécurité avec la marionnette et l'identifie souvent à lui-même ou à la "
         "personne qui le réconforte.",
  "sec": "vérifier que l'animal-marionnette convient à la culture."},

 {"t": "Nous allons…", "obs": "les enfants acquièrent des aptitudes sociales, deviennent plus curieux, prennent confiance en eux et se sentent en sécurité ; leurs interactions entre eux et avec l'adulte les rendent plus sociables.", "nodiff": True, "mat": "aucun", "age": "Bébés-3 ans",
  "obj": "sécurité affective, confiance et estime de soi ; développe aussi la sociabilité.",
  "der": "chanter une mélodie familière en annonçant ce qui va se passer (« Nous allons sortir, "
         "jouer, rire… ») ; prendre les tout-petits dans les bras et les dorloter plusieurs fois par "
         "jour ; inventer des chansons sur le prénom de chaque enfant.",
  "sec": "supervision permanente ; jamais de punition verbale ou physique."},

 {"t": "Interprétation théâtrale d'une histoire", "st": "source Doc 1",
  "age": "très jeunes enfants (dans notre bande)",
  "mat": "marionnettes, objets divers, éventuellement danse et musique",
  "obj": "jouer des rôles, personnifier des personnages, exprimer son vécu.",
  "der": "choisir une histoire ou un conte avec les enfants, distribuer des rôles (y compris pour "
         "les enfants en situation de handicap : arbres, fleurs, herbe…) ; une voix externe raconte "
         "pendant que les enfants jouent ; abréger les dialogues."},
]

D4 = [
 {"t": "Je suis là. Qui est là ?", "obs": "les enfants interagissent avec les autres et avec l'adulte, ce qui renforce leurs aptitudes sociales, l'apprentissage précoce, l'estime et la confiance en soi ; ils améliorent leurs capacités à reconnaître et analyser.", "nodiff": True, "mat": "aucun", "age": "Bébés-3 ans",
  "obj": "interagir avec l'adulte et les autres, renforcer les aptitudes sociales, l'estime et la "
         "confiance en soi ; reconnaître.",
  "der": "dire ou fredonner le prénom de l'enfant et observer son attention ; chanter « Je suis là. "
         "Qui est là ? » en ajoutant le prénom de l'enfant et de l'animateur ; saluer chaque enfant "
         "qui arrive ou part (« Regardez, [prénom] est là »)."},

 {"t": "Coopérer avec les cubes de construction", "st": "renvoi", "age": "1-3 ans",
  "der": "voir « Cubes de construction » (Domaine 2) : donner un cube à chaque enfant pour "
         "construire ensemble, à tour de rôle → premières coopérations 1-3 ans."},
]

A_VALIDER = [
 "**Rituels et routines** (2-8 ans) — instaurer un rituel de début et de fin de journée (chanson, "
 "jeu), petits rituels de transition. → éveil, cadre sécurisant. Très pertinent 0-3.",
 "**Exercices de détente** (respiration profonde, « la marionnette », câlins papillon, respiration "
 "abdominale, rire) — apaiser, se calmer. → pertinent, à alléger du cadre trauma.",
 "**De mon cœur au tien** (4-8 dans la source) — dire « je te souhaite du bien » en pointant des "
 "parties du corps. → lien affectif ; à re-tester pour le bas de la tranche.",
 "**Réseau de liens** (3-8) — faire rouler une balle ou une marionnette en disant le prénom. → "
 "social et mémoire des prénoms.",
 "**Dessin libre** (2-8) — un temps régulier pour dessiner librement ses idées et ses émotions. → "
 "expression de soi (Domaine 3).",
 "**Notre cercle de mains / objets transitionnels** — décorer une main en papier, la relier aux "
 "autres. → appartenance au groupe ; fort ancrage « urgence » dans la source, à reformuler.",
]

DOMAINES = [
 ("1", "Parler et réfléchir",
  "Participer à une conversation, relier les mots aux actes, comprendre des concepts (doux/dur, "
  "grand/petit, positions), imaginer, faire un plan, mener une tâche à terme, raisonner, compter "
  "et trier.", D1),
 ("2", "Bouger et faire",
  "Prendre conscience de son corps et de l'espace, améliorer l'équilibre, la coordination "
  "œil-main, la motricité globale et fine (mains, poignets, doigts).", D2),
 ("3", "Comprendre ce qu'on ressent, apprendre qui on est",
  "Exprimer et nommer ses émotions, prendre confiance (« je peux le faire ! »), se sentir en "
  "sécurité, se constituer une image de soi.", D3),
 ("4", "S'entendre avec les autres",
  "Jouer avec d'autres, coopérer, partager, suivre une règle simple, se sentir membre d'un "
  "groupe.", D4),
]

# =============================================================================================
# PARTIE 2 — LES TEMPS DU QUOTIDIEN
# =============================================================================================
P2 = [
 {"t": "Le jeu et l'exploration",
  "ret": "L'exploration de l'enfant est favorisée et encouragée en toute circonstance. Les interdits "
         "liés au danger sont systématiquement interrogés : s'agit-il d'un danger réel, ou d'une "
         "peur de l'adulte ?",
  "p": ["L'enfant a besoin d'explorer librement : toucher, manipuler, flairer, goûter, déchirer, "
        "soulever, renverser, escalader. Il se tache et se salit — c'est le signe que ça fonctionne. "
        "L'enfant ne se développe pas par sphères cloisonnées (sensoriel, moteur, cognitif, "
        "langagier) mais globalement, en synergie : une activité de motricité développe l'ensemble."],
  "li": ["Il laisse l'enfant circuler et explorer ; il joue avec lui, reste à proximité et attentif.",
         "Il propose du matériel « bon à tout faire » (boîtes, tubes, contenants vides, tissus) qui "
         "permet de nombreuses combinaisons, et accepte le détournement des objets du quotidien.",
         "Quand l'exploration entre en conflit avec la sécurité ou le collectif, il **réoriente** "
         "l'enfant vers autre chose plutôt que d'interdire ou d'arrêter.",
         "Il distingue le **danger** (dont l'enfant doit être protégé) du **risque** (occasion "
         "d'exploration accompagnée). Si le lieu présente un danger réel, c'est au lieu de s'adapter.",
         "**Quand il se surprend à dire « non » trop souvent, il s'interroge sur l'aménagement de "
         "l'espace**, pas sur l'enfant.",
         "Il est vigilant aux stéréotypes de genre dans le choix des jeux et déguisements, et "
         "accepte toutes les formes de jeu sans distinction."]},

 {"t": "Le langage",
  "ret": "Le professionnel s'adresse à l'enfant quel que soit son âge et prend le temps de "
         "l'interaction, qu'elle soit verbale ou pré-verbale.",
  "p": ["Le langage s'acquiert dans l'interaction. À 2 ans, un enfant peut avoir 50 mots quand un "
        "autre en produit 500 — l'écart tient à la qualité du bain langagier depuis la naissance."],
  "li": ["Il parle à l'enfant à tous les âges : il explique les soins qu'il prodigue, décrit "
         "l'action, raconte, pose des questions au bébé et laisse le temps de la réponse non verbale.",
         "Il emploie un langage riche, précis, construit ; il n'utilise pas de langage enfantin et "
         "ne parle jamais de l'enfant à la troisième personne devant lui.",
         "Il parle **individuellement**, en regardant l'enfant dans les yeux, et évite les paroles "
         "adressées au groupe, surtout pour les plus petits.",
         "Il ne l'interrompt pas quand il s'exprime, verbalement ou non.",
         "Il porte une attention particulière aux enfants « discrets », qui parlent peu ou ne "
         "sollicitent pas l'adulte.",
         "Il nomme les émotions des personnages quand il raconte une histoire, et demande aux plus "
         "grands ce qu'ils ressentent.",
         "**Pas de musique de fond en continu** : elle freine la perception des sons et les "
         "interactions langagières.",
         "Il encourage le contact avec plusieurs langues, dont la langue d'origine des familles "
         "allophones."]},

 {"t": "Les émotions de l'enfant",
  "ret": "L'expression des émotions est favorisée, jamais empêchée. Lors d'émotions fortes, le "
         "professionnel accompagne et sécurise sans chercher à faire cesser.",
  "p": ["Le jeune enfant ne peut pas réguler seul ses émotions : son cerveau est immature, il ne "
        "peut pas « se raisonner ». L'adulte est le principal régulateur. La régulation viendra "
        "progressivement, par imitation de l'adulte."],
  "li": ["Il nomme les émotions — celles de l'enfant comme les siennes.",
         "Il ne dit pas « calme-toi », ne minimise pas (« ce n'est pas grave »), ne gronde pas parce "
         "que l'enfant crie.",
         "Il émet des hypothèses à voix haute, **y compris pour un enfant qui ne parle pas encore** : "
         "« es-tu triste, en colère, as-tu peur ? »",
         "Il apaise par le regard, le contact, le portage, la parole. Si l'enfant rejette la "
         "proximité, il reste à distance **en gardant le lien visuel**.",
         "Il accueille toutes les émotions avec la même bienveillance, sans distinction de genre — "
         "la colère chez les filles autant que la tristesse chez les garçons.",
         "Si le comportement menace la sécurité, il peut tenir l'enfant **en lui expliquant qu'il le "
         "tient pour le protéger**.",
         "Une fois l'enfant calme, il revient avec lui sur ce qui s'est passé, et s'interroge sur ce "
         "qui aurait pu l'éviter."]},

 {"t": "Les pleurs",
  "ret": "Le professionnel accompagne et sécurise l'enfant qui pleure, cherche le besoin insatisfait "
         "— sans avoir pour objectif premier de faire cesser les pleurs.",
  "p": ["Les pleurs sont une alarme qui signale un besoin non satisfait, même quand l'adulte ne "
        "l'identifie pas. Les pleurs ne sont jamais des caprices ni des tentatives de manipulation. "
        "Consoler ne veut pas dire faire taire."],
  "li": ["Il demande à l'enfant ce qu'il ressent.",
         "Il le prend dans les bras, dans un climat apaisé et s'il l'accepte, **sans craindre qu'il "
         "« s'habitue aux bras »**.",
         "Il ne cherche pas à interrompre les pleurs avec une tétine ou un doudou : ces objets ne "
         "remplacent pas la présence de l'adulte.",
         "Quand les pleurs sont intenses et répétés, il cherche la cause du côté du lieu d'accueil "
         "autant que de l'enfant : bruit, lumière, ruptures dans le planning, manque de "
         "disponibilité, tension dans l'équipe."]},

 {"t": "Les interactions entre enfants",
  "ret": "Les conflits ne se règlent pas de façon punitive. Pas de reproche à l'enfant qui initie le "
         "conflit : le professionnel se place en médiateur.",
  "p": ["Chez les tout-petits, le conflit autour d'un jouet et l'imitation joyeuse sont le même "
        "processus : découvrir l'autre en s'identifiant à lui. Un conflit, c'est de « l'imitation "
        "empêchée », pas de l'agressivité. L'enfant n'est ni égoïste ni méchant : il ne comprend pas "
        "encore les désirs de l'autre."],
  "li": ["Il prévoit **plusieurs jeux identiques** (même forme, même couleur) : cela facilite "
         "l'imitation et diminue les conflits.",
         "Il ne dit pas « tu n'es pas gentil » ; il explique et cherche une solution : « je vois que "
         "tu veux faire comme lui, mais il a encore envie de jouer, on va chercher comment faire ».",
         "Il rappelle la règle calmement, montre comment agir autrement, nomme l'émotion.",
         "Il relève et encourage le comportement adapté quand il apparaît (demander le jouet au lieu "
         "de l'arracher)."]},

 {"t": "Le cadre, les repères et les interdits",
  "ret": "Le cadre n'a pas pour fonction de discipliner mais de sécuriser. Le professionnel fait "
         "régulièrement le compte des interdits qu'il formule, et se demande s'ils répondent aux "
         "besoins de l'enfant ou aux attentes de l'adulte.",
  "p": ["L'enfant a besoin d'entendre la même règle de tous les adultes. Lorsqu'une limite est "
        "posée, il lui faut un délai pour l'intégrer et l'appliquer. L'enfant ne fait pas de "
        "caprices : dans sa colère il exprime un besoin frustré et une incapacité, à ce stade, à "
        "contrôler sa frustration."],
  "li": ["Il formule l'interdit **de façon affirmative** : « descends de la table » plutôt que « ne "
         "monte pas sur la table » — la forme négative est plus difficile à comprendre.",
         "Il explique les raisons des interdits **en dehors** des moments où ils sont franchis.",
         "Il compte ses interdits, particulièrement ceux qui touchent à la motricité (ne pas courir, "
         "ne pas grimper, ne pas jeter), et cherche à les réduire.",
         "Il ne pose pas comme objectif la discipline, la « maîtrise » ou le calme : ces objectifs "
         "ne correspondent ni aux besoins ni aux capacités d'un enfant de moins de 3 ans.",
         "**L'expression des émotions ne fait jamais l'objet d'un interdit** : la colère peut "
         "s'exprimer, le professionnel propose seulement une façon de le faire sans casser ni blesser.",
         "Les moments de repas, change et sommeil ne donnent pas lieu à des règles rigides."]},

 {"t": "Le sommeil",
  "ret": "L'enfant n'est jamais forcé à aller au lit, mais on le lui propose chaque jour. La sieste "
         "peut se faire à l'extérieur ou dans la salle de vie. On ne demande pas aux parents qui "
         "endorment leur enfant dans les bras de cesser cette pratique.",
  "p": ["Les espaces de sommeil ne sont pas dans l'obscurité totale, mais à la lumière du jour "
        "tamisée. Le sommeil se prépare par des rituels quotidiens : temps calmes, comptines, voix "
        "basse, respiration, musique lente, massage du visage, histoire redondante lue en chuchotant.",
        "**Repères de durée.** 15 à 17 h par 24 h à la naissance · 12 à 15 h entre 4 et 11 mois · "
        "11 à 14 h entre 1 et 2 ans · 10 à 12 h à 3 ans."],
  "li": ["Il ne réveille pas un bébé qui dort. Au-delà de 2 ans, si une sieste trop tardive (après "
         "16 h) ou trop longue gêne la nuit, le réveil peut être induit, au cas par cas avec les "
         "parents.",
         "Il propose le lit chaque jour sans forcer. **Maintenir un enfant au lit de force, par la "
         "voix ou par le geste, est une pratique maltraitante.**",
         "Pour l'enfant qui ne parvient pas à dormir, il renforce la sécurisation affective : temps "
         "individuel, câlins, échanges.",
         "Il installe les enfants au sommeil léger contre un mur, dans un coin, avec vue sur la "
         "porte — jamais au milieu de la pièce.",
         "Il reste disponible pour ceux qui ne dorment pas."]},

 {"t": "L'alimentation",
  "ret": "On ne pousse pas l'enfant à finir son assiette ni à goûter ; on lui repropose "
         "régulièrement, en manifestant le plaisir qu'on a soi-même à manger. L'enfant touche, "
         "goûte, mélange — sans interdit systématique ni réprimande.",
  "p": ["Le repas est un moment de relation, et le plaisir de manger mobilise les cinq sens. C'est "
        "aussi un lieu privilégié d'autonomie : se servir, passer le plat, débarrasser."],
  "li": ["Il laisse manger avec les mains et découvrir les textures avec les doigts.",
         "Il ne demande pas de « respecter la nourriture » : un enfant de moins de 3 ans ne peut pas "
         "le comprendre.",
         "Il présente chaque **nouvel aliment séparément**, sans le mélanger, et le repropose "
         "plusieurs fois sur des repas distincts.",
         "Il ne fait pas de chantage : **ni « encore une petite cuillère pour me faire plaisir », ni "
         "« si tu finis ton assiette, tu auras un dessert »**.",
         "Il accepte l'appréhension de certains aliments, normale surtout vers 2 ans.",
         "Il autorise l'enfant à se lever pendant le repas : rester assis est fatigant à cet âge.",
         "Il nomme et parle des aliments.",
         "L'organisation permet à chacun de manger à son rythme."]},

 {"t": "Le change et la continence",
  "ret": "Le change est un moment de soin intime, mis à profit pour un échange individuel. Il est "
         "fait dès que l'enfant manifeste une gêne. L'enfant n'est jamais contraint dans "
         "l'acquisition de la continence.",
  "p": ["La continence relève d'un processus naturel de maturation : on n'apprend pas à un enfant à "
        "être continent. Le rythme varie d'un enfant à l'autre et n'est pas linéaire — les "
        "régressions font partie du processus. Le respect du développement de l'enfant prime sur les "
        "attentes sociétales ou scolaires."],
  "li": ["Il ne laisse jamais un enfant avec une couche souillée, et ne réprime pas celui qui "
         "demande à aller aux toilettes — **même en pleine activité**.",
         "Il verbalise les soins qu'il prodigue et ce que fait l'enfant.",
         "Il fait du change un moment de relation : regard, parole, jeux, sourires, rires.",
         "Il favorise l'autonomie selon l'âge — change debout, lever la jambe, tenir la couche, "
         "avoir son propre gant — **sans en faire un objectif** : un enfant peut ne pas en avoir "
         "envie ce jour-là.",
         "Il laisse l'enfant participer et regarder (jeter la couche, vider le pot) et répond à ses "
         "questions.",
         "Il ne gronde jamais en cas d'accident."]},

 {"t": "Les sorties quotidiennes en extérieur",
  "ret": "Les enfants sortent chaque jour, quel que soit le temps, hors alerte météo. Les enfants ne "
         "restent pas dans les poussettes pendant les moments de loisirs.",
  "li": ["Il demande aux parents des vêtements adaptés à toutes les saisons : combinaison chaude, "
         "bottes de pluie, chapeau.",
         "En forte chaleur, il sort tôt le matin ou dans des espaces ombragés et aérés.",
         "Il favorise la découverte de milieux naturels variés.",
         "**Il ne laisse pas un enfant assis ou allongé plus d'une heure d'affilée** en dehors du "
         "sommeil et de la sieste."]},

 {"t": "Les arts et les cultures",
  "ret": "L'éveil artistique passe par la pratique de l'enfant. Dans tous les espaces de vie, des "
         "livres adaptés sont en libre accès, à hauteur d'enfant.",
  "sous": [("Le livre et la lecture",
            "Le professionnel laisse l'enfant s'approprier le livre par l'observation et le toucher, "
            "lit à voix haute, met en chanson. Il relit plusieurs fois le même livre — l'enfant a du "
            "plaisir à anticiper la suite. **Les livres ne sont pas rangés hors de portée par "
            "crainte qu'ils soient abîmés.**"),
           ("Les arts plastiques",
            "Peinture, modelage, collage, pliage, construction, avec des matières variées (lisses, "
            "rugueuses, brillantes, mates). Ateliers « fait maison » à base de produits naturels et "
            "biodégradables — pâte à modeler alimentaire, peintures végétales — reproductibles à la "
            "maison, ce qui associe les familles. L'espace est protégé (bâche, tissu) plutôt que "
            "l'activité empêchée ; elle peut se faire dehors."),
           ("La musique",
            "De la musicalité tout au long de la journée — chansons, comptines, jeux de doigts — "
            "selon le besoin du moment : calmer des pleurs, ouvrir un temps collectif, accompagner "
            "l'endormissement. Instruments acoustiques plutôt qu'électroniques, avec un souci de "
            "qualité sonore. Musiques d'autres cultures et d'autres langues, en invitant les parents "
            "à partager la leur.")]},

 {"t": "L'arrivée : familiarisation, doudous et tétines",
  "ret": "Le mot familiarisation est préféré à « adaptation » : il dit qu'on prend le temps de faire "
         "connaissance — l'enfant, les parents et le professionnel.",
  "sous2": [("La familiarisation",
    ["On préfère **la répétition de situations semblables** (même lieu, même personne, même heure) à "
     "une progression par étapes (une heure, puis un repas). La répétition rend l'environnement "
     "prévisible, et c'est ce qui sécurise.",
     "La présence des parents est prolongée, plusieurs heures sur plusieurs jours, et le parent y "
     "est acteur auprès de son enfant.",
     "Pas de protocole rigide : les modalités s'ajustent à chaque enfant et à chaque famille.",
     "Même un enfant déjà accueilli ailleurs recommence **une nouvelle familiarisation**.",
     "Les temps de présence commune ne s'arrêtent pas à la familiarisation."]),
   ("Les doudous et les tétines",
    ["Les doudous sont **à libre disposition**, accessibles seuls ; ils sont donnés aux plus petits "
     "dès qu'ils en manifestent l'envie.",
     "Le doudou **voyage** entre la maison et le lieu d'accueil : il fait le lien entre deux mondes.",
     "Tous les enfants n'ont pas de doudou — cela n'existe pas dans toutes les familles ni dans "
     "toutes les cultures. On n'insiste pas pour que les parents en fournissent un.",
     "La tétine est découragée pendant les temps de veille, surtout en situation de communication : "
     "elle altère l'expression verbale et non verbale.",
     "**Ces objets ne servent jamais à faire taire une émotion.** L'émotion est un signal social qui "
     "appelle d'abord une réponse humaine : l'adulte console par sa présence avant de proposer un "
     "objet."])]},
]


# =============================================================================================
class Doc(FPDF):
    partie = ""

    def header(self):
        if self.page_no() <= 2:
            return
        self.set_font("D", "", 7.5)
        self.set_text_color(*GRIS)
        self.cell(0, 5, "Référentiel d'éveil 0-3 ans — aSchool")
        self.cell(0, 5, self.partie, align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*GRIS_TRAIT)
        self.set_line_width(0.2)
        self.line(self.l_margin, self.get_y() + 0.5, self.w - self.r_margin, self.get_y() + 0.5)
        self.ln(4.5)

    def footer(self):
        """La mention court sur TOUTES les pages, page de titre comprise : un document qui sort
        d'aSchool dit ce qu'il est, où qu'on l'ouvre et quelle que soit la page photocopiée.
        « En service » parce qu'il l'est ; « sans valeur institutionnelle » parce qu'aucune des
        trois sources ne l'a validé — c'est plus juste que « non officiel », qui laisserait
        entendre officieux ou provisoire."""
        self.set_y(-14)
        self.set_font("D", "", 7.5)
        self.set_text_color(*GRIS)
        self.cell(0, 5, "Référentiel maison aSchool — en service, sans valeur institutionnelle")
        self.cell(0, 5, "" if self.page_no() == 1 else str(self.page_no()), align="R")

    # -- briques -------------------------------------------------------------------------------
    def para(self, txt, taille=9.8, inter=5.1, apres=2.6, couleur=ENCRE, gras=False):
        self.set_font("D", "B" if gras else "", taille)
        self.set_text_color(*couleur)
        self.multi_cell(0, inter, txt, new_x="LMARGIN", new_y="NEXT", markdown=True)
        self.ln(apres)

    def puce(self, txt, taille=9.8, inter=5.1, retrait=0.0, signe="•"):
        self.set_font("D", "", taille)
        self.set_text_color(*ENCRE)
        x = self.l_margin + retrait
        self.set_x(x)
        self.cell(4, inter, signe)
        self.set_x(x + 4.5)
        self.multi_cell(self.epw - retrait - 4.5, inter, txt, new_x="LMARGIN", new_y="NEXT",
                        markdown=True)
        self.ln(1.1)

    def rubrique(self, label, txt, retrait=0.0):
        """« Âge : … » — le label et son contenu sur la MÊME ligne logique : c'est ce qui permet à
        l'épuration de les retrouver ensemble."""
        self.set_x(self.l_margin + retrait)
        self.set_font("D", "B", 9.8)
        self.set_text_color(*VIOLET)
        largeur = self.get_string_width(label + " : ") + 0.5
        self.cell(largeur, 5.1, label + " :")
        self.set_font("D", "", 9.8)
        self.set_text_color(*ENCRE)
        self.multi_cell(self.epw - retrait - largeur, 5.1, txt, new_x="LMARGIN", new_y="NEXT",
                        markdown=True)
        self.ln(1.4)

    def encadre(self, titre, corps, fond, trait, couleur_titre, taille=9.3):
        if self.get_y() > self.h - 55:
            self.add_page()
        self.set_fill_color(*fond)
        self.set_draw_color(*trait)
        y0 = self.get_y()
        self.set_y(y0 + 2.5)
        if titre:
            self.set_x(self.l_margin + 4)
            self.set_font("D", "B", 8)
            self.set_text_color(*couleur_titre)
            self.multi_cell(self.epw - 8, 4.4, titre, new_x="LMARGIN", new_y="NEXT")
            self.ln(0.8)
        self.set_x(self.l_margin + 4)
        self.set_font("D", "", taille)
        self.set_text_color(*couleur_titre)
        self.multi_cell(self.epw - 8, 4.9, corps, new_x="LMARGIN", new_y="NEXT", markdown=True)
        y1 = self.get_y() + 2.5
        self.set_line_width(0.3)
        self.rect(self.l_margin, y0, self.epw, y1 - y0, style="D")
        self.set_line_width(0.2)
        self.set_y(y1)
        self.ln(4)

    def titre_partie(self, sur, titre, chapeau):
        self.add_page()
        self.ln(14)
        self.set_font("D", "B", 9)
        self.set_text_color(*VIOLET)
        self.cell(0, 6, sur.upper(), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)
        self.set_font("D", "B", 22)
        self.set_text_color(*ENCRE)
        self.multi_cell(0, 10, titre, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_draw_color(*VIOLET)
        self.set_line_width(1.1)
        y = self.get_y()
        self.line(self.l_margin, y, self.l_margin + 42, y)
        self.set_line_width(0.2)
        self.ln(8)
        self.para(chapeau, taille=10.2, inter=5.6, apres=4, couleur=GRIS)

    def titre_domaine(self, num, nom, apprend):
        if self.get_y() > self.h - 70:
            self.add_page()
        else:
            self.ln(3)
        self.set_fill_color(*VIOLET)
        y = self.get_y()
        self.rect(self.l_margin, y, 9, 9, style="F")
        self.set_xy(self.l_margin, y + 1.3)
        self.set_font("D", "B", 13)
        self.set_text_color(255, 255, 255)
        self.cell(9, 6.4, num, align="C")
        self.set_xy(self.l_margin + 13, y + 0.6)
        self.set_font("D", "B", 14)
        self.set_text_color(*ENCRE)
        self.multi_cell(self.epw - 13, 7.2, "DOMAINE " + num + " — " + nom, new_x="LMARGIN",
                        new_y="NEXT")
        self.ln(2)
        self.set_x(self.l_margin + 13)
        self.set_font("D", "", 9.3)
        self.set_text_color(*GRIS)
        self.multi_cell(self.epw - 13, 4.8, "Ce que l'enfant apprend : " + apprend,
                        new_x="LMARGIN", new_y="NEXT")
        self.ln(1)
        self.set_draw_color(*VIOLET_TRAIT)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(5)

    def fiche(self, f):
        besoin = 42
        if self.get_y() > self.h - besoin:
            self.add_page()
        self.set_font("D", "B", 11.5)
        self.set_text_color(*VIOLET)
        titre = f["t"]
        self.multi_cell(0, 6, titre, new_x="LMARGIN", new_y="NEXT")
        if f.get("st"):
            self.set_font("D", "", 8.5)
            self.set_text_color(*GRIS)
            self.multi_cell(0, 4.2, f["st"], new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        if f.get("age"):
            self.rubrique("Âge", f["age"])
        if f.get("mat"):
            self.rubrique("Matériel", f["mat"])
        if f.get("obj"):
            self.rubrique("Objectifs", f["obj"])
        der = f.get("der")
        if isinstance(der, str):
            self.rubrique("Déroulé", der)
        elif isinstance(der, list):
            self.set_font("D", "B", 9.8)
            self.set_text_color(*VIOLET)
            self.cell(0, 5.1, "Déroulé :", new_x="LMARGIN", new_y="NEXT")
            self.ln(1)
            for tranche, texte in der:
                self.set_x(self.l_margin + 4)
                self.set_font("D", "B", 9.5)
                self.set_text_color(*ENCRE)
                lg = self.get_string_width(tranche + " — ") + 0.5
                self.cell(lg, 5.1, tranche + " —")
                self.set_font("D", "", 9.8)
                self.multi_cell(self.epw - 4 - lg, 5.1, texte, new_x="LMARGIN", new_y="NEXT")
                self.ln(1.1)
            self.ln(0.4)
        if f.get("obs"):
            self.rubrique("À observer", f["obs"])
        if f.get("sec"):
            self.rubrique("Sécurité", f["sec"])
        # La source ne distingue pas les âges sur cette fiche : on le DIT, plutôt que de laisser
        # croire qu'un nourrisson et un enfant de 3 ans reçoivent la même consigne par choix.
        if f.get("nodiff"):
            self.rubrique("Différenciation", "la source donne un déroulé unique pour toute la "
                                             "bande 0-3. Adapter au développement observé : "
                                             "l'écart entre un nourrisson et un enfant de 3 ans "
                                             "est ici à la charge de l'adulte.")
        self.ln(3)
        self.set_draw_color(*GRIS_TRAIT)
        y = self.get_y()
        self.line(self.l_margin, y, self.l_margin + 26, y)
        self.ln(5)

    def fiche2(self, num, f):
        if self.get_y() > self.h - 62:
            self.add_page()
        self.set_font("D", "B", 11.5)
        self.set_text_color(*VIOLET)
        self.multi_cell(0, 6, "Fiche %d — %s" % (num, f["t"]), new_x="LMARGIN", new_y="NEXT")
        self.ln(2.5)
        if f.get("ret"):
            self.encadre("À RETENIR", f["ret"], VIOLET_CLAIR, VIOLET_TRAIT, (49, 46, 129))
        for p in f.get("p", []):
            self.para(p)
        if f.get("li"):
            self.set_font("D", "B", 10)
            self.set_text_color(*ENCRE)
            self.cell(0, 5.5, "Ce que fait le professionnel", new_x="LMARGIN", new_y="NEXT")
            self.ln(1.6)
            for li in f["li"]:
                self.puce(li)
        for nom, corps in f.get("sous", []):
            self.set_font("D", "B", 10)
            self.set_text_color(*ENCRE)
            self.cell(0, 5.5, nom, new_x="LMARGIN", new_y="NEXT")
            self.ln(1.4)
            self.para(corps)
        for nom, items in f.get("sous2", []):
            self.set_font("D", "B", 10)
            self.set_text_color(*ENCRE)
            self.cell(0, 5.5, nom, new_x="LMARGIN", new_y="NEXT")
            self.ln(1.6)
            for it in items:
                self.puce(it)
        self.ln(2)
        self.set_draw_color(*GRIS_TRAIT)
        y = self.get_y()
        self.line(self.l_margin, y, self.l_margin + 26, y)
        self.ln(5)


def construire(sortie):
    d = Doc(format="A4", unit="mm")
    d.set_margins(22, 15, 22)
    d.set_auto_page_break(True, margin=20)
    d.add_font("D", "", TTF)
    d.add_font("D", "B", TTF_B)
    d.set_title("Référentiel d'éveil 0-3 ans — aSchool")
    d.set_author("aSchool")
    d.set_subject("Document de travail non officiel. Partie 1 : activités d'éveil (sources UNICEF). "
                  "Partie 2 : les temps du quotidien (Référentiel national de la qualité d'accueil "
                  "du jeune enfant, avril 2025).")

    # ---------------------------------------------------------------- page de titre
    d.partie = ""
    d.add_page()
    d.ln(46)
    d.set_font("D", "B", 9.5)
    d.set_text_color(*VIOLET)
    d.cell(0, 6, "CRÈCHE · NIVEAU BMG_0-3", new_x="LMARGIN", new_y="NEXT")
    d.ln(4)
    d.set_font("D", "B", 30)
    d.set_text_color(*ENCRE)
    d.multi_cell(0, 13.5, "Référentiel d'éveil\n0-3 ans", new_x="LMARGIN", new_y="NEXT")
    d.ln(4)
    d.set_draw_color(*VIOLET)
    d.set_line_width(1.4)
    y = d.get_y()
    d.line(d.l_margin, y, d.l_margin + 52, y)
    d.set_line_width(0.2)
    d.ln(9)
    d.set_font("D", "", 12)
    d.set_text_color(*GRIS)
    d.multi_cell(0, 6.4, "Activités d'éveil et temps du quotidien pour les professionnels de la "
                         "petite enfance", new_x="LMARGIN", new_y="NEXT")
    d.ln(30)
    d.encadre("RÉFÉRENTIEL MAISON — SANS VALEUR INSTITUTIONNELLE",
              "Ce référentiel est **le référentiel crèche d'aSchool**, élaboré en interne à partir "
              "de trois publications extérieures (voir « Sources & attribution » en fin de "
              "document). Il est **en service** : c'est lui qui sert de base aux contenus produits "
              "pour le niveau BMG_0-3.\n\n"
              "**Il n'a aucune valeur institutionnelle.** Aucune des trois sources ne l'a relu ni "
              "validé, et il n'engage ni l'UNICEF, ni le ministère chargé des Solidarités et des "
              "Familles. La question des droits de réutilisation auprès de l'UNICEF sera traitée "
              "au moment de la diffusion.\n\n"
              "Reprise de l'avertissement UNICEF (Doc 2, p. 2) : « Les opinions et points de vue "
              "exprimés dans le présent document sont entièrement ceux de leurs auteurs et ne "
              "peuvent en aucune manière être attribués au Fonds des Nations Unies pour l'enfance "
              "(UNICEF)… Le texte n'a pas été préparé en conformité avec les normes officielles de "
              "publication. »",
              AMBRE_FOND, AMBRE_TRAIT, AMBRE_TEXTE, taille=8.6)

    # ---------------------------------------------------------------- sommaire
    d.add_page()
    d.ln(6)
    d.set_font("D", "B", 18)
    d.set_text_color(*ENCRE)
    d.cell(0, 10, "Sommaire", new_x="LMARGIN", new_y="NEXT")
    d.ln(4)

    def entree(txt, gras=False, retrait=0.0, gris=False):
        d.set_x(d.l_margin + retrait)
        d.set_font("D", "B" if gras else "", 10.6 if gras else 9.8)
        d.set_text_color(*(GRIS if gris else ENCRE))
        d.multi_cell(0, 6.2 if gras else 5.4, txt, new_x="LMARGIN", new_y="NEXT")

    entree("Préambule", gras=True)
    for x in ["À qui s'adresse ce référentiel", "Le jeu, moteur de l'apprentissage 0-3",
              "Les quatre domaines de développement"]:
        entree(x, retrait=5)
    d.ln(3)
    entree("Première partie — Les activités d'éveil", gras=True)
    for num, nom, _, fiches in DOMAINES:
        entree("Domaine %s — %s (%s)" % (num, nom,
               "1 activité + 1 renvoi" if num == "4" else "%d activités" % len(fiches)), retrait=5)
    entree("À valider — activités affectives et sociales de l'Unité II", retrait=5, gris=True)
    d.ln(3)
    entree("Deuxième partie — Les temps du quotidien", gras=True)
    for i, f in enumerate(P2, 1):
        entree("Fiche %d — %s" % (i, f["t"]), retrait=5)
    d.ln(3)
    entree("Sources & attribution", gras=True)

    # ---------------------------------------------------------------- préambule
    d.partie = "Préambule"
    d.add_page()
    d.ln(4)
    d.set_font("D", "B", 18)
    d.set_text_color(*ENCRE)
    d.cell(0, 10, "Préambule", new_x="LMARGIN", new_y="NEXT")
    d.ln(5)

    d.set_font("D", "B", 12)
    d.set_text_color(*VIOLET)
    d.cell(0, 7, "À qui s'adresse ce référentiel", new_x="LMARGIN", new_y="NEXT")
    d.ln(2.5)
    d.para("Le destinataire est l'adulte qui anime l'éveil des tout-petits : éducateur ou éducatrice "
           "de jeunes enfants, auxiliaire de puériculture, assistant ou assistante maternelle. Le "
           "format des activités est celui d'une activité **animée par l'adulte avec l'enfant** — "
           "pas d'exercices « questions/réponses » adressés à l'enfant.")
    d.para("**Tranches d'âge.** Ce document reprend fidèlement les tranches des sources : Bébés "
           "(0-1 an) et 1-3 ans. Le contenu « 4-6 ans » des sources (maternelle) est écarté, hors "
           "périmètre crèche. Le référentiel ne subdivise pas lui-même la bande 1-3 : les sources ne "
           "la distinguent pas, et aSchool n'invente pas cette finesse. L'âge précis se saisit au "
           "moment de la demande, activité par activité.")
    d.ln(2)

    d.set_font("D", "B", 12)
    d.set_text_color(*VIOLET)
    d.cell(0, 7, "Le jeu, moteur de l'apprentissage 0-3", new_x="LMARGIN", new_y="NEXT")
    d.ln(2.5)
    d.para("Le cerveau grandit plus vite pendant les cinq premières années qu'à tout autre moment. "
           "**C'est par le jeu que les enfants apprennent** : en jouant, ils se servent de tous "
           "leurs sens (ouïe, vue, goût, toucher, odorat, mouvement) pour récolter des informations "
           "sur le monde et se construire.")
    d.para("Le rôle de l'adulte est d'accompagner, parler, écouter, encourager, rassurer — jamais de "
           "punir verbalement ou physiquement. Se mettre à hauteur d'yeux de l'enfant, sourire, "
           "annoncer ce qui va se passer, laisser l'enfant explorer et manipuler.")
    d.para("**Comment utiliser ce référentiel.** Réunir les enfants dans un lieu accueillant et sûr, "
           "en petits groupes par âge quand c'est possible. Installer une routine régulière : les "
           "tout-petits sont rassurés par ce qui est prévisible. Adapter chaque activité à l'âge et "
           "aux intérêts de l'enfant.")
    d.ln(2)

    d.set_font("D", "B", 12)
    d.set_text_color(*VIOLET)
    d.cell(0, 7, "Les quatre domaines de développement", new_x="LMARGIN", new_y="NEXT")
    d.ln(2.5)
    d.para("Les activités développent, souvent en même temps, quatre domaines (source Doc 2, p. ii). "
           "Une même activité en nourrit fréquemment plusieurs ; le domaine secondaire est signalé "
           "par « développe aussi ».")
    for num, nom, apprend, _ in DOMAINES:
        d.set_font("D", "B", 9.8)
        d.set_text_color(*VIOLET)
        lg = d.get_string_width(num + ". " + nom + " — ") + 0.5
        if d.get_y() > d.h - 30:
            d.add_page()
        d.cell(lg, 5.1, num + ". " + nom + " —")
        d.set_font("D", "", 9.8)
        d.set_text_color(*ENCRE)
        d.multi_cell(d.epw - lg, 5.1, apprend, new_x="LMARGIN", new_y="NEXT")
        d.ln(1.6)
    d.ln(2)
    d.encadre("COMMENT LIRE UNE FICHE — ET POURQUOI CERTAINES RUBRIQUES MANQUENT",
              "Chaque activité se lit toujours dans le même ordre : **Âge**, **Matériel** (« aucun » "
              "quand l'activité n'en demande pas), **Objectifs**, **Déroulé**, **À observer**, "
              "**Sécurité**, **Différenciation**.\n\n"
              "Une rubrique absente n'est jamais un oubli : c'est que la source ne la donne pas. "
              "Quatre activités venues du Doc 1 n'ont pas d'**À observer** — ce manuel n'a pas cette "
              "rubrique, il donne « facultés développées » et « ce que vous pouvez faire ». Et "
              "« Créer ses propres livres de lecture » n'a pas d'**Objectifs** : la source la donne "
              "en cinq étapes, sans en énoncer. Rien n'est complété d'invention.",
              GRIS_CLAIR, GRIS_TRAIT, GRIS, taille=8.8)

    d.encadre("SÉCURITÉ — RÈGLE GÉNÉRALE, VALABLE POUR TOUTE ACTIVITÉ",
              "Les consignes de sécurité qui figurent au bas de certaines fiches sont celles que les "
              "sources ont écrites. **Elles sont inégales** : le puzzle à encastrer et le trieur de "
              "formes alertent sur la mise en bouche, le puzzle à anneaux — mêmes petites pièces de "
              "bois, même tranche d'âge — n'en dit rien. Plutôt que d'inventer une consigne source "
              "par source, aSchool pose ici une règle qui les couvre toutes.\n\n"
              "**Toute activité comportant des pièces manipulables — perles, anneaux, cubes, formes, "
              "dominos, cartes, pâte à modeler — se fait sous surveillance permanente d'un adulte, "
              "et la mise en bouche est surveillée jusqu'à ce que l'enfant ne porte plus les objets "
              "à la bouche.** Un enfant n'est jamais laissé seul avec ce matériel. Cette règle "
              "l'emporte sur le silence d'une fiche.",
              AMBRE_FOND, AMBRE_TRAIT, AMBRE_TEXTE, taille=8.8)

    d.encadre("DIFFÉRENCIATION PAR ÂGE — CE QUE LES SOURCES FONT, ET CE QU'ELLES NE FONT PAS",
              "Le niveau crèche est unique (BMG_0-3) : l'âge se précise au moment de la demande, "
              "pas dans le profil. Encore faut-il que le référentiel ait de quoi répondre.\n\n"
              "**Neuf fiches ont deux déroulés distincts** (« Bébés » et « 1-3 ans ») : les sources "
              "les différencient, la réponse changera vraiment selon l'âge demandé.\n\n"
              "**Neuf autres n'ont qu'un déroulé unique** couvrant toute la bande 0-3. Les sources "
              "ne les distinguent pas, et aSchool n'invente pas cette finesse. Ces fiches portent "
              "désormais une rubrique **Différenciation** qui le dit explicitement : l'écart entre "
              "un nourrisson et un enfant de 3 ans y est à la charge de l'adulte.\n\n"
              "**C'est une limite réelle du référentiel**, pas un oubli de mise en forme : pour ces "
              "quinze activités, préciser « bébés » ou « 2 ans et demi » au moment de la demande ne "
              "changera pas la matière disponible. Les dix fiches restantes portent une tranche plus "
              "étroite (1-3 ans, ou dès 2 ans) : la question ne s'y pose pas.",
              GRIS_CLAIR, GRIS_TRAIT, GRIS, taille=8.8)

    d.encadre("ARBITRAGE — QUAND LES DEUX SOURCES SE CONTREDISENT SUR L'ÂGE",
              "Dominos, cubes de construction, cubes-puzzle et jeu de mémoire sont donnés « 1-3 ans » "
              "par le Doc 2, qui leur consacre une fiche dédiée à cette tranche, et « âge "
              "préscolaire (4 à 7-8 ans) » par le Doc 1, dont c'est la seconde série de jouets.\n\n"
              "**Décision : le Doc 2 fait foi sur l'âge.** C'est un guide d'activités bâti tranche "
              "par tranche, avec une fiche par âge et par objet ; le Doc 1 est un manuel "
              "d'intervention en situation d'urgence, dont le classement par âge est secondaire. "
              "Ces quatre activités sont donc retenues en 1-3 ans, en gardant à l'esprit que leur "
              "forme aboutie (compter les points, gagner des paires) relève du haut de la bande.",
              GRIS_CLAIR, GRIS_TRAIT, GRIS, taille=8.8)

    d.encadre("NOTE DE TRANSPARENCE",
              "Le classement des activités par domaine est une mise en ordre éditoriale d'aSchool "
              "(domaine dominant de chaque activité). Le contenu des activités, lui, provient des "
              "sources.", GRIS_CLAIR, GRIS_TRAIT, GRIS, taille=8.8)

    # ---------------------------------------------------------------- partie 1
    d.partie = "Première partie"
    d.titre_partie("Première partie", "Les activités d'éveil",
                   "Vingt-sept activités animées par l'adulte avec l'enfant, classées par domaine "
                   "dominant, plus un renvoi d'un domaine à l'autre. Chacune donne son âge, son matériel, ses objectifs, son déroulé, ce "
                   "qu'il faut observer et, s'il y a lieu, ses consignes de sécurité.")
    for num, nom, apprend, fiches in DOMAINES:
        d.titre_domaine(num, nom, apprend)
        if num == "4":
            d.encadre("CONSTAT HONNÊTE — À NE PAS COMBLER PAR DE L'INVENTION",
                      "Dans les sources, les activités explicitement sociales (« Amis ensemble », "
                      "« Un jouet, deux enfants », « Aider ses partenaires », « Suivez le guide ») "
                      "sont toutes classées 4-6 ans, donc **hors de notre bande 0-3 et écartées**. "
                      "Pour le 0-3, la dimension sociale se développe surtout **à l'intérieur** des "
                      "autres activités : le lien à l'adulte, jouer côte à côte, coopérer sur les "
                      "cubes. On ne fabrique pas de fausses fiches sociales 0-3 que les sources ne "
                      "contiennent pas.", GRIS_CLAIR, GRIS_TRAIT, GRIS, taille=8.8)
        for f in fiches:
            d.fiche(f)

    if d.get_y() > d.h - 80:
        d.add_page()
    d.ln(2)
    d.set_font("D", "B", 13)
    d.set_text_color(*ENCRE)
    d.multi_cell(0, 7, "À valider — activités affectives et sociales de l'Unité II",
                 new_x="LMARGIN", new_y="NEXT")
    d.ln(2.5)
    d.encadre("EN ATTENTE DE DÉCISION — NON INTÉGRÉ AUX DOMAINES",
              "Ces activités viennent de l'Unité II (psychosociale) du Doc 1. Elles sont fortement "
              "teintées « situation d'urgence / trauma » dans la source. Reformulées pour un cadre "
              "d'éveil ordinaire, plusieurs sont pertinentes pour le 0-3, surtout en Domaine 3 et "
              "en Domaine 4. Elles ne sont pas intégrées aux domaines ci-dessus : elles sont listées "
              "pour que soit décidé lesquelles garder avant de les reformuler proprement.",
              AMBRE_FOND, AMBRE_TRAIT, AMBRE_TEXTE, taille=8.8)
    for it in A_VALIDER:
        d.puce(it)

    # ---------------------------------------------------------------- partie 2
    d.partie = "Deuxième partie"
    d.titre_partie("Deuxième partie", "Les temps du quotidien",
                   "Les activités de la première partie ne se déroulent pas dans le vide. Elles "
                   "s'insèrent dans une journée faite de repas, de siestes, de changes, de pleurs, "
                   "d'arrivées et de départs — et c'est là que se joue l'essentiel du métier.")
    d.para("Cette partie ne contient pas d'activités à animer. Elle donne le **cadre de conduite "
           "professionnelle** dans lequel toute activité prend place. Elle est de nature différente "
           "de la première partie et doit être lue comme telle : des principes et des pratiques, pas "
           "des déroulés.")
    d.ln(1)
    d.encadre("DEUX RÈGLES TRAVERSENT TOUT LE DOCUMENT OFFICIEL ET VALENT POUR CHAQUE FICHE",
              "**Aucune pratique de forçage.** Ni pour manger, ni pour dormir, ni pour la "
              "continence. Le forçage — par la voix intimidante comme par le geste — est qualifié de "
              "pratique maltraitante.\n\n"
              "**Aucune punition.** Paroles dévalorisantes, coin, isolement : proscrits par la loi, "
              "et contre-productifs. Le professionnel peut se mettre à l'écart **avec** l'enfant "
              "pour l'apaiser ; il ne met jamais l'enfant à l'écart seul.",
              VIOLET_CLAIR, VIOLET_TRAIT, (49, 46, 129), taille=9)
    for i, f in enumerate(P2, 1):
        d.fiche2(i, f)

    # ---------------------------------------------------------------- sources
    d.partie = "Sources"
    d.add_page()
    d.ln(4)
    d.set_font("D", "B", 18)
    d.set_text_color(*ENCRE)
    d.cell(0, 10, "Sources & attribution", new_x="LMARGIN", new_y="NEXT")
    d.ln(5)
    d.para("Ce référentiel de travail est une compilation et une adaptation aSchool des trois "
           "publications suivantes, dont il reprend le contenu pédagogique. Rien n'y a été inventé : "
           "aucune activité, aucune pratique, aucune tranche d'âge élargie au-delà de ce que les "
           "sources énoncent.")
    d.ln(2)

    for etiquette, titre, detail, statut in [
        ("DOC 2 — UNICEF",
         "Le kit pour le développement de la petite enfance — Guide d'activités : une boîte à "
         "trésors pleine d'activités",
         "UNICEF, unité du Développement de la petite enfance, avec Cassie Landers, consultante ; "
         "illustrations de Joan Auclair. Prototype non préparé selon les normes officielles de "
         "publication de l'UNICEF.",
         "Périmètre repris : les 22 activités marquées « Bébés » ou « 1-3 ans ». Les 6 marquées "
         "« 4-6 ans » sont écartées."),
        ("DOC 1 — UNICEF",
         "Manuel d'activité pour le développement de la petite enfance — Module III",
         "In Manuel Éducation en situation d'urgence et de crise (ESU), Kits d'éducation de "
         "l'UNICEF, Division des approvisionnements (WSEC), Copenhague. Auteur : Miresi Busana, "
         "1ʳᵉ édition, 2013.",
         "Périmètre repris : Unité I / Activité II (activités manuelles et artistiques, de jeu, "
         "d'expression et de lecture). Unités III (protection) et IV (mines, catastrophes, hygiène "
         "de survie, paix) écartées, hors périmètre éveil. Unité II (psychosociale) : voir la "
         "section « À valider »."),
        ("DOC 3 — ÉTAT FRANÇAIS",
         "Référentiel national de la qualité d'accueil du jeune enfant",
         "Avril 2025. Ministère du Travail, de la Santé, des Solidarités et des Familles. "
         "Élaboration pilotée par l'Inspection générale des affaires sociales : Dr Nicole Bohic, "
         "inspectrice générale des affaires sociales, et Jean-Baptiste Frossard, directeur de projet "
         "à l'IGAS. Deux ans de travaux, 7 groupes de travail, près de 2 000 professionnels "
         "consultés. Base légale : article L214-1-1 du code de l'action sociale et des familles.",
         "Périmètre repris : 12 fiches de sa partie 1 (la relation au jeune enfant), celles qui "
         "touchent au métier d'éveil. Ses parties 2 (relation aux parents) et 3 (organisation, "
         "management, locaux) sont écartées. Document public librement réutilisable : le ministère "
         "invite explicitement à le diffuser et à le compléter."),
    ]:
        if d.get_y() > d.h - 62:
            d.add_page()
        d.set_font("D", "B", 8.5)
        d.set_text_color(*VIOLET)
        d.cell(0, 5, etiquette, new_x="LMARGIN", new_y="NEXT")
        d.ln(0.8)
        d.set_font("D", "B", 10.5)
        d.set_text_color(*ENCRE)
        d.multi_cell(0, 5.4, titre, new_x="LMARGIN", new_y="NEXT")
        d.ln(1.4)
        d.set_font("D", "", 9.2)
        d.set_text_color(*GRIS)
        d.multi_cell(0, 4.9, detail, new_x="LMARGIN", new_y="NEXT")
        d.ln(1.6)
        d.set_font("D", "", 9.2)
        d.set_text_color(*ENCRE)
        d.multi_cell(0, 4.9, statut, new_x="LMARGIN", new_y="NEXT")
        d.ln(6)

    if d.get_y() > d.h - 42:
        d.add_page()
    d.encadre("STATUTS JURIDIQUES — ILS NE SONT PAS LES MÊMES",
              "Les Doc 1 et Doc 2 sont des publications de l'UNICEF : leur réutilisation reste à "
              "traiter au moment de la diffusion. Le Doc 3 est un document public de l'État français, "
              "librement réutilisable, dont la diffusion est explicitement encouragée. Cette "
              "différence doit être conservée si le document venait à être diffusé hors d'aSchool.",
              AMBRE_FOND, AMBRE_TRAIT, AMBRE_TEXTE, taille=8.8)

    d.ln(2)
    d.set_font("D", "", 8.5)
    d.set_text_color(*GRIS)
    d.multi_cell(0, 4.8, "Référentiel maison aSchool, en service · sans valeur institutionnelle · "
                         "attribution UNICEF et État français · droits UNICEF à traiter à la diffusion.",
                 new_x="LMARGIN", new_y="NEXT", align="C")

    d.output(sortie)
    print("OK — %s · %d pages" % (sortie, d.page_no()))


if __name__ == "__main__":
    import sys
    construire(sys.argv[1] if len(sys.argv) > 1 else "/tmp/referentiel.pdf")
