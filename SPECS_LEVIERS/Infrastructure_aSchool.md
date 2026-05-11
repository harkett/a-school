# Infrastructure technique d'aSchool

## Comment utiliser ce document
Ce document décrit le socle technique commun qui alimente les leviers retenus. Ce n'est pas une fonctionnalité visible par le prof — c'est la couche de données pédagogiques structurées qui rend chaque levier plus précis et plus puissant. Le développeur doit lire ce document avant d'implémenter les leviers retenus : plusieurs d'entre eux en dépendent directement.

---

## Origine
Ces éléments d'infrastructure sont extraits du levier "Index pédagogique universel des notions scolaires". Ce levier n'est pas une fonctionnalité utilisateur — c'est une base de connaissances pédagogiques structurées couvrant toutes les notions scolaires du CP à la Terminale, leurs relations, dépendances, ambiguïtés et variations disciplinaires.

Sans cette infrastructure, les leviers retenus fonctionnent sur des règles linguistiques générales.
Avec elle, ils fonctionnent sur de la connaissance pédagogique structurée et validée.

---

## Élément 1 — Graphe universel des notions + Index des ambiguïtés conceptuelles

### Ce que c'est
Un graphe structuré reliant toutes les notions du programme scolaire entre elles : hiérarchie, prérequis, dépendances, notions connexes, notions confondues. Complété par un index de toutes les confusions possibles entre notions proches, documentées et classées par matière et par niveau.

### Ce que ça contient concrètement
- Toutes les notions du programme (CP → Terminale), structurées en graphe
- Pour chaque notion : ses prérequis, ses dépendances, ses notions connexes
- Pour chaque paire de notions proches : les types de confusion possibles et leur fréquence
- Les mots polysémiques à risque par matière ("figure", "valeur", "produit", "modèle", "tirer", "simplifier"…)
- Les ambiguïtés de transfert : notions qui changent de sens selon le contexte

### Où ça alimente
**→ Levier 2 — Détection automatique des zones d'ambiguïté cognitive**
Sans cet index, aSchool détecte des ambiguïtés linguistiques (formulations floues). Avec lui, il détecte des ambiguïtés proprement pédagogiques — confusions conceptuelles documentées, connues, spécifiques à une notion et à un niveau. La détection passe du niveau "texte" au niveau "connaissance pédagogique".

**→ Levier 1 — Générateur d'orchestrations pédagogiques**
Le graphe permet de construire des transitions conceptuelles cohérentes entre les phases d'une séance : aSchool sait quelles notions doivent précéder quelle autre, et peut alerter si une phase suppose une notion non encore vue.

**→ Levier 4 — Moteur de cohérence curriculaire inter-disciplines**
L'index des ambiguïtés disciplinaires (une même notion qui change de sens selon la matière) est exactement ce dont le moteur de cohérence a besoin pour détecter les contradictions inter-matières.

### Approfondissement — Moteur de granularisation intelligente des notions

Le graphe universel relie les notions entre elles. La granularisation définit la structure interne de chaque nœud du graphe. C'est le niveau de détail qui permet à aSchool de comprendre une notion comme un expert didacticien, pas comme un mot dans un texte.

**Structure granulaire de chaque notion :**
- **Niveau 1 — Micro-notions fondamentales** : les composants atomiques de la notion
- **Niveau 2 — Micro-compétences** : ce que l'élève doit savoir faire avec chaque micro-notion
- **Niveau 3 — Gestes cognitifs** : les opérations mentales requises (comparer, isoler, vérifier…)
- **Niveau 4 — Ambiguïtés** : mots, schémas, contextes qui induisent en erreur à ce niveau
- **Niveau 5 — Erreurs typiques** : erreurs récurrentes associées à chaque micro-notion
- **Niveau 6 — Activités compatibles** : quelles activités conviennent à quel niveau de granularité

**Exemple concret — Notion : Proportionnalité**

| Niveau | Contenu |
|---|---|
| Micro-notions | rapport, coefficient, tableau de proportionnalité, passage multiplicatif |
| Micro-compétences | identifier une situation proportionnelle, calculer un coefficient, compléter un tableau, détecter une non-proportionnalité |
| Gestes cognitifs | reconnaître une relation multiplicative, comparer deux rapports, isoler une variable, vérifier une cohérence numérique |
| Ambiguïtés | "taux" vs "pourcentage", "coefficient" vs "rapport", "proportion" (sens courant) |
| Erreurs typiques | additionner au lieu de multiplier, confondre coefficient et multiplicateur, inverser les rapports |
| Activités compatibles | manipulation, tableaux, problèmes concrets, graphiques |

