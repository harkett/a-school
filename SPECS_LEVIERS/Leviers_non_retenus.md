# Leviers non retenus — aSchool

## Comment utiliser ce document
Ce document archive les leviers analysés et écartés, avec leur contenu complet et la raison précise du rejet. L'idée n'est pas jetée — elle est mise en attente. Si le produit évolue (infrastructure données, modèle élève, nouvelle architecture), certains leviers pourront être réexaminés à partir de ce document.

---

## Levier — Cartographie cognitive des classes

### Idée centrale
Modéliser en temps réel la structure cognitive collective d'une classe : ce que les élèves comprennent, ce qu'ils confondent, ce qu'ils n'ont pas assimilé, et comment les notions s'organisent dans leur esprit. Une radiographie pédagogique dynamique, impossible à obtenir avec un chatbot classique.

### Ce que ça peut inclure
- **Modèle mental collectif** — représentation des notions comprises, fragiles ou non acquises.
- **Cartes de confusion** — détection des notions que les élèves mélangent.
- **Nœuds cognitifs critiques** — points d'étranglement qui bloquent la progression.
- **Flux d'apprentissage** — visualisation du chemin réel suivi par la classe dans la compréhension.
- **Clusters d'élèves** — regroupements automatiques par profils cognitifs.
- **Indice de cohérence conceptuelle** — mesure de la logique interne des réponses des élèves.
- **Thermomètre de stabilité cognitive** — mesure de la solidité des acquis.

### Exemple concret
Le professeur ouvre la cartographie cognitive de sa classe et voit :
- Un cluster de 12 élèves qui confondent périmètre et aire.
- Un nœud cognitif rouge sur la notion "proportionnalité", indiquant une incompréhension structurelle.
- Un flux d'apprentissage brisé : les élèves ont compris les fractions mais pas leur lien avec les pourcentages.
- Un indice de cohérence conceptuelle faible sur les exercices de géométrie, révélant des raisonnements instables.
- Trois élèves dont la stabilité cognitive chute depuis deux semaines (risque de décrochage conceptuel).

### Niveau supérieur
- **Comparaison inter-classes** — visualiser les différences cognitives entre deux classes.
- **Projection cognitive** — prédire les futures incompréhensions avant qu'elles n'apparaissent.
- **Simulation pédagogique** — tester virtuellement l'impact d'une séance avant de la faire.
- **Alignement automatique des séquences** — adapter la progression en fonction de la carte cognitive réelle.
- **Détection des dérives conceptuelles** — repérer quand une classe développe une mauvaise représentation mentale.

### Valeur stratégique
aSchool deviendrait le seul outil capable de modéliser la pensée collective d'une classe. Les données générées sont structurelles (modèles, graphes, cohérences, flux), pas conversationnelles. Cette cartographie devient un actif stratégique : plus les classes l'utilisent, plus elle devient précise et impossible à rattraper. Elle transforme aSchool en infrastructure cognitive, pas en assistant.

### Pourquoi non retenu
Pour que la carte existe, il faut des données sur les élèves (réponses, erreurs, comportements). Cela implique que les élèves interagissent avec aSchool — ce qui en fait un outil élève, à l'opposé de la philosophie du produit. Si le prof saisit les données manuellement, la promesse "temps réel" ne tient plus. L'idée est unique et stratégiquement forte, mais elle présuppose un changement de nature du produit : d'un outil de génération à une plateforme de données cognitives.

---

## Levier — Profilage Pédagogique Dynamique (PPD)

### Idée centrale
Créer pour chaque élève un profil cognitif vivant, recalculé en continu, qui modélise non seulement ce qu'il sait, mais comment il apprend, comment il se trompe, comment il hésite, comment il stabilise ses acquis, et comment il transfère ses connaissances. Le PPD n'est pas un diagnostic. C'est une empreinte cognitive évolutive, unique à chaque élève.

### Ce que ça peut inclure
- **Signature cognitive individuelle** — style d'apprentissage propre à l'élève (logique, intuitif, séquentiel, analogique…).
- **Indice d'hésitation** — mesure du doute avant la réponse (temps, reformulations, micro-erreurs).
- **Profil d'erreurs récurrentes** — patterns d'erreurs révélant des incompréhensions structurelles.
- **Courbe de stabilisation des acquis** — vitesse à laquelle une notion devient durable.
- **Sensibilité aux consignes** — capacité à comprendre une consigne du premier coup.
- **Indice de transfert cognitif** — capacité à réutiliser une notion dans un contexte différent.
- **Profil d'attention conceptuelle** — mesure de la concentration sur les éléments clés d'un exercice.
- **Niveau d'autonomie pédagogique** — capacité à avancer sans guidage.
- **Stabilité émotionnelle légère** — détection des moments de surcharge ou de perte de confiance (sans données sensibles).

