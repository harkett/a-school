# aSchool — TABLEAU DE BORD

> Document de **détail** (pour Claude) : réservoir d'idées priorisé (corps) + sections de référence + historique livré (FAIT). Le **pilotage** (ordre + statut + dépendance) vit dans [TRACKER.md](TRACKER.md).
> Détail de chaque chantier → fiche `BOUSSOLE/Dxx.md`. Mise à jour : fin de chaque session.

**Date :** 2026-06-11 · **Version :** 3.3.0 · **Focus :** Consolidation du cœur (filet de tests) avant réouverture du push

> Note dev : Bannière "Bientôt disponible" sidebar prof → `Sidebar.jsx`, bloc `{!collapsed && ...}` en bas.
> **Règle Aide :** Dès qu'une fonctionnalité est livrée, sa section Aide est rédigée dans la même session — à chaud, pendant que c'est frais. Jamais en retard.

---

## 🧭 Règle de pilotage — deux docs, un seul pilote par rôle

**Le pilotage (ordre + statut + dépendance) vit dans [TRACKER.md](TRACKER.md) ; ce document fait foi sur le détail** (score, description, réservoir, audits, RAG, journal FAIT). Le statut ne vit qu'une fois, dans le TRACKER — ce tableau n'a plus de colonne « État ». Aucun autre document ne ré-ordonne les priorités : tout plan/diagnostic/audit ponctuel est absorbé ici en chantier `Dxx` (détail) ou en item (réservoir) — jamais un pilote concurrent. Les anciens états vivent dans l'**historique git**.

