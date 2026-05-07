"""
Seed — Exemples A-SCHOOL
Crée le compte démo et insère 2 activités d'exemple par matière (24 au total).
Toutes partagées = True → visibles dans la Bibliothèque de tous les profs.
Idempotent : ne recrée pas ce qui existe déjà.
Pour masquer les exemples : désactiver le compte demo@aschool.fr dans AdminProfils.
"""
import bcrypt

DEMO_EMAIL = "demo@aschool.fr"
DEMO_PRENOM = "Équipe A-SCHOOL"

EXEMPLES = [

    # ─── FRANÇAIS ────────────────────────────────────────────────────────────
    {
        "matiere": "Français", "niveau": "6e",
        "activite_key": "comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Le Petit Prince (Saint-Exupéry)",
        "texte_source": "Le Petit Prince, Antoine de Saint-Exupéry (1943). Le narrateur, pilote échoué dans le désert, rencontre un petit prince venu d'une autre planète. Celui-ci lui raconte ses voyages et sa relation avec une rose unique qu'il a laissée derrière lui.",
        "resultat": """## Questions de compréhension — *Le Petit Prince*, Saint-Exupéry

**Texte support :** *Le Petit Prince*, Antoine de Saint-Exupéry (1943)

---

**Question 1.** Où se déroule la rencontre entre le narrateur et le Petit Prince ?
- A) Dans une forêt enchantée
- B) Dans le désert du Sahara ✓
- C) Sur une île déserte
- D) Dans une ville inconnue

**Question 2.** D'où vient le Petit Prince ?
- A) De la Lune
- B) D'une planète très lointaine, l'astéroïde B 612 ✓
- C) D'un pays imaginaire
- D) Du fond de la mer

**Question 3.** Quel animal le Petit Prince apprivoise-t-il sur Terre ?
- A) Un oiseau
- B) Un chien
- C) Un renard ✓
- D) Un serpent

**Question 4.** Que signifie « apprivoiser » selon le renard dans le livre ?
- A) Capturer et domestiquer un animal
- B) Créer des liens, rendre quelqu'un unique pour soi ✓
- C) Apprendre à obéir à quelqu'un
- D) Faire peur pour se protéger

**Question 5.** Quelle est la leçon principale que le renard enseigne au Petit Prince ?
- A) Il faut voyager pour être heureux
- B) On ne voit bien qu'avec le cœur, l'essentiel est invisible pour les yeux ✓
- C) Les grandes personnes ont toujours raison
- D) La rose est moins importante que les étoiles

---

**Correction**
1-B / 2-B / 3-C / 4-B / 5-B
""",
    },
    {
        "matiere": "Français", "niveau": "6e",
        "activite_key": "evaluation_orthographe", "activite_label": "Évaluation d'orthographe",
        "sous_type": None, "nb": None, "avec_correction": True,
        "objet": "[Exemple] Dictée — La forêt en automne (niveau 6e)",
        "texte_source": "Texte sur la forêt en automne — accords sujet-verbe, pluriel des noms simples, majuscules. Niveau 6e, début de collège.",
        "resultat": """## Dictée — La forêt en automne

*Lisez le texte une première fois en entier, puis dictez-le en deux parties.*

---

Les arbres de la forêt perdent leurs feuilles chaque automne. Les écureuils cherchent des noisettes et des glands pour préparer l'hiver. Un chemin étroit serpente entre les troncs couverts de mousse verte. Les enfants du village aiment ramasser les feuilles dorées et les châtaignes brillantes. Le vent souffle doucement et fait tomber les dernières feuilles accrochées aux branches.

---

**Points de vigilance :**
- Accord sujet-verbe au pluriel : *les arbres perdent*, *les écureuils cherchent*, *les enfants aiment*
- Pluriel des noms : *feuilles*, *noisettes*, *glands*, *châtaignes*
- Adjectifs qui s'accordent : *dorées*, *brillantes*, *verte*
- Pas de majuscule à *automne*, *hiver*, *forêt*

**Correction**

| Mot | Règle |
|---|---|
| *perdent* | Verbe perdre, 3e pers. pluriel → -ent |
| *cherchent* | Verbe chercher, 3e pers. pluriel → -ent |
| *dorées* | Adjectif accordé avec *feuilles* (fém. plur.) |
| *brillantes* | Adjectif accordé avec *châtaignes* (fém. plur.) |
| *couverts* | Adjectif accordé avec *troncs* (masc. plur.) |
""",
    },
    {
        "matiere": "Français", "niveau": "4e",
        "activite_key": "comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — La nouvelle réaliste (Maupassant)",
        "texte_source": "La Parure, Guy de Maupassant (1884). Mathilde Loisel, femme d'un modeste employé, emprunte un collier de diamants à une amie pour assister à une soirée mondaine. Elle le perd et, pour le remplacer, s'endette pendant dix ans. Elle apprend à la fin que le collier était faux.",
        "resultat": """## Questions de compréhension — *La Parure*, Maupassant

**Texte support :** *La Parure*, Guy de Maupassant (1884)

---

**Question 1.** Pourquoi Mathilde Loisel emprunte-t-elle un bijou à son amie ?
- A) Elle veut le vendre
- B) Elle n'a pas de bijou pour aller à une soirée mondaine ✓
- C) Elle veut impressionner son mari
- D) Elle a perdu ses propres bijoux

**Question 2.** Que lui arrive-t-il après la soirée ?
- A) Elle rencontre un homme riche
- B) Elle est félicitée par ses collègues
- C) Elle perd le collier emprunté ✓
- D) Elle retrouve le collier dans sa voiture

**Question 3.** Quelle décision prennent les époux Loisel pour remplacer le bijou ?
- A) Ils fuient à l'étranger
- B) Ils avouent la perte à l'amie
- C) Ils s'endettent pour acheter un collier identique ✓
- D) Ils achètent un collier moins cher

**Question 4.** Pendant combien de temps les Loisel remboursent-ils leurs dettes ?
- A) Deux ans
- B) Cinq ans
- C) Dix ans ✓
- D) Vingt ans

**Question 5.** Quelle est la chute de la nouvelle ?
- A) Mathilde retrouve le vrai collier
- B) Le collier emprunté était faux ✓
- C) L'amie pardonne sans rancune
- D) Mathilde devient riche grâce à cette expérience

---

**Correction**
1-B / 2-C / 3-C / 4-C / 5-B
""",
    },
    {
        "matiere": "Français", "niveau": "4e",
        "activite_key": "evaluation_orthographe", "activite_label": "Évaluation d'orthographe",
        "sous_type": None, "nb": None, "avec_correction": True,
        "objet": "[Exemple] Dictée — L'automne (niveau 4e)",
        "texte_source": "Texte sur l'automne — accords du participe passé, pluriel des noms composés, homophones grammaticaux. Niveau 4e.",
        "resultat": """## Dictée — L'automne

*Lisez le texte une première fois en entier, puis dictez-le en trois parties.*

---

Les feuilles mortes s'étaient accumulées le long des chemins que nous avions empruntés la veille. Les enfants, que leurs parents avaient emmenés au parc, jouaient en criant de joie. Des châtaignes qu'on avait ramassées dans la matinée remplissaient les paniers en osier. Le vent, dont la force s'était accrue depuis midi, agitait les dernières feuilles accrochées aux branches. La lumière, qu'on aurait pu croire disparue, filtrait encore entre les nuages gris.

---

**Points de vigilance :**
- Accord des participes passés avec *avoir* (empruntés, emmenés, ramassées)
- Antécédent du pronom relatif *que* (feuilles, chemins, enfants, châtaignes)
- Homophones : *qu'on* / *con* — *dont* / *donc*
- Pluriel : *châtaignes*, *branches*, *paniers*

**Correction complète**

| Mot | Justification |
|---|---|
| *accumulées* | PP avec avoir, accord avec COD *les feuilles mortes* placé avant |
| *empruntés* | PP avec avoir, accord avec COD *que* mis pour *chemins* (masc. plur.) |
| *emmenés* | PP avec avoir, accord avec COD *que* mis pour *enfants* (masc. plur.) |
| *ramassées* | PP avec avoir, accord avec COD *qu'on* mis pour *châtaignes* (fém. plur.) |
| *accrue* | PP avec être (verbe pronominal), accord avec le sujet *la force* |
""",
    },

    {
        "matiere": "Français", "niveau": "5e",
        "activite_key": "comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Les Fables de La Fontaine",
        "texte_source": "Les Fables de Jean de La Fontaine (1668-1694). Recueil de fables en vers inspirées d'Ésope et Phèdre. Chaque fable illustre une morale. Exemples : Le Corbeau et le Renard, La Cigale et la Fourmi, Le Loup et l'Agneau.",
        "resultat": """## Questions de compréhension — *Les Fables*, La Fontaine

---

**Question 1.** Dans *La Cigale et la Fourmi*, que fait la cigale tout l'été ?
- A) Elle travaille dur pour stocker de la nourriture
- B) Elle chante sans se soucier de l'hiver ✓
- C) Elle aide la fourmi à transporter des graines
- D) Elle part en voyage vers des pays chauds

**Question 2.** Dans *Le Corbeau et le Renard*, comment le renard parvient-il à obtenir le fromage ?
- A) Il grimpe dans l'arbre pour le prendre
- B) Il flatte le corbeau pour qu'il chante et lâche le fromage ✓
- C) Il attend que le corbeau s'endorme
- D) Il lui propose un échange

**Question 3.** Où se trouve généralement la morale d'une fable ?
- A) Au milieu du récit
- B) Dans le titre
- C) Au début ou à la fin du texte ✓
- D) Elle n'est jamais exprimée directement

**Question 4.** Quelle est la morale de *Le Loup et l'Agneau* ?
- A) Les petits doivent se méfier des grands
- B) La raison du plus fort est toujours la meilleure ✓
- C) L'innocence finit toujours par triompher
- D) Les animaux peuvent vivre en paix

**Question 5.** À qui La Fontaine s'est-il principalement inspiré pour écrire ses Fables ?
- A) Molière et Racine
- B) Virgile et Homère
- C) Ésope et Phèdre ✓
- D) Shakespeare et Dante

---

**Correction :** 1-B / 2-B / 3-C / 4-B / 5-C
""",
    },
    {
        "matiere": "Français", "niveau": "3e",
        "activite_key": "comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Le Roman autobiographique (Rousseau, Sarraute)",
        "texte_source": "L'autobiographie en littérature : pacte autobiographique (Philippe Lejeune), Je = auteur = narrateur = personnage. Œuvres : Les Confessions de Rousseau, L'Enfance de Sarraute. Caractéristiques du genre.",
        "resultat": """## Questions de compréhension — Le Roman autobiographique

---

**Question 1.** Qu'est-ce que le « pacte autobiographique » selon Philippe Lejeune ?
- A) Un contrat signé entre l'auteur et son éditeur
- B) L'engagement implicite de l'auteur envers le lecteur que le « je » désigne bien l'auteur réel ✓
- C) Une convention littéraire qui autorise l'invention dans un récit de vie
- D) La décision de l'auteur d'écrire en première personne

**Question 2.** Dans une autobiographie, quelle triple identité est requise ?
- A) Auteur = éditeur = lecteur
- B) Narrateur = personnage = héros
- C) Auteur = narrateur = personnage ✓
- D) Auteur = personnage = lecteur

**Question 3.** Quelle est la différence entre une autobiographie et des mémoires ?
- A) Les mémoires sont écrits à la troisième personne
- B) L'autobiographie se centre sur la vie intérieure de l'auteur, les mémoires davantage sur les événements historiques ✓
- C) Les mémoires ne peuvent pas contenir de souvenirs d'enfance
- D) Il n'y a aucune différence

**Question 4.** Jean-Jacques Rousseau commence ses *Confessions* par la célèbre phrase : « Je veux montrer à mes semblables un homme dans toute la vérité de la nature. » Quel sentiment cela révèle-t-il ?
- A) Une volonté de cacher ses défauts
- B) Un désir de sincérité absolue et de transparence ✓
- C) Une fierté excessive
- D) Un projet politique

**Question 5.** Le roman d'apprentissage (*Bildungsroman*) se distingue de l'autobiographie car :
- A) Il est toujours écrit à la troisième personne
- B) Il suit la formation et l'évolution d'un personnage fictif ✓
- C) Il ne comporte pas de narrateur
- D) Il ne peut pas se dérouler au XIXe siècle

---

**Correction :** 1-B / 2-C / 3-B / 4-B / 5-B
""",
    },
    {
        "matiere": "Français", "niveau": "2nde",
        "activite_key": "comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — La Poésie lyrique (Du Bellay, Ronsard)",
        "texte_source": "La Pléiade et la poésie lyrique du XVIe siècle. Poètes : Du Bellay (*Les Regrets*), Ronsard (*Odes*, *Sonnets pour Hélène*). Thèmes : le temps qui passe, l'amour, le retour au pays natal, la mélancolie.",
        "resultat": """## Questions de compréhension — La Poésie lyrique

---

**Question 1.** Qu'est-ce que la Pléiade ?
- A) Un recueil de poèmes de Ronsard
- B) Un groupe de sept poètes français du XVIe siècle qui voulaient renouveler la poésie française ✓
- C) Une forme poétique inventée au XVIe siècle
- D) L'école de pensée de Du Bellay uniquement

**Question 2.** Dans le sonnet « Heureux qui comme Ulysse » de Du Bellay, quel sentiment dominant s'exprime ?
- A) La joie du voyage et de la découverte
- B) La nostalgie du pays natal et le désir de retour ✓
- C) L'orgueil d'avoir voyagé loin
- D) L'amour pour une femme lointaine

**Question 3.** La célèbre formule de Ronsard « Cueillez dès aujourd'hui les roses de la vie » exprime :
- A) Un conseil de jardinage
- B) L'invitation à profiter du moment présent car la vie est brève (carpe diem) ✓
- C) La tristesse face à la mort des fleurs
- D) Un hymne à la nature printanière

**Question 4.** Un sonnet est composé de :
- A) Trois strophes de six vers
- B) Deux quatrains et deux tercets ✓
- C) Quatre strophes de quatre vers
- D) Un nombre de vers variable selon l'auteur

**Question 5.** Le registre lyrique se caractérise par :
- A) L'expression des émotions et des sentiments personnels à travers le « je » ✓
- B) La description objective d'événements historiques
- C) L'intention de faire rire le lecteur
- D) Le récit d'aventures héroïques

---

**Correction :** 1-B / 2-B / 3-B / 4-B / 5-A
""",
    },
    {
        "matiere": "Français", "niveau": "1ère",
        "activite_key": "comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Le Roman réaliste et naturaliste (Balzac, Zola)",
        "texte_source": "Le réalisme et le naturalisme au XIXe siècle. Balzac (*La Comédie humaine*), Flaubert (*Madame Bovary*), Zola (*Les Rougon-Macquart*). Caractéristiques : observation du réel, milieux sociaux, déterminisme.",
        "resultat": """## Questions de compréhension — Le Roman réaliste et naturaliste

---

**Question 1.** Quelle est la principale ambition du roman réaliste au XIXe siècle ?
- A) Raconter des histoires merveilleuses et fantastiques
- B) Représenter fidèlement la société et les mœurs de son époque ✓
- C) Dénoncer la politique de l'Empire
- D) Célébrer les valeurs romantiques

**Question 2.** Honoré de Balzac a regroupé ses romans sous un titre général. Lequel ?
- A) Les Misérables
- B) Les Rougon-Macquart
- C) La Comédie humaine ✓
- D) Le Cycle balzacien

**Question 3.** Le naturalisme, dont Zola est le chef de file, se distingue du réalisme car il :
- A) Refuse toute description du milieu social
- B) S'appuie sur les théories scientifiques (hérédité, milieu) pour expliquer les comportements humains ✓
- C) Ne traite que des classes populaires
- D) Privilégie le style poétique sur la narration

**Question 4.** Dans *Madame Bovary*, Flaubert est poursuivi en justice à la parution du roman en 1857. Pourquoi ?
- A) Pour plagiat d'un auteur anglais
- B) Pour offense à la morale publique et religieuse ✓
- C) Pour diffamation envers Napoléon III
- D) Pour avoir révélé des secrets d'État

**Question 5.** La technique narrative du « point de vue omniscient » permet au narrateur de :
- A) Ne rapporter que ce qu'un personnage voit et ressent
- B) Connaître les pensées et actions de tous les personnages, et se situer en dehors de l'histoire ✓
- C) S'impliquer comme personnage dans le récit
- D) Ne jamais commenter les actions des personnages

---

**Correction :** 1-B / 2-C / 3-B / 4-B / 5-B
""",
    },

    # ─── HISTOIRE-GÉOGRAPHIE ─────────────────────────────────────────────────
    {
        "matiere": "Histoire-Géographie", "niveau": "6e",
        "activite_key": "hg_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — La Grèce antique et la démocratie athénienne",
        "texte_source": "La Grèce antique : cité-État (polis), démocratie athénienne, citoyenneté, agora, Acropole. Personnages : Périclès, Socrate. Vie quotidienne et religion grecque. Niveau 6e.",
        "resultat": """## Questions de cours — La Grèce antique

---

**Question 1.** Comment appelle-t-on une cité-État grecque ?
- A) Un Empire
- B) Une polis ✓
- C) Une République
- D) Une tribu

**Question 2.** Qu'est-ce que l'agora dans une cité grecque ?
- A) Le temple principal dédié aux dieux
- B) La place publique où les citoyens se réunissent pour délibérer et commercer ✓
- C) Le palais du roi
- D) Le port de la cité

**Question 3.** Qui peut être citoyen à Athènes au Ve siècle av. J.-C. ?
- A) Tout habitant d'Athènes
- B) Les hommes libres nés de parents athéniens ✓
- C) Les femmes et les esclaves libérés
- D) Tous ceux qui habitent en Grèce

**Question 4.** Quel bâtiment se trouve sur l'Acropole d'Athènes ?
- A) Le Colisée
- B) Le Parthénon ✓
- C) Le Forum
- D) Le Sénat

**Question 5.** À quel dirigeant athénien associe-t-on l'âge d'or de la démocratie et la construction du Parthénon ?
- A) Alexandre le Grand
- B) Socrate
- C) Périclès ✓
- D) Aristote

---

**Correction :** 1-B / 2-B / 3-B / 4-B / 5-C
""",
    },
    {
        "matiere": "Histoire-Géographie", "niveau": "5e",
        "activite_key": "hg_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — L'Islam médiéval et les grandes conquêtes",
        "texte_source": "L'Islam au Moyen Âge : naissance de l'Islam (VIIe siècle), Mahomet, la Hégire (622), le Coran, les cinq piliers, les califats, les grandes conquêtes arabes. Niveau 5e.",
        "resultat": """## Questions de cours — L'Islam médiéval

---

**Question 1.** En quelle année se situe la Hégire, point de départ du calendrier musulman ?
- A) 570
- B) 610
- C) 622 ✓
- D) 632

**Question 2.** Qu'est-ce que la Hégire ?
- A) La mort de Mahomet
- B) La révélation du Coran à Mahomet
- C) Le départ de Mahomet de La Mecque vers Médine ✓
- D) La première conquête arabe

**Question 3.** Combien y a-t-il de piliers de l'Islam ?
- A) Trois
- B) Quatre
- C) Cinq ✓
- D) Sept

**Question 4.** Quel est le livre sacré de l'Islam ?
- A) La Torah
- B) La Bible
- C) Le Coran ✓
- D) Les Hadiths

**Question 5.** Quelle ville est considérée comme la plus sainte de l'Islam ?
- A) Médine
- B) Jérusalem
- C) La Mecque ✓
- D) Bagdad

---

**Correction :** 1-C / 2-C / 3-C / 4-C / 5-C
""",
    },
    {
        "matiere": "Histoire-Géographie", "niveau": "3e",
        "activite_key": "hg_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — La Seconde Guerre mondiale (1939-1945)",
        "texte_source": "La Seconde Guerre mondiale : causes, grandes phases (1939-1945), génocide des Juifs et des Tziganes, Résistance, Libération, bilan. Niveau 3e.",
        "resultat": """## Questions de cours — La Seconde Guerre mondiale

---

**Question 1.** Quel événement déclenche officiellement la Seconde Guerre mondiale en Europe ?
- A) L'annexion de l'Autriche par Hitler en 1938
- B) L'invasion de la Pologne par l'Allemagne nazie le 1er septembre 1939 ✓
- C) L'attaque de Pearl Harbor par le Japon
- D) La déclaration de guerre de l'URSS à l'Allemagne

**Question 2.** Comment appelle-t-on le génocide systématique des Juifs d'Europe par les nazis ?
- A) La Nuit de Cristal
- B) La Solution finale / la Shoah ✓
- C) La déportation
- D) Le Blitzkrieg

**Question 3.** Qui a lancé l'appel du 18 juin 1940 depuis Londres ?
- A) Winston Churchill
- B) Philippe Pétain
- C) Charles de Gaulle ✓
- D) Jean Moulin

**Question 4.** Quel débarquement marque le début de la libération de l'Europe occidentale le 6 juin 1944 ?
- A) Le débarquement de Normandie ✓
- B) Le débarquement en Sicile
- C) Le débarquement en Provence
- D) Le débarquement aux Pays-Bas

**Question 5.** Quand l'Allemagne nazie capitule-t-elle ?
- A) 6 juin 1944
- B) 8 mai 1945 ✓
- C) 2 septembre 1945
- D) 30 avril 1945

---

**Correction :** 1-B / 2-B / 3-C / 4-A / 5-B
""",
    },
    {
        "matiere": "Histoire-Géographie", "niveau": "2nde",
        "activite_key": "hg_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — La Renaissance (XVe-XVIe siècle)",
        "texte_source": "La Renaissance : retour aux sources antiques, humanisme, imprimerie (Gutenberg), grandes découvertes, artistes (Léonard de Vinci, Michel-Ange, Raphaël). Réforme protestante (Luther, Calvin). Niveau 2nde.",
        "resultat": """## Questions de cours — La Renaissance

---

**Question 1.** Quelle invention de Gutenberg (vers 1450) favorise la diffusion des idées humanistes ?
- A) La boussole
- B) L'imprimerie à caractères mobiles ✓
- C) Le télescope
- D) La poudre à canon

**Question 2.** Quel est le foyer principal de la Renaissance en Italie ?
- A) Rome
- B) Venise
- C) Florence ✓
- D) Naples

**Question 3.** L'humanisme de la Renaissance se caractérise par :
- A) Le refus de toute religion
- B) Un intérêt centré sur l'homme, sa dignité et la redécouverte des textes antiques ✓
- C) Le rejet des sciences au profit de la foi
- D) Une pensée exclusivement religieuse

**Question 4.** Martin Luther publie ses 95 thèses en 1517. Que remet-il en cause ?
- A) L'autorité du roi de France
- B) Certaines pratiques de l'Église catholique, notamment la vente des indulgences ✓
- C) L'existence de Dieu
- D) Les travaux des humanistes italiens

**Question 5.** *La Joconde* est une œuvre de :
- A) Michel-Ange
- B) Raphaël
- C) Léonard de Vinci ✓
- D) Botticelli

---

**Correction :** 1-B / 2-C / 3-B / 4-B / 5-C
""",
    },
    {
        "matiere": "Histoire-Géographie", "niveau": "1ère",
        "activite_key": "hg_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Les régimes totalitaires dans les années 1930",
        "texte_source": "Les régimes totalitaires des années 1930 : nazisme (Hitler, Allemagne), stalinisme (URSS), fascisme (Mussolini, Italie). Caractéristiques communes : parti unique, culte du chef, terreur, propagande. Niveau 1ère.",
        "resultat": """## Questions de cours — Les régimes totalitaires

---

**Question 1.** Quelle est la caractéristique commune à tous les régimes totalitaires ?
- A) Ils sont tous issus d'élections libres
- B) Ils cherchent à contrôler tous les aspects de la vie des individus et de la société ✓
- C) Ils s'appuient uniquement sur l'armée
- D) Ils refusent toute idéologie

**Question 2.** En quelle année Hitler arrive-t-il au pouvoir en Allemagne ?
- A) 1929
- B) 1933 ✓
- C) 1936
- D) 1939

**Question 3.** Comment appelle-t-on la politique de terreur stalinienne des années 1936-1938 ?
- A) Le Komintern
- B) Les Grandes Purges ✓
- C) La collectivisation forcée
- D) Le Goulag

**Question 4.** Quel slogan résume l'idéologie nazie concernant la nation allemande ?
- A) « Un peuple, un Reich, un Führer » ✓
- B) « Prolétaires de tous les pays, unissez-vous »
- C) « Tout pour l'État, rien contre l'État »
- D) « La force par la joie »

**Question 5.** Le pacte germano-soviétique est signé en 1939 entre :
- A) Hitler et Mussolini
- B) Hitler et Franco
- C) Hitler et Staline ✓
- D) Mussolini et Staline

---

**Correction :** 1-B / 2-B / 3-B / 4-A / 5-C
""",
    },
    {
        "matiere": "Histoire-Géographie", "niveau": "Terminale",
        "activite_key": "hg_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — La Ve République française",
        "texte_source": "La Ve République : naissance (1958), De Gaulle, Constitution, institutions (Président, Premier ministre, Parlement), cohabitation, alternances politiques, grandes réformes. Niveau Terminale.",
        "resultat": """## Questions de cours — La Ve République française

---

**Question 1.** En quelle année est fondée la Ve République ?
- A) 1944
- B) 1946
- C) 1958 ✓
- D) 1962

**Question 2.** Quelle crise politique majeure précipite la fin de la IVe République et la naissance de la Ve ?
- A) La guerre de Corée
- B) La crise de Suez
- C) La guerre d'Algérie ✓
- D) La révolution hongroise

**Question 3.** Quelle réforme de 1962 renforce le pouvoir du Président de la République ?
- A) La création du Sénat
- B) L'élection du Président de la République au suffrage universel direct ✓
- C) La réduction du mandat présidentiel à 5 ans
- D) La suppression du Premier ministre

**Question 4.** Qu'est-ce qu'une « cohabitation » sous la Ve République ?
- A) Une alliance entre deux partis de gauche
- B) La situation où le Président et le Premier ministre appartiennent à des majorités politiques opposées ✓
- C) Le partage du pouvoir entre le Président et le Sénat
- D) Un accord de gouvernement entre la France et l'Allemagne

**Question 5.** Le quinquennat (mandat de 5 ans pour le Président) est instauré par référendum en :
- A) 1986
- B) 1995
- C) 2000 ✓
- D) 2002

---

**Correction :** 1-C / 2-C / 3-B / 4-B / 5-C
""",
    },

    # ─── HISTOIRE-GÉOGRAPHIE ─────────────────────────────────────────────────
    {
        "matiere": "Histoire-Géographie", "niveau": "4e",
        "activite_key": "hg_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 6, "avec_correction": True,
        "objet": "[Exemple] QCM — La Révolution française",
        "texte_source": "Chapitre : La Révolution française (1789-1799). Notions clés : Tiers État, États généraux, DDHC, Terreur, 18 Brumaire.",
        "resultat": """## Questions de cours — La Révolution française

---

**Question 1.** En quelle année les États généraux sont-ils convoqués par Louis XVI ?
- A) 1776
- B) 1789 ✓
- C) 1792
- D) 1799

**Question 2.** Que représente le Tiers État ?
- A) La noblesse et le clergé
- B) Les 98 % de la population non privilégiée ✓
- C) Les soldats de l'armée royale
- D) Les marchands étrangers

**Question 3.** Qu'est-ce que la DDHC ?
- A) Un traité de paix avec l'Angleterre
- B) La Déclaration des Droits de l'Homme et du Citoyen ✓
- C) Une loi sur la réforme fiscale
- D) Le manifeste du Comité de salut public

**Question 4.** Comment appelle-t-on la période de 1793-1794 marquée par les exécutions massives ?
- A) Le Directoire
- B) La Terreur ✓
- C) La Consulat
- D) La Fronde

**Question 5.** Quel événement met fin à la Révolution française en 1799 ?
- A) La mort de Robespierre
- B) Le coup d'État du 18 Brumaire par Napoléon Bonaparte ✓
- C) La signature du traité de Lunéville
- D) L'abolition de la monarchie

**Question 6.** Quel document royal convoque les États généraux ?
- A) Une ordonnance royale
- B) Une lettre de cachet
- C) Un édit du roi ✓
- D) Un décret du Parlement

---

**Correction :** 1-B / 2-B / 3-B / 4-B / 5-B / 6-C
""",
    },
    {
        "matiere": "Histoire-Géographie", "niveau": "4e",
        "activite_key": "hg_frise", "activite_label": "Frise chronologique",
        "sous_type": None, "nb": None, "avec_correction": False,
        "objet": "[Exemple] Frise — De la Révolution à l'Empire (1789-1815)",
        "texte_source": "Séquence : De la Révolution française à la chute de Napoléon. Repères à placer : 1789, 1792, 1793, 1799, 1804, 1815.",
        "resultat": """## Frise chronologique — De la Révolution à l'Empire (1789-1815)

**Consigne :** Place les événements suivants sur la frise chronologique ci-dessous, puis relie chaque date à son événement.

---

**Événements à placer :**

1. Prise de la Bastille et début de la Révolution
2. Proclamation de la Ire République
3. Début de la Terreur (exécution de Louis XVI)
4. Coup d'État du 18 Brumaire — fin de la Révolution
5. Napoléon se proclame Empereur des Français
6. Bataille de Waterloo et exil définitif de Napoléon

---

**Frise à compléter :**

```
1789 ——— 1792 ——— 1793 ——— 1799 ——— 1804 ——— 1815
  |         |         |         |         |         |
  ?         ?         ?         ?         ?         ?
```

---

**Bonus :** Colorie en rouge la période de la Terreur, en bleu la période du Consulat, en jaune l'Empire.
""",
    },

    # ─── MATHÉMATIQUES ───────────────────────────────────────────────────────
    {
        "matiere": "Mathématiques", "niveau": "3e",
        "activite_key": "maths_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Rappel d'une propriété / théorème", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Théorème de Pythagore",
        "texte_source": "Théorème de Pythagore et sa réciproque. Niveau 3e. Calcul de l'hypoténuse et des côtés de l'angle droit.",
        "resultat": """## Questions de cours — Théorème de Pythagore

---

**Question 1.** Dans un triangle rectangle en C, quelle relation lie les côtés ?
- A) AB² = AC² - BC²
- B) AC² = AB² + BC²
- C) AB² = AC² + BC² ✓
- D) BC² = AB² + AC²

**Question 2.** Un triangle a pour côtés 3 cm, 4 cm et 5 cm. Est-il rectangle ?
- A) Non, car 3 + 4 ≠ 5
- B) Oui, car 3² + 4² = 5² ✓
- C) Non, car les côtés ne sont pas égaux
- D) Oui, car il a un angle obtus

**Question 3.** Dans un triangle rectangle, comment appelle-t-on le côté opposé à l'angle droit ?
- A) La médiane
- B) La hauteur
- C) L'hypoténuse ✓
- D) La bissectrice

**Question 4.** Dans un triangle rectangle en A, avec AB = 5 cm et AC = 12 cm, quelle est la valeur de BC ?
- A) 7 cm
- B) 13 cm ✓
- C) 17 cm
- D) 11 cm

**Question 5.** La réciproque du théorème de Pythagore permet de :
- A) Calculer la surface d'un triangle
- B) Vérifier qu'un triangle est rectangle ✓
- C) Trouver les angles d'un triangle
- D) Calculer le périmètre d'un triangle

---

**Correction :** 1-C / 2-B / 3-C / 4-B (√(5²+12²) = √169 = 13) / 5-B
""",
    },
    {
        "matiere": "Mathématiques", "niveau": "3e",
        "activite_key": "maths_comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "Identification des données utiles", "nb": 4, "avec_correction": True,
        "objet": "[Exemple] Exercices — Équations du premier degré",
        "texte_source": "Résolution d'équations du premier degré à une inconnue. Niveau 3e. Techniques : isoler l'inconnue, simplifier, vérifier.",
        "resultat": """## Questions de compréhension — Équations du premier degré

---

**Question 1.** Quelle est la solution de l'équation : 2x + 5 = 13 ?
- A) x = 4 ✓
- B) x = 9
- C) x = 3
- D) x = 6

*Vérification : 2×4 + 5 = 8 + 5 = 13 ✓*

**Question 2.** On résout 3x - 7 = 2x + 1. Quelle est la première étape correcte ?
- A) Diviser les deux membres par 3
- B) Soustraire 2x des deux membres ✓
- C) Ajouter 7 au membre gauche uniquement
- D) Multiplier par -1

**Question 3.** Parmi les équations suivantes, laquelle a pour solution x = -3 ?
- A) x + 5 = 8
- B) 2x + 6 = 0 ✓
- C) x - 3 = 0
- D) 4x = 12

*Vérification : 2×(-3) + 6 = -6 + 6 = 0 ✓*

**Question 4.** L'équation 5(x - 2) = 3x + 4 a pour solution :
- A) x = 5
- B) x = 7 ✓
- C) x = 3
- D) x = 14

*Développement : 5x - 10 = 3x + 4 → 2x = 14 → x = 7*

---

**Correction :** 1-A / 2-B / 3-B / 4-B
""",
    },

    {
        "matiere": "Mathématiques", "niveau": "6e",
        "activite_key": "maths_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Calcul", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Fractions et nombres décimaux",
        "texte_source": "Fractions : numérateur, dénominateur, fractions égales, simplification, comparaison. Nombres décimaux. Niveau 6e.",
        "resultat": """## Questions de cours — Fractions et nombres décimaux

---

**Question 1.** Quelle fraction est égale à 1/2 ?
- A) 2/3
- B) 3/6 ✓
- C) 4/9
- D) 2/5

**Question 2.** Laquelle de ces fractions est la plus grande ?
- A) 1/4
- B) 1/3 ✓
- C) 1/5
- D) 1/6

**Question 3.** Quel est le résultat de 3/4 + 1/4 ?
- A) 3/8
- B) 4/8
- C) 1 ✓
- D) 4/4 (mais non simplifié)

**Question 4.** Comment s'appelle le nombre écrit en haut d'une fraction ?
- A) Le dénominateur
- B) Le numérateur ✓
- C) Le quotient
- D) Le dividende

**Question 5.** 0,5 est égal à :
- A) 5/100
- B) 5/10 ✓
- C) 1/5
- D) 50/10

---

**Correction :** 1-B / 2-B / 3-C / 4-B / 5-B
""",
    },
    {
        "matiere": "Mathématiques", "niveau": "5e",
        "activite_key": "maths_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Calcul littéral", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Proportionnalité et pourcentages",
        "texte_source": "Proportionnalité : tableau de proportionnalité, coefficient de proportionnalité, règle de trois. Pourcentages. Niveau 5e.",
        "resultat": """## Questions de cours — Proportionnalité et pourcentages

---

**Question 1.** Dans un tableau de proportionnalité, si 3 stylos coûtent 6 €, combien coûtent 5 stylos ?
- A) 8 €
- B) 9 €
- C) 10 € ✓
- D) 12 €

**Question 2.** Quel est le coefficient de proportionnalité entre x et y si y = 4x ?
- A) x
- B) 4 ✓
- C) 4x
- D) 1/4

**Question 3.** 20 % de 150 =
- A) 20
- B) 25
- C) 30 ✓
- D) 35

**Question 4.** Un article coûte 80 € et est soldé à -25 %. Quel est son nouveau prix ?
- A) 55 €
- B) 60 € ✓
- C) 65 €
- D) 70 €

**Question 5.** Deux grandeurs sont proportionnelles si :
- A) Leur somme est constante
- B) Leur différence est constante
- C) Leur rapport est constant ✓
- D) Leur produit est constant

---

**Correction :** 1-C / 2-B / 3-C / 4-B / 5-C
""",
    },
    {
        "matiere": "Mathématiques", "niveau": "4e",
        "activite_key": "maths_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Fonctions", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Puissances et notation scientifique",
        "texte_source": "Puissances entières (positives et négatives), règles de calcul sur les puissances, notation scientifique. Niveau 4e.",
        "resultat": """## Questions de cours — Puissances et notation scientifique

---

**Question 1.** Quel est le résultat de 2³ ?
- A) 6
- B) 8 ✓
- C) 9
- D) 16

**Question 2.** Comment simplifie-t-on 3⁴ × 3² ?
- A) 3⁸
- B) 9⁶
- C) 3⁶ ✓
- D) 3²

**Question 3.** Que vaut 5⁰ ?
- A) 0
- B) 5
- C) 1 ✓
- D) Indéfini

**Question 4.** 0,000 47 s'écrit en notation scientifique :
- A) 4,7 × 10²
- B) 4,7 × 10⁻⁴ ✓
- C) 47 × 10⁻⁵
- D) 4,7 × 10⁴

**Question 5.** Quel est le résultat de (2³)² ?
- A) 2⁵
- B) 2⁶ ✓
- C) 4⁶
- D) 2⁹

---

**Correction :** 1-B / 2-C / 3-C / 4-B / 5-B
""",
    },
    {
        "matiere": "Mathématiques", "niveau": "2nde",
        "activite_key": "maths_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Fonctions affines", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Fonctions affines et représentation graphique",
        "texte_source": "Fonctions affines f(x) = ax + b : pente, ordonnée à l'origine, tableau de valeurs, représentation graphique. Fonctions linéaires. Niveau 2nde.",
        "resultat": """## Questions de cours — Fonctions affines

---

**Question 1.** Une fonction affine est de la forme :
- A) f(x) = ax²
- B) f(x) = ax + b ✓
- C) f(x) = a/x
- D) f(x) = √x

**Question 2.** Pour f(x) = 3x - 2, quelle est l'ordonnée à l'origine ?
- A) 3
- B) 0
- C) -2 ✓
- D) 2

**Question 3.** La représentation graphique d'une fonction affine est :
- A) Une parabole
- B) Une droite ✓
- C) Une courbe exponentielle
- D) Un cercle

**Question 4.** Pour f(x) = -2x + 1, la fonction est :
- A) Croissante sur ℝ
- B) Décroissante sur ℝ ✓
- C) Constante
- D) Croissante puis décroissante

**Question 5.** Si f(x) = 4x + 1, quelle est la valeur de f(3) ?
- A) 12
- B) 13 ✓
- C) 7
- D) 15

---

**Correction :** 1-B / 2-C / 3-B / 4-B / 5-B
""",
    },
    {
        "matiere": "Mathématiques", "niveau": "1ère",
        "activite_key": "maths_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Dérivées", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Dérivation et étude de fonctions",
        "texte_source": "Dérivées : définition, règles (somme, produit, composée), dérivées usuelles, variations d'une fonction, extremums. Niveau 1ère.",
        "resultat": """## Questions de cours — Dérivation

---

**Question 1.** Quelle est la dérivée de f(x) = x³ ?
- A) x²
- B) 3x ✓ (3x²)
- C) 3x²  ✓
- D) x⁴/4

*Réponse : f'(x) = 3x²*

**Question 2.** La dérivée de f(x) = 5 (fonction constante) est :
- A) 5
- B) 5x
- C) 0 ✓
- D) 1

**Question 3.** Une fonction est croissante sur un intervalle si sa dérivée est :
- A) Négative sur cet intervalle
- B) Nulle sur cet intervalle
- C) Positive sur cet intervalle ✓
- D) Non définie sur cet intervalle

**Question 4.** La dérivée de f(x) = sin(x) est :
- A) -sin(x)
- B) cos(x) ✓
- C) tan(x)
- D) -cos(x)

**Question 5.** En un extremum (maximum ou minimum local), la dérivée vaut :
- A) 1
- B) -1
- C) 0 ✓
- D) Elle n'est pas définie

---

**Correction :** 1-C / 2-C / 3-C / 4-B / 5-C
""",
    },
    {
        "matiere": "Mathématiques", "niveau": "Terminale",
        "activite_key": "maths_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Probabilités", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Probabilités et loi des grands nombres",
        "texte_source": "Probabilités : loi de probabilité, espérance, variance, loi binomiale, loi normale, intervalle de fluctuation, échantillonnage. Niveau Terminale.",
        "resultat": """## Questions de cours — Probabilités

---

**Question 1.** Si on lance un dé équilibré à 6 faces, quelle est la probabilité d'obtenir un nombre pair ?
- A) 1/6
- B) 1/3
- C) 1/2 ✓
- D) 2/3

**Question 2.** L'espérance d'une variable aléatoire X représente :
- A) La valeur maximale que peut prendre X
- B) La valeur moyenne de X sur un grand nombre d'expériences ✓
- C) La probabilité de l'événement le plus probable
- D) L'écart entre le maximum et le minimum

**Question 3.** Une loi binomiale B(n, p) modélise le nombre de succès dans :
- A) Une seule expérience aléatoire
- B) n expériences indépendantes, chacune ayant une probabilité p de succès ✓
- C) n expériences dont les résultats sont liés
- D) Une suite d'événements certains

**Question 4.** La loi normale est représentée graphiquement par :
- A) Un rectangle
- B) Une courbe en cloche symétrique par rapport à la moyenne ✓
- C) Une droite croissante
- D) Une parabole

**Question 5.** La variance d'une variable aléatoire mesure :
- A) La valeur centrale de la distribution
- B) La probabilité de l'événement moyen
- C) La dispersion des valeurs autour de l'espérance ✓
- D) Le nombre de valeurs possibles

---

**Correction :** 1-C / 2-B / 3-B / 4-B / 5-C
""",
    },

    # ─── PHYSIQUE-CHIMIE ─────────────────────────────────────────────────────
    {
        "matiere": "Physique-Chimie", "niveau": "3e",
        "activite_key": "pc_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Rappel d'une loi / formule", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Lois de l'électricité (circuit en série / dérivation)",
        "texte_source": "Lois de l'électricité : loi des nœuds, loi des mailles, loi d'Ohm. Circuits en série et en dérivation. Niveau 3e.",
        "resultat": """## Questions de cours — Lois de l'électricité

---

**Question 1.** Dans un circuit en série, quelle grandeur est identique dans tous les composants ?
- A) La tension
- B) La résistance
- C) L'intensité ✓
- D) La puissance

**Question 2.** Quelle est la loi des mailles dans un circuit en dérivation ?
- A) La tension est nulle dans les branches
- B) Les tensions dans les branches sont égales entre elles ✓
- C) Les intensités dans les branches s'additionnent uniquement
- D) La résistance totale est la somme des résistances

**Question 3.** Un dipôle résistif a une tension de 6 V et une intensité de 2 A. Quelle est sa résistance ?
- A) 12 Ω
- B) 4 Ω
- C) 3 Ω ✓
- D) 8 Ω

*R = U/I = 6/2 = 3 Ω*

**Question 4.** Dans un circuit en série avec deux résistances R1 = 10 Ω et R2 = 15 Ω, quelle est la résistance totale ?
- A) 5 Ω
- B) 150 Ω
- C) 25 Ω ✓
- D) 10 Ω

**Question 5.** La loi des nœuds affirme que :
- A) La tension est constante en tout point
- B) La somme des intensités arrivant à un nœud est égale à la somme des intensités qui en repartent ✓
- C) L'intensité est nulle dans une branche dérivée
- D) La résistance dépend de la tension

---

**Correction :** 1-C / 2-B / 3-C / 4-C / 5-B
""",
    },
    {
        "matiere": "Physique-Chimie", "niveau": "4e",
        "activite_key": "pc_comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "Lecture d'un graphique", "nb": 4, "avec_correction": True,
        "objet": "[Exemple] Questions — Optique géométrique et lumière",
        "texte_source": "Chapitre optique : propagation rectiligne de la lumière, formation d'images, lentilles convergentes. Niveau 4e.",
        "resultat": """## Questions de compréhension — Optique géométrique

---

**Question 1.** Comment se propage la lumière dans un milieu homogène et transparent ?
- A) En zigzag
- B) En ligne courbe
- C) En ligne droite ✓
- D) En spirale

**Question 2.** Une lentille convergente fait converger les rayons lumineux. Où se forme l'image d'un objet éloigné ?
- A) En avant de la lentille
- B) Au foyer image de la lentille ✓
- C) À l'infini
- D) Au centre de la lentille

**Question 3.** Qu'est-ce que le phénomène de réfraction ?
- A) Le rebond de la lumière sur une surface
- B) La décomposition de la lumière blanche
- C) Le changement de direction de la lumière lors du passage entre deux milieux ✓
- D) L'absorption de la lumière par un matériau

**Question 4.** Une image est dite « réelle » lorsqu'elle :
- A) Se forme du même côté que l'objet
- B) Peut être recueillie sur un écran ✓
- C) Est toujours droite et agrandie
- D) N'existe que pour les miroirs

---

**Correction :** 1-C / 2-B / 3-C / 4-B
""",
    },

    {
        "matiere": "Physique-Chimie", "niveau": "5e",
        "activite_key": "pc_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Les états de la matière",
        "texte_source": "Les trois états de la matière : solide, liquide, gazeux. Changements d'état : fusion, solidification, vaporisation, condensation, sublimation. Niveau 5e.",
        "resultat": """## Questions de cours — Les états de la matière

---

**Question 1.** Comment appelle-t-on le passage de l'état solide à l'état liquide ?
- A) Vaporisation
- B) Fusion ✓
- C) Condensation
- D) Solidification

**Question 2.** À quelle température l'eau pure fond-elle sous pression atmosphérique normale ?
- A) -10 °C
- B) 0 °C ✓
- C) 100 °C
- D) 37 °C

**Question 3.** Lors d'un changement d'état, la température d'un corps pur :
- A) Augmente toujours
- B) Diminue toujours
- C) Reste constante ✓
- D) Varie de façon aléatoire

**Question 4.** Comment appelle-t-on le passage direct de l'état solide à l'état gazeux ?
- A) Vaporisation
- B) Condensation
- C) Sublimation ✓
- D) Fusion

**Question 5.** Dans quel état la matière a-t-elle un volume fixe mais pas de forme propre ?
- A) Solide
- B) Liquide ✓
- C) Gazeux
- D) Plasma

---

**Correction :** 1-B / 2-B / 3-C / 4-C / 5-B
""",
    },
    {
        "matiere": "Physique-Chimie", "niveau": "2nde",
        "activite_key": "pc_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — La lumière et les ondes",
        "texte_source": "La lumière : nature ondulatoire, spectre électromagnétique, dispersion (arc-en-ciel, prisme), vitesse de la lumière, sources lumineuses. Niveau 2nde.",
        "resultat": """## Questions de cours — La lumière et les ondes

---

**Question 1.** Quelle est la vitesse de la lumière dans le vide ?
- A) 300 000 km/h
- B) 300 000 km/s ✓
- C) 3 000 km/s
- D) 300 000 m/s

**Question 2.** Quelles couleurs composent le spectre visible de la lumière blanche ?
- A) Rouge, vert, bleu uniquement
- B) Les sept couleurs de l'arc-en-ciel (rouge, orange, jaune, vert, bleu, indigo, violet) ✓
- C) Blanc et noir
- D) Infrarouge et ultraviolet

**Question 3.** Un prisme décompose la lumière blanche car :
- A) Il absorbe certaines couleurs
- B) Les différentes longueurs d'onde sont déviées différemment en changeant de milieu ✓
- C) Il réfléchit la lumière
- D) Il amplifie certaines couleurs

**Question 4.** Quelle longueur d'onde correspond au rouge dans le spectre visible ?
- A) 400 nm
- B) 550 nm
- C) 700 nm ✓
- D) 900 nm

**Question 5.** Les rayons X sont :
- A) Des ondes sonores de haute fréquence
- B) Des ondes électromagnétiques de longueur d'onde inférieure à celle de la lumière visible ✓
- C) Des particules chargées
- D) Un type de lumière visible

---

**Correction :** 1-B / 2-B / 3-B / 4-C / 5-B
""",
    },
    {
        "matiere": "Physique-Chimie", "niveau": "1ère",
        "activite_key": "pc_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Cinématique : vitesse et accélération",
        "texte_source": "Cinématique : mouvement rectiligne uniforme et uniformément accéléré, vitesse instantanée et moyenne, accélération, vecteur vitesse. Niveau 1ère.",
        "resultat": """## Questions de cours — Cinématique

---

**Question 1.** Un mouvement rectiligne uniforme (MRU) est caractérisé par :
- A) Une vitesse qui augmente régulièrement
- B) Une vitesse constante en module et en direction ✓
- C) Une accélération constante non nulle
- D) Une trajectoire courbe

**Question 2.** Quelle est l'unité SI de la vitesse ?
- A) km/h
- B) m/s ✓
- C) km/s
- D) cm/s

**Question 3.** Un objet en chute libre (sans frottement) subit :
- A) Un MRU
- B) Un mouvement uniformément décéléré
- C) Un mouvement uniformément accéléré ✓
- D) Un mouvement de rotation

**Question 4.** L'accélération est nulle pour un objet qui :
- A) Tombe en chute libre
- B) Accélère sur une droite
- C) Se déplace à vitesse constante sur une trajectoire rectiligne ✓
- D) Tourne en rond à vitesse constante

**Question 5.** Si un objet parcourt 120 m en 4 s à vitesse constante, sa vitesse est :
- A) 480 m/s
- B) 30 m/s ✓
- C) 60 m/s
- D) 0,03 m/s

---

**Correction :** 1-B / 2-B / 3-C / 4-C / 5-B
""",
    },
    {
        "matiere": "Physique-Chimie", "niveau": "Terminale",
        "activite_key": "pc_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Thermodynamique : premier principe",
        "texte_source": "Premier principe de la thermodynamique : énergie interne, travail, chaleur, conservation de l'énergie. Transformations isotherme, adiabatique, isobare. Niveau Terminale.",
        "resultat": """## Questions de cours — Thermodynamique

---

**Question 1.** Le premier principe de la thermodynamique énonce que :
- A) La chaleur ne peut passer que du corps chaud au corps froid
- B) L'énergie totale d'un système isolé se conserve ✓
- C) L'entropie d'un système isolé ne peut que diminuer
- D) Le travail est toujours positif

**Question 2.** L'énergie interne d'un système dépend de :
- A) Sa vitesse uniquement
- B) Sa position dans l'espace
- C) L'état microscopique des particules qui le composent (agitation thermique) ✓
- D) Sa masse uniquement

**Question 3.** Dans une transformation adiabatique :
- A) La température est constante
- B) La pression est constante
- C) Il n'y a pas d'échange de chaleur avec l'extérieur ✓
- D) Le volume est constant

**Question 4.** Le premier principe s'écrit ΔU = W + Q. Que représente W ?
- A) La chaleur échangée
- B) Le travail reçu par le système ✓
- C) La variation d'énergie interne
- D) L'entropie produite

**Question 5.** Pour un gaz parfait lors d'une transformation isotherme :
- A) ΔU ≠ 0
- B) W = 0
- C) ΔU = 0 donc W = -Q ✓
- D) Q = 0

---

**Correction :** 1-B / 2-C / 3-C / 4-B / 5-C
""",
    },

    # ─── SVT ─────────────────────────────────────────────────────────────────
    {
        "matiere": "SVT", "niveau": "3e",
        "activite_key": "svt_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — La génétique et l'hérédité",
        "texte_source": "Génétique : ADN, chromosomes, gènes, allèles, hérédité des caractères, lois de Mendel simplifiées. Niveau 3e.",
        "resultat": """## Questions de cours — La génétique et l'hérédité

---

**Question 1.** Quel est le support de l'information génétique dans une cellule ?
- A) Les protéines
- B) Les mitochondries
- C) L'ADN ✓
- D) Les ribosomes

**Question 2.** Combien de chromosomes possède une cellule humaine normale (non reproductrice) ?
- A) 23
- B) 46 ✓
- C) 92
- D) 24

**Question 3.** Que sont les allèles ?
- A) Des chromosomes identiques
- B) Les différentes formes possibles d'un même gène ✓
- C) Des protéines produites par les gènes
- D) Des segments d'ADN non codants

**Question 4.** Un individu est dit « homozygote » pour un gène lorsque :
- A) Il porte deux allèles différents
- B) Il porte deux allèles identiques ✓
- C) Il n'a qu'un seul chromosome
- D) Il présente une mutation

**Question 5.** Les cellules reproductrices (gamètes) contiennent :
- A) 46 chromosomes
- B) 92 chromosomes
- C) 23 chromosomes ✓
- D) 12 chromosomes

---

**Correction :** 1-C / 2-B / 3-B / 4-B / 5-C
""",
    },
    {
        "matiere": "SVT", "niveau": "5e",
        "activite_key": "svt_comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "Lecture d'un schéma", "nb": 4, "avec_correction": True,
        "objet": "[Exemple] Questions — Le système digestif",
        "texte_source": "Le système digestif : trajet des aliments, organes impliqués, digestion mécanique et chimique. Niveau 5e.",
        "resultat": """## Questions de compréhension — Le système digestif

---

**Question 1.** Dans quel ordre les aliments traversent-ils ces organes ?
- A) Estomac → bouche → intestin grêle → œsophage
- B) Bouche → œsophage → estomac → intestin grêle ✓
- C) Bouche → estomac → œsophage → intestin grêle
- D) Intestin grêle → estomac → bouche → œsophage

**Question 2.** Où s'effectue principalement l'absorption des nutriments ?
- A) Dans l'estomac
- B) Dans la bouche
- C) Dans l'intestin grêle ✓
- D) Dans le gros intestin

**Question 3.** Quel organe produit la bile, nécessaire à la digestion des graisses ?
- A) Le pancréas
- B) L'estomac
- C) Le foie ✓
- D) Les reins

**Question 4.** Qu'est-ce que la digestion chimique ?
- A) La mastication et le brassage mécanique des aliments
- B) La transformation des aliments en nutriments grâce aux enzymes ✓
- C) L'absorption des nutriments dans le sang
- D) L'élimination des déchets non digérés

---

**Correction :** 1-B / 2-C / 3-C / 4-B
""",
    },

    {
        "matiere": "SVT", "niveau": "6e",
        "activite_key": "svt_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Le vivant : la cellule",
        "texte_source": "La cellule : unité du vivant, cellule animale et végétale, noyau, membrane, cytoplasme, chloroplastes. Unicellulaires et pluricellulaires. Niveau 6e.",
        "resultat": """## Questions de cours — La cellule, unité du vivant

---

**Question 1.** Qu'est-ce qu'une cellule ?
- A) Un organe du corps humain
- B) L'unité de base de tous les êtres vivants ✓
- C) Une molécule chimique
- D) Un tissu du corps humain

**Question 2.** Quelle structure contient l'information génétique dans une cellule ?
- A) La membrane cellulaire
- B) Le cytoplasme
- C) Le noyau ✓
- D) La mitochondrie

**Question 3.** Quelle est la différence principale entre une cellule végétale et une cellule animale ?
- A) La cellule végétale n'a pas de noyau
- B) La cellule végétale possède une paroi cellulaire et des chloroplastes ✓
- C) La cellule animale possède des chloroplastes
- D) Il n'y a aucune différence

**Question 4.** Un être unicellulaire est composé de :
- A) Des milliers de cellules spécialisées
- B) Une seule cellule ✓
- C) Des organes complexes
- D) Plusieurs tissus

**Question 5.** Les chloroplastes permettent à la cellule végétale de :
- A) Se reproduire
- B) Réaliser la photosynthèse en captant la lumière ✓
- C) Stocker de l'eau
- D) Absorber les minéraux du sol

---

**Correction :** 1-B / 2-C / 3-B / 4-B / 5-B
""",
    },
    {
        "matiere": "SVT", "niveau": "4e",
        "activite_key": "svt_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — La tectonique des plaques",
        "texte_source": "Tectonique des plaques : lithosphère, plaques tectoniques, dorsales océaniques, subduction, séismes, volcans. Niveau 4e.",
        "resultat": """## Questions de cours — La tectonique des plaques

---

**Question 1.** Combien de grandes plaques tectoniques compose la lithosphère ?
- A) 3 ou 4
- B) Une dizaine ✓
- C) Plus de 50
- D) 2 (une continentale, une océanique)

**Question 2.** Qu'est-ce qu'une dorsale océanique ?
- A) Une fosse abyssale très profonde
- B) Une chaîne de montagnes sous-marine où se forme une nouvelle lithosphère ✓
- C) Un volcan continental
- D) Une zone où une plaque s'enfonce sous une autre

**Question 3.** Comment appelle-t-on la zone où une plaque océanique s'enfonce sous une autre ?
- A) Une dorsale
- B) Une faille
- C) Une zone de subduction ✓
- D) Un point chaud

**Question 4.** Les séismes résultent principalement de :
- A) L'éruption de volcans sous-marins
- B) La rupture brutale des roches le long d'une faille, libérant de l'énergie ✓
- C) La fonte des glaces polaires
- D) La variation de la pression atmosphérique

**Question 5.** La chaîne de montagnes himalayenne s'est formée par :
- A) Un volcanisme intense
- B) La subduction d'une plaque océanique
- C) La collision de deux plaques continentales ✓
- D) L'érosion du plateau tibétain

---

**Correction :** 1-B / 2-B / 3-C / 4-B / 5-C
""",
    },
    {
        "matiere": "SVT", "niveau": "2nde",
        "activite_key": "svt_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — La biodiversité et l'évolution",
        "texte_source": "Biodiversité : diversité spécifique, génétique, des écosystèmes. Évolution : sélection naturelle, mutation, dérive génétique. Darwin. Niveau 2nde.",
        "resultat": """## Questions de cours — Biodiversité et évolution

---

**Question 1.** La biodiversité comprend trois niveaux. Lesquels ?
- A) Animal, végétal, minéral
- B) Diversité des espèces, diversité génétique, diversité des écosystèmes ✓
- C) Diversité terrestre, marine, aérienne
- D) Diversité des individus, des organes, des cellules

**Question 2.** Quel scientifique a proposé la théorie de la sélection naturelle ?
- A) Lamarck
- B) Mendel
- C) Darwin ✓
- D) Pasteur

**Question 3.** La sélection naturelle favorise :
- A) Les individus les plus grands
- B) Les individus les mieux adaptés à leur environnement, qui se reproduisent davantage ✓
- C) Les individus qui ont le plus de mutations
- D) Les individus les plus colorés

**Question 4.** Une mutation génétique est :
- A) Toujours mortelle pour l'individu
- B) Une modification de la séquence d'ADN, aléatoire et héréditaire si elle touche les gamètes ✓
- C) Toujours avantageuse
- D) Toujours visible sur l'individu

**Question 5.** Deux espèces ayant un ancêtre commun récent ont :
- A) Exactement les mêmes gènes
- B) Aucune ressemblance génétique
- C) Un degré de parenté plus élevé que deux espèces à ancêtre commun lointain ✓
- D) Forcément le même habitat

---

**Correction :** 1-B / 2-C / 3-B / 4-B / 5-C
""",
    },
    {
        "matiere": "SVT", "niveau": "1ère",
        "activite_key": "svt_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Le système immunitaire",
        "texte_source": "Système immunitaire : immunité innée et adaptative, lymphocytes B et T, anticorps, vaccination, mémoire immunitaire. Niveau 1ère.",
        "resultat": """## Questions de cours — Le système immunitaire

---

**Question 1.** L'immunité innée se caractérise par :
- A) Une réponse lente et spécifique à chaque pathogène
- B) Une réponse rapide, non spécifique, identique pour tout agent pathogène ✓
- C) La production d'anticorps spécifiques
- D) La mémoire immunitaire à long terme

**Question 2.** Quel type de cellule produit les anticorps ?
- A) Les lymphocytes T
- B) Les phagocytes
- C) Les lymphocytes B (plasmocytes) ✓
- D) Les globules rouges

**Question 3.** La vaccination crée une immunité en :
- A) Détruisant directement les agents pathogènes
- B) Introduisant des anticorps fabriqués en laboratoire
- C) Stimulant le système immunitaire à produire des cellules mémoire sans déclencher la maladie ✓
- D) Augmentant le nombre de globules blancs en permanence

**Question 4.** Les lymphocytes T cytotoxiques ont pour rôle de :
- A) Produire des anticorps
- B) Détruire directement les cellules infectées ou tumorales ✓
- C) Déclencher l'inflammation
- D) Filtrer le sang

**Question 5.** La mémoire immunitaire explique pourquoi :
- A) Certaines maladies sont chroniques
- B) On tombe malade lors d'une première infection
- C) Une deuxième infection par le même pathogène provoque une réponse plus rapide et plus forte ✓
- D) Les antibiotiques sont efficaces

---

**Correction :** 1-B / 2-C / 3-C / 4-B / 5-C
""",
    },
    {
        "matiere": "SVT", "niveau": "Terminale",
        "activite_key": "svt_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Le système nerveux et la transmission de l'influx",
        "texte_source": "Système nerveux : neurones, synapse, potentiel d'action, neurotransmetteurs, intégration nerveuse, réflexe. Niveau Terminale.",
        "resultat": """## Questions de cours — Le système nerveux

---

**Question 1.** Un neurone transmet l'information sous forme de :
- A) Signaux chimiques uniquement
- B) Signaux électriques (potentiel d'action) le long de l'axone ✓
- C) Signaux lumineux
- D) Variations de température

**Question 2.** La synapse est :
- A) Le noyau du neurone
- B) La zone de communication entre deux neurones ✓
- C) La gaine de myéline
- D) Le corps cellulaire du neurone

**Question 3.** Les neurotransmetteurs sont libérés :
- A) Par la cellule post-synaptique
- B) Dans le noyau du neurone
- C) Dans la fente synaptique par la terminaison axonale ✓
- D) Dans le sang

**Question 4.** La myélinisation de l'axone permet de :
- A) Réduire la vitesse de conduction
- B) Accélérer la transmission du potentiel d'action ✓
- C) Produire des neurotransmetteurs
- D) Connecter les neurones aux muscles

**Question 5.** Un arc réflexe implique dans l'ordre :
- A) Effecteur → moelle épinière → récepteur
- B) Récepteur → nerf sensitif → moelle épinière → nerf moteur → effecteur ✓
- C) Cerveau → nerf moteur → effecteur → récepteur
- D) Récepteur → cerveau → effecteur

---

**Correction :** 1-B / 2-B / 3-C / 4-B / 5-B
""",
    },

    # ─── SES ─────────────────────────────────────────────────────────────────
    {
        "matiere": "SES", "niveau": "1ère",
        "activite_key": "ses_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Les marchés et la concurrence",
        "texte_source": "Chapitre : Marchés et prix. Offre, demande, prix d'équilibre, concurrence pure et parfaite, défaillances de marché. Niveau 1ère SES.",
        "resultat": """## Questions de cours — Les marchés et la concurrence

---

**Question 1.** Qu'est-ce que le prix d'équilibre sur un marché ?
- A) Le prix fixé par l'État
- B) Le prix auquel l'offre égale la demande ✓
- C) Le prix le plus bas proposé par les vendeurs
- D) Le prix moyen calculé sur un an

**Question 2.** Dans un marché de concurrence pure et parfaite, les agents sont :
- A) Preneurs de prix (price takers) ✓
- B) Faiseurs de prix (price makers)
- C) Protégés par des barrières à l'entrée
- D) Subventionnés par l'État

**Question 3.** Une externalité négative se produit lorsque :
- A) Une entreprise réalise un bénéfice
- B) Une activité économique impose un coût à un tiers non impliqué dans la transaction ✓
- C) Le prix d'un bien augmente soudainement
- D) La demande d'un bien diminue

**Question 4.** Que se passe-t-il sur un marché si le prix est supérieur au prix d'équilibre ?
- A) Il y a une pénurie
- B) Il y a un excès de demande
- C) Il y a un excès d'offre (surplus) ✓
- D) Le marché est en équilibre

**Question 5.** Un bien public se caractérise par :
- A) Son prix élevé et sa rareté
- B) Sa non-rivalité et sa non-exclusion ✓
- C) Sa production uniquement par l'État
- D) Sa consommation individuelle et privée

---

**Correction :** 1-B / 2-A / 3-B / 4-C / 5-B
""",
    },
    {
        "matiere": "SES", "niveau": "1ère",
        "activite_key": "ses_étude_de_vocabulaire", "activite_label": "Étude de vocabulaire - notions clés",
        "sous_type": "Définir un concept économique", "nb": None, "avec_correction": True,
        "objet": "[Exemple] Vocabulaire — Notions clés de macroéconomie",
        "texte_source": "Notions de macroéconomie à maîtriser en 1ère SES : PIB, inflation, chômage, politique budgétaire, politique monétaire.",
        "resultat": """## Étude de vocabulaire — Notions clés de macroéconomie

**Consigne :** Associe chaque notion à sa définition correcte, puis rédige une phrase d'exemple pour chacune.

---

**Notions :**
1. PIB (Produit Intérieur Brut)
2. Inflation
3. Taux de chômage
4. Politique budgétaire
5. Politique monétaire

**Définitions à associer :**

A. Hausse générale et durable du niveau des prix
B. Ensemble des décisions de l'État relatives aux dépenses publiques et aux impôts
C. Valeur totale des biens et services produits sur un territoire donné en un an
D. Proportion de la population active sans emploi et en recherche d'emploi
E. Action de la banque centrale sur la masse monétaire et les taux d'intérêt

---

**Correction :**
1 → C | 2 → A | 3 → D | 4 → B | 5 → E

**Exemples de phrases :**
- *Le PIB de la France s'élève à environ 2 800 milliards d'euros en 2023.*
- *Une inflation de 5 % signifie qu'un panier de biens qui coûtait 100 € l'an dernier coûte 105 € aujourd'hui.*
- *Un taux de chômage de 7 % signifie que 7 actifs sur 100 sont sans emploi.*
- *La politique budgétaire expansionniste consiste à augmenter les dépenses publiques pour relancer l'économie.*
- *La BCE mène la politique monétaire de la zone euro en fixant les taux directeurs.*
""",
    },

    {
        "matiere": "SES", "niveau": "2nde",
        "activite_key": "ses_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Économie et société : besoins, biens et services",
        "texte_source": "Introduction à l'économie : besoins humains, biens économiques et libres, biens et services marchands/non marchands, rareté, agents économiques. Niveau 2nde.",
        "resultat": """## Questions de cours — Économie et société

---

**Question 1.** Qu'est-ce qu'un bien économique ?
- A) Un bien disponible en quantité illimitée et gratuit
- B) Un bien rare dont la production nécessite des ressources ✓
- C) Un service fourni uniquement par l'État
- D) Un bien uniquement matériel

**Question 2.** Quelle est la différence entre un bien marchand et un bien non marchand ?
- A) Un bien marchand est gratuit, un bien non marchand est payant
- B) Un bien marchand est vendu sur un marché, un bien non marchand est fourni gratuitement ou quasi-gratuitement ✓
- C) Les biens marchands sont uniquement produits par des entreprises publiques
- D) Il n'y a aucune différence

**Question 3.** Quels sont les trois grands agents économiques ?
- A) L'État, la banque et les entreprises
- B) Les ménages, les entreprises et les administrations publiques ✓
- C) Les consommateurs, les producteurs et les importateurs
- D) Les travailleurs, les chômeurs et les retraités

**Question 4.** La rareté en économie désigne :
- A) L'absence totale d'un bien
- B) Le fait que les ressources sont limitées face à des besoins illimités ✓
- C) Un bien de luxe réservé aux riches
- D) Un bien dont la production est interdite

**Question 5.** Le PIB mesure :
- A) La richesse totale accumulée dans un pays
- B) La valeur de tous les biens et services produits sur un territoire en une année ✓
- C) Le revenu moyen des ménages
- D) Les exportations nettes d'un pays

---

**Correction :** 1-B / 2-B / 3-B / 4-B / 5-B
""",
    },
    {
        "matiere": "SES", "niveau": "Terminale",
        "activite_key": "ses_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Mondialisation et inégalités",
        "texte_source": "Mondialisation : échanges commerciaux, firmes multinationales, IDE, division internationale du travail, inégalités de développement, IDH. Niveau Terminale SES.",
        "resultat": """## Questions de cours — Mondialisation et inégalités

---

**Question 1.** Qu'est-ce qu'un investissement direct à l'étranger (IDE) ?
- A) Un prêt accordé à un pays étranger par l'État
- B) L'implantation ou le rachat d'une entreprise dans un pays étranger pour contrôler son activité ✓
- C) L'achat d'actions en bourse à l'étranger
- D) Une aide publique au développement

**Question 2.** La division internationale du travail (DIT) désigne :
- A) La répartition des emplois entre hommes et femmes
- B) La spécialisation des pays dans certaines productions à l'échelle mondiale ✓
- C) Les inégalités de salaires entre pays riches et pauvres
- D) La délocalisation des emplois industriels

**Question 3.** L'IDH (Indice de Développement Humain) mesure :
- A) Uniquement le revenu par habitant
- B) Le niveau de vie, l'espérance de vie et le niveau d'éducation ✓
- C) Le taux de croissance économique d'un pays
- D) Le degré d'ouverture commerciale d'un pays

**Question 4.** La mondialisation accroît les inégalités car elle :
- A) Bénéficie de manière égale à tous les pays et tous les individus
- B) Profite surtout aux pays et individus déjà bien insérés dans les échanges, creusant les écarts ✓
- C) Réduit automatiquement la pauvreté dans tous les pays
- D) Supprime les firmes multinationales

**Question 5.** Quel organisme régule les échanges commerciaux mondiaux ?
- A) Le FMI
- B) La Banque mondiale
- C) L'Organisation Mondiale du Commerce (OMC) ✓
- D) L'ONU

---

**Correction :** 1-B / 2-B / 3-B / 4-B / 5-C
""",
    },

    # ─── NSI ─────────────────────────────────────────────────────────────────
    {
        "matiere": "NSI", "niveau": "Terminale",
        "activite_key": "nsi_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Identifier une structure de données", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Algorithmes de tri",
        "texte_source": "Algorithmes de tri : tri par insertion, tri par sélection, tri fusion. Complexité, principe, cas favorable/défavorable. Terminale NSI.",
        "resultat": """## Questions de cours — Algorithmes de tri

---

**Question 1.** Quelle est la complexité en moyenne du tri par insertion ?
- A) O(n)
- B) O(n log n)
- C) O(n²) ✓
- D) O(log n)

**Question 2.** Dans quel cas le tri par insertion est-il particulièrement efficace ?
- A) Quand la liste est triée en ordre décroissant
- B) Quand la liste est déjà presque triée ✓
- C) Quand la liste contient des doublons
- D) Quand la liste est très longue

**Question 3.** Le tri fusion repose sur quel principe algorithmique ?
- A) La programmation dynamique
- B) Le backtracking
- C) Diviser pour régner ✓
- D) L'algorithme glouton

**Question 4.** Quelle est la complexité en pire cas du tri fusion ?
- A) O(n²)
- B) O(n)
- C) O(n log n) ✓
- D) O(log n)

**Question 5.** Le tri par sélection consiste à :
- A) Insérer chaque élément à sa place dans une sous-liste triée
- B) Trouver le minimum de la partie non triée et le placer en tête ✓
- C) Diviser la liste en deux moitiés récursivement
- D) Comparer des éléments adjacents et les échanger

---

**Correction :** 1-C / 2-B / 3-C / 4-C / 5-B
""",
    },
    {
        "matiere": "NSI", "niveau": "1ère",
        "activite_key": "nsi_questions_support", "activite_label": "Questions sur un support",
        "sous_type": "Lecture de code Python", "nb": 4, "avec_correction": True,
        "objet": "[Exemple] Lecture de code Python — Les fonctions",
        "texte_source": """def factorielle(n):
    if n == 0:
        return 1
    return n * factorielle(n - 1)

print(factorielle(4))""",
        "resultat": """## Questions sur un support — Lecture de code Python

**Code à analyser :**
```python
def factorielle(n):
    if n == 0:
        return 1
    return n * factorielle(n - 1)

print(factorielle(4))
```

---

**Question 1.** Quel résultat affiche `print(factorielle(4))` ?
- A) 4
- B) 16
- C) 24 ✓
- D) 10

*Calcul : 4 × 3 × 2 × 1 = 24*

**Question 2.** Comment appelle-t-on une fonction qui s'appelle elle-même ?
- A) Une fonction itérative
- B) Une fonction récursive ✓
- C) Une fonction lambda
- D) Une fonction imbriquée

**Question 3.** Quel est le rôle de la condition `if n == 0` dans cette fonction ?
- A) Vérifier que n est positif
- B) Initialiser le calcul
- C) Constituer le cas de base pour arrêter la récursion ✓
- D) Optimiser le temps d'exécution

**Question 4.** Que se passerait-il si on appelait `factorielle(-1)` ?
- A) Elle retournerait 0
- B) Elle retournerait 1
- C) Elle provoquerait une erreur de dépassement de pile (récursion infinie) ✓
- D) Elle retournerait -1

---

**Correction :** 1-C / 2-B / 3-C / 4-C
""",
    },

    # ─── PHILOSOPHIE ─────────────────────────────────────────────────────────
    {
        "matiere": "Philosophie", "niveau": "Terminale",
        "activite_key": "philo_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Définir un concept", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — La liberté et le libre arbitre",
        "texte_source": "Notion : La liberté. Auteurs : Descartes, Sartre, Spinoza. Concepts : libre arbitre, déterminisme, liberté comme conquête. Terminale.",
        "resultat": """## Questions de cours — La liberté et le libre arbitre

---

**Question 1.** Pour Descartes, le libre arbitre est :
- A) Une illusion créée par nos passions
- B) La capacité infinie de la volonté à choisir, indépendamment de l'entendement ✓
- C) Le résultat de nos conditionnements sociaux
- D) Une propriété exclusive de Dieu

**Question 2.** Quelle est la position de Spinoza sur le libre arbitre ?
- A) Il défend un libre arbitre absolu
- B) Il considère que la liberté consiste à obéir à sa propre nature en la comprenant ✓
- C) Il rejette toute forme de liberté
- D) Il pense que la liberté est un droit naturel

**Question 3.** Selon Sartre, l'existence précède l'essence signifie que :
- A) L'homme est déterminé par sa nature
- B) L'homme se définit par ses choix et ses actes ✓
- C) L'homme naît libre mais partout il est dans les fers
- D) La liberté est une illusion existentielle

**Question 4.** Le déterminisme affirme que :
- A) L'homme est entièrement libre de ses choix
- B) Tous les événements, y compris les actions humaines, sont causalement déterminés ✓
- C) La liberté est une valeur morale absolue
- D) Seul Dieu est déterminant dans nos actes

**Question 5.** "L'homme est condamné à être libre." Cette formule est de :
- A) Descartes
- B) Kant
- C) Sartre ✓
- D) Hegel

---

**Correction :** 1-B / 2-B / 3-B / 4-B / 5-C
""",
    },
    {
        "matiere": "Philosophie", "niveau": "Terminale",
        "activite_key": "philo_analyse_contenu", "activite_label": "Analyse de contenu",
        "sous_type": "Analyse d'un texte d'auteur", "nb": None, "avec_correction": True,
        "objet": "[Exemple] Analyse — Cogito de Descartes (Méditations Métaphysiques)",
        "texte_source": "« Je pense, donc je suis » (Cogito ergo sum). Extrait des Méditations Métaphysiques, Descartes. Première certitude absolue après le doute méthodique.",
        "resultat": """## Analyse de texte — Le Cogito de Descartes

**Texte support :**
> *« Mais aussitôt après je pris garde que, pendant que je voulais ainsi penser que tout était faux, il fallait nécessairement que moi qui le pensais fusse quelque chose. Et remarquant que cette vérité, je pense, donc je suis, était si ferme et si assurée, que toutes les plus extravagantes suppositions des sceptiques n'étaient pas capables de l'ébranler, je jugeai que je pouvais la recevoir sans scrupule pour le premier principe de la philosophie que je cherchais. »*
> — Descartes, *Discours de la méthode*, 1637

---

**Consignes d'analyse :**

**1. Identifier la thèse principale**
Quelle est la première vérité que Descartes établit dans ce texte ? Pourquoi est-elle indubitable même face au doute radical ?

**2. Analyser l'argumentation**
Reconstituez le raisonnement : comment Descartes passe-t-il du doute à la certitude ? Quel est le rôle de l'acte de penser dans cette démarche ?

**3. Expliquer les concepts clés**
- *Je pense* : que désigne exactement cet acte chez Descartes ?
- *Donc je suis* : en quoi l'existence est-elle ici garantie par la pensée ?
- *Premier principe* : pourquoi le cogito peut-il servir de fondement à toute la philosophie ?

**4. Ouverture critique**
Un philosophe matérialiste pourrait-il contester ce raisonnement ? Que dirait Hume à propos de l'identité du « je » dans le cogito ?

---

**Éléments de correction :**
- La thèse : l'existence du sujet pensant est la seule certitude absolue résistant au doute hyperbolique
- Le raisonnement : pour douter, il faut penser ; pour penser, il faut exister → existence prouvée par l'acte de pensée lui-même
- Limite : Hume conteste l'idée d'un « moi » stable — il ne perçoit que des impressions successives, pas un sujet unifié
""",
    },

    # ─── LANGUES VIVANTES ────────────────────────────────────────────────────
    {
        "matiere": "Langues Vivantes (LV)", "niveau": "2nde",
        "activite_key": "lv_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Règle grammaticale", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM Anglais — Le present perfect",
        "texte_source": "Le present perfect en anglais : formation (have/has + participe passé), emplois (expérience, résultat présent, durée avec since/for). Niveau 2nde.",
        "resultat": """## Questions de cours — Le present perfect (Anglais)

---

**Question 1.** Comment forme-t-on le present perfect ?
- A) Sujet + did + verbe à l'infinitif
- B) Sujet + have/has + participe passé ✓
- C) Sujet + be + verbe en -ing
- D) Sujet + will + infinitif

**Question 2.** Quelle phrase est correcte au present perfect ?
- A) She has went to Paris last year.
- B) She has gone to Paris. ✓
- C) She have go to Paris.
- D) She is gone to Paris yesterday.

**Question 3.** On utilise le present perfect (et non le prétérit) pour :
- A) Décrire une action terminée à un moment précis du passé
- B) Exprimer une action dont le résultat est encore présent ou pertinent maintenant ✓
- C) Raconter une suite d'événements passés
- D) Parler d'habitudes dans le passé

**Question 4.** Complète avec *since* ou *for* : "I have lived in Lyon ___ ten years."
- A) since
- B) for ✓

*For = durée (ten years) / Since = point de départ (2015)*

**Question 5.** Quelle phrase exprime une expérience de vie au present perfect ?
- A) I went to New York in 2019.
- B) I have never eaten sushi. ✓
- C) I am eating sushi right now.
- D) I will eat sushi tomorrow.

---

**Correction :** 1-B / 2-B / 3-B / 4-B / 5-B
""",
    },
    {
        "matiere": "Langues Vivantes (LV)", "niveau": "2nde",
        "activite_key": "lv_comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "Compréhension écrite", "nb": 4, "avec_correction": True,
        "objet": "[Exemple] Compréhension écrite — The Environment (Anglais)",
        "texte_source": "Climate change is one of the biggest challenges facing humanity today. Rising temperatures, melting ice caps, and extreme weather events are all signs that the planet is warming. Scientists agree that human activities, particularly the burning of fossil fuels, are the main cause. Governments and individuals must act now to reduce carbon emissions and protect our future.",
        "resultat": """## Questions de compréhension — The Environment

**Texte :**
*Climate change is one of the biggest challenges facing humanity today. Rising temperatures, melting ice caps, and extreme weather events are all signs that the planet is warming. Scientists agree that human activities, particularly the burning of fossil fuels, are the main cause. Governments and individuals must act now to reduce carbon emissions and protect our future.*

---

**Question 1.** What is the main topic of this text?
- A) Natural disasters in history
- B) Climate change and its causes ✓
- C) The history of fossil fuels
- D) Political debates about the environment

**Question 2.** According to the text, what are signs that the planet is warming? (Choose 2)
- A) Rising temperatures ✓
- B) Increasing biodiversity
- C) Melting ice caps ✓
- D) Falling sea levels

**Question 3.** What do scientists identify as the main cause of climate change?
- A) Natural volcanic activity
- B) Changes in solar activity
- C) Human activities, especially burning fossil fuels ✓
- D) Deforestation alone

**Question 4.** What does the text call for?
- A) More research before taking action
- B) Immediate action to reduce carbon emissions ✓
- C) Government control of all industries
- D) Individual action only, not government involvement

---

**Correction :** 1-B / 2-A & C / 3-C / 4-B
""",
    },

    {
        "matiere": "Langues Vivantes (LV)", "niveau": "6e",
        "activite_key": "lv_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Règle grammaticale", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM Anglais — Se présenter et le présent simple",
        "texte_source": "Anglais débutant : verbe to be, présent simple, vocabulaire de la famille, chiffres, couleurs, se présenter. Niveau 6e.",
        "resultat": """## Questions de cours — Se présenter et le présent simple (Anglais)

---

**Question 1.** Comment dit-on « Je m'appelle » en anglais ?
- A) I am called...
- B) My name is... ✓
- C) I have a name...
- D) Call me...

**Question 2.** Quelle est la bonne conjugaison du verbe *to be* à la 3e personne du singulier ?
- A) I am
- B) You are
- C) She is ✓
- D) They are

**Question 3.** Comment dit-on « J'ai 12 ans » en anglais ?
- A) I have 12 years
- B) I am 12 years old ✓
- C) My age is 12 years
- D) I count 12 years

**Question 4.** Quelle question pose-t-on pour demander la nationalité ?
- A) Where do you live?
- B) What is your job?
- C) Where are you from? ✓
- D) How old are you?

**Question 5.** Complète : « She ___ a student. »
- A) have
- B) are
- C) is ✓
- D) am

---

**Correction :** 1-B / 2-C / 3-B / 4-C / 5-C
""",
    },
    {
        "matiere": "Langues Vivantes (LV)", "niveau": "5e",
        "activite_key": "lv_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Règle grammaticale", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM Anglais — Le prétérit simple (past simple)",
        "texte_source": "Le prétérit simple en anglais : formation des verbes réguliers (-ed) et irréguliers, questions et négations au passé, marqueurs temporels. Niveau 5e.",
        "resultat": """## Questions de cours — Le prétérit simple (Anglais)

---

**Question 1.** Comment forme-t-on le prétérit des verbes réguliers ?
- A) Verbe + -ing
- B) Verbe + -ed ✓
- C) Did + verbe
- D) Verbe + -s

**Question 2.** Quelle est la forme correcte de la question au prétérit ?
- A) She went to school yesterday?
- B) Did she go to school yesterday? ✓
- C) Does she went to school yesterday?
- D) She did go to school yesterday?

**Question 3.** Quel est le prétérit du verbe irrégulier *go* ?
- A) Goed
- B) Going
- C) Went ✓
- D) Gone

**Question 4.** La phrase négative au prétérit est :
- A) He not played football.
- B) He didn't play football. ✓
- C) He doesn't played football.
- D) He not did play football.

**Question 5.** Quel marqueur temporel indique le plus souvent le prétérit ?
- A) Now
- B) Usually
- C) Yesterday ✓
- D) Tomorrow

---

**Correction :** 1-B / 2-B / 3-C / 4-B / 5-C
""",
    },
    {
        "matiere": "Langues Vivantes (LV)", "niveau": "4e",
        "activite_key": "lv_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Règle grammaticale", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM Anglais — Les modaux (can, must, should, might)",
        "texte_source": "Les verbes modaux en anglais : can/could (capacité, permission), must/have to (obligation), should (conseil), might/may (possibilité). Niveau 4e.",
        "resultat": """## Questions de cours — Les modaux (Anglais)

---

**Question 1.** Quel modal exprime une obligation forte ?
- A) Should
- B) Might
- C) Must ✓
- D) Can

**Question 2.** Quelle phrase exprime une suggestion ou un conseil ?
- A) You must eat vegetables.
- B) You can eat vegetables.
- C) You should eat vegetables. ✓
- D) You might eat vegetables.

**Question 3.** Quelle est la règle grammaticale des modaux ?
- A) Ils sont suivis de l'infinitif avec *to*
- B) Ils s'accordent avec le sujet (-s à la 3e personne)
- C) Ils sont suivis de l'infinitif sans *to* ✓
- D) Ils forment le passé avec *did*

**Question 4.** « It ___ rain tomorrow. » (possibilité) :
- A) must
- B) should
- C) might ✓
- D) can

**Question 5.** La négation de *must* pour exprimer l'interdiction est :
- A) Don't must
- B) Mustn't ✓
- C) Can't
- D) Shouldn't

---

**Correction :** 1-C / 2-C / 3-C / 4-C / 5-B
""",
    },
    {
        "matiere": "Langues Vivantes (LV)", "niveau": "3e",
        "activite_key": "lv_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Règle grammaticale", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM Anglais — Le conditionnel (would + if clauses)",
        "texte_source": "Le conditionnel en anglais : second conditionnel (If + past simple, would + infinitif), premier conditionnel (If + present simple, will + infinitif). Niveau 3e.",
        "resultat": """## Questions de cours — Le conditionnel (Anglais)

---

**Question 1.** Quelle phrase est au premier conditionnel (situation réelle/probable) ?
- A) If I had money, I would buy a car.
- B) If it rains, I will stay home. ✓
- C) If I were rich, I would travel.
- D) If she studied, she would pass.

**Question 2.** Quelle phrase est au deuxième conditionnel (situation imaginaire/irréelle) ?
- A) If I study, I will pass the exam.
- B) If it rains, we won't go out.
- C) If I had wings, I would fly. ✓
- D) If you call me, I will answer.

**Question 3.** Complète : « If I ___ (be) a teacher, I ___ (give) less homework. »
- A) am / will give
- B) were / would give ✓
- C) was / will give
- D) am / would give

**Question 4.** Dans le deuxième conditionnel, quel temps utilise-t-on dans la proposition en *if* ?
- A) Le présent simple
- B) Le futur
- C) Le prétérit simple ✓
- D) Le present perfect

**Question 5.** Quelle question correspond au deuxième conditionnel ?
- A) What will you do if you miss the bus?
- B) What would you do if you won the lottery? ✓
- C) What do you do when you are bored?
- D) What did you do if you were late?

---

**Correction :** 1-B / 2-C / 3-B / 4-C / 5-B
""",
    },
    {
        "matiere": "Langues Vivantes (LV)", "niveau": "1ère",
        "activite_key": "lv_comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "Compréhension écrite", "nb": 4, "avec_correction": True,
        "objet": "[Exemple] Compréhension écrite — Social Media and Youth (Anglais)",
        "texte_source": "Social media has transformed the way young people communicate and access information. While platforms like Instagram and TikTok offer creativity and connection, they also raise concerns about mental health, cyberbullying, and addiction. Studies show that teenagers who spend more than three hours a day on social media are more likely to experience anxiety and depression. However, many experts argue that the problem lies not in the technology itself, but in how it is used.",
        "resultat": """## Questions de compréhension — Social Media and Youth

**Texte :**
*Social media has transformed the way young people communicate and access information. While platforms like Instagram and TikTok offer creativity and connection, they also raise concerns about mental health, cyberbullying, and addiction. Studies show that teenagers who spend more than three hours a day on social media are more likely to experience anxiety and depression. However, many experts argue that the problem lies not in the technology itself, but in how it is used.*

---

**Question 1.** What is the main idea of this text?
- A) Social media should be banned for teenagers
- B) Social media has both positive and negative effects on young people ✓
- C) Instagram and TikTok are the most popular apps
- D) Technology is always harmful to mental health

**Question 2.** According to studies, what is the risk for teenagers who spend more than 3 hours daily on social media?
- A) They become more creative
- B) They develop better social skills
- C) They are more likely to experience anxiety and depression ✓
- D) They spend less time on schoolwork

**Question 3.** What do many experts suggest about social media problems?
- A) The technology itself is always harmful
- B) Young people should never use social media
- C) The issue depends on how social media is used, not the technology itself ✓
- D) Parents should control all online activity

**Question 4.** Find a word in the text meaning « dépendance ».
- A) Cyberbullying
- B) Addiction ✓
- C) Concern
- D) Creativity

---

**Correction :** 1-B / 2-C / 3-C / 4-B
""",
    },
    {
        "matiere": "Langues Vivantes (LV)", "niveau": "Terminale",
        "activite_key": "lv_comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "Compréhension écrite", "nb": 4, "avec_correction": True,
        "objet": "[Exemple] Compréhension écrite — Artificial Intelligence and Society (Anglais)",
        "texte_source": "Artificial intelligence is no longer science fiction. From facial recognition to medical diagnosis, AI systems are making decisions that affect millions of people every day. Proponents argue that AI increases efficiency and can solve complex global challenges such as climate change or disease. Critics, however, warn of biases embedded in algorithms, the risk of mass unemployment, and the erosion of privacy. The question is not whether AI will change society, but how we choose to govern it.",
        "resultat": """## Questions de compréhension — Artificial Intelligence and Society

**Texte :**
*Artificial intelligence is no longer science fiction. From facial recognition to medical diagnosis, AI systems are making decisions that affect millions of people every day. Proponents argue that AI increases efficiency and can solve complex global challenges such as climate change or disease. Critics, however, warn of biases embedded in algorithms, the risk of mass unemployment, and the erosion of privacy. The question is not whether AI will change society, but how we choose to govern it.*

---

**Question 1.** What is the main argument of those who support AI?
- A) AI will replace all human jobs
- B) AI increases efficiency and can address major global problems ✓
- C) AI is still science fiction
- D) AI is only useful in medicine

**Question 2.** Which concern about AI is NOT mentioned in the text?
- A) Algorithmic bias
- B) Mass unemployment
- C) Privacy erosion
- D) Environmental damage caused by data centres ✓

**Question 3.** What does the author suggest in the final sentence?
- A) AI will not change society
- B) AI development should be stopped
- C) The key challenge is governance and regulation of AI ✓
- D) AI benefits outweigh its risks

**Question 4.** Find a word in the text meaning « partisans, défenseurs ».
- A) Critics
- B) Proponents ✓
- C) Algorithms
- D) Challenges

---

**Correction :** 1-B / 2-D / 3-C / 4-B
""",
    },

    # ─── TECHNOLOGIE ─────────────────────────────────────────────────────────
    {
        "matiere": "Technologie", "niveau": "5e",
        "activite_key": "techno_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Le développement durable",
        "texte_source": "Développement durable : définition, trois piliers (économique, social, environnemental), éco-conception, cycle de vie d'un produit. Niveau 5e.",
        "resultat": """## Questions de cours — Le développement durable

---

**Question 1.** Quels sont les trois piliers du développement durable ?
- A) Politique, économique, militaire
- B) Environnemental, économique, social ✓
- C) Technologique, scientifique, humain
- D) Local, national, international

**Question 2.** Que signifie « éco-concevoir » un produit ?
- A) Le fabriquer le moins cher possible
- B) Le concevoir en tenant compte de son impact environnemental tout au long de son cycle de vie ✓
- C) Le rendre esthétique et moderne
- D) Le fabriquer uniquement avec des matériaux recyclés

**Question 3.** Quelles sont les étapes du cycle de vie d'un produit ?
- A) Création → vente → destruction
- B) Extraction → fabrication → distribution → utilisation → fin de vie ✓
- C) Conception → production → consommation
- D) Idée → prototype → marché

**Question 4.** Parmi ces actions, laquelle contribue au développement durable ?
- A) Jeter un téléphone dès qu'un nouveau modèle sort
- B) Réparer un appareil électroménager plutôt que de le remplacer ✓
- C) Acheter des produits avec le maximum d'emballage
- D) Utiliser sa voiture pour de très courts trajets

**Question 5.** Que signifie le logo « point vert » sur un emballage ?
- A) Le produit est biodégradable
- B) Le fabricant a contribué financièrement au recyclage des emballages ✓
- C) L'emballage est entièrement recyclé
- D) Le produit est fabriqué en France

---

**Correction :** 1-B / 2-B / 3-B / 4-B / 5-B
""",
    },
    {
        "matiere": "Technologie", "niveau": "5e",
        "activite_key": "techno_étude_de_vocabulaire", "activite_label": "Étude de vocabulaire - notions clés",
        "sous_type": "Vocabulaire mécanique", "nb": None, "avec_correction": True,
        "objet": "[Exemple] Vocabulaire — Les matériaux et leurs propriétés",
        "texte_source": "Les familles de matériaux en technologie : métaux, plastiques, bois, céramiques, composites. Propriétés mécaniques, thermiques, électriques. Niveau 5e.",
        "resultat": """## Étude de vocabulaire — Les matériaux et leurs propriétés

**Consigne :** Associe chaque terme à sa définition, puis cite un exemple de matériau pour chaque famille.

---

**Termes à définir :**

| Terme | Définition |
|---|---|
| 1. Ductilité | A. Capacité d'un matériau à conduire la chaleur |
| 2. Conductivité thermique | B. Capacité à se déformer sans se casser (s'étirer en fil) |
| 3. Résistance à la traction | C. Propriété d'un matériau à résister à un effort qui tend à l'étirer |
| 4. Matériau composite | D. Association de deux matériaux ou plus pour combiner leurs propriétés |
| 5. Isolant électrique | E. Matériau qui ne laisse pas passer le courant électrique |

---

**Correction :**
1 → B | 2 → A | 3 → C | 4 → D | 5 → E

---

**Exemples par famille de matériaux :**

| Famille | Exemple | Propriété principale |
|---|---|---|
| Métaux | Acier | Résistance mécanique, conductivité |
| Plastiques | Polypropylène (PP) | Légèreté, isolant électrique |
| Bois | Chêne | Résistance naturelle, renouvelable |
| Céramiques | Porcelaine | Résistance à la chaleur, fragilité |
| Composites | Fibre de carbone | Légèreté + rigidité |
""",
    },

    {
        "matiere": "Technologie", "niveau": "6e",
        "activite_key": "techno_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Les objets techniques et leurs fonctions",
        "texte_source": "Les objets techniques : fonction d'usage, fonction d'estime, constituants, matériaux. Évolution des objets techniques. Niveau 6e.",
        "resultat": """## Questions de cours — Les objets techniques

---

**Question 1.** Qu'est-ce que la fonction d'usage d'un objet technique ?
- A) Ce que l'objet représente pour son propriétaire (beauté, prestige)
- B) Ce à quoi l'objet sert, son utilité principale ✓
- C) La matière dont l'objet est fabriqué
- D) Le prix de l'objet

**Question 2.** Un stylo a pour fonction d'usage :
- A) Être beau et moderne
- B) Écrire ✓
- C) Être recyclable
- D) Coûter peu cher

**Question 3.** Qu'est-ce qu'un constituant d'un objet technique ?
- A) La matière première utilisée
- B) La notice d'utilisation
- C) Une pièce ou un sous-ensemble qui compose l'objet ✓
- D) L'emballage de l'objet

**Question 4.** Pourquoi un objet technique évolue-t-il au fil du temps ?
- A) Uniquement pour changer de couleur
- B) Pour s'adapter aux nouveaux besoins, aux nouvelles technologies et aux contraintes environnementales ✓
- C) Parce que les anciennes versions sont interdites
- D) Pour augmenter son prix de vente

**Question 5.** La fonction d'estime d'un objet correspond à :
- A) Son efficacité technique
- B) Sa durée de vie
- C) L'attrait esthétique ou le prestige qu'il procure à son propriétaire ✓
- D) Sa résistance aux chocs

---

**Correction :** 1-B / 2-B / 3-C / 4-B / 5-C
""",
    },
    {
        "matiere": "Technologie", "niveau": "4e",
        "activite_key": "techno_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Le numérique et les réseaux",
        "texte_source": "Le numérique : codage binaire, réseau informatique, Internet, protocoles de communication, sécurité des données. Niveau 4e.",
        "resultat": """## Questions de cours — Le numérique et les réseaux

---

**Question 1.** Le codage binaire utilise uniquement les chiffres :
- A) 0, 1, 2
- B) 0 et 1 ✓
- C) 1 à 9
- D) 0 à 7

**Question 2.** Qu'est-ce qu'un réseau informatique ?
- A) Un ensemble de câbles électriques
- B) Un ensemble d'ordinateurs et d'équipements interconnectés pour partager des ressources et des données ✓
- C) Un logiciel de sécurité
- D) Un type de processeur

**Question 3.** Quel protocole est à la base du fonctionnement d'Internet ?
- A) WiFi
- B) Bluetooth
- C) TCP/IP ✓
- D) USB

**Question 4.** Un mot de passe sécurisé doit contenir :
- A) Uniquement des chiffres
- B) Le prénom de l'utilisateur
- C) Des majuscules, minuscules, chiffres et caractères spéciaux ✓
- D) Moins de 6 caractères pour être mémorisable

**Question 5.** Le chiffrement des données sur un site web (HTTPS) sert à :
- A) Accélérer le chargement des pages
- B) Protéger les données échangées contre les interceptions ✓
- C) Bloquer les publicités
- D) Sauvegarder les données sur le serveur

---

**Correction :** 1-B / 2-B / 3-C / 4-C / 5-B
""",
    },
    {
        "matiere": "Technologie", "niveau": "3e",
        "activite_key": "techno_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Les systèmes automatisés",
        "texte_source": "Systèmes automatisés : capteurs, actionneurs, unité de traitement, boucle fermée/ouverte, programmation (algorithme). Exemples : portail automatique, feu de circulation. Niveau 3e.",
        "resultat": """## Questions de cours — Les systèmes automatisés

---

**Question 1.** Quel est le rôle d'un capteur dans un système automatisé ?
- A) Exécuter une action sur l'environnement
- B) Traiter les informations reçues
- C) Acquérir des informations sur l'état du système ou de l'environnement ✓
- D) Alimenter le système en énergie

**Question 2.** Un actionneur dans un système automatisé :
- A) Mesure une grandeur physique
- B) Transforme un signal de commande en action sur l'environnement ✓
- C) Stocke les données
- D) Communique avec l'utilisateur

**Question 3.** Un système en boucle fermée se distingue par :
- A) L'absence de capteur
- B) L'absence de retour d'information vers l'unité de traitement
- C) La présence d'une rétroaction : la sortie est comparée à la consigne pour ajuster la commande ✓
- D) La commande manuelle obligatoire de l'opérateur

**Question 4.** Dans un algorithme de contrôle d'un portail automatique, quelle instruction permet de répéter une action ?
- A) SI ... ALORS
- B) TANT QUE ... FAIRE ✓
- C) AFFICHER
- D) LIRE

**Question 5.** Un thermostat de chauffage est un exemple de système :
- A) En boucle ouverte
- B) Sans capteur
- C) En boucle fermée (il compare la température mesurée à la consigne) ✓
- D) Manuel uniquement

---

**Correction :** 1-C / 2-B / 3-C / 4-B / 5-C
""",
    },

    # ─── ARTS ────────────────────────────────────────────────────────────────
    {
        "matiere": "Arts", "niveau": "4e",
        "activite_key": "arts_comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "Compréhension d'une œuvre", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — L'impressionnisme",
        "texte_source": "Mouvement impressionniste : Monet, Renoir, Degas, Pissarro. Caractéristiques : touche visible, lumière naturelle, scènes de vie moderne, plein air. 1874-1886.",
        "resultat": """## Questions de compréhension — L'impressionnisme

---

**Question 1.** En quelle année a lieu la première exposition impressionniste ?
- A) 1863
- B) 1874 ✓
- C) 1886
- D) 1900

**Question 2.** D'où vient le terme « impressionnisme » ?
- A) D'une déclaration du peintre Monet
- B) D'un article de critique d'art se moquant du tableau *Impression, soleil levant* de Monet ✓
- C) D'un manifeste des peintres du mouvement
- D) D'un musée qui a exposé ces œuvres en premier

**Question 3.** Quelle technique caractérise la peinture impressionniste ?
- A) Des contours précis et des couleurs uniformes
- B) Des touches visibles, rapides, qui reconstituent la lumière et le mouvement ✓
- C) L'utilisation exclusive de la peinture à l'huile épaisse
- D) La représentation détaillée de scènes historiques

**Question 4.** Quelle lumière les impressionnistes privilégient-ils ?
- A) La lumière artificielle des ateliers
- B) La lumière naturelle, souvent peinte en plein air ✓
- C) La lumière symbolique et religieuse
- D) La lumière du soir uniquement

**Question 5.** Lequel de ces peintres N'est PAS impressionniste ?
- A) Claude Monet
- B) Auguste Renoir
- C) Salvador Dalí ✓
- D) Edgar Degas

---

**Correction :** 1-B / 2-B / 3-B / 4-B / 5-C
""",
    },
    {
        "matiere": "Arts", "niveau": "4e",
        "activite_key": "arts_questions_support", "activite_label": "Questions sur un support",
        "sous_type": "Analyse d'une œuvre plastique", "nb": 4, "avec_correction": True,
        "objet": "[Exemple] Analyse — Les Nymphéas de Monet",
        "texte_source": "Les Nymphéas, Claude Monet (série de 1896 à 1926). Huile sur toile. Représentation du bassin aux nénuphars du jardin de Giverny. Traitement de la lumière, du reflet, de la surface de l'eau.",
        "resultat": """## Questions sur un support — *Les Nymphéas*, Claude Monet

**Œuvre étudiée :** *Les Nymphéas* (série), Claude Monet, entre 1896 et 1926. Huile sur toile. Musée de l'Orangerie, Paris.

---

**Question 1.** Quel élément naturel constitue le sujet principal de cette série ?
- A) Un ciel nuageux au coucher du soleil
- B) La surface d'un bassin avec des nénuphars et leurs reflets ✓
- C) Des arbres en fleurs au printemps
- D) Une rivière en forêt

**Question 2.** Comment Monet traite-t-il la limite entre le ciel et l'eau dans ces toiles ?
- A) Il dessine une ligne d'horizon claire et précise
- B) Il efface cette limite, mêlant reflets et plantes dans une composition sans horizon ✓
- C) Il peint le ciel en bleu uni au-dessus de l'eau
- D) Il ne peint que la surface de l'eau, sans aucun reflet

**Question 3.** Quelle technique picturale Monet utilise-t-il pour rendre la lumière changeante de l'eau ?
- A) Des aplats de couleur uniformes
- B) Des touches courtes et colorées qui se superposent ✓
- C) Des glacis transparents et lisses
- D) Des lignes de contour précises remplies de couleur

**Question 4.** Quel effet cette série de peintures cherche-t-elle à provoquer chez le spectateur ?
- A) Un sentiment de peur face à la nature
- B) Une réflexion intellectuelle sur la condition humaine
- C) Une expérience sensorielle d'immersion dans la lumière et la couleur ✓
- D) Un sentiment de nostalgie pour un monde disparu

---

**Correction :** 1-B / 2-B / 3-B / 4-C
""",
    },

    {
        "matiere": "Arts", "niveau": "6e",
        "activite_key": "arts_comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "Compréhension d'une œuvre", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — La couleur et Matisse",
        "texte_source": "Henri Matisse et l'usage de la couleur. Fauvisme : couleurs pures, expressives, non réalistes. La Danse (1910), La Tristesse du Roi (1952), découpages colorés. Niveau 6e.",
        "resultat": """## Questions de compréhension — La couleur et Matisse

---

**Question 1.** Le mouvement artistique auquel Matisse appartient au début de sa carrière s'appelle :
- A) L'impressionnisme
- B) Le cubisme
- C) Le fauvisme ✓
- D) Le surréalisme

**Question 2.** Pourquoi les fauves ont-ils été ainsi nommés ?
- A) Parce qu'ils peignaient des animaux sauvages
- B) Parce qu'un critique d'art s'est moqué de leurs couleurs violentes en les traitant de « fauves » ✓
- C) Parce qu'ils utilisaient des pinceaux épais
- D) Parce qu'ils exposaient dans un zoo

**Question 3.** Dans les œuvres de Matisse, la couleur est utilisée pour :
- A) Reproduire fidèlement la réalité
- B) Exprimer des émotions et des sensations plutôt que pour imiter la nature ✓
- C) Créer des illusions de profondeur uniquement
- D) Représenter uniquement des scènes religieuses

**Question 4.** Quelle technique artistique Matisse développe-t-il vers la fin de sa vie ?
- A) La peinture à l'huile épaisse
- B) La sculpture sur marbre
- C) Les découpages colorés (papiers gouachés découpés) ✓
- D) La fresque murale

**Question 5.** Quelles sont les trois couleurs primaires ?
- A) Vert, orange, violet
- B) Rouge, bleu, jaune ✓
- C) Blanc, noir, gris
- D) Rouge, vert, bleu

---

**Correction :** 1-C / 2-B / 3-B / 4-C / 5-B
""",
    },
    {
        "matiere": "Arts", "niveau": "5e",
        "activite_key": "arts_comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "Compréhension d'une œuvre", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — La sculpture et Rodin",
        "texte_source": "Auguste Rodin et la sculpture moderne. Le Penseur (1902), Les Bourgeois de Calais (1895), La Porte de l'Enfer. Matériaux : bronze, marbre. Expression des émotions dans la sculpture. Niveau 5e.",
        "resultat": """## Questions de compréhension — La sculpture et Rodin

---

**Question 1.** Quelle est la sculpture la plus célèbre de Rodin ?
- A) La Vénus de Milo
- B) La Liberté guidant le peuple
- C) Le Penseur ✓
- D) Le David

**Question 2.** En quelle matière Le Penseur est-il principalement réalisé ?
- A) Marbre blanc
- B) Bronze ✓
- C) Bois
- D) Pierre calcaire

**Question 3.** Quelle est l'innovation principale de Rodin dans la sculpture du XIXe siècle ?
- A) L'utilisation de l'acier inoxydable
- B) La représentation des muscles et des émotions avec un réalisme expressif intense ✓
- C) La création de sculptures uniquement abstraites
- D) L'introduction de la couleur dans la sculpture

**Question 4.** Les Bourgeois de Calais représentent :
- A) Des soldats victorieux
- B) Six habitants de Calais qui se sacrifient pour sauver leur ville lors du siège anglais de 1347 ✓
- C) Des aristocrates au XVIIe siècle
- D) Des personnages mythologiques grecs

**Question 5.** La sculpture en ronde-bosse est une sculpture :
- A) Fixée contre un mur, visible de face uniquement
- B) Entièrement dégagée, visible sous tous les angles ✓
- C) Creusée dans une paroi rocheuse
- D) Réalisée uniquement en petits formats

---

**Correction :** 1-C / 2-B / 3-B / 4-B / 5-B
""",
    },
    {
        "matiere": "Arts", "niveau": "3e",
        "activite_key": "arts_comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "Compréhension d'une œuvre", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — L'art contemporain (Warhol, Basquiat)",
        "texte_source": "Art contemporain : pop art (Andy Warhol), street art (Jean-Michel Basquiat), art conceptuel. Remise en question de la notion d'œuvre d'art, médias et société de consommation. Niveau 3e.",
        "resultat": """## Questions de compréhension — L'art contemporain

---

**Question 1.** Andy Warhol est le figure principale d'un mouvement appelé :
- A) Le cubisme
- B) Le pop art ✓
- C) Le surréalisme
- D) L'expressionnisme abstrait

**Question 2.** Quelle est la démarche principale de Warhol dans ses œuvres (Marilyn, boîtes Campbell's) ?
- A) Critiquer la pollution industrielle
- B) Peindre des paysages naturels américains
- C) Utiliser des images de la culture de masse et de la société de consommation ✓
- D) Reproduire des œuvres de la Renaissance

**Question 3.** Jean-Michel Basquiat a commencé sa carrière artistique comme :
- A) Sculpteur classique
- B) Photographe de mode
- C) Graffeur dans les rues de New York ✓
- D) Musicien classique

**Question 4.** L'art conceptuel affirme que :
- A) La technique et le savoir-faire manuel sont les seuls critères de l'art
- B) C'est l'idée ou le concept derrière l'œuvre qui est plus importante que sa réalisation matérielle ✓
- C) L'art doit toujours être beau et harmonieux
- D) L'art ne peut exister que dans les musées

**Question 5.** Quelle œuvre de Marcel Duchamp est considérée comme fondatrice de l'art conceptuel ?
- A) Les Demoiselles d'Avignon
- B) La Nuit étoilée
- C) Fontaine (un urinoir signé) ✓
- D) Le Cri

---

**Correction :** 1-B / 2-C / 3-C / 4-B / 5-C
""",
    },
    {
        "matiere": "Arts", "niveau": "2nde",
        "activite_key": "arts_comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "Compréhension d'une œuvre", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — L'architecture : Le Corbusier et l'architecture moderne",
        "texte_source": "Architecture moderne : Le Corbusier, les 5 points de l'architecture moderne (pilotis, toit-terrasse, plan libre, fenêtre en longueur, façade libre), Villa Savoye, Unité d'habitation. Niveau 2nde.",
        "resultat": """## Questions de compréhension — L'architecture moderne

---

**Question 1.** Quel architecte a formulé les « 5 points de l'architecture moderne » ?
- A) Frank Lloyd Wright
- B) Ludwig Mies van der Rohe
- C) Le Corbusier ✓
- D) Oscar Niemeyer

**Question 2.** Parmi ces éléments, lequel NE fait PAS partie des 5 points de Le Corbusier ?
- A) Les pilotis
- B) Le toit-terrasse
- C) Les arcs en plein cintre ✓
- D) La façade libre

**Question 3.** La Villa Savoye (1931) illustre surtout :
- A) L'architecture baroque et ses ornements
- B) Les principes de l'architecture moderne : fonctionnalité, béton, ouverture sur le paysage ✓
- C) Le retour aux matériaux naturels (bois, pierre)
- D) L'architecture médiévale revisitée

**Question 4.** La phrase « Une maison est une machine à habiter » est de :
- A) Frank Gehry
- B) Gustave Eiffel
- C) Le Corbusier ✓
- D) Antoni Gaudí

**Question 5.** L'architecture est considérée comme un art car elle :
- A) Sert uniquement à abriter les hommes
- B) Ne nécessite aucune compétence technique
- C) Combine fonctions pratiques et recherche esthétique, exprimant une vision du monde ✓
- D) Est uniquement réservée aux bâtiments publics

---

**Correction :** 1-C / 2-C / 3-B / 4-C / 5-C
""",
    },

    # ─── EPS ─────────────────────────────────────────────────────────────────
    {
        "matiere": "EPS", "niveau": "6e",
        "activite_key": "eps_comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "Compréhension d'une règle", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — L'athlétisme : course et saut",
        "texte_source": "Athlétisme en EPS : courses (sprint, endurance), sauts (hauteur, longueur), lancer. Règles de base, posture, technique. Niveau 6e.",
        "resultat": """## Questions de compréhension — L'athlétisme

---

**Question 1.** Dans une course de vitesse (sprint), quelle est la position de départ recommandée ?
- A) Debout, les bras ballants
- B) En position basse, le corps penché en avant pour une meilleure impulsion ✓
- C) Assis sur les talons
- D) Les bras levés au-dessus de la tête

**Question 2.** Qu'est-ce que le « faux départ » en course ?
- A) Partir trop lentement
- B) Partir avant le signal de départ ✓
- C) Courir en dehors de sa couloir
- D) S'arrêter pendant la course

**Question 3.** En saut en longueur, l'athlète doit appeler (prendre son élan) :
- A) Sur n'importe quel pied, sans contrainte
- B) Sur la planche d'appel sans la dépasser ✓
- C) À au moins 1 mètre de la planche
- D) En s'aidant des deux pieds simultanément

**Question 4.** La course de fond se distingue du sprint par :
- A) L'utilisation d'obstacles
- B) Une distance plus longue et une allure régulière et maîtrisée ✓
- C) Le départ en position couchée
- D) L'obligation de sauter des haies

**Question 5.** Pour améliorer ses performances en athlétisme, il est important de :
- A) Ne jamais s'échauffer pour garder de l'énergie
- B) S'entraîner régulièrement et s'échauffer avant chaque séance ✓
- C) Manger juste avant de courir
- D) Courir le plus vite possible à chaque entraînement

---

**Correction :** 1-B / 2-B / 3-B / 4-B / 5-B
""",
    },
    {
        "matiere": "EPS", "niveau": "5e",
        "activite_key": "eps_comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "Compréhension d'une règle", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Les sports collectifs : le handball",
        "texte_source": "Handball en EPS : terrain, règles fondamentales, nombre de joueurs, positions, gardien de but, dribble, passes. Niveau 5e.",
        "resultat": """## Questions de compréhension — Le handball

---

**Question 1.** Combien de joueurs compose une équipe de handball sur le terrain ?
- A) 5
- B) 6
- C) 7 ✓
- D) 11

**Question 2.** Qu'est-ce que la zone de but (l'aire de but) au handball ?
- A) La zone où le gardien peut toucher le ballon avec les pieds
- B) Une zone interdite aux joueurs de champ adverses, réservée au gardien ✓
- C) La ligne de tir à 9 mètres
- D) La zone de remplacement des joueurs

**Question 3.** Combien de pas maximum un joueur peut-il faire avec le ballon sans dribbler ?
- A) 1 pas
- B) 2 pas
- C) 3 pas ✓
- D) Autant qu'il veut

**Question 4.** Quelle faute est sanctionnée par un jet franc au handball ?
- A) Marquer un but
- B) Passer le ballon en arrière
- C) Empiéter sur la zone de but adverse ou commettre une faute sur un adversaire ✓
- D) Effectuer une remise en jeu

**Question 5.** Le gardien de handball a-t-il le droit de sortir de sa zone ?
- A) Non, il doit toujours rester dans sa zone
- B) Oui, mais il devient alors un joueur de champ ordinaire ✓
- C) Oui, mais uniquement pour tirer au but
- D) Uniquement lors des prolongations

---

**Correction :** 1-C / 2-B / 3-C / 4-C / 5-B
""",
    },
    {
        "matiere": "EPS", "niveau": "4e",
        "activite_key": "eps_comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "Compréhension d'une règle", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — La natation : nages et règles",
        "texte_source": "Natation en EPS : quatre nages (crawl, dos crawl, brasse, papillon), règles de compétition, virages, départ. Niveau 4e.",
        "resultat": """## Questions de compréhension — La natation

---

**Question 1.** Combien existe-t-il de nages officielles en natation compétitive ?
- A) 2
- B) 3
- C) 4 ✓
- D) 5

**Question 2.** Quelle nage est généralement la plus rapide ?
- A) La brasse
- B) Le dos crawl
- C) Le papillon
- D) Le crawl (nage libre) ✓

**Question 3.** En brasse, comment effectue-t-on le virage ?
- A) En touchant le mur avec une seule main
- B) En roulant sur le côté
- C) En touchant le mur avec les deux mains simultanément ✓
- D) En effectuant un salto

**Question 4.** En natation, qu'est-ce qu'une « fausse départ » ?
- A) Plonger trop loin de la ligne de départ
- B) Entrer dans l'eau avant le signal de départ ✓
- C) Nager dans le mauvais couloir
- D) Faire un virage incorrect

**Question 5.** En nage papillon, les bras :
- A) Alternent, l'un après l'autre
- B) Bougent simultanément en sortant de l'eau ✓
- C) Restent sous la surface en permanence
- D) Sont placés sur les hanches

---

**Correction :** 1-C / 2-D / 3-C / 4-B / 5-B
""",
    },
    {
        "matiere": "EPS", "niveau": "1ère",
        "activite_key": "eps_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Sécurité", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Activité physique et santé",
        "texte_source": "Bienfaits de l'activité physique sur la santé : système cardiovasculaire, musculaire, osseux, bien-être mental. Recommandations OMS. Niveau 1ère.",
        "resultat": """## Questions de cours — Activité physique et santé

---

**Question 1.** Selon l'OMS, quelle durée d'activité physique modérée les adultes et lycéens doivent-ils pratiquer par semaine ?
- A) 30 minutes par semaine
- B) Au moins 150 minutes (2h30) par semaine ✓
- C) 1 heure par jour tous les jours
- D) 30 minutes par jour uniquement le week-end

**Question 2.** Quel effet régulier de l'activité physique observe-t-on sur le cœur ?
- A) Le cœur bat plus vite au repos
- B) Le cœur diminue en taille
- C) Le cœur devient plus efficace et la fréquence cardiaque au repos diminue ✓
- D) La tension artérielle augmente en permanence

**Question 3.** L'activité physique régulière contribue à la santé mentale en :
- A) Augmentant le taux de cortisol (hormone du stress)
- B) Favorisant la libération d'endorphines, qui améliorent l'humeur ✓
- C) Réduisant les capacités de concentration
- D) Augmentant le risque d'anxiété

**Question 4.** Quel type d'activité physique est particulièrement bénéfique pour la densité osseuse ?
- A) La natation uniquement
- B) Le vélo couché
- C) Les activités avec impact (course, saut, sports collectifs) ✓
- D) Les étirements passifs

**Question 5.** La sédentarité (manque d'activité physique) est associée à un risque accru de :
- A) Maladies cardiovasculaires, diabète de type 2 et obésité ✓
- B) Hypotension et anémie uniquement
- C) Maladies infectieuses
- D) Troubles de la vue uniquement

---

**Correction :** 1-B / 2-C / 3-B / 4-C / 5-A
""",
    },
    {
        "matiere": "EPS", "niveau": "Terminale",
        "activite_key": "eps_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "mélange", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Activités de pleine nature et gestion du risque",
        "texte_source": "Activités physiques de pleine nature (APPN) : randonnée, escalade, VTT, kayak. Gestion du risque, équipement, règles de sécurité, respect de l'environnement. Niveau Terminale.",
        "resultat": """## Questions de cours — Activités de pleine nature

---

**Question 1.** Qu'est-ce qu'une activité physique de pleine nature (APPN) ?
- A) Une activité pratiquée uniquement dans les gymnases
- B) Une activité sportive pratiquée en milieu naturel, avec des contraintes et aléas liés à l'environnement ✓
- C) Un sport sans aucun risque
- D) Une activité réservée aux professionnels

**Question 2.** En escalade, le « relais » désigne :
- A) Le passage d'une corde à une autre
- B) Le point d'ancrage sécurisé où l'on s'arrête pour assurer son partenaire ✓
- C) La chute contrôlée d'un grimpeur
- D) L'équipement de protection individuelle

**Question 3.** La gestion du risque en APPN implique de :
- A) Prendre le maximum de risques pour progresser
- B) Éviter toute activité physique en plein air
- C) Identifier, évaluer et réduire les dangers par une préparation adaptée et un équipement approprié ✓
- D) Pratiquer uniquement par beau temps

**Question 4.** Lors d'une randonnée en montagne, quelle règle de sécurité est essentielle ?
- A) Partir sans carte ni boussole pour développer son sens de l'orientation
- B) Prévenir quelqu'un de son itinéraire et de l'heure de retour prévue ✓
- C) Marcher seul pour aller plus vite
- D) Ne pas emporter d'eau pour voyager léger

**Question 5.** Le respect de l'environnement lors des APPN signifie :
- A) Laisser ses déchets dans la nature pour nourrir les animaux
- B) Ne jamais pratiquer d'activité physique en nature
- C) Ramasser ses déchets, rester sur les sentiers balisés et respecter la faune et la flore ✓
- D) Couper des branches pour marquer son passage

---

**Correction :** 1-B / 2-B / 3-C / 4-B / 5-C
""",
    },
    {
        "matiere": "EPS", "niveau": "3e",
        "activite_key": "eps_comprehension", "activite_label": "Questions de compréhension",
        "sous_type": "Compréhension d'une règle", "nb": 5, "avec_correction": True,
        "objet": "[Exemple] QCM — Règles du badminton",
        "texte_source": "Règles du badminton : terrain, filet, service, fautes, points, sets. Niveau 3e EPS.",
        "resultat": """## Questions de compréhension — Règles du badminton

---

**Question 1.** Combien de points faut-il pour gagner un set au badminton ?
- A) 15 points
- B) 21 points ✓
- C) 25 points
- D) 11 points

**Question 2.** Lors du service en badminton, où doit se trouver le volant au moment du contact ?
- A) Au-dessus de la ceinture du serveur
- B) En dessous de la ceinture du serveur ✓
- C) À hauteur des yeux
- D) N'importe où, il n'y a pas de règle

**Question 3.** Une faute est commise lorsque :
- A) Le volant touche le filet et passe de l'autre côté
- B) Le joueur frappe le volant deux fois de suite ✓
- C) Le volant tombe sur la ligne de fond adverse
- D) Le serveur change de carré de service

**Question 4.** En simple, quelle zone constitue le terrain de service correct ?
- A) Tout le terrain adverse
- B) Le carré de service diagonal au serveur, en deçà de la ligne de fond courte ✓
- C) Uniquement la moitié gauche du terrain adverse
- D) La zone entre le filet et la ligne de fond

**Question 5.** Que se passe-t-il si le score est à 20-20 ?
- A) Le set continue jusqu'à 25 points
- B) Un joueur doit marquer 2 points d'écart, jusqu'à un maximum de 30-29 ✓
- C) On joue un point décisif au service
- D) Le set est déclaré nul et on recommence

---

**Correction :** 1-B / 2-B / 3-B / 4-B / 5-B
""",
    },
    {
        "matiere": "EPS", "niveau": "2nde",
        "activite_key": "eps_questions_cours", "activite_label": "Questions de cours",
        "sous_type": "Sécurité", "nb": 4, "avec_correction": True,
        "objet": "[Exemple] QCM — Sécurité et échauffement en EPS",
        "texte_source": "Principes de sécurité en EPS : échauffement, étirements, prévention des blessures, règles de sécurité en salle et en extérieur. Niveau 2nde.",
        "resultat": """## Questions de cours — Sécurité et échauffement en EPS

---

**Question 1.** À quoi sert l'échauffement avant une séance d'EPS ?
- A) À montrer ses capacités physiques au professeur
- B) À préparer progressivement le corps à l'effort et réduire le risque de blessures ✓
- C) À se reposer avant l'effort principal
- D) À améliorer directement ses performances sportives

**Question 2.** Dans quel ordre doit-on réaliser un échauffement complet ?
- A) Étirements → cardio → échauffement articulaire
- B) Cardio léger → échauffement articulaire → exercices spécifiques ✓
- C) Exercices spécifiques → cardio → étirements
- D) Étirements → exercices spécifiques → cardio

**Question 3.** Quand faut-il réaliser des étirements statiques (maintenus 20-30 sec) ?
- A) Avant l'effort, pour préparer les muscles
- B) Pendant l'effort, pour éviter les crampes
- C) Après l'effort, en fin de séance ✓
- D) Les étirements statiques sont déconseillés en EPS

**Question 4.** En cas de chute ou de douleur pendant une séance d'EPS, que doit faire l'élève ?
- A) Continuer l'activité pour ne pas gêner le cours
- B) S'arrêter immédiatement et en informer le professeur ✓
- C) Appliquer lui-même de la glace sans prévenir
- D) Rentrer chez lui directement

---

**Correction :** 1-B / 2-B / 3-C / 4-B
""",
    },
]


