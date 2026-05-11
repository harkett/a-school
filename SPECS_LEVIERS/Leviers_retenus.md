# Leviers retenus — aSchool

## Comment utiliser ce document
Ce document liste les leviers validés pour l'amélioration d'aSchool, destinés au développeur. Pour chaque levier : idée centrale, contenu détaillé, distinctions importantes, périmètre matières, exemple concret, niveau supérieur et valeur stratégique. Les éléments marqués ⚠️ nécessitent des données élèves et sont hors scope de la version actuelle d'aSchool — ils sont conservés pour une version future.

---

## Levier 1 — Générateur d'orchestrations pédagogiques

### Idée centrale
Créer automatiquement des séquences pédagogiques complètes, cohérentes, optimisées et adaptées à une classe donnée, en orchestrant : les notions, les activités, les niveaux cognitifs, les transitions, les temps forts, les moments de consolidation, les évaluations, les remédiations.

Ce n'est pas un générateur d'exercices.
C'est un chef d'orchestre pédagogique qui compose une séance entière comme une partition.

---

### ⚠️ Distinction critique avec l'outil actuel — important pour le développeur

Ces deux fonctions sont différentes dans leur nature. Ne pas les confondre.

| | aSchool actuel | Ce levier |
|---|---|---|
| Entrée du prof | Un texte collé | Un thème + niveau + durée |
| Sortie | Un exercice avec correction | Une séance complète en 5-6 phases |
| Échelle | La brique (l'exercice) | L'édifice (la séance entière) |
| Usage | Exercice ponctuel | Planification d'une heure de cours complète |

Ces deux fonctions coexistent. Ce levier ne remplace pas l'outil actuel — il l'étend à une échelle supérieure.

---

### Ce que ça peut inclure
- **Architecture de séance intelligente** — structure optimale selon la matière, le niveau et la classe.
- **Transitions pédagogiques automatiques** — passages fluides entre activités pour maintenir l'attention.
- **Rythme cognitif adaptatif** — alternance entre charge forte, charge faible, consolidation.
- **Moments d'ancrage mémoriel** — placement stratégique des activités qui stabilisent les acquis.
- **Séquences différenciées intégrées** — variantes automatiques pour les groupes d'élèves.
- **Points de bascule conceptuelle** — moments où une notion change de statut (intuition → maîtrise).
- **Boucles de rétroaction instantanées** — ajustements automatiques selon les réponses des élèves. *(⚠️ version future — nécessite données élèves)*
- **Orchestration multi-modalités** — texte, schémas, manipulations, oral, numérique.

---

### Périmètre matières
Toutes matières, tous niveaux (6e à Terminale). La structure en phases est un modèle pédagogique universel, non lié à une discipline.

---

### Exemple concret
Un prof de français veut préparer une séance de 55 minutes sur le point de vue narratif en 3e. Il n'a aucun texte sous la main. Il saisit : *"point de vue narratif — français — 3e — 55 min."*

aSchool génère :

- **Phase 1 — Activation (5 min)** : Deux extraits courts (1re personne / 3e personne). Question unique : "Qu'est-ce qui change ?"
- **Phase 2 — Exploration (10 min)** : 6 courts passages à identifier selon le point de vue.
- **Phase 3 — Explicitation (8 min)** : Tableau à compléter (interne / externe / omniscient) avec exemples guidés.
- **Phase 4 — Entraînement différencié (15 min)** : Parcours A → réécrire un passage en changeant le point de vue. Parcours B → analyser l'effet produit sur le lecteur.
- **Phase 5 — Transfert (10 min)** : Extrait d'un roman contemporain → identifier le point de vue et justifier.
- **Phase 6 — Ancrage (7 min)** : Mini-évaluation 5 questions + correction intégrée.

---

### Niveau supérieur
- **Orchestration prédictive** — la séance s'adapte selon les difficultés anticipées sur le thème.
- **Orchestration multi-classes** — générer une progression cohérente pour plusieurs classes d'un même niveau.
- **Orchestration spiralaire** — réintégration automatique des notions anciennes au bon moment.
- **Orchestration émotionnelle légère** — ajustement du rythme selon la confiance et la fatigue cognitive.
- **Orchestration collaborative** — création de binômes optimaux. *(⚠️ version future — nécessite profils élèves)*
- **Orchestration augmentée par données réelles** — intégration des résultats et comportements. *(⚠️ version future — nécessite données élèves)*

---

### Valeur stratégique
Un chatbot peut générer un exercice. aSchool génère une séance complète, cohérente, optimisée, différenciée. L'orchestration repose sur des modèles internes, des graphes de notions et des algorithmes de rythme pédagogique. C'est une couche propriétaire impossible à rattraper sans architecture dédiée. Plus aSchool est utilisé, plus les orchestrations deviennent précises et efficaces. Ce levier transforme aSchool en moteur pédagogique complet, pas en assistant conversationnel.

### Modes d'entrée — note pour le développeur

Le Levier 1 fonctionne avec **trois modes d'entrée distincts**. Le moteur de génération est le même — seule l'interface d'entrée change. Les implémenter comme trois points d'entrée vers un moteur commun.

---

#### Mode 1 — Séance standard
**Entrée :** Thème + matière + niveau + durée
**Usage :** Planification normale, le prof prépare une nouvelle séance
**Exemple :** *"Point de vue narratif — français — 3e — 55 min"*

---

#### Mode 2 — Remédiation contextuelle
**Entrée :** Description libre de la situation réelle de la classe (déclarée par le prof)
**Usage :** Urgence pédagogique — la classe n'a pas compris, le prof cherche un scénario de rattrapage créatif
**Exemple :** *"Ma classe est fatiguée, ils n'ont pas compris la photosynthèse, et ils adorent le jeu vidéo."*

aSchool génère un scénario de remédiation qui utilise les intérêts déclarés comme point d'accroche pédagogique :
*"Scénario : 'La centrale énergétique de votre personnage'. Exercice : Créer une carte de compétence 'Photosynthèse' pour un RPG. Support : Infographie style HUD de jeu vidéo."*

Le prof n'a plus qu'à imprimer et lancer.

Ce que le prof peut déclarer librement :
- L'état de la classe (*"fatiguée", "démotivée", "en difficulté avec l'abstraction"*)
- La notion bloquante (*"n'ont pas compris les fractions"*)
- Les centres d'intérêt (*"adorent le foot, les jeux vidéo, la musique"*)
- Le contexte local (*"il y a eu un match hier", "c'est la semaine des sciences"*)

**⚠️ Ce qui est hors scope :** profils psychologiques déduits automatiquement des interactions passées, mémorisation de ce qui a fonctionné par classe — nécessitent des données élèves.

---

#### Mode 3 — Trajectoire multi-séances *(extension future)*
**Entrée :** Thème + niveau + nombre de séances
**Usage :** Planification d'un chapitre entier sur plusieurs semaines
Documenté en détail dans Leviers_non_retenus.md sous "Générateur de trajectoires d'apprentissage optimales".

---

## Levier 2 — Détection automatique des zones d'ambiguïté cognitive

### Idée centrale
Identifier automatiquement les endroits où les élèves risquent de mal comprendre, d'interpréter de travers, de confondre deux notions, ou de construire une représentation mentale erronée.

Ce levier ne détecte pas les erreurs.
Il détecte les risques d'erreur avant qu'elles n'apparaissent.
C'est un radar cognitif.

---

### Ce que ça peut inclure
- **Analyse des formulations ambiguës** — repérage des phrases, consignes ou énoncés pouvant être interprétés de plusieurs façons.
- **Détection des confusions conceptuelles** — identification des notions proches que les élèves mélangent souvent.
- **Points de rupture cognitive** — moments où la compréhension bascule dans l'erreur.
- **Ambiguïtés liées au vocabulaire scolaire** — mots polysémiques (ex : "figure", "valeur", "produit", "tirer").
- **Ambiguïtés structurelles dans les exercices** — pièges involontaires dans la mise en page ou la logique.
- **Ambiguïtés de raisonnement** — étapes implicites que les élèves interprètent mal.
- **Ambiguïtés de transfert** — quand une notion change de contexte et perd son sens pour l'élève.
- **Analyse des micro-indices d'incompréhension** — hésitations, reformulations, réponses incohérentes. *(⚠️ version future — nécessite données élèves)*

---

### Périmètre matières
Toutes matières, tous niveaux (6e à Terminale). Particulièrement impactant en mathématiques et sciences exactes, où la précision du vocabulaire est critique.

---

### Exemple concret
Le prof de maths prépare un exercice sur les probabilités en 4e. Il colle l'énoncé suivant dans aSchool :

*"Un sac contient 3 billes rouges et 2 billes bleues. Quelle est la probabilité de tirer une bille rouge ?"*

aSchool détecte automatiquement 3 zones d'ambiguïté :

1. **"Tirer"** — sens courant : arracher, saisir avec effort. Sens mathématique : prélever aléatoirement. 30 à 40 % des élèves de 4e n'ont pas encore automatisé ce sens technique.
2. **Conditions implicites** — ni le caractère aléatoire du tirage, ni le fait que les billes soient identiques au toucher, ni que le sac soit opaque ne sont précisés. Évidents pour le prof, invisibles pour l'élève.
3. **Espace des possibles non ancré** — l'élève peut répondre "3 sur 5" sans jamais construire la représentation des 5 issues également probables.

aSchool propose la version corrigée, modifications en surbrillance :

*"Un sac **opaque** contient 3 billes rouges et 2 billes bleues, **identiques au toucher**. On prélève **une bille au hasard sans regarder**. Quelle est la probabilité **d'obtenir** une bille rouge ?"*

Le prof voit chaque modification en surbrillance et comprend immédiatement pourquoi chaque mot a changé.

---

### Niveau supérieur
- **Ambiguïté inter-disciplinaire** — repérage des notions qui changent de sens selon la matière ("produit" en maths ≠ "produit" en SVT).
- **Ambiguïté de progression** — détection des moments où une notion est introduite trop tôt ou trop tard.
- **Ambiguïté invisible** — ambiguïtés que même les enseignants ne voient pas, révélées par les modèles cognitifs.
- **Ambiguïté émotionnelle légère** — repérage des formulations anxiogènes ou démotivantes.
- **Ambiguïté prédictive** — anticipation des ambiguïtés selon les profils cognitifs. *(⚠️ version future — nécessite données élèves)*
- **Ambiguïté collective** — détection des zones où toute la classe risque de diverger. *(⚠️ version future — nécessite données élèves)*

---

### Valeur stratégique
Un chatbot répond. aSchool analyse, prédit, corrige et sécurise la compréhension avant même que les élèves ne se trompent. La détection d'ambiguïtés repose sur des graphes conceptuels, des modèles cognitifs et des patterns d'erreurs historiques — une couche propriétaire qui s'améliore avec le temps. Elle crée une barrière technologique : les concurrents ne peuvent pas rattraper des années d'ambiguïtés détectées, classées, modélisées. Elle transforme aSchool en système de prévention pédagogique, pas en assistant conversationnel.

---

## Levier 3 — Optimiseur de séquences pédagogiques
*(Priorité haute — voir note de positionnement ci-dessous)*

### Idée centrale
Analyser, améliorer et réécrire automatiquement n'importe quelle séquence pédagogique existante pour la rendre plus cohérente, plus fluide, plus efficace cognitivement, plus progressive et mieux alignée avec les programmes.

Ce n'est pas un générateur de séquences.
C'est un optimiseur — un "compresseur-améliorateur" pédagogique qui transforme une séquence brute en séquence améliorée.

---

### ⚠️ Distinction critique avec le Levier 1 (Générateur d'orchestrations) — important pour le développeur

Ces deux leviers sont complémentaires, pas redondants. Ils couvrent deux besoins distincts.

| | Levier 1 — Générateur d'orchestrations | Levier 3 — Optimiseur |
|---|---|---|
| Situation de départ | Le prof n'a rien | Le prof a déjà une séquence |
| Entrée | Thème + niveau + durée | Une séquence existante (saisie ou collée) |
| Sortie | Séquence générée from scratch | Séquence existante améliorée |
| Usage | Préparer une nouvelle séance | Améliorer ce qu'on a déjà |

**Note de positionnement pour le développeur :** ce levier mérite d'être traité en priorité haute. Chaque prof a des années de séquences existantes qu'il réutilise. La capacité à coller n'importe quelle séquence et recevoir une version améliorée est la fonctionnalité à plus fort impact immédiat — sans changer le comportement du prof, juste en ajoutant une étape de validation. C'est aussi le point de convergence naturel des autres leviers retenus : l'optimiseur applique la détection d'ambiguïtés (Levier 2) et la cohérence curriculaire (Levier 4) à une séquence complète.

---

### Ce que ça peut inclure
- **Analyse de cohérence interne** — vérifie la logique, la progression, les transitions.
- **Optimisation de la charge cognitive** — ajuste la difficulté et le rythme.
- **Réécriture des consignes** — clarifie les formulations ambiguës.
- **Rééquilibrage des activités** — évite les séquences trop lourdes ou trop légères.
- **Détection des ruptures conceptuelles** — repère les sauts logiques trop brusques.
- **Alignement curriculaire automatique** — vérifie la conformité au programme et aux autres matières.
- **Optimisation des transitions pédagogiques** — fluidifie le passage d'une activité à l'autre.
- **Insertion d'ancrages mémoriels** — ajoute des moments de consolidation manquants.
- **Détection des activités inefficaces** — repère les exercices qui n'apportent rien à l'objectif.
- **Intégration de différenciation automatique** — propose des variantes selon les niveaux. *(⚠️ version future — nécessite profils élèves pour différenciation PPD)*

---

### Périmètre matières
Toutes matières, tous niveaux (6e à Terminale).

---

### Exemple concret
Le professeur soumet une séquence de 50 minutes sur les angles complémentaires et supplémentaires.

L'optimiseur détecte :
- **Rupture conceptuelle** : introduction trop rapide des angles supplémentaires sans consolider les complémentaires.
- **Surcharge cognitive** : 3 définitions + 2 propriétés dans les 10 premières minutes.
- **Consigne ambiguë** : "trace un angle de 40° adjacent" → risque d'interprétation multiple.
- **Activité inefficace** : un exercice de reproduction géométrique sans lien avec l'objectif.
- **Manque d'ancrage** : aucune consolidation avant l'exercice final.
- **Progression déséquilibrée** : 35 minutes d'exercices, 5 minutes de correction.

aSchool génère automatiquement la séquence optimisée :
- **Activation (5 min)** — rappel des angles droits, repère cognitif.
- **Découverte guidée (10 min)** — angles complémentaires, exemples concrets.
- **Structuration (10 min)** — formalisation + premiers angles supplémentaires.
- **Entraînement différencié (15 min)** — exercices progressifs par niveau.
- **Ancrage + mini-évaluation (10 min)** — consolidation et correction immédiate.

Avec : consignes clarifiées, activités pertinentes, transitions fluides, charge cognitive équilibrée.

---

### Niveau supérieur
- **Optimisation prédictive** — améliore la séquence avant même qu'elle ne soit utilisée.
- **Optimisation inter-disciplinaire** — harmonise la séquence avec les autres matières.
- **Optimisation spiralaire** — réintègre automatiquement les notions anciennes au bon moment.
- **Optimisation cognitive profonde** — ajuste selon les mécanismes mentaux requis.
- **Optimisation émotionnelle légère** — évite les moments anxiogènes ou démotivants.
- **Optimisation en temps réel** — ajuste la séquence selon les réactions des élèves. *(⚠️ version future — nécessite données élèves)*

---

### Valeur stratégique
Un chatbot génère une séquence. aSchool analyse, corrige, optimise et perfectionne une séquence existante. L'optimisation s'appuie sur l'index pédagogique universel (infrastructure), les ambiguïtés conceptuelles, la cohérence curriculaire et les erreurs typiques — une couche propriétaire qui s'améliore avec l'usage. Ce levier transforme aSchool en moteur d'ingénierie pédagogique, pas en assistant conversationnel. C'est un levier unique, défendable, et massivement différenciant.

---

## Levier 4 — Moteur de cohérence curriculaire inter-disciplines

### Idée centrale
Créer un moteur capable d'aligner automatiquement les notions, compétences, démarches et progressions entre toutes les disciplines scolaires. Assurer que ce qui est enseigné en Mathématiques, Français, Histoire, SVT, Physique, Technologie, etc., reste cohérent, synchronisé et conceptuellement compatible.

Ce n'est pas un tableau de correspondances.
C'est un système de cohérence curriculaire vivant, qui détecte les contradictions, les décalages, les doublons, les ruptures logiques et les opportunités de synergie.

---

### ⚠️ Deux versions — important pour le développeur

Ce levier fonctionne selon deux niveaux d'activation. Les documenter clairement aux profs est indispensable.

| | Version immédiate | Version enrichie |
|---|---|---|
| Source des données | Programmes officiels de l'Éducation nationale (fixes, publics) | Activités partagées par les profs + saisie manuelle du planning dans les paramètres |
| Action requise du prof | Aucune — fonctionne automatiquement | Saisie initiale du planning dans les réglages + activation du partage |
| Précision | Bonne (théorique) | Très précise (réelle) |
| Disponibilité | Immédiate dès l'installation | Croît avec l'usage et les contributions |

**Note développeur :** prévoir dans les paramètres utilisateur un module de gestion du planning réel par matière. Le prof (ou l'établissement) peut y renseigner l'avancement réel de chaque matière. Sans ce module, seule la version immédiate est active.

---

### Ce que ça peut inclure
- **Graphe curriculaire global** — représentation de toutes les notions du programme, reliées entre elles.
- **Alignement inter-disciplines** — détection des notions communes (ex : proportionnalité ↔ vitesse ↔ échelle).
- **Détection des contradictions pédagogiques** — repérage des incohérences entre matières.
- **Synchronisation temporelle** — alignement des progressions pour éviter les décalages (ex : utiliser les pourcentages en SVT avant de les avoir vus en Maths).
- **Opportunités de renforcement croisé** — suggestions d'activités qui renforcent plusieurs matières simultanément.
- **Détection des doublons curriculaires** — éviter que deux matières enseignent la même notion sans coordination.
- **Analyse des ruptures conceptuelles** — repérage des moments où une notion change de sens selon la discipline.
- **Cohérence lexicale inter-disciplines** — harmonisation du vocabulaire utilisé dans plusieurs matières.

---

### Périmètre matières
Toutes matières, tous niveaux (6e à Terminale). C'est l'essence même de ce levier : connecter toutes les disciplines entre elles.

---

### Exemple concret
Un prof de français en 3e prépare une séance sur le texte argumentatif.

aSchool détecte (sur la base des programmes officiels) :

- En **EMC** : un débat sur les droits fondamentaux est prévu → alignement parfait, opportunité de co-activité.
- En **Histoire** : la Seconde Guerre mondiale est en cours → les discours de propagande sont un support argumentatif naturel et disponible immédiatement.
- En **Français** lui-même : la lecture d'une œuvre de Zola est prévue au trimestre → "J'accuse" comme texte source possible pour l'argumentation.

aSchool génère automatiquement une séance qui exploite ces trois connexions, sans que le prof ait cherché lui-même les liens.

---

### Niveau supérieur
- **Cohérence curriculaire prédictive** — anticipation des futurs décalages entre matières.
- **Cohérence curriculaire dynamique** — mise à jour automatique à chaque nouvelle séance générée.
- **Cohérence curriculaire inter-cycles** — continuité entre CM2 → 6e → 5e → 4e → 3e → lycée.
- **Cohérence curriculaire émotionnelle légère** — éviter les séquences trop lourdes simultanément dans plusieurs matières.
- **Cohérence curriculaire personnalisée par classe** — adaptation selon les progressions réelles. *(⚠️ version future — nécessite module paramètres enrichi)*
- **Cohérence curriculaire augmentée par données cognitives** — alignement basé sur cartographie cognitive et PPD. *(⚠️ version future — nécessite données élèves)*

---

### Valeur stratégique
Un chatbot peut générer un exercice. aSchool garantit que toute la progression de l'élève est cohérente entre les matières. Le moteur repose sur des graphes curriculaires, des modèles conceptuels et des liens interdisciplinaires — une couche propriétaire impossible à rattraper sans architecture dédiée. Plus aSchool est utilisé et alimenté, plus la cohérence devient fine, précise, transversale. Ce levier transforme aSchool en système d'ingénierie curriculaire, pas en assistant conversationnel. C'est un levier unique, défendable, et inaccessible aux IA classiques.

---

## Levier 5 — Analyseur de qualité didactique des consignes

### Idée centrale
Analyser automatiquement la qualité didactique d'une consigne : sa clarté, sa précision, son niveau cognitif, son risque d'ambiguïté, sa charge mentale, sa cohérence avec l'objectif pédagogique et sa robustesse face aux erreurs typiques.

Ce n'est pas une vérification grammaticale.
C'est une analyse didactique profonde, impossible à réaliser par un chatbot.

---

### ⚠️ Distinction avec les leviers existants — important pour le développeur

Ce levier est chirurgical : il s'applique à une seule consigne, pas à une séquence entière.

| | Levier 2 — Ambiguïtés | Levier 3 — Optimiseur | Levier 5 — Analyseur de consignes |
|---|---|---|---|
| Objet analysé | Un exercice entier | Une séquence complète | Une seule consigne |
| Focus | Zones de risque cognitif | La séquence dans sa globalité | Qualité didactique de l'instruction elle-même |
| Usage typique | Avant de distribuer un exercice | Avant de préparer une heure de cours | Avant d'écrire une question d'examen ou de devoir |

---

### Ce que ça peut inclure
- **Analyse de clarté linguistique** — repère les formulations floues, vagues ou trop longues.
- **Analyse de précision didactique** — vérifie que la consigne dit exactement ce qu'elle doit dire.
- **Détection d'ambiguïtés conceptuelles** — identifie les mots à double sens ("simplifier", "réduire", "produit").
- **Analyse de cohérence avec l'objectif** — vérifie que la consigne correspond à ce que l'enseignant veut évaluer.
- **Analyse de structure logique** — repère les étapes implicites ou les sauts logiques.
- **Analyse de risque d'erreurs typiques** — détecte les formulations qui provoquent des erreurs récurrentes.
- **Analyse de charge cognitive** — mesure l'effort mental imposé par la consigne.
- **Analyse de compatibilité PPD** — adapte la consigne aux profils cognitifs. *(⚠️ version future — nécessite données élèves)*

---

### Périmètre matières
Toutes matières, tous niveaux. Particulièrement impactant en mathématiques, sciences et langues où la précision des consignes est critique.

---

### Exemple concret
Consigne initiale soumise par le prof :
*"Trace un triangle isocèle de base 6 cm et calcule son aire."*

L'analyseur détecte :
- **Ambiguïté** : "trace un triangle isocèle" → lequel ? sommet en haut ? base horizontale ?
- **Étape implicite** : pour calculer l'aire, il faut connaître la hauteur → non mentionnée.
- **Risque d'erreur typique** : confondre hauteur et côté égal.
- **Charge cognitive excessive** : deux tâches en une (construction + calcul).
- **Incohérence didactique** : objectif flou — géométrie ? mesure ? aire ? construction ?

aSchool propose la version optimisée :
1. Trace un triangle isocèle dont la base mesure 6 cm.
2. Trace la hauteur issue du sommet principal.
3. Mesure cette hauteur.
4. Calcule l'aire du triangle.

La consigne devient claire, progressive, non ambiguë, didactiquement cohérente.

---

### Niveau supérieur
- **Consigne prédictive** — anticipe les ambiguïtés avant qu'elles ne soient écrites.
- **Consigne multi-modalités** — propose texte, schéma, oral, manipulation selon le profil de la classe.
- **Consigne spiralaire** — réactive une notion ancienne dans la consigne.
- **Consigne inter-disciplinaire** — harmonise la consigne avec les autres matières.
- **Consigne adaptative** — reformule selon le profil PPD. *(⚠️ version future — nécessite données élèves)*
- **Consigne émotionnelle légère** — évite les formulations anxiogènes. *(⚠️ version future)*

---

### Valeur stratégique
Un chatbot reformule une phrase. aSchool analyse la consigne comme un expert didacticien, en tenant compte de la charge cognitive, des ambiguïtés, des erreurs typiques, de la cohérence curriculaire et des objectifs pédagogiques. C'est une couche propriétaire qui s'améliore avec l'usage. Ce levier transforme aSchool en système d'ingénierie didactique, pas en assistant conversationnel.

---

## Levier 6 — Détecteur d'équité pédagogique

### Idée centrale
Analyser automatiquement n'importe quelle évaluation — générée par aSchool ou créée par l'enseignant — pour détecter les biais qui faussent les résultats ou rendent l'évaluation non fiable.

*"aSchool corrige l'évaluation elle-même, pas la copie."*

Ce levier transforme aSchool en garant de l'équité pédagogique.

---

### ⚠️ Périmètre retenu — important pour le développeur

Ce levier ne retient que les 3 composants genuinement uniques. Les autres biais (linguistique, cognitif, d'ambiguïté) sont déjà couverts par les Leviers 2, 3 et 5. Ne pas dupliquer.

| Composant | Statut |
|---|---|
| Biais linguistique | ❌ Couvert par Levier 2 + Levier 5 |
| Biais d'ambiguïté | ❌ Couvert par Levier 2 |
| Biais cognitif (surcharge) | ❌ Couvert par Levier 3 + Levier 5 |
| Biais PPD | ❌ Hors scope — nécessite données élèves |
| **Biais de contenu** | ✅ Retenu — unique |
| **Biais de difficulté** | ✅ Retenu — unique |
| **Biais émotionnel léger** | ✅ Retenu — unique |

---

### Les 3 composants retenus

**1. Biais de contenu**
L'évaluation ne mesure pas ce qu'elle prétend mesurer. C'est le composant le plus différenciant — personne ne le détecte automatiquement.
Exemples : exercice de proportionnalité qui évalue en réalité la lecture de graphique / exercice de géométrie qui évalue la précision du dessin / exercice de français qui évalue la culture générale.

**2. Biais de difficulté**
L'évaluation est mal calibrée par rapport au niveau réel de la classe.
Exemples : exercice d'un niveau supérieur glissé dans une évaluation / question trop simple qui ne discrimine pas les compétences.

**3. Biais émotionnel léger**
Certaines formulations augmentent le stress ou la démotivation avant même que l'élève commence.
Exemples : "attention, piège !", "réponds vite", "tu dois absolument réussir", annonce anxiogène des pénalités.

---

### Périmètre matières
Toutes matières, tous niveaux (6e à Terminale).

---

### Exemple concret
Un prof de géographie en 4e soumet une évaluation sur les grands fleuves européens.

aSchool détecte :

- **Biais de contenu** : Question *"Décris le trajet du Rhin en utilisant un vocabulaire géographique précis."* → L'objectif déclaré est géographique, mais la question évalue en réalité la maîtrise rédactionnelle. Un élève qui connaît parfaitement la géographie mais écrit difficilement sera injustement pénalisé.

- **Biais de difficulté** : Dernière question sur *"le bassin versant du Danube et son importance économique"* → notion typiquement introduite en 3e, un niveau au-dessus de la classe évaluée.

- **Biais émotionnel** : En-tête de l'évaluation *"Chaque faute enlève un demi-point"* → focalise l'élève sur la peur de l'erreur avant même la première lecture.

aSchool génère une version corrigée avec les 3 biais neutralisés.

---

### Niveau supérieur
- **Biais prédictifs** — anticipe les biais avant que l'évaluation soit finalisée.
- **Biais spiralaires** — notions oubliées qui auraient dû être réactivées avant l'évaluation.
- **Biais inter-disciplinaires** — contradictions entre matières dans les attendus.

---

### Valeur stratégique
Un chatbot corrige une copie. aSchool corrige l'évaluation elle-même. Ce levier repose sur l'index des erreurs typiques, les graphes conceptuels et les niveaux de granularité des notions — une couche propriétaire impossible à rattraper. Il transforme aSchool en système d'équité pédagogique, pas en assistant conversationnel. C'est un levier massivement différenciant, défendable, et inaccessible aux IA classiques.

---
