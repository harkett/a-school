# SPEC-MODULE-CRECHE-aSCHOOL-V2

## Version
2.0

## Statut
Référentiel pédagogique de référence

## Public cible

- Crèches
- Micro-crèches
- Multi-accueils
- Haltes-garderies
- Assistantes maternelles
- EJE
- CAP AEPE
- Enseignants de Petite Section

---

# 1. OBJECTIFS DU MODULE

- Fournir un référentiel pédagogique national 0-3 ans
- Accompagner les professionnels dans l'observation des enfants
- Générer des activités adaptées à l'âge
- Produire des bilans pédagogiques
- Faciliter la transition Crèche → École maternelle

---

# 2. TRANCHES D'ÂGE

## Groupe A - Nourrisson
0 à 12 mois

## Groupe B - Jeune marcheur
12 à 24 mois

## Groupe C - Grand explorateur
24 à 36 mois

---

# 3. NIVEAUX D'ACQUISITION

| Niveau | Description |
|----------|----------|
| Non observé | Aucun indice observé |
| En émergence | Premières manifestations |
| En cours d'acquisition | Réalisation irrégulière |
| Acquis | Réalisation régulière |
| Consolidé | Réalisation stable et transférable |

---

# 4. AXES PÉDAGOGIQUES

1. Sécurité affective
2. Développement cognitif
3. Développement du langage
4. Développement moteur
5. Socialisation
6. Autonomie
7. Bien-être quotidien
8. Relation avec les familles
9. Aménagement des espaces

---

# 5. STRUCTURE DES OBSERVATIONS

Les observations doivent être :
- factuelles
- neutres
- datées
- contextualisées

Exemple :
> Lina a empilé 4 cubes de manière autonome.

---

# 6. STRUCTURE DES ACTIVITÉS

- titre
- âge cible
- axe pédagogique
- objectif
- matériel
- déroulement
- variantes
- points de vigilance
- durée estimée

---

# 7. STRUCTURE DES BILANS

- Forces observées
- Progressions observées
- Centres d'intérêt
- Compétences en développement
- Recommandations pédagogiques
- Préparation à l'entrée en PS

---

# 8. PASSERELLE CRÈCHE → PS

| Axe Crèche | Domaine PS |
|------------|------------|
| Sécurité affective | Devenir élève |
| Langage | Mobiliser le langage |
| Cognitif | Structurer sa pensée |
| Motricité | Activité physique |
| Socialisation | Vivre ensemble |
| Autonomie | Devenir élève |
| Bien-être | Adaptation scolaire |
| Famille | Liaison école-famille |

---

# 9. MODÈLE DE DONNÉES

## AxeCreche
- id
- nom
- description

## DomaineCreche
- id
- axe_id
- nom

## CompetenceCreche
- id
- domaine_id
- tranche_age
- libelle

## ObservationCreche
- id
- enfant_id
- competence_id
- niveau_acquisition

---

# 10. RÈGLES IA

L'IA ne doit jamais :
- diagnostiquer
- interpréter médicalement
- étiqueter un enfant

L'IA doit :
- rester factuelle
- valoriser les progrès
- proposer des activités adaptées

---

FIN DE SPÉCIFICATION