### Exemple concret
Le professeur ouvre le PPD d'un élève :
- Signature cognitive : raisonnement très logique, faible intuition.
- Indice d'hésitation élevé sur les problèmes de proportionnalité → l'élève doute avant de répondre.
- Profil d'erreurs : confond systématiquement "taux" et "pourcentage".
- Courbe de stabilisation : met 3 à 4 séances pour stabiliser une notion (lent mais durable).
- Sensibilité aux consignes : 2 relectures nécessaires en moyenne.
- Transfert cognitif faible : comprend les fractions mais ne les applique pas en géométrie.
- Autonomie pédagogique : dépend fortement des exemples fournis.
- Stabilité émotionnelle : légère baisse de confiance sur les exercices longs.

### Niveau supérieur
- **PPD prédictif** — anticipation des futures difficultés avant qu'elles n'apparaissent.
- **PPD comparatif** — comparaison entre élèves ayant des signatures cognitives similaires.
- **PPD multi-matières** — détection des compétences transversales (logique, langage, spatial).
- **PPD émotionnel léger** — repérage des moments de surcharge cognitive ou de perte de confiance.
- **PPD adaptatif en temps réel** — modification instantanée des exercices selon l'état cognitif du moment.
- **PPD longitudinal** — évolution du profil sur plusieurs mois ou années.
- **PPD collaboratif** — détection des affinités cognitives entre élèves pour créer des binômes optimaux.

### Valeur stratégique
Le PPD repose sur des métriques invisibles dans une conversation : hésitation, stabilité, transfert, cohérence, patterns d'erreurs. Il transforme aSchool en système d'observation pédagogique, pas en assistant textuel. Les données accumulées deviennent un avantage cumulatif : plus aSchool est utilisé, plus les profils deviennent précis et uniques. C'est un levier défendable, non réplicable, et hautement différenciant — avec une barrière technologique réelle.

