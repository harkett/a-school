# SOMMAIRE_DOCS — Carte des documents .md du projet aSchool

> Inventaire des **86 fichiers `.md` du projet** (hors `.git`, `node_modules`, `.venv`, `.pytest_cache`).
> Chaque fichier a été lu pour décrire son rôle exact.
> Établi le 29/06/2026 · **Rafraîchi le 06/07/2026** (delta git depuis le 29/06). Document de repérage — ne pilote rien (le pilotage reste au `TRACKER.md`).

---

## Légende des statuts

| Statut | Signification |
|---|---|
| 🟢 VIVANT | À jour et utile. |
| 🟠 PÉRIMÉ MAIS UTILE | Contenu faux/dépassé, mais le document sert encore → **à réécrire, pas à jeter**. |
| 🔴 JETABLE MAINTENANT | Mission finie, **référencé nulle part** → suppression possible sans casser de lien. |
| 🟡 JETABLE PLUS TARD | Mission finie, mais **encore référencé ailleurs** → nettoyer les renvois AVANT de supprimer. |
| ⚪ INCERTAIN | Statut non tranché — à vérifier avant de décider. |

> « Jetable » = classement, **pas** un ordre de suppression. La suppression se fait manuellement, doc par doc.
> Les références **excluent `SOMMAIRE_DOCS.md`** (ce fichier liste les docs par construction : il ne compte pas comme dépendance réelle).

---

## Synthèse du classement (06/07/2026)

**Bilan : 74 🟢 vivants · 2 🟠 périmés-utiles · 0 🔴 jetable maintenant · 9 🟡 jetables plus tard · 1 ⚪ incertain.**

> Delta depuis le 29/06 (rafraîchi le 06/07) :
> - **+11 nouveaux** : `architecture-chunking-référentiels.md`, `aSchool_matiere.md`, `DOCS_A_ANALYSER/REFERENTIEL-EVEIL-0-3-aSchool.md`, fiches `D00, D55, D56, D57, D58, D59, D60, D61`.
> - **−2 supprimés le 06/07** : `PROF_PILOTE/Matiere_Prof_Pilote.md` + `PROF_PILOTE/Recrute_Prof_Pilote.md` (récupérés hors projet).
> - **Déplacé** : `SOMMAIRE_DOCS.md` racine → `MesMD/`.
> - **Reclassements** : `CLAUDE.md` (caveat SQLite retiré — réécrit PostgreSQL) ; `INFRA-RAG.md` 🟠→🟢 et `REFERENTIELS/README.md` 🟠→🟢 (passés pgvector) ; `AUDIT-EN-BASE-VS-EN-DUR.md` 🟢→🟠 ; `TRACKER_REFORME.md` 🟢→🟡.

### 🔴 JETABLE MAINTENANT — référencé nulle part

| Doc | Preuve d'absence de référence |
|---|---|
| _(aucun document dans cette catégorie actuellement)_ | — |

### 🟡 JETABLE PLUS TARD — encore référencé (nettoyer les liens d'abord)

| Doc | Pourquoi jetable | Références à traiter |
|---|---|---|
| MesMD\BOUSSOLE\D01.md | Livré + commité 18/05. | D12.md · TABLEAU-DE-BORD.md |
| MesMD\BOUSSOLE\D02.md | Livré + commité 18/05. | D12.md · TABLEAU-DE-BORD.md |
| MesMD\BOUSSOLE\D04.md | Livré + commité 18/05. | D12.md · TABLEAU-DE-BORD.md |
| MesMD\BOUSSOLE\D05.md | Livré + commité 18/05. | D12.md · TABLEAU-DE-BORD.md |
| MesMD\BOUSSOLE\D08.md | Dette branding terminée + commitée 19/05. | TABLEAU-DE-BORD.md |
| MesMD\BOUSSOLE\D11.md | Dégraissage clos (fusion 11/06). | TABLEAU-DE-BORD.md |
| MesMD\BOUSSOLE\D33.md | « Ambiguïté → séquence » livré + testé 10/06. | TABLEAU-DE-BORD.md |
| MesMD\TRACKER_NOTIONS_SCOLAIRES.md | Tracker éphémère « à supprimer une fois dispatché » ; dispatch coché. | D49.md · TABLEAU-DE-BORD.md |
| MesMD\TRACKER_REFORME.md | Réforme moteur LLM+RAG quasi entièrement cochée (reste ☐ « CRUD matières admin ») ; tracker éphémère → archivage git à la fin. | CLAUDE.md · TRACKER.md |

