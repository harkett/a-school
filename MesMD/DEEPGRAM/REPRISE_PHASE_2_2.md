# Handoff Phase 2.2 — Intégration STT Deepgram

> Document de reprise pour nouvelle conversation Claude. Écrit en fin de session du 16/05/2026 à la clôture de **Phase 2.1** (route WebSocket `/api/transcribe/stream`). Prochaine étape : 7 tests backend automatisés.

---

## Contexte général

- Projet **aSchool** — plateforme web de génération d'activités pédagogiques (FastAPI + React, prod aschool.fr)
- Chantier en cours : **migration dictée vocale Web Speech API → Deepgram Nova-3 streaming**
- Spec canonique : `MesMD/DEEPGRAM/SPEC_DEEPGRAM_STT.md` (v1.1)
- Suivi des phases : `MesMD/DEEPGRAM/ROADMAP_PHASES.md` (checklist + détail par phase + notes de vigilance)
- **Méthode de travail** (règle validée 16/05/2026) :
  - **2 réfléchissent** (utilisateur chef de projet + Claude)
  - **1 seul écrit le code = Claude** (édition, write, mv, rm)
  - **Propositions indifférentes** : l'un ou l'autre propose, on s'aligne, Claude édite
  - **Exception** : les secrets (`.env` valeur de clé) — utilisateur colle la vraie valeur après placeholder
  - **Anti-quiproquo** : si silence des deux côtés, Claude propose en premier
  - Yes/no avant action environnement (pip install, git push, suppression fichier)
  - **Handoffs sans pré-décider** : les recos non tranchées vont dans "Décisions ouvertes", pas en acquis (apprentissage Phase 2.1)

---

## Conventions codebase (à respecter scrupuleusement)

- **SQLAlchemy ORM** (pas raw SQL), `Base.metadata.create_all()` au démarrage
- **`logging.getLogger(__name__)`** partout, jamais `print` en code prod
- **`@dataclass`** stdlib, typing moderne (`list[str]`, `| None`, `from __future__ import annotations` quand nécessaire)
- Scripts standalone à la racine (`test_*.py`), **pas pytest** dans ce projet
- **Instance module-level** pour singletons stateful (cf. `session_tracker.py:tracker`)
- **Factory** pour stateless (cf. `backend/stt/__init__.py:get_stt_provider`)
- **`os.getenv()`** direct (pas Pydantic Settings)
- Hiérarchie d'exceptions métier : `STTError` racine → `STTRateLimitError`, `STTServiceUnavailableError`, `STTCreditExhaustedError`, `STTSessionTimeoutError`
- `_PROVIDERS` dict pour les mappings extensibles (cf. `__init__.py`)
- **Pattern asyncio Phase 2.1 (validé) à reproduire pour toute route WS future** : `create_task` explicite + `cancel`-in-finally + `await gather(*, return_exceptions=True)` pour drain. `asyncio.gather` pur ne cancelle pas les sœurs — risque de leak zombie Deepgram.

---

## État actuel — Phase 2 (1/2 items)

Phase 2.1 livrée et commitée :

| Commit | Phase | Scope |
|---|---|---|
| `9256cab` | **2.1** | **Route WS `/api/transcribe/stream` (auth + tracker + 3 pumps + cleanup) + smoke test rejet** |
| `8872dfe` | 1.6 | Factory `get_stt_provider()` avec switch `STT_PROVIDER` |
| `536682d` | 1.5 | DeepgramProvider + test d'intégration |
| `b4ba5da` | 1.4 | STTSessionTracker (Lock+int) + test concurrence |
| `fd5f0e4` | 1.3 | Interfaces async + clean break Groq Whisper batch |
| `ca42905` | 1.2 | BDD STT (4 tables + seed) |
| `0d85c34` | 1.1 | `.env.example` STT (17 variables) |

**10 commits locaux ahead, jamais pushés** (push prévu Phase 5.5).

TodoWrite cross-session : 8 completed (Phase 1.1 → 2.1) / 11 pending (Phase 2.2 → 5.5).

Asset utile présent dans `MesMD/DEEPGRAM/test_audio.wav` (PCM 16 kHz mono linear16, utilisé Phase 0.2/1.5).

---

## SDK et versions clés