**Périmètre de lecture = `main` uniquement.** Le contenu des autres branches (ex. `wip/deepgram-streaming` = chantier Deepgram gelé) n'est jamais lu spontanément : c'est du git, lecture **sur demande explicite** seulement. Pas de commande git large (`git grep --all`, `git log --all`, checkout d'une autre branche) de ma propre initiative.

---

## ▶️ Prochaine action (ouvre une nouvelle session ? lis ici en premier)

> ⏭️ **PREMIÈRE TÂCHE — matin du 13/06/2026 : TRAITER LA CRÈCHE (0-3 ans).** Stratégie : **même procédure que BTS CIEL option A** — (1) trouver le **référentiel officiel** de la petite enfance (0-3 ans, ex. cadre national d'accueil du jeune enfant — **à chercher/confirmer**) ; (2) en extraire les **vraies matières/domaines** (et **revoir les niveaux** Crèche : aujourd'hui 3 groupes d'âge `Groupe A/B/C` issus d'une spec interne, pas du référentiel officiel) ; (3) **script de seed** (niveau(x) Crèche + matières + paires) ; (4) `traite=true` → la **Crèche réapparaît** dans la vue prof (elle est **cachée** aujourd'hui car non traitée). C'est la **réintégration** de la Crèche par la procédure. Détail méthode : TRACKER § Refonte programmes (🧪 cas-test).

**Chantier actif = Consolidation du cœur ([D16](BOUSSOLE/D16.md)).** Filet de tests posé (Phase 1), on traite le suspect **tâche par tâche, sous filet** (19/19 verts). **Fait :** auto-save durci (2.1), P3.4 (`/api/generate` → 400/502), P3.6 (`nb`/`sous_type` manquant → 400). **Prochain : P5.11** (clarifier menu vs bouton), puis P3.5 (verdicts : § AUDIT, plus bas). Objectif final : rouvrir le push proprement, **Deepgram restant hors push**.

**Rappel :** dictée stabilisée (31/05, [D15](BOUSSOLE/D15.md)) ; Deepgram gelé sur `wip/deepgram-streaming`.

---

## Checklist avant modification

- [ ] Lire `FAIT ✅` (en fin de doc) — la modif est peut-être déjà livrée
- [ ] Lire le fichier cible **complet**, pas le diff
- [ ] Vérifier que routes/paths/fonctions cités existent
- [ ] Confirmer avec l'équipe avant action destructive ou multi-fichiers

---

## 🧭 Direction produit — aSchool décliné par niveau *(stratégique, conditionnel)*

*Note de cap, **pas un engagement**.* Au-delà du collège-lycée actuel, déclinaison possible d'aSchool **par niveau de scolarité** : **Crèche · Maternelle · Primaire · Collège · Lycée · Supérieur**. À engager **segment par segment, « si ça accroche »** (traction réelle) — jamais en bloc.

- **Premier maillon exploré** : Module Petite Enfance 0-3 ans → [D48](BOUSSOLE/D48.md).
- **Maillon déjà amorcé** : support niveau Supérieur ([D36](BOUSSOLE/D36.md), ex-I21) — devient rétrospectivement un segment de cette vision.

---

## Réservoir — Vue globale (tableau scoré)

> Tableau trié par **Score = Valeur + Faisabilité** (meilleur ROI en premier). Quand un item est livré → ~~barrer la ligne~~ + déplacer dans FAIT. La trace reste visible.

> **Leviers livrés en production :** L1 — Générateur d'orchestrations · L2 — Détecteur d'ambiguïtés cognitives · L3 — Optimiseur de séquences

> **Pré-requis transverse :** INFRA-RAG (pile RAG mutualisée) — codé en mode DEV, pas branché. Voir section *DÉCISION D'ARCHITECTURE — RAG* ci-dessous et fiche [INFRA-RAG](RAG/INFRA-RAG.md).

| N° | Titre | Effort | Valeur | Faisabilité | Score | Section | Détail (→Dxx) |
|---|---|---|---|---|---|---|---|
| [35](#item-35) | Versioning & transposition de séquences | 3 sessions | ★★★★★ | ★★★★★ | **10/10** | IMPORTANT | [D26](BOUSSOLE/D26.md) |
| [37](#item-37) | Affinage interactif de séquence (instruction prof + versions éphémères) | 1 session | ★★★★★ | ★★★★★ | **10/10** | IMPORTANT — code dormant (parké, D07) | [D07](BOUSSOLE/D07.md) |
| [36](#item-36) | Corpus Programmes MEN (producteur RAG) | 3,5-5 sessions restantes | ★★★★★ | ★★★★☆ | **9/10** | OPTIONNEL | [D24](BOUSSOLE/D24.md) |
| [38](#item-38) | Sortie séquence en JSON structuré (rendu pro) | 1 session | ★★★★☆ | ★★★★☆ | **8/10** | IMPORTANT — après 37 | [D27](BOUSSOLE/D27.md) |
| [39](#item-39) | Switch provider séquence → Claude Sonnet 4.6 | 2h | ★★★☆☆ | ★★★★★ | **8/10** | OPTIONNEL — après 38 | [D28](BOUSSOLE/D28.md) |
| [03](#item-03) | Analyseur de consignes | 1 session | ★★★★☆ | ★★★★★ | **9/10** | Mes Outils | [D17](BOUSSOLE/D17.md) |
| [04](#item-04) | Détecteur d'équité pédagogique | 1 session | ★★★★☆ | ★★★★★ | **9/10** | Mes Outils | [D17](BOUSSOLE/D17.md) |
| [28](#item-28) | Stratégie de remédiation | 0,5 session | ★★★★☆ | ★★★★★ | **9/10** | Mes Outils | [D17](BOUSSOLE/D17.md) |
| [33](#item-33) | Mémo flash (format révision rapide) | 0,5 session | ★★★★☆ | ★★★★★ | **9/10** | IMPORTANT — après 32 | [D21](BOUSSOLE/D21.md) |
| [07](#item-07) | Onboarding email J+2 / J+7 / J+14 | 3 jours | ★★★★☆ | ★★★★☆ | **8/10** | IMPORTANT | [D40](BOUSSOLE/D40.md) |
| [14](#item-14) | Bouton "Partagez avec vos collègues" | 1 session | ★★★★☆ | ★★★★☆ | **8/10** | OPTIONNEL | [D41](BOUSSOLE/D41.md) |
| [30](#item-30) | Différenciation DYS / FLE / approfondissement | 1 session | ★★★★☆ | ★★★★☆ | **8/10** | IMPORTANT | [D23](BOUSSOLE/D23.md) |
| [32](#item-32) | Visuels Mermaid / SVG | 1 session | ★★★★☆ | ★★★★☆ | **8/10** | IMPORTANT — prérequis 33+34 | [D20](BOUSSOLE/D20.md) |
| [02](#item-02) | Email admin → prof (3 templates) | 2h | ★★★☆☆ | ★★★★★ | **8/10** | IMPORTANT | [D42](BOUSSOLE/D42.md) |
| [08](#item-08) | Analyse des notations Groq | 1 jour | ★★★☆☆ | ★★★★★ | **8/10** | IMPORTANT | [D43](BOUSSOLE/D43.md) |
| [11](#item-11) | Fiche de révision Français + Fiche pédagogique HG | 30 min | ★★★☆☆ | ★★★★★ | **8/10** | IMPORTANT | [D45](BOUSSOLE/D45.md) |
| [16](#item-16) | Ambiguité → Créer une séquence | 1h | ★★★☆☆ | ★★★★★ | **8/10** | OPTIONNEL | [D33](BOUSSOLE/D33.md) |
| [27](#item-27) | Validation texte source par LLM (Option B) | 2h | ★★★☆☆ | ★★★★★ | **8/10** | OPTIONNEL | [D38](BOUSSOLE/D38.md) |
| [31](#item-31) | Appréciations bulletins & communication parents | 1 session | ★★★☆☆ | ★★★★★ | **8/10** | IMPORTANT | [D19](BOUSSOLE/D19.md) |
| [17](#item-17) | Quiz interactif élèves | 2 semaines | ★★★★★ | ★★☆☆☆ | **7/10** | OPTIONNEL | [D34](BOUSSOLE/D34.md) |
| [21](#item-21) | Support niveau Supérieur (BTS/prépa/licence) | 2 semaines | ★★★★☆ | ★★★☆☆ | **7/10** | OPTIONNEL | [D36](BOUSSOLE/D36.md) |
| [24](#item-24) | Google OAuth | 2-3 semaines | ★★★★☆ | ★★★☆☆ | **7/10** | OPTIONNEL | [D32](BOUSSOLE/D32.md) |
| [26](#item-26) | Pipeline qualité automatique | progressif | ★★★★☆ | ★★★☆☆ | **7/10** | OPTIONNEL | [D17](BOUSSOLE/D17.md) |
| [10](#item-10) | Timeouts sessions | 2h | ★★★☆☆ | ★★★★☆ | **7/10** | IMPORTANT | [D31](BOUSSOLE/D31.md) |
| [18](#item-18) | Aide spécifique par matière | 3-5 jours | ★★★☆☆ | ★★★★☆ | **7/10** | OPTIONNEL | [D35](BOUSSOLE/D35.md) |
| [23](#item-23) | Escape Game pédagogique | 2-3 semaines | ★★★☆☆ | ★★★★☆ | **7/10** | OPTIONNEL | [D37](BOUSSOLE/D37.md) |
| [29](#item-29) | Mode expérience prof (T1 / confirmé / expert) | 0,5 session | ★★★☆☆ | ★★★★☆ | **7/10** | Mes Outils | [D18](BOUSSOLE/D18.md) |
| [34](#item-34) | Supports de créativité élève | 1 session | ★★★☆☆ | ★★★★☆ | **7/10** | IMPORTANT — après 32 | [D22](BOUSSOLE/D22.md) |
| [01](#item-01) | Pages légales CNIL — placeholders [À COMPLÉTER] | En attente infos admin | ★★☆☆☆ | ★★★★★ | **7/10** | IMPORTANT | [D39](BOUSSOLE/D39.md) |
| [05](#item-05) | Page /contact | 2h | ★★☆☆☆ | ★★★★★ | **7/10** | IMPORTANT | [D29](BOUSSOLE/D29.md) |
| [06](#item-06) | Civilité M./Mme dans le profil | 2h | ★★☆☆☆ | ★★★★★ | **7/10** | IMPORTANT | [D30](BOUSSOLE/D30.md) |
| [12](#item-12) | Synchronisation pages afia.fr ↔ projets | Au prochain push MINOR/MAJOR | ★★☆☆☆ | ★★★★★ | **7/10** | TRANSVERSE | règle permanente — CLAUDE.md |
| [19](#item-19) | Admin — Menu Activités en groupe | 2h | ★★☆☆☆ | ★★★★★ | **7/10** | OPTIONNEL | [D44](BOUSSOLE/D44.md) |
| [25](#item-25) | Cohérence curriculaire inter-disciplines | 2-3 sessions | ★★★★☆ | ★★☆☆☆ | **6/10** | OPTIONNEL | [D25](BOUSSOLE/D25.md) |
| [15](#item-15) | Gestion emails sortants — backoffice admin | 1-2 sessions | ★★★☆☆ | ★★★☆☆ | **6/10** | OPTIONNEL | [D46](BOUSSOLE/D46.md) |
| [22](#item-22) | Théâtre — 13e matière | 1-2 semaines | ★★★☆☆ | ★★★☆☆ | **6/10** | OPTIONNEL | [D47](BOUSSOLE/D47.md) |
| [20](#item-20) | Projet demo-perf FastAPI + PostgreSQL | En fin de projet | ★★☆☆☆ | ★★★☆☆ | **5/10** | HORS-PÉRIMÈTRE | hors-périmètre — projet séparé |
| [40](#item-40) | Badge « aSchool vous reconnaît » près du nom du prof | 0,5 session | ★★★☆☆ | ★★★★☆ | à scorer | Mon Profil / Header | — |
| [41](#item-41) | Recherche dans la page Aide (plein-texte) | 0,5 session | à scorer | à scorer | à scorer | LIVRÉ LOCAL — non déployé | — |
| [42](#item-42) | Recherche globale dans l'application | à scorer | à scorer | à scorer | à scorer | OPTIONNEL | — |
| [43](#item-43) | Module Petite Enfance 0-3 ans — 1er segment vision multi-niveaux | à scorer | à scorer | à scorer | à scorer | FUTUR / stratégique | [D48](BOUSSOLE/D48.md) |
| [44](#item-44) | Bouton « Encoder » — ingestion autonome de référentiels (admin) | à scorer | à scorer | à scorer | à scorer | INFRA / Admin — à cadrer | — |

---

## ARCHITECTURE LEVIERS — Carte des synergies (14/05/2026)

> Grille de décision rapide : avant de lancer un item, savoir s'il doit être une feature standalone, une option absorbée, ou les deux. Évite de créer des pages inutiles ou au contraire de noyer une feature dans une autre.

### Cat. A — Absorbé par un autre (livrer dans la même session que le parent)

| Item | Absorbé par | Note |
|---|---|---|
| 28 — Extension L2 (remédiation) | L2 | Modifie prompt + section dans Ambiguites.jsx |
| 16 — Ambiguité → Créer une séquence | L2 | Bouton dans résultats L2 → navigue L1 |
| 11 — Fiche révision FR + Fiche pédago HG | Générateur d'activités | Deux lignes dans MATRICE_ACTIVITES |
| 27 — Validation texte LLM (Option B) | Générateur d'activités | Pré-validation dans le flow, invisible comme feature |
| 06 — Civilité M./Mme | Mon Profil | Un champ de plus dans le formulaire |
| 08 — Analyse notations Groq | AdminFeedbacks | Un prompt + un bloc dans la page admin |
| 02 — Email admin → prof (templates) | AdminFeedbacks | Bouton "Contacter" dans la page admin |
| 10 — Timeouts sessions | Auth (backend) | Config middleware, invisible UI |
| 18 — Aide spécifique par matière | Aide.jsx | Personnalisation du contenu selon profil |
| 19 — Admin — Menu Activités en groupe | Admin (backoffice) | Pattern `group: true` déjà dans AdminLayout |
| 29 — Mode expérience prof (T1/confirmé/expert) | Mon Profil + tous les prompts | 1 champ BDD + variable injectée partout — plus on attend, plus il manque |

### Cat. B — Standalone uniquement (ne peut pas être une option)

| Item | Raison |
|---|---|
| 01 — Pages légales CNIL | Routes dédiées, aucun sens en option |
| 05 — Page /contact | Route statique dédiée |
| 07 — Onboarding email J+2/J+7/J+14 | Infrastructure APScheduler backend, invisible UI |
| 15 — Gestion emails sortants admin | Journal + stats + bounces, périmètre propre |
| 17 — Quiz interactif élèves | Architecture entièrement différente (liens publics, live) |
| 20 — Projet demo-perf | Projet technique séparé hors aSchool |
| 21 — Support niveau Supérieur | Segment nouveau, scope trop large pour être une option |
| 22 — Théâtre — 13e matière | Extension scope distincte par nature |
| 23 — Escape Game pédagogique | Nouveau type de produit, architecture propre |
| 24 — Google OAuth | Infrastructure auth séparée |
| 31 — Appréciations bulletins & communication parents | Nouvelle section "Communication" — aucun outil existant pour l'accueillir |
| 36 — Corpus Programmes MEN (producteur RAG) | Premier producteur de corpus, consommé par L1/L25/Générateur d'activités |
| INFRA-RAG — Pile RAG mutualisée | Prérequis transverse, livrable une fois, hors numérotation L — voir [INFRA-RAG](RAG/INFRA-RAG.md) |
| 12 — Synchronisation afia.fr ↔ projets | Procédure transverse, pas une feature UI |

### Cat. C — Les 2 (standalone ET complément d'un autre)

| Item | En standalone | En complément de |
|---|---|---|
| **L1** (prod) | Générateur d'orchestrations | Reçoit L3 post-génération + item 16 depuis L2 |
| **L2** (prod) | Détecteur d'ambiguïtés | Item 28 s'y absorbe + pré-vérification avant génération d'activité |
| **L3** (prod) | Optimiseur de séquences | Bouton "Optimiser" post-L1 |
| 03 — Analyseur de consignes | Page dédiée Mes Outils | Bouton "Analyser" dans le générateur avant de cliquer "Générer" |
| 04 — Détecteur d'équité | Page dédiée Mes Outils | Bouton "Vérifier l'équité" dans ZoneResultat après génération évaluation |
| 14 — Partagez avec vos collègues | Modale dédiée | Option dans ZoneResultat ou HistoriqueActivités |
| 25 — Cohérence curriculaire | Page dédiée Mes Outils | Rapport post-L1 sur séquence générée |
| 26 — Pipeline qualité | Page "Rapport qualité" dédiée | Bouton "Analyser la qualité" dans ZoneResultat — agrège L2 + 03 + 04 en parallèle |
| 30 — Différenciation DYS/FLE/approfondissement | Outil standalone "Adapter une activité" | 3 boutons dans ZoneResultat après génération |
| 32 — Visuels Mermaid / SVG | Type d'activité "Schéma / Diagramme" | Rendu automatique dans ZoneResultat sur sorties existantes |
| 33 — Mémo flash | Type standalone "Créer un mémo flash" | Bouton dans ZoneResultat après une fiche de révision |
| 34 — Supports de créativité élève | Section "Créativité" dans Mes Outils | Nouveaux types dans le générateur standard |
| 35 — Versioning & transposition séquences | Outil "Transposer une séquence" | Bouton "Réutiliser / Fork" dans historique L1 |

> **Note clé :** Item 26 (Pipeline qualité) n'a de sens que quand L2 + 03 + 04 existent — c'est le méta-agrégateur. Sa forme minimale : bouton "Rapport qualité" dans ZoneResultat appelant les 3 en parallèle.

---

## DÉCISION D'ARCHITECTURE — RAG : Architecture et corpus

**Date :** 2026-05-15
**Statut :** validée (provisoire — révision après implémentation effective de 3 leviers consommateurs : Générateur de séquences, D25, D23)

---

### Pré-requis transverse — INFRA-RAG

Pile commune `backend/rag/` (client ChromaDB, embeddings, retrieve).
Livrable une fois, réutilisée par tous les producteurs et consommateurs RAG.
Hors typologie pédagogique (infra pure, pas un levier).

### 1. Principe & infrastructure

> **Portée :** typologie applicable uniquement aux leviers utilisant un grounding RAG. Les leviers sans RAG (analyseurs / transformateurs purs) ne sont pas concernés — voir section 4.

- **Pile unique :** instance ChromaDB partagée ([VPS_HOSTNAME]), collections distinctes par corpus
- **Classement par question pédagogique** (fonction), pas par contenu thématique

### 2. Règles de classification

1. Chaque levier déclare **1 question principale** + **1..N corpus mobilisés**
2. Tout corpus mobilisé est qualifié de **Principal** (répond directement à la question) ou **Secondaire** (ancrage contextuel). Le Secondaire est facultatif.
3. Distinction **producteur ≠ consommateur** : un levier qui indexe un corpus n'en est pas consommateur au sens pédagogique
4. Levier hors typologie → signal d'alerte (typologie incomplète OU levier mal défini)

### 3. Table active — Typologie pédagogique

| # | Question pédagogique | Corpus principal | Consommateurs | Producteur |
|---|---|---|---|---|
| 1 | Que doit-on enseigner ? | Programmes officiels MEN | Générateur de séquences, D25, Générateur d'activités | D24 |
| 2 | Comment adapter à un profil d'élève ? | Guides MEN inclusion / DYS / FLE | D23 | — |
| 3 | Comment évaluer équitablement ? | Charte laïcité / référentiels équité | D17 | — |
| 4 | Comment communiquer avec familles/admin ? | Guides académiques communication | D19 | — |
| 5 | Comment stimuler la créativité élève ? | Recherche pédagogique créativité | D22 | — |

**Légende :**
- **Producteur** = levier responsable de l'ingestion/maintenance du corpus dans ChromaDB
- `—` = pas de producteur défini, alimentation manuelle ou via un producteur futur non encore désigné
- **D24** dans la colonne Producteur = producteur du corpus *Programmes MEN* uniquement. L'infrastructure RAG (pile mutualisée) est traitée séparément dans la fiche [INFRA-RAG](RAG/INFRA-RAG.md).

### 4. Leviers sans RAG

Analyseurs / transformateurs purs (hors-portée de la typologie ci-dessus) :
**L2, L3, items 03, 26, 27, 28, 32, 33, 35, 37, 38**

### 5. Réserve — questions identifiées sans corpus actuel

- **Comment animer en classe ?** (gestion de classe, postures, transitions)
- **Comment progresser professionnellement ?** (veille pédagogique, développement)

> **Critère d'activation :** YAGNI — créer le corpus uniquement quand un levier concret le demande.

### 6. TODO implémentation

- [ ] Définir traduction technique **Principal/Secondaire** (pondération vs fallback vs purement documentaire)
- [ ] Format de métadonnée ChromaDB pour le champ `question_pedagogique`
- [ ] Convention de nommage des collections (ex. `corpus_programmes_men`, `corpus_inclusion_dys_fle`)

### 7. Template fiche levier consommateur (référence)

> **Application :** obligatoire pour toute fiche levier comportant un grounding RAG. À reproduire dans l'en-tête de la section "Grounding RAG".

```markdown
## Grounding RAG
**Question principale :** [une des 5 questions de la table active — section 3]
**Corpus mobilisés :**
- Principal : [nom du corpus]
- Secondaire : [nom du corpus] (si applicable)
**Infra :** instance ChromaDB partagée ([VPS_HOSTNAME]), collection `corpus_xxx`
```

---

## PRIORITAIRE

- [x] **PWA — Installabilité** | Livré 12/05
  *IOSInstallBanner, bfcache fix, cross-tab logout, SW update banner — testé iOS Safari.*

- [x] **PWA — Service Worker** | Livré 12/05
  *SW opérationnel, offline banner, cache propre au logout, update détectée automatiquement.*

- [x] **PWA — Responsive mobile (pages restantes)** | Livré 12/05
  *ZoneResultat, Bibliothèque, Aide — complété. Toutes les pages adaptées mobile.*

---

## OUTILLAGE / DETTE TECHNIQUE — hors gel des features

> Chantiers d'infrastructure / outillage, **non soumis au gel du backlog features** (ce ne sont pas des features produit). Pas urgents — à traiter à la réouverture du développement.

- [ ] **[Infra] Filet de test front (Vitest + React Testing Library)** | Chantier à part, non urgent
  *Le front aSchool n'a aucun test automatisé : chaque modif React (Aide, auto-save, AuthContext…) repose sur une vérif manuelle non rejouable. Installer Vitest + Testing-Library, câbler `npm test`, puis couvrir en priorité les composants critiques (dictée `TexteSource`, auto-save activités, `AuthContext`). Objectif : que toute modif front se solde par un test, comme le backend (règle CLAUDE.md n°8). Identifié 08/06/2026, en marge du nettoyage code (modif Aide.jsx validée à l'œil faute de filet front).*

- [ ] **[Process] Organisation des tests à 3 étages + journal de versions** | Formalisation, hors gel
  *Graver qui teste quoi et quand, pour qu'aucune tâche n'arrive direct chez les profs.*
  ***Étage 1 — Test technique** : CC, à CHAQUE tâche, en DEV. Test auto (pytest backend) ou prépa front. Question : « le code fait-il ce qu'il doit sans rien casser ? »*
  ***Étage 2 — Test d'usage** : Harketti, à CHAQUE tâche, en local. Vérif manuelle. Question : « ça marche pour un humain, c'est clair, le rendu est bon ? » Filtre obligatoire avant tout déploiement.*
  ***Étage 3 — Test terrain** : profs pilotes, PAR VERSION déployée, en PROD. Question : « ça sert vraiment en classe, que manque-t-il ? » Feedback produit, pas test technique.*
  ***Principe clé** : une tâche franchit étage 1 (CC) → étage 2 (Harketti), s'accumule avec d'autres en une VERSION cohérente, déployée via deploy.ps1, et seulement LÀ testée par les profs (étage 3). Leur retour redevient des tâches → repart à l'étage 1.*
  ***Besoin lié** : un mini journal de versions reliant chaque version aux tâches livrées → entrée dédiée ci-dessous. Identifié 08/06/2026.*

- [ ] **[Outillage] Mini journal de versions (version ↔ tâches livrées)** | Compagnon de l'étage 3, hors gel
  *Pas seulement lister « v3.3.0 = ces features » : **relier chaque version déployée aux tâches qu'elle embarque**, pour que lorsqu'un prof pilote remonte un problème, on sache **quelle version il utilise et ce qu'elle contient**. Traçabilité feedback prof ↔ version testée — compagnon direct de l'**étage 3** (item [Process] ci-dessus). Identifié 08/06/2026.*

- [ ] **[UX/Aide] Rubrique « Exemple » dans tous les « Comment ça marche »** | Transverse — à appliquer sur TOUS les outils
  *Ajouter une rubrique « Exemple » (un cas concret entrée → sortie) à la structure commune des onglets « Comment ça marche », pour **chaque** outil de l'appli — pas seulement le détecteur d'ambiguïtés. But : rendre l'aide vivante, le prof voit ce qu'il obtient avant de tester. Le contenu d'exemple **propre à chaque outil** vit dans son D respectif (ex. détecteur → D17) ; cet item ne porte que la **règle de structure commune**. Identifié 10/06/2026.*

- [ ] **[Refactor] Migration React Query (TanStack Query)** | Session dédiée, hors gel — ne pas mélanger
  *Adopter le standard industrie 2024-2026 pour la gestion des données en React, en remplacement des 20+ `fetch` manuels actuels : timeout AbortController, retry automatique différencié (auth vs Groq), loading/error centralisés, cache `staleTime` par type de requête. À traiter en session dédiée, sans mélanger avec d'autres chantiers. (Ex-item backlog #09, score 6/10 — basculé en dette le 10/06/2026.)*

- [ ] **[Maintenance] Dette technique complète (passe transverse)** | 2 sessions dédiées, hors gel
  *Passe de consolidation transverse : dépendances obsolètes, cohérence de la gestion d'erreurs API, documentation des règles métier, revue sécurité des routes. La migration React Query, initialement listée ici, est suivie séparément (voir l'item **[Refactor]** ci-dessus). À planifier en sessions dédiées. (Ex-item backlog #13, score 6/10 — basculé en dette le 10/06/2026.)*

- [ ] **[Mémoire] Nettoyer les memory files périmés (BOUSSOLE/BACKLOG → doc unique)** | Tâche mémoire dédiée, hors gel
  *Après la fusion (P1-P5, voir FAIT), plusieurs memory files de `~/.claude` décrivent encore « BOUSSOLE pilote / BACKLOG réservoir » comme deux docs, et `feedback_tracker_levier_sync` porte une **ref morte `MesMD/LEVIERS/`**. À reprendre à froid, **hook d'index + fichier ensemble** (cohérence) : `feedback_pilotage_boussole`, `feedback_boussole_tout_tracker`, `feedback_noter_idees`, `feedback_tracker_levier_sync`, + hooks MEMORY.md (23/24/35/60/66). Identifié 11/06/2026.*

- [ ] **[Archi/Échelle] Passage à grande échelle du référentiel (≈145 BTS + Masters/Licences/FC…)** | Réflexion validée 12/06/2026 — à ressortir le jour où on attaque l'échelle, rien à coder avant
  *Analyse de charge (factuelle). **Distinction clé** : la **structure** (niveaux/matières/paires) ne pèse rien — quelques milliers de lignes indexées, des Ko ; c'est le **CONTENU** (texte officiel embarqué en RAG, type BOEN 139 p / 699 vecteurs) qui pèse, **et seulement si on l'embarque**. **Ça casse par le HAUT, pas par le bas.** Ordre des vrais seuils : ① **INTERFACE ADMIN = le 1er mur, et il arrive tôt** — la grille matières×niveaux est un tableau lignes×colonnes par cycle ; au Supérieur ~200 niveaux × ~1000 matières = ~200 000 cases dans un seul tableau → DOM à genoux dès **quelques dizaines de niveaux/cycle** (~10k cases = lent, ~100k = inutilisable). ② **`/api/programmes` fourre-tout** : renvoie TOUT, appelé sur **6 pages, sans cache** → ~0,5-1 Mo/chargement à ~300-500 niveaux (gaspillage, pas blocage). ③ **Contenu RAG** si embarqué : 145 BTS × ~500-1000 chunks ≈ **100-150k vecteurs** Chroma → le vrai poste RAM/stockage VPS (optionnel, RAG éteint). ④ **SQLite (structure)** : jamais le problème à cette échelle. **Réponse VUE PROF = filtrage par `user_enseignements`** (déjà prévu par le modèle) : le prof déclare ce qu'il enseigne, l'appli ne montre que ça. **3 PIÈGES à garder** : (a) **ça ne règle PAS l'admin** → la refonte de la grille admin est un **chantier séparé, et c'est le vrai premier** ; (b) l'**écran de déclaration** a besoin d'un **picker cherchable/autocomplétion** (« tape BTS CIEL… »), jamais un `<select>` de 500 — sinon on déplace la lourdeur ; (c) **deux endpoints** : un « **mes programmes** » **scopé** (léger, quotidien) + un de **recherche paginé** (déclaration), pas le `/api/programmes` actuel. Le filtrage règle la **VUE**, pas la **GESTION** (admin) ni le **STOCKAGE** (contenu).*

- [ ] **[Notation] Deux nomenclatures de cycles qui ne se superposent pas** | À reprendre — NE PAS corriger seul, lié au chantier référentiel
  *Notre app nomme les cycles par **étape de scolarité** (Crèche · Maternelle · Primaire · Collège · Lycée · Supérieur, `seed_programmes.py:15-18`). L'**Éducation nationale**, elle, numérote des **cycles 1 à 4** (cycle 4 = 5e/4e/3e ; la 6e est en cycle 3). « cycle 4 » s'est invité chez nous **uniquement** par le référentiel maths : métadonnée `cycle="4"`, collection `maths_cycle4`, constante `CYCLE4_LEVELS={5e,4e,3e}` (`generate.py:23`). **Frictions factuelles** : (1) notre « Collège » (6e→3e) ≠ « cycle 4 » EN (5e→3e) ; (2) piège de chiffres — « Collège » est aussi le 4ᵉ de notre liste (`ordre=4`), sans aucun rapport avec le « cycle 4 » EN. À trancher AVEC le chantier référentiel (quelle nomenclature fait foi, comment relier les deux), pas en isolé. Identifié 12/06/2026, pendant l'analyse de l'existant du référentiel.*

- [ ] **[UX] Accès à TOUT l'historique en multi-cycles** | Rattaché au chantier programmes (TRACKER § Refonte programmes, réserve 3) — à traiter AVEC le passage `user_enseignements`, pas en isolé
  *« Mes activités » filtre **dur** sur matière+niveau du profil (`MesActivites.jsx:121-125`, aucune échappatoire). Inoffensif aujourd'hui (profil mono = 1 niveau), mais en multi un prof 3e+2nde ne verrait **jamais** la moitié de son travail. **Cible = garantir l'accès à tout l'historique** (« Voir tout » / chips niveau désactivables / autre — décision UI ouverte), PAS la mécanique du filtre en soi. Données jamais perdues (tri 100 % côté client, l'API renvoie tout). Le passage multi réécrira de toute façon la logique d'affichage → à regrouper là. Identifié 12/06/2026.*

- [ ] **[Évaluation] Échelles « niveaux d'acquisition » (Crèche & Supérieur)** | Module évaluation/observation futur — hors grille matière×niveau
  *Les deux référentiels définissent des **échelles d'évaluation**, distinctes de la grille programmes (matière×niveau) : Crèche = Non observé → En émergence → En cours d'acquisition → Acquis → Consolidé (SPEC-MODULE-CRECHE §3) ; Supérieur = Découverte → Débutant → Intermédiaire → Avancé → Expert (SPEC-MODULE-SUPERIEUR §4). **NON seedées** (ce ne sont pas des niveaux de classe), juste tracées : ressortiront quand on bâtira l'évaluation par compétences / l'observation. Identifié 12/06/2026.*

- [ ] **[Aide] Passe pro finale — qualité du contenu de toute l'aide** | En fin de parcours, hors gel
  *Les rubriques d'aide sont volontairement **légères** au fil de l'eau (on documente à chaque livraison — règle absolue `CLAUDE.md` § Aide). Une **passe dédiée en fin de parcours** étoffe TOUT le contenu : chaque rubrique complète, **exemples concrets** (entrée → sortie), ton pro, cohérence d'ensemble. Distincte de la refonte **visuelle** déjà faite (12/05, layout 2 colonnes) : ici c'est le **contenu**, pas le contenant. Absorbe les items partiels #269 (rubrique « Exemple » par outil) et #18 (aide personnalisée par matière). Identifié 12/06/2026.*

- [ ] **[Qualité/Supérieur] Wording « secondaire / cycle 4 » codé en dur, appliqué à tous les niveaux** | Défaut systémique (relevé 14/06) — tâche transverse, pas un patch CIEL
  *Foyers (prompts cadrant le LLM en « secondaire / cycle 4 » quel que soit le niveau) : (1) `_build_rag_prefix` (`src/prompts.py`) → « Programme MEN cycle 4 » / « attendus de fin de cycle 4 » (génération RAG) ; (2) `sequence.py` `_PROMPT_STANDARD` + (3) `_PROMPT_REMEDIATION` ; (4) `ambiguites.py` `_PROMPT` ; (5) `consigne.py` `_PROMPT` ; (6) `optimiseur.py` `_PROMPT` — tous « enseignement secondaire français (collège-lycée, 6e→Terminale) ». Cas connexe distinct : `fiches.py:287` (fiche marketing « du secondaire »). Le `{niveau}`/`{matiere}` est injecté correctement, mais le CADRAGE système contredit le Supérieur (BTS) — et contredira Crèche/Primaire. Symptôme observé (14/06) : séquence BTS CIEL correcte sur le fond mais « élèves » au lieu d'« étudiants ». Fix = paramétrer le cadrage par cycle/niveau — touche AUSSI collège/lycée. Lié à la décision #1 (RAG CIEL). **Voir aussi P5.11** (Supérieur : retirer/bloquer du menu, D16 §AUDIT) — même cluster « Supérieur à moitié supporté », **à NE PAS fusionner** (P5.11 = garde-fou menu ; ici = qualité du wording généré).*

- [ ] **[UX/Séquence] « Tester un exemple » (écran Séquence) ne couvre pas les matières CIEL** | Cosmétique, indépendant du grounding embeddings
  *Le prefill statique `_EX` (`SequenceForm.jsx`) n'a pas de clé pour Réseaux/Cybersécurité/etc. + BTS hors des listes `_LYCEE`/`_COL_BAS` → fallback thèmes Français/littérature. L'écran Activité (TexteSource → `/api/exemple-referentiel` → embeddings CIEL) n'est PAS concerné. Fix = ajouter des thèmes CIEL ou neutraliser le fallback hors-catalogue. Identifié 14/06/2026.*

- **PRINCIPE — « Tester un exemple » (écran Activité), déploiement progressif** (acté 15/06/2026)
  *Pour chaque couple matière+niveau dont le référentiel est **intégré et indexé** (1er fait : **BTS CIEL option A**), le bouton produit un **vrai texte d'exemple ancré** sur ce référentiel. Tant qu'un couple n'est **pas traité** → **modale** « Exemple non encore généré par l'application ». On avance **couple par couple**, à mesure qu'on traite chaque référentiel. C'est déjà le comportement du code ([exemple_referentiel.py](../backend/routers/exemple_referentiel.py) : couple sans référentiel → `available:false`, rien d'inventé) — la règle est ici notée pour piloter la suite.*

- [ ] **[UX/Menu] Consigne + Optimiseur : code livré mais gatés « bientôt »** | Décider : rouvrir (retirer `disabled`) ou assumer le report
  *`Sidebar.jsx` `disabled:true` sur `consigne` + `optimiseur` (et `equite`, lui PAS codé). Consigne (`/analyser-consigne` + `Consigne.jsx`) et Optimiseur (`/optimize-sequence`, bouton inline `SequenceForm`) sont fonctionnels mais invisibles au prof. Identifié 14/06/2026.*

- [ ] **[Décision RAG] Brancher le référentiel CIEL sur `/api/generate` — décision #1, OUVERTE** | Discutée 14/06, reportée, non tranchée — ne pas perdre
  *Aujourd'hui `/api/generate` n'active le RAG que si `RAG_ENABLED=true` ET matière∈{maths} ET niveau∈{5e,4e,3e} → RAG éteint pour tout CIEL. 3 options pesées : (a) branche CIEL dédiée + préfixe référentiel-aware (reco) ; (b) élargir le gate (cassé tel quel) ; (c) ne rien faire. Prérequis : régler aussi le défaut [Qualité/Supérieur]. Relève de Chantier B (TRACKER l.123). Identifié 14/06/2026.*

- [ ] **[Vérif/Prod] Valeur de `RAG_ENABLED` dans le `.env` prod (VPS) inconnue** | À vérifier — dit seulement si maths cycle 4 a le RAG actif en prod ; sans effet sur CIEL. Identifié 14/06/2026.

---

## AUDIT — Mes outils → Créer → Activité (15/05/2026)

> Audit complet de la fonctionnalité. 11 issues identifiées, classées P1-P5 par gravité × urgence. Workflow point par point avec validation à chaque étape.

### Livré

- [x] **P1.1** — Erreurs OCR (TexteSource.jsx) basculées de div inline vers modal showError + reformulation message "PDF scanné" en langage prof (backend/routers/ocr.py)
- [x] **P1.2** — Deux alert() natifs de la dictée (micro refusé + navigateur non supporté) basculés vers showError
- [~] **P1.3 partiel** — Dictée : feedback visuel "Préparation du micro" + bip sonore (1× démarrage, 2× arrêt) via Web Audio API + bascule sur onaudiostart + buffer 400 ms + pré-chauffage AudioContext. Cas stop/redémarrage encore imparfait → voir NON RETENU.

### Triage Phase 2.3 (reprise, 31/05) — verdicts tranchés

- [x] **P2** — Auto-save activité : perte silencieuse → **modal + helper testable**. **FAIT** (Phase 2.1, commit `95fec11`).
- [x] **P3.4** — `generate.py` : distinguer 401 / clé inconnue / Groq down (vs `except Exception` → 500). → **FAIT (08/06)** : `ValueError → 400` (clé inconnue, signal distinct du `KeyError` `.format()` réservé à P3.6) / `RuntimeError`+`RequestException` → 502 (Groq down) ; happy path inchangé. Filet **14 → 17 verts** (baseline réel 14, pas 17). Commit `f8d9317`.
- [x] **P3.6** — Protéger contre `KeyError` quand `nb` manque pour une activité qui l'exige (App.jsx:272 + prompt). → **FAIT (11/06)** : `build_prompt` (`src/prompts.py`) entoure le `.format()` ; liste blanche `_USER_PARAMS = {nb, sous_type}` (params prof, supprimés par le frontend s'ils sont vides) → `ValueError → 400` (message clair, modale prof) ; tout autre placeholder manquant = bug template/code → re-levé → 500 (jamais masqué en faux 400). `generate.py` inchangé. Filet **17 → 19 verts**.
- [ ] **P5.11** — Niveau « Supérieur » non supporté (= item #21, non entamé). → **CORRIGER** · ordre 3 · **clarifier d'abord** : retirer du menu vs bloquer le bouton (ne pas présumer).
- [ ] **P3.5** — Sur 401, rediriger vers /login. → **CORRIGER** · ordre 4 (le + sensible) · **relire le flux refresh token avant** (risque de boucle 401→login→retry→401).
- [ ] **P4.7** — Compteur few-shot `localStorage` → backend (désynchro toast vs BDD). → **SOUS-D** (refactor d'état, socle de l'item 40).
- [ ] **P5.10** — Centraliser la liste MATIERES (DRY, 3 endroits). → **SOUS-D** (refactor, isoler la régression).
- [ ] **P4.8** — Aligner carte Activité sur pattern btn-primary (App.jsx:606-614). → **GARDER/DÉFER** (cosmétique, backlog gelé).
- [ ] **P4.9** — Toast informatif au reset params (changement matière, App.jsx:225-231). → **GARDER/DÉFER** (mini-UX, backlog gelé).

> **TEMPS 2** (corrections une par une, filet vert entre chaque) — ordre : **P3.4 → P3.6 → P5.11 → P3.5**.

---

## ITEMS — Résumés (détails complets dans `BOUSSOLE/Dxx`)

### Pré-requis transverses (hors numérotation L)

<a id="infra-rag"></a>
- [~] **INFRA-RAG — Pile RAG mutualisée** | 1 session restante — DEV branché et validé, prod non décidée
  *Pile commune `backend/rag/` (singleton ChromaDB + sentence-transformers + fonction `retrieve` générique). Branchée sur `/api/generate` avec gates (matière/niveau/feature flag) + fallback silencieux + logs INFO. **Test 4 validé en DEV le 15/05** : canary `Z36-27` injecté puis retrouvé cité 4 fois dans la sortie LLM (preuve que les chunks influencent vraiment la génération) ; wording du préfixe RAG renforcé (avant : 0 marqueur institutionnel MEN dans la sortie / après : 14+ marqueurs « compétences », « connaissances », « attendus cycle 4 », sources `[BOEN_..., page X]`). Livrable une fois, réutilisée par tous les producteurs de corpus (item 36 MEN, item 30 DYS/FLE, item 04 équité, item 31 communication, item 34 créativité) et tous les consommateurs (L1, L25, Générateur d'activités). Hors numérotation L — infra pure, pas un levier. Reste : hébergement chroma_db côté VPS, opti cold start sentence-transformers, branchement L1 (séquences) et autres consommateurs.*
  → [INFRA-RAG](RAG/INFRA-RAG.md)

### Items numérotés

<a id="item-01"></a>
- [ ] **01 — Pages légales CNIL — placeholders [À COMPLÉTER]** | En attente infos admin
  *4 pages légales rédigées dans `CNIL/`. Bloqué par délais administration française (forme juridique, SIRET, etc.). À compléter dès réception + intégrer dans React (4 routes + liens footer).*
  → [D39](BOUSSOLE/D39.md)

<a id="item-02"></a>
- [ ] **02 — Email admin → prof** | Facile | 2h
  *Bouton "Contacter" dans AdminFeedbacks + 3 templates (Traité / Précision / Remerciement). Endpoint `POST /api/admin/feedbacks/{id}/email`.*
  → [D42](BOUSSOLE/D42.md)

<a id="item-03"></a>
- [x] **03 — Analyseur de consignes (L5)** | Livré 14/05
  *5 axes (clarté, précision didactique, ambiguïté, structure, erreurs typiques) + version optimisée. Backend + frontend en place.*
  → [D17](BOUSSOLE/D17.md)

<a id="item-04"></a>
- [ ] **04 — Détecteur d'équité pédagogique** | Facile | 1 session
  *Audit d'une évaluation → 3 biais (contenu, difficulté, émotionnel). Grounding RAG sur charte de la laïcité + référentiels équité — infra commune avec [D24](BOUSSOLE/D24.md).*
  → [D17](BOUSSOLE/D17.md)

<a id="item-05"></a>
- [ ] **05 — Page /contact** | Facile | 2h
  *Remplace l'adresse email brute dans le footer — réduit le spam.*
  → [D29](BOUSSOLE/D29.md)

<a id="item-06"></a>
- [ ] **06 — Civilité M./Mme dans le profil** | Facile | 2h
  *Personnalisation de l'en-tête. Absorbé par Mon Profil.*
  → [D30](BOUSSOLE/D30.md)

<a id="item-07"></a>
- [ ] **07 — Onboarding email J+2 / J+7 / J+14** | Moyen | 3 jours
  *APScheduler installé, J+0 welcome existe. Relances J+2/J+7/J+14 = impact rétention direct.*
  → [D40](BOUSSOLE/D40.md)

<a id="item-08"></a>
- [ ] **08 — Analyse des notations Groq** | Facile | 1 jour
  *Un prompt + un bloc dans AdminFeedbacks. Utile dès 15 retours pour orienter le produit.*
  → [D43](BOUSSOLE/D43.md)

<a id="item-10"></a>
- [ ] **10 — Timeouts sessions** | Facile | 2h
  *Sessions trop longues signalées. À traiter séparément — ne pas toucher à l'auth sans analyse préalable.*
  → [D31](BOUSSOLE/D31.md)

<a id="item-11"></a>
- [ ] **11 — Fiche de révision Français + Fiche pédagogique HG** | Facile | 30 min
  *Deux types d'activités manquants à ajouter dans la matrice (sur le modèle des autres matières).*
  → [D45](BOUSSOLE/D45.md)

<a id="item-12"></a>
- **12 — Synchronisation pages afia.fr ↔ projets** | règle permanente (pas un chantier)
  *Claude génère le contenu mis à jour de School.jsx (AFIA-FR) à chaque push MINOR ou MAJOR — prêt à coller.*
  → règle permanente — voir CLAUDE.md (§ Synchronisation afia.fr — Règle absolue)

<a id="item-14"></a>
- [ ] **14 — Bouton "Partagez avec vos collègues"** | Moyen | 1 session
  *Prof envoie invitation par email. Backend `POST /api/partager/` (max 5 adresses/jour). Modale `PartagerCollègues.jsx`.*
  → [D41](BOUSSOLE/D41.md)

<a id="item-15"></a>
- [ ] **15 — Gestion emails sortants — backoffice admin** | Moyen | 1-2 sessions
  *Journal envois + stats + bounces → liste noire + lien désinscription. Prérequis : SMTP transactionnel (Brevo/Resend).*
  → [D46](BOUSSOLE/D46.md)

<a id="item-16"></a>
- [x] **16 — Ambiguité → Créer une séquence** | Facile | 1h
  *Bouton "Créer une séquence →" sur chaque reformulation corrigée → pré-remplit le thème.*
  → [D33](BOUSSOLE/D33.md)

<a id="item-17"></a>
- [ ] **17 — Quiz interactif élèves** | Difficile | 2 semaines
  *Prof génère QCM → lien public → élèves répondent sur téléphone → résultats live. Différenciateur fort. Spec v1 validée 07/05.*
  → [D34](BOUSSOLE/D34.md)

<a id="item-18"></a>
- [ ] **18 — Aide spécifique par matière** | Moyen | 3-5 jours
  *Infrastructure prête (subject en BDD). Textes d'aide adaptés selon le profil prof.*
  → [D35](BOUSSOLE/D35.md)

<a id="item-19"></a>
- [ ] **19 — Admin — Menu Activités en groupe** | Facile | 2h
  *Prépare la modération des activités partagées. Pattern `group: true` déjà disponible dans AdminLayout.*
  → [D44](BOUSSOLE/D44.md)

<a id="item-20"></a>
- **20 — Projet demo-perf — FastAPI + PostgreSQL** | hors-périmètre aSchool
  *Projet technique séparé (hors aSchool), non suivi comme chantier ici. Conservé pour mémoire : stack FastAPI async + PostgreSQL + Docker, tests de charge (index, pagination, N+1, connection pool).*

<a id="item-21"></a>
- [ ] **21 — Support niveau Supérieur (BTS/prépa/licence)** | Difficile | 2 semaines
  *Ouvre un segment nouveau (formateurs BTS/prépa). Surtout du travail de prompts et d'activités.*
  → [D36](BOUSSOLE/D36.md)

<a id="item-22"></a>
- [ ] **22 — Théâtre — 13e matière** | Moyen | 1-2 semaines
  *Activités dans MATRICE_ACTIVITES + parse_markdown.py. Prérequis : trouver un prof pilote théâtre.*
  → [D47](BOUSSOLE/D47.md)

<a id="item-23"></a>
- [ ] **23 — Escape Game pédagogique** | Difficile | 2-3 semaines
  *Prof choisit matière + niveau + thème → scénario + énigmes + épreuve finale. HTML imprimable.*
  → [D37](BOUSSOLE/D37.md)

<a id="item-24"></a>
- [ ] **24 — Google OAuth** | Difficile | 2-3 semaines
  *Réduit la friction d'inscription. Inutile avant validation des pilotes.*
  → [D32](BOUSSOLE/D32.md)

<a id="item-25"></a>
- [ ] **25 — Cohérence curriculaire inter-disciplines** | Difficile | 2-3 sessions
  *Aligne notions et progressions entre matières. 3 étapes : structurer programmes MEN, similarité sémantique inter-notions, définir la sortie. Approche : commencer 1 matière × 1 niveau. Grounding RAG mutualisé avec [D24](BOUSSOLE/D24.md).*
  → [D25](BOUSSOLE/D25.md)

<a id="item-26"></a>
- [ ] **26 — Pipeline qualité automatique** | Moyen | progressif
  *Assemblage des 6 leviers en un rapport qualité synthétique. Se construit au fil des leviers livrés.*
  → [D17](BOUSSOLE/D17.md)

<a id="item-27"></a>
- [ ] **27 — Validation texte source par LLM (Option B)** | Facile | 2h
  *Appel Groq pré-génération : "texte pédagogique exploitable ?" → JSON `{valide, raison}`. À implémenter quand Option A (heuristique livrée 13/05) montrera ses limites.*
  → [D38](BOUSSOLE/D38.md)

<a id="item-28"></a>
- [ ] **28 — Stratégie de remédiation** | Facile | 0,5 session
  *Étend L2 : pour chaque ambiguïté détectée, ajouter contre-exemple + activité de remédiation + formulation alternative. Modifie prompt L2 + ajuste Ambiguites.jsx. Pas de nouveau endpoint.*
  → [D17](BOUSSOLE/D17.md)

<a id="item-29"></a>
- [ ] **29 — Mode expérience prof (T1 / confirmé / expert)** | Facile | 0,5 session
  *1 champ `experience` en BDD + variable injectée dans tous les prompts. T1 = détaillé ; expert = condensé. Plus on attend, plus il manque partout.*
  → [D18](BOUSSOLE/D18.md)

<a id="item-30"></a>
- [ ] **30 — Différenciation DYS / FLE / approfondissement** | Moyen | 1 session
  *3 variantes d'une activité après génération : DYS (syntaxe épurée + OpenDyslexic), FLE (vocabulaire simplifié), approfondissement (nuances). 3 boutons dans ZoneResultat + 3 modificateurs de prompt. Grounding RAG sur guides MEN inclusion — infra commune avec [D24](BOUSSOLE/D24.md).*
  → [D23](BOUSSOLE/D23.md)

<a id="item-31"></a>
- [ ] **31 — Appréciations bulletins & communication parents** | Moyen | 1 session
  *Nouvelle section "Communication" dans Mes Outils + 4 prompts (appréciation bulletin, mail parents, compte-rendu, libre). 360 appréciations/an par prof — justifie l'abonnement. Grounding RAG sur guides communication aux familles.*
  → [D19](BOUSSOLE/D19.md)

<a id="item-32"></a>
- [ ] **32 — Visuels Mermaid / SVG** | Moyen | 1 session — prérequis de 33 et 34
  *Texte → SVG via librairie Mermaid. Frontend `npm install mermaid` + auto-rendu. Backend : 4 prompts (frise, séquence, carte conceptuelle, arbre). Pas d'IA d'images. Débloque le mémo flash (33) et les supports de créativité (34).*
  → [D20](BOUSSOLE/D20.md)

<a id="item-33"></a>
- [ ] **33 — Mémo flash (format révision rapide)** | Facile | 0,5 session — après 32
  *Format ultra-condensé recto/verso, distinct de la fiche de révision classique. 1 nouveau type dans MATRICE_ACTIVITES + prompts. Avec le moteur visuel (32) : version carte mentale visuelle.*
  → [D21](BOUSSOLE/D21.md)

<a id="item-34"></a>
- [ ] **34 — Supports de créativité élève** | Moyen | 1 session — après 32
  *4 types multi-matières : amorces d'écriture, situations-problèmes, défis structurés, canevas BD (nécessite le moteur visuel, 32). Grounding RAG sur recherche pédagogique créativité.*
  → [D22](BOUSSOLE/D22.md)

<a id="item-35"></a>
- [ ] **35 — Versioning & transposition de séquences** | Difficile | 3 sessions
  *Permettre au prof de réutiliser/adapter une séquence existante au lieu de la régénérer — c'est le vrai moat. Nouvelle table `sequence_versions`, transposition automatique d'un niveau à l'autre, UI fork dans l'historique. Prérequis : [D07](BOUSSOLE/D07.md) (mécanique versions éphémère).*
  → [D26](BOUSSOLE/D26.md)

<a id="item-36"></a>
- [ ] **36 — Corpus Programmes MEN (producteur RAG)** | Moyen-Difficile | 3,5-5 sessions restantes — 1/96 docs indexés
  *Producteur de la collection `corpus_programmes_men` (~96 docs, 12 matières × 8 niveaux + programme 2026 cycle 4 progressif). Consommateurs : L1, L25, Générateur d'activités. Contrainte critique : coexistence 2020/2026 sur 3 ans → filtrage par métadonnée `programme` + `niveau` + `matiere` obligatoire. Prérequis : [INFRA-RAG](RAG/INFRA-RAG.md). État actuel : collection `maths_cycle4` indexée via POC, 95 docs restants.*
  → [D24](BOUSSOLE/D24.md) (volumétrie corpus, pipeline ingestion, contrainte 2020/2026, test d'éval binaire, risques hétérogénéité sources)

<a id="item-37"></a>
- [ ] **37 — Affinage interactif de séquence (instruction prof + versions éphémères)** | Moyen | 1 session — code dormant / parké (D07)
  *Le prof pilote l'affinage par instruction libre ("phase 3 trop courte", "remplace par jeu de rôle"). Bouton "Affiner" + zone saisie texte/dictée + mini-pagination V1/V2/Vn. State React, perdu au refresh. Nouveau `POST /api/affiner-sequence`. Prérequis de [D26](BOUSSOLE/D26.md).*
  → [D07](BOUSSOLE/D07.md)

<a id="item-38"></a>
- [ ] **38 — Sortie séquence en JSON structuré (rendu pro)** | Moyen | 1 session — après 37
  *Passe du markdown brut à un JSON typé + rendu React avec cartes par phase, badges durée, code couleur par type d'organisation. Migration douce (fallback markdown). Facilite [D07](BOUSSOLE/D07.md) et [D26](BOUSSOLE/D26.md).*
  → [D27](BOUSSOLE/D27.md)

<a id="item-39"></a>
- [ ] **39 — Switch provider séquence → Claude Sonnet 4.6** | Facile | 2h — après 38
  *Évaluer Claude Sonnet 4.6 vs Groq llama-3.3-70b sur la génération de séquences. Ajouter `anthropic_client.py` + toggle ou variable `AI_PROVIDER_SEQUENCE`. Coût ~3$/Mtok input à monitorer.*
  → [D28](BOUSSOLE/D28.md)

<a id="item-40"></a>
- [ ] **40 — Signe distinctif « aSchool vous reconnaît » près du nom du prof** | Facile | 0,5 session — à scorer
  *Dès l'activation du few-shot (message « aSchool reconnaît maintenant votre façon de travailler… », `App.jsx:296`, au 3e save d'un même type), afficher un signe distinctif **persistant près du nom du prof dans le Header**. À trancher à l'implémentation : badge **global** (reconnu sur ≥1 type) ou **par type / compteur** ; source de l'état pour persister entre sessions (le `localStorage` par type actuel, ou données few-shot backend). Idée notée 31/05 — **GELÉE pendant la reprise** (pas de feature avant cœur solide + push rouvert).*

<a id="item-41"></a>
- [x] **41 — Recherche dans la page Aide (plein-texte)** | LIVRÉ EN LOCAL (testé étages 1+2), NON DÉPLOYÉ — en attente de la prochaine version poussée en prod
  *La page Aide grossit à chaque livraison (règle « Aide rédigée à chaud »). Solution **RETENUE = Option A** — champ de recherche plein-texte en haut de Aide, filtrage live sur titre + contenu réel des sections via un `extractText` récursif mémoïsé (aucune duplication de contenu), surlignage des termes, compteur de résultats, état vide propre. Desktop : liste de résultats à plat ; mobile : filtre l'accordéon. Accessible (focus, Échap pour vider). Périmètre : 1 seul fichier `Aide.jsx`, pas de backend, pas de dépendance. Option B (palette Cmd/Ctrl+K) : V2 éventuelle par-dessus A, non prioritaire. Distinct de l'item 18 (contenu d'aide personnalisé par matière) : ici c'est de la découvrabilité/navigation. Gel levé volontairement le 08/06/2026 pour ce seul item ; **livré en local** (node:test 25/25 + build Vite + vérif usage étage 2), **non déployé** — partira dans la prochaine version poussée en prod.*

<a id="item-42"></a>
- [ ] **42 — Recherche globale dans l'application** | à cadrer | à scorer
  *Recherche transverse dans les données de l'app — distincte de l'item 41 (qui est une recherche LOCALE à la page Aide). Périmètre à définir le jour venu : chercher dans quoi exactement (activités sauvegardées, séquences, réseau des collègues…) ; touchera probablement le backend (endpoints de recherche) → chantier transverse, pas un simple composant front, à cadrer séparément. Emplacement pressenti (décidé par Harketti) : dans le HEADER, une LOUPE à côté du titre central « Générateur d'activités pédagogiques ». Au clic sur la loupe, le titre s'efface et le champ de recherche prend sa place au centre ; recherche terminée ou champ fermé (✕ / Échap), le champ disparaît et le titre réapparaît. Les autres éléments du header (matière, nom, déconnexion) ne bougent pas. Exigence (comme l'item 41) : utilisable par TOUS les profs, même peu à l'aise avec le numérique — fermeture évidente, rien de caché. Lien : le pattern codé pour l'item 41 (normalize, surlignage, ergonomie) sert de RÉFÉRENCE d'ergonomie, pas de code réutilisé tel quel (données différentes). Feature produit — soumise au gel.*

<a id="item-43"></a>
- [ ] **43 — Module Petite Enfance 0-3 ans** | FUTUR / stratégique — à scorer
  *Premier maillon de la **vision multi-niveaux** (voir § Direction produit en tête de ce document) — relié à l'autre maillon déjà amorcé, le **niveau Supérieur** ([D36](BOUSSOLE/D36.md), ex-I21) : les deux bouts de la vision (Crèche ↔ Supérieur) se maillent. Décliner aSchool pour la petite enfance 0-3 ans (crèches, micro-crèches, assistantes maternelles, EJE, CAP AEPE, PS). **⚠️ Garde-fou IA dur : l'IA ne doit JAMAIS diagnostiquer, interpréter médicalement, ni étiqueter un enfant** — rester factuelle, valoriser les progrès, proposer des activités adaptées. Spec complète + détail → [D48](BOUSSOLE/D48.md).*

<a id="item-44"></a>
- [ ] **44 — Bouton « Encoder » : ingestion autonome de référentiels par l'admin** | INFRA / Admin — à cadrer
  *Aujourd'hui, vectoriser un référentiel dans le RAG passe par un script dev lancé à la main (`backend/rag/ingest_referentiel.py`) → chaque nouveau référentiel exige une intervention dev. **Cible : un bouton « Encoder » côté backoffice admin** qui ingère un référentiel **de bout en bout SANS dev** (admin autonome). Deux piliers actés en réflexion : (1) le mapping « blocs du référentiel → matières » devient une donnée **ÉDITABLE** (plus du code en dur — l'admin l'ajuste) ; (2) le dev n'intervient plus que pour l'**EXCEPTION** (cas non prévu). Socle déjà en place : la procédure BTS CIEL (slice 1, métadonnée niveau) + INFRA-RAG. Distinct de l'ingestion elle-même (déjà faite) : ici la valeur, c'est l'**AUTONOMIE** de l'admin. Noté 13/06/2026, sorti des notes pour ne pas se perdre.*

---

## NON RETENU — À reconsidérer plus tard

- **Capture d'écran intégrée dans le feedback** — Le bouton "Capturer l'écran" (API navigateur `getDisplayMedia`) a été supprimé le 12/05/2026. Problème : ne permet pas de sélectionner une zone précise — capture l'écran entier, une fenêtre ou un onglet, ce qui est inutile et trompeur pour un prof. Utilisateur non satisfait. Solution envisagée : script Python local (mss + tkinter) permettant de dessiner un rectangle comme le Snipping Tool Windows, le prof uploade ensuite le PNG via le formulaire. À reprendre en session dédiée quand le script Python sera prêt.

- **`logoutManager.ts` — Service de déconnexion centralisé** — Extraire la logique logout d'AuthContext vers `src/services/logoutManager.ts`. Pertinent si : (1) logout dispersé dans 5+ composants sans passer par le contexte, (2) plusieurs variantes de logout (normal / forcé admin / inactivité / SSO), (3) besoin de tests unitaires purs TS sans React. Aujourd'hui la logique est déjà centralisée dans AuthContext — ne pas créer de couche inutile. À reconsidérer si Google OAuth ou SSO est ajouté.

- **Recrutement profs pilotes via Facebook / Twitter-X** — Testé, décevant : algorithme, bruit, profil trop international pour un produit ancré dans l'Éducation nationale française. À reconsidérer si quelqu'un d'autre reprend la stratégie d'acquisition.

- **Générateur de trajectoires multi-séances** — Extension naturelle de L1 (Mode 3). Quand L1 sera solide, ajouter "trajectoire sur plusieurs semaines" est l'évolution logique.

- **Laboratoire de Simulation de Classe** — Le prof teste sa séance sur une classe virtuelle IA avant de la donner en vrai. Vision long terme : nécessite un moteur de simulation interactif, pas juste un générateur de documents.

- **Modal multi-actions (showConfirm Oui/Non)** (audit 15/05) — Le système actuel `showError(msg)` ne supporte qu'un bouton OK. Pattern à implémenter pour modales Oui/Non avec navigation (ex : *"Voulez-vous consulter l'aide ?"* depuis le message d'erreur micro refusé). Touche `errorDialog.js` + `App.jsx` (état modal enrichi) + propagation `onOpenAide` aux composants.

- **STT Phase 3.1 — Latence Deepgram (tune `endpointing_ms`)** (audit 17/05) — Default actuel 800ms, le prof perçoit un délai entre fin de phrase et apparition du final. Tester valeurs 300-500ms pour réduire la latence sans casser la qualité de segmentation. Risque : phrases découpées prématurément. À benchmarker sur dictée réelle de 5-10 énoncés pédagogiques.

- **STT Phase 3.1 — Position visuelle zone interim** (audit 17/05) — La zone interim jaune pâle s'affiche entre les zones d'état (Préparation/Enregistrement) et le bloc des boutons. Le prof perçoit le texte "qui apparaît en dessous des boutons puis se déplace dans la zone source" — non-intuitif. Revoir le positionnement (ex : flottante au-dessus du textarea, ou overlay) si feedback utilisateur confirme.

- **STT Phase 3.1 — Bug auth sur sessions WS longues > 2 min** (audit 17/05) — Pendant une dictée de 138s observée en smoke test, le refresh JWT AuthContext (toutes les 10 min) a renvoyé 401, invalidant le cookie `aschool_access`. Au 2e clic Dicter, la WS est rejetée pré-accept (4401 → HTTP 403 → côté client `event.code === 1006` → heuristique D15 affiche "Service saturé" alors que c'est en réalité une auth expirée). 3 pistes : (a) allonger TTL access_token, (b) fix race condition refresh tokens à usage unique, (c) refresh AuthContext sur `visibilitychange` au réveil onglet. Hors scope Phase 3.1, lié à `backend/auth.py` — à traiter Phase 5.x ou en session dédiée auth.

- **STT Phase 3.1 — D9 modal showError lourd si 3 erreurs `getUserMedia` successives** (acté 17/05) — En cas de refus permission + débranche micro + autre app occupe le micro, l'utilisateur subit 3 modales bloquantes successives. Revue prévue Phase 5.x si feedback utilisateur confirme la lourdeur → bascule vers toast non-bloquant pour erreurs récupérables.

- **STT Phase 3.1 — D14 reconnect/retry policy** (acté 17/05) — MVP = aucun retry sur close inattendu (4502/4408/1011), le prof re-clique manuellement. Revisitable Phase 4.x après observation patterns réels (saturation midsession vs ouverture, fréquence des Deepgram down).

- **STT Phase 3.1 — Q-int-1 concaténation append-only vs insertion au curseur** (acté 17/05) — Le texte dicté s'ajoute toujours à la fin du textarea, même si le prof a placé le curseur ailleurs. Choix MVP. Revisitable si feedback utilisateur sur "j'aimerais corriger une faute puis dicter à l'endroit du curseur".

- **STT Phase 4.x — Alerte admin 4402 (crédit Deepgram épuisé)** (acté 17/05) — Aujourd'hui le prof voit un modal neutre "Service de dictée temporairement indisponible" et personne côté admin n'est notifié. À câbler dans Phase 4.x (monitoring) : alerte email/dashboard admin lorsque close 4402 survient, pour pouvoir recharger le crédit Deepgram avant panne prolongée.

- **STT Phase 3.2 — Dictée Deepgram points de vigilance** (audit 16/05, partiellement traité 17/05) — Smart Format agressif (`smart_format=true`) confirmé empiriquement Phase 3.1 sur vraie voix Edge (nombres et homophones). Tester avec `smart_format=false` pour vocabulaire mathématique notationnel. Reste à valider : substitution "hypoténuse" → "hypothèse" malgré keyterm boost (besoin tests dédiés).

---

## HORS SCOPE

- **Intégration ENT / Pronote** — API propriétaires, accords institutionnels, des mois de travail
- **Tableau de bord multi-profs établissement** — Nécessite concept "établissement" en BDD + rôles
- **Migration SQLite → PostgreSQL** — Uniquement si charge réelle. SQLite tient jusqu'à 500 users actifs/jour
- **Cartographie cognitive des classes** — Nécessite que les élèves interagissent avec aSchool. Contraire à la philosophie du produit (outil prof uniquement).
- **Profilage Pédagogique Dynamique (PPD)** — Même problème + contrainte RGPD lourde sur les mineurs.

---

## Fiches livrées + commitées (à archiver dans le FAIT ci-dessous lors du dégraissage D11)

D01 (L5 Analyseur de consignes) · D02 (Optimiseur inline) · D03 (INFRA-RAG DEV) · D04 (Groq fallback) · D05 (errorDialog + niveau header) — commités le 18/05/2026. · D08 (branding `MesAdmin/` finalisé, 44/44) — commité le 19/05 (`cba2642`).

---

## FAIT ✅

- [x] **Menu « Mes outils » réagencé par levier + rubrique d'aide « organisation des outils »** | Livré 12/06
  *`Sidebar.jsx` repassé **par levier** (Activité / Séquence / Analyse, Créer + Historique groupés dans chaque levier) au lieu de par-verbe — bloc récupéré de `b257412` puis **greffé** dans le fichier actuel (pas de checkout brutal, reste intact). Les 3 outils pas prêts (Optimiser, Consignes, Équité) affichés **grisés + badge « bientôt » + tooltip**, NON cliquables (span sans handler). Code mort retiré. Commit `0e3ac52`. **Aide** : rubrique prof « Comment vos outils sont rangés » (catégorie Comprendre), collée au menu RÉEL par-levier — pas les 4 verbes (qui restent la grille interne). **Taxonomie de classement** (4 verbes Créer/Analyser/Améliorer/Adapter + critère de tri) actée en note de conception `CLAUDE.md`, commit `19c214b`. Décision par-levier validée par avis raisonné (sert l'usage récurrent du prof).*

- [x] **Seed Programmes — Crèche + Supérieur (niveaux + axes + paires) + nettoyage bruit de test** | DEV 12/06 — en attente commit (GO)
  *Crèche et Supérieur, laissés vides au seed initial, remplis depuis les référentiels (SPEC-MODULE-CRECHE §4 / SPEC-MODULE-SUPERIEUR §3 v2.1), **à l'identique de collège/lycée** : Crèche = 3 tranches d'âge × 9 axes (**27 paires**) ; Supérieur = 7 niveaux (BTS → Formation continue) × 7 axes (**49 paires**). Collision « Autonomie » (axe crèche + axe supérieur, clé unique) → clés préfixées `creche-*` / `sup-*`, libellé affiché inchangé. Seed **idempotent** (76 nouvelles, 2e passage = 0). Fichier renommé `seed_curriculum.py → seed_programmes.py` (git mv, 0 référence). Label menu/titre admin « Curriculum » → « **Programmes** ». **Nettoyage (DELETE assumé, option B validée par l'utilisateur le 12/06)** : **13 paires parasites** issues des clics de test T2 — `Français × PS` (`actif=False`, Maternelle) + les 12 matières du secondaire × `BTS` (`actif=True`, Supérieur) — **SUPPRIMÉES**. Bruit de test sans valeur d'historique, pas des entrées de référence → DELETE justifié (garde-fou : suppression seulement si compte == 13, sinon abort). Base finale **140 paires propres** (Crèche 27 / Collège 35 / Lycée 29 / Supérieur 49). Réserve « niveaux d'acquisition » (échelles d'évaluation) tracée en Dette, non seedée. **Non fait** : menu matière du profil encore **en dur** (`MonProfil.jsx:5`) → les axes seedés ne sont **pas** atteignables par le prof ; réconciliation des noms de matières + scope par cycle à planifier.*

- [x] **Alignement vocabulaire « curriculum » → « programmes » (couche technique)** | DEV 12/06 — en attente commit (GO)
  *Suite à la décision « Programmes » côté UI : on supprime l'anglicism résiduel en technique pour un vocabulaire unique. Route `/api/curriculum*` → `/api/programmes*`, fichier `routers/curriculum.py` → `programmes.py`, page `AdminCurriculum.jsx` → `AdminProgrammes.jsx` (+ composant), URL admin `/admin/curriculum` → `/admin/programmes`, et les 6 appelants frontend + tests en lockstep. Suite **24/24**, build frontend OK, **0 occurrence `curriculum`** restante dans le code. Surface interne uniquement (web cookie-auth, aucun consommateur externe). Les récits FAIT historiques gardent « curriculum ».*

- [x] **Migration des relations BDD `user_email → user_id` (expand → contract) — DEV** | Livré 11/06
  *Refonte du défaut de conception d'origine : toutes les tables liaient leurs FK sur `user_email` (clé naturelle string) au lieu de `users.id` (clé primaire numérique). Bascule par **expand/contract** (parallel change), table par table, app fonctionnelle à chaque étape, jamais de big-bang. **Outillage** : runner de migrations maison `migrations/run_migrations.py` (SQL numérotés idempotents, table `schema_migrations`, 1 transaction/fichier, `foreign_keys=ON`) + `migrations/README.md` ; pas d'Alembic. **Expand** (9 SQL `001→009`) : colonne `user_id` ajoutée + backfill déterministe `UPDATE … SET user_id=(SELECT id FROM users WHERE email=…)` sur 7 tables prof (NOT NULL visé) + 2 journaux (`connexion_logs`, `email_tokens`, `user_id` NULLABLE, colonne `email` conservée car peut viser un non-user). Dual-write `user_id` à tous les inserts ; lectures admin/stats basculées sur `user_id`/join (**4a**). **Contract** (`010`) : reconstruction SQLite des 7 tables prof → `user_id INTEGER NOT NULL REFERENCES users(id)`, **`user_email` SUPPRIMÉE**, index recréés. Vérifs sur copie puis vraie base : **0 perte** (568/4/4/101/440/0/35), FK posées, `foreign_key_check` vide, **pytest 19/19**. Backup local `data/aschool.db.bak-20260611`. Commits `9142327` (expand+4a) + `d2e28be` (contract). **Reste : intégration PROD non faite** — voir ligne 🚫 **BLOQUANT DÉPLOIEMENT** du [TRACKER](TRACKER.md) (brancher le runner dans `deploy.sh` + garde-fou backup/orphelins avant tout `deploy.ps1`).*

- [x] **Fusion BOUSSOLE + BACKLOG → `TABLEAU-DE-BORD.md` (doc pilote unique)** | Livré 11/06
  *Les deux docs pivots (BOUSSOLE = pilote, BACKLOG = réservoir) fusionnés en un seul `MesMD/TABLEAU-DE-BORD.md` : pilotage (tête) + réservoir scoré (corps) + journal FAIT (fin) ; les fiches `BOUSSOLE/Dxx` restent la couche détail. 5 phases scopées : **P1** création du doc (`fc21a86`) ; **P2** réconciliation des codes L migrés → numéro d'item (`c75be07`) ; **P3** cascade des back-links de 35 fiches Dxx → `TABLEAU-DE-BORD` (`fd0e9b4`) ; **P4** fusion des §« Pilotage » + §« Réservoir » de `CLAUDE.md` (`f62dfb2`) ; **P5** suppression de `BOUSSOLE.md` + `BACKLOG.md` + retarge INFRA-RAG + `MEMORY.md` L.34 (`d98450b`). Absorbe **D11** (dégraissage/fusion) et l'ex-item **[Doc]** (passe de réconciliation = P2). Reste en dette : nettoyage des memory files périmés (voir § Dette).*

- [x] **Accès Ambiguïtés restauré dans la sidebar + I16 (Ambiguïté → séquence) confirmé livré** | Livré 10/06
  *Deux choses tranchées le 10/06. **(a) Accès corrigé** : la section « Analyser » du menu latéral avait été **retirée volontairement le 14/05** (livraison L5, cf. entrée plus bas) — conséquence non anticipée : les outils d'analyse devenaient introuvables depuis la sidebar. Remise d'une sous-section repliable « Analyser → Ambiguïtés » dans `Sidebar.jsx` (calquée sur « Historique », couvre desktop + mobile). **Consigne et Équité restent hors sidebar** pour l'instant (périmètre volontaire : Ambiguïtés seul). Commit `c63172f`. **(b) I16 — « Ambiguïté → Créer une séquence »** : découvert **déjà entièrement codé** (bouton sur chaque carte de reformulation + dialog + câblage `App.jsx onCreateSequence` → pré-remplit le thème) ; seul l'accès manquait (point a). Vérifié de bout en bout (run Harketti). Migré en [D33](BOUSSOLE/D33.md). Commit `dd41cd6`.*

- [x] **Dictée vocale — retour à Groq Whisper batch + fix 400 + retour visuel** | Livré 31/05
  *Décision 31/05 : la dictée repasse du streaming WS Deepgram (Phase 3.2 jamais finalisée) au **POST batch Groq Whisper** (`whisper-large-v3`) — base fiable, aligné « Groq par défaut ». Deepgram conservé comme amélioration future, **isolé sur la branche `wip/deepgram-streaming`** (rien supprimé). **Fix du 400** confirmé par repro empirique : Groq détermine le format par l'**EXTENSION du nom de fichier** (un blob sans extension → 400) ET exige le paramètre **`model`** ; le backend force désormais les deux. Backend `groq_client.transcribe_audio()` + route `/api/transcribe` batch ; suppression du code mort STT (`backend/stt/*`, `seed_stt`, hook `useTranscribeStream`, tests Deepgram). **Retour visuel** pendant l'enregistrement (la vraie lacune du batch) : visualiseur de volume temps réel (AnalyserNode + 12 barres CSS pilotées par refs, zéro re-render), chronomètre, message qui pose l'attente (« le texte s'affichera à l'Arrêter »), micro SVG (plus d'emoji), bandeau « Transcription… » à l'arrêt. **Tests** : `test_transcribe.py` (garde-fou des 2 pièges du 400, via la vraie route) + `frontend/src/utils/audioViz.test.js` (`node --test` : `formatTime` + `computeBarLevels`). Détail : [D15](BOUSSOLE/D15.md).*

- [x] **Dev — cohabitation locale aSchool sur 8001** | Livré 31/05
  *Le 8000 local étant souvent occupé par un autre projet (A-VIEWCAM), `run.ps1` lance désormais aSchool sur **8001** (paramètre `-BackendPort`, défaut 8001, aligné sur l'archi VPS), **ne tue plus le 8000 voisin**, et injecte `VITE_API_PORT` au frontend. Proxy Vite rendu configurable (`vite.config.js` : `process.env.VITE_API_PORT || 8000`). Détail : [D15](BOUSSOLE/D15.md).*

- [x] **STT Deepgram — Phase 3.1 frontend WS + refactor TexteSource batch→stream** | Livré 17/05
  *Migration de la dictée vocale (ancien `POST /api/transcribe` Groq Whisper batch, route backend qui n'existait plus) vers streaming WS Deepgram Nova-3. Hook custom `useTranscribeStream` (192 lignes, frontend/src/hooks/) encapsule MediaRecorder Opus + WebSocket + cleanup en 3 endroits (unmount, stop, ws.onclose) + pivot AuthContext pour heuristique D15 (cookie httpOnly invisible à document.cookie). Refactor TexteSource (400→280 lignes) : suppression du POST batch mort, 4 visuels bouton (idle/requesting/recording/unsupported) + 3 conditions d'erreur en modal, zone interim volatile (D8 β), bips audio go/stop/warning T-60s. Patch infra `vite.config.js` (ws: true sur proxy /api). Patch backend `deepgram_provider.py` : omettre encoding/sample_rate quand cfg.encoding=opus pour que Deepgram auto-détecte le container WebM via magic bytes EBML (sinon Deepgram décode l'Opus 48k comme du 16k → zero transcript, bug découvert empiriquement après 3h de diagnostic). 8 décisions D7-D16 actées (recos non tranchées dans handoff puis validées après affinement). 16 patches de revue code appliqués (mountedRef reset au mount React 18 strict mode, ordre cleanup recorder→tracks→ws commenté, stateRef pour useCallback stables, etc.). Test test_phase22.py 7/7 PASS confirmé après patch backend (filet de sécurité Phase 2.2 intact).*

- [x] **STT Deepgram — test_phase22.py 7 scénarios robustesse route WS** | Livré 17/05
  *Tests d'intégration in-process via `fastapi.testclient.TestClient` (Option B archi — A éliminée (incompatible CI/fragile), B' pesée puis B retenu (convention scripts standalone + plumbing uvicorn évité)). 7/7 PASS confirmé en local (commit `fc09c34`). Scénarios : (1)(2) rejet pré-accept auth, (3) golden path transcript reçu, (4) saturation env override D5γ, (5) `FakeExhaustedProvider` D6 δ2 mappé en close 4402, (6) idle timeout, (7) max duration + warning `EXPIRING_SOON` à t=10s + close 4408 à t=70s. Threading nécessaire pour scénarios 3 et 7 (Starlette 1.0.0 `WebSocketTestSession.receive_*()` bloquant sans timeout natif). Sentinel `_Skipped` distinct de PASS/FAIL pour close 4502 (Deepgram down). Particularités : `ws.close()` côté client cancel les tasks serveur → `CancelledError` au teardown attrapé en outer try ssi transcript validé (bénin) ; piège idle×max neutralisé par override double `STT_SESSION_IDLE_TIMEOUT_SECONDS=120` dans scénario 7 (sinon default 30s tuerait avant warning t=10s). `test_phase21_smoke.py` conservé en parallèle (handshake via TCP loopback, complémentaire à TestClient in-process — docstrings clarifient les rôles).*

- [x] **STT Deepgram — Observabilité rejets pré-accept (R4 traitée Phase 2.2)** | Livré 16/05
  *Refactor `STTSessionTracker` (décision D5γ de la Phase 2.2) : `max_concurrent` relu live à chaque `acquire()` via helper `_read_max()` — suppression de `self._max` figé pour avoir une seule source de vérité (l'env). Permet la mutation dynamique sans restart serveur (utile pour tests scénarios saturation + future Phase 4.1 admin). Compteur agrégé R4 par catégorie de denial pré-accept exposé via `snapshot() → STTSessionSnapshot` TypedDict, à brancher dans `/admin/stt-status` Phase 4.1. **3 catégories** (élargies par rapport au scope R4 initial qui prévoyait 2) : `anonymous` (pas de cookie), `bad_token` (cookie présent mais JWT invalide/expiré), `saturated` (quota concurrence atteint, ajouté pour cohérence sémantique — la saturation est aussi un denial pré-accept, exposer 2/3 côté admin serait trompeur). 7 tests unitaires standalone (3 migrés Phase 1.4 + 4 nouveaux) : race condition strict 41/40, bump dynamique env entre acquires, concurrence 50+30+20 sur `record_pre_accept_reject`, structure snapshot, whitelist runtime defense-in-depth.*

- [x] **Branchement RAG en DEV — Générateur d'activités** | Livré 15/05
  *INFRA-RAG branchée sur `/api/generate` avec gates (RAG_ENABLED + subject Maths normalisé NFKD + niveau cycle 4) + fallback silencieux + logs INFO observables. `GenerateResponse.chunks` populé quand RAG actif. Protocole 4 tests DEV validés : (1) non-régression RAG-off, (2) gate subject Français, (3) gate niveau Terminale, (4) activation effective prouvée par canary `Z36-27` + wording du préfixe RAG renforcé pour forcer la citation explicite du vocabulaire institutionnel MEN. Fix collatéraux : logger applicatif INFO activé dans `backend/main.py`, sync `params.niveau` ↔ `user.niveau` après sauvegarde profil dans `frontend/src/App.jsx`, niveau affiché dans le header, migration manquante `ALTER TABLE sequences_sauvegardees ADD COLUMN partagee`. Mode DEV uniquement — décision hébergement chroma_db côté VPS reportée. Outil canary conservé dans `backend/rag/_canary_inject.py` (utile pour validation futurs producteurs).*

- [x] **Fiabilisation fallback Groq (413/503)** | Livré 15/05
  *Bug : optimisation séquence renvoyait 413 "Request too large" car le 1er fallback `llama-3.1-8b-instant` (TPM 6000) ne tient pas une requête d'optim (~7400 tokens). Correctif `backend/groq_client.py` : (1) ordre du fallback inversé — `gpt-oss-120b` → `gpt-oss-20b` → `8b-instant` (le moins capable en dernier recours), (2) le fallback se déclenche aussi sur 413 et 503 (plus seulement 429), (3) nettoyage variable morte `last_error`. La génération de séquence (~4500 tokens) n'était pas affectée car elle tenait sous la limite.*

- [x] **Refonte structure docs — 1 fichier par item dans `LEVIERS/`** | Livré 15/05
  *39 fichiers créés (L*.md pour leviers pédagogiques, I*.md pour items techniques/admin). BACKLOG allégé : sections détaillées remplacées par résumés courts + lien. Colonne "Détail" ajoutée au tableau global. Architecture transverse (Cat. A/B/C, mapping RAG) maintenue dans BACKLOG.*

- [x] **L5 — Analyseur de consignes** | Livré 14/05
  *Backend `POST /api/analyser-consigne` (5 axes). Frontend `Consigne.jsx` complet (8 points standard). Accessible via mes-outils → "Qualité des consignes". L2 intégré dans ZoneResultat (bouton "Ambiguïtés" → pré-remplit Ambiguites). Section "Analyser" retirée du sidebar.*

- [x] **Optimisation intégrée dans SequenceForm** | Livré 14/05
  *Bouton "Optimiser" dans la zone résultat → dialog de confirmation → appel `/api/optimize-sequence` sur place → remplace le résultat affiché. Plus de navigation vers l'écran Optimiseur séparé. Sidebar : "Créer" s'ouvre automatiquement au clic "Mes outils".*
  *Backend `optimiseur.py` : `max_tokens` 4000→6000, `temperature: 0`, `response_format: json_object` ajoutés.*
  *En cours : prompt L3 modifié pour forcer markdown avec sauts de ligne dans `sequence_optimisee` — à retester. Fichiers : `SequenceForm.jsx`, `Sidebar.jsx`, `optimiseur.py`.*

- [x] **Aide — Rubrique "Premiers pas"** | Livré 14/05
  *3 sections ajoutées dans Aide.jsx : Créer votre compte (inscription + vérif + mdp oublié), Compléter votre profil (importance profil complet), Première activité (5 étapes + exports). GUIDE_PREMIERE_CONNEXION.md supprimé — contenu intégré dans l'Aide.*

- [x] **Accueil — Réorganisation** | Livré 13/05
  *Stats déplacées vers page "Mes stats" (menu sidebar après Mes feedbacks). Page Accueil épurée : bandeau bienvenue + "Mes dernières créations" (3 sections : Activité / Séquence / Analyse raccourcis) + colonne droite CTA + lien stats + astuce. Astuce clampée à 4 lignes max (WebkitLineClamp). Backend : `/api/dashboard` renvoie désormais `derniere_sequence` (theme, matiere, niveau, duree, mode, description_classe, resultat).*

- [x] **Stats & Fréquentation — 3 blocs** | Livré 13/05
  *3 blocs distincts validés le 13/05.*

  **B1 — Stats personnelles prof** *(widget KPI page Accueil)*
  Calculées à la volée depuis données existantes : total activités générées, séquences créées, activités partagées, type favori ("votre spécialité"), estimation heures gagnées (15 min × nb activités), streak créateur (X jours consécutifs), score d'adaptation few-shot ("aSchool vous connaît à X%"), "vos partages repris X fois" (nécessite `utilise_count` en BDD).

  **B2 — Jauge communauté** *(page Accueil profs + admin)*
  Le site "bat" — effet réseau, fidélisation : "X profs actifs aujourd'hui · X activités générées cette semaine · X partages en circulation". Données anonymes, mises à jour à chaque chargement. Visible aussi dans le backoffice admin.

  **B3 — Graphe de fréquentation** *(backoffice admin + vue admin de B2)*
  Courbe connexions uniques par jour sur 30/90 jours. Histogramme heure de pointe (0h→24h). Nécessite table `connexions(user_email, created_at)` alimentée à chaque login. Couvre aussi "Historique de connexions" — une seule tâche pour deux besoins. Librairie : Recharts.

  > **Note : réfléchir à d'autres stats** pertinentes pour les profs et l'admin (ex : taux de partage, matières les plus actives, progression mensuelle…)

- [x] **Aide — Sections Historique Activités / Séquences / Mon réseau** | Livré 13/05
  *4 nouvelles sections dans Aide.jsx : Historique des activités (Plus de détails, Reprendre, Partager, Supprimer), Historique des séquences (idem + choix anonymat + badge Partagé), Mon réseau (Activités et Séquences partagées, Utiliser). Section Partager mise à jour avec nouveau flow anonymat. Catégorie "Gérer" ajoutée dans la nav.*

- [x] **Alignement noms UI ↔ code** | Livré 13/05
  *`bibliotheque` → `mon-reseau` partout : composants (`MonReseau.jsx`, `MonReseauSequences.jsx`), page IDs, routes API (`/api/mon-reseau`, `/api/mon-reseau/sequences`), Sidebar. Bug `seqFormVisible` supprimé. CORS `school.afia.fr` → `aschool.fr` dans main.py et deploy.sh. Règle de cascade ajoutée dans CLAUDE.md.*

- [x] **Nettoyage code mort** | Livré 13/05
  *`Bibliotheque.jsx` et `BibliothequeSequences.jsx` supprimés. Références `BIBLIOTHEQUE_PAGES`, `IconBibliotheque` renommées. Ancienne page ID `'bibliotheque'` (vestige) retirée de App.jsx.*

- [x] **L2 — Détecteur d'ambiguïtés cognitives** | Livré
  *Analyse un exercice ou énoncé → zones de risque d'incompréhension + reformulations corrigées. Composant Ambiguites.jsx fonctionnel, intégré dans Mes outils → Analyse.*

- [x] **FB1 — Page Mes feedbacks** | Livré 12/05
  *Page sidebar "Mes feedbacks". 2 onglets : Envoyer / Mes retours. Upload multi-fichiers (PNG/JPEG/PDF, max 5Mo, max 5 fichiers), drag&drop + Parcourir. Bouton Modifier si statut nouveau/en_cours. Capture écran via Win+Maj+S (message d'aide intégré). Aide rédigée à chaud (section "Mes feedbacks" dans Aide.jsx).*

- [x] **Mon réseau (ex-Ma bibliothèque)** — Accordéon sidebar avec 2 sous-menus : Activités / Séquences. Partage des séquences + choix anonymat (Afficher mon nom / Rester anonyme) au moment du partage. Label "Partages de vos collègues" + bulle d'aide dans les deux pages. "Plus de détails" modal dans les deux pages. (13/05)
- [x] **Historique Activités — normalisé** — Modale "Plus de détails" fond sombre, bouton "Reprendre" (ex-Charger), suppression avec confirmation. (13/05)
- [x] **Historique Séquences — normalisé** — Modale "Plus de détails" fond sombre, bouton "Partager" + choix anonymat, suppression avec confirmation. (13/05)
- [x] **Blocage profil incomplet** — Modal bloquant dans App.jsx si prenom ou nom manquant — redirige vers Mon profil. (13/05)
- [x] **Mon journal supprimé** — Placeholder inutile (doublon Historique Activités/Séquences) retiré de sidebar et App.jsx. (13/05)
- [x] **Analyse → Historique supprimé** — Sous-menu inutile (analyses one-shot ; à l'époque Consignes/Équité non exposés). (13/05) — *MàJ 14/06 : Consigne a depuis été codée (14/05) mais reste gatée « bientôt » ; Équité toujours non codée. Cf. réservoir [UX/Menu].*

- [x] **Auto-versioning PATCH** — deploy.ps1 bumpe automatiquement le PATCH à chaque déploiement. Version initiale : 3.2.0 (12/05)
- [x] **SW mise à jour — bannière bordeaux + countdown 30s** — registerType: prompt, auto-reload 30s, bouton "Actualiser maintenant" (12/05)
- [x] **Aide — Sections complètes** — PWA offline, PWA update, Dictée vocale, OCR, Partage activités, Séquences corrigé (L1 live) (12/05)
- [x] **Bientôt disponible — mis à jour** — L2 + L4 ajoutés, Application mobile retirée (PWA livrée), sidebar "En développement" à jour (12/05)
- [x] **Aide — Refonte visuelle pro** — Layout 2 colonnes desktop, accordéon mobile inchangé (12/05)
- [x] **PWA — Complète** — Installabilité iOS, SW, responsive toutes pages, polish mobile, tests post-prod validés (12/05)
- [x] **PWA — Checklist QA complète** — 20/35 points validés en dev, 15 prod vérifiés (12/05)
- [x] **L3 — Optimiseur de séquences** — `POST /api/optimize-sequence`, 6 critères, séquence optimisée + score (11/05)
- [x] **L1 — Générateur d'orchestrations** — `POST /api/generate-sequence`, Mode standard + Mode remédiation (11/05)
- [x] **Analytique admin — 4 sous-pages** — Vue générale / Activités / Outils / Communauté (11/05)
- [x] **Menu Mes Outils amélioré** (11/05)
- [x] **Filtre automatique Mes activités par profil** — Suppression dropdowns, badge compteur bordeaux (09/05)
- [x] **Tableau analytique admin** — KPI cards, tableau prof×matière×niveau×type, top 20 types (09/05)
- [x] **Widget stats communauté** — Total plateforme + nb profs + top 3 types (09/05)
- [x] **Fiches Matières** — Backend + Frontend (09/05)
- [x] **Rebranding aSchool + migration domaine** — aschool.fr en production, school.afia.fr obsolète (11/05)
- [x] **Logo et icône finalisés** (09/05)
- [x] **Bibliothèque complète** — 73 exemples, 100% des couples matière×niveau (08/05)
- [x] **Comptes non vérifiés en admin** — Badge jaune, filtre, boutons Valider/Email/Supprimer (08/05)
- [x] **Page Maintenance BDD** — /admin/maintenance, 7 catégories orphelines, boutons Purger (08/05)
- [x] **Mail groupé admin** — /admin/communication, cases à cocher, filtre, SMTP, audit (07/05)
- [x] **Documents légaux CNIL** — ML, PC, CGU, cookies, PL finalisés dans CNIL/ (07/05)
- [x] **Partage d'activités entre collègues** — Bibliothèque + toggle partage par activité (07/05)
- [x] **Backoffice admin complet** — Sessions live, brute force, audit trail, alertes auto (02/05)
- [x] **Few-shot adaptation au style prof** — Adapte le style après 3 saves du même type (30/04)
- [x] **Export PDF** — window.print() dans ZoneResultat.jsx
- [x] **Pied de page .docx + impression CSS + signature mailto**
- [x] **Compteur "X activités créées"** — Badge bordeaux sur le total filtré par profil

---

[CLAUDE.md (règles)](../CLAUDE.md)
