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

    # ─── EPS ─────────────────────────────────────────────────────────────────
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
