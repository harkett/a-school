# TRACKER — Notions Scolaires

> **Doc de travail vivant.** On transforme une vision (`NOTION_SCOLAIRE.md`,
> levier 13 — « Moteur de granularisation intelligente des notions ») en une spec
> costaud, pas à pas.
>
> **Comment on s'en sert :** on *réfléchit* dans « Questions ouvertes ». Dès qu'un
> point est tranché, il **monte** dans « Acquis » ou « Principes directeurs ». Le
> doc est à tout instant la photo de l'état de la pensée — pas un fil de discussion
> à relire en entier. Le « Journal » en bas garde la trace datée, en une ligne.

---

## Panorama (état au 24/06)

Les notions = le **sol** d'aSchool (cf. §4). 14 briques évaluées — détail et notes
au §5, qui fait foi.

- **Socle — à construire d'abord :**
  - **P1** (racine + plus fort apport) : 1 Découpage · 2 Niveaux · 6 Erreurs typiques · 7 Ambiguïtés
  - **P2** : 3 Cognitive · 4 Didactique · 8 Activités compatibles
  - **P3** : 5 Disciplinaire
- **Niveau supérieur (11-14) :** tous **P3** — se posent par-dessus le socle, plus incertains.

> La **brique 1 (Découpage)** est la racine : tout le reste en dépend.

## Sommaire

[1. Source](#1-source) · [2. Vision](#2-vision-synthèse) · [3. Acquis](#3-acquis--décisions-tranchés--on-ne-rediscute-plus) · [4. Principes](#4-principes-directeurs-les-règles-quon-se-donne-pour-ce-chantier) · [5. Évaluation des briques](#5-évaluation-des-briques) · [6. Questions ouvertes](#6-questions-ouvertes--à-trancher-file-de-réflexion) · [7. Chantiers](#7-chantiers--découpage-construction) · [8. Lexique](#8-lexique) · [9. Journal](#9-journal)

---

## 1. Source

- Vision d'origine : `MesMD/a faire/NOTION_SCOLAIRE.md`
- Levier concerné : **13 — Moteur de granularisation intelligente des notions**
  (les leviers 14 « Détecteur de biais d'évaluation » et 15 « Assistant de
  calibration pédagogique » cohabitent dans ce fichier mais ne sont pas le sujet ici).

---

## 2. Vision (synthèse)

**L'idée centrale, en une phrase :** faire passer aSchool de « il connaît le **nom**
des notions » (une notion = une étiquette, un mot dans un texte) à « il comprend la
notion **comme un didacticien** » (une notion = une structure détaillée et
exploitable).

**Le mécanisme :** pour chaque notion scolaire (ex. proportionnalité, fractions), le
moteur construit une **carte détaillée** — il casse la notion en petits morceaux et,
pour chacun, il sait :

- **De quoi c'est fait** — micro-compétences (fraction → numérateur, dénominateur,
  équivalence, simplification…).
- **Dans quel ordre on l'apprend** — prérequis, ordre d'introduction, progressivité.
- **Ce qui coince habituellement** — erreurs typiques, ambiguïtés (mots, schémas,
  contextes qui induisent en erreur).
- **L'effort mental demandé** — charge cognitive par micro-notion.
- **Quelles activités aSchool savent travailler ce morceau** — lien vers le
  catalogue d'activités, par niveau de granularité.

**Sa place dans aSchool :** ce n'est pas un outil de plus, mais une **couche de
connaissance sous-jacente** — un socle qui nourrit les outils déjà existants
(Détecteur d'ambiguïtés, Différenciation/Remédiation, catalogue d'activités).

---

## 3. Acquis / décisions (tranchés — on ne rediscute plus)

| Date | Décision |
|---|---|
| 24/06 | **C'est très utile, pas du superflu.** Les outils IA concurrents sont des « enrobages de prompt » qui traitent la notion comme une étiquette → facile à copier, non différenciant. Une connaissance didactique structurée, non. → c'est un **moat** (actif qui se construit, pas un prompt recopiable). |
| 24/06 | **« Unique » se joue au niveau du PRODUIT, pas de la fonctionnalité.** aSchool ne devient pas unique parce qu'il « a un moteur de granularisation » ; il le devient parce que **toute la plateforme repose sur une compréhension didactique des notions** — c'est sa nature, pas une option. L'unicité = l'**ADN** du produit. |
| 24/06 | **Périmètre respecté :** reste « aSchool est POUR l'enseignant ». Le prof génère ; le moteur outille **sa** compréhension. Rien qui s'adresse directement à l'élève. |