def run_seed(db):
    """Insère les exemples si le compte démo n'existe pas encore."""
    from backend.models_db import User, ActiviteSauvegardee

    user = db.query(User).filter(User.email == DEMO_EMAIL).first()
    if not user:
        fake_hash = bcrypt.hashpw(b"not-a-real-password-" + __import__('os').urandom(16), bcrypt.gensalt(12)).decode()
        user = User(
            email=DEMO_EMAIL,
            password_hash=fake_hash,
            is_verified=True,
            prenom=DEMO_PRENOM,
            nom="",
            is_active=True,
        )
        db.add(user)
        db.commit()

    inserted = 0
    for ex in EXEMPLES:
        already = db.query(ActiviteSauvegardee).filter(
            ActiviteSauvegardee.user_email == DEMO_EMAIL,
            ActiviteSauvegardee.objet == ex["objet"],
        ).first()
        if already:
            continue
        db.add(ActiviteSauvegardee(
            user_email=DEMO_EMAIL,
            activite_key=ex["activite_key"],
            activite_label=ex["activite_label"],
            niveau=ex["niveau"],
            sous_type=ex.get("sous_type"),
            nb=ex.get("nb"),
            avec_correction=ex.get("avec_correction", True),
            matiere=ex["matiere"],
            objet=ex["objet"],
            texte_source=ex["texte_source"],
            resultat=ex["resultat"],
            partagee=True,
        ))
        inserted += 1

    if inserted:
        db.commit()

    return inserted


if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        n = run_seed(db)
        print(f"✅ Seed terminé — {n} exemple(s) insérés sous {DEMO_EMAIL}")
    finally:
        db.close()
