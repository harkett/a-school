# Dashboard développeur — Leviers aSchool

> Référence de session. Lire avant de coder. Se base sur les 3 documents de SPECS_LEVIERS.

---

## Ce qu'est aSchool aujourd'hui

Générateur d'exercices pédagogiques pour enseignants du secondaire (6e → Terminale).
Modèle actuel : le prof colle un texte → aSchool génère un exercice avec correction.
Stack : FastAPI (port 8001 VPS) + React + Groq (llama-3.3-70b-versatile) + SQLite.

---

## Ce que les leviers ajoutent

Les leviers ne remplacent pas la génération existante. Ils ajoutent des outils qui opèrent à des niveaux supérieurs (séquence complète, analyse didactique, optimisation, audit).

Chaque levier a une **double vie** :
1. **Usage direct** — le prof l'active volontairement pour un besoin ciblé
2. **Pipeline automatique** — tourne en arrière-plan sur chaque sortie d'aSchool

---

## Les 6 leviers retenus

| Statut | # | Nom | Ce que le prof fournit | Ce qu'aSchool produit | Ordre | Durée est. | Difficulté |
|---|---|---|---|---|---|---|---|
| ☐ | **L1** | Générateur d'orchestrations | Thème + matière + niveau + durée | Séance complète en 5-6 phases structurées | 3 | 2 sessions | Moyen |
| ☐ | **L2** | Détecteur d'ambiguïtés cognitives | Un exercice ou un énoncé | Zones de risque d'incompréhension + reformulations | 2 | 1 session | Facile |
| ☐ | **L3** | Optimiseur de séquences | Une séquence existante (collée) | Version améliorée + liste des problèmes détectés | **1** | **1 session** | **Facile** |
| ☐ | **L4** | Cohérence curriculaire | Rien (automatique) | Alertes inter-disciplines + opportunités de synergie | 6 | 2-3 sessions | Difficile |
| ☐ | **L5** | Analyseur de consignes | Une consigne seule | Analyse didactique chirurgicale + version optimisée | 4 | 1 session | Facile |
| ☐ | **L6** | Détecteur d'équité | Une évaluation | Détection de 3 biais : contenu, difficulté, émotionnel | 5 | 1 session | Facile |
| ☐ | **Pipeline** | Assemblage automatique | Transparent pour le prof | Rapport qualité synthétique sur chaque sortie | Progressif | Au fil des leviers | Moyen |

> **Statut :** ☐ À faire — ☑ Livré en prod
> **Ordre :** ordre d'implémentation recommandé (1 = premier à coder)
> **Durée est. :** 1 session ≈ 3-4h de dev effectif
> **Difficulté :** complexité technique côté code (pas côté pédagogie)

### Distinctions clés à ne pas confondre

| | L1 — Orchestrations | L3 — Optimiseur |
|---|---|---|
| Point de départ | Le prof n'a rien | Le prof a déjà une séquence |
| Entrée | Thème + niveau + durée | Séquence existante collée |
| Sortie | Séquence générée from scratch | Séquence existante améliorée |

| | L2 — Ambiguïtés (exercice entier) | L5 — Consignes (une seule consigne) |
|---|---|---|
| Granularité | Exercice complet | Une instruction isolée |
| Usage typique | Avant de distribuer un exercice | Avant d'écrire une question d'exam |

---

## L'infrastructure (socle invisible)

Ce n'est pas une fonctionnalité visible. C'est la base de connaissances pédagogiques qui rend chaque levier plus précis.

| Statut | Élément | Contenu | Alimente |
|---|---|---|---|
| ☐ v2 | **Élément 1** — Graphe universel des notions | Toutes les notions 6e→Terminale, leurs prérequis, dépendances, confusions possibles, mots polysémiques | L1, L2, L3, L4, L5, L6 |
| ☐ v2 | **Élément 2** — Index erreurs typiques | Erreurs récurrentes par notion, cause cognitive, niveau scolaire | L2, L3, L5, L6, génération actuelle |
| ☐ v2 | **Élément 3** — Index activités compatibles | Activités les plus efficaces par notion, classées par niveau Bloom | L1, L3, génération actuelle |
| ☐ v2 | **Élément 4** — Variantes disciplinaires | Comment un même mot/concept change de sens selon la matière | L4, L2 |

> **Statut ☐ v2** : pas encore construit — LLM Groq joue ce rôle en v1. Sera enrichi progressivement avec l'usage en production.

### Stratégie d'implémentation de l'infrastructure