- **`deepgram-sdk==3.11.0`** (pinned dans `requirements.txt`)
- API 3.x : `from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents`
- Python 3.12, venv `.venv` (utilisé par `run.ps1`)
- Région **`us`** en Phase 1 (migration EU bloquante avant scale >50 profs, cf. spec §3.4)
- `websockets==16.0` côté tests Python (déjà dispo dans le venv)
- `fastapi.testclient.TestClient` utilisable pour tests in-process (utilisé Phase 2.1 smoke)

---

## Prochaine étape — Phase 2.2 : 7 tests wscat backend

Spec détaillée : `MesMD/DEEPGRAM/SPEC_DEEPGRAM_STT.md` §12.2.

Objectif : valider la robustesse de la route `/api/transcribe/stream` sur les 7 scénarios identifiés, via un script Python automatisé.

### Les 7 scénarios

| # | Scénario | Code attendu | Setup |
|---|---|---|---|
| 1 | Sans cookie | denial 403 (4401 déclaratif) | rien — **déjà smoke Phase 2.1** |
| 2 | Cookie invalide / expiré | denial 403 (4401 déclaratif) | rien — **déjà smoke Phase 2.1** |
| 3 | Cookie valide → accept + audio | reception transcripts OU close 4502 | cookie login local + push audio |
| 4 | Saturation | denial 403 (4429 déclaratif) | `STT_MAX_CONCURRENT_SESSIONS=1`, 2 sessions concurrentes |
| 5 | Crédit épuisé | close 4402 | mock provider OU clé invalidée OU skip |
| 6 | Idle timeout | close 4408 IDLE | `STT_SESSION_IDLE_TIMEOUT_SECONDS=2`, attendre 3s |
| 7 | Max duration + warning EXPIRING_SOON | `session_warning` puis close 4408 | `STT_SESSION_MAX_DURATION_SECONDS=70` (>60 pour avoir le warning) |

### Point de départ

Le fichier `test_phase21_smoke.py` (commit `9256cab`) couvre déjà les scénarios 1 et 2. Phase 2.2 le **promeut** vers `test_phase22.py` (ou enrichit le smoke selon préférence) avec les 7 scénarios. Convention repo : test_*.py standalone à la racine.

---

## Décisions ouvertes à trancher en début de Phase 2.2

**Rien n'est pré-tranché. Tout est à valider explicitement avant la première ligne de code Phase 2.2.**

### Décisions techniques — Audio & route param (3 imbriquées)

**D1. Encoding utilisé pour les tests : LINEAR16 ou Opus muxé Python ?**

