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

## ⚙️ Mode d'emploi & procédure de reprise

> **Ce que c'est :** la **spécification complète des 12 briques** du moteur de
> granularisation (8 cœur + 4 futures), tranchée une par une le 25/06. Pas un doc à lire
> une fois — c'est la **référence qu'on rouvre à chaque brique qu'on bâtit**.
>
> **Comment s'en servir (à la construction) :** avant de coder une brique, relire sa
> fiche au §5 — elle donne, sans re-débattre : ce qu'on **extrait** du référentiel vs ce
> qu'on **génère** (+ validation prof), les **dépendances** (donc l'ordre — la **brique 1**
> est la racine), les **frontières** (ne pas confondre deux briques) et le **garde-fou
> RGPD** (rester sur la notion générique, **jamais** sur un élève).
>
> **Procédure de reprise (prochaine étape — PAS encore faite) :** ce tracker est un
> **chantier éphémère**. À la reprise, on le **dispatche brique par brique** vers le
> pilotage permanent :
> - **TRACKER.md** → les lignes de pilotage (construire le moteur ; prérequis
>   « **étoffer le catalogue BTS CIEL** ») ;
> - **TABLEAU-DE-BORD.md** → l'entrée dans l'inventaire des travaux (avec lien) ;
> - **BOUSSOLE / Dxx** → le **détail** (les 12 fiches).
>
> Une fois tout dispatché, **ce document disparaît** : son contenu vit dans les trois
> ci-dessus, son historique reste dans git → **on le commite avant de le supprimer**.

---

## Panorama (état au 24/06)

Les notions sont une couche de connaissance qui nourrit les outils d'aSchool.
12 briques évaluées — détail et notes au §5, qui fait foi.

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
- **Aucune donnée personnelle d'élève (ligne rouge).** aSchool ne doit **jamais**
  permettre de saisir ni de stocker une information sur un **élève précis** (nom +
  difficulté, résultats, diagnostic…), **même saisie par le prof** — données
  personnelles sur un mineur (RGPD) et contraire à la nature du produit. On travaille
  uniquement sur la **notion** (savoir générique) et des **catégories génériques**
  (DYS, FLE, niveau) — **jamais sur un individu**.
  → **À publier dans les DEUX Aides — Aide prof ET Aide admin** — pour l'annoncer
  clairement aux utilisateurs. *(tâche à part, hors de cette session.)*

---

## 5. Évaluation des briques

> **Méthode validée :** un **tableau compact** (les notes, pour comparer d'un coup
> d'œil) + une **fiche courte par brique** (le texte : apport, raccordement,
> dépendance, risque). On remplit **une brique à la fois**, tranquillement.
>
> **Légende** — Importance / Faisabilité : ★ sur 5. Effort : ★ sur 5 (5 = lourd).
> Durée : fourchette grossière (affinée au moment de construire).

### Tableau compact

| Brique | Importance | Faisabilité | Effort | Durée |
|---|---|---|---|---|
| **— BRIQUE EXISTANTE —** | | | | |
| 1. Découpage en micro-notions | ★★★★★ | ★★★★☆ | ★★★★☆ | ~2-4 sessions |
| 2. Niveaux de granularité | ★★★★☆ | ★★★★☆ | ★★★☆☆ | ~1-2 sessions |
| 3. Granularité cognitive | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | ~1-2 sessions |
| 4. Granularité didactique | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | ~1-2 sessions |
| 5. Granularité disciplinaire | ★★★☆☆ | ★★★☆☆ | ★★★★☆ | ~2-3 sessions |
| 6. Granularité des erreurs typiques | ★★★★★ | ★★★★☆ | ★★★☆☆ | ~1-2 sessions |
| 7. Granularité des ambiguïtés | ★★★★☆ | ★★★★☆ | ★★★☆☆ | ~1-2 sessions |
| 8. Granularité des activités compatibles | ★★★★☆ | ★★★☆☆ | ★★★★☆ | ~2-3 sessions |
| **— BRIQUE FUTURE —** | | | | |
| 11. Granularisation interdisciplinaire | ★★★☆☆ | ★★☆☆☆ | ★★★★☆ | ~2-3 sessions |
| 12. Granularisation spiralaire | ★★★★☆ | ★★★☆☆ | ★★★★☆ | ~2-3 sessions |
| 13. Granularisation émotionnelle légère | ★★☆☆☆ | ★★☆☆☆ | ★★★☆☆ | ~1-2 sessions |
| 14. Granularisation cognitive profonde | ★★★☆☆ | ★★☆☆☆ | ★★★★★ | ~3+ sessions |

