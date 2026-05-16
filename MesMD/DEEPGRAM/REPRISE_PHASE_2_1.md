# Handoff Phase 2.1 — Intégration STT Deepgram

> Document de reprise pour nouvelle conversation Claude. Écrit en fin de session du 16/05/2026 à la clôture **complète de Phase 1** (fondations backend). Prochaine étape : la route WebSocket — gros morceau du projet.

---

## Contexte général

- Projet **aSchool** — plateforme web de génération d'activités pédagogiques (FastAPI + React, prod aschool.fr)
- Chantier en cours : **migration dictée vocale Web Speech API → Deepgram Nova-3 streaming**
- Spec canonique : `MesMD/DEEPGRAM/SPEC_DEEPGRAM_STT.md` (v1.1)
- **Méthode de travail** (règle validée 16/05/2026) :
  - **2 réfléchissent** (utilisateur chef de projet + Claude)
  - **1 seul écrit le code = Claude** (édition, write, mv, rm)
  - **Propositions indifférentes** : l'un ou l'autre propose, on s'aligne, Claude édite
  - **Exception** : les secrets (`.env` valeur de clé) — utilisateur colle la vraie valeur après placeholder
  - **Anti-quiproquo** : si silence des deux côtés, Claude propose en premier
  - Yes/no avant action environnement (pip install, git push, suppression fichier)

---

## Conventions codebase (à respecter scrupuleusement)

- **SQLAlchemy ORM** (pas raw SQL), `Base.metadata.create_all()` au démarrage
- **`logging.getLogger(__name__)`** partout, jamais `print` en code prod
- **`@dataclass`** stdlib, typing moderne (`list[str]`, `| None`, `from __future__ import annotations` quand nécessaire)
- Scripts standalone à la racine (`test_*.py`), **pas pytest** dans ce projet
- **Instance module-level** pour singletons stateful (cf. `session_tracker.py`, `database.py`, `limiter.py`)
- **Factory** pour stateless (cf. `backend/stt/__init__.py:get_stt_provider`)
- **`os.getenv()`** direct (pas Pydantic Settings)
- Hiérarchie d'exceptions métier : `STTError` racine → `STTRateLimitError`, `STTServiceUnavailableError`, `STTCreditExhaustedError`, `STTSessionTimeoutError`
- `_PROVIDERS` dict pour les mappings extensibles (cf. `__init__.py`)

---

## État actuel — Phase 1 COMPLÈTE (7/7 items)

Tous les items fondation backend sont commités localement (9 commits ahead, jamais pushés — push prévu Phase 5.5) :

| Commit | Phase | Scope |
|---|---|---|
| `0d85c34` | 1.1 | `.env.example` (17 variables STT) |
| `025b4fa` | Pre-1.2 | logging + routers consigne/transcribe + col partagee (WIP séparé) |
| `ca42905` | 1.2 | BDD STT (4 tables + seed 8 messages + 80 keyterms) |
| `50485c2` | Pre-1.3 | OCR errors modal + dictée feedback visuel TexteSource (WIP séparé) |
| `fd5f0e4` | 1.3 | Interfaces async + clean break Groq Whisper batch |
| `b4ba5da` | 1.4 | STTSessionTracker (Lock+int) + test concurrence 41/40 |
| `536682d` | 1.5 | DeepgramProvider + test d'intégration (Phase 0.2 close, 2/3 termes R1) |
| `981af30` | chore | Refonte TRACKER (PRIORITAIRE→BACKLOG) + notes vigilance Phase 3.2 |
| `8872dfe` | 1.6 | Factory `get_stt_provider()` avec switch `STT_PROVIDER` (multi-provider ready) |

TodoWrite : **7 completed (Phase 1.1, 0.2, 1.2, 1.3, 1.4, 1.5, 1.6)** + **12 pending** (Phase 2.1 → 5.5).

---

## SDK et versions clés

- **`deepgram-sdk==3.11.0`** (pinned dans `requirements.txt`)
- API 3.x : `from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents`
- Signature callbacks SDK 3.x : `async def _on_x(self, _self_unused, result, **kwargs)` (premier arg ignoré = ref connexion)
- WebSocket : `client.listen.asyncwebsocket.v("1")` ; `await connection.start(options)` / `.send(chunk)` / `.finish()`
- Région **`us`** en Phase 1 (migration EU bloquante avant scale >50 profs, cf. spec §3.4)
- Python 3.12, venv `.venv` (utilisé par `run.ps1`)

