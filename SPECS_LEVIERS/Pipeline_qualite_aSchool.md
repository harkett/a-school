# Pipeline de validation qualité — aSchool

## Comment utiliser ce document
Ce document décrit l'architecture de validation qualité qui relie tous les leviers retenus en un seul flux cohérent. Ce n'est pas un levier supplémentaire — c'est le système qui fait fonctionner tous les leviers ensemble, automatiquement, à chaque sortie d'aSchool. Le développeur doit lire ce document après avoir lu les leviers retenus (Leviers_retenus.md) et l'infrastructure technique (Infrastructure_aSchool.md) : il suppose que les 6 leviers sont connus.

---

## Idée centrale

Chaque fois qu'aSchool produit une sortie — qu'il s'agisse d'un exercice généré à partir d'un texte collé, d'une séance générée par le Levier 1, ou d'une séquence optimisée par le Levier 3 — le contenu passe automatiquement par un pipeline de validation qualité avant d'être livré au prof.

Ce pipeline n'est pas un filtre.
C'est un système de contrôle qualité pédagogique multicouches, invisible pour le prof, mais dont les résultats lui sont restitués sous forme d'un rapport synthétique.

Le prof ne déclenche rien. Il reçoit le contenu + le rapport. Il choisit ce qu'il fait.

---

## Origine de ce document

Ce pipeline est extrait de l'"Assistant de calibration pédagogique", levier analysé en session. Conclusion de l'analyse : ce levier n'est pas une fonctionnalité utilisateur à ajouter. C'est l'architecture d'exécution des 6 leviers retenus. Chacun de ses 8 types de calibration est déjà documenté dans un levier retenu. Plutôt que de créer un 7e levier redondant, ce document architecturise la relation entre les 6 existants.

---

## Deux modes d'activation

Le pipeline fonctionne dans deux situations distinctes.

| Mode | Déclencheur | Leviers actifs |
|---|---|---|
| **Mode génération** | aSchool génère lui-même le contenu (Levier 1, outil actuel) | Tous les leviers pertinents s'appliquent automatiquement à la sortie |
| **Mode validation** | Le prof colle son propre contenu pour le faire analyser | Les leviers s'appliquent comme vérificateurs externes |

En mode validation, aSchool devient un auditeur pédagogique : le prof soumet ce qu'il a déjà produit, le pipeline analyse et restitue un rapport. C'est l'usage principal du Levier 3 (Optimiseur) et du Levier 5 (Analyseur de consignes).

---

## Les 6 étapes du pipeline

Chaque étape correspond à un levier retenu. Elles s'appliquent en séquence. Une sortie qui franchit les 6 étapes est une sortie validée pédagogiquement.

---

### Étape 1 — Contrôle de cohérence structurelle
**Levier source : Levier 1 — Générateur d'orchestrations pédagogiques**

Vérifie que le contenu produit respecte une architecture pédagogique cohérente : phases logiques, progression des niveaux cognitifs, transitions valides, durée équilibrée, présence des moments d'ancrage.

**En mode génération :** le Levier 1 est lui-même l'auteur — la structure est garantie à la source.
**En mode validation :** le pipeline analyse la structure existante et signale les ruptures.

Ce que le pipeline vérifie :
- Progression logique des phases (activation → exploration → structuration → entraînement → ancrage)
- Équilibre des durées (aucune phase ne monopolise la séance)
- Présence d'au moins un moment de consolidation mémorielle
- Transitions entre activités (pas de sauts brutaux)

---

### Étape 2 — Détection des ambiguïtés cognitives
**Levier source : Levier 2 — Détection automatique des zones d'ambiguïté cognitive**

Parcourt l'intégralité du contenu produit pour repérer les formulations, les notions et les exercices qui présentent un risque d'interprétation erronée ou de confusion conceptuelle.

Ce que le pipeline vérifie :
- Mots polysémiques à risque dans le contexte de la matière et du niveau
- Conditions implicites non formulées (tirages aléatoires, hypothèses géométriques, etc.)
- Confusions notionnelles documentées dans l'index des ambiguïtés (Infrastructure Élément 1)
- Ambiguïtés de transfert entre disciplines

