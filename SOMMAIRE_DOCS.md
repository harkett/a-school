# SOMMAIRE_DOCS — Carte des documents .md du projet aSchool

> Inventaire des **75 fichiers `.md` du projet** (hors `.git`, `node_modules`, `.venv`).
> Chaque fichier a été lu en entier pour décrire son rôle exact.
> Établi le 29/06/2026. Document de repérage — ne pilote rien (le pilotage reste au `TRACKER.md`).

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
> Les références ci-dessous **excluent `SOMMAIRE_DOCS.md`** (ce fichier liste les docs par construction : il ne compte pas comme dépendance réelle).

---

## Synthèse du classement (29/06/2026)

**Bilan : 63 🟢 vivants · 3 🟠 périmés-utiles · 0 🔴 jetable maintenant · 8 🟡 jetables plus tard · 1 ⚪ incertain.**

> Historique des retraits :
> - `MesMD\BOUSSOLE\D10.md` (🔴) **supprimé le 29/06/2026** (chantier clôturé sans objet) → 77 → 76.
> - `.pytest_cache\README.md` (🔴) **retiré le 29/06/2026** (artefact auto-généré par pytest, dossier gitignoré, recréé au prochain run) → 76 → 75.

### 🔴 JETABLE MAINTENANT — référencé nulle part

| Doc | Preuve d'absence de référence |
|---|---|
| _(aucun document dans cette catégorie actuellement)_ | — |

### 🟡 JETABLE PLUS TARD — encore référencé (nettoyer les liens d'abord)

| Doc | Pourquoi jetable | Références à traiter (fichier:ligne) |
|---|---|---|
| MesMD\BOUSSOLE\D01.md | Livré + commité 18/05. | D12.md:30 · TABLEAU-DE-BORD.md:649 |
| MesMD\BOUSSOLE\D02.md | Livré + commité 18/05. | D12.md:30 · TABLEAU-DE-BORD.md:649 |
| MesMD\BOUSSOLE\D04.md | Livré + commité 18/05. | D12.md:30 · D12.md:67 · TABLEAU-DE-BORD.md:649 |
| MesMD\BOUSSOLE\D05.md | Livré + commité 18/05. | D12.md:30 · TABLEAU-DE-BORD.md:649 |
| MesMD\BOUSSOLE\D08.md | Dette branding terminée + commitée 19/05 (`cba2642`). | TABLEAU-DE-BORD.md:649 |
| MesMD\BOUSSOLE\D11.md | Dégraissage clos, réalisé par la fusion 11/06. | TABLEAU-DE-BORD.md:647 · TABLEAU-DE-BORD.md:668 |
| MesMD\BOUSSOLE\D33.md | « Ambiguïté → séquence » livré + testé 10/06. | TABLEAU-DE-BORD.md:96 · TABLEAU-DE-BORD.md:452 · TABLEAU-DE-BORD.md:671 |
| MesMD\TRACKER_NOTIONS_SCOLAIRES.md | Tracker éphémère auto-marqué « à supprimer une fois dispatché » ; dispatch coché ✅. | D49.md:6 · TABLEAU-DE-BORD.md:601 |

### 🟠 PÉRIMÉ MAIS UTILE — à réécrire

| Doc | Pourquoi périmé | Pourquoi utile |
|---|---|---|
| MesMD\BASE-DE-DONNEES.md | Auto-marqué périmé : décrit l'ancien schéma SQLite (20 tables, pivot email). | Doc de référence du schéma BDD — à refaire pour PostgreSQL/`user_id`. |
| MesMD\RAG\INFRA-RAG.md | Décrit la pile ChromaDB — faux après bascule pgvector. | Seule fiche d'archi du RAG — à réécrire post-migration. |
| REFERENTIELS\README.md | Procédure décrivant ChromaDB. | Procédure d'ajout de référentiel toujours utilisée. |

