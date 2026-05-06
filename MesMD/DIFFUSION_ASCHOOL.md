# Plan de diffusion — A-SCHOOL (school.afia.fr)

> **Rôle : référence de la stratégie de communication — personas, messages, canaux, leviers viraux, métriques.**
>
> ⚠ Ce document est complémentaire de `PLAN_LANCEMENT_ASCHOOL.md`. La frontière est la suivante :
> - **Ce document** = qui on cible, quoi dire, comment le dire (stratégie et positionnement)
> - **`PLAN_LANCEMENT_ASCHOOL.md`** = ce qu'on fait, quand, et comment mesurer le succès (plan d'action daté)
>
> Ce document contient :
> - **Description fonctionnelle exacte** de l'outil : ce qu'il fait vraiment, matières couvertes avec leurs types d'activités, toutes les fonctionnalités accessibles (génération, saisie, export, historique, compte, feedback)
> - **Ce que l'outil N'est PAS** : pas un chatbot, pas un outil de création de cours, pas pour les élèves, pas un ENT
> - **Positionnement** : pitch en une phrase + pitch étendu
> - **3 personas cibles réels** : Prof de français collège (persona pilote), Prof HG lycée, Prof polyvalent REP+ — avec leur profil et leur levier d'entrée
> - **5 messages clés** : gain de temps, spécificité métier, directement utilisable, données privées, produit qui s'améliore — avec l'ancrage produit et la cible pour chacun
> - **6 leviers viraux intégrés au logiciel** : fichier Word partagé, mailto intégré, historique Mes activités, feedback ambassadeur, spécialisation matière, impression en classe — avec mécanisme, action recommandée, impact attendu
> - **Ce qu'il faut supprimer du discours** : tableau des formulations à éviter avec pourquoi et ce qu'il faut dire à la place
> - **Plan de communication par canal** : 6 canaux détaillés (bouche-à-oreille, Facebook avec format de post, LinkedIn, email onboarding J+0/J+2/J+7/J+14, associations, SEO)
> - **Calendrier de lancement** : Phase 0 (avril), Phase 1 (mai), Phase 2 (juin), Phase 3 (août-septembre)
> - **Métriques de succès** : 5 métriques avec outil de mesure et objectifs mai 2026 / rentrée 2026
> - **Messages clés par canal** : tableau récapitulatif (Facebook, LinkedIn, email, bouche-à-oreille, Word/impression, association)
>
> **À consulter quand** : on prépare un post, un email, une présentation, ou qu'on veut retrouver le bon message pour un contexte donné.
>
> **Vérifié le : 30/04/2026 — État : mis à jour (12 matières, few-shot, dictée vocale, OCR)**

---

## Sommaire