**Sortie :** liste des zones à risque avec proposition de reformulation corrigée.

---

### Étape 3 — Optimisation de la séquence
**Levier source : Levier 3 — Optimiseur de séquences pédagogiques**

Analyse la séquence complète — pas les éléments un par un, mais leur articulation globale. Vérifie que la progression est équilibrée, cohérente, sans ruptures conceptuelles et sans activités inefficaces.

Ce que le pipeline vérifie :
- Absence de surcharge cognitive (trop de notions nouvelles dans un temps court)
- Absence de ruptures conceptuelles (notion B supposant notion A non encore construite)
- Efficacité de chaque activité par rapport à l'objectif pédagogique déclaré
- Rééquilibrage si la distribution des phases est déséquilibrée

**Note :** en mode génération, cette étape agit comme contrôle post-production (le Levier 1 construit, le Levier 3 valide). En mode validation, elle est l'étape centrale.

---

### Étape 4 — Vérification de la cohérence curriculaire
**Levier source : Levier 4 — Moteur de cohérence curriculaire inter-disciplines**

Confronte le contenu produit aux programmes officiels et — si le module paramètres est activé — aux progressions réelles des autres matières de l'établissement.

Ce que le pipeline vérifie :
- Notions supposées acquises par le programme mais non encore vues selon le calendrier réel
- Termes ou notions qui changent de sens dans d'autres matières (variantes disciplinaires — Infrastructure Élément 4)
- Opportunités de connexion inter-disciplinaires non exploitées
- Contradictions avec ce qui est enseigné en parallèle dans d'autres cours

**Sortie :** alertes sur les incohérences + suggestions de synergie inter-disciplines.

---

### Étape 5 — Analyse qualité des consignes
**Levier source : Levier 5 — Analyseur de qualité didactique des consignes**

Analyse chaque consigne individuellement, avec une précision chirurgicale : clarté, précision didactique, charge cognitive, risque d'erreur typique, cohérence avec l'objectif.

Ce que le pipeline vérifie consigne par consigne :
- Formulations floues ou vagues ("commentez", "analysez", "décrivez")
- Étapes implicites non formulées
- Mots à double sens dans le contexte de la matière
- Charge mentale excessive (plusieurs tâches confondues en une seule consigne)
- Incohérence entre la consigne et l'objectif pédagogique déclaré

**Note développeur :** cette étape est la plus granulaire du pipeline. Elle s'appuie sur l'index des erreurs typiques (Infrastructure Élément 2) et le moteur de granularisation (Infrastructure Élément 1 — Approfondissement).

---

### Étape 6 — Contrôle d'équité pédagogique
**Levier source : Levier 6 — Détecteur d'équité pédagogique**

Vérifie que le contenu ne contient pas de biais qui fausseraient l'évaluation ou créeraient des désavantages injustes.

Ce que le pipeline vérifie (les 3 composants retenus uniquement — voir Leviers_retenus.md) :
- **Biais de contenu** : le contenu mesure-t-il réellement ce qu'il prétend mesurer ?
- **Biais de difficulté** : le niveau est-il cohérent avec la classe et la progression réelle ?
- **Biais émotionnel léger** : y a-t-il des formulations anxiogènes ou démotivantes ?

---

## Ce que le prof reçoit

À l'issue du pipeline, le prof reçoit deux choses simultanément :

**1. Le contenu validé** — exercice, séance, séquence, consigne — prêt à l'usage.

**2. Un rapport qualité synthétique** structuré ainsi :

```
Rapport qualité aSchool
─────────────────────────────────────────
✅ Structure pédagogique       — validée
⚠️ Ambiguïtés détectées       — 2 zones signalées (voir détail)
✅ Séquence                    — équilibrée
⚠️ Cohérence inter-disciplines — 1 décalage temporel détecté
✅ Qualité des consignes       — 4 consignes analysées, 1 reformulée
✅ Équité pédagogique          — aucun biais détecté
─────────────────────────────────────────
Score global : Bon — 2 points d'attention
```