> **Réserve à trancher (signalée le 29/06, pas encore appliquée ci-dessous) :** `TRACKER_REFORME.md` (#23) et `AUDIT-EN-BASE-VS-EN-DUR.md` (#11) portent des lignes **fausses** (base décrite « encore SQLite » / runtime SQLite / chunks ChromaDB) → candidats 🟠 PÉRIMÉ MAIS UTILE. Encore notés 🟢 dans le tableau ci-dessous en attente de décision.

### ⚪ INCERTAIN

| Doc | Doute |
|---|---|
| MesMD\AUDIT_COHERENCE_C_HAB.md | Audit ponctuel = liste de contrôle. Jetable SI le réalignement a été fait, encore utile sinon — non vérifié. Mention en FIABILITE_CLAUDE.md:4. |

> Réserve dans le 🟢 VIVANT : `CLAUDE.md` reste vivant. La ligne stack 54 (« BDD = SQLite aujourd'hui ») a été **corrigée le 29/06** (→ PostgreSQL moteur unique). **Restent FAUX dans `CLAUDE.md`, à corriger en session docs** : le titre **« ## Tables BDD (`data/aschool.db`) »** (chemin SQLite) et la section **« Base vectorielle (ChromaDB) »** (RAG sur pgvector désormais). ⚠️ `CLAUDE.md` est chargé à chaque session → tant que ces lignes sont fausses, se fier au **code réel (PostgreSQL + pgvector)**, jamais à elles.

---

## Tableau des 75 documents

| # | Statut | Chemin | Rôle |
|---|---|---|---|
| 1 | 🟢 VIVANT | d:\A-SCHOOL\CLAUDE.md | Référence permanente chargée à chaque session : règles, vision, stack, VPS, routes API, tables BDD, conventions UI, workflow. Source unique de vérité. **(Ligne 54 périmée : « BDD = SQLite ».)** |
| 2 | 🟢 VIVANT | d:\A-SCHOOL\CNIL\00-Explication-Legale.md | Note de cadrage des obligations légales FR (LCEN, RGPD, CNIL) + structure des pages légales. Document interne, pas publié. |
| 3 | 🟢 VIVANT | d:\A-SCHOOL\CNIL\CGU.md | Texte des Conditions Générales d'Utilisation, destiné à être publié. |
| 4 | 🟢 VIVANT | d:\A-SCHOOL\CNIL\ML.md | Texte des Mentions légales (LCEN) ; champs identité société encore « À COMPLÉTER ». Destiné à être publié. |
| 5 | 🟢 VIVANT | d:\A-SCHOOL\CNIL\PC.md | Texte de la Politique de confidentialité (RGPD/CNIL). Destiné à être publié. |
| 6 | 🟢 VIVANT | d:\A-SCHOOL\CNIL\cookies.md | Texte de la page Cookies (2 cookies techniques, pas de bandeau). Destiné à être publié. |
| 7 | 🟢 VIVANT | d:\A-SCHOOL\MesAdmin\ADMIN_ASCHOOL.md | Fiche marque/domaine/réseaux : statut `aschool.fr`, dépôt de marque INPI, logos, handles sociaux. Gestion de la marque. |
| 8 | 🟢 VIVANT | d:\A-SCHOOL\MesAdmin\DIFFUSION_ASCHOOL.md | Stratégie de communication : positionnement, personas, messages, leviers viraux, canaux, métriques. |
| 9 | 🟢 VIVANT | d:\A-SCHOOL\MesAdmin\EMAIL_PILOTES.md | Templates d'emails d'activation/suivi des profs pilotes + tableau de suivi des envois. |
| 10 | 🟢 VIVANT | d:\A-SCHOOL\MesAdmin\PLAN_LANCEMENT_ASCHOOL.md | Plan d'action daté du lancement (avr→sept 2026) : phases, cibles, leviers, séquence onboarding, KPI. |
| 11 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\AUDIT-EN-BASE-VS-EN-DUR.md | Doctrine « tout en base, rien en dur » + plan en 3 niveaux (BDD / migration SQLite→PostgreSQL en 14 pas / sortie du dur) + audit prouvé code base-vs-dur. Feuille de route du socle. **(Lignes 134/186 périmées : ChromaDB / runtime SQLite — voir réserve.)** |
| 12 | ⚪ INCERTAIN | d:\A-SCHOOL\MesMD\AUDIT_COHERENCE_C_HAB.md | Audit ponctuel doc-vs-doc des incohérences entre les 4 docs de pilotage, par cluster/gravité. Liste de contrôle, rien corrigé dedans. |
| 13 | 🟠 PÉRIMÉ-UTILE | d:\A-SCHOOL\MesMD\BASE-DE-DONNEES.md | Doc admin du schéma + outillage (DB Browser/dbdiagram). **Marqué périmé** (décrit l'ancien SQLite 20 tables/pivot email). |
| 14 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\EMAILS.md | Référence obligatoire emails : SMTP Infomaniak, 2 adresses, .env, 4 fonctions d'envoi, principe `_smtp_send` unique. À lire avant toute modif email. |
| 15 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\FIABILITE_CLAUDE.md | Tracker (éphémère) anti-affirmations fausses de Claude : protocole de preuve en 5 étapes, registre d'anomalies, ledger nettoyage mémoire/CLAUDE.md. |
| 16 | 🟠 PÉRIMÉ-UTILE | d:\A-SCHOOL\MesMD\RAG\INFRA-RAG.md | Fiche d'archi de la pile RAG (ChromaDB + sentence-transformers + `retrieve`) : stack, volumétrie, état, reste à faire. **Décrit ChromaDB (à réviser post-pgvector).** |
| 17 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\SPEC-MODULE-CRECHE-aSCHOOL.md | Spec de référence du module Petite Enfance 0-3 ans : âges, axes, structures, garde-fous IA. Source produit de l'item D48. |
| 18 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\SPEC-MODULE-SUPERIEUR-aSchool.md | Spec de référence du module Supérieur (v2.1) recentrée « POUR l'enseignant » : 4 couches, ECTS, structures, contraintes IA. Source produit de D36. |
| 19 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\TABLEAU-DE-BORD.md | Doc de détail (Claude) : réservoir d'idées scoré, synergies, décision archi RAG, audits, journal FAIT. Couche détail/historique. |
| 20 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\TRACKER-AIDE.md | Tracker du système d'aide à 3 niveaux + tout le contenu rédigé d'avance (FAQ, textes, renvois). Réservoir en attente d'intégration au code. |
| 21 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\TRACKER.md | Tracker de pilotage principal (vue utilisateur) : tout le reste-à-faire ordonné, statut, dépendances. Fait foi sur l'ordre et le statut. |
| 22 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\TRACKER_FOURNISSEURS_IA.md | Référence unique « fournisseurs IA » (Groq/Anthropic) : chantier 4.1.e suspendu, plan de reprise, état réel du code, lien épic #45. |
| 23 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\TRACKER_REFORME.md | Tracker éphémère de la réforme moteur LLM+RAG en 6 phases (cases ✅/☐). Réforme **en cours**. **(Lignes 30/45 périmées : « base encore SQLite » — voir réserve.)** |
| 24 | 🟡 JETABLE +TARD | d:\A-SCHOOL\MesMD\TRACKER_NOTIONS_SCOLAIRES.md | Tracker éphémère : spec des 12 briques du « moteur de granularisation des notions », garde-fou RGPD, plan de dispatch (item 51/D49). **Auto-marqué « à supprimer après dispatch ».** Réf : D49.md:6 · TABLEAU-DE-BORD.md:601. |
| 25 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\aSchool-cycles-niveaux.md | Référence fixant la liste fermée cycles & niveaux (11 cycles, 88 niveaux), classée par effectifs FR. Seule donnée assumée « en dur ». |
| 26 | 🟡 JETABLE +TARD | d:\A-SCHOOL\MesMD\BOUSSOLE\D01.md | L5 « Analyseur de consignes » (`POST /api/analyser-consigne` + `Consigne.jsx`) ; livré + commité 18/05. Réf : D12.md:30 · TABLEAU-DE-BORD.md:649. |
| 27 | 🟡 JETABLE +TARD | d:\A-SCHOOL\MesMD\BOUSSOLE\D02.md | Refonte UX « Optimiseur inline + sidebar lean » ; livré + commité 18/05. Réf : D12.md:30 · TABLEAU-DE-BORD.md:649. |
| 28 | 🟡 JETABLE +TARD | d:\A-SCHOOL\MesMD\BOUSSOLE\D04.md | Fix infra Groq : `groq_client.py` + fallback 413/503 sur 3 modèles ; livré + commité 18/05. Réf : D12.md:30 · D12.md:67 · TABLEAU-DE-BORD.md:649. |
| 29 | 🟡 JETABLE +TARD | d:\A-SCHOOL\MesMD\BOUSSOLE\D05.md | Règle « erreurs en modale » (`errorDialog.js`) + matière-niveau header + resync niveau ; livré + commité 18/05. Réf : D12.md:30 · TABLEAU-DE-BORD.md:649. |
| 30 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D07.md | Affinage interactif de séquence (`POST /api/affiner-sequence` à câbler) ; plumbing dormant, décision à arbitrer. |
| 31 | 🟡 JETABLE +TARD | d:\A-SCHOOL\MesMD\BOUSSOLE\D08.md | Dette branding `school.afia.fr` → `aschool.fr` (migration 11/05) ; terminé + commité 19/05 (`cba2642`). Réf : TABLEAU-DE-BORD.md:649. |
| 32 | 🟡 JETABLE +TARD | d:\A-SCHOOL\MesMD\BOUSSOLE\D11.md | Dégraissage `BACKLOG.md` en index ; clos, réalisé par la fusion dans `TABLEAU-DE-BORD.md` 11/06. Réf : TABLEAU-DE-BORD.md:647 · :668. |
| 33 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D12.md | Chantier « Activité 100% fonctionnel en prod » : audit+finitions du flow `/api/generate`. À planifier. |
| 34 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D13.md | Chantier « Séquences 100% fonctionnel en prod » (L1+L3+L37) ; dépend de D07. À planifier. |
| 35 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D15.md | Dictée vocale : retour Deepgram→Groq Whisper batch, fix 400, retour visuel ; livré local, non poussé (gel prod). |
| 36 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D16.md | Chantier actif « Consolidation du cœur » : filet de tests + audit tâche par tâche puis réouverture du push. Phase 1 close, Phase 2 en cours. |
| 37 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D17.md | Spec « Analyse qualité d'une sortie pédagogique » : 3 analyseurs (ambiguïtés/consignes livrés, équité à faire) + agrégateur. |
| 38 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D18.md | Mode « expérience prof » (T1/confirmé/expert) : champ `experience` injecté dans tous les prompts. À faire. |
| 39 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D19.md | Textes administratifs prof-only (appréciations, mails parents) : section « Communication » + 4 prompts, grounding RAG. À faire. |
| 40 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D20.md | Moteur visuel Mermaid/SVG (frises, diagrammes, cartes). Socle prérequis de D21/D22. À faire. |
| 41 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D21.md | Format « mémo flash » recto/verso (type via `/api/generate`). À faire, après D20. |
| 42 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D22.md | « Supports de créativité élève » multi-matières ; canevas BD dépend de D20. |
| 43 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D23.md | « Différenciation DYS/FLE/approfondissement » : 3 variantes via boutons `ZoneResultat.jsx` + modificateurs de prompt. |
| 44 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D25.md | « Cohérence curriculaire inter-disciplines » : alignement notions/progressions (embeddings/LLM). |
| 45 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D26.md | « Versioning & transposition de séquences » (BDD, fork, transposition niveau) ; dépend de D07. |
| 46 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D27.md | « Sortie séquence en JSON structuré » : rendu React (cartes/badges) via `SequenceRenderer.jsx`. |
| 47 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D28.md | « Switch provider séquence → Claude Sonnet 4.6 » : client Anthropic parallèle + toggle .env. |
| 48 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D29.md | « Page /contact » pour réduire le spam (remplace l'email brut du footer). |
| 49 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D30.md | « Civilité M./Mme dans le profil » pour personnaliser l'en-tête. |
| 50 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D31.md | « Timeouts sessions » : sessions trop longues ; session séparée, prudence auth. |
| 51 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D32.md | « Google OAuth » : réduire la friction d'inscription ; reporté (chantier lourd auth). |
| 52 | 🟡 JETABLE +TARD | d:\A-SCHOOL\MesMD\BOUSSOLE\D33.md | « Ambiguïté → Créer une séquence » (✅ livré/testé 10/06) : bouton de navigation pré-remplie. Réf : TABLEAU-DE-BORD.md:96 · :452 · :671. |
| 53 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D34.md | « Quiz interactif élèves » : QCM→lien public→réponses téléphone→résultats live. Archi standalone (spec v1 07/05). |
| 54 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D35.md | « Aide spécifique par matière » : textes d'aide selon `subject` ; absorbé par `Aide.jsx`. |
| 55 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D36.md | « Support niveau Supérieur » (BTS/prépa/licence) ; lié à P5.11 et D48, spec dans SPEC-MODULE-SUPERIEUR. |
| 56 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D37.md | « Escape Game pédagogique » : scénario+énigmes+épreuve (HTML imprimable) depuis matière+niveau+thème. |
| 57 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D38.md | « Validation texte source par LLM (Option B) » : appel Groq de jugement avant génération (successeur heuristique Option A). |
| 58 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D39.md | Conformité CNIL : intégrer les 4 pages légales au React ; en attente des infos administratives société. |
| 59 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D40.md | Onboarding email : relances auto J+2/J+7/J+14 (APScheduler) après inscription. |
| 60 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D41.md | Bouton « Partagez avec vos collègues » : invitation email depuis l'interface (`POST /api/partager/`). |
| 61 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D42.md | Email admin→prof depuis le backoffice (bouton « Contacter » + 3 templates + trace BDD). |
| 62 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D43.md | Analyse des notations via Groq dans AdminFeedbacks (utile dès ~15 retours). |
| 63 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D44.md | Admin — Menu Activités en groupe (pattern `group: true`) pour préparer la modération. |
| 64 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D45.md | Catalogue : 2 types manquants (Fiche révision Français + Fiche péda Histoire-Géo) dans la matrice. |
| 65 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D46.md | Gestion emails sortants en backoffice (journal, stats, bounces) ; dépend d'un SMTP transactionnel à webhooks. |
| 66 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D47.md | Théâtre comme 13e matière (matrice + `parse_markdown.py`) ; prérequis = prof pilote théâtre. |
| 67 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D48.md | Module Petite Enfance (crèche 0-3 ans), 1er maillon multi-niveaux, garde-fou IA dur ; spec dans SPEC-MODULE-CRECHE. |
| 68 | 🟢 VIVANT | d:\A-SCHOOL\MesMD\BOUSSOLE\D49.md | Moteur de granularisation des notions (12 briques) nourrissant les outils existants ; ligne rouge RGPD. |
| 69 | 🟢 VIVANT | d:\A-SCHOOL\PROF_PILOTE\Matiere_Prof_Pilote.md | Tableau de suivi (modèle vide) des couples niveau/matière pour organiser l'encadrement des profs pilotes. |
| 70 | 🟢 VIVANT | d:\A-SCHOOL\PROF_PILOTE\Recrute_Prof_Pilote.md | Mémo de recrutement des profs pilotes : canaux de prospection + texte type de l'annonce. |
| 71 | 🟢 VIVANT | d:\A-SCHOOL\PWA\Checklist_QA_Prod_aSchool.md | Checklist QA pré-prod PWA (21 points / 35 sous-tests mobile réel) ; règle « 1 point rouge bloquant = pas de déploiement ». |
| 72 | 🟢 VIVANT | d:\A-SCHOOL\PWA\Install_Android.md | Notice prof : installer aSchool en PWA sur Android (Chrome) ; repris dans Aide. |
| 73 | 🟢 VIVANT | d:\A-SCHOOL\PWA\Install_iOS.md | Notice prof : installer aSchool en PWA sur iPhone (Safari) ; repris dans Aide. |
| 74 | 🟠 PÉRIMÉ-UTILE | d:\A-SCHOOL\REFERENTIELS\README.md | Procédure du dossier REFERENTIELS : emplacement unique, cycle de vie, procédure en 4 temps, future page admin. **Décrit ChromaDB.** |
| 75 | 🟢 VIVANT | d:\A-SCHOOL\data\README.md | Notes d'archi BDD : décision « synchrone » + dossier de référence justifiant PostgreSQL+pgvector (coûts, effort migration, déclencheurs). |

---

**Note de fraîcheur (29/06/2026) :** trois fichiers décrivent encore l'ancien socle technique (SQLite/ChromaDB) — `BASE-DE-DONNEES.md` (#13, auto-marqué périmé), `INFRA-RAG.md` (#16) et `REFERENTIELS/README.md` (#74). Deux autres portent des lignes fausses signalées mais non encore reclassées — `AUDIT-EN-BASE-VS-EN-DUR.md` (#11) et `TRACKER_REFORME.md` (#23). Mise à jour prévue dans une session docs dédiée.
