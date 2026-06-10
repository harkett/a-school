# SPEC-MODULE-SUPERIEUR-aSCHOOL

Version : 2.1

Statut : Référentiel pédagogique de référence

---

# 0. PRINCIPE DE PÉRIMÈTRE (cadre tout le reste)

**aSchool est un outil POUR L'ENSEIGNANT.** Son unique public, à tous les niveaux (Crèche, Maternelle, Primaire, Collège, Lycée, Supérieur), reste **l'enseignant**.

**Règle dure :** si une fonctionnalité ne sert pas le prof à enseigner, elle est **hors périmètre** — même si elle est « pédagogique ». Tout ce qui s'adresse directement à l'étudiant (chercher un emploi, gérer son CV, son portfolio personnel), ou à un autre public (conseillers d'orientation, recruteurs), est exclu.

Conséquence pour le Supérieur : on outille **l'enseignant du supérieur** à concevoir, structurer, produire et évaluer son enseignement. Le reste sort.

---

# 1. OBJECTIF GLOBAL

Le module Enseignement Supérieur d'aSchool permet **à l'enseignant** :

- de structurer ses formations post-bac (UE, ECTS, compétences) ;
- de concevoir et générer des contenus pédagogiques (cours, TD, TP, QCM, examens, corrigés) ;
- d'évaluer par compétences ;
- de suivre la progression de ses étudiants ;
- de produire des bilans pédagogiques.

Public concerné : **enseignants** intervenant en
- BTS
- BUT
- Licence
- Master
- Écoles spécialisées
- CFA
- Formation continue

---

# 2. ARCHITECTURE PÉDAGOGIQUE

## Couche 1 - Formation

Exemples :

- BTS SIO
- BTS MCO
- BUT Informatique
- Licence Informatique
- Master IA

---

## Couche 2 - Unités d'Enseignement (UE)

Exemples :

- Développement Web
- Bases de données
- Réseaux
- Mathématiques
- Gestion de projet

---

## Couche 3 - Modules

Exemples :

- HTML
- CSS
- Python
- SQL
- Docker

---

## Couche 4 - Compétences

Chaque module est associé à des compétences observables, que l'enseignant mobilise pour concevoir et évaluer son enseignement.

---

# 3. AXES PÉDAGOGIQUES

> Ces axes décrivent ce que l'enseignant peut **enseigner et évaluer** avec aSchool. Ils ne décrivent pas des démarches personnelles de l'étudiant.

## Axe 1 - Connaissances disciplinaires

### Objectifs

- acquérir des savoirs
- comprendre les concepts
- maîtriser les fondamentaux

### Exemples

#### Informatique

- algorithmique
- programmation
- réseau
- cybersécurité

#### Gestion

- comptabilité
- finance
- marketing

#### Santé

- biologie
- anatomie
- réglementation

---

## Axe 2 - Compétences professionnelles

### Objectifs

- préparer au métier
- appliquer les connaissances
- résoudre des problèmes réels

### Compétences

- analyser
- concevoir
- développer
- produire
- tester
- maintenir
- évaluer

---

## Axe 3 - Compétences transversales

### Communication

- rédiger
- présenter
- argumenter

### Collaboration

- travail en équipe
- animation de réunion
- gestion de conflit

### Numérique

- culture numérique
- cybersécurité
- IA générative

### Citoyenneté

- éthique
- RGPD
- responsabilité

---

## Axe 4 - Autonomie

### Compétences

- gestion du temps
- organisation
- planification
- autoformation
- autoévaluation

---

## Axe 5 - Recherche et Innovation

### Compétences

- veille
- recherche documentaire
- esprit critique
- méthodologie scientifique

---

## Axe 6 - Professionnalisation

> Ce que l'enseignant **encadre et évalue** : stages, alternance, projets tutorés. aSchool aide le prof à concevoir et suivre ces dispositifs — il ne gère pas la recherche d'emploi de l'étudiant.

### Activités

- stages
- alternance
- projets tutorés
- hackathons
- cas réels

---

## Axe 7 - Évaluation

### Modalités

- contrôle continu
- examens
- TP
- projets
- soutenances
- certifications

---

> **Note de périmètre — ce qui a été retiré (v2.0 → v2.1) :**
> L'ancien « Axe 8 - Insertion professionnelle » (CV, LinkedIn, portfolio personnel, entretien, réseau professionnel) a été **retiré** : ces fonctions s'adressent directement à l'étudiant dans sa démarche d'insertion, pas à l'enseignant dans son acte d'enseigner. Hors périmètre d'aSchool.

---

# 4. NIVEAUX D'ACQUISITION

| Niveau | Description |
|----------|----------|
| Découverte | Première exposition |
| Débutant | Réalisation guidée |
| Intermédiaire | Réalisation partiellement autonome |
| Avancé | Réalisation autonome |
| Expert | Transmission et optimisation |

---

# 5. ECTS

## Structure

Chaque UE possède :

- nombre d'ECTS
- volume horaire
- compétences associées
- modalités d'évaluation

### Exemple

UE Développement Web

- 6 ECTS
- 60 heures
- 5 compétences

---

# 6. STRUCTURE DES COURS

Chaque cours contient :

- id
- titre
- description
- objectifs
- prérequis
- compétences visées
- ressources
- évaluations

---

# 7. STRUCTURE DES ACTIVITÉS

Chaque activité contient :

- id
- titre
- module
- objectifs
- durée
- consignes
- ressources
- critères d'évaluation

---

# 8. STRUCTURE DES ÉVALUATIONS

## Savoirs

- QCM
- examens
- devoirs

## Savoir-faire

- TP
- projets
- études de cas

## Savoir-être

- communication
- collaboration
- autonomie

---

# 9. STRUCTURE DES BILANS

## Résultats académiques

- moyenne
- crédits obtenus

## Compétences acquises

- liste détaillée

## Compétences en développement

- axes de progression

## Recommandations

- pédagogiques

---

# 10. IA PÉDAGOGIQUE

> **Public unique : l'enseignant.** L'IA produit des supports **que le prof génère**, pour son enseignement et pour ses étudiants. L'outil n'est pas mis entre les mains de l'étudiant.

L'IA peut générer, **à la demande de l'enseignant** :

- cours
- TD
- TP
- QCM
- examens
- corrigés
- exercices, quiz et fiches de révision **destinés à ses étudiants** (produits par le prof, pas par l'étudiant)

> **Note de périmètre — ce qui a été retiré (v2.0 → v2.1) :**
> L'ancienne sous-section « Étudiants » (l'IA générant directement pour l'étudiant : parcours personnalisés en autonomie, etc.) a été **reformulée** : tout ce que l'IA produit pour les étudiants est généré **par l'enseignant**, qui reste l'unique utilisateur de l'outil.
> L'ancienne section « Portfolio étudiant » a été **retirée** : un portfolio personnel d'étudiant (projets, stages, certifications, publications) sert l'étudiant, pas le prof. Hors périmètre.

---

# 11. MODÈLE DE DONNÉES

## Formation

- id
- nom
- diplôme

## UE

- id
- formation_id
- nom
- ects

## Module

- id
- ue_id
- nom

## Compétence

- id
- module_id
- libelle

## Activité

- id
- module_id
- titre

## Évaluation

- id
- module_id
- type

## Étudiant

- id
- nom
- prénom

> Note : l'entité « Étudiant » existe pour que **l'enseignant** suive la progression et produise des bilans. Ce n'est pas un compte utilisateur étudiant.

## Bilan

- id
- etudiant_id

---

# 12. PASSERELLE GLOBALE aSCHOOL

> La passerelle d'aSchool est une chaîne de **niveaux d'enseignement**. Elle s'arrête au Supérieur (formation continue incluse). L'**emploi n'est pas un niveau d'enseignement** : aSchool prépare à l'employabilité comme compétence enseignée, mais ne gère pas l'emploi lui-même.

Crèche
→ Maternelle
→ Élémentaire
→ Collège
→ Lycée
→ Supérieur
→ Formation continue

> **Note de périmètre — ce qui a été retiré (v2.0 → v2.1) :**
> Le maillon « → Emploi » a été **retiré** de la passerelle : ce n'est ni un niveau de scolarité, ni de l'enseignement. Hors périmètre.

---

# 13. CONTRAINTES IA

Interdictions :

- discrimination
- notation arbitraire
- génération de résultats fictifs

Obligations :

- neutralité
- traçabilité
- explicabilité
- conformité RGPD

---

# PISTE PARQUÉE (hors de cette spec — à statuer séparément)

> **Module « orientation » (public = conseillers d'orientation / ex-CIO) :** idée évoquée, NON intégrée ici car elle viserait un **public autre que l'enseignant** (les conseillers d'orientation). Cela sortirait du principe de périmètre (§0). À examiner comme décision stratégique distincte, à froid — ne pas mélanger avec la spec Supérieur.

---

# FIN DE SPÉCIFICATION