### 🟠 PÉRIMÉ MAIS UTILE — à réécrire

| Doc | Pourquoi périmé | Pourquoi utile |
|---|---|---|
| MesMD\BASE-DE-DONNEES.md | Décrit l'ancien schéma SQLite (20 tables, pivot email). | Doc de référence du schéma BDD — à refaire pour PostgreSQL/`user_id`. |
| MesMD\AUDIT-EN-BASE-VS-EN-DUR.md | Ligne « filet : sans `DATABASE_URL` l'app reste sur SQLite » (l.103) contredite par `database.py` qui REFUSE SQLite ; `seed_programmes.py` présenté comme chargeur vivant alors que « seed » est banni/supprimé ; réf. `data/aschool.db`. | Doctrine « tout en base, rien en dur » + audit du « en dur » + les 14 Pas de migration restent la feuille de route du socle. |

### ⚪ INCERTAIN

| Doc | Doute |
|---|---|
| MesMD\AUDIT_COHERENCE_C_HAB.md | Audit ponctuel = liste de contrôle. Jetable SI le réalignement a été fait, encore utile sinon — non vérifié. |

---

## Tableau des 86 documents

| # | Statut | Chemin | Rôle |
|---|---|---|---|
| 1 | 🟢 VIVANT | CLAUDE.md | Référence permanente chargée à chaque session : règles absolues, vision, stack (PostgreSQL/pgvector), doctrine + méthode référentiel RAG, conventions UI, workflow. Source unique de vérité. **(À jour : SQLite banni, ChromaDB retiré.)** |
| 2 | 🟢 VIVANT | CNIL/00-Explication-Legale.md | Note de cadrage des obligations légales FR (LCEN, RGPD, CNIL) + structure des pages légales. Interne, pas publié. |
| 3 | 🟢 VIVANT | CNIL/CGU.md | Texte des Conditions Générales d'Utilisation, destiné à être publié. |
| 4 | 🟢 VIVANT | CNIL/ML.md | Texte des Mentions légales (LCEN) ; identité société encore « À COMPLÉTER ». |
| 5 | 🟢 VIVANT | CNIL/PC.md | Texte de la Politique de confidentialité (RGPD/CNIL). |
| 6 | 🟢 VIVANT | CNIL/cookies.md | Texte de la page Cookies (2 cookies techniques, pas de bandeau). |
| 7 | 🟢 VIVANT | MesAdmin/ADMIN_ASCHOOL.md | Fiche marque/domaine/réseaux : `aschool.fr`, marque INPI, logos, handles. |
| 8 | 🟢 VIVANT | MesAdmin/DIFFUSION_ASCHOOL.md | Stratégie de communication : positionnement, personas, messages, canaux, métriques. |
| 9 | 🟢 VIVANT | MesAdmin/EMAIL_PILOTES.md | Templates d'emails d'activation/suivi des profs pilotes + suivi des envois. |
| 10 | 🟢 VIVANT | MesAdmin/PLAN_LANCEMENT_ASCHOOL.md | Plan d'action daté du lancement (avr→sept 2026) : phases, cibles, leviers, KPI. |
| 11 | 🟠 PÉRIMÉ-UTILE | MesMD/AUDIT-EN-BASE-VS-EN-DUR.md | Doctrine « tout en base, rien en dur » + audit en-dur + 14 Pas de migration SQLite→PostgreSQL. **(Ligne 103 « filet SQLite » + refs `seed_programmes`/`data/aschool.db` périmées.)** |
| 12 | ⚪ INCERTAIN | MesMD/AUDIT_COHERENCE_C_HAB.md | Audit ponctuel doc-vs-doc des incohérences entre docs de pilotage. Liste de contrôle, rien corrigé dedans. |
| 13 | 🟠 PÉRIMÉ-UTILE | MesMD/BASE-DE-DONNEES.md | Doc admin du schéma + outillage. **Périmé** (décrit l'ancien SQLite 20 tables/pivot email). |
| 14 | 🟢 VIVANT | MesMD/BOUSSOLE/D00.md | Chantier (item 00) : remettre à plat la numérotation item N ↔ fiche DN. Explicitement « pas maintenant ». |
| 15 | 🟡 JETABLE +TARD | MesMD/BOUSSOLE/D01.md | L5 « Analyseur de consignes » ; livré + commité 18/05. |
| 16 | 🟡 JETABLE +TARD | MesMD/BOUSSOLE/D02.md | Refonte UX « Optimiseur inline + sidebar lean » ; livré 18/05. |
| 17 | 🟡 JETABLE +TARD | MesMD/BOUSSOLE/D04.md | Fix infra Groq (`groq_client.py` + fallback) ; livré 18/05. |
| 18 | 🟡 JETABLE +TARD | MesMD/BOUSSOLE/D05.md | Règle « erreurs en modale » + matière-niveau header ; livré 18/05. |
| 19 | 🟢 VIVANT | MesMD/BOUSSOLE/D07.md | Affinage interactif de séquence (route à câbler) ; plumbing dormant, à arbitrer. |
| 20 | 🟡 JETABLE +TARD | MesMD/BOUSSOLE/D08.md | Dette branding `school.afia.fr` → `aschool.fr` ; terminé + commité 19/05. |
| 21 | 🟡 JETABLE +TARD | MesMD/BOUSSOLE/D11.md | Dégraissage `BACKLOG.md` ; clos par la fusion 11/06. |
| 22 | 🟢 VIVANT | MesMD/BOUSSOLE/D12.md | Chantier « Activité 100% fonctionnel en prod » ; à planifier. |
| 23 | 🟢 VIVANT | MesMD/BOUSSOLE/D13.md | Chantier « Séquences 100% fonctionnel en prod » ; dépend de D07. |
| 24 | 🟢 VIVANT | MesMD/BOUSSOLE/D15.md | Dictée vocale (Groq Whisper batch) ; livré local, non poussé. |
| 25 | 🟢 VIVANT | MesMD/BOUSSOLE/D16.md | Chantier « Consolidation du cœur » : filet de tests + audit ; Phase 1 close. |
| 26 | 🟢 VIVANT | MesMD/BOUSSOLE/D17.md | Spec « Analyse qualité d'une sortie » : 3 analyseurs + agrégateur. |
| 27 | 🟢 VIVANT | MesMD/BOUSSOLE/D18.md | Mode « expérience prof » (T1/confirmé/expert) injecté dans les prompts. |
| 28 | 🟢 VIVANT | MesMD/BOUSSOLE/D19.md | Textes administratifs prof-only (appréciations, mails parents) + grounding RAG. |
| 29 | 🟢 VIVANT | MesMD/BOUSSOLE/D20.md | Moteur visuel Mermaid/SVG. Socle de D21/D22. |
| 30 | 🟢 VIVANT | MesMD/BOUSSOLE/D21.md | Format « mémo flash » recto/verso. Après D20. |
| 31 | 🟢 VIVANT | MesMD/BOUSSOLE/D22.md | « Supports de créativité élève » ; dépend de D20. |
| 32 | 🟢 VIVANT | MesMD/BOUSSOLE/D23.md | « Différenciation DYS/FLE/approfondissement » via modificateurs de prompt. |
| 33 | 🟢 VIVANT | MesMD/BOUSSOLE/D25.md | « Cohérence curriculaire inter-disciplines » (embeddings/LLM). |
| 34 | 🟢 VIVANT | MesMD/BOUSSOLE/D26.md | « Versioning & transposition de séquences » ; dépend de D07. |
| 35 | 🟢 VIVANT | MesMD/BOUSSOLE/D27.md | « Sortie séquence en JSON structuré » + rendu React. |
| 36 | 🟢 VIVANT | MesMD/BOUSSOLE/D28.md | « Switch provider séquence → Claude Sonnet » (client Anthropic + toggle). |
| 37 | 🟢 VIVANT | MesMD/BOUSSOLE/D29.md | « Page /contact » (remplace l'email brut du footer). |
| 38 | 🟢 VIVANT | MesMD/BOUSSOLE/D30.md | « Civilité M./Mme dans le profil ». |
| 39 | 🟢 VIVANT | MesMD/BOUSSOLE/D31.md | « Timeouts sessions » ; prudence auth. |
| 40 | 🟢 VIVANT | MesMD/BOUSSOLE/D32.md | « Google OAuth » ; reporté (chantier lourd auth). |
| 41 | 🟡 JETABLE +TARD | MesMD/BOUSSOLE/D33.md | « Ambiguïté → Créer une séquence » ; livré/testé 10/06. |
| 42 | 🟢 VIVANT | MesMD/BOUSSOLE/D34.md | « Quiz interactif élèves » ; archi standalone (spec 07/05). |
| 43 | 🟢 VIVANT | MesMD/BOUSSOLE/D35.md | « Aide spécifique par matière » ; absorbé par `Aide.jsx`. |
| 44 | 🟢 VIVANT | MesMD/BOUSSOLE/D36.md | « Support niveau Supérieur » (BTS/prépa/licence). |
| 45 | 🟢 VIVANT | MesMD/BOUSSOLE/D37.md | « Escape Game pédagogique » (HTML imprimable). |
| 46 | 🟢 VIVANT | MesMD/BOUSSOLE/D38.md | « Validation texte source par LLM (Option B) ». |
| 47 | 🟢 VIVANT | MesMD/BOUSSOLE/D39.md | Conformité CNIL : intégrer les 4 pages légales au React. |
| 48 | 🟢 VIVANT | MesMD/BOUSSOLE/D40.md | Onboarding email : relances J+2/J+7/J+14 (APScheduler). |
| 49 | 🟢 VIVANT | MesMD/BOUSSOLE/D41.md | Bouton « Partagez avec vos collègues » (invitation email). |
| 50 | 🟢 VIVANT | MesMD/BOUSSOLE/D42.md | Email admin→prof depuis le backoffice (3 templates + trace BDD). |
| 51 | 🟢 VIVANT | MesMD/BOUSSOLE/D43.md | Analyse des notations via Groq dans AdminFeedbacks. |
| 52 | 🟢 VIVANT | MesMD/BOUSSOLE/D44.md | Admin — Menu Activités en groupe (pattern `group: true`). |
| 53 | 🟢 VIVANT | MesMD/BOUSSOLE/D45.md | Catalogue : 2 types manquants (Fiche révision Français + Fiche péda HG). |
| 54 | 🟢 VIVANT | MesMD/BOUSSOLE/D46.md | Gestion emails sortants en backoffice ; dépend d'un SMTP transactionnel. |
| 55 | 🟢 VIVANT | MesMD/BOUSSOLE/D47.md | Théâtre comme 13e matière ; prérequis prof pilote théâtre. |
| 56 | 🟢 VIVANT | MesMD/BOUSSOLE/D48.md | Module Petite Enfance (crèche 0-3 ans) ; spec dans SPEC-MODULE-CRECHE. |
| 57 | 🟢 VIVANT | MesMD/BOUSSOLE/D49.md | Moteur de granularisation des notions (12 briques) ; ligne rouge RGPD. |
| 58 | 🟢 VIVANT | MesMD/BOUSSOLE/D53.md | « Remplacer un référentiel existant » (geste explicite + cascade). |
| 59 | 🟢 VIVANT | MesMD/BOUSSOLE/D55.md | Chantier (item 55) : injecter les cycles 7-11 du socle matières + supprimer doublon 0-3. Non démarré. |
| 60 | 🟢 VIVANT | MesMD/BOUSSOLE/D56.md | Chantier (item 56) : réconcilier l'artefact pré-réforme BTS CIEL Option A. Constat, rien décidé. |
| 61 | 🟢 VIVANT | MesMD/BOUSSOLE/D57.md | Chantier (item 57) : registre « couple → méthode d'extraction » data-driven en base. Dépend de la crèche. |
| 62 | 🟢 VIVANT | MesMD/BOUSSOLE/D58.md | Chantier (item 58) : dossier `MesMD/CONNAISSANCE/` (fonctionnement réel extrait du code). |
| 63 | 🟢 VIVANT | MesMD/BOUSSOLE/D59.md | Chantier (item 59) : crèche en pause — source déposée = référentiel « qualité d'accueil » et non d'éveil ; attend la bonne source officielle. |
| 64 | 🟢 VIVANT | MesMD/BOUSSOLE/D60.md | Chantier (item 60) : procédure référentiel de bout en bout (socle + routine, analyse amont, 9 étapes) ; archi figée 06/07, automatisation à faire. |
| 65 | 🟢 VIVANT | MesMD/BOUSSOLE/D61.md | Chantier parapluie (item 61) : regrouper les retouches du menu admin sous une seule ligne tracker. |
| 66 | 🟢 VIVANT | MesMD/DOCS_A_ANALYSER/REFERENTIEL-EVEIL-0-3-aSchool.md | Référentiel d'éveil 0-3 (compilation aSchool non officielle, 2 docs UNICEF, hors prod) ; doc de travail crèche de l'analyse amont D60 (27 activités taguées par âge). |
| 67 | 🟢 VIVANT | MesMD/EMAILS.md | Référence obligatoire emails : SMTP Infomaniak, `.env`, fonctions d'envoi, `_smtp_send` unique. À lire avant toute modif email. |
| 68 | 🟢 VIVANT | MesMD/FIABILITE_CLAUDE.md | Tracker (éphémère) anti-affirmations fausses : protocole de preuve, registre d'anomalies. |
| 69 | 🟢 VIVANT | MesMD/RAG/INFRA-RAG.md | Fiche d'archi de la pile RAG **(pgvector + BGE-M3 + `retrieve_pg`)**. *(Réserves mineures : « État actuel » daté 15/05 ; nom de collection à uniformiser.)* |
| 70 | 🟢 VIVANT | MesMD/SOMMAIRE_DOCS.md | Ce fichier : carte des documents `.md`. Repérage, ne pilote rien. **(Déplacé racine → MesMD/ le 06/07.)** |
| 71 | 🟢 VIVANT | MesMD/SPEC-MODULE-CRECHE-aSCHOOL.md | Spec de référence du module Petite Enfance 0-3 ans (item D48). |
| 72 | 🟢 VIVANT | MesMD/SPEC-MODULE-SUPERIEUR-aSchool.md | Spec de référence du module Supérieur (v2.1, item D36). |
| 73 | 🟢 VIVANT | MesMD/TABLEAU-DE-BORD.md | Doc de détail (Claude) : réservoir scoré, décisions archi, audits, journal FAIT. |
| 74 | 🟢 VIVANT | MesMD/TRACKER-AIDE.md | Tracker du système d'aide à 3 niveaux + contenu rédigé d'avance. |
| 75 | 🟢 VIVANT | MesMD/TRACKER.md | Tracker de pilotage principal (vue utilisateur) ; fait foi sur l'ordre et le statut. |
| 76 | 🟢 VIVANT | MesMD/TRACKER_FOURNISSEURS_IA.md | Référence « fournisseurs IA » (Groq/Anthropic) ; chantier 4.1.e suspendu. |
| 77 | 🟡 JETABLE +TARD | MesMD/TRACKER_NOTIONS_SCOLAIRES.md | Tracker éphémère (12 briques du moteur de granularisation) ; « à supprimer après dispatch » (coché). |
| 78 | 🟡 JETABLE +TARD | MesMD/TRACKER_REFORME.md | Tracker éphémère réforme moteur LLM+RAG ; quasi tout coché (reste ☐ CRUD matières admin) → archivage git à la fin. **(À jour : pgvector.)** |
| 79 | 🟢 VIVANT | MesMD/aSchool-cycles-niveaux.md | Référence de la liste fermée cycles & niveaux (11 cycles, 88 niveaux), classée par effectifs FR. |
| 80 | 🟢 VIVANT | MesMD/aSchool_matiere.md | Socle des matières écrit à la main (11 cycles) ; source d'injection en base (réf D55 / README / CLAUDE.md). Cycle 11 « 0-3 ans » = doublon à supprimer (D55). |
| 81 | 🟢 VIVANT | MesMD/architecture-chunking-référentiels.md | Note d'archi (04/07) : chunking des référentiels = moteur générique `chunker.py` + une fiche/procédure par référentiel (extraction incluse). |
| 82 | 🟢 VIVANT | PWA/Checklist_QA_Prod_aSchool.md | Checklist QA pré-prod PWA (21 points / 35 sous-tests) ; « 1 point rouge = pas de déploiement ». |
| 83 | 🟢 VIVANT | PWA/Install_Android.md | Notice prof : installer aSchool en PWA sur Android (Chrome). |
| 84 | 🟢 VIVANT | PWA/Install_iOS.md | Notice prof : installer aSchool en PWA sur iPhone (Safari). |
| 85 | 🟢 VIVANT | REFERENTIELS/README.md | Procédure et emplacement unique des référentiels officiels **(table `referentiel_chunks`, pgvector)**. *(Petite incohérence de chemin à uniformiser avec CLAUDE.md.)* |
| 86 | 🟢 VIVANT | data/README.md | Notes d'archi BDD : décision « synchrone » + dossier justifiant PostgreSQL+pgvector. |

---

**Note de fraîcheur (06/07/2026) :** deux docs décrivent encore l'ancien socle SQLite — `BASE-DE-DONNEES.md` (#13) et `AUDIT-EN-BASE-VS-EN-DUR.md` (#11, ligne 103) → à réécrire en session docs. Tout le reste vérifié à jour (le RAG est passé à pgvector partout : `CLAUDE.md`, `INFRA-RAG`, `REFERENTIELS/README`, `TRACKER_REFORME`).
