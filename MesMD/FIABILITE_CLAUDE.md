# FIABILITÉ CLAUDE — empêcher les affirmations fausses (données périmées + vérification)

> Tracker de chantier (éphémère). Finira en archive git une fois le chantier clos.
> Distinct de `AUDIT_COHERENCE_C_HAB.md` (autre sujet, non touché ici).
>
> But global : que Claude **cesse de produire des affirmations fausses** sur le projet.
> Le titre ne se réduit pas à « mémoire » : les bourdes ont DEUX causes (voir ci-dessous),
> et la mémoire n'en est qu'une.

## Deux causes, pas une (à ne jamais confondre)
Mes bourdes n'ont pas une seule origine :

- **Cause A — données périmées (LE RANGEMENT).** La mémoire / `CLAUDE.md` contiennent
  des faits qui ont vieilli, et je les récite tels quels. → réparable par l'audit (phase A).
- **Cause B — comportement de vérification (INDÉPENDANT du rangement).** Même avec une
  mémoire parfaitement rangée, je peux affirmer sans rouvrir le fichier (supposition,
  inférence plausible, ou « tout texte déjà là traité comme acquis »). → NON réparable
  par le rangement. Seulement discipline + garde-fou (hook), jamais à 100 %.
  Piste séparée, traitée APRÈS la phase A (voir § Phase B).

**Cause B — les 3 endroits précis où ça casse (= les barrières à tenir) :**