Le prof voit immédiatement ce qui est validé et ce qui mérite attention. Il peut consulter le détail de chaque signal ou ignorer ceux qu'il juge non pertinents. Il reste maître de la décision finale.

---

## Architecture pour le développeur

### Ordre d'exécution

Les étapes 2, 4, 5 et 6 peuvent s'exécuter en parallèle (elles sont indépendantes).
Les étapes 1 et 3 doivent s'exécuter l'une avant l'autre (la 3 valide ce que la 1 a produit).

**Séquence recommandée :**
1. Étape 1 (Structure) — en premier, définit la forme globale
2. Étapes 2, 4, 5, 6 — en parallèle sur le contenu produit par l'étape 1
3. Étape 3 (Optimiseur) — en dernier, consolide les signaux et propose la version optimisée finale

### Infrastructure requise

Chaque étape du pipeline s'appuie sur les éléments d'infrastructure documentés dans Infrastructure_aSchool.md :

| Étape | Infrastructure utilisée |
|---|---|
| Étape 1 — Structure | Graphe universel des notions (Élément 1) + Index activités compatibles (Élément 3) |
| Étape 2 — Ambiguïtés | Graphe universel + Index ambiguïtés (Élément 1) + Index erreurs typiques (Élément 2) |
| Étape 3 — Optimiseur | Tous les éléments d'infrastructure |
| Étape 4 — Cohérence curriculaire | Variantes disciplinaires (Élément 4) + Graphe universel (Élément 1) |
| Étape 5 — Consignes | Index erreurs typiques (Élément 2) + Granularisation (Élément 1 approfondissement) |
| Étape 6 — Équité | Index erreurs typiques (Élément 2) + Graphe universel (Élément 1) |

### Dépendance au module paramètres

L'Étape 4 (Cohérence curriculaire) fonctionne en deux niveaux selon ce qui est disponible :
- **Sans module paramètres** : s'appuie sur les programmes officiels uniquement (version immédiate)
- **Avec module paramètres** : s'appuie sur les progressions réelles saisies par l'établissement (version enrichie)

Le module paramètres est documenté dans Leviers_retenus.md, Levier 4.

### Ce qui ne fait PAS partie du pipeline

Certains composants de l'"Assistant de calibration pédagogique" original ont été écartés car ils nécessitent des données élèves (hors scope actuel) :
- Calibration par profil cognitif individuel → nécessite PPD ⚠️
- Calibration en temps réel selon les réponses des élèves → nécessite données élèves ⚠️
- Calibration émotionnelle fine → nécessite données comportementales ⚠️

Ces composants sont documentés dans Leviers_non_retenus.md.

---

## Résumé de la relation entre leviers et pipeline

| Levier | Rôle autonome (usage direct par le prof) | Rôle dans le pipeline (automatique) |
|---|---|---|
| Levier 1 — Orchestrations | Générer une séance from scratch | Définit la structure de référence (Étape 1) |
| Levier 2 — Ambiguïtés | Analyser un exercice pour détecter les risques | Parcourt tout le contenu produit (Étape 2) |
| Levier 3 — Optimiseur | Améliorer une séquence existante | Consolide et optimise la sortie finale (Étape 3) |
| Levier 4 — Cohérence curriculaire | Vérifier l'alignement inter-disciplines | Confronte le contenu au curriculum (Étape 4) |
| Levier 5 — Consignes | Analyser une consigne en profondeur | Contrôle chaque consigne du contenu (Étape 5) |
| Levier 6 — Équité | Auditer une évaluation pour ses biais | Contrôle les biais de contenu, difficulté, émotion (Étape 6) |

Chaque levier a donc une double vie : il est activable directement par le prof pour un usage ciblé, ET il s'exécute automatiquement en arrière-plan sur chaque sortie d'aSchool.

---