- LINEAR16 : le `test_audio.wav` est déjà PCM 16 kHz mono linear16, prêt à pousser. Aucune dépendance audio à ajouter.
- Opus muxé : plus représentatif du runtime réel (MediaRecorder navigateur envoie de l'Opus), mais nécessite `pyogg` ou `ffmpeg-python` en dépendance test — pollue requirements.txt.

→ **Reco (non tranchée)** : LINEAR16. L'Opus réel sera de toute façon validé en Phase 3.2 avec MediaRecorder Edge.

**D2. Si LINEAR16 : la route accepte-t-elle un paramètre d'encoding ?**

Aujourd'hui [backend/routers/transcribe.py:130](backend/routers/transcribe.py#L130) appelle `await provider.create_session()` sans config → utilise `STTSessionConfig()` par défaut → `encoding="opus"`. Pour qu'un test LINEAR16 passe sans erreur Deepgram, il faut un mécanisme d'override :

- Option α — query string : `ws://.../api/transcribe/stream?encoding=linear16` lu via `websocket.query_params`
- Option β — header : `X-STT-Encoding: linear16`
- Option γ — hardcode opus + accepter que LINEAR16 envoyé comme Opus va probablement faire échouer Deepgram (Phase 2.2 = test de saturation/timeouts uniquement, on skip scénario 3 audio réel)

→ **Reco (non tranchée)** : Option α. Query string plus simple à tester en wscat/Python WS, plus visible dans les logs. Modif `transcribe.py` **~10 lignes** :
  1. Lecture query string : `encoding = websocket.query_params.get("encoding", "opus")` (1 ligne)
  2. Whitelist D3 si retenue : ~5 lignes (vérif `if encoding not in {"opus", "linear16"}: await websocket.close(code=1011); return` + log)
  3. Log du paramètre reçu : `logger.info("STT encoding=%s requested — user=%s", encoding, user)` (traçabilité)
  4. Instanciation `STTSessionConfig(encoding=encoding, sample_rate=..., language=..., ...)` en **conservant explicitement** les autres champs (sinon `STTSessionConfig(encoding=...)` reset silencieusement `sample_rate`, `language`, `interim_results`, `smart_format`, `endpointing_ms`, `dictation`, `keyterms` aux defaults dataclass — piège à éviter)

**D3. Si paramètre d'encoding accepté : whitelist côté backend ?**

Sans whitelist, un client malveillant peut injecter `?encoding=garbage` qui sera forwarded à Deepgram. Comportement Deepgram inconnu sur encoding invalide — peut-être 400 brut, peut-être crash.

→ **Reco (non tranchée)** : whitelist `{"opus", "linear16"}` côté route, sinon close 1011 ou refus 4401. À discuter selon le niveau de paranoia attendu.

### Décisions stratégie tests (3 pré-requis setup)

**D4. Scénario 3 — Cookie de login pour test authentifié : comment l'obtenir ?**

Options :
- α — Endpoint `/api/auth/login` réel : POST credentials prof réels → récupérer cookie `aschool_access` → injecter dans WS test. Plus fidèle au chemin réel.
- β — JWT forgé en Python avec `SECRET_KEY` du `.env` local + `auth_lib.create_access_token("test@example.com")`. Plus rapide, pas besoin d'un compte prof réel en local.
- γ — Compte de test dédié seed BDD spécifique (`stt_test@aschool.local`).

→ **Reco (non tranchée)** : β si on veut un test indépendant du seed BDD, α si on veut un test "end-to-end" complet incluant le flow login. À trancher selon le niveau de couverture visé.

**D5. Mutation des variables d'env entre scénarios — comment ?**

Les scénarios 4, 6, 7 nécessitent des valeurs différentes de `STT_MAX_CONCURRENT_SESSIONS`, `STT_SESSION_IDLE_TIMEOUT_SECONDS`, `STT_SESSION_MAX_DURATION_SECONDS`. Or ces variables sont lues à 2 endroits :
- `STT_MAX_CONCURRENT_SESSIONS` : lu au démarrage du module dans `backend/stt/session_tracker.py:69` (instance module-level)
- `STT_SESSION_IDLE_TIMEOUT_SECONDS` / `STT_SESSION_MAX_DURATION_SECONDS` : lus **à l'ouverture de chaque session** dans `backend/routers/transcribe.py:123-124` (au début de `_run_stt_session`). Donc monkeypatch `os.environ` AVANT l'ouverture WS suffit pour D5β — pas besoin de toucher au code. **À NOTER** : ces valeurs sont **figées pendant la session en cours** (pas relues en continu), donc on ne peut pas raccourcir un timeout au milieu d'un test.

Options :
- α — Restart du serveur entre chaque scénario avec env vars différentes (lourd, lent, pas dans une seule exécution Python)
- β — Monkeypatch `tracker._max` directement avant le scénario 4 + `os.environ[...]` pour 6/7 (rapide, mais touche aux internes)
- γ — Réécrire `STTSessionTracker` pour relire `max_concurrent` à chaque `acquire()` (refactor mineur, plus propre)

→ **Reco (non tranchée)** : β pour rester dans un seul script + ne pas modifier le code prod pour faire fonctionner les tests. γ serait plus propre mais c'est un refactor à débattre.

**Note de cohérence D5γ + R4 (opportunité two-for-one)** : si Phase 2.2 décide D5 = γ (refactor `STTSessionTracker` pour relire `max_concurrent` à chaque `acquire()`), ça ouvre naturellement l'opportunité de traiter **R4** (compteur agrégé rejets pré-accept, cf. section "Dettes TRACKER" ci-dessous) dans la foulée — un seul commit touche `session_tracker.py`, ajoute le relire-à-chaque-acquire ET le compteur agrégé `(anonymous, bad_token)`. À discuter en début Phase 2.2 selon l'ambition de la session.

**D6. Scénario 5 (crédit épuisé) — comment simuler ?**

Le `DeepgramProvider._map_deepgram_error` détecte les erreurs `402 / payment / insufficient / credit` et raise `STTCreditExhaustedError`. Pour déclencher ça dans un test :
- α — Mock provider injecté via `STT_PROVIDER=mock` qui raise `STTCreditExhaustedError` au premier `send_audio()` — nécessite ajouter une classe `MockExhaustedProvider` dans `backend/stt/__init__.py:_PROVIDERS`. Propre, isolé.
- β — Forcer une clé Deepgram invalidée volontairement (`DEEPGRAM_API_KEY=invalid`). Mais Deepgram retournera probablement 401, pas 402 → mappage `STTServiceUnavailableError`, pas `STTCreditExhaustedError`. **Ne couvre pas le bon scénario.**
- γ — Skip et reporter à Phase 4.2 (cron monitoring crédit) où on aura plus de contexte sur la vraie réaction Deepgram en cas de crédit à 0.

→ **Reco (non tranchée)** : α. Le mock est aligné sur la philosophie multi-provider du repo (factory + `_PROVIDERS` dict) — ajouter `mock_exhausted` est une ligne. Préfère γ si on veut éviter d'ajouter du code juste pour les tests.

---

## Référence aux décisions déjà actées Phase 2.1 — NE PAS REJOUER

- **Auth WS = cas C** : lecture directe `websocket.cookies.get("aschool_access")` + `auth_lib.verify_access_token(token)`, pas de Depends() partagé. Wrap défensif `try/except Exception` pour cookies tordus (cf. transcribe.py:53-58).
- **Pattern asyncio = create_task + cancel-in-finally** : impératif. `asyncio.gather()` pur ne cancelle pas les sœurs sur exception → leak Deepgram. Voir transcribe.py:189-208 pour la référence.
- **Watchdog avec warning T-60s** (option α de la spec §5.3) : implémenté, validé. Pas de changement à prévoir.
- **Codes pré-accept (4401, 4429) sont déclaratifs** : Starlette ne peut pas transiter un code WS sur handshake non accepté → client voit HTTP 403. Documenté dans le docstring de `stt_stream`. **À NE PAS oublier en Phase 3.1 frontend** : "connection failed" doit être interprété comme "auth manquante ou saturation".
- **Codes post-accept (4402, 4502, 4408, 1011) transitent correctement** comme close frames.
- **Log AVANT close** : pattern adopté Phase 2.1 (assure la trace d'audit même si close raise). Close wrappé en try/except + log warning si raise.
- **`duration_s` mesure le temps avant `session.close()`** — sémantique "durée audio reçue", pas "durée totale". Acté comme plus pertinent métier.

---

## Dettes notées au TRACKER

Toutes consignées dans `MesMD/TRACKER.md` section `## NON RETENU — À reconsidérer plus tard` :

1. **STT Deepgram — Observabilité rejets pré-accept** (16/05) — Compteur agrégé denials avant `accept()` (anonymous + bad_token) dans `STTSessionTracker` ou metric process-local, exposable via `/admin/stt-status` Phase 4.1. À traiter Phase 2.2 ou 4.
2. **Dictée Deepgram — points de vigilance Phase 3.2** (16/05) — Smart Format agressif sur nombres + "hypoténuse" substituée. À retester avec MediaRecorder Opus + vraie voix (Phase 3.2, conditions différentes du test PCM Phase 0.2/1.5).

Ces dettes ne bloquent PAS Phase 2.2. Le point 1 peut éventuellement être implémenté en 2.2 si on touche déjà `STTSessionTracker` pour le scénario 4 (D5γ — refactor pour relire `max_concurrent` à chaque acquire) — mais ce n'est pas un pré-requis.

---

## Pré-conditions environnement

- `.\run.ps1` lance backend (:8000) + frontend (:5173). Smoke test Phase 2.1 a démarré sans erreur d'import.
- Backend healthy → `GET /api/health` retourne `{"status":"ok","service":"aSchool API"}`.
- Routes WS absentes de `/openapi.json` (limitation FastAPI/OpenAPI 3.x) — vérifier l'enregistrement via `app.routes` introspection (cf. smoke Phase 2.1).
- `DEEPGRAM_API_KEY` configurée dans `.env` (sinon `DeepgramProvider._client = None` et raise `STTServiceUnavailableError` au `create_session`).

---

## Message d'amorçage pour la nouvelle conversation

> À coller intégralement dans le premier message de la prochaine session.

```
Reprise projet aSchool — intégration STT Deepgram, Phase 2.2 (7 tests wscat backend).

Contexte général
- Migration dictée vocale Web Speech API → Deepgram Nova-3 streaming
- Spec : MesMD/DEEPGRAM/SPEC_DEEPGRAM_STT.md (v1.1)
- Suivi des phases : MesMD/DEEPGRAM/ROADMAP_PHASES.md (checklist)
- Handoff détaillé : MesMD/DEEPGRAM/REPRISE_PHASE_2_2.md — à lire en début de session
- Convention de travail validée 16/05/2026 : 2 réfléchissent, 1 seul écrit (Claude).
  Yes/no avant action environnement. Handoffs sans pré-décider.

Conventions codebase
- SQLAlchemy ORM, Base.metadata.create_all() au démarrage
- logging.getLogger(__name__) partout
- @dataclass stdlib, typing moderne (list[str], | None)
- Scripts standalone à la racine (test_*.py), pas pytest
- Instance module-level pour singletons stateful (tracker)
- Factory pour stateless (get_stt_provider)
- os.getenv() direct (pas Pydantic Settings)
- Pattern asyncio WS = create_task + cancel-in-finally OBLIGATOIRE (cf. transcribe.py Phase 2.1)

État actuel — Phase 2.1 COMPLÈTE (8/19 items global)
- Items completed : 1.1, 0.2, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1
- 10 commits locaux non-pushés (push prévu Phase 5.5)
- Phase 2.1 = route WS /api/transcribe/stream (commit 9256cab) opérationnelle
- Smoke test test_phase21_smoke.py couvre les scénarios 1 et 2 (rejet sans cookie / cookie bidon)

Prochaine étape — Phase 2.2 : 7 tests wscat backend
Objectif : valider robustesse de la route sur 7 scénarios (sans cookie, cookie bidon,
cookie valide+audio, saturation, crédit épuisé, idle timeout, max duration + warning).
Approche pressentie : script Python hybride test_phase22.py (à confirmer).

Décisions ouvertes à trancher en début de Phase 2.2 (6 décisions imbriquées)
D1. Encoding test : LINEAR16 ou Opus muxé Python ?
D2. Route paramétrable encoding : query string / header / hardcode ?
D3. Whitelist côté backend si paramétrable ?
D4. Scénario 3 cookie login : endpoint /api/auth/login / JWT forgé / compte seed ?
D5. Mutation env vars entre scénarios : restart / monkeypatch / refactor tracker ?
D6. Scénario 5 crédit épuisé : MockExhaustedProvider / clé invalide / skip vers 4.2 ?

Recos non tranchées dans le handoff : LINEAR16, query string, whitelist oui,
JWT forgé, monkeypatch, mock provider. À re-discuter et trancher explicitement.

Items restants après 2.2 : 10 (3.1, 3.2, 4.1, 4.2, 4.3, 5.1 → 5.5)

Méthode : tu lis le handoff, tu critiques mes recos D1-D6, on aligne, je code.
```

---

## Checklist "avant de couper" (validée 16/05/2026)

- [x] Phase 2.1 commitée proprement (`9256cab`)
- [x] Note TRACKER ajoutée — section `## NON RETENU` (compteur agrégé pré-accept rejects)
- [x] `MesMD/DEEPGRAM/ROADMAP_PHASES.md` créé avec checklist + détail par phase
- [x] Phase 2.1 cochée dans la checklist ROADMAP_PHASES, SHA `9256cab` consigné dans la table de détail
- [x] Smoke test `test_phase21_smoke.py` commité avec la route (scope unique 2.1)
- [x] Aucun pre-décidé dans le handoff (D1-D6 toutes ouvertes avec reco notée)
- [ ] Commit handoff Phase 2.2 — à faire avant fin session (scope `docs(deepgram): handoff Phase 2.2`)

---

## Roadmap restante (10 items après Phase 2.2)

2.2 (7 tests wscat) → 3.1 (frontend WS + purge dead code TexteSource) → 3.2 (tests Edge MediaRecorder Opus + vraie voix) → 4.1 (admin lecture seule) → 4.2 (cron crédit) → 4.3 (alertes clé) → 5.1 (iOS PWA) → 5.2 (CGU RGPD) → 5.3 (TRACKER sync — audit final, pas traitement) → 5.4 (Aide) → 5.5 (push v3.3.0 MINOR + sync School.jsx afia.fr)

**Note d'ordre crucial** : Phase 3.2 (tests vraie voix) DOIT être close avant d'attaquer Phase 4.x. Sinon on bâtit un monitoring sur une route encore en stabilisation = dette assurée.