| # | Où ça casse | Barrière qui l'arrête |
|---|---|---|
| **B1** | Je réponds depuis la mémoire/les docs **sans ouvrir le code** (le plus fréquent) | Protocole étape 1 : indice ≠ preuve → citer `fichier:ligne` ou « pas vérifié » |
| **B2** | Je lis le code mais **je ne vérifie pas la joignabilité** (le prof n'y a pas accès) → je dis « live » à tort | Règle n°9 : joignabilité AVANT la chaîne (protocole étape 2) |
| **B3** | Je dis « ça marche » **sans avoir exécuté** → « ça devrait marcher » déguisé en certitude | « Tester soi-même avant » (protocole étape 4) : exécuter, sinon écrire « non testé » |

> La phase A traite **A**. **B** est notée pour ne pas l'oublier, pas résolue par le tri.

## Mécanique vérifiée — pourquoi ça dérive sur TOUT projet
> Vérifié via la doc officielle Claude Code (agent `claude-code-guide`), pas de mémoire.

- **`CLAUDE.md` (projet ET global `~/.claude/`)** : chargé **verbatim à chaque session**,
  **jamais re-synchronisé** avec le code — mise à jour **100 % manuelle**, aucune
  détection de péremption.
- **Mémoire** : `MEMORY.md` (≤ 200 lignes / 25 Ko) chargé chaque session ; les fichiers
  de détail lus **à la demande** ; **aucune détection de péremption**.
- **Rien** ne garde ces fichiers en phase avec le code ; seul `/compact` relit `CLAUDE.md`
  du disque — sans le **valider**.
- **Hooks** : `PreToolUse` peut **bloquer un outil** (exit code 2) ; l'injection de contexte
  (`UserPromptSubmit`) est **« advisory »** — un rappel, pas un verrou. → **rien n'empêche
  physiquement une affirmation fausse.**
- **Best practice Anthropic** : `CLAUDE.md`/mémoire = conventions durables / archi /
  standards ; **PAS** d'état volatil ni de procédure multi-étapes.

Sources : doc Claude Code `memory.md`, `how-claude-code-works.md`, `hooks.md`.
→ Conclusion : `CLAUDE.md`/mémoire = une **photo**, le code = le **film**. Toute photo d'un
truc qui bouge **devient fausse**. C'est documenté comme comportement normal, sur **tout** projet.

## Méthode (phase A = audit données)
Confronter chaque **fait** de la mémoire Claude (`~/.claude/projects/d--A-SCHOOL/memory/`)
et de `CLAUDE.md` au **code réel**. Principe : **mémoire = indice, jamais preuve**.
Toute affirmation sans citation `fichier:ligne` obtenue par un outil = « pas vérifié ».

1. Vérification **fait par fait**, source par source. Preuve `fichier:ligne` obligatoire.
2. Anomalie trouvée → inscrite dans le REGISTRE ci-dessous. **On NE corrige pas tout de
   suite** — on liste et on continue.
3. Nettoyage / corrections = **phase séparée**, APRÈS l'inventaire, validée par l'utilisateur.

## Le PROTOCOLE de réponse — répondre à une question sur le code (5 étapes)
> Le geste à faire à CHAQUE question « est-ce que X est opérationnel / fait / branché ? ».
> Exemple déroulé en vrai sur la fonctionnalité « gestion de l'ambiguïté » (lignes réelles).

Question : « La gestion de l'ambiguïté dans aSchool est-elle opérationnelle ? »

1. **Indice d'abord (jamais une réponse).** La mémoire/docs disent seulement OÙ chercher :
   `Ambiguites.jsx`, route `/api/detect-ambiguites`, routeur `ambiguites.py`. = pistes.
2. **Joignabilité AVANT la chaîne (règle n°9).** Le prof peut-il seulement cliquer ? Entrée
   visible, pas `disabled`, pas « bientôt ». → entrée cliquable `App.jsx:697`, page rendue
   `App.jsx:935`. *Un code parfait qu'on ne peut pas atteindre n'est PAS opérationnel.*
3. **La chaîne de code.** Bouton → route → routeur monté → LLM :
   - le front appelle la route : `Ambiguites.jsx:88` `apiFetch('/api/detect-ambiguites')`
   - la route existe : `ambiguites.py:67` `@router.post("/detect-ambiguites")`
   - le routeur est monté : `main.py:138` `include_router(ambiguites.router, prefix="/api")`
   - la logique appelle le LLM : `ambiguites.py:84` `generate(prompt, provider=…, model=…)`
4. **Exécution réelle si possible.** Lancer l'appel et constater. Ici : **non exécuté en live**
   (serveur + clé requis) → je le DIS, jamais « ça devrait marcher ».
5. **Réponse AVEC preuve, ou « pas vérifié ».** Verdict : « Chaîne complète et joignable
   (lignes ci-dessus) → **opérationnel en statique ; non testé en exécution réelle.** »

❌ La version paresseuse à BANNIR : lire « L2 /api/detect-ambiguites » en mémoire et répondre
« Oui, opérationnel ». Zéro preuve — la route peut être débranchée, le bouton masqué, etc.

## Progression (pour ne pas perdre le fil)
- [ ] `CLAUDE.md` — Stack
- [ ] `CLAUDE.md` — VPS production
- [ ] `CLAUDE.md` — Scripts
- [ ] `CLAUDE.md` — Catalogue d'activités (12 × 43 = 140 ?)
- [ ] `CLAUDE.md` — Routes API
- [ ] `CLAUDE.md` — Tables BDD
- [ ] `CLAUDE.md` — Auth / backoffice
- [ ] `CLAUDE.md` — Variables d'environnement
- [ ] `CLAUDE.md` — autres sections
- [ ] `memory/` — fichiers `project_*` (faits)  — 1 / ~30 (1 supprimée)
- [ ] `memory/` — fichiers `feedback_*` (doublons)  — 0 / ~60
- [ ] `memory/MEMORY.md` (index vs fichiers réels)

## REGISTRE DES ANOMALIES
| # | Source | Affirmé | Réel (preuve fichier:ligne) | Verdict | Action prévue (nettoyage) |
|---|---|---|---|---|---|
| 1 | `memory/MEMORY.md` | L'index liste les fichiers mémoire | 6 fichiers existaient hors index | ❌ index incomplet | ✅ **traité** (voir § ORPHELINS du ledger) |
| 2 | `CLAUDE.md` § Tables BDD | « Tables app » = `feedbacks` + `activites_sauvegardees` ; `user_email` partout | 21 tables réelles (`models_db.py`) ; clé = `user_id` | ❌ périmé / incomplet | ✅ **FAIT** — section réécrite (21 tables groupées, `user_email`→`user_id`, pointeur source de vérité) |
| 3 | `memory/project_refonte_niveaux_matieres.md` | « pas encore en code / seeds à arbitrer » | modèle EN code (`models_db.py:244-293`) + seed complet & arbitré (`seed_programmes.py`), 3 pièges résolus | ❌ périmé | ✅ **FAIT** — mémoire supprimée + ligne `MEMORY.md` retirée (résidu backfill tracé `TRACKER.md` A4) |
| 4 | `MesMD/TRACKER.md` § Refonte programmes | « conçu, **pas encore construit** » + Réserve 1 SEED ☐ | construit : `models_db.py:244-293` + `seed_programmes.py` ; Réserve 1 (SEED) FAITE. *(Réserve 2 BACKFILL ☐ encore vraie : `users` garde `subject`/`niveau`, `models_db.py:20-23`)* | ❌ périmé | ✅ **FAIT** — titre + blockquote + 3 cases corrigés (preuves), A2/A3 recalés ; Réserve 2/3 laissées ☐ (« en base » non affirmé) |
| 5 | `memory/ameliorations_futures.md` | backlog idées futures | sous-ensemble strict de `project_future_improvements.md` (lu + comparé) | ❌ doublon (orphelin hors index) | ✅ **SUPPRIMÉ** |
| 6 | `memory/feedback_mesressources.md` | règle dossier MesRessources | contenu = « règle supprimée le 13/05 » → mémoire morte (lu) | ❌ obsolète (orphelin) | ✅ **SUPPRIMÉ** |

## Ledger scouts (4 agents, lecture seule) — pistes À RECONFIRMER par moi avant toute action
> Défriché en parallèle. **Rien n'est supprimé/modifié sur cette seule base** : je rouvre chaque fichier avant de le toucher.

**À SUPPRIMER — traité (relu moi-même) :**
- ✅ **SUPPRIMÉS** : `project_session_07052026`, `…08…`, `…09…`, `…11…` (journaux datés → git) · `project_roadmap` (l'ordre vit dans `TRACKER.md`) · `project_vps_status` (instruction déjà dans `CLAUDE.md`) · `project_admin_activites_future` (dup orphelin)
- ✅ **différés finalement traités** : `project_session_15052026` SUPPRIMÉ (son mécanisme `_build_rag_prefix` a été retiré par la réforme — `TRACKER_REFORME.md:39` → journal périmé ; état RAG vivant dans `TRACKER_REFORME`) · `project_outputs_demo` SUPPRIMÉ (`outputs/` vide, Glob)

**À METTRE À JOUR — traité (revérifié par moi, jamais sur la parole du scout) :**
- ✅ `project_few_shot_adaptation` — **scout DÉMENTI** : `_build_few_shot_prefix()` existe bien (`src/prompts.py:2709,2750`) → mémoire **exacte, gardée sans changement** (preuve que je vérifie les scouts).
- ✅ **MAJ** : `project_vision` (faux « terminé 100 % » retiré, nugget whisper gardé) · `project_preferences_stockage` (auth EST prête ; dette localStorage `App.jsx:201` ouverte, pas d'endpoint `/api/user/preferences`) · `project_mes_outils_plan` (L5 back `consigne.py` présent ; L6 `equite` absent).
- ✅ **SUPPRIMÉS** (dup `CLAUDE.md` / statut stale falsifié, vérifiés moi) : `project_aschool` (port 8000 + dup) · `project_etat_session` (chronologie → git) · `project_llm_agnostique_etat` (`call_groq` **introuvable** dans `backend/` → audit 20/06 périmé ; vivant dans `TRACKER_REFORME.md`) · `project_outputs_demo` (`outputs/` **vide**, Glob).
- ⏸️ GARDÉ tel quel : `project_fusion_tableau_bord` (exact : fusion faite, simplification + renommage `BOUSSOLE/` pendants — pilotage durable).

**RÉFÉRENCES MORTES — traité :**
- ✅ `PLAN_BACKOFFICE_FASTAPI.md` : confirmé **absent** (Glob=0) → pointeur mort retiré de `CLAUDE.md:167` (→ `admin.py` + § Tables BDD) ; `project_backoffice_status` (qui le citait + dupliquait `CLAUDE.md`) **SUPPRIMÉ**.
- ⏸️ `_canary_inject.py` / `_build_rag_prefix` (`project_session_15`) — à vérifier en traitant session_15 (déféré).

**ORPHELINS (#1) — traité :** les 6 hors-index résolus → **supprimés** : `ameliorations_futures`, `feedback_mesressources`, `project_admin_activites_future`, `feedback_methode` (workflow obsolète → `ROADMAP.md` mort, supplanté par `feedback_regles_travail_aschool`), `feedback_logo_header` (supplanté par `feedback_header_size`) ; **`project_future_improvements` SUPPRIMÉ** : les idées vivent déjà dans le réservoir `TABLEAU-DE-BORD.md` (items 18/22/08/27 + modération ; dictée & bannière faites) — une 2e liste d'idées en mémoire = pilote concurrent, interdit par les règles.

**VÉRIFIÉS DURABLES (KEEP) :** `project_auth_status`, `project_vps`, `project_vps_architecture`, `project_feedback_architecture`, `project_profil_multi_matiere_niveau`, `project_tracker_reforme`, `project_chantier_aide_refonte`, `project_quiz_interactif`, `project_tagline_apprentissage`, `project_assistant_utilisation`, `project_logo_aschool`, `project_fonctionnalites_operationnelles`.

## Phase NETTOYAGE (A) — à faire APRÈS l'audit (vide pour l'instant)

## Phase B — comportement (à traiter séparément, APRÈS A)
Mécanique vérifiée : aucun hook ne peut **forcer** Claude à vérifier avant de parler
(injection de contexte = « advisory »). On ne vise donc pas 100 % — on **affame** la source
et on **relève le plancher**.

**Règle générale portable (à porter dans `~/.claude/CLAUDE.md` global — en attente du GO) :**
1. **Test d'admission avant d'écrire un fait en mémoire/`CLAUDE.md`** : « Est-ce que ça peut
   devenir faux sans que personne ne réécrive ce fichier ? »
   - **Oui → VOLATIL → interdit ici** (statuts « fait/livré/en cours », comptes, versions,
     schémas de tables, listes de fichiers, routes). Lu **en direct** dans la source
     (code/git/base). Au plus, un **pointeur** (« le schéma vit dans `models_db.py` »).
   - **Non → DURABLE → autorisé** (conventions, décisions d'archi, préférences, standards).
2. **Mémoire = indice, jamais preuve.** Tout fait technique (route, table, fichier, port,
   statut, version, compte) ne s'affirme qu'**après avoir ouvert la source et cité
   `fichier:ligne`**. Sinon : « pas vérifié » + aller voir AVANT de parler.
3. **Aucun journal ni statut d'avancement** en mémoire/`CLAUDE.md` ; l'avancement vit dans
   le code/git/les trackers, lu en direct.

**Appoint (optionnel) :** hook global `UserPromptSubmit` réinjectant le point 2 à chaque
message (nudge, pas verrou).