---

## 4. Principes directeurs (les règles qu'on se donne pour ce chantier)

- **Les notions sont le SOL, pas une brique.** Tout aSchool se tient dessus. C'est ce
  sol qui rend l'ensemble unique — pas une feature isolée.
- **Rien qui ne soit raccordé.** La valeur de cette couche n'existe **que** si elle
  est branchée à des outils réels (Ambiguïtés, Différenciation/Remédiation,
  catalogue d'activités). Base de connaissance isolée que personne ne consulte =
  vaut zéro. Branchée = rend *tous* les autres outils meilleurs.
- **Connaissance structurée, pas génération à la volée.** Ce qui fait la différence,
  c'est l'actif construit et organisé — pas un prompt qui improvise à chaque appel.

---

## 5. Évaluation des briques

> **Méthode validée :** un **tableau compact** (les notes, pour comparer d'un coup
> d'œil) + une **fiche courte par brique** (le texte : apport, raccordement,
> dépendance, risque). On remplit **une brique à la fois**, tranquillement.
>
> **Légende** — Importance / Faisabilité : ★ sur 5. Effort : ★ sur 5 (5 = lourd).
> Durée : fourchette grossière (affinée au moment de construire). Priorité : P1/P2/P3.

### Tableau compact

| Brique | Importance | Faisabilité | Effort | Durée | Priorité |
|---|---|---|---|---|---|
| **— SOCLE —** | | | | | |
| 1. Découpage en micro-notions | ★★★★★ | ★★★★☆ | ★★★★☆ | ~2-4 sessions | **P1** |
| 2. Niveaux de granularité | ★★★★☆ | ★★★★☆ | ★★★☆☆ | ~1-2 sessions | **P1** |
| 3. Granularité cognitive | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | ~1-2 sessions | **P2** |
| 4. Granularité didactique | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | ~1-2 sessions | **P2** |
| 5. Granularité disciplinaire | ★★★☆☆ | ★★★☆☆ | ★★★★☆ | ~2-3 sessions | **P3** |
| 6. Granularité des erreurs typiques | ★★★★★ | ★★★★☆ | ★★★☆☆ | ~1-2 sessions | **P1** |
| 7. Granularité des ambiguïtés | ★★★★☆ | ★★★★☆ | ★★★☆☆ | ~1-2 sessions | **P1** |
| 8. Granularité des activités compatibles | ★★★★☆ | ★★★☆☆ | ★★★★☆ | ~2-3 sessions | **P2** |
| **— NIVEAU SUPÉRIEUR —** | | | | | |
| 11. Granularisation interdisciplinaire | ★★★☆☆ | ★★☆☆☆ | ★★★★☆ | ~2-3 sessions | **P3** |
| 12. Granularisation spiralaire | ★★★★☆ | ★★★☆☆ | ★★★★☆ | ~2-3 sessions | **P3** |
| 13. Granularisation émotionnelle légère | ★★☆☆☆ | ★★☆☆☆ | ★★★☆☆ | ~1-2 sessions | **P3** |
| 14. Granularisation cognitive profonde | ★★★☆☆ | ★★☆☆☆ | ★★★★★ | ~3+ sessions | **P3** |

### Fiches (le détail texte, une par brique)

> On crée/complète la fiche d'une brique **au moment où on l'évalue**. Gabarit :
>
> **Brique N — Nom**
> - **Apport :** ce que ça débloque / quels outils ça nourrit.
> - **Se raccorde à :** quel(s) outil(s) réel(s).
> - **Dépend de :** rien / telle autre brique.
> - **Risque :** ce qui peut coincer.

**Brique 1 — Découpage en micro-notions**
*Casser une notion en micro-compétences élémentaires (fraction → numérateur,
dénominateur, équivalence, simplification…).*
- **Apport :** débloque **toutes** les autres briques ; donne un **grain fin** à la
  Différenciation/Remédiation (savoir *quel* morceau re-cibler) et au Détecteur
  d'ambiguïtés (savoir *quelle* micro-notion est floue).
- **Se raccorde à :** Différenciation/Remédiation · Détecteur d'ambiguïtés ·
  catalogue d'activités.
- **Dépend de :** rien — c'est la racine du moteur.
- **Risque :** la **qualité du découpage**. Un LLM seul est variable → il faudra
  sans doute une **validation** (prof ou référentiel) pour éviter des découpages
  incohérents d'une notion à l'autre.

**Brique 2 — Niveaux de granularité**
*Organiser les morceaux en niveaux de profondeur : notion → sous-notion →
micro-compétence → geste cognitif.*
- **Apport :** permet de **viser le bon niveau** (différencier au niveau
  « sous-notion » vs « geste cognitif »). C'est le squelette sur lequel les autres
  granularités viennent se ranger.
- **Se raccorde à :** Différenciation/Remédiation (niveau de re-ciblage) ·
  catalogue d'activités (associer une activité au bon niveau de profondeur).
- **Dépend de :** **brique 1** — il faut les morceaux avant de les hiérarchiser.
- **Risque :** **sur-ingénierie** de la hiérarchie (trop de niveaux = usine à gaz).
  Se fixer **3-4 niveaux maximum**.

**Brique 3 — Granularité cognitive**
*L'effort mental (charge cognitive) requis par chaque micro-notion.*
- **Apport :** nourrit le **dosage de la difficulté** et la différenciation (éviter
  de surcharger l'élève, choisir un morceau à sa portée).
- **Se raccorde à :** Différenciation/Remédiation · (futur) Assistant de calibration.
- **Dépend de :** **brique 1** (les morceaux) — idéalement **brique 2** (situer la
  charge par niveau).
- **Risque :** la **subjectivité** — pas de mesure objective. Garder une **échelle
  simple** (faible / moyen / élevé), pas un score faussement précis.

**Brique 4 — Granularité didactique**
*L'ordre optimal d'introduction des micro-notions (la progressivité).*
- **Apport :** donne l'**ordre d'enseignement** → alimente directement le Générateur
  de séquences et l'Optimiseur de séquences. C'est la progressivité.
- **Se raccorde à :** Générateur de séquences · Optimiseur de séquences.
- **Dépend de :** **brique 1** (les morceaux) — s'appuie sur les **prérequis** entre
  micro-notions.
- **Risque :** « optimal » **n'est pas unique** (plusieurs progressions valides selon
  le prof). Ne pas imposer un ordre rigide : **proposer**, laisser le prof ajuster.

**Brique 5 — Granularité disciplinaire**
*La variation du découpage selon la matière (« modèle » en SVT ≠ en Maths).*
- **Apport :** évite les **contresens inter-matières** et fiabilise le découpage
  propre à chaque discipline.
- **Se raccorde à :** catalogue d'activités (par matière) · Générateur d'activités.
- **Dépend de :** **brique 1** (le découpage de base).
- **Risque :** **explosion combinatoire** (12 matières × notions). À ne traiter que
  pour les notions **réellement polysémiques** entre disciplines, pas systématiquement.

**Brique 6 — Granularité des erreurs typiques**
*Les erreurs fréquentes associées à chaque micro-notion.*
- **Apport :** **cœur de la Remédiation** — anticiper les erreurs fréquentes permet
  des remédiations ciblées, des exercices anti-erreur, et de l'anticipation dans les
  activités. Très concret.
- **Se raccorde à :** Remédiation · Détecteur d'ambiguïtés · Générateur d'activités.
- **Dépend de :** **brique 1**.
- **Risque :** varie selon niveau/contexte → **ancrer sur des sources didactiques**,
  pas un LLM seul.

**Brique 7 — Granularité des ambiguïtés**
*Les mots, schémas, contextes qui induisent en erreur, par micro-notion.*
- **Apport :** rend le **Détecteur d'ambiguïtés (déjà en prod)** bien plus précis —
  il sait *quelle* micro-notion porte le piège.
- **Se raccorde à :** Détecteur d'ambiguïtés (direct) · Générateur d'activités.
- **Dépend de :** **brique 1** — proche de la brique 6.
- **Risque :** **chevauchement avec les erreurs typiques** (brique 6) : bien
  distinguer ambiguïté (formulation/piège) vs erreur (résultat faux).

**Brique 8 — Granularité des activités compatibles**
*Quelles activités conviennent à quel niveau de granularité.*
- **Apport :** relie chaque morceau aux **activités du catalogue** qui le travaillent
  → le Générateur peut proposer la bonne activité pour le bon grain. C'est le **pont**
  entre la connaissance et le catalogue (140 entrées).
- **Se raccorde à :** catalogue d'activités · Générateur d'activités.
- **Dépend de :** **briques 1 et 2** (morceaux + niveaux).
- **Risque :** **mapping lourd** à maintenir quand le catalogue évolue → automatiser
  le lien plutôt qu'une table figée.

**Brique 11 — Granularisation interdisciplinaire**
*Relie/découpe une même notion entre matières (ponts inter-disciplines).*
- **Apport :** ponts entre disciplines → **cohérence curriculaire inter-matières**.
- **Se raccorde à :** (futur) Cohérence curriculaire inter-disciplines.
- **Dépend de :** **brique 5** + socle.
- **Risque :** **recouvre la brique 5** — distinguer : 5 = variation *intra*-matière du
  découpage ; 11 = *ponts entre* matières. Très ambitieux.

**Brique 12 — Granularisation spiralaire**
*Organise les retours/réactivations optimaux sur les micro-notions.*
- **Apport :** planifie les **réactivations** (revoir un morceau au bon moment) →
  mémorisation durable, séquences sur l'année.
- **Se raccorde à :** Générateur de séquences · Optimiseur de séquences.
- **Dépend de :** **briques 1, 2, 4** (morceaux, niveaux, ordre).
- **Risque :** nécessite une **vision temps long** (progression annuelle) pas encore
  modélisée.

**Brique 13 — Granularisation émotionnelle légère**
*Évite de placer trop tôt des micro-notions anxiogènes/décourageantes.*
- **Apport :** meilleure **motivation** — ne pas démarrer par un morceau démoralisant.
- **Se raccorde à :** Différenciation · (futur) calibration émotionnelle.
- **Dépend de :** socle.
- **Risque :** très **subjectif**, frôle le gadget → garder « léger » (le mot du
  fichier source), faible priorité.

**Brique 14 — Granularisation cognitive profonde**
*Relie chaque micro-notion aux mécanismes mentaux requis (mémoire de travail,
inhibition…).*
- **Apport :** calibration **cognitive fine** — relier les morceaux aux mécanismes
  mobilisés.
- **Se raccorde à :** (futur) Assistant de calibration cognitive.
- **Dépend de :** tout le socle — **approfondit la brique 3**.
- **Risque :** **frontière recherche**, risque de sur-théorisation sans gain concret
  pour le prof. YAGNI tant que le socle ne tourne pas.

---

## 6. À trancher au moment de construire chaque brique (pas maintenant)

Les détails d'une brique — comment elle marche, qui valide, où c'est stocké — se
décident quand on l'attaque, pas au stade de l'inventaire.

---

## 7. Chantiers / découpage (construction)

> Vide pour l'instant — se remplira quand on passera de la réflexion à la
> construction (modèle de données, ingestion, raccordement aux outils…).

---

## 8. Lexique

> À enrichir. Pour qu'on parle le même langage.

- **Notion** — un objet de savoir scolaire (ex. la proportionnalité).
- **Micro-notion / micro-compétence** — un morceau élémentaire d'une notion
  (ex. numérateur, dénominateur, équivalence pour « fraction »).
- **Geste cognitif** — l'opération mentale élémentaire mobilisée.
- **Granularité** — le niveau de découpage : notion → sous-notion →
  micro-compétence → geste cognitif.
- **Charge cognitive** — l'effort mental requis par un morceau.
- *(à compléter)*

---

## 9. Journal

- **24/06** — Création du tracker. Compréhension posée (Vision). Trois acquis :
  utilité/moat, unicité au niveau produit, périmètre prof respecté. Trois principes
  directeurs posés. Passage du format question/réponse à un tracker de travail en
  sections fixes (validé par Harketti).
- **24/06** — Section « Évaluation des briques » créée : méthode validée (tableau
  compact des 14 briques en 2 blocs + fiche courte par brique). Prêt à évaluer la
  brique 1.
- **24/06** — **Évaluation complète des 14 briques** (notes + fiches). Socle :
  1-2-6-7 en **P1**, 3-4-8 en **P2**, 5 en **P3**. Niveau supérieur (9-14) tous
  **P3**. 5 questions ouvertes consignées (§6). En attente de l'analyse de Harketti.
- **24/06** — **Idées « prédictive » et « adaptative » retirées** (ex-briques 9 et
  10). Motif : elles supposent de **suivre/deviner chaque élève** — interdit chez
  aSchool (règle absolue « outil POUR le prof, pas l'élève » ; RGPD mineurs). Hors
  périmètre, donc sorties du tracker. Restent 12 briques. Les 2 questions ouvertes
  qui en découlaient sont supprimées. (Les idées d'origine subsistent dans le fichier
  source `NOTION_SCOLAIRE.md`.)
- **24/06** — §6 simplifié : les « questions ouvertes » étaient du détail de
  construction → remplacées par « à trancher au moment de construire chaque brique ».
  Le tracker reste à hauteur d'inventaire.