---

## Prochaine étape — Phase 2.1 : Route WebSocket `/api/transcribe/stream`

**C'est le gros morceau du projet.** Spec détaillée : `MesMD/DEEPGRAM/SPEC_DEEPGRAM_STT.md` §5.

Objectif : endpoint FastAPI WebSocket qui :

1. Authentifie le prof (JWT cookie httpOnly, comme `/api/generate`)
2. Réserve un slot via `stt_session_tracker.acquire()` (raise `STTRateLimitError` si 40 sessions concurrentes atteintes)
3. Récupère un provider via `get_stt_provider()`
4. Ouvre une `STTSession` Deepgram via `provider.create_session(config)`
5. Pont bidirectionnel :
   - Frontend → backend : chunks audio binaires (Opus en prod, linear16 en test) → `session.send_audio(chunk)`
   - Backend → frontend : transcripts JSON `{text, is_final, confidence, start, end}` issus de `session.receive_transcripts()`
6. Gère les timeouts : idle `STT_SESSION_IDLE_TIMEOUT_SECONDS=30s`, max `STT_SESSION_MAX_DURATION_SECONDS=300s` (raise `STTSessionTimeoutError`)
7. Cleanup propre dans `finally` : `session.close()`, release tracker, log audit BDD si table prévue

---

## Décisions ouvertes à trancher en début de Phase 2.1

Ces 3 points seront discutés AVANT d'écrire la moindre ligne de route :

1. **Mécanisme auth WebSocket exact** : JWT en cookie httpOnly comme `/api/generate` confirmé, mais comment FastAPI le lit-il sur un upgrade WS ? Inspecter `backend/auth.py` + `backend/routers/auth.py` (intouchables sans demande, cf. CLAUDE.md) — chercher si un middleware/dépendance existe déjà pour les WS.

2. **Emplacement du fichier route** :
   - Option A : enrichir le stub Phase 1.3 `backend/routers/transcribe.py` (déjà neutralisé HTTP 503)
   - Option B : créer `backend/routers/transcribe_stream.py` séparé (HTTP batch obsolète vs streaming = scopes différents)
   - À trancher après lecture du stub actuel
   - Ne pas oublier d'enregistrer le router dans `backend/main.py`

3. **Convention WebSocket existante dans le projet** : y a-t-il déjà des routes WS pour s'inspirer du style/imports ? Si non, on définit la convention ici. Grep `WebSocket` dans `backend/routers/*.py` au démarrage.

---

## Référence aux décisions déjà actées (Phase 1) — NE PAS REJOUER

- **R1** : 2/3 termes critiques au test d'intégration Phase 0.2 = `pass` avec warning (acceptable). Le critère 3/3 strict sera durci en CI plus tard quand on aura un `test_audio.wav` figé + stats de régression.
- **Plan B dictation** : `LiveOptions(**kwargs, dictation=cfg.dictation)` dans try/except `TypeError`, fallback sans la clé + warning log. Géré dans `deepgram_provider.py`.
- **Mutation `cfg.keyterms`** : corrigée en variable locale dans `create_session()`. Pas de side-effect sur la config passée.
- **Multi-provider switch** : implémenté via dict `_PROVIDERS` module-level dans `__init__.py`. Ajouter un provider = 1 import + 1 ligne dans le dict. `STTServiceUnavailableError` si valeur env inconnue.
- **Région us** : Phase 1 OK. **Bloquant avant scale >50 profs** — alarme à mettre en Phase 4.3 si pas avant. À vérifier que la spec §3.4 listait bien les conditions de migration EU.
- **Décisions techniques Phase 1.5 [1] à [10]** : toutes appliquées dans `deepgram_provider.py`. Voir spec §4-5 si besoin de relire.
- **`tasks cancelled error`** du SDK Deepgram au teardown : log ERROR inoffensif, comportement normal de `connection.finish()` qui annule les tâches WS internes. À ne pas paniquer.

---

## Dettes notées au TRACKER (à retester Phase 3.2)