1. [Ce que fait vraiment l'outil](#1-ce-que-fait-vraiment-loutil)
2. [Positionnement affiné](#2-positionnement-affiné)
3. [Messages clés](#3-messages-clés)
4. [Personas cibles réels](#4-personas-cibles-réels)
5. [Leviers viraux intégrés au logiciel](#5-leviers-viraux-intégrés-au-logiciel)
6. [Ce qu'il faut supprimer du discours](#6-ce-quil-faut-supprimer-du-discours)
7. [Plan de communication par canal](#7-plan-de-communication-par-canal)
8. [Calendrier de lancement](#8-calendrier-de-lancement)
9. [Métriques de succès](#9-métriques-de-succès)
10. [Messages clés par canal](#10-messages-clés-par-canal)

---

## 1. Ce que fait vraiment l'outil

### Description fonctionnelle exacte

A-SCHOOL est une **application web** qui génère automatiquement des **activités pédagogiques prêtes à l'emploi** à partir d'un texte fourni par l'enseignant, en s'appuyant sur un LLM (Groq / LLaMA 3.3).

L'enseignant colle un extrait de texte (roman, document historique, article), choisit le type d'exercice, le niveau de classe et obtient en moins de 10 secondes une activité complète qu'il peut télécharger, imprimer ou envoyer par e-mail.

### Matières couvertes (avril 2026)

| Matière | Types d'activités |
|---|---|
| **Français** | 15 types — Questions de compréhension, réécriture, analyse de texte, production d'écrit, grammaire, orthographe, évaluation... |
| **Histoire-Géographie** | 12 types — Analyse de source, frise chronologique, composition, croquis, document iconographique, oral, dissertation... |
| **Mathématiques** | Exercices, problèmes, démonstrations... |
| **Physique-Chimie** | Exercices, TP, analyse de résultats... |
| **SVT** | Exercices, étude de documents, comptes-rendus... |
| **SES** | Analyse de données, dissertation, étude de cas... |
| **NSI** | Exercices algorithmiques, projets, fiches... |
| **Philosophie** | Dissertation, explication de texte, questions... |
| **Langues Vivantes** | Compréhension, expression, traduction... |
| **Technologie** | Fiches, projets, évaluations... |
| **Arts** | Analyse d'œuvre, fiches, projets... |
| **EPS** | Fiches, évaluations, projets... |

**Total : 43 types d'activités répartis sur 12 matières** — chacun avec 3 à 9 sous-types.

### Fonctionnalités réelles (livrées et accessibles)

#### Génération d'activités
- **43 types d'activités** sur 12 matières, chacun avec 3 à 9 sous-types
- **Niveaux** : 6e, 5e, 4e, 3e, 2nde, 1re, Terminale, Supérieur
- **Option correction** : génère la correction en même temps que l'exercice
- **Résultat en 5 à 10 secondes**
- **Adaptation au style du prof** : à partir de 3 activités du même type, A-SCHOOL imite le style sans ré-entraînement (few-shot)

#### Saisie du texte source
- Saisie directe (copier-coller)
- Import fichier `.txt`
- **Dictée vocale** (Groq Whisper API) — opérationnel
- **OCR image JPG/PNG** — lecture de scans de manuels ou photocopies — opérationnel

#### Export et usage immédiat
- Téléchargement en `.txt` (texte brut)
- Téléchargement en `.docx` (Word — prêt à modifier)
- Impression directe depuis le navigateur
- Envoi par e-mail via le client mail du prof (`mailto:`)

#### Historique personnel
- Toutes les activités générées sont sauvegardées automatiquement
- Accessible depuis "Mes activités"
- Chargeable en un clic pour régénérer ou modifier les paramètres

#### Compte sécurisé
- Inscription par e-mail + vérification
- Connexion sécurisée (JWT, tokens httpOnly, renouvellement automatique)
- Les données d'un prof restent privées

#### Feedback intégré
- Formulaire en sidebar : catégorie (Problème / Suggestion / Question) + message
- Notation : 1 à 5 étoiles + commentaire optionnel
- Envoyé directement à l'équipe

---

## 2. Positionnement affiné

### Ce que l'outil N'est PAS
- Ce n'est **pas** un chatbot généraliste (pas de conversation libre)
- Ce n'est **pas** un outil pour créer des cours (pas de progression pédagogique auto)
- Ce n'est **pas** un outil pour les élèves
- Ce n'est **pas** une plateforme type ENT (pas de gestion de classes, de notes, d'élèves)

### Ce que l'outil EST vraiment

> **A-SCHOOL est un générateur d'exercices et d'évaluations pour les enseignants du secondaire français — collège, lycée, toutes matières.**

Il transforme un texte en une activité pédagogique structurée, calibrée pour le bon niveau, en quelques secondes.

### Positionnement en une phrase

> "Vous avez le texte. A-SCHOOL fait l'exercice."

### Positionnement étendu

> A-SCHOOL est fait pour les profs qui passent des heures chaque semaine à concevoir des exercices à partir de documents. Collez un extrait, choisissez le type d'activité et le niveau — vous avez votre exercice en 10 secondes, prêt à imprimer ou à distribuer en Word.

---

## 3. Messages clés

### Message #1 — Gain de temps immédiat et mesurable
> "Ce qui prenait 45 minutes prend maintenant 10 secondes."

**Ancrage produit** : génération en < 10 sec, export direct, pas de mise en forme à faire.
**Pour qui** : tous les profs, surtout ceux qui manquent de temps de préparation.

---

### Message #2 — Spécifique à leur métier (pas un outil générique)
> "Fait pour les profs. Pas pour tout le monde."

**Ancrage produit** : 43 types d'activités calés sur les programmes français (brevet, bac, compétences collège), 12 matières.
**Pour qui** : profs qui ont essayé ChatGPT et trouvé ça trop générique, pas calibré.

---

### Message #3 — Directement utilisable en classe
> "Téléchargez en Word. Imprimez. Distribuez. C'est tout."

**Ancrage produit** : export `.docx`, bouton impression, `mailto:` intégré.
**Pour qui** : profs qui veulent un résultat sans reformatage.

---

### Message #4 — Votre travail reste le vôtre
> "Vos textes, vos activités, votre compte. Rien n'est partagé."

**Ancrage produit** : compte individuel, JWT sécurisé, historique privé.
**Pour qui** : profs méfiants vis-à-vis de la confidentialité de leurs ressources.

---

### Message #5 — Le produit s'améliore avec vous
> "Vous signalez ce qui ne va pas. On corrige."

**Ancrage produit** : bouton feedback intégré dans la sidebar, note + message + catégorie.
**Pour qui** : early adopters qui veulent avoir un impact sur l'outil.

---

## 4. Personas cibles réels

### Persona A — Prof de français collège (persona pilote)
- Enseigne en 4e ou 5e
- Prépare 4 à 6 séances par semaine
- Utilise des extraits de romans au programme (Zola, Maupassant, Molière...)
- Passe 1 à 2h sur les exercices de compréhension et de réécriture
- Familiarisé avec Word, parfois Teams ou Pronote
- **Levier d'entrée** : "Donne-moi ton extrait. Voilà les questions de compréhension."

### Persona B — Prof d'histoire-géographie lycée
- Prépare des fiches de révision, des exercices sur documents, des dissertations
- Travaille souvent avec des cartes, des documents iconographiques
- Prépare ses élèves au Grand Oral et au bac
- **Levier d'entrée** : "Analyse de source automatique pour mes terminales."

### Persona C — Prof polyvalent (collège REP+)
- Enseigne plusieurs matières dans le même établissement
- Surcharge de travail structurelle
- Moins de ressources internes
- **Levier d'entrée** : "Je gagne du temps sur plusieurs matières en même temps."

---

## 5. Leviers viraux intégrés au logiciel

Ces leviers existent **déjà dans le produit** ou sont à portée immédiate.

### Levier 1 — Le fichier Word partagé (viral passif, déjà actif)
**Mécanisme** : Le prof télécharge un `.docx`, le distribue à ses élèves ou l'envoie à un collègue. Le fichier circule sans que le prof ait besoin de "parler" de l'outil.
**Action produit recommandée** : Ajouter un pied de page discret dans le `.docx` généré : *"Activité générée avec A-SCHOOL — school.afia.fr"*
**Impact attendu** : Chaque fichier distribué est une impression potentielle sur 25 à 30 élèves et les parents qui voient les cours.

---

### Levier 2 — Le mailto intégré (viral actif, déjà actif)
**Mécanisme** : Le bouton "Envoyer par e-mail" ouvre le client mail du prof avec l'activité en corps du message. Si le prof envoie à un collègue, le collègue voit l'activité et peut demander comment elle a été générée.
**Action produit recommandée** : Ajouter une signature en bas du corps du mail : *"Généré avec A-SCHOOL — school.afia.fr — Créez votre compte gratuit"*
**Impact attendu** : chaque mail envoyé devient un vecteur d'acquisition.

---

### Levier 3 — L'historique "Mes activités" (rétention + bouche-à-oreille)
**Mécanisme** : Le prof retrouve toutes ses activités en un clic. Cela crée une dépendance positive et un "capital de travail" dans la plateforme.
**Action produit recommandée** : Ajouter un compteur "X activités créées" visible sur la page. Les gens aiment voir leur propre production.
**Impact attendu** : rétention longue durée + fierté à montrer ("regarde, j'en ai fait 47").

---

### Levier 4 — Le feedback intégré (signal produit + lien émotionnel)
**Mécanisme** : Le formulaire de feedback crée un lien direct entre le prof et l'équipe. Quand on répond à un feedback, le prof devient ambassadeur.
**Action produit recommandée** : Répondre à chaque feedback dans les 48h. Même une ligne suffit.
**Impact attendu** : 2 à 3 profs transformés en ambassadeurs actifs par mois.

---

### Levier 5 — La spécialisation matière (différenciation virale)
**Mécanisme** : Un outil générique (ChatGPT) ne peut pas dire "je suis fait pour toi". A-SCHOOL si. Quand un prof montre l'outil à un collègue, la précision des activités (calibrées brevet, bac, compétences BO) est immédiatement visible.
**Action produit recommandée** : Sur la page d'accueil, afficher visuellement les matières avec des exemples concrets d'activités générées.
**Impact attendu** : la spécialisation est le premier argument de bouche-à-oreille entre profs.

---

### Levier 6 — L'impression en classe (exposition physique)
**Mécanisme** : Le prof imprime l'activité et la distribue. Si "A-SCHOOL" apparaît en pied de page, d'autres profs qui voient la feuille peuvent demander d'où ça vient.
**Action produit recommandée** : Ajouter automatiquement un pied de page sur toutes les impressions : *"Généré avec A-SCHOOL — school.afia.fr"* — visible sur la feuille papier, invisible à l'écran.
**Impact attendu** : visibilité dans les salles des profs, les photocopieuses, les couloirs.

---

## 6. Ce qu'il faut supprimer du discours

Ces éléments créent des attentes non satisfaites ou affaiblissent la proposition de valeur.

| À supprimer | Pourquoi | À remplacer par |
|---|---|---|
| "Outil IA pour tous les enseignants" | Terme flou | "Pour les profs du secondaire — toutes matières" |
| "Intelligence artificielle" | Méfiance des profs | "Génération automatique", "en 10 secondes" |
| "Révolution de l'enseignement" | Trop vague, pas crédible | Parler du gain de temps concret et mesurable |
| "Plateforme complète" | Pas d'ENT, pas de gestion élèves | "Générateur d'activités" — fonctionnel, précis |
| Logo/texte "IA" dans l'interface | Règle interface | "A-SCHOOL" ou rien |

---

## 7. Plan de communication par canal

### Canal 1 — Bouche-à-oreille entre profs (priorité absolue)

**Pourquoi c'est le canal #1** : Les profs font confiance à leurs collègues. Un outil recommandé par un pair vaut 10 pubs.

**Actions** :
1. Identifier et chouchouter les profs pilotes (Français 4e + HG + autres matières)
2. Leur demander de montrer l'outil à 1 ou 2 collègues dans leur établissement
3. Fournir un "kit de démonstration" : 3 exemples d'activités générées prêts à partager
4. Répondre à tous leurs feedbacks en moins de 48h

**Métriques** : nombre de nouveaux inscrits par parrainage identifiable (demander "comment vous avez connu l'outil" à l'inscription)

---

### Canal 2 — Groupes Facebook de profs (acquisition organique)

**Groupes cibles** :
- "Profs de français" (> 50 000 membres)
- "Profs d'histoire-géo" (> 30 000 membres)
- "Ressources pédagogiques collège/lycée"
- Groupes académiques (ex: "Profs Académie de Paris")

**Format de post recommandé** :
```
J'ai testé A-SCHOOL cette semaine pour mes 4e.
J'ai collé un extrait de Maupassant, choisi "exercices de réécriture",
et j'avais mes consignes + correction en 10 secondes.
Le .docx est directement utilisable.
Voilà ce que ça donne : [capture écran résultat]
C'est gratuit pour l'instant → school.afia.fr
```

**Règle** : Toujours poster un exemple réel de résultat (capture d'écran). Jamais de pub abstraite.

---

### Canal 3 — LinkedIn (crédibilité + réseau éducation)

**Cible** : formateurs INSPE, inspecteurs, directeurs d'établissements, journalistes spécialisés

**Format** :
- Post mensuel avec un exemple d'activité générée + données d'usage (ex: "50 profs, 800 activités générées ce mois")
- Témoignage d'un prof pilote (1 post trimestriel)
- Pas de jargon tech

---

### Canal 4 — E-mail direct (inscription + onboarding)

**Séquence d'onboarding recommandée** (à implémenter) :

| Email | Timing | Contenu |
|---|---|---|
| Email 1 — Bienvenue | J+0 (vérification compte) | "Votre compte est actif. Voici comment faire votre première activité." |
| Email 2 — Premier usage | J+2 | "Avez-vous essayé les exercices de réécriture ? Voilà un exemple." |
| Email 3 — Rétention | J+7 | "X activités générées par des profs cette semaine. Vos collègues l'utilisent." |
| Email 4 — Feedback | J+14 | "Qu'est-ce qui manque ? Répondez directement." |

---

### Canal 5 — Associations de profs et syndicats (canal long mais fort)

**Cibles** :
- AFEF (Association Française des Enseignants de Français)
- APHG (Association des Professeurs d'Histoire-Géographie)
- Newsletters académiques

**Action** : Proposer une démonstration gratuite lors d'une réunion ou d'un webinaire. Un seul contact peut débloquer des dizaines d'inscriptions.

---

### Canal 6 — Contenus pédagogiques (SEO long terme)

**Articles à écrire** (blog ou page statique sur school.afia.fr) :

1. "10 exemples d'exercices de réécriture pour la 4e générés en 10 secondes"
2. "Comment créer une fiche de révision brevet à partir d'un document HG"
3. "Analyse de source automatique : est-ce vraiment utilisable en classe ?"

**Règle** : chaque article doit contenir un exemple réel de sortie de l'outil.

---

## 8. Calendrier de lancement

### Phase 0 — Pilotes ciblés (Avril 2026)
Email direct aux profs sélectionnés — voir EMAIL_PILOTES.md

### Phase 1 — Consolidation pilote (Mai 2026)

| Semaine | Action |
|---|---|
| S0 | Déploiement VPS school.afia.fr — PRIORITÉ #1 |
| S1 | Ajouter pied de page A-SCHOOL dans les exports `.docx` et `@media print` |
| S1 | Ajouter signature dans le corps du mail `mailto:` |
| S2 | Contacter les profs pilotes pour un retour structuré (entretien 20 min) |
| S3 | Créer 3 captures d'écran d'exemples prêts à partager |
| S4 | Premier post dans 1 groupe Facebook de profs (avec exemple réel) |

### Phase 2 — Ouverture progressive (Juin 2026)

| Semaine | Action |
|---|---|
| S1-S2 | Implémenter séquence e-mail onboarding (4 mails) |
| S2 | Ajouter compteur "X activités créées" sur la page Mes activités |
| S3 | Post LinkedIn avec données pilote + témoignage prof |
| S4 | Contacter 1 association prof (AFEF ou APHG) pour présentation |

### Phase 3 — Avant rentrée (Août-Septembre 2026)

| Action | Timing |
|---|---|
| Post Facebook "préparez vos séquences de rentrée avec A-SCHOOL" | 25 août |
| Article blog "10 activités de rentrée prêtes en 2 minutes" | 28 août |
| Campagne e-mail vers inscrits inactifs | 1er septembre |
| Objectif inscrits actifs | 50 profs |

---

## 9. Métriques de succès

Ces métriques sont directement lisibles depuis le panel admin ou la base de données.

| Métrique | Outil de mesure | Objectif Mai 2026 | Objectif Rentrée 2026 |
|---|---|---|---|
| Inscrits vérifiés | Admin logs (signup) | 10 | 50 |
| Activités générées | Table `activites_sauvegardees` | 100 | 500 |
| Rétention J+7 | Comparer login J0 vs J+7 | 40% | 50% |
| Feedbacks reçus | Table feedback | 10 | 30 |
| Note moyenne feedback | Moyenne `rating` | > 3.5 | > 4.0 |

---

## 10. Messages clés par canal

| Canal | Message principal | Format |
|---|---|---|
| Facebook (profs) | "Voilà ce que ça génère en 10 secondes" | Capture d'écran du résultat |
| LinkedIn | "50 profs, 800 activités, un outil spécialisé" | Données + témoignage |
| Email onboarding | "Votre première activité en 3 clics" | GIF ou lien direct |
| Bouche-à-oreille | "Donne-moi ton extrait, je te montre" | Démonstration live |
| Fichier Word/impression | "Généré avec A-SCHOOL — school.afia.fr" | Pied de page silencieux |
| Association prof | "Présentez-nous à vos membres, c'est gratuit" | Démo 20 min |

---

*Document rédigé le 27/04/2026 — Mis à jour le 30/04/2026 — school.afia.fr — harketti@afia.fr*