**Ce que ça apporte aux leviers retenus :**
- **Génération d'exercices (cœur d'aSchool)** : l'outil génère un exercice au bon niveau de granularité, pas juste "facile/moyen/difficile" — il sait exactement quelle micro-compétence cibler.
- **Levier 1 (Orchestrations)** : chaque phase de la séance peut être calibrée sur un niveau de granularité précis.
- **Levier 3 (Optimiseur)** : vérifie que la séquence couvre tous les niveaux dans le bon ordre.
- **Levier 2 (Ambiguïtés) et Levier 5 (Analyseur de consignes)** : les ambiguïtés et erreurs sont connues au niveau de chaque micro-notion, pas seulement au niveau de la notion globale.

---

## Élément 2 — Index des erreurs typiques par notion

### Ce que c'est
Pour chaque notion du programme, un index des erreurs récurrentes commises par les élèves : types d'erreurs, fréquence, niveau scolaire où elles apparaissent, cause cognitive sous-jacente.

### Ce que ça contient concrètement
- Erreurs typiques par notion (ex : fractions → confondre numérateur/dénominateur, comparer 1/8 et 1/6)
- Cause cognitive de chaque erreur (confusion de sens, étape implicite, transfert raté…)
- Niveau scolaire où chaque erreur est la plus fréquente
- Patterns d'erreurs récurrentes entre notions liées

### Où ça alimente
**→ Génération d'exercices (cœur d'aSchool)**
L'outil sait déjà générer un exercice à partir d'un texte. Avec cet index, il sait aussi quels pièges éviter dans la formulation, ou au contraire, lesquels intégrer intentionnellement pour tester la compréhension réelle — et pas seulement la mémorisation.

**→ Levier 2 — Détection automatique des zones d'ambiguïté cognitive**
L'index des erreurs typiques enrichit la détection : aSchool ne se contente pas de signaler une formulation ambiguë, il peut préciser "cette formulation génère typiquement l'erreur X chez les élèves de 5e".

---

## Élément 3 — Index des activités compatibles par notion

### Ce que c'est
Pour chaque notion, un index des types d'activités pédagogiques les plus adaptées : manipulation, schéma, exercice formel, problème concret, jeu de rôle, débat, carte mentale, etc. Classées par niveau cognitif (Bloom), par efficacité documentée, et par modalité.

### Ce que ça contient concrètement
- Pour chaque notion : liste ordonnée des activités les plus efficaces
- Classification par niveau cognitif (compréhension → application → transfert → abstraction)
- Modalités adaptées (texte, schéma, manipulation, oral, numérique)
- Activités à éviter ou contre-indiquées pour certaines notions

### Où ça alimente
**→ Levier 1 — Générateur d'orchestrations pédagogiques**
Quand le prof demande une séance sur la proportionnalité, aSchool ne choisit pas les activités au hasard : il sélectionne les types d'activités documentés comme les plus efficaces pour cette notion précise. Chaque phase de la séance est construite sur une base de connaissance, pas sur une règle générique.

**→ Génération d'exercices (cœur d'aSchool)**
L'outil peut proposer proactivement des types d'activités alternatives mieux adaptées à la notion du texte collé par le prof.

---

## Élément 4 — Variantes disciplinaires

### Ce que c'est
Un index documentant comment une même notion, un même mot ou un même concept change de sens, de définition ou d'usage selon la discipline. Couvre toutes les matières du programme.

### Ce que ça contient concrètement
- Mots et notions multi-disciplinaires avec leur sens par matière
- Exemples : "modèle" (Maths / SVT / Physique / Technologie), "fonction" (Maths / Français / Biologie), "valeur" (Maths / Philosophie / Économie), "fraction" (Maths / Physique / Technologie)
- Risques de confusion documentés entre disciplines
- Opportunités de transfert positif entre disciplines

### Où ça alimente
**→ Levier 4 — Moteur de cohérence curriculaire inter-disciplines**
C'est le carburant direct du moteur de cohérence. Savoir que "modèle" signifie des choses différentes en SVT et en Physique est exactement ce dont le moteur a besoin pour détecter les contradictions et signaler les risques de confusion inter-matières au prof.

**→ Levier 2 — Détection automatique des zones d'ambiguïté cognitive**
Les variantes disciplinaires alimentent la détection des ambiguïtés de transfert : quand un prof de Physique utilise un mot qui a un sens différent en Maths (matière vue juste avant), aSchool peut le signaler.

---

## Résumé des dépendances

| Infrastructure | L1 Orchestrations | L2 Ambiguïtés | L3 Optimiseur | L4 Cohérence | L5 Consignes | L6 Équité | Génération actuelle |
|---|---|---|---|---|---|---|---|
| Graphe universel + ambiguïtés | ✓ transitions | ✓ cœur | ✓ | ✓ contradictions | ✓ granularisation | ✓ | — |
| Index erreurs typiques | — | ✓ enrichissement | ✓ | — | ✓ cœur | ✓ | ✓ qualité exercices |
| Index activités compatibles | ✓ cœur | — | ✓ | — | — | — | ✓ suggestions |
| Variantes disciplinaires | — | ✓ transfert | ✓ | ✓ cœur | — | — | — |

---