1. **Smart Format Deepgram convertit agressivement les nombres** — "deux x au carré" transcrit "10 au carré". Tester avec/sans `smart_format=true` pour vocabulaire mathématique notationnel.
2. **"hypoténuse" substitué par "hypothèse" malgré keyterm boost** — substitution homophone non corrigée par 80 keyterms BDD chargés/injectés. Pistes : prononciation marquée, variant "l'hypoténuse" en plus, ou prompt système via `extra_params`.

Ces 2 points sont des signaux UX à confronter au vrai usage (MediaRecorder Opus + vraie voix live), pas des bugs Phase 1.5.

---

## Message d'amorçage pour la nouvelle conversation

> À coller intégralement dans le premier message de la prochaine session.

```
Reprise projet aSchool — intégration STT Deepgram, Phase 2.1 (route WebSocket).

Contexte général
- Migration dictée vocale Web Speech API → Deepgram Nova-3 streaming
- Spec complète : MesMD/DEEPGRAM/SPEC_DEEPGRAM_STT.md (v1.1)
- Handoff détaillé : MesMD/DEEPGRAM/REPRISE_PHASE_2_1.md — à lire en début de session
- Convention de travail (validée 16/05/2026) : 2 réfléchissent, 1 seul écrit le code = Claude.
  Propositions indifférentes (utilisateur ou Claude). Exception : secrets dans .env.
  Yes/no avant action environnement (pip, git, suppression fichier).

Conventions codebase
- SQLAlchemy ORM (pas raw SQL), Base.metadata.create_all() au démarrage
- logging.getLogger(__name__) partout
- @dataclass standard library, typing moderne (list[str], | None)
- Scripts standalone à la racine (test_*.py), pas pytest
- Instance module-level pour singletons stateful (tracker, database, limiter)
- Factory pour stateless (get_stt_provider)
- os.getenv() direct (pas Pydantic Settings)

État actuel — Phase 1 COMPLÈTE (7/7 items)
- Items completed : 1.1, 0.2, 1.2, 1.3, 1.4, 1.5, 1.6
- 9 commits locaux non-pushés (push prévu Phase 5.5)
- SDK pinné : deepgram-sdk==3.11.0 (API 3.x)
- Provider Deepgram opérationnel via get_stt_provider() (cf. backend/stt/__init__.py)
- STTSessionTracker prêt (40 sessions concurrentes max, asyncio.Lock+int)

Prochaine étape — Phase 2.1 : endpoint WebSocket /api/transcribe/stream
LE gros morceau du projet. Pont bidirectionnel auth → tracker.acquire() →
provider.create_session() → forward chunks audio + transcripts JSON →
gestion timeouts (idle 30s / max 300s) → cleanup finally.

Décisions ouvertes à trancher en début de Phase 2.1
1. Mécanisme auth WS exact (lire backend/auth.py + voir si dépendance FastAPI existe pour WS)
2. Emplacement fichier route : enrichir backend/routers/transcribe.py (stub Phase 1.3)
   OU créer backend/routers/transcribe_stream.py séparé
3. Convention WS existante dans le projet : grep "WebSocket" dans backend/routers/*.py

Items restants après 2.1 : 11 (2.2, 3.1, 3.2, 4.1, 4.2, 4.3, 5.1 à 5.5)

Méthode : tu proposes analyse + cadrage Phase 2.1, je critique, on aligne, tu codes.
```

---

## Checklist "avant de couper" (validée 16/05/2026)

- [x] Phase 1 complètement close (7 items completed dans TodoWrite)
- [x] 9 commits locaux propres, scopes séparés
- [x] Memory `feedback_workflow.md` à jour (règle "1 écrit, 2 réfléchissent" — 16/05/2026)
- [x] `MesMD/DEEPGRAM/` nettoyé : SPEC + seeds + test_audio.wav + ce document
- [x] `.env` et binaires audio bien exclus de git
- [x] Document handoff prêt à coller dans nouvelle conversation

---

## Roadmap restante (12 items)

2.1 (route WS) → 2.2 (7 tests wscat) → 3.1 (frontend WS + purge dead code TexteSource) → 3.2 (tests Edge MediaRecorder Opus + vraie voix) → 4.1 (admin lecture seule) → 4.2 (cron crédit) → 4.3 (alertes clé) → 5.1 (iOS PWA) → 5.2 (CGU RGPD) → 5.3 (TRACKER sync) → 5.4 (Aide) → 5.5 (push v3.3.0 MINOR + sync School.jsx afia.fr)
