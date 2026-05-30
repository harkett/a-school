# COMPTE-RENDU aSchool — État du projet

> **Date :** 31/05/2026
> **Objet :** état réel du projet (fait / commencé non fini / jamais entamé) + diagnostic de saturation.
> **Statut :** document de travail destiné à être décortiqué en équipe. Projet gelé depuis le 18/05.

---

## Méthode & fiabilité

Basé sur : lecture intégrale de `MesMD/` + docs de lancement (`MesAdmin/`) ; deux passes d'audit code automatisées ; **et re-vérification manuelle** des points porteurs ou contradictoires (tests, code dormant L37, EyeIcon, état git) via `git` / `grep` / lecture directe — c'est-à-dire des faits **déterministes et reproductibles**, pas des conclusions d'agent.

Chaque fait ci-dessous est vérifié, sauf mention explicite `⚠️ NON VÉRIFIÉ`. Le premier audit automatisé avait produit deux erreurs (« zéro test », « EyeIcon = code mort ») : **les deux ont été détectées par recoupement et corrigées** — elles figurent ci-dessous pour traçabilité.

**Principe retenu pour la fiabilité :** un fait vérifiable (un endpoint existe-t-il ? un import est-il présent ? combien de commits d'avance ?) a une réponse fixe que `grep`/`git` redonnent à l'identique. On ne tranche jamais un fait par « avis d'agent » — l'agent trouve la piste, la commande confirme.

---

## 0. Synthèse en une phrase

Le **produit est mature et complet en local**, mais **`main` est à +33 commits de `origin/main` (dernier commit le 18/05)** : une grande partie de ce qui est documenté « livré » **n'est pas déployé en production**. Le projet est gelé au milieu du chantier Deepgram. La saturation n'est pas technique — elle est dans l'écart entre l'état local, l'état déployé et l'état documenté.

---

## 1. Ce qui est FAIT et MARCHE (vérifié dans le code)

Cœur produit codé, câblé, cohérent. 18 routers montés + 2 routes inline, ~90 endpoints (`backend/main.py`).

| Bloc | Endpoint(s) | État |
|---|---|---|
| Générateur d'activités | `POST /api/generate` (+ few-shot, gates RAG) | OK |
| Séquences (L1) | `POST /api/generate-sequence` + CRUD `mes-sequences` + `mon-reseau/sequences` | OK |
| Optimiseur (L3) | `POST /api/optimize-sequence` | OK |
| Ambiguïtés (L2) | `POST /api/detect-ambiguites` | OK |
| Analyseur de consignes (L5) | `POST /api/analyser-consigne` | OK |
| Auth | 12 endpoints (signup / login / refresh / reset / heartbeat / logout…) | OK |
| Admin | 29 endpoints (sessions, audit, alertes, maintenance, mail groupé, stats) | OK |
| Profil, Mes activités (CRUD), Mon réseau, OCR, Feedback, Votes, Fiches, Stats (9) | | OK |

**Cohérence frontend ↔ backend (vérifiée) :** 103 appels API sur 47 fichiers. **Aucun appel frontend vers un endpoint inexistant.** Seul `GET /api/health` n'est pas consommé par le front (normal : sonde monitoring). Routage `Sidebar.jsx` ↔ `App.jsx` cohérent, **aucun composant frontend orphelin**.

➡️ La proposition de valeur — générer activités et séquences — fonctionne.

---

## 2. Ce qui est COMMENCÉ mais PAS FINI

### 🔴 Écart prod ↔ local — le fait le plus important
**`main` est à +33 commits de `origin/main`, dernier commit le 18/05/2026**, plus des modifications non commitées. La prod (`aschool.fr`) se déploie depuis `origin/main`.
**Conséquence :** tout le travail depuis mi-mai — RAG, fallback Groq, errorDialog, L5, optimiseur inline, finalisation branding, **et l'intégralité du chantier Deepgram** — **n'est pas déployé**. Ce que les docs disent « livré » est livré *en local*.

### 🔴 Dictée Deepgram — code complet, jamais validé, non déployé
- Code présent et câblé : WebSocket `/api/transcribe/stream` (`backend/routers/transcribe.py`, montée), hook `frontend/src/hooks/useTranscribeStream.js`, bouton dans `frontend/src/components/TexteSource.jsx`.
- **Mais** : la Phase 3.2 (runs vocaux R0→R6) **n'a jamais été exécutée** → qualité réelle non validée. Le chemin **opus** de bout en bout n'est couvert par **aucun test** (les tests utilisent linear16).
- C'est le **goulot** : [D12](MesMD/BOUSSOLE/D12.md) (Activité 100 %) et [D13](MesMD/BOUSSOLE/D13.md) (Séquences 100 %) sont explicitement en attente de D09.
- *Note : l'alternative Whisper auto-hébergé a déjà été évaluée et écartée (`SPEC_DEEPGRAM_STT.md` §16) — décision actée, non rouverte.*

### 🟠 RAG — DEV uniquement, 1 corpus sur 96
Branché **seulement** sur `/api/generate`, derrière 3 gates (`RAG_ENABLED` défaut **false**, matière = maths, niveau = cycle 4), collection `maths_cycle4`, fallback silencieux (`backend/routers/generate.py`). 2 `TODO` actifs (filtre niveau désactivé ; `top_k=4` non calibré). Hébergement prod non décidé. Corpus indexé : **1/96** (`maths_cycle4`).

### 🟠 L37 Affinage de séquence — code dormant (vérifié)
~45 lignes dans `backend/routers/sequence.py` : classes `ChatMessage` (l.31), `AffinerRequest` (l.36), `RegenererRequest` (l.47) + prompts `_SYSTEM_AFFINER` (l.98), `_PROMPT_REGENERER` (l.113). **Aucun endpoint** (`affiner-sequence` / `regenerer-sequence` n'existent nulle part) et **aucun appel frontend**. Bloque [D13](MesMD/BOUSSOLE/D13.md).

### 🟡 Audit « Activité » du 15/05 — 9 cases P2→P5 non traitées
auto-save sans try/catch (perte silencieuse possible), erreurs 401/Groq génériques, compteur few-shot localStorage désynchro BDD, liste MATIERES dupliquée ×3, etc. (cf. [TRACKER](MesMD/TRACKER.md)).

---

## 3. Ce qui n'a JAMAIS été entamé

~33 des 39 items du backlog, dont des « faciles, forte valeur » :

- **L04 Détecteur d'équité** : la page `equite` n'affiche qu'un placeholder « en cours de développement » — **pas de backend ni de composant** (vérifié).
- **I01 Pages légales CNIL** : rédigées dans `CNIL/`, **jamais intégrées au React** (risque réglementaire réel pour un service avec utilisateurs).
- **I05 /contact · I06 Civilité M./Mme · I02 Email admin→prof · I07 Onboarding J+2/7/14** (chacun 2h–3j).
- **L28 Remédiation · L29 Mode expérience prof · L30 DYS/FLE · L31 Appréciations bulletins · L32/33/34 Visuels/Mémo/Créativité · L35 Versioning séquences** (décrit dans les fiches comme « le vrai moat »).
- RAG-consommateurs (L25 ; L36 corpus MEN à **1/96**), Quiz interactif #17, Google OAuth #24, Théâtre #22, Supérieur #21.
- **Dégraissage documentaire déjà identifié par l'équipe** : [D11](MesMD/BOUSSOLE/D11.md) (TRACKER 586→150 lignes) + [D10](MesMD/BOUSSOLE/D10.md).

---

## 4. TESTS — vérifié (correction d'une erreur d'audit)

Le premier audit affirmait « zéro test » : **FAUX**. Il existe **5 fichiers `test_*.py` à la racine** + 2 scripts RAG (`backend/rag/_test_retrieve.py`, `_canary_inject.py`, marqués « jetables / à supprimer »).

**Mais le constat de fond est confirmé, et il est sévère :** **les 5 tests portent à 100 % sur la brique STT/Deepgram** (route WS, `STTSessionTracker`, `DeepgramProvider`) + 1 script de connexion SMTP.

| Module / endpoint | Testé ? |
|---|---|
| `transcribe` (WS STT), `STTSessionTracker`, `DeepgramProvider` | **OUI** |
| RAG `retrieve` | Partiel (script manuel non-assertif) |
| `/api/generate`, `/api/generate-sequence`, `/api/detect-ambiguites`, `/api/analyser-consigne`, `/api/optimize-sequence` | **NON** |
| Flux `auth` (signup / login / reset / refresh) | **NON** |

Ce sont des scripts standalone (`python test_x.py`), pas une suite pytest.
➡️ L'effort de test est allé à 100 % sur l'**optionnel** (dictée), 0 % sur l'**essentiel**.

---

## 5. Critiques & diagnostic de saturation

Le système documentaire est cohérent et discipliné — **le problème n'est pas le désordre, c'est la trajectoire** :

1. **33 commits non poussés depuis le 18/05.** L'écart prod ↔ local est devenu un gouffre. La règle « pas de push sans validation » (saine) + l'accumulation = **paralysie de déploiement**.
2. **Un seul goulot gèle tout** : Deepgram (D09) bloque D12 + D13 → bloque la validation pilotes → qui est l'objectif de la phase actuelle ([PLAN_LANCEMENT](MesAdmin/PLAN_LANCEMENT_ASCHOOL.md) : 10 inscrits / 100 activités visés mai 2026).
3. **Décalage de phase** : le produit est en **phase de lancement** (recrutement pilotes en cours), mais l'énergie va dans l'ingénierie (Deepgram, RAG) plutôt que « déployer + faire valider par 3 profs ». Symptôme : `PLAN_LANCEMENT §10` est périmé (liste partage / export PDF / matières comme « à faire » alors qu'ils sont livrés).
4. **Build-ahead** : RAG (1/96), L37 dormant, corpus MEN — fondations posées avant le besoin prouvé par les pilotes.
5. **Pas de filet sur le cœur** : zéro test sur les 5 endpoints centraux → toute reprise après le gel se fait à l'aveugle.

---

## 6. Pourquoi l'efficacité de l'assistant a baissé (cause cernée en session)

Ni la complexité, ni les docs. La cause : **parler avant d'avoir lu** — proposer une solution déjà tranchée (Whisper, §16), qualifier de « fouillis » un système réfléchi, annoncer « aucune mémoire » alors que `CLAUDE.md` (mémoire tracée, chargée à chaque session) était disponible. Les deux agents d'audit ont reproduit la même faute à leur échelle (« zéro test », « EyeIcon mort ») : **conclure vite sans vérifier.**

**Garde-fou mis en place :** 8 règles de conduite ajoutées à `CLAUDE.md` (section « Règles de conduite Claude — absolues »), dont : pas de réponse hâtive ; ne jamais présenter une supposition comme une certitude ; vérifier avant d'affirmer ; rester dans le périmètre ; ne rien exécuter sans validation. + re-vérification systématique de toute affirmation d'agent porteuse.

---

## Limites assumées de ce CR (`⚠️ NON VÉRIFIÉ`)

- L'application n'a **pas été exécutée** (sandbox) : « aucune erreur au build » est inféré de l'analyse statique, pas d'un run réel.
- Présence / format de l'asset `MesMD/DEEPGRAM/test_audio.wav` non vérifiés.
- Usage de `/api/health` par un monitoring externe (VPS/systemd) non vérifié (hors périmètre du dépôt).

---

*Généré avec aSchool — analyse d'état, 31/05/2026.*