- **v1 (maintenant)** : le LLM Groq joue le rôle de l'infrastructure via des prompts bien conçus. Valeur immédiate, zéro délai.
- **v2 (progressivement)** : les patterns détectés en production alimentent une base de données structurée interne. L'infrastructure propriétaire se construit naturellement avec l'usage, sans demander quoi que ce soit aux profs.

---

## Le pipeline qualité — architecture d'assemblage

Ce pipeline n'est PAS un levier supplémentaire. C'est le système qui fait fonctionner tous les leviers ensemble automatiquement sur chaque sortie.

```
┌─────────────────────────────────────────────────┐
│  Étape 1 — Contrôle structure (L1)              │  ← en premier
└─────────────────────┬───────────────────────────┘
                      │
        ┌─────────────┼─────────────────┐
        ▼             ▼                 ▼
  Étape 2 (L2)   Étape 4 (L4)    Étapes 5+6       ← en parallèle
  Ambiguïtés     Cohérence        (L5+L6)
        └─────────────┼─────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│  Étape 3 — Optimiseur (L3)                      │  ← en dernier
└─────────────────────────────────────────────────┘
```

**Ce que le prof reçoit à la fin :**
```
Rapport qualité aSchool
─────────────────────────────────────────
✅ Structure pédagogique       — validée
⚠️ Ambiguïtés détectées       — 2 zones signalées
✅ Séquence                    — équilibrée
⚠️ Cohérence inter-disciplines — 1 décalage détecté
✅ Qualité des consignes       — 1 reformulée
✅ Équité pédagogique          — aucun biais
─────────────────────────────────────────
Score global : Bon — 2 points d'attention
```

**Deux modes :**
- **Mode génération** : aSchool produit le contenu (L1, outil actuel) → pipeline s'applique en sortie
- **Mode validation** : le prof colle son contenu existant → pipeline audite et restitue un rapport

---

## Ce qui est hors scope (nécessite données élèves)

Marqué ⚠️ dans les specs. Ne pas implémenter :
- Boucles de rétroaction temps réel selon les réponses des élèves
- Différenciation PPD automatique
- Cartographie cognitive des classes
- Profilage Pédagogique Dynamique (PPD) — aussi RGPD sur mineurs

---

## Ordre d'implémentation recommandé

| Ordre | Levier | Statut | Pourquoi cet ordre |
|---|---|---|---|
| 1 | **L3 — Optimiseur** | ☐ | Impact immédiat — chaque prof a des séquences existantes. Priorité haute explicitée dans les specs. |
| 2 | **L2 — Ambiguïtés** | ☐ | S'intègre naturellement sur le flux de génération existant. |
| 3 | **L1 — Orchestrations** | ☐ | Nouvelle UI, nouveau mode d'entrée — plus lourd à développer. |
| 4 | **L5 — Consignes** | ☐ | Chirurgical, scope étroit, rapide à ajouter après L2. |
| 5 | **L6 — Équité** | ☐ | 3 composants clairs, périmètre borné. |
| 6 | **L4 — Cohérence** | ☐ | Le plus complexe — nécessite les programmes officiels. En dernier. |
| — | **Pipeline** | ☐ | S'assemble progressivement à chaque levier livré. |

---

## Plan session actuelle — L3 Optimiseur

### Ce que L3 fait concrètement
1. Le prof colle une séquence pédagogique existante (texte libre)
2. aSchool détecte : ruptures conceptuelles, surcharge cognitive, consignes ambiguës, activités inefficaces, progression déséquilibrée, ancrages manquants
3. aSchool génère : la séquence optimisée + la liste des problèmes détectés avec explication

### Ce que ça implique en code

**Backend** (`backend/routers/`)
- Nouveau endpoint : `POST /api/optimize-sequence`
- Payload : `{ sequence: str, matiere: str, niveau: str }`
- Prompt Groq structuré appliquant les 6 critères de l'Optimiseur
- Réponse : `{ sequence_optimisee: str, problemes_detectes: list, score: str }`

**Frontend** (`frontend/src/`)
- Nouveau composant ou nouvelle section dans l'UI existante
- Textarea pour coller la séquence + sélecteurs matière/niveau
- Affichage : séquence optimisée + liste des problèmes détectés en surbrillance

### Ce qui est hors scope pour cette session
- Pipeline complet (L3 standalone d'abord)
- Rapport qualité synthétique multi-leviers (viendra quand d'autres leviers seront implémentés)
- Infrastructure v2 (LLM comme proxy pour l'instant)

---

*Document créé le 11/05/2026 — à mettre à jour à chaque levier livré.*