> **Numérotation :** pas de brique 9 ni 10 — ce sont les ex-« prédictive » et
> « adaptative », **retirées** (elles supposaient un suivi d'élève → RGPD, cf. Journal
> 24/06). La numérotation **11-14 est conservée volontairement** (éviter une réécriture
> de masse des références croisées ; le détail prime sur le cosmétique).
>
> **Ligne rouge (élève) — coup d'œil :** **aucune** brique ne touche un élève nommé —
> tout reste sur la **notion générique**. Points de **vigilance** (où la pente vers
> l'élève existe) : **13** (émotionnelle, max) et **12** (spiralaire). Détail dans chaque
> fiche → rubrique « Garde rouge ».

### Fiches (le détail texte, une par brique)

> On crée/complète la fiche d'une brique **au moment où on l'évalue**. Gabarit :
>
> **Brique N — Nom**
> - **Apport :** ce que ça débloque / quels outils ça nourrit.
> - **Se raccorde à :** quel(s) outil(s) réel(s).
> - **Dépend de :** rien / telle autre brique.
> - **Risque :** ce qui peut coincer.

**Brique 1 — Découpage en micro-notions**
*Casser une notion en micro-compétences élémentaires.*

**En clair (exemple pour comprendre — les fractions) :**
On donne à la brique **un sujet du programme** — par exemple **« les fractions »** —
et elle le **casse en petits morceaux** qu'on apprend un par un :
numérateur · dénominateur · équivalence (2/4 = 1/2) · simplification · addition de
fractions… Chaque morceau = une **micro-notion**. La brique ne fait que ça : sortir
**la liste des morceaux** d'une notion.
*(« fractions » est une image d'école pour comprendre ; notre périmètre réel de
travail est BTS CIEL.)*

**Pourquoi c'est la base — l'image des crochets :**
Chaque morceau est un **crochet**. Seul, un crochet ne sert à rien. **Toutes les
autres briques viennent accrocher leur savoir dessus** — sans crochets, elles n'ont
nulle part où l'accrocher. Exemple sur le morceau **« addition de fractions »** :
- brique 6 (erreurs typiques) accroche : « erreur classique → additionner les dénominateurs ».
- brique 7 (ambiguïtés) accroche : « le mot *sur* (1 *sur* 2) embrouille ».
- brique 3 (cognitive) accroche : « effort mental élevé ».
- brique 4 (didactique — l'ordre) accroche : « à voir après équivalence et simplification ».
- brique 8 (activités) accroche : « tel exercice du catalogue travaille ce morceau ».

**Sur notre périmètre réel (BTS CIEL) — c'est EXTRACTIF, pas génératif :**
Le référentiel officiel **énumère déjà ses morceaux**, de façon discrète et codée. On
n'invente pas une liste avec un LLM : on **extrait** ce qui est déjà écrit.
- Le document liste les **compétences** (C01 → C11) ; sous chacune, une liste à puces
  de **« connaissances associées »**, chacune portant un **niveau taxonomique** (1 à 4).
- Exemple réel (chunk p.33) : compétence **C01 « Communiquer en situation
  professionnelle »** → connaissances : « Communication interpersonnelle » ·
  « Communication écrite : cahiers des charges, dossiers de présentation » ·
  « Règles de présentation et de typographie »…

**La maille — tranchée :**
- **Le crochet = la connaissance associée** (« Communication écrite… »). C'est sur
  elle que viennent accrocher les briques 6, 7, 3, 8. Une compétence comme
  « Communiquer en situation professionnelle » est **trop large** pour porter une
  erreur typique ou une ambiguïté précise.
- **La compétence = le parent** (le rangement, niveau « notion »).
- **Sortie de brique 1** = un arbre à **2 niveaux (1 seul étage de parenté)** :
  `compétence → [connaissances associées]`.

**Frontière brique 1 / brique 2 :** brique 1 extrait à la maille **connaissance
associée**. Découper **encore plus fin** une connaissance qui en bundle plusieurs
(« cahiers des charges, dossiers de présentation » = deux choses) = **brique 2**
(sous-atomisation). Brique 1 ne descend pas plus bas.

**Ce qu'on garde / ce qu'on écarte à l'extraction :**
- **On garde :** les connaissances associées (les crochets).
- **On écarte (→ autres briques) :** les activités (R1, R4…) et les critères
  d'évaluation ne sont **pas** des micro-notions ; le **niveau taxonomique → brique 3**
  (granularité cognitive), déjà repéré.

- **Apport :** débloque **toutes** les autres briques ; donne un **grain fin** à la
  Différenciation/Remédiation (savoir *quel* morceau re-cibler) et au Détecteur
  d'ambiguïtés (savoir *quelle* micro-notion est floue).
- **Se raccorde à :** Différenciation/Remédiation · Détecteur d'ambiguïtés ·
  catalogue d'activités.
- **Dépend de :** rien — c'est la racine du moteur.
- **Fiabilité du découpage — double validation :**
  1. **Le référentiel EST le découpage (extractif).** Sur un référentiel structuré
     comme BTS CIEL, les morceaux sont **déjà dans le document officiel** → on les extrait,
     on ne les fait pas inventer. Fiabilité native, pas un LLM hasardeux.
     *Deux réserves honnêtes :* (a) l'extraction du PDF est **bruitée** (niveau taxo en
     bout de ligne, items sur deux lignes) → solvable, mais **pas gratuit** ; (b) les
     236 chunks RAG actuels sont taillés à ~900 car. **pour la génération** et coupés en
     pleine phrase → ils **ne portent pas** la structure discrète : brique 1 est une
     **autre passe d'extraction**, pas la réutilisation de ces chunks.
  2. **Le prof adapte.** Le moteur **restitue** le découpage officiel, le prof
     l'**ajuste** à sa classe (fusionner, renommer, compléter). C'est le **jugement de
     terrain** : le référentiel donne une base juste, le prof la rend vivante. Se branche
     au mécanisme **few-shot** existant (l'app apprend la façon du prof) → le découpage
     s'aligne sur **sa** manière. **Toujours sur la notion (savoir générique), jamais
     sur un élève** (garde rouge respectée).

**Brique 2 — Niveaux de granularité**
*Ranger les morceaux sur une échelle de profondeur, du plus large au plus fin.*

**En clair :** la brique 1 sort les **crochets** (les connaissances) ; la brique 2 est
**l'échelle** qui dit, pour chaque morceau, *à quel étage de zoom* il se trouve — du
plus large au plus fin (lexique : notion → sous-notion → micro-compétence → geste
cognitif).

**Sur BTS CIEL — le référentiel ne donne que 2 étages (pas 4) :**
- **compétence** (C01) = niveau **notion** (large, le parent) ;
- **connaissance associée** = la **micro-notion** (le crochet) — **même terme qu'en
  brique 1** (= « micro-compétence » dans l'échelle du lexique : les deux mots désignent
  le même cran).
- « sous-notion » et « geste cognitif » **ne sont pas dans l'officiel** → voir la nature.

**Nature — hybride, trois opérations :**
- **Situer (natif, gratuit) :** placer compétence et connaissance sur l'échelle. C'est
  déjà extrait par la brique 1, rien à produire.
- **Éclater (a) — quasi-extractif :** dédoubler une connaissance composite déjà écrite
  (« cahiers des charges, dossiers de présentation » = 2 items). **Ne crée pas
  d'étage** — ça dédouble *à l'intérieur* du niveau connaissance. Risque **résiduel
  faible, pas nul** (zone grise des conjonctions internes : « verbale et non verbale »
  = un geste ou deux ?) → **validation prof légère**.
- **Générer (b) — seul vrai génératif :** créer un cran **« geste cognitif » sous la
  connaissance**, qui n'est écrit **nulle part** dans l'officiel. C'est **ça** qui
  ajoute un 3ᵉ étage.

**Combien d'étages ? 2 ou 3 — et c'est (b) qui pilote (règle, pas flou) :**
- **2 étages** (compétence + connaissance) quand le geste n'est pas utile ;
- **3 étages** (+ geste) **uniquement** quand (b) est activé.
Le 3ᵉ étage n'existe **que si** un geste est généré ; (a) ne change **jamais** le nombre
d'étages (il dédouble dans le niveau connaissance). On ne dépasse pas 3 (anti usine à gaz).

**Où est le risque — localisé en (b) :** (b) est le seul endroit où le moteur **crée**
au lieu de **lire** → donc le seul où il peut **créer faux** (LLM sans filet officiel,
contrairement à la brique 1 extractive) **et** **créer-vers-l'élève** (garde rouge). Un
seul point de vigilance, deux risques. Limiter (b) au strict utile réduit d'autant la
surface de risque.

**Garde rouge :** (a) comme (b) restent du **savoir générique sur la notion**. La pente
« descendre plus fin » → « découper selon ce dont **cet élève** a besoin » ne pourrait
s'ouvrir qu'**en (b)** ; jamais sur un élève.

- **Apport :** **viser le bon étage** (différencier/remédier au niveau connaissance vs
  geste) ; c'est l'échelle sur laquelle les autres granularités se rangent.
- **Se raccorde à :** Différenciation/Remédiation (niveau de re-ciblage) ·
  catalogue d'activités (associer une activité au bon étage).
- **Dépend de :** **brique 1** — il faut les crochets avant de les situer.
- **Double validation — poids gradué selon l'étage :**
  - **Situer / éclater (a) :** validation prof **légère** (on lit / on sépare de
    l'officiel).
  - **Générer (b) :** le prof **valide ce qui n'a aucune source officielle** — ici il
    n'est plus un confort, c'est **le seul garde-fou**. Poids différent de la brique 1,
    où le prof *affine* un découpage déjà officiel.
- **Frontière brique 1 / brique 2 :** brique 1 = *quels* morceaux (maille native,
  extractive) ; brique 2 = *jusqu'où* on descend (situer + éclater + générer le geste).
  Brique 2 ne ré-extrait pas ; brique 1 ne descend pas sous la connaissance.

**Brique 3 — Granularité cognitive**
*Pour chaque micro-notion, deux choses distinctes : le niveau de maîtrise visé
(officiel) et l'effort mental demandé (estimé).*

**En clair :** une fois les crochets (brique 1) rangés sur l'échelle (brique 2), la
brique 3 répond à deux questions différentes pour chaque morceau — **« il faut le
maîtriser jusqu'où ? »** et **« il coûte combien d'effort ? »**.

**Sur BTS CIEL — deux axes orthogonaux, prouvés par la légende officielle :**
Le référentiel attache à chaque connaissance un **niveau taxonomique 1-4**
(lignes 1364-1370), défini comme **« les limites de connaissances attendues »** :
Niveau 1 = information · 2 = expression · 3 = maîtrise d'outils · 4 = maîtrise
méthodologique.
→ C'est une **ambition de maîtrise** (jusqu'où l'élève doit aller), **pas** l'effort
mental. Les deux sont **orthogonaux** : un Niveau 2 peut être lourd, un Niveau 4 léger.

**Nature — une part extractive + une part générative (comme briques 1-2) :**
- **Part extractive — le niveau de maîtrise visé :** le **niveau taxo officiel**, lu
  tel quel. Fiable, gratuit. Risque **résiduel faible, pas nul** (même bruit PDF que les
  connaissances : « Niveau 3 » traîne en bout de ligne).
- **Part générative — la charge cognitive (effort) :** **absente de l'officiel** →
  estimée par le moteur. Pendant du (b) de la brique 2 : sans filet officiel → **échelle
  simple (faible / moyen / élevé)**, **pas de score faussement précis**, **validée par
  le prof**.

**Le lien entre les deux (sinon elles semblent juxtaposées) :** le **niveau taxo est
l'indice d'entrée** qui *alimente* l'estimation d'effort (un Niveau 4 *suggère souvent*
plus de charge) **sans la déterminer** (Niveau 2 lourd / Niveau 4 léger restent
possibles). L'estimation finale de charge **reste un jugement distinct, validé prof**.
L'extractif **informe** le génératif, il ne le **remplace pas**.

**Garde rouge :** maîtrise visée et charge restent des **propriétés de la notion**
(génériques). La pente vers « l'effort **de cet élève** » ne s'ouvrirait que sur la part
générative → jamais sur un élève.

- **Apport :** **dosage de la difficulté** + différenciation (choisir un morceau à la
  portée de l'élève, sans le surcharger).
- **Se raccorde à :** Différenciation/Remédiation · (futur) Assistant de calibration.
- **Dépend de :** **brique 1** (les morceaux) et **brique 2** (situer sur l'échelle).
- **Double validation — poids gradué (comme briques 1-2) :** part extractive (taxo) →
  validation prof **légère** ; part générative (charge) → le prof est **le garde-fou**
  (rien d'officiel en dessous).
- **Frontière :** brique 3 **qualifie** le morceau (maîtrise visée + effort) ; elle ne
  le **crée** pas (brique 1) ni ne le **range** pas (brique 2). En un mot :
  **1 le crée, 2 le range, 3 le qualifie.**

**Brique 4 — Granularité didactique (l'ordre)**
*L'ordre d'enseignement des micro-notions — quoi avant quoi (progressivité, prérequis).*

**En clair :** la 4 pose la **flèche du temps** sur les crochets — dans quel ordre les
enseigner.

**Nature — générative + prof, conforme à l'intention du référentiel.** Constat acté : le
référentiel ne donne **pas** d'ordre — ni explicite, ni implicite (listage **thématique**
par discipline, pas chronologique ; puces non numérotées) — et **délègue explicitement la
progression au prof** (lignes 2140/2173 : « organisent leurs progressions en
concertation »). Donc le génératif + prof n'est **pas un pis-aller** : c'est ce que le
référentiel demande.

**Deux types d'ordre — localiser le risque :**
- **Ordre contraint** — déductible de la structure des notions (additionner des fractions
  exige le dénominateur). **Mais pas auto-évident :** c'est le **LLM qui propose** le
  prérequis, et il peut en **inventer un faux** (poser « A avant B » alors qu'ils sont
  indépendants) ou **inverser** une dépendance. → **risque résiduel faible (pas nul)**,
  validation prof **légère mais réelle** — proposé puis vérifié, pas lu quelque part.
- **Ordre optionnel** — vrai choix pédagogique (équivalence avant ou après
  simplification ?). Plusieurs progressions défendables → **« optimal n'est pas unique »
  à plein, prof central, risque d'arbitraire.**

**Rapport à la brique 3 — elle éclaire, ne détermine pas.** Le taxo (information →
maîtrise) peut *suggérer* une montée, mais l'ordre se fonde d'abord sur les **prérequis
logiques**, pas sur le taxo. → **enrichie par la 3, sans en dépendre** (comme la 6 par la
7). Pas de « posé ≠ raccordé ».

**Garde rouge :** un ordre est une propriété de la **notion / de la progression**
(générique), jamais « l'ordre adapté à *cet élève* ».

- **Apport :** donne l'**ordre d'enseignement** → alimente le **Générateur de séquences**
  et l'**Optimiseur** (la 4 est la première brique qui nourrit fortement les outils de
  séquence).
- **Se raccorde à :** Générateur de séquences · Optimiseur de séquences.
- **Dépend de :** **brique 1 (dur)** — il faut les connaissances pour les ordonner entre
  elles ; la profondeur de la 2 n'est pas requise à ce niveau. **Brique 2 (conditionnel)**
  — **seulement si** on ordonne aussi les **gestes** générés en 2(b) (la 4 ordonne les
  frères à chaque étage existant). Rapport **différent** de la brique 3, qui dépend
  vraiment de la 2.
- **Double validation — poids gradué :** ordre contraint → prof **léger (mais réel)** ;
  ordre optionnel → prof **central**.
- **Frontière — ne pas confondre 2 et 4 :** la **2 range en profondeur** (étages de zoom),
  la **4 ordonne dans le temps** (quoi avant quoi) — deux axes **orthogonaux**. La 4 ne
  crée pas le morceau (1), ne le range pas en profondeur (2), ne le qualifie pas (3).
  Mnémonique : **1 le crée · 2 le range (profondeur) · 3 le qualifie · 4 l'ordonne
  (temps) · 7 signale le piège · 6 dit l'erreur · 8 le relie aux activités.**

**Brique 5 — Granularité disciplinaire**
*La même notion découpée différemment selon la matière — le même mot, un sens différent.*

**En clair :** un même mot peut être un savoir différent selon la matière (ex. « fonction »
en Maths ≠ en Développement, « signal » en Physique ≠ en Réseaux). La 5 **distingue** ces
sens et **signale le contresens**.

**Sur BTS CIEL — portée étroite (réserve de portée) :** on est sur **un seul référentiel**,
donc la « variation entre disciplines » se réduit aux **9 matières** du BTS CIEL (pas une
variation entre référentiels — ça, c'est multi-référentiel/secondaire). → **faible
priorité**, à ne traiter que sur les **notions vraiment polysémiques** entre ces 9 matières.
Cohérent avec sa note basse, et désamorce le risque « explosion combinatoire ».

**Nature — hybride, mais le cœur est génératif :**
- **Extractif :** surtout la **matière/bloc** où vit chaque connaissance — signal solide,
  mais **trivial**.
- **Puce de discipline (⚫ physique / − STI, légende 1362-1363) — bonus GROSSIER, pas la
  matière fine :** vérifié, elle ne distingue que **2 champs** (physique vs STI), **à
  l'intérieur des compétences pro seulement** (les matières générales n'y sont pas). Elle
  n'atteint **pas** les 9 matières ; la polysémie fine (« fonction » Maths vs Développement)
  **tombe hors de ce marqueur**. Utile au plus pour un contresens physique↔STI.
- **Génératif (le vrai cœur) :** **détecter la polysémie** (même mot, sens ≠ selon la
  matière) et **signaler le contresens** — absent du référentiel → inféré, **prof valide**.
  C'est le **contenu propre** de la 5 (sans ça, elle se réduirait au rangement par matière,
  déjà trivial).

**Frontière — 5 vs 11 :** **5 distingue** (même mot, découpage ≠ selon la matière) ;
**11 (future) relie** (ponts entre matières). *5 distingue, 11 relie.*

**Relation à la 8 :** même **axe matière** que la 8 ; la 5 fiabilise « quel découpage pour
quelle matière » en amont du pont 8.

**Garde rouge :** variation = propriété de la **notion selon la matière** (générique),
jamais selon un élève. *(C'est la brique où la garde rouge est la moins sollicitée — la
polysémie est intrinsèquement une propriété de la notion ; gardée pour l'homogénéité.)*

- **Apport :** évite les **contresens inter-matières**, fiabilise le découpage par discipline.
- **Se raccorde à :** catalogue d'activités (par matière) · Générateur d'activités.
- **Dépend de :** **brique 1** (le découpage de base).
- **Double validation :** extractif (matière) → trivial ; génératif (polysémie/contresens)
  → **prof = garde-fou**.

**Brique 6 — Granularité des erreurs typiques**
*Pour chaque micro-notion, les erreurs typiques de la notion — le résultat faux fréquent.*

**En clair :** sur chaque morceau, la brique 6 accroche **l'erreur classique** qu'on y
rencontre (ex. « addition de fractions → additionner les dénominateurs »). C'est le
**cœur de la Remédiation** : anticiper l'erreur permet des remédiations ciblées, des
exercices anti-erreur, de l'anticipation dans les activités.

**Sur BTS CIEL — pas de part extractive (constaté) :** le référentiel ne liste **pas** les
erreurs typiques (recherche « erreur » déjà faite en brique 7 : seulement des grilles
d'éval, jamais une liste par notion). → la brique 6 **produit** ses erreurs.

**Deux sources, aucune n'est « la » source :**
- **(i) dérivée d'une ambiguïté (chaînage 7→6) :** « ce piège de formulation produit
  typiquement cette erreur ». La 7 **enrichit** la 6.
- **(ii) autonome (conceptuelle) :** erreurs **sans** ambiguïté amont (malentendu de
  fond) — **probablement le plus gros volume en pratique**.
→ La 7 est **une porte parmi deux, pas la principale** : l'essentiel des erreurs peut ne
passer par aucune ambiguïté. Les deux sources sont **génératives** → **prof = garde-fou**.

**État actuel — génératif, pas figé définitivement :** la fiche d'origine vise un
**ancrage didactique** (« ancrer sur des sources didactiques »), **mais ce corpus
n'existe pas dans le projet aujourd'hui**. Donc, **à ce jour, brique 6 = 100 %
génératif + prof**. **À reconsidérer si/quand un RAG didactique est ajouté** : il
introduirait une part extractive → la 6 deviendrait **hybride** (comme 1 et 3). On
n'écrit pas l'ancrage comme un acquis (« posé ≠ raccordé »).

**Chaînage et frontière (cause→effet) :** 6 = l'**effet** (le résultat faux, **aval**) ;
elle se raccroche à la 7 = la **cause** (la formulation qui piège, amont). La fiche 6
**s'arrête à sa moitié**, ne redéfinit pas la 7.

**Garde rouge :** une erreur typique est une propriété **générique de la notion**
(« erreur classique sur ce morceau »), jamais « *cet élève* a fait cette erreur ».

- **Apport :** cœur de la Remédiation (remédiations ciblées, exercices anti-erreur,
  anticipation dans les activités).
- **Se raccorde à :** Remédiation · Détecteur d'ambiguïtés · Générateur d'activités.
- **Dépend de :** **briques 1 et 2** (on annote le morceau tel qu'il existe après la 2) ;
  **enrichie par la 7**, sans en dépendre.
- **Double validation :** génératif (i et ii) → **prof = garde-fou** ; poids à graduer le
  jour où un ancrage didactique existe.
- **Frontière :** brique 6 **dit l'erreur** qui résulte sur un morceau ; elle ne le crée
  pas (1), ne le range pas (2), ne le qualifie pas (3), ne signale pas le piège amont (7).
  Mnémonique : **1 le crée, 2 le range, 3 le qualifie, 7 signale ce qui y piège, 6 dit
  l'erreur qui en résulte.**

**Brique 7 — Granularité des ambiguïtés**
*Pour chaque micro-notion, les mots / schémas / contextes qui peuvent induire en
erreur — la formulation qui piège.*

**En clair :** sur chaque crochet (brique 1), la brique 7 accroche **ce qui peut
tromper** dans la façon de présenter le morceau — un mot à double sens, un schéma
trompeur, un contexte ambigu. Elle rend le **Détecteur d'ambiguïtés (déjà en prod)**
plus précis : il sait *quelle* micro-notion porte le piège.

**Sur BTS CIEL — pas de part extractive (confirmé) :** le référentiel **ne liste nulle
part** d'ambiguïtés/pièges (vérifié : structure = activités / connaissances + taxo /
critères, rien d'autre ; les « limites / erreurs » trouvés sont du contenu, des
exclusions de programme ou des grilles d'éval — jamais une source de piège par notion).
Donc, contrairement aux briques 1 et 3, **aucun ancrage officiel** : la brique 7
**produit** ses ambiguïtés.

**Deux régimes génératifs (pas un bloc) :**
- **Régime 1 — adossé au Détecteur d'ambiguïtés (en prod) :** on **récolte / indexe**,
  crochet par crochet, la sortie d'un outil **déjà éprouvé**. Risque = **hérité** (la
  fiabilité du détecteur, déjà jaugée en prod), **pas neuf**.
- **Régime 2 — création pure :** les ambiguïtés que le détecteur ne couvre pas,
  proposées en plus par le LLM. **Vrai (b) plein régime, sans filet → prof = seul
  garde-fou.**

**Chaînage avec la brique 6 (cause → effet) — frontière à tenir :** la brique 7 produit
la **cause** (l'ambiguïté, la formulation qui peut tromper, **en amont**) ; la brique 6
s'y **raccrochera** pour l'**effet** (le résultat faux, **en aval**). **La fiche 7
s'arrête à sa moitié** — elle ne décrit pas comment la 6 travaille (sinon on pré-écrit
la 6 ici). Frontière : **7 = la formulation qui peut tromper · 6 = le résultat faux qui
en découle.**

**Garde rouge :** une ambiguïté est une propriété de la **formulation / de la notion**
(« ce mot piège *en général* »), jamais « *cet élève* s'est trompé ». Reste générique.

- **Apport :** rend le Détecteur d'ambiguïtés (en prod) plus précis (il sait *quelle*
  micro-notion porte le piège) ; nourrit aussi le Générateur d'activités.
- **Se raccorde à :** Détecteur d'ambiguïtés (direct) · Générateur d'activités.
- **Dépend de :** **briques 1 et 2** — la 1 produit les crochets, la 2 peut **affiner
  le grain** (sous-atomisation) ; une ambiguïté porte sur le morceau **tel qu'il existe
  après la 2** (même rapport amont que la brique 3).
- **Double validation — poids gradué :** régime 1 (adossé détecteur) → risque hérité,
  validation prof **légère** ; régime 2 (création pure) → prof = **seul garde-fou**.
- **Frontière :** brique 7 **signale ce qui peut tromper** sur un morceau ; elle ne le
  **crée** pas (1), ne le **range** pas (2), ne le **qualifie** pas (3), et ne décrit pas
  l'**erreur résultante** (6). En un mot : **1 le crée, 2 le range, 3 le qualifie,
  7 signale ce qui y piège.**

**Brique 8 — Granularité des activités compatibles**
*Quelles activités du catalogue savent travailler chaque micro-notion.*

**En clair :** sur chaque crochet (avec son grain / brique 2), la 8 accroche **quelles
activités du catalogue** le travaillent → le Générateur propose la bonne activité pour le
bon morceau. C'est le **pont** entre la connaissance et le catalogue.

**Constat du catalogue (structure réelle, `src/activities.py`) :** une entrée =
`matière → type d'activité → { sous_types (format), params }`. Tagué à la maille
**matière × type × format** ; **aucun champ ne relie une activité à une micro-notion**.
Association **par nom exact** de matière (`routers/activites.py:14`).

**Nature — hybride à dominante générative :**
- **Extractif (grossier) :** matière, type d'activité, sous-type de format — **lus** dans
  le catalogue.
- **Génératif (le gros) :** le **lien jusqu'au crochet** (« cette activité travaille cette
  micro-notion ») n'est **nulle part** dans le catalogue → **inféré**. Sans filet → **prof
  = garde-fou**, risque de mapping arbitraire.

**Type d'activité = implicite dans le nom** (« Évaluation… », « Fiche de révision »), pas
un champ. Pour s'en servir, l'**inférer**. Une « Évaluation » pourrait s'aligner sur le
taxo (brique 3). **La 8 est aussi enrichie par la 6** : les erreurs typiques orientent le
choix d'une activité **anti-erreur**. **Nuance :** le catalogue n'ayant **pas de type
« remédiation »**, ce lien 6→activité n'est **pas porté par un tag** — il reste **inféré**
(génératif).

**Réserve d'état — sur BTS CIEL, le catalogue est quasi vide.** Constaté : sur les 9
matières BTS CIEL, **1 seule (Mathématiques)** a de vraies activités ; les **8 autres**
retombent sur **3 types génériques**. → La brique 8 est **définie**, mais **quasi vide sur
BTS CIEL tant que le catalogue n'est pas étoffé**. **« Étoffer le catalogue BTS CIEL » =
un chantier à part entière** (4 matières *near-miss* à adapter du secondaire — Français,
Langues Vivantes, Physique-Chimie, NSI — + 4 techniques à créer — Réseaux, Cybersécurité,
Développement, Maintenance).

**Garde rouge :** le lien activité↔notion est une propriété **générique** (la notion),
jamais « l'activité pour *cet élève* ».

- **Apport :** le Générateur propose la bonne activité pour le bon grain — le pont
  connaissance ↔ catalogue.
- **Se raccorde à :** catalogue d'activités · Générateur d'activités.
- **Dépend de :** **briques 1 et 2 (dur)** — les morceaux + leur grain. **Enrichie par**
  la **3** (taxo → type d'éval), la **4** (ordre → la bonne activité au bon moment) et la
  **6** (erreurs → activité anti-erreur) — liens **inférés**, pas des dépendances.
- **Double validation :** extractif (matière/type) → prof **léger** ; lien au crochet
  (génératif) → **prof = garde-fou**.
- **Frontière :** la 8 **relie** le morceau aux activités ; elle ne le crée pas (1), ne le
  range pas (2), ne le qualifie pas (3), ne l'ordonne pas (4), ne décrit pas pièges/erreurs
  (7/6). Mnémonique : **1 le crée · 2 le range (profondeur) · 3 le qualifie · 4 l'ordonne
  (temps) · 7 signale le piège · 6 dit l'erreur · 8 le relie aux activités.**

**Brique 11 — Granularisation interdisciplinaire**
*Relier une même notion entre matières — tisser le pont.*

**En clair :** la 11 **relie** un crochet d'une matière à son équivalent dans une autre
(ex. « signal » Physique ↔ Réseaux) — pour **tisser le pont**, pas pour distinguer (ça,
c'est la 5).

**Nature — générative, doublement réservée :**
- **Pas d'extractif :** le référentiel ne liste **aucun pont** entre matières → inféré,
  prof valide. (Il évoque juste une intention « pluri-disciplinarité », ligne 2173 — un
  cap, pas des ponts donnés.)
- **Réserve double :** (1) outil cible **futur** (« Cohérence curriculaire
  inter-disciplines » n'existe pas) → **non raccordable aujourd'hui** ; (2) **un seul
  référentiel** → ponts possibles seulement entre les 9 matières BTS CIEL, pas entre
  référentiels. → **très basse priorité.**

- **Apport :** ponts entre disciplines → **cohérence curriculaire inter-matières**.
- **Se raccorde à :** (futur) Cohérence curriculaire inter-disciplines.
- **Dépend de :** **brique 1 (dur)** — les crochets à relier. **Enrichie par la 5**
  (sans en dépendre) : la 5 distingue les sens d'un même mot → elle **garde la 11 contre
  les faux ponts** (même mot ≠ même notion), mais la 11 peut inférer un pont directement
  des deux crochets. *(Aligné sur les autres fiches : dépendance dure = la racine 1 ; le
  reste = enrichissement.)*
- **Frontière :** **5 distingue, 11 relie** — quasi-opposées : la 5 sépare, la 11 tisse.
- **Garde rouge :** un pont est une propriété **générique** (notion ↔ notion entre
  matières), jamais selon un élève.

**Brique 12 — Granularisation spiralaire**
*Le rythme de réactivation d'une micro-notion — quand la revoir.*

**En clair :** la 12 attache à chaque morceau son **rythme de retours** (répétition
espacée) — « ce morceau se réactive bien à tel intervalle ».

**Nature — générative :** le référentiel ne donne aucun rythme de réactivation → inféré,
prof valide.

**Rythme ABSTRAIT, pas calendrier concret (point tranché) :** la 12 produit un **rythme
générique, propriété de la notion** (« réactiver à J+7, J+30… »), **pas un calendrier
daté**. Le **calendrier concret** (ancré sur les dates réelles d'introduction) se construit
**en aval, dans le Générateur/Optimiseur de séquences**, qui combine le rythme (12) +
l'ordre réel (4). → cohérent avec tout le moteur : les briques produisent des **propriétés
génériques de la notion** ; les **outils** les appliquent à une classe réelle.

**Particularité parmi les futures :** seule future raccordée à des **outils existants**
(Générateur + Optimiseur de séquences), pas à un outil futur. Sa réserve n'est donc pas
« non raccordable faute d'outil » mais **« temps long (progression annuelle) pas encore
modélisé »**.

- **Apport :** mémorisation durable, séquences sur l'année.
- **Se raccorde à :** Générateur de séquences · Optimiseur de séquences.
- **Dépend de :** **brique 1 (dur)** — les morceaux à réactiver. **Enrichie par la 4**
  (l'ordre **calibre** le rythme) et la **2** (le grain), sans en dépendre : le rythme
  reste générique même sans l'ordre réel — c'est l'**outil aval** qui a besoin de la 4
  pour dater, pas la brique.
- **Frontière — 4 vs 12 :** la **4 = la 1ʳᵉ passe** (quoi avant quoi, l'introduction) ;
  la **12 = les retours** (le rythme des révisions). 4 = ordre d'introduction, 12 =
  répétition espacée.
- **Garde rouge (sollicitée) :** le rythme est une **propriété générique de la notion**,
  jamais « réactiver selon ce que **cet élève** a oublié » (= suivi d'élève, interdit). Le
  choix **« rythme abstrait » verrouille la garde rouge** ; la pente vers
  l'individualisation (naturelle pour la répétition espacée) est refusée ici.

**Brique 13 — Granularisation émotionnelle légère**
*Étiqueter un morceau « généralement intimidant / décourageant en première approche ».*

**En clair :** la 13 attache à un morceau un label générique « intimidant en début
d'apprentissage » — pour éviter de démarrer par là.

**Nature — générative, la plus subjective :** rien d'émotionnel dans le référentiel →
entièrement inféré, prof valide. La plus molle du moteur → garder **léger**.

**Label ABSTRAIT, même résolution que la 12 :** la 13 produit un **label générique** (« ce
morceau intimide en général »), **indépendant de l'ordre**. La recommandation « ne pas le
placer **trop tôt** » est l'**application** de ce label **croisé avec l'ordre (4)**, faite
**en aval** (au moment de séquencer). → **dépend dur de 1 ; enrichie par 4** (l'ordre situe
le « trop tôt ») **et par 3** (forte charge en début = souvent décourageant), sans en
dépendre. *(Cohérent avec la 12 : la brique produit une propriété générique ; le croisement
avec l'ordre est aval.)*

**Frontière — 13 vs 3 :** la **3 = l'effort** (objectivable, ancré taxo) ; la **13 = le
ressenti** (anxiogène/motivant). Liées mais distinctes : lourd ≠ intimidant (un morceau
peut être lourd mais motivant, ou léger mais intimidant). Ne pas réduire la 13 à « 3 élevé ».

**Garde rouge — la plus sollicitée du moteur :** « intimidant » appelle dangereusement
« pour **cet élève** ». La 13 reste **générique** (« cette notion intimide en général »),
**jamais** « cet élève est anxieux ». La pente vers l'élève est ici la plus forte (signalée
dès le début).

**Réserve double :** (1) outil cible **futur** (« calibration émotionnelle » n'existe pas)
→ non raccordable ; (2) **très subjective** → garder **léger**, faible priorité (★★), ne
pas en faire un gadget.

- **Apport :** meilleure **motivation** — ne pas démarrer par un morceau démoralisant.
- **Se raccorde à :** Différenciation · (futur) calibration émotionnelle.
- **Dépend de :** **brique 1 (dur)** ; **enrichie par 3 et 4**, sans en dépendre.

**Brique 14 — Granularisation cognitive profonde**
*Relier une micro-notion aux mécanismes mentaux qu'elle mobilise (mémoire de travail,
inhibition…).*

**En clair :** là où la 3 dit *combien* d'effort, la 14 dit **quels rouages mentaux** un
morceau mobilise.

**Nature — générative, la plus théorique :** rien de tel dans le référentiel → entièrement
inféré. Brique **frontière recherche**.

**Frontière — 14 vs 3 (l'enjeu) :** la **3 = l'effort global** (combien) ; la **14 = les
mécanismes précis** (quels rouages). Deux **grains de la même dimension cognitive**, lus
tous deux **depuis le morceau (1)**. Ne pas refaire la 3 sous un vocabulaire savant.

**Garde rouge :** les mécanismes sont une propriété de la **notion** (ce qu'**elle** exige),
jamais « la mémoire de travail de **cet élève** » (pas de profilage cognitif).

**Réserve forte (la plus « future ») :** (1) outil cible **futur** (« Assistant de
calibration cognitive » n'existe pas) ; (2) **frontière recherche** → **YAGNI explicite** :
ne rien construire tant que le cœur (briques 1-8) ne tourne pas. Priorité plancher
(faisabilité la plus basse, effort le plus haut ★★★★★).

- **Apport :** calibration **cognitive fine** — relier les morceaux aux mécanismes mobilisés.
- **Se raccorde à :** (futur) Assistant de calibration cognitive.
- **Dépend de :** **brique 1 (dur)** — les mécanismes se lisent **directement du morceau**,
  pas de la sortie de la 3. **En lien étroit avec la 3** (même dimension, grain plus fin) :
  elles **s'éclairent mutuellement** sans dépendance dure. *(Le mot « approfondit » de la
  fiche d'origine était trompeur — la 14 lit le morceau, pas le verdict de la 3 ; aligné
  sur 12/13 : dur = 1, le reste = enrichissement.)*

---

## 6. À trancher au moment de construire chaque brique (pas maintenant)

Les détails d'une brique — comment elle marche, qui valide, où c'est stocké — se
décident quand on l'attaque, pas au stade de l'inventaire.

---

## 7. Plan de dispatch (où va chaque brique dans le tableau de bord)

> Pour chaque brique : **« Nouvel item »** (à créer) ou **« Enrichit l'item X »**
> (item qui existe déjà). Une ligne à la fois, validée ensemble. Rien d'écrit dans
> le tableau de bord aujourd'hui — c'est juste le plan.

| Brique | Où elle va |
|---|---|
| 1. Découpage en micro-notions | Nouvel item |

*(Briques suivantes : à analyser une par une.)*

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
- **Différenciation** — adapter une activité à des besoins différents d'élèves, sans
  changer l'objectif. Toujours sur des **catégories génériques**, jamais sur un élève
  nommé.
- **DYS** — famille des troubles « dys » de l'apprentissage : dyslexie (lecture),
  dyspraxie (geste), dyscalculie (nombres), dysphasie (langage)… Catégorie générique.
- **FLE** — « Français Langue Étrangère » : élèves dont le français n'est pas la
  langue maternelle. Catégorie générique.
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
- **24/06** — **Évaluation complète des 14 briques** (notes + fiches). Brique existante :
  1-2-6-7 en **P1**, 3-4-8 en **P2**, 5 en **P3**. Brique future (11-14) toutes
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
- **25/06** — Tableau §5 : intitulés des deux blocs renommés (« Socle » → **Brique
  existante**, « Niveau supérieur » → **Brique future**) — ils trompaient ; la vraie
  ligne de partage = outil branché **déjà existant** vs **futur**. Fiche brique 1 :
  l'ancien « risque » devient **double validation** — (1) référentiel/RAG **déjà
  résolu et prouvé** (9/9 Activité, BTS CIEL) ; (2) **validation prof obligatoire**
  (ajuste le découpage, se branche au few-shot, toujours sur la notion jamais sur un
  élève). Point jugé essentiel, à retrouver dès qu'on attaque la brique 1.
- **25/06** — **Brique 1 tranchée (constat code à l'appui).** Lecture du RAG : 236
  chunks taillés à ~900 car. **pour la génération**, coupés en pleine phrase → ne
  portent PAS de structure de découpage. MAIS le référentiel BTS CIEL **liste nativement**
  ses morceaux (compétences C01→C11 → « connaissances associées » à puces, chacune avec
  un niveau taxonomique). **Décisions actées :** (1) découpage = **EXTRACTIF**, pas
  génératif (le doc officiel contient déjà les morceaux) ; (2) **maille = la connaissance
  associée** (= le crochet) ; compétence = parent ; sortie = `compétence →
  [connaissances]` ; (3) renvoyé à la brique 2 = **uniquement** la sous-atomisation des
  connaissances composites ; (4) garde = connaissances ; écarte = activités + critères
  (autres briques), niveau taxo → brique 3 ; (5) l'ancienne « preuve 9/9 = découpage
  résolu » **supprimée** (le 9/9 prouvait la génération, pas le découpage) → double
  validation reformulée : le référentiel EST le découpage, le prof adapte.
- **25/06** — **Brique 2 tenue.** L'échelle de profondeur, ancrée sur le réel BTS CIEL (le
  référentiel ne donne que 2 étages : compétence = notion, connaissance =
  micro-compétence). **Nature hybride en 3 opérations :** *situer* (natif, gratuit) ·
  *éclater (a)* une connaissance composite (quasi-extractif, **risque résiduel faible
  pas nul**, validation prof légère) · *générer (b)* un geste sous la connaissance
  (**seul vrai génératif, sans filet officiel**). **Distinction (a)/(b)** = grille qui
  **localise** le risque : LLM-faux ET pente-vers-l'élève tombent tous deux en (b) (seul
  endroit où le moteur crée au lieu de lire) → un point de vigilance, deux risques.
  **Étages : 2 ou 3, piloté par (b)** (3ᵉ étage seulement si geste généré ; (a) ne crée
  pas d'étage). **Validation prof à poids gradué** : légère sur situer/(a), seul
  garde-fou sur (b). Garde rouge : tout reste générique, dérive possible seulement en (b).
- **25/06** — **Brique 3 tenue (constat légende à l'appui).** Vérif de la légende
  taxonomique du référentiel (lignes 1364-1370) : les Niveau 1-4 décrivent **« les
  limites de connaissances attendues »** (information → expression → maîtrise d'outils →
  maîtrise méthodologique) = **maîtrise visée, PAS effort**. Donc **deux axes
  orthogonaux** (prouvé, pas supposé). **Structure :** part **extractive** = niveau taxo
  officiel (maîtrise visée, risque résiduel faible) · part **générative** = charge
  cognitive estimée (effort, sans filet officiel, échelle simple, prof valide). **Lien :**
  le taxo est l'**indice d'entrée** qui alimente l'estimation d'effort sans la déterminer
  (Niveau 2 lourd / Niveau 4 léger possibles) ; estimation finale = jugement distinct,
  validé prof. Garde rouge : propriétés de la notion, dérive possible seulement sur le
  génératif.
- **25/06** — **Brique 7 tenue (constat à l'appui).** Vérif ciblée du référentiel
  (*limite/précision/vigilance/difficulté/piège/erreur…*) : **aucune rubrique
  d'ambiguïtés par notion** (les occurrences = contenu, exclusions de programme, grilles
  d'éval). → **pas de part extractive** : la brique 7 **produit** ses ambiguïtés. **Deux
  régimes génératifs** (pas un bloc) : régime 1 = adossé au **Détecteur d'ambiguïtés en
  prod** (récolte/indexe, **risque hérité déjà jaugé**) · régime 2 = **création pure**
  (sans filet, prof seul garde-fou). **Chaînage 6/7 cause→effet** (7 = formulation qui
  piège, amont · 6 = résultat faux, aval) ; la fiche 7 s'arrête à sa moitié, ne pré-écrit
  pas la 6. Garde rouge : propriété de la formulation, jamais d'un élève.
  **Fil ouvert noté** (hors brique 7) : les **exclusions de programme** Maths/LV
  (« à l'exception de… ») sont une donnée officielle qui pourrait servir une future
  brique **« périmètre de génération autorisé »** (ce que le moteur a le droit de
  générer). À ressortir le moment venu.
- **25/06** — **Brique 6 tenue.** Pas de part extractive (référentiel ne liste pas les
  erreurs — recherche « erreur » déjà couverte en brique 7) → **générative**. **Deux
  sources, aucune principale :** (i) dérivée d'une ambiguïté (chaînage 7→6, la 7
  *enrichit*) · (ii) autonome/conceptuelle (sans ambiguïté amont, **probablement le plus
  gros volume**). La 7 = une porte sur deux, pas la principale. **Dépend de 1 et 2,
  enrichie par 7 sans en dépendre** (parallèle taxo→charge brique 3). Chaînage cause→effet
  (6 = effet/aval, 7 = cause/amont), fiche 6 s'arrête à sa moitié. Garde rouge : propriété
  générique de la notion. **Fil ouvert / réserve d'état :** la fiche d'origine vise un
  ancrage « sources didactiques » **inexistant aujourd'hui** → **brique 6 figée dans son
  état actuel (100 % génératif + prof), PAS définitivement** ; si/quand un **RAG
  didactique** est ajouté, elle devient **hybride** (extractif + génératif, comme 1 et 3)
  et la fiche est à reprendre. Ne pas croire la fiche 6 « à jour » ce jour-là.
- **25/06** — **Brique 4 tenue (constat à l'appui).** Vérif ordre dans le référentiel :
  **aucun ordre** explicite ni implicite (listage thématique par discipline, puces non
  numérotées) ; mieux, le doc **délègue la progression au prof** (lignes 2140/2173). →
  **générative + prof, conforme à l'intention du référentiel** (pas un pis-aller). **Deux
  types d'ordre :** *contraint* (déductible des notions, mais **proposé par le LLM** qui
  peut inventer/inverser un prérequis → **résiduel faible pas nul**, prof léger mais
  réel) · *optionnel* (vrai choix pédagogique, « optimal pas unique », prof central). Pendant
  de (a)/(b). **Enrichie par la 3** (taxo informe l'ordre) sans en dépendre. **Dépend de 1
  (dur)** ; **2 conditionnel** (seulement pour ordonner les gestes générés en 2(b)) — rapport
  différent de la 3. **Frontière 2/4 :** la 2 range en profondeur (zoom), la 4 ordonne dans
  le temps — deux axes orthogonaux. Mnémonique : 1 crée · 2 range (profondeur) · 3 qualifie
  · 4 ordonne (temps) · 7 piège · 6 erreur.
- **25/06** — **Brique 8 figée AVEC RÉSERVE (constat code à l'appui).** Structure du
  catalogue (`src/activities.py`, `routers/activites.py:14`) : `matière → type → {sous_types
  (format), params}`, match **par nom exact**, **aucun lien à la micro-notion**. → brique 8 =
  **hybride à dominante générative** : extractif grossier (matière/type/format lus) +
  génératif (lien jusqu'au crochet inféré, prof = garde-fou). Type d'activité **implicite
  dans le nom** (pas un champ) ; pas de type « remédiation » → pas de raccord direct à la 6.
  **RÉSERVE D'ÉTAT :** sur les **9 matières BTS CIEL**, **1 couverte** (Mathématiques),
  **8 sur 3 génériques** → la 8 est **définie mais quasi vide sur BTS CIEL tant que le
  catalogue n'est pas étoffé**. **Chantier à part « étoffer le catalogue BTS CIEL »** acté
  par Harketti (priorité) : 4 *near-miss* (Français, Langues Vivantes, Physique-Chimie, NSI
  — adapter le secondaire) + 4 techniques à créer (Réseaux, Cybersécurité, Développement,
  Maintenance). Dépend de 1 et 2 ; type inféré → lien possible vers la 3. Mnémonique
  étendue : …7 piège · 6 erreur · **8 relie aux activités**.
- **25/06** — **Brique 5 tenue (constat puce vérifié).** Cœur = **génératif** : détecter la
  polysémie (même mot, sens ≠ selon la matière) + signaler le contresens — c'est son contenu
  propre. **Extractif faible :** surtout la matière/bloc (trivial) ; la **puce ⚫/− est
  grossière** (vérifié légende 1362-1363 : seulement 2 champs **physique vs STI**, dans les
  compétences pro, pas les 9 matières → la polysémie fine tombe hors puce). **Réserve de
  portée :** un seul référentiel → variation entre les **9 matières** BTS CIEL seulement (pas
  inter-référentiel) → **faible priorité, notions polysémiques uniquement** (désamorce
  l'explosion combinatoire). **Frontière 5/11 : 5 distingue, 11 relie.** Garde rouge la moins
  sollicitée (polysémie = propriété de la notion). → **Catégorie « Brique existante »
  complète : 1, 2, 3, 4, 5, 6, 7, 8 toutes tenues.**
- **25/06** — **Brique 11 tenue (1ʳᵉ des futures).** **Générative** (le référentiel ne
  liste aucun pont inter-matières → inféré, prof valide). **Doublement réservée :** outil
  cible **futur** (non raccordable) + **un seul référentiel** (ponts seulement entre les 9
  matières BTS CIEL). **Dépend dur de 1 ; enrichie par la 5** (qui garde contre les faux
  ponts : même mot ≠ même notion), sans en dépendre — aligné sur les autres fiches.
  **Frontière : 5 distingue, 11 relie** (quasi-opposées). Très basse priorité. Garde rouge :
  pont générique, jamais selon un élève.
- **25/06** — **Brique 12 tenue.** **Générative** (aucun rythme dans le référentiel).
  **Point tranché : rythme ABSTRAIT** (propriété générique de la notion, « J+7, J+30… »),
  **pas un calendrier daté** — le calendrier concret (ancré sur les dates réelles
  d'introduction) se fait **en aval, dans l'outil séquence** qui combine rythme (12) +
  ordre (4). Cohérent avec le moteur (briques = propriétés génériques ; outils = application
  à une classe). **Dépend dur de 1 ; enrichie par 4 (calibre le rythme) + 2** — la dépendance
  à la 4 vit dans l'outil aval, pas dans la brique. **Seule future raccordée à des outils
  existants** (séquences) ; réserve = **temps long non modélisé** (pas « outil futur »).
  **Frontière 4 (introduction) / 12 (retours).** **Garde rouge sollicitée**, verrouillée par
  le choix « rythme abstrait » (pas d'individualisation → pas de dérive élève).
- **25/06** — **Brique 13 tenue.** **Générative, la plus subjective** (rien d'émotionnel
  dans le référentiel → garder léger, ★★). **Label ABSTRAIT (même résolution que la 12) :**
  produit un label générique « intimidant en général », **indépendant de l'ordre** ; le
  « ne pas placer trop tôt » = application croisée avec l'ordre (4), **en aval**. → **dépend
  dur de 1 ; enrichie par 4** (situe le « trop tôt ») **et 3** (charge), sans en dépendre.
  **Frontière 13 (ressenti) ≠ 3 (effort)** — lourd ≠ intimidant. **Garde rouge MAXIMALE**
  (« intimidant » appelle « pour cet élève » → rester générique). **Réserve double :** outil
  futur + subjectivité → léger.
- **25/06** — **Brique 14 tenue — bloc des futures (11-14) complet.** **Générative, la plus
  théorique** (frontière recherche). **Frontière 14 vs 3 :** 3 = combien d'effort, 14 = quels
  rouages mentaux — deux **grains de la même dimension**, lus du morceau (1) ; ne pas refaire
  la 3. **CORRECTION du mot « approfondit »** (fiche d'origine) : il faisait croire que la 14
  prend la sortie de la 3 en entrée → faux, les mécanismes se lisent **directement du
  morceau**. → **dépend dur de 1 ; lien mutuel avec la 3, sans dépendance** (aligné 12/13).
  **Garde rouge :** propriété de la notion, pas de profilage cognitif de l'élève. **Réserve
  forte : YAGNI** tant que les briques 1-8 ne tournent pas (faisabilité plancher, effort ★★★★★).
  → **Les 12 briques sont écrites (8 cœur + 4 futures). Reste le ménage final.**
- **25/06** — **Ménage final fait — spec close.** (1) Mnémonique uniformisée, ordre **7→6**
  conservé (fiche 4 complétée « · 8 relie aux activités » ; 6/7 inchangées). (2) Mot
  « socle » / « niveau supérieur » retiré de la ligne 24/06 (→ Brique existante / Brique
  future). (3) **Renumérotation 11-14→9-12 abandonnée** (coût des références croisées >
  bénéfice cosmétique) → **ligne d'explication du trou 9/10** ajoutée sous le tableau.
  (4) Note « ligne rouge élève » (coup d'œil) ajoutée sous le tableau. → **TRACKER =
  spécification complète des 12 briques du moteur de granularisation.**