### Pourquoi non retenu
Pour calculer tous ces indices (hésitation, stabilisation, transfert, profil d'erreurs), l'élève doit interagir avec aSchool. Le prof devient destinataire final, l'élève devient l'utilisateur réel — contraire à la philosophie du produit. Point supplémentaire : construire un profil cognitif individuel sur des mineurs relève du RGPD, contrainte légale lourde indépendante de la philosophie du produit.

---

## Levier — Générateur de trajectoires d'apprentissage optimales *(vision long terme)*

### Idée centrale
Construire automatiquement pour chaque élève — ou pour une classe entière — une trajectoire d'apprentissage optimale : le bon contenu, au bon moment, avec la bonne difficulté, dans la bonne modalité, selon le bon rythme cognitif, avec les bonnes remédiations et les bons retours en arrière.

Ce n'est pas une "progression".
C'est une navigation intelligente dans l'espace des connaissances, pilotée par les données cognitives réelles.

### Ce que ça peut inclure
- **Chemin conceptuel optimal** — ordre idéal des notions selon le profil cognitif.
- **Points d'ancrage personnalisés** — moments où l'élève doit consolider une notion.
- **Rétro-progression intelligente** — retour automatique sur une notion mal stabilisée.
- **Transitions conceptuelles guidées** — étapes intermédiaires pour éviter les ruptures.
- **Trajectoires différenciées par PPD** — adaptation selon la signature cognitive.
- **Trajectoires multi-modalités** — texte, schémas, manipulations, oral, numérique.
- **Trajectoires de transfert** — apprentissage optimisé pour réutiliser une notion dans un autre contexte.
- **Trajectoires de remédiation ciblée** — correction des erreurs structurelles.

### Exemple concret
Un élève de 5e doit apprendre la proportionnalité. aSchool génère automatiquement une trajectoire sur plusieurs séances :

- **Phase d'intuition** — activité manipulatoire → comprendre intuitivement les rapports.
- **Phase de structuration** — passage au tableau de proportionnalité → formalisation progressive.
- **Phase d'entraînement différencié** — Groupe A : consolidation / Groupe B : standard / Groupe C : approfondissement.
- **Phase de transfert** — application dans : vitesse, échelle, recettes, pourcentages.
- **Phase d'ancrage** — micro-évaluation + correction automatique + stabilisation cognitive.
- **Phase de rétro-progression** — retour ciblé sur les erreurs récurrentes.
- **Phase d'extension** — notions connexes : taux, coefficient, proportion.

### Niveau supérieur
- **Trajectoire prédictive** — anticipation des futures difficultés et ajustement avant qu'elles n'apparaissent.
- **Trajectoire collective** — optimisation pour une classe entière.
- **Trajectoire spiralaire intelligente** — réactivation automatique des notions anciennes au bon moment.
- **Trajectoire inter-disciplinaire** — progression optimisée entre plusieurs matières.
- **Trajectoire adaptative en temps réel** — modification instantanée selon les réponses de l'élève.
- **Trajectoire émotionnelle légère** — adaptation selon la confiance et la fatigue cognitive.

### Valeur stratégique
Un chatbot peut générer un exercice. aSchool génère un parcours complet, optimisé, personnalisé, dynamique et prédictif. Ce levier transforme aSchool en GPS pédagogique, pas en assistant conversationnel. C'est un levier unique, défendable, et massivement différenciant.

### Pourquoi non retenu — et comment le réactiver
Ce levier est la somme de tous les autres. La phrase clé du document original : *"Chaque étape est optimisée selon : la charge cognitive, la cartographie cognitive, le profil PPD, les ambiguïtés détectées, la cohérence curriculaire inter-disciplines."* Ce sont exactement les systèmes déjà analysés — rejetés ou retenus. Ce levier ne peut pas exister seul : c'est une couche d'intégration qui suppose que tous les autres sont déjà construits.

**Lien avec Levier 1 (Générateur d'orchestrations pédagogiques) :** dans sa forme allégée (sans données élèves), ce levier est l'extension naturelle du Levier 1. Le Levier 1 génère une séance unique (55 min). Ce levier génère une trajectoire sur plusieurs séances. Quand le Levier 1 sera implémenté, ajouter un mode "trajectoire multi-séances" sera l'évolution logique. Voir note ajoutée dans Leviers_retenus.md, Levier 1.

---

## Levier — Laboratoire de Simulation de Classe *(vision long terme)*

### Idée centrale
Un environnement de simulation où le professeur peut tester une séquence pédagogique, une discipline ou une méthode sur une classe virtuelle générée par IA (avec des profils d'élèves réalistes, des réactions imprévisibles) avant de la donner en vrai, pour anticiper les problèmes.

### Ce que ça peut inclure
- **Création de "classes virtuelles"** avec des profils réalistes (élèves en difficulté, surdoués, perturbateurs, timides).
- **Simulation des réactions** : "Si vous posez cette question, voici comment 30% de la classe va réagir (baisse d'attention, confusion, débat)."
- **Test de scénarios de gestion de classe** : "Que se passe-t-il si je sanctionne cet élève ? Comment les autres vont-ils réagir ?"
- **Analyse des risques** : "Cette explication risque de créer un malentendu sur le concept X dans 40% des cas."
- **Feedback post-simulation** : "Votre gestion du temps était mauvaise, voici comment optimiser."

### Exemple concret
Un jeune prof doit donner une leçon sur la Révolution française :
- Il simule sa séance avec une classe virtuelle de 25 élèves.
- L'IA lui dit : "Attention, à la minute 12, 5 élèves vont se disperser car le sujet est trop abstrait. Voici une astuce pour les reconnecter."
- Il ajuste sa séance avant de la donner en vrai.
- Il gagne en confiance et évite les échecs en classe réelle.

### Niveau supérieur
- **Banques de scénarios de crise** : "Comment gérer une classe en ébullition ? Testez 10 stratégies."
- **Formation continue** : "Simulez une situation de conflit avec un parent."
- **Benchmarking** : "Comment les autres profs ont-ils géré cette situation ?"

### Valeur stratégique
C'est le seul outil d'"entraînement en sécurité" pour les enseignants. Il permet aux profs — débutants ou expérimentés — de tester, d'échouer et d'apprendre sans risque pour les vrais élèves. C'est un levier de formation et de confiance pédagogique qui n'existe nulle part ailleurs. Particulièrement précieux pour les jeunes enseignants et pour ceux qui gardent le trac malgré l'expérience.

### Pourquoi non retenu — et comment le réactiver

**Problème de nature :** aSchool génère des documents. Ce levier suppose une simulation interactive — le prof interagit avec une classe virtuelle qui répond en temps réel. Ce n'est pas un générateur de documents, c'est une architecture de simulation conversationnelle. Le changement de nature est trop important pour la version actuelle.

**Problème de qualité :** pour que les prédictions soient utiles (*"à la minute 12, 5 élèves se dispersent"*), la simulation doit être crédible. Cette crédibilité repose soit sur des données comportementales réelles (hors scope actuel), soit sur des modèles de recherche en sciences cognitives très fins. Sans ça, les réactions sont trop génériques pour apporter une valeur réelle au-delà de ce que font déjà les Leviers 2 et 3.

**Ce qui est déjà couvert par les leviers retenus :**

| Composant | Couvert par |
|---|---|
| Anticiper les zones de confusion cognitive | Levier 2 — Détection des ambiguïtés |
| Identifier les ruptures et moments inefficaces | Levier 3 — Optimiseur |
| Prédire les malentendus sur une notion | Levier 2 + Infrastructure (graphe universel) |

**Ce qui est genuinement unique et non couvrable aujourd'hui :**
- La simulation comportementale interactive (attention, dispersion, perturbation en temps réel)
- La gestion de classe virtuelle (conséquences d'une sanction sur la dynamique de groupe)
- La formation à la gestion du trac et à la confiance pédagogique
- Les scénarios de crise (conflit avec un élève, avec un parent)

**Comment le réactiver :** ce levier devient pertinent si aSchool évolue vers une architecture de simulation interactive — un deuxième produit complémentaire, distinct du générateur de documents. La base de connaissances pédagogiques (Infrastructure_aSchool.md) constituerait le socle de la simulation. Les leviers retenus (notamment Leviers 1, 2, 3) fourniraient les modèles cognitifs. La couche manquante est le moteur de simulation comportementale.

---
