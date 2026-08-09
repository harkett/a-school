# -*- coding: utf-8 -*-
"""Bloc 1 — LES ACTIVITÉS D'ÉVEIL, croisées entre le Doc 1 et le Doc 2.

Ces deux sources décrivent les MÊMES objets (le kit de DPE de l'UNICEF) mais pas de la même
façon : le Doc 2 donne une fiche par tranche d'âge (Que faire / Qu'observer / Prolongements /
Attention), le Doc 1 donne une fiche par activité (Matériel / Âge / Facultés développées / Ce que
vous pouvez faire) et y ajoute des activités que le Doc 2 n'a pas. Chaque entrée ci-dessous est
UNE activité, nourrie des deux quand les deux en parlent — c'est ce croisement qui manquait.

`forme` reprend le mot de la source, jamais un mot à moi : c'est ce champ que le prompt des types
lira. `developpe` reprend les facultés telles que les sources les énoncent : c'est ce champ que le
prompt des matières lira. Aucune classification n'est imposée par le plan du document.
"""

EVEIL = [
 {"titre": "Puzzle à encastrer",
  "forme": "activité avec matériel du kit · jeu avec un jouet",
  "age": "Bébés (0-1 an) · 1-3 ans",
  "materiel": "puzzle à encastrer sans boutons",
  "developpe": "Se servir de ses yeux avant de tendre la main et de saisir ; reconnaître formes, "
               "tailles et couleurs ; réfléchir et raisonner ; coordination œil-main.",
  "faire": [
    ("Bébés", ["Laisser le bébé sortir les pièces, les tenir, les taper l'une contre l'autre ou "
               "sur le sol — le bruit lui plaît.",
               "Le laisser explorer chaque pièce et le contour du trou où l'insérer.",
               "Observer comment il fait le lien entre la pièce et son trou.",
               "Encourager à haute voix, nommer les couleurs et les formes.",
               "Cacher une pièce sous un tissu, expliquer ce qu'on fait, lui demander de la trouver.",
               "Inventer une histoire à propos des pièces."]),
    ("1-3 ans", ["Expliquer que les pièces ont des tailles et des formes différentes : certaines "
                 "ont des bosses et des coins arrondis, d'autres des côtés bien droits.",
                 "Demander à un enfant ou à un groupe de faire le puzzle aussi vite que possible.",
                 "Puis leur demander de se souvenir dans quel trou chaque pièce s'encastre."]),
  ],
  "observer": ["Les pièces, par leurs formes et leurs couleurs, affinent l'usage du regard avant la "
               "préhension.",
               "Les enfants sont calmes et concentrés : le puzzle est une occasion de réfléchir et "
               "de raisonner."],
  "securite": ["Veiller à ce que l'enfant ne porte pas les pièces à la bouche."],
  "source": "Doc 2, fiche 1 · Doc 1, Activité avec jouet 1"},

 {"titre": "Puzzle à anneaux",
  "forme": "activité avec matériel du kit · jeu avec un jouet",
  "age": "Bébés (0-1 an) · 1-3 ans",
  "materiel": "puzzle à anneaux",
  "developpe": "Attraper et tenir des objets de formes et de textures différentes ; démonter et "
               "assembler ; commencer à compter ; montrer les couleurs du doigt ; écouter une "
               "histoire simple.",
  "faire": [
    ("Bébés", ["Placer les pièces détachées devant le bébé, le laisser les attraper et les tenir. "
               "Peut-il en prendre une dans chaque main ?",
               "Les frapper l'une contre l'autre, écouter le bruit.",
               "Parler des couleurs du puzzle.",
               "Cacher une pièce sous un bout de tissu, expliquer, lui demander de la trouver.",
               "Assembler les pièces sous ses yeux.",
               "Inventer une histoire : est-ce qu'on dirait un bateau ? un oiseau ? où va-t-il ?"]),
    ("1-3 ans", ["Laisser jouer librement, démonter le puzzle et le refaire.",
                 "Parler des couleurs de chaque pièce : « Tu peux trouver la rouge ? Ajoutons la "
                 "verte à la chaîne. » Parler aussi des couleurs des vêtements.",
                 "Compter chaque pièce pendant que l'enfant les assemble.",
                 "Faire une chaînette de trois anneaux, montrer chaque pièce en disant son numéro, "
                 "répéter avec des chaînettes de tailles différentes.",
                 "Inventer une chanson à compter ou une comptine sur les couleurs.",
                 "Démanteler le puzzle, mettre les pièces dans une boîte vide, laisser l'enfant la "
                 "vider puis lui demander de la remplir."]),
  ],
  "observer": ["Les bébés attrapent un objet, trouvent un objet caché sous un tissu, tiennent deux "
               "petits objets en même temps, écoutent une histoire simple.",
               "Les enfants démontent et remontent, chantent des bouts de chanson, suivent des "
               "instructions simples, comprennent un et deux, essaient de compter, montrent du "
               "doigt les couleurs qu'on nomme."],
  "securite": ["Veiller à ce que l'enfant ne porte pas les pièces à la bouche."],
  "source": "Doc 2, fiche 2 · Doc 1, Activité avec jouet 2"},

 {"titre": "Imagier",
  "forme": "activité avec matériel du kit · activité de lecture",
  "age": "Bébés (0-1 an) · 1-3 ans",
  "materiel": "imagier (livre d'images cartonné)",
  "developpe": "Éveil du langage et de la curiosité ; détente physique, mentale et émotionnelle ; "
               "relation de confiance avec l'adulte.",
  "faire": [
    ("Bébés", ["Parler le plus possible au bébé.",
               "Écouter les sons qu'il fait et lui répondre.",
               "Parler des dessins qu'il voit, l'aider à tourner les pages : « Qu'est-ce qui vient "
               "après, à ton avis ? Tu peux tourner la page pour voir ? »",
               "Changer souvent d'image. De un à trois mois, le bébé distingue mieux les images à "
               "20 à 30 cm ; à trois mois son champ de vision s'élargit.",
               "Répéter lentement les mots correspondant aux images, lui laisser voir le mouvement "
               "des lèvres."]),
    ("1-3 ans", ["Regarder l'imagier avec un ou plusieurs enfants.",
                 "Poser des questions simples sur les images pour les aider à utiliser certains "
                 "mots ou à montrer qu'ils les comprennent.",
                 "Montrer l'image du doigt en prononçant le mot avec eux.",
                 "Leur demander de montrer certaines images ; s'ils n'y arrivent pas, chercher "
                 "ensemble.",
                 "Nommer une chose vue sur la page pour éveiller leur curiosité.",
                 "Parler des couleurs, compter les objets du livre ou ceux qu'ils préfèrent.",
                 "Inventer des histoires à partir des différentes images."]),
  ],
  "observer": ["Le bébé se détend physiquement, mentalement et émotionnellement ; il est poussé à "
               "échanger avec l'adulte, ce qui développe sa curiosité.",
               "L'enfant a la curiosité en éveil, tourne des pages, apprend de nouvelles choses."],
  "prolongements": ["Copier les images de l'imagier et inviter les enfants à les colorier.",
                    "Faire travailler différents groupes sur différentes histoires."],
  "source": "Doc 2, fiche 3 · Doc 1, Activité de lecture 1"},

 {"titre": "Balles en éponge",
  "forme": "activité avec matériel du kit · activité récréative",
  "age": "Bébés (0-1 an) · 1-3 ans",
  "materiel": "balles en éponge",
  "developpe": "Motricité, contrôle du mouvement, renforcement musculaire ; concentration et "
               "précision ; curiosité ; jeu avec l'adulte et avec les autres.",
  "faire": [
    ("Bébés", ["Faire rouler une balle vers le bébé, le laisser observer comment elle roule.",
               "Le laisser toucher et tenir la balle : c'est par le toucher qu'il appréhende le "
               "monde.",
               "Lui faire toucher la balle molle, ce qui l'incite à bouger et à exercer ses "
               "muscles."]),
    ("1-3 ans", ["Cacher partiellement la balle tout près de l'enfant, l'encourager à la trouver ; "
                 "une fois le jeu compris, la cacher complètement.",
                 "Faire rouler la balle vers lui, lui demander de la renvoyer, rire avec lui.",
                 "Le laisser taper dans la balle, la lancer, la rattraper.",
                 "S'asseoir en rond, faire rouler la balle vers un enfant et lui demander de la "
                 "renvoyer, inciter tout le groupe à participer."]),
  ],
  "observer": ["Le bébé améliore sa motricité en manipulant la balle, exerce sa curiosité, "
               "communique avec l'adulte.",
               "L'enfant se baisse pour ramasser la balle, apprend la concentration et la "
               "précision, joue avec les autres."],
  "source": "Doc 2, fiche 4 · Doc 1, Activité récréative 4"},

 {"titre": "Trieur de formes",
  "forme": "activité avec matériel du kit · jeu avec un jouet",
  "age": "Bébés (0-1 an) · 1-3 ans",
  "materiel": "trieur de formes (boîte à formes)",
  "developpe": "Coordination œil-main et habileté gestuelle ; noms des couleurs et des formes ; "
               "orientation spatiale ; relations de cause à effet.",
  "faire": [
    ("Bébés", ["Placer le trieur et les formes colorées devant le bébé, le laisser jouer librement.",
               "Lui parler de ce qu'il est en train de faire pendant qu'il manipule.",
               "Le laisser découvrir comment ouvrir la boîte ; la vider et lui demander de la "
               "remplir à nouveau.",
               "Nommer la forme qu'il manipule et l'inciter à trouver le trou correspondant."]),
    ("1-3 ans", ["Pendant qu'ils jouent avec les formes et les laissent tomber, les laisser "
                 "explorer comment chaque pièce s'encastre dans son trou.",
                 "Nommer la forme que l'enfant manipule et lui demander de trouver le bon trou.",
                 "Les laisser apprendre à tourner la main et le poignet pour encastrer une pièce."]),
  ],
  "observer": ["Le bébé améliore sa coordination oculo-manuelle et sa motricité.",
               "L'enfant apprend le nom des couleurs et des formes, comprend mieux l'orientation "
               "spatiale et les relations de cause à effet."],
  "securite": ["Ne jamais laisser un bébé seul avec le trieur ; veiller à ce qu'il ne porte pas "
               "les pièces à la bouche."],
  "source": "Doc 2, fiche 5 · Doc 1, Activité avec jouet 3"},

 {"titre": "Papier et crayons",
  "forme": "activité avec matériel du kit · activité manuelle et artistique",
  "age": "Bébés (0-1 an) · 1-3 ans",
  "materiel": "papier, gros crayons cire pour les petits, crayons de couleur",
  "developpe": "Curiosité ; expression par le dessin ; créativité et dextérité ; reconnaissance "
               "des couleurs et des formes.",
  "faire": [
    ("Bébés", ["Découper des formes (ronds, triangles, carrés) de tailles différentes dans du "
               "papier de couleur, percer un trou dans chacune, les enfiler sur un ruban vif et "
               "les suspendre de façon que le bébé puisse les regarder bouger.",
               "Parler des couleurs et des formes pendant qu'il les regarde bouger."]),
    ("1-3 ans", ["Donner de grands crayons et du papier, les laisser trouver la façon la plus "
                 "confortable de tenir le crayon.",
                 "Les laisser dessiner ce qu'ils veulent.",
                 "Si possible, afficher les dessins au mur."]),
  ],
  "observer": ["Le bébé aiguise sa curiosité, essaie de toucher, d'attraper ou de tirer les objets "
               "suspendus, sourit et gazouille.",
               "L'enfant s'exprime à travers le dessin, aiguise sa créativité et sa dextérité, "
               "apprend à reconnaître les couleurs et les formes."],
  "source": "Doc 2, fiche 6"},

 {"titre": "Perles à enfiler",
  "forme": "activité avec matériel du kit · jeu avec un jouet",
  "age": "Bébés (0-1 an) · 1-3 ans",
  "materiel": "perles à enfiler et cordelettes",
  "developpe": "Coordination œil-main ; distinction des couleurs et des formes ; motricité fine et "
               "dextérité ; manipulation de petits objets.",
  "faire": [
    ("Bébés", ["Nouer des perles de tailles et de couleurs différentes au bout de plusieurs "
               "cordelettes, bien serrer pour qu'elles ne se détachent pas.",
               "Déposer une cordelette devant le bébé assis, lui montrer comment tirer dessus pour "
               "faire glisser le jouet vers lui.",
               "Lui donner la cordelette et lui parler de ce qu'il fait.",
               "On peut suspendre des perles de formes et de couleurs variées au-dessus de "
               "l'endroit où il dort, pour le stimuler quand il est réveillé."]),
    ("1-3 ans", ["Mettre quelques perles colorées à leur portée pour qu'ils jouent librement.",
                 "Encourager chacun à les enfiler par couleur ou par forme.",
                 "Compter avec l'enfant combien de perles il a enfilées.",
                 "Le féliciter pour le bracelet ou le collier qu'il a fabriqué."]),
  ],
  "observer": ["Le bébé essaie de toucher, d'attraper ou de tirer la cordelette, exprime sa joie, "
               "sourit et gazouille.",
               "L'enfant apprend à distinguer les couleurs, améliore sa motricité et sa dextérité."],
  "securite": ["La supervision d'un adulte est indispensable dès qu'on joue avec des perles et du "
               "fil."],
  "source": "Doc 2, fiche 7 · Doc 1, Activité avec jouet 4"},

 {"titre": "Marionnettes",
  "forme": "activité avec matériel du kit · activité d'expression",
  "age": "Bébés (0-1 an) · 1-3 ans",
  "materiel": "marionnettes à mains et à doigts",
  "developpe": "Sécurité affective ; imagination ; expression de ce qu'on ressent ; interaction "
               "avec les pairs et les adultes ; mise en mots de situations difficiles.",
  "faire": [
    ("Bébés", ["Enfiler une marionnette sur sa main et la faire parler au bébé ; changer de voix "
               "quand c'est elle qui parle ; lui faire dire qui elle est.",
               "Laisser le bébé la toucher pendant qu'elle parle, rire et s'amuser, le laisser "
               "jouer avec elle."]),
    ("1-3 ans", ["Se servir de marionnettes animales pour parler et chanter : parler de l'animal, "
                 "de son nom, du cri qu'il pousse. Inventer des chansons — « Où est le chat ? Le "
                 "voilà. Que dit-il ? Miaou, miaou. »",
                 "Faire poser par la marionnette des questions auxquelles l'enfant sait répondre : "
                 "son nom, ses vêtements, les parties de son corps.",
                 "Les laisser jouer eux-mêmes avec les marionnettes et inventer leurs propres "
                 "histoires et chansons."]),
  ],
  "observer": ["Le bébé se sent en sécurité avec une gentille marionnette qu'il manipule lui-même ; "
               "celui qui craint le danger peut surmonter sa peur en jouant des scènes "
               "réconfortantes ; il identifie souvent la marionnette à lui-même ou à la personne "
               "qui le réconforte.",
               "L'enfant parle aux marionnettes et apprend à s'en occuper comme d'une amie ; elles "
               "lui permettent d'exprimer son sentiment d'impuissance et parfois de trouver "
               "lui-même la solution à ses problèmes."],
  "securite": ["Veiller à ce que les marionnettes soient adaptées à la culture : dans certaines, "
               "des animaux sont sacrés ou bannis et ne conviennent pas au jeu."],
  "source": "Doc 2, fiche 8 · Doc 1, Activité théâtrale 1"},

 {"titre": "Ensemble d'objets à trier et empiler",
  "forme": "activité avec matériel du kit · jeu avec un jouet",
  "age": "Bébés (0-1 an) · 1-3 ans",
  "materiel": "ensemble d'objets à trier et à empiler (boîtes gigognes)",
  "developpe": "Poser un objet sur un autre ; comparer tailles, formes et couleurs ; imiter ; "
               "trier ; s'intéresser à une activité nouvelle.",
  "faire": [
    ("Bébés", ["Déposer un objet devant le bébé et en poser un autre dessus pendant qu'il regarde.",
               "Lui donner un autre objet à poser dessus.",
               "Expliquer ce qu'on est en train de faire.",
               "Lui laisser le temps d'explorer librement le matériel."]),
    ("1-3 ans", ["Poser les objets au milieu de la pièce et laisser les enfants jouer librement ; "
                 "regarder comment ils explorent un objet nouveau.",
                 "Les laisser empiler à leur manière — peu importe que ce ne soit pas dans l'ordre, "
                 "cela viendra plus tard.",
                 "Parler de l'aspect des objets : couleur, taille, forme, grands et petits. Montrer "
                 "comment les empiler et voir s'ils imitent.",
                 "Choisir un objet et voir s'ils en trouvent un semblable ; leur demander de "
                 "trouver tous les objets d'une même couleur."]),
  ],
  "observer": ["Le bébé pose des objets l'un sur l'autre et montre de l'intérêt pour une activité "
               "nouvelle.",
               "L'enfant imite, remarque les différences de taille, compare le plus grand et le "
               "plus petit, trie quand c'est facile."],
  "source": "Doc 2, fiche 9 · Doc 1, Activité avec jouet 5"},

 {"titre": "Dominos",
  "forme": "activité avec matériel du kit · jeu avec un jouet",
  "age": "1-3 ans",
  "materiel": "kit de dominos",
  "developpe": "Reproduire une forme ; compter les points et retrouver le même nombre ; nommer les "
               "chiffres.",
  "faire": [
    ("1-3 ans", ["Laisser les enfants jouer librement avec les dominos et leur poser des questions "
                 "sur ce qu'ils font : ils peuvent les empiler, les aligner, faire des formes.",
                 "Créer des formes ou des dessins avec une série de dominos et leur demander de "
                 "les reproduire.",
                 "Compter le nombre de points sur un domino et leur demander d'en trouver un autre "
                 "portant le même nombre de points sur une de ses faces."]),
  ],
  "observer": ["L'enfant reproduit une forme, compte les points et retrouve le même nombre "
               "ailleurs, nomme les chiffres."],
  "source": "Doc 2, fiche 10 · Doc 1, Activité avec jouet 4 (dominos)"},

 {"titre": "Cubes de construction",
  "forme": "activité avec matériel du kit · jeu avec un jouet",
  "age": "1-3 ans",
  "materiel": "cubes de construction de couleur",
  "developpe": "Nom des couleurs ; coordination oculo-manuelle ; motricité et dextérité ; "
               "conversation, imagination, plan, équilibre, coopération.",
  "faire": [
    ("1-3 ans", ["Déposer une série de cubes de couleur là où les enfants peuvent jouer librement ; "
                 "les laisser tout déverser en tas et jouer comme ils le veulent.",
                 "Quand un enfant prend un cube, lui parler de sa couleur et de sa forme, lui "
                 "demander d'en choisir un autre de même forme et de même couleur ; s'il en choisit "
                 "un différent, nommer la couleur et la forme de celui qu'il vient de prendre."]),
  ],
  "observer": ["L'enfant apprend le nom des couleurs, améliore sa coordination oculo-manuelle, "
               "affine sa motricité et sa dextérité."],
  "prolongements": ["Marcher sur un chemin tracé par les cubes pour travailler les termes de "
                    "position ; transporter des cubes d'un bout à l'autre de la pièce pour "
                    "l'équilibre ; inventer ensemble une histoire sur ce qui a été construit."],
  "securite": ["Poser une règle simple pour que tout le monde soit en sécurité : « on ne jette pas "
               "les cubes »."],
  "source": "Doc 2, fiche 11 et p. ii · Doc 1, Activité avec jouet 6"},

 {"titre": "Pâte à modeler",
  "forme": "activité avec matériel du kit · activité manuelle et artistique",
  "age": "Bébés (0-1 an) · 1-3 ans",
  "materiel": "pâte à modeler ; éléments naturels (coquillages, feuilles, brindilles) en "
              "prolongement",
  "developpe": "Créativité ; manipulation et toucher ; création de formes et de silhouettes ; "
               "coordination oculo-manuelle ; nom des couleurs.",
  "faire": [
    ("Bébés", ["Laisser simplement le bébé tâter la pâte à modeler avec les mains : l'activité "
               "vise à stimuler le toucher."]),
    ("1-3 ans", ["Sortir de la pâte à modeler de couleur et les laisser créer formes et silhouettes, "
                 "jouer librement, explorer cette matière nouvelle.",
                 "Les inciter à expérimenter en combinant la pâte avec des éléments naturels — "
                 "coquillages, feuilles, brindilles — ou recyclés — capsules, bouteilles.",
                 "Mettre une histoire en scène : reproduire avec la pâte les personnages d'une "
                 "histoire favorite, puis créer des dialogues entre eux ; façonner aussi voitures, "
                 "arbres et maisons à l'appui du récit."]),
  ],
  "observer": ["L'enfant apprend le nom des couleurs, améliore sa coordination oculo-manuelle, "
               "affine sa dextérité et sa créativité."],
  "securite": ["Veiller à ce que l'enfant ne porte pas la pâte à modeler à la bouche et ne "
               "l'ingère pas."],
  "source": "Doc 2, fiche 12 · Doc 1, Activité artistique 2"},

 {"titre": "Cubes puzzle",
  "forme": "activité avec matériel du kit · jeu avec un jouet",
  "age": "1-3 ans",
  "materiel": "cubes-puzzle (images sur les faces)",
  "developpe": "Réfléchir et raisonner ; concentration ; reconstituer une image.",
  "faire": [
    ("1-3 ans", ["Expliquer que ces cubes ont des images sur les côtés et qu'on peut les assembler "
                 "de façon à former une nouvelle image.",
                 "Laisser un enfant ou un groupe assembler le puzzle.",
                 "Former un groupe et les encourager à le terminer aussi vite que possible, en "
                 "faisant participer tout le monde."]),
  ],
  "observer": ["Les enfants sont calmes et concentrés mais leur cerveau fonctionne : le puzzle est "
               "une occasion de réfléchir et de raisonner."],
  "source": "Doc 2, fiche 13 · Doc 1, Activité avec jouet 7"},

 {"titre": "Jeu de mémoire",
  "forme": "activité avec matériel du kit · jeu avec un jouet",
  "age": "1-3 ans",
  "materiel": "cartes du jeu de mémoire",
  "developpe": "Reconnaître les similarités et les différences ; imagination ; connaissance du "
               "monde environnant ; langage autour des images.",
  "faire": [
    ("1-3 ans", ["Laisser les enfants déverser toutes les cartes en tas et jouer avec.",
                 "Les laisser fourrager dans le tas et trouver les cartes qui vont ensemble.",
                 "Leur demander quelles cartes ils préfèrent et pourquoi ; les encourager à parler "
                 "des images et à jouer librement."]),
  ],
  "observer": ["L'enfant s'intéresse au jeu et veut en savoir plus sur les cartes ; il apprend des "
               "choses sur son environnement et aiguise son imagination grâce aux images."],
  "source": "Doc 2, fiche 14"},
]
