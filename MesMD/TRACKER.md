# aSchool — TRACKER

> **Source de vérité unique.** Toute idée, tâche ou livraison est ici — nulle part ailleurs.
> Specs techniques détaillées → `LEVIERS/`

> Note dev : Bannière "Bientôt disponible" sidebar prof → `Sidebar.jsx`, bloc `{!collapsed && ...}` en bas.

> **Règle Aide :** Dès qu'une fonctionnalité est livrée, sa section Aide est rédigée dans la même session — à chaud, pendant que c'est frais. Jamais en retard.

---

## BACKLOG — Vue globale

> Tableau trié par **Score = Valeur + Faisabilité** (meilleur ROI en premier). Quand un item est livré → ~~barrer la ligne~~ + déplacer dans FAIT. La trace reste visible.

> **Leviers livrés en production :** L1 — Générateur d'orchestrations · L2 — Détecteur d'ambiguïtés cognitives · L3 — Optimiseur de séquences

> **Pré-requis transverse :** INFRA-RAG (pile RAG mutualisée) — codé en mode DEV, pas branché. Voir section *DÉCISION D'ARCHITECTURE — RAG* ci-dessous et fiche [INFRA-RAG](RAG/INFRA-RAG.md).

| # | Titre | Effort | Valeur | Faisabilité | Score | Section | Détail | ✅ |
|---|---|---|---|---|---|---|---|---|
| [35](#item-35) | Versioning & transposition de séquences | 3 sessions | ★★★★★ | ★★★★★ | **10/10** | IMPORTANT | [L35](LEVIERS/L35.md) | ☐ |
| [37](#item-37) | Affinage interactif de séquence (instruction prof + versions éphémères) | 1 session | ★★★★★ | ★★★★★ | **10/10** | IMPORTANT — chantier en cours | [L37](LEVIERS/L37.md) | ☐ |
| [36](#item-36) | Corpus Programmes MEN (producteur RAG) | 3,5-5 sessions restantes | ★★★★★ | ★★★★☆ | **9/10** | OPTIONNEL | [L36](LEVIERS/L36.md) | ☐ |
| [38](#item-38) | Sortie séquence en JSON structuré (rendu pro) | 1 session | ★★★★☆ | ★★★★☆ | **8/10** | IMPORTANT — après 37 | [L38](LEVIERS/L38.md) | ☐ |
| [39](#item-39) | Switch provider séquence → Claude Sonnet 4.6 | 2h | ★★★☆☆ | ★★★★★ | **8/10** | OPTIONNEL — après 38 | [L39](LEVIERS/L39.md) | ☐ |
| [03](#item-03) | Analyseur de consignes | 1 session | ★★★★☆ | ★★★★★ | **9/10** | Mes Outils | [L03](LEVIERS/L03.md) | ☑ |
| [04](#item-04) | Détecteur d'équité pédagogique | 1 session | ★★★★☆ | ★★★★★ | **9/10** | Mes Outils | [L04](LEVIERS/L04.md) | ☐ |
| [28](#item-28) | Stratégie de remédiation | 0,5 session | ★★★★☆ | ★★★★★ | **9/10** | Mes Outils | [L28](LEVIERS/L28.md) | ☐ |
| [33](#item-33) | Mémo flash (format révision rapide) | 0,5 session | ★★★★☆ | ★★★★★ | **9/10** | IMPORTANT — après 32 | [L33](LEVIERS/L33.md) | ☐ |
| [07](#item-07) | Onboarding email J+2 / J+7 / J+14 | 3 jours | ★★★★☆ | ★★★★☆ | **8/10** | IMPORTANT | [I07](LEVIERS/I07.md) | ☐ |
| [14](#item-14) | Bouton "Partagez avec vos collègues" | 1 session | ★★★★☆ | ★★★★☆ | **8/10** | OPTIONNEL | [I14](LEVIERS/I14.md) | ☐ |
| [30](#item-30) | Différenciation DYS / FLE / approfondissement | 1 session | ★★★★☆ | ★★★★☆ | **8/10** | IMPORTANT | [L30](LEVIERS/L30.md) | ☐ |
| [32](#item-32) | Visuels Mermaid / SVG | 1 session | ★★★★☆ | ★★★★☆ | **8/10** | IMPORTANT — prérequis 33+34 | [L32](LEVIERS/L32.md) | ☐ |
| [02](#item-02) | Email admin → prof (3 templates) | 2h | ★★★☆☆ | ★★★★★ | **8/10** | IMPORTANT | [I02](LEVIERS/I02.md) | ☐ |
| [08](#item-08) | Analyse des notations Groq | 1 jour | ★★★☆☆ | ★★★★★ | **8/10** | IMPORTANT | [I08](LEVIERS/I08.md) | ☐ |
| [11](#item-11) | Fiche de révision Français + Fiche pédagogique HG | 30 min | ★★★☆☆ | ★★★★★ | **8/10** | IMPORTANT | [I11](LEVIERS/I11.md) | ☐ |
| [16](#item-16) | Ambiguité → Créer une séquence | 1h | ★★★☆☆ | ★★★★★ | **8/10** | OPTIONNEL | [I16](LEVIERS/I16.md) | ☐ |
| [27](#item-27) | Validation texte source par LLM (Option B) | 2h | ★★★☆☆ | ★★★★★ | **8/10** | OPTIONNEL | [I27](LEVIERS/I27.md) | ☐ |
| [31](#item-31) | Appréciations bulletins & communication parents | 1 session | ★★★☆☆ | ★★★★★ | **8/10** | IMPORTANT | [L31](LEVIERS/L31.md) | ☐ |
| [17](#item-17) | Quiz interactif élèves | 2 semaines | ★★★★★ | ★★☆☆☆ | **7/10** | OPTIONNEL | [I17](LEVIERS/I17.md) | ☐ |
| [21](#item-21) | Support niveau Supérieur (BTS/prépa/licence) | 2 semaines | ★★★★☆ | ★★★☆☆ | **7/10** | OPTIONNEL | [I21](LEVIERS/I21.md) | ☐ |
| [24](#item-24) | Google OAuth | 2-3 semaines | ★★★★☆ | ★★★☆☆ | **7/10** | OPTIONNEL | [I24](LEVIERS/I24.md) | ☐ |
| [26](#item-26) | Pipeline qualité automatique | progressif | ★★★★☆ | ★★★☆☆ | **7/10** | OPTIONNEL | [L26](LEVIERS/L26.md) | ☐ |
| [10](#item-10) | Timeouts sessions | 2h | ★★★☆☆ | ★★★★☆ | **7/10** | IMPORTANT | [I10](LEVIERS/I10.md) | ☐ |
| [18](#item-18) | Aide spécifique par matière | 3-5 jours | ★★★☆☆ | ★★★★☆ | **7/10** | OPTIONNEL | [I18](LEVIERS/I18.md) | ☐ |
| [23](#item-23) | Escape Game pédagogique | 2-3 semaines | ★★★☆☆ | ★★★★☆ | **7/10** | OPTIONNEL | [I23](LEVIERS/I23.md) | ☐ |
| [29](#item-29) | Mode expérience prof (T1 / confirmé / expert) | 0,5 session | ★★★☆☆ | ★★★★☆ | **7/10** | Mes Outils | [L29](LEVIERS/L29.md) | ☐ |
| [34](#item-34) | Supports de créativité élève | 1 session | ★★★☆☆ | ★★★★☆ | **7/10** | IMPORTANT — après 32 | [L34](LEVIERS/L34.md) | ☐ |
| [01](#item-01) | Pages légales CNIL — placeholders [À COMPLÉTER] | En attente infos admin | ★★☆☆☆ | ★★★★★ | **7/10** | IMPORTANT | [I01](LEVIERS/I01.md) | ☐ |
| [05](#item-05) | Page /contact | 2h | ★★☆☆☆ | ★★★★★ | **7/10** | IMPORTANT | [I05](LEVIERS/I05.md) | ☐ |
| [06](#item-06) | Civilité M./Mme dans le profil | 2h | ★★☆☆☆ | ★★★★★ | **7/10** | IMPORTANT | [I06](LEVIERS/I06.md) | ☐ |
| [12](#item-12) | Synchronisation pages afia.fr ↔ projets | Au prochain push MINOR/MAJOR | ★★☆☆☆ | ★★★★★ | **7/10** | TRANSVERSE | [I12](LEVIERS/I12.md) | ☐ |
| [19](#item-19) | Admin — Menu Activités en groupe | 2h | ★★☆☆☆ | ★★★★★ | **7/10** | OPTIONNEL | [I19](LEVIERS/I19.md) | ☐ |
| [25](#item-25) | Cohérence curriculaire inter-disciplines | 2-3 sessions | ★★★★☆ | ★★☆☆☆ | **6/10** | OPTIONNEL | [L25](LEVIERS/L25.md) | ☐ |
| [09](#item-09) | Migration React Query (TanStack Query) | 1 session dédiée | ★★★☆☆ | ★★★☆☆ | **6/10** | IMPORTANT | [I09](LEVIERS/I09.md) | ☐ |
| [13](#item-13) | Dette technique complète | 2 sessions | ★★★☆☆ | ★★★☆☆ | **6/10** | SESSION DÉDIÉE | [I13](LEVIERS/I13.md) | ☐ |
| [15](#item-15) | Gestion emails sortants — backoffice admin | 1-2 sessions | ★★★☆☆ | ★★★☆☆ | **6/10** | OPTIONNEL | [I15](LEVIERS/I15.md) | ☐ |
| [22](#item-22) | Théâtre — 13e matière | 1-2 semaines | ★★★☆☆ | ★★★☆☆ | **6/10** | OPTIONNEL | [I22](LEVIERS/I22.md) | ☐ |
| [20](#item-20) | Projet demo-perf FastAPI + PostgreSQL | En fin de projet | ★★☆☆☆ | ★★★☆☆ | **5/10** | OPTIONNEL | [I20](LEVIERS/I20.md) | ☐ |
| [40](#item-40) | Badge « aSchool vous reconnaît » près du nom du prof | 0,5 session | ★★★☆☆ | ★★★★☆ | à scorer | Mon Profil / Header | — | ☐ |
| [41](#item-41) | Recherche dans la page Aide (plein-texte) | 0,5 session | à scorer | à scorer | à scorer | OPTIONNEL | — | ☐ |
| [42](#item-42) | Recherche globale dans l'application | à scorer | à scorer | à scorer | à scorer | OPTIONNEL | — | ☐ |

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
| 09 — Migration React Query | Refactoring transverse |
| 13 — Dette technique | Session dédiée |
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
**Statut :** validée (provisoire — révision après implémentation effective de 3 leviers consommateurs : L1, L25, L30)

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
| 1 | Que doit-on enseigner ? | Programmes officiels MEN | L1, L25, Générateur d'activités | L36 |
| 2 | Comment adapter à un profil d'élève ? | Guides MEN inclusion / DYS / FLE | L30 | — |
| 3 | Comment évaluer équitablement ? | Charte laïcité / référentiels équité | L04 | — |
| 4 | Comment communiquer avec familles/admin ? | Guides académiques communication | L31 | — |
| 5 | Comment stimuler la créativité élève ? | Recherche pédagogique créativité | L34 | — |

**Légende :**
- **Producteur** = levier responsable de l'ingestion/maintenance du corpus dans ChromaDB
- `—` = pas de producteur défini, alimentation manuelle ou via un producteur futur non encore désigné
- **L36** dans la colonne Producteur = producteur du corpus *Programmes MEN* uniquement. L'infrastructure RAG (pile mutualisée) est traitée séparément dans la fiche [INFRA-RAG](RAG/INFRA-RAG.md).

### 4. Leviers sans RAG

Analyseurs / transformateurs purs (hors-portée de la typologie ci-dessus) :
**L2, L3, L03, L26, L27, L28, L32, L33, L35, L37, L38**

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
  ***Principe clé** : une tâche franchit étage 1 (CC) → étage 2 (Harketti), s'accumule avec d'autres en une VERSION cohérente, déployée via prod.ps1, et seulement LÀ testée par les profs (étage 3). Leur retour redevient des tâches → repart à l'étage 1.*
  ***Besoin lié** : un mini journal de versions reliant chaque version aux tâches livrées → entrée dédiée ci-dessous. Identifié 08/06/2026.*

- [ ] **[Outillage] Mini journal de versions (version ↔ tâches livrées)** | Compagnon de l'étage 3, hors gel
  *Pas seulement lister « v3.3.0 = ces features » : **relier chaque version déployée aux tâches qu'elle embarque**, pour que lorsqu'un prof pilote remonte un problème, on sache **quelle version il utilise et ce qu'elle contient**. Traçabilité feedback prof ↔ version testée — compagnon direct de l'**étage 3** (item [Process] ci-dessus). Identifié 08/06/2026.*

---

## AUDIT — Mes outils → Créer → Activité (15/05/2026)

> Audit complet de la fonctionnalité. 11 issues identifiées, classées P1-P5 par gravité × urgence. Workflow point par point avec validation à chaque étape.

### Livré

- [x] **P1.1** — Erreurs OCR (TexteSource.jsx) basculées de div inline vers modal showError + reformulation message "PDF scanné" en langage prof (backend/routers/ocr.py)
- [x] **P1.2** — Deux alert() natifs de la dictée (micro refusé + navigateur non supporté) basculés vers showError
- [~] **P1.3 partiel** — Dictée : feedback visuel "Préparation du micro" + bip sonore (1× démarrage, 2× arrêt) via Web Audio API + bascule sur onaudiostart + buffer 400 ms + pré-chauffage AudioContext. Cas stop/redémarrage encore imparfait → voir NON RETENU.

### Triage Phase 2.3 (reprise, 31/05) — verdicts tranchés

- [x] **P2** — Auto-save activité : perte silencieuse → **modal + helper testable**. **FAIT** (Phase 2.1, commit `95fec11`).
- [ ] **P3.4** — `generate.py` : distinguer 401 / `KeyError` build_prompt (clé inconnue) / Groq down (vs `except Exception` → 500). → **CORRIGER** · ordre 1 · filet à compléter (KeyError + Groq-down).
- [ ] **P3.6** — Protéger contre `KeyError` quand `nb` manque pour une activité qui l'exige (App.jsx:272 + prompt). → **CORRIGER** · ordre 2 · test backend +.
- [ ] **P5.11** — Niveau « Supérieur » non supporté (= item #21, non entamé). → **CORRIGER** · ordre 3 · **clarifier d'abord** : retirer du menu vs bloquer le bouton (ne pas présumer).
- [ ] **P3.5** — Sur 401, rediriger vers /login. → **CORRIGER** · ordre 4 (le + sensible) · **relire le flux refresh token avant** (risque de boucle 401→login→retry→401).
- [ ] **P4.7** — Compteur few-shot `localStorage` → backend (désynchro toast vs BDD). → **SOUS-D** (refactor d'état, socle de l'item 40).
- [ ] **P5.10** — Centraliser la liste MATIERES (DRY, 3 endroits). → **SOUS-D** (refactor, isoler la régression).
- [ ] **P4.8** — Aligner carte Activité sur pattern btn-primary (App.jsx:606-614). → **GARDER/DÉFER** (cosmétique, backlog gelé).
- [ ] **P4.9** — Toast informatif au reset params (changement matière, App.jsx:225-231). → **GARDER/DÉFER** (mini-UX, backlog gelé).

> **TEMPS 2** (corrections une par une, filet vert entre chaque) — ordre : **P3.4 → P3.6 → P5.11 → P3.5**.

---

## ITEMS — Résumés (détails complets dans `LEVIERS/`)

### Pré-requis transverses (hors numérotation L)

<a id="infra-rag"></a>
- [~] **INFRA-RAG — Pile RAG mutualisée** | 1 session restante — DEV branché et validé, prod non décidée
  *Pile commune `backend/rag/` (singleton ChromaDB + sentence-transformers + fonction `retrieve` générique). Branchée sur `/api/generate` avec gates (matière/niveau/feature flag) + fallback silencieux + logs INFO. **Test 4 validé en DEV le 15/05** : canary `Z36-27` injecté puis retrouvé cité 4 fois dans la sortie LLM (preuve que les chunks influencent vraiment la génération) ; wording du préfixe RAG renforcé (avant : 0 marqueur institutionnel MEN dans la sortie / après : 14+ marqueurs « compétences », « connaissances », « attendus cycle 4 », sources `[BOEN_..., page X]`). Livrable une fois, réutilisée par tous les producteurs de corpus (L36 MEN, L30 DYS/FLE, L04 équité, L31 communication, L34 créativité) et tous les consommateurs (L1, L25, Générateur d'activités). Hors numérotation L — infra pure, pas un levier. Reste : hébergement chroma_db côté VPS, opti cold start sentence-transformers, branchement L1 (séquences) et autres consommateurs.*
  → [INFRA-RAG](RAG/INFRA-RAG.md)

### Items numérotés

<a id="item-01"></a>
- [ ] **01 — Pages légales CNIL — placeholders [À COMPLÉTER]** | En attente infos admin
  *4 pages légales rédigées dans `CNIL/`. Bloqué par délais administration française (forme juridique, SIRET, etc.). À compléter dès réception + intégrer dans React (4 routes + liens footer).*
  → [I01](LEVIERS/I01.md)

<a id="item-02"></a>
- [ ] **02 — Email admin → prof** | Facile | 2h
  *Bouton "Contacter" dans AdminFeedbacks + 3 templates (Traité / Précision / Remerciement). Endpoint `POST /api/admin/feedbacks/{id}/email`.*
  → [I02](LEVIERS/I02.md)

<a id="item-03"></a>
- [x] **03 — Analyseur de consignes (L5)** | Livré 14/05
  *5 axes (clarté, précision didactique, ambiguïté, structure, erreurs typiques) + version optimisée. Backend + frontend en place.*
  → [L03](LEVIERS/L03.md)

<a id="item-04"></a>
- [ ] **04 — Détecteur d'équité pédagogique** | Facile | 1 session
  *Audit d'une évaluation → 3 biais (contenu, difficulté, émotionnel). Grounding RAG sur charte de la laïcité + référentiels équité — infra commune avec [L36](LEVIERS/L36.md).*
  → [L04](LEVIERS/L04.md)

<a id="item-05"></a>
- [ ] **05 — Page /contact** | Facile | 2h
  *Remplace l'adresse email brute dans le footer — réduit le spam.*
  → [I05](LEVIERS/I05.md)

<a id="item-06"></a>
- [ ] **06 — Civilité M./Mme dans le profil** | Facile | 2h
  *Personnalisation de l'en-tête. Absorbé par Mon Profil.*
  → [I06](LEVIERS/I06.md)

<a id="item-07"></a>
- [ ] **07 — Onboarding email J+2 / J+7 / J+14** | Moyen | 3 jours
  *APScheduler installé, J+0 welcome existe. Relances J+2/J+7/J+14 = impact rétention direct.*
  → [I07](LEVIERS/I07.md)

<a id="item-08"></a>
- [ ] **08 — Analyse des notations Groq** | Facile | 1 jour
  *Un prompt + un bloc dans AdminFeedbacks. Utile dès 15 retours pour orienter le produit.*
  → [I08](LEVIERS/I08.md)

<a id="item-09"></a>
- [ ] **09 — Migration React Query (TanStack Query)** | Difficile | 1 session dédiée
  *Remplace 20+ fetch manuels par le standard industrie (timeout, retry, cache, loading/error centralisés). Session dédiée.*
  → [I09](LEVIERS/I09.md)

<a id="item-10"></a>
- [ ] **10 — Timeouts sessions** | Facile | 2h
  *Sessions trop longues signalées. À traiter séparément — ne pas toucher à l'auth sans analyse préalable.*
  → [I10](LEVIERS/I10.md)

<a id="item-11"></a>
- [ ] **11 — Fiche de révision Français + Fiche pédagogique HG** | Facile | 30 min
  *Deux types d'activités manquants à ajouter dans la matrice (sur le modèle des autres matières).*
  → [I11](LEVIERS/I11.md)

<a id="item-12"></a>
- [ ] **12 — Synchronisation pages afia.fr ↔ projets** | Facile | Au prochain push MINOR/MAJOR
  *Claude génère le contenu mis à jour de School.jsx (AFIA-FR) à chaque push MINOR ou MAJOR — prêt à coller. Règle dans CLAUDE.md.*
  → [I12](LEVIERS/I12.md)

<a id="item-13"></a>
- [ ] **13 — Dette technique complète** | 2 sessions — à planifier après 02 + 03 + 04
  *Périmètre : dépendances obsolètes, gestion d'erreurs API, migration React Query, doc règles métier, revue sécurité routes.*
  → [I13](LEVIERS/I13.md)

<a id="item-14"></a>
- [ ] **14 — Bouton "Partagez avec vos collègues"** | Moyen | 1 session
  *Prof envoie invitation par email. Backend `POST /api/partager/` (max 5 adresses/jour). Modale `PartagerCollègues.jsx`.*
  → [I14](LEVIERS/I14.md)

<a id="item-15"></a>
- [ ] **15 — Gestion emails sortants — backoffice admin** | Moyen | 1-2 sessions
  *Journal envois + stats + bounces → liste noire + lien désinscription. Prérequis : SMTP transactionnel (Brevo/Resend).*
  → [I15](LEVIERS/I15.md)

<a id="item-16"></a>
- [ ] **16 — Ambiguité → Créer une séquence** | Facile | 1h
  *Bouton "Créer une séquence →" sur chaque reformulation corrigée → pré-remplit le thème.*
  → [I16](LEVIERS/I16.md)

<a id="item-17"></a>
- [ ] **17 — Quiz interactif élèves** | Difficile | 2 semaines
  *Prof génère QCM → lien public → élèves répondent sur téléphone → résultats live. Différenciateur fort. Spec v1 validée 07/05.*
  → [I17](LEVIERS/I17.md)

<a id="item-18"></a>
- [ ] **18 — Aide spécifique par matière** | Moyen | 3-5 jours
  *Infrastructure prête (subject en BDD). Textes d'aide adaptés selon le profil prof.*
  → [I18](LEVIERS/I18.md)

<a id="item-19"></a>
- [ ] **19 — Admin — Menu Activités en groupe** | Facile | 2h
  *Prépare la modération des activités partagées. Pattern `group: true` déjà disponible dans AdminLayout.*
  → [I19](LEVIERS/I19.md)

<a id="item-20"></a>
- [ ] **20 — Projet demo-perf — FastAPI + PostgreSQL à l'échelle** | Difficile | En fin de projet
  *Projet technique séparé. Stack FastAPI async + PostgreSQL + Docker. Tests scénarios index, pagination, N+1, connection pool.*
  → [I20](LEVIERS/I20.md)

<a id="item-21"></a>
- [ ] **21 — Support niveau Supérieur (BTS/prépa/licence)** | Difficile | 2 semaines
  *Ouvre un segment nouveau (formateurs BTS/prépa). Surtout du travail de prompts et d'activités.*
  → [I21](LEVIERS/I21.md)

<a id="item-22"></a>
- [ ] **22 — Théâtre — 13e matière** | Moyen | 1-2 semaines
  *Activités dans MATRICE_ACTIVITES + parse_markdown.py. Prérequis : trouver un prof pilote théâtre.*
  → [I22](LEVIERS/I22.md)

<a id="item-23"></a>
- [ ] **23 — Escape Game pédagogique** | Difficile | 2-3 semaines
  *Prof choisit matière + niveau + thème → scénario + énigmes + épreuve finale. HTML imprimable.*
  → [I23](LEVIERS/I23.md)

<a id="item-24"></a>
- [ ] **24 — Google OAuth** | Difficile | 2-3 semaines
  *Réduit la friction d'inscription. Inutile avant validation des pilotes.*
  → [I24](LEVIERS/I24.md)

<a id="item-25"></a>
- [ ] **25 — Cohérence curriculaire inter-disciplines** | Difficile | 2-3 sessions
  *Aligne notions et progressions entre matières. 3 étapes : structurer programmes MEN, similarité sémantique inter-notions, définir la sortie. Approche : commencer 1 matière × 1 niveau. Grounding RAG mutualisé avec [L36](LEVIERS/L36.md).*
  → [L25](LEVIERS/L25.md)

<a id="item-26"></a>
- [ ] **26 — Pipeline qualité automatique** | Moyen | progressif
  *Assemblage des 6 leviers en un rapport qualité synthétique. Se construit au fil des leviers livrés.*
  → [L26](LEVIERS/L26.md)

<a id="item-27"></a>
- [ ] **27 — Validation texte source par LLM (Option B)** | Facile | 2h
  *Appel Groq pré-génération : "texte pédagogique exploitable ?" → JSON `{valide, raison}`. À implémenter quand Option A (heuristique livrée 13/05) montrera ses limites.*
  → [I27](LEVIERS/I27.md)

<a id="item-28"></a>
- [ ] **28 — Stratégie de remédiation** | Facile | 0,5 session
  *Étend L2 : pour chaque ambiguïté détectée, ajouter contre-exemple + activité de remédiation + formulation alternative. Modifie prompt L2 + ajuste Ambiguites.jsx. Pas de nouveau endpoint.*
  → [L28](LEVIERS/L28.md)

<a id="item-29"></a>
- [ ] **29 — Mode expérience prof (T1 / confirmé / expert)** | Facile | 0,5 session
  *1 champ `experience` en BDD + variable injectée dans tous les prompts. T1 = détaillé ; expert = condensé. Plus on attend, plus il manque partout.*
  → [L29](LEVIERS/L29.md)

<a id="item-30"></a>
- [ ] **30 — Différenciation DYS / FLE / approfondissement** | Moyen | 1 session
  *3 variantes d'une activité après génération : DYS (syntaxe épurée + OpenDyslexic), FLE (vocabulaire simplifié), approfondissement (nuances). 3 boutons dans ZoneResultat + 3 modificateurs de prompt. Grounding RAG sur guides MEN inclusion — infra commune avec [L36](LEVIERS/L36.md).*
  → [L30](LEVIERS/L30.md)

<a id="item-31"></a>
- [ ] **31 — Appréciations bulletins & communication parents** | Moyen | 1 session
  *Nouvelle section "Communication" dans Mes Outils + 4 prompts (appréciation bulletin, mail parents, compte-rendu, libre). 360 appréciations/an par prof — justifie l'abonnement. Grounding RAG sur guides communication aux familles.*
  → [L31](LEVIERS/L31.md)

<a id="item-32"></a>
- [ ] **32 — Visuels Mermaid / SVG** | Moyen | 1 session — prérequis de 33 et 34
  *Texte → SVG via librairie Mermaid. Frontend `npm install mermaid` + auto-rendu. Backend : 4 prompts (frise, séquence, carte conceptuelle, arbre). Pas d'IA d'images. Débloque [L33](LEVIERS/L33.md) et [L34](LEVIERS/L34.md).*
  → [L32](LEVIERS/L32.md)

<a id="item-33"></a>
- [ ] **33 — Mémo flash (format révision rapide)** | Facile | 0,5 session — après 32
  *Format ultra-condensé recto/verso, distinct de la fiche de révision classique. 1 nouveau type dans MATRICE_ACTIVITES + prompts. Avec [L32](LEVIERS/L32.md) : version carte mentale visuelle.*
  → [L33](LEVIERS/L33.md)

<a id="item-34"></a>
- [ ] **34 — Supports de créativité élève** | Moyen | 1 session — après 32
  *4 types multi-matières : amorces d'écriture, situations-problèmes, défis structurés, canevas BD (nécessite [L32](LEVIERS/L32.md)). Grounding RAG sur recherche pédagogique créativité.*
  → [L34](LEVIERS/L34.md)

<a id="item-35"></a>
- [ ] **35 — Versioning & transposition de séquences** | Difficile | 3 sessions
  *Permettre au prof de réutiliser/adapter une séquence existante au lieu de la régénérer — c'est le vrai moat. Nouvelle table `sequence_versions`, transposition automatique d'un niveau à l'autre, UI fork dans l'historique. Prérequis : [L37](LEVIERS/L37.md) (mécanique versions éphémère).*
  → [L35](LEVIERS/L35.md)

<a id="item-36"></a>
- [ ] **36 — Corpus Programmes MEN (producteur RAG)** | Moyen-Difficile | 3,5-5 sessions restantes — 1/96 docs indexés
  *Producteur de la collection `corpus_programmes_men` (~96 docs, 12 matières × 8 niveaux + programme 2026 cycle 4 progressif). Consommateurs : L1, L25, Générateur d'activités. Contrainte critique : coexistence 2020/2026 sur 3 ans → filtrage par métadonnée `programme` + `niveau` + `matiere` obligatoire. Prérequis : [INFRA-RAG](RAG/INFRA-RAG.md). État actuel : collection `maths_cycle4` indexée via POC, 95 docs restants.*
  → [L36](LEVIERS/L36.md) (volumétrie corpus, pipeline ingestion, contrainte 2020/2026, test d'éval binaire, risques hétérogénéité sources)

<a id="item-37"></a>
- [ ] **37 — Affinage interactif de séquence (instruction prof + versions éphémères)** | Moyen | 1 session — chantier en cours 14/05
  *Le prof pilote l'affinage par instruction libre ("phase 3 trop courte", "remplace par jeu de rôle"). Bouton "Affiner" + zone saisie texte/dictée + mini-pagination V1/V2/Vn. State React, perdu au refresh. Nouveau `POST /api/affiner-sequence`. Prérequis de [L35](LEVIERS/L35.md).*
  → [L37](LEVIERS/L37.md)

<a id="item-38"></a>
- [ ] **38 — Sortie séquence en JSON structuré (rendu pro)** | Moyen | 1 session — après 37
  *Passe du markdown brut à un JSON typé + rendu React avec cartes par phase, badges durée, code couleur par type d'organisation. Migration douce (fallback markdown). Facilite [L37](LEVIERS/L37.md) et [L35](LEVIERS/L35.md).*
  → [L38](LEVIERS/L38.md)

<a id="item-39"></a>
- [ ] **39 — Switch provider séquence → Claude Sonnet 4.6** | Facile | 2h — après 38
  *Évaluer Claude Sonnet 4.6 vs Groq llama-3.3-70b sur la génération de séquences. Ajouter `anthropic_client.py` + toggle ou variable `AI_PROVIDER_SEQUENCE`. Coût ~3$/Mtok input à monitorer.*
  → [L39](LEVIERS/L39.md)

<a id="item-40"></a>
- [ ] **40 — Signe distinctif « aSchool vous reconnaît » près du nom du prof** | Facile | 0,5 session — à scorer
  *Dès l'activation du few-shot (message « aSchool reconnaît maintenant votre façon de travailler… », `App.jsx:296`, au 3e save d'un même type), afficher un signe distinctif **persistant près du nom du prof dans le Header**. À trancher à l'implémentation : badge **global** (reconnu sur ≥1 type) ou **par type / compteur** ; source de l'état pour persister entre sessions (le `localStorage` par type actuel, ou données few-shot backend). Idée notée 31/05 — **GELÉE pendant la reprise** (pas de feature avant cœur solide + push rouvert).*

<a id="item-41"></a>
- [ ] **41 — Recherche dans la page Aide (plein-texte)** | Facile | 0,5 session — à scorer
  *La page Aide grossit à chaque livraison (règle « Aide rédigée à chaud »). Solution **RETENUE = Option A** — champ de recherche plein-texte en haut de Aide, filtrage live sur titre + contenu réel des sections via un `extractText` récursif mémoïsé (aucune duplication de contenu), surlignage des termes, compteur de résultats, état vide propre. Desktop : liste de résultats à plat ; mobile : filtre l'accordéon. Accessible (focus, Échap pour vider). Périmètre : 1 seul fichier `Aide.jsx`, pas de backend, pas de dépendance. Option B (palette Cmd/Ctrl+K) : V2 éventuelle par-dessus A, non prioritaire. Distinct de l'item 18 (contenu d'aide personnalisé par matière) : ici c'est de la découvrabilité/navigation. Feature produit — soumise au gel.*

<a id="item-42"></a>
- [ ] **42 — Recherche globale dans l'application** | à cadrer | à scorer
  *Recherche transverse dans les données de l'app — distincte de l'item 41 (qui est une recherche LOCALE à la page Aide). Périmètre à définir le jour venu : chercher dans quoi exactement (activités sauvegardées, séquences, réseau des collègues…) ; touchera probablement le backend (endpoints de recherche) → chantier transverse, pas un simple composant front, à cadrer séparément. Emplacement pressenti (décidé par Harketti) : dans le HEADER, une LOUPE à côté du titre central « Générateur d'activités pédagogiques ». Au clic sur la loupe, le titre s'efface et le champ de recherche prend sa place au centre ; recherche terminée ou champ fermé (✕ / Échap), le champ disparaît et le titre réapparaît. Les autres éléments du header (matière, nom, déconnexion) ne bougent pas. Exigence (comme l'item 41) : utilisable par TOUS les profs, même peu à l'aise avec le numérique — fermeture évidente, rien de caché. Lien : le pattern codé pour l'item 41 (normalize, surlignage, ergonomie) sert de RÉFÉRENCE d'ergonomie, pas de code réutilisé tel quel (données différentes). Feature produit — soumise au gel.*

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

## FAIT ✅

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
  *39 fichiers créés (L*.md pour leviers pédagogiques, I*.md pour items techniques/admin). TRACKER allégé : sections détaillées remplacées par résumés courts + lien. Colonne "Détail" ajoutée au tableau global. Architecture transverse (Cat. A/B/C, mapping RAG) maintenue dans TRACKER.*

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
- [x] **Analyse → Historique supprimé** — Sous-menu inutile (Consignes/Équité pas encore codés, analyses one-shot). (13/05)

- [x] **Auto-versioning PATCH** — prod.ps1 bumpe automatiquement le PATCH à chaque déploiement. Version initiale : 3.2.0 (12/05)
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
