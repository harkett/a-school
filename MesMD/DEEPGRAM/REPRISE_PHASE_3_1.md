# Handoff Phase 3.1 — Frontend WebSocket + purge dead code TexteSource

> Document de reprise pour nouvelle conversation Claude. Écrit en fin de session du 17/05/2026 à la clôture de **Phase 2.2** (`test_phase22.py`, 7/7 PASS, commit `fc09c34` + doc clôture `db3e0a3`). Prochaine étape : remplacer `webkitSpeechRecognition` par MediaRecorder + WebSocket vers `/api/transcribe/stream` dans le composant Dictée, et purger le code mort Web Speech API.

---

## 1. Synthèse de clôture — Session Phase 2.2 (17/05/2026)

### Ce qui a été livré — 6 commits Phase 2.2 (de 13 à 21 ahead)

| SHA | Type | Scope |
|---|---|---|
| `7165a5e` | refactor | tracker D5γ + R4 (3 catégories pré-accept agrégées) |
| `b4ff416` | feat | route `?encoding=opus\|linear16` + whitelist close 1003 (D2/D3) |
| `5498400` | chore | `CHECKLIST_PHASES.md` + règle d'affinement ±30 min |
| `9319f1a` | docs | mini-état mi-parcours + question archi tests |
| `fc09c34` | feat | `test_phase22.py` 7 scénarios — **7/7 PASS** |
| `db3e0a3` | docs | clôture Phase 2.2 + docstrings smoke/test_phase22 |

Working tree clean côté Deepgram (autres modifs hors scope conservées intactes — cf. Section 4 + Section 10).

### Trois éléments durables produits cette session (au-delà du code)

1. **Pattern threading pour TestClient WS** — `WebSocketTestSession.receive_*()` est bloquant sans timeout natif dans Starlette 1.0.0. Solution : thread daemon push audio + main thread `receive_json()` bloquant + `threading.Event` stop coordonné. Réutilisable Phase 4.x si tests WS admin.
2. **Sentinel `_Skipped` distinct de PASS/FAIL** — pour dépendances externes (Deepgram down = close 4502). Décompte final sépare passes/failures/skipped, exit 0 si zero FAIL. Pattern à dupliquer pour toute future suite touchant un provider externe.
3. **Règle ±30 min validée par la pratique** — estim. initiale Phase 2.2 = 8-10h, réel = 7-8h, intervalle bas. La règle tient ; à appliquer systématiquement en ouverture de Phase 3.1, 4.x, 5.x.

### Méthode de travail (rappel — version courante validée 16-17/05/2026)

- 2 réfléchissent (utilisateur chef de projet + Claude)
- 1 seul écrit le code = Claude (Edit, Write, mv, rm, commits via Bash)
- Propositions indifférentes : l'un ou l'autre propose, on s'aligne, Claude édite
- Yes/no avant action environnement (pip install, git push, suppression)
- Handoffs sans pré-décider : recos étiquetées "non tranchée"
- Pattern asyncio WS = `create_task` + `cancel`-in-finally (cf. `transcribe.py` Phase 2.1)
- Référence canonique : `feedback_workflow.md` mémoire utilisateur + section "Méthode de travail" de REPRISE_PHASE_2_2.md

---

## 2. Contexte général

- Projet **aSchool** — plateforme web React/FastAPI, prod aschool.fr
- Chantier en cours : **migration dictée vocale Web Speech API → Deepgram Nova-3 streaming**
- Spec canonique : `MesMD/DEEPGRAM/SPEC_DEEPGRAM_STT.md` (v1.1), section dédiée frontend : **§10 "Frontend — composant dictée"** (sous-sections 10.1 à 10.5)
- Suivi des phases : `MesMD/DEEPGRAM/ROADMAP_PHASES.md` (Phase 1 ✅ 7/7, Phase 2 ✅ 2/2, Phase 3 ⏳ À VENIR)
- Méthode de travail validée 16-17/05/2026 (cf. Section 1 ci-dessus)

---

## 3. Conventions codebase

### Backend (identiques Phase 2.2 — à respecter scrupuleusement)

- **SQLAlchemy ORM** (pas raw SQL), `Base.metadata.create_all()` au démarrage
- **`logging.getLogger(__name__)`** partout, jamais `print` en code prod
- **`@dataclass`** stdlib, typing moderne (`list[str]`, `| None`, `from __future__ import annotations`)
- Scripts standalone à la racine (`test_*.py`), **pas pytest** dans ce projet
- **Instance module-level** pour singletons stateful (cf. `session_tracker.py:tracker`)
- **Factory** pour stateless (cf. `backend/stt/__init__.py:get_stt_provider`)
- **`os.getenv()`** direct (pas Pydantic Settings)
- Hiérarchie d'exceptions métier : `STTError` racine → `STTRateLimitError`, `STTServiceUnavailableError`, `STTCreditExhaustedError`, `STTSessionTimeoutError`
- **Pattern asyncio Phase 2.1 OBLIGATOIRE** pour toute route WS future : `create_task` + `cancel`-in-finally + `await gather(*, return_exceptions=True)` pour drain. `asyncio.gather` pur ne cancelle pas les sœurs.

### Frontend (à découvrir en ouverture Phase 3.1)

- **React + Vite** (cf. CLAUDE.md "Stack technique" — `frontend/` port Vite)
- Layout général imposé par CLAUDE.md — voir section Layout (Header, Logo, Sidebar repliable mobile, Footer)
- **Composants** : `frontend/src/components/` (TexteSource.jsx, Parametres.jsx, ZoneResultat.jsx, etc.)
- **Pages** : `frontend/src/pages/`
- **Contexte d'état** : `AuthContext` (`frontend/src/context/AuthContext.jsx`) — pattern existant pour état global
- **Pattern erreurs** : `showError(msg)` modal via `errorDialog.js` (cf. mémoire `feedback_error_dialog` — règle absolue UI)
- **Navigateur de référence** : **Edge** uniquement (CLAUDE.md règle absolue — pas de Chrome)
- **Patterns à observer en ouverture** : hooks audio existants (si présents), état du composant `TexteSource.jsx`, conventions de nommage (PascalCase composants, camelCase props), gestion du loading state, intégration au routing `App.jsx`

---

## 4. État actuel — Phase 3 (frontend WS + tests e2e)

Phase 2 close (2.1 route WS livrée commit `9256cab`, 2.2 7 scénarios livrés commit `fc09c34`).

- **22 commits locaux ahead**, jamais pushés (push prévu Phase 5.5)
- **Route WS `/api/transcribe/stream`** opérationnelle : auth JWT cookie httpOnly + tracker D5γ + 3 pumps (audio/transcript/watchdog) + cleanup centralisé + watchdog warning `EXPIRING_SOON` à T-60s
- **Tests Phase 2.2** (`test_phase22.py`) = **filet de sécurité backend** pour modifs accidentelles à la route pendant Phase 3.1. 7/7 PASS confirmé en local — à relancer après chaque modif éventuelle de `transcribe.py`, `session_tracker.py` ou `deepgram_provider.py`.
- **Smoke** (`test_phase21_smoke.py`) = filet bind TCP réel, complémentaire (cf. docstrings clarifiés en `db3e0a3`)

**Working tree dirty au début Phase 3.1** — héritage sessions 14-15/05/2026 (modifs hors scope Deepgram, à ne pas commiter dans un commit Phase 3.1) :

- 8 fichiers supprimés sous `SPECS_LEVIERS/` (refonte structure docs, déplacés dans `MesMD/SPECS_LEVIERS/` visibles en untracked)
- ~13 modifs backend/frontend (RAG branchement, L5 Consigne, errorDialog refonte, Groq fallback 413/503, prompts)
- Untracked : `backend/rag/`, `backend/groq_client.py`, `backend/routers/consigne.py`, `frontend/src/components/Consigne.jsx`, `frontend/src/errorDialog.js`, `MesMD/SPECS_LEVIERS/`, `MesMD/SPECS_TRANSVERSES/`, `rag_demo/`

**Ces modifs ne concernent pas Phase 3.1.** À laisser intactes ou traiter séparément (jugement chef de projet), mais **pas de commit accidentel** dans un commit Phase 3.1.

---

## 5. SDK et versions clés (côté frontend)

- **MediaRecorder API natif navigateur** — pas de lib externe pour la capture audio. Cible spec §10.2 : `audio/webm;codecs=opus` mono chunks 250ms. **Sample rate à trancher (cf. D10)** — spec dit 16 kHz mais MediaRecorder Edge produit 48 kHz par défaut.
- **WebSocket API natif navigateur** — `new WebSocket("wss://...")`, pas de lib WS côté client
- **Edge** = navigateur de référence pour tous les tests Phase 3.1 (CLAUDE.md règle absolue — pas de Chrome dans les instructions, jamais)
- **React + Vite** (déjà installés, cf. Section 3) — pas de nouvelle dep `npm` prévue pour Phase 3.1 (à confirmer en ouverture, mais le scope MediaRecorder + WebSocket natif n'en demande pas)
- **iOS Safari MediaRecorder Opus** = piège connu, traité Phase 5.1 séparément (cf. `CHECKLIST_PHASES.md` facteur de dérapage #2). Phase 3.1 cible Edge uniquement.

---

## 6. Prochaine étape — Phase 3.1 (frontend WS + purge TexteSource)

Scope défini dans `ROADMAP_PHASES.md` §3.1 et `SPEC_DEEPGRAM_STT.md` §10.

### Code à écrire / refondre

- Remplacer `webkitSpeechRecognition` par `MediaRecorder` Opus mono chunks 250ms (sample rate cf. D10)
- Ouvrir WebSocket vers `/api/transcribe/stream` avec cookie auth httpOnly (transmis automatiquement par le navigateur, pas de manip explicite côté client)
- Streamer chaque chunk `MediaRecorder` `dataavailable` en `ws.send(blob)`
- Lire les messages JSON serveur : `transcript` (interim/final) et `session_warning` (EXPIRING_SOON)
- Affichage : **interim en gris/italique**, **final en noir** (cf. spec §10.4)
- Gestion `session_warning` → toast info "session expire dans 60s"

### États du bouton micro (cf. spec §10.3)

- disponible (idle)
- en cours (recording active)
- saturé (close 4429 → message "Service saturé, réessayez")
- indisponible (close 4402 ou 4502 → message "Service indisponible")
- timeout (close 4408 → message "Session expirée")
- non supporté (MediaRecorder absent → bouton grisé permanent + tooltip)

### Code à refactorer (correction 17/05/2026 — écart découvert post-clôture 2.2)

> **Le grep "webkitSpeechRecognition" en clôture 2.2 était erroné.** Vérification project-wide 17/05/2026 : `webkitSpeechRecognition` / `SpeechRecognition` sont **absents du code** (uniquement dans la doc DEEPGRAM/TRACKER/SPEC). Le scope réel de Phase 3.1 est donc un **refactor batch → streaming WS**, pas un remplacement Web Speech API.

- **`frontend/src/components/TexteSource.jsx`** (400 lignes) utilise **déjà** `MediaRecorder` + `getUserMedia` + détection codec Opus (lignes 113, 152, 172, 231). Le blob complet est envoyé en POST batch à `POST /api/transcribe` (ligne 130) — probablement Groq Whisper batch. La dictée est actuellement désactivée avec un message d'attente utilisateur (ligne 389 : "en cours de migration vers une nouvelle technologie de transcription temps réel").
- **Travail Phase 3.1** : remplacer le `POST /api/transcribe` batch par un `WebSocket /api/transcribe/stream`, streamer chaque chunk `dataavailable` au lieu d'attendre le blob final, câbler la réception `transcript` interim/final, réactiver le bouton micro.
- **Dépréciation** : retirer la route `POST /api/transcribe` backend une fois la nouvelle dictée validée (vérifier zéro caller résiduel avant suppression).
- **Aucune dépendance `react-speech-recognition`** détectée dans le projet — purge npm/yarn pas nécessaire.

### Q2 traçable (cf. transcribe.py docstring)

Côté client, un close pré-accept (4401/4429/1003) apparaît comme "connection failed" sans code lisible car Starlette transcode en HTTP 403 au handshake. Le frontend doit traiter "connection failed" comme "auth manquante / saturation / encoding non supporté" via fallback informatif — **3 cas à désambiguïser côté UX (cf. D15)**.

### Notes inline (pas des décisions pleines)

- **Cleanup unmount (discipline React)** : à implémenter `useEffect` cleanup couvrant `MediaRecorder.stop()` + `MediaStream.getTracks().forEach(t => t.stop())` (sinon LED micro reste allumée) + `ws.close(1000)` côté client + cancel des timers/effets. Cohérent avec la discipline cleanup centralisé adoptée Phase 2.1 côté serveur.
- **Backpressure client** : si le serveur est lent à consommer (Deepgram lent ou saturation interne), le `MediaRecorder` continue à produire des chunks 250ms. La route Phase 2.1 gère côté serveur (asyncio buffering naturel + close si idle), donc probablement aucune logique côté client n'est nécessaire. À confirmer empiriquement Phase 3.2 si symptômes observés. Pas une décision Phase 3.1 pleine — note inline ici, et c'est tout.

---

## 7. Décisions ouvertes à trancher en début de Phase 3.1

**Rien n'est pré-tranché. Tout est à valider explicitement avant la première ligne de code Phase 3.1.**

> Décisions D7-D16 listées ci-dessous (D12 fusionné dans D11, D13 backpressure traité inline Section 6).

Les recommandations sont étiquetées explicitement **"non tranchée"** pour rester fidèles à la règle "handoffs sans pré-décider" (apprentissage Phase 2.1).

### D7 — Architecture état React pour la session WS

Comment exposer la session STT au composant qui consomme le texte transcrit (le futur remplaçant de `TexteSource.jsx`) ?

- **α** Context global `STTContext` partagé via React Context API
- **β** Hook custom autonome `useTranscribeStream(onTranscript, onWarning, onClose, onError)`
- **γ** Logique inline dans le composant Dictée lui-même (pas de couche d'abstraction)

→ **Reco (non tranchée)** : β. Hook custom = encapsule le cycle de vie WS + MediaRecorder + état UI dans une seule unité testable, sans polluer le Context (réservé à l'auth dans ce projet). À discuter selon le besoin de partager la session entre plusieurs composants (improbable Phase 3.1).

### D8 — Affichage transcripts interim/final

Spec §10.4 dit "interim en gris/italique, final en noir" mais ne précise pas la disposition spatiale :

- **α** Zone unique : interim remplace partial → final remplace définitivement (single source of truth)
- **β** Zone interim volatile au-dessus du champ texte + final injecté dans le champ principal
- **γ** Inline dans le champ texte avec rendu CSS différencié (italique/gris pour interim, normal pour final)

→ **Reco (non tranchée)** : α si l'UX cible est "le prof voit le texte se construire en direct dans le champ", β si l'UX cible est "le prof voit l'interim séparément et valide le final via le champ". À trancher selon préférence ergonomique.

### D9 — Gestion erreurs (modal showError vs UX dédiée micro)

Convention projet = `showError(msg)` modal partout (mémoire `feedback_error_dialog`). Mais pour STT, certaines erreurs sont éphémères (saturation à retry plus tard) :

- **α** `showError()` modal pour tous les cas — cohérent convention projet, mais modal "Service saturé" peut être lourd
- **β** Toast non bloquant pour erreurs récupérables (saturation, timeout) + `showError()` modal pour bloquantes (auth manquante, service indisponible)
- **γ** Banner inline au-dessus du composant Dictée pour toutes les erreurs STT

→ **Reco (non tranchée)** : α (cohérence stricte avec la règle UI) ou β (UX plus fluide pour erreurs éphémères). γ écarté car ajouterait un pattern d'erreur supplémentaire au projet.

### D10 — sample_rate Opus côté frontend (dette TRACKER)

Conflit spec §10.2 ("16 kHz") vs réalité MediaRecorder Edge (48 kHz par défaut, cf. dette TRACKER NON RETENU "sample_rate paramétrable Phase 3.2") :

- **α** Ajuster default `STTSessionConfig.sample_rate` à 48000 quand `encoding=opus` (suit D2 logique côté backend)
- **β** Ajouter `?sample_rate=48000` en query string (cohérent D2 pattern paramétrable)
- **γ** Downsampler côté client en 16 kHz avant `ws.send(blob)` — ajoute du code complexe, à éviter si Deepgram accepte 48 kHz natif (à confirmer dans la spec Deepgram et empiriquement)
- **δ** Mettre à jour la spec §10.2 pour acter 48 kHz au lieu de 16 kHz

→ **Reco (non tranchée)** : α + δ groupés. Le downsampling client (γ) ajoute du code complexe sans bénéfice clair si Deepgram accepte 48 kHz natif. La query string (β) est une généralisation prématurée si Edge produit toujours 48 kHz. À trancher en ouverture après test rapide MediaRecorder Edge.

### D11 — Détection support MediaRecorder (fallback acté par spec)

Combine ex-D11 (fallback) et ex-D12 (détection) — fusionnés car indissociables. **Le fallback est acté par spec §10.3** (grisé permanent + tooltip "Dictée vocale non disponible sur ce navigateur") — décision ouverte = seulement la détection.

- **α** Check au mount du composant Dictée : `MediaRecorder.isTypeSupported('audio/webm;codecs=opus')` → state `isSupported`
- **β** Check au premier click bouton micro (lazy)

→ **Reco (non tranchée)** : α (mount). Évite un click qui foire en bruit utilisateur.

### D14 — Reconnect/retry policy sur close inattendu

Si le serveur close 4502 (service indisponible) ou 4408 (timeout) pendant l'enregistrement, le client retry-t-il automatiquement ?

- **α** Aucun retry, stop + message clair "Service interrompu, réessayez" (MVP)
- **β** 1 retry après 3s de backoff, puis stop + message si toujours en échec
- **γ** Retry continu avec compteur visible et close manuel utilisateur

→ **Reco (non tranchée)** : α pour MVP Phase 3.1. β a du sens pour Phase 4.x après observation des patterns réels de close 4502 (mid-session vs ouverture). γ écarté car bruit utilisateur (UX qui clignote).

### D15 — Désambiguïsation message erreur pré-accept (HTTP 403 → 3 cas)

Côté client, un close pré-accept (4401/4429/1003) apparaît comme "connection failed" sans code lisible (Starlette transcode en HTTP 403 au handshake). 3 cas à distinguer côté utilisateur :

- **α** Message générique unique "Connexion impossible, vérifiez votre session ou réessayez plus tard" (1 message pour 3 cas — clair mais imprécis)
- **β** Heuristique côté client : si pas de cookie `aschool_access` → message "Session expirée, reconnectez-vous" ; sinon → message "Service saturé, réessayez"
- **γ** Endpoint diagnostic HTTP pré-WS `GET /api/transcribe/check` qui répond précisément (auth/saturation/encoding) avant l'ouverture WS

→ **Reco (non tranchée)** : β pour Phase 3.1 (heuristique pragmatique, zéro code backend, UX correcte 80% du temps — auth manquante = cookie expiré = ré-login). γ écarté car ajoute une route backend pour une décision UX. α écarté car flou utilisateur.

### D16 — Permission micro getUserMedia + gestion erreurs

Avant `MediaRecorder`, il faut `navigator.mediaDevices.getUserMedia({audio: true})` qui déclenche le prompt permission utilisateur. Flux distinct avec ses propres erreurs :

- `NotAllowedError` : permission refusée définitivement (settings navigateur)
- `NotFoundError` : pas de micro physique
- `NotReadableError` : micro occupé par une autre app (Teams, Zoom, etc.)

Question UX : on prompt au click bouton micro ou au mount du composant ? Comment on gère les 3 erreurs distinctement de D11 (support codec) et D14 (close serveur) ?

- **α** Prompt au click (lazy) + gestion erreurs avec messages distincts par type
- **β** Prompt au mount (eager) + gestion erreurs au démarrage du composant
- **γ** Hybride : check `permissions.query({name: 'microphone'})` au mount pour détecter état "denied" → bouton grisé direct ; prompt au click sinon

→ **Reco (non tranchée)** : α. Pattern web standard = ne demander la permission qu'au moment de l'usage (sinon UX intrusif). Messages d'erreur dédiés par type (cohérent avec dette TRACKER "Aide rubrique dictée réactivation micro"). γ écarté car `permissions.query` pour 'microphone' a un support inégal selon navigateurs ; complexité non justifiée.

---

## 8. Référence aux décisions déjà actées — NE PAS REJOUER

### Phase 2.1

- **Auth WS = cas C** : lecture directe `websocket.cookies.get("aschool_access")` + `auth_lib.verify_access_token(token)`, pas de Depends() partagé. Wrap défensif `try/except Exception` pour cookies tordus (cf. `transcribe.py:53-58`).
- **Pattern asyncio = create_task + cancel-in-finally** : impératif. `asyncio.gather()` pur ne cancelle pas les sœurs sur exception → leak Deepgram. Voir `transcribe.py:189-208` pour la référence.
- **Watchdog avec warning T-60s** (option α de la spec §5.3) : implémenté, validé. `remaining_seconds: 60` hardcoded dans le payload `session_warning`.
- **Codes pré-accept (4401, 4429, 1003) sont déclaratifs côté backend** : Starlette transcode en HTTP 403 au handshake. Le frontend doit traiter "connection failed" comme "auth manquante / saturation / encoding non supporté" (cf. D15 pour la stratégie de message).
- **Codes post-accept (4402, 4502, 4408, 1011) transitent correctement** comme close frames WebSocket, lisibles via `WebSocketDisconnect.code` côté client.
- **Log AVANT close** : pattern adopté Phase 2.1. Close wrappé en try/except + log warning si raise.
- **`duration_s` mesure le temps avant `session.close()`** — sémantique "durée audio reçue", pas "durée totale". Acté comme plus pertinent métier.

### Phase 2.2

- **D2/D3 query string `?encoding=` + whitelist** `{"opus", "linear16"}` côté backend. Hors-whitelist → close 1003 pré-accept (transcodé HTTP 403). Phase 3.1 utilise `?encoding=opus` (D10 décide du sample_rate).
- **D5γ tracker relit `max_concurrent` live** à chaque `acquire()`. Pas d'impact direct frontend Phase 3.1, mais explique pourquoi un changement `STT_MAX_CONCURRENT_SESSIONS` côté admin (Phase 4.1) sera pris en compte sans restart.
- **R4 — 3 catégories pré-accept agrégées** (`anonymous`, `bad_token`, `saturated`) exposées via `tracker.snapshot()`. Côté frontend Phase 3.1 : pas d'usage direct, mais à anticiper pour `/admin/stt-status` Phase 4.1.
- **Tests `test_phase22.py` = filet de sécurité** : à relancer après toute modif du backend STT pendant Phase 3.1 (cf. Section 10 pour vérification actionnable).

### Méthode validée 16-17/05/2026

Cf. Section 1 ci-dessus, sous-section "Méthode de travail".

---

## 9. Dettes notées au TRACKER

Toutes consignées dans `MesMD/TRACKER.md` section `## NON RETENU — À reconsidérer plus tard`. Pertinentes pour Phase 3.1 (par ordre de proximité au scope) :

### Directement liées au cœur de Phase 3.1 (peuvent être traitées dans la foulée)

1. **Dictée vocale — REMPLACER webkitSpeechRecognition** (audit 15/05) — c'est **le cœur même de Phase 3.1**. La dette pointait Groq Whisper / autre fournisseur comme pistes ; la Phase 1-2 a tranché pour Deepgram Nova-3 streaming. **À cocher et déplacer en FAIT à la clôture Phase 3.1.**

2. **STT Deepgram — sample_rate paramétrable Phase 3.2** (audit 16/05) — **directement lié à D10**. Phase 2.2 a ajouté `?encoding=opus|linear16`, Phase 3.1 doit trancher le sample rate effectif (16 vs 48 kHz). Résolution attendue dans le commit qui livre le composant Dictée Phase 3.1, OU explicitement reportée à Phase 3.2 si tests Edge montrent que c'est un point bloquant à trancher avec vraie voix.

3. **Aide — Rubrique dictée à enrichir avec procédure de réactivation du micro** (audit 15/05) — **connexe à D16** (permission getUserMedia). La rubrique `Aide.jsx` mentionne déjà d'autoriser le micro mais n'explique pas la réactivation si refusé (cadenas → autorisations Edge → Microphone). À traiter en cohérence avec D16 dans la foulée Phase 3.1 (rappel règle CLAUDE.md "Aide rédigée à chaud dans la même session que la livraison").

4. **Modal multi-actions (showConfirm Oui/Non)** (audit 15/05) — touche `errorDialog.js` + `App.jsx`. **Peut interférer avec D9** (modal vs toast vs banner). Si D9=α (modal `showError`) → groupable avec D9 et traitable dans la foulée. Sinon → conserver en dette pour traitement séparé.

### Reportées à Phase 3.2 (tests vraie voix Edge MediaRecorder Opus)

5. **Dictée Deepgram — points de vigilance Phase 3.2** (audit 16/05) — Smart Format agressif sur nombres ("deux x au carré" → "10 au carré") + "hypoténuse" substituée par "hypothèse" malgré keyterm boost. Conditions Phase 0.2/1.5 (PCM linear16) ≠ Phase 3.2 (Opus live MediaRecorder Edge avec vraie voix). À retester Phase 3.2, pas Phase 3.1.

### Hors scope Phase 3.1 mais utiles à connaître

6. **Région US Phase 1 — temporaire** (R3 ROADMAP) — bloquant avant scale >50 profs, à migrer EU avant Phase 5.5. Pas d'action Phase 3.1.

Aucune de ces dettes ne **bloque** Phase 3.1. Les dettes 1, 2, 3 (et 4 selon D9) sont organiquement liées et peuvent être résolues dans la foulée — à arbitrer en ouverture.

---

## 10. Pré-conditions environnement

### Backend & infra

- **`.\run.ps1`** lance backend (`:8000`) + frontend (port Vite, cf. `vite.config.js`) — flow validé en local depuis Phase 2.1
- **`GET /api/health`** retourne `{"status":"ok","service":"aSchool API"}` (vérif rapide)
- **`DEEPGRAM_API_KEY`** configurée dans `.env` (sinon `DeepgramProvider._client = None` et `STTServiceUnavailableError` au `create_session`)
- Routes WS absentes de `/openapi.json` (limitation FastAPI/OpenAPI 3.x) — vérifier l'enregistrement via `app.routes` introspection si doute

### Filet de sécurité Phase 2.2

- **`python test_phase22.py`** doit retourner **7/7 PASS exit 0** avant d'attaquer Phase 3.1 — filet de sécurité backend en cas de modifs accidentelles à `transcribe.py`, `session_tracker.py` ou `deepgram_provider.py` pendant la session. À relancer après chaque modif éventuelle.
- **`python test_phase21_smoke.py`** complémentaire — valide le bind WS via TCP loopback (backend lancé via `.\run.ps1`)

### Frontend & navigateur

- **Edge installé** (navigateur de référence — CLAUDE.md règle absolue, pas de Chrome dans les instructions)
- **Permission micro physique** : un micro doit être branché/intégré pour tester scénarios D16. Le cas `NotFoundError` est testable en débranchant temporairement le micro pendant le test ; `NotAllowedError` en refusant la permission au prompt ; `NotReadableError` en lançant une autre app qui occupe le micro (Teams, Zoom).
- **HTTPS local** (à vérifier) : `getUserMedia` exige typiquement HTTPS ou `localhost`. En dev local sur `localhost` (port Vite, cf. `vite.config.js`), normalement OK. Si problème en ouverture, vérifier le contexte sécurisé.

### Working tree

- **Modifs hors scope Deepgram** présentes en début Phase 3.1 — cf. Section 4 pour la liste détaillée. **Ne pas commiter accidentellement** dans un commit Phase 3.1.

---

## 11. Affinement ±30 min — à exécuter en ouverture Phase 3.1

> **Mode d'emploi**, pas exécution. La règle ±30 min veut "affiner quand on s'approche, avec connaissance du terrain". Le terrain Phase 3.1 = code frontend (non lu dans la session de clôture 2.2). À exécuter au tout début de la prochaine session, AVANT de tomber dans le code Phase 3.1.

### Procédure en 4 étapes (validée 16/05/2026, cf. CHECKLIST_PHASES.md section "Méthode d'affinement")

1. **Lire les fichiers concernés** :
   - `frontend/src/components/TexteSource.jsx` — composant à remplacer (Web Speech API à purger, seul fichier contenant `webkitSpeechRecognition` selon grep en clôture 2.2)
   - Grep imports `TexteSource` dans `frontend/src/**/*.jsx` — identifier les callers (liste réelle à l'ouverture)
   - `frontend/src/App.jsx` — routing et intégration des composants top-level
   - `frontend/src/context/AuthContext.jsx` — pattern existant pour état global
   - `frontend/src/errorDialog.js` — pattern showError() (pour décider D9)

2. **Comparer le scope perçu à la réalité du code** :
   - LOC à modifier (TexteSource purge + nouveau composant Dictée)
   - Dépendances cachées (libs npm utilisées dans TexteSource, hooks audio préexistants si présents)
   - Libs à retirer (a priori aucune si `webkitSpeechRecognition` est natif sans wrapper npm)

3. **Réviser ±30 min l'estimation** dans `MesMD/DEEPGRAM/CHECKLIST_PHASES.md` tableau estimatif ligne Phase 3.1 — colonne Affinement passe de 📊 → 🎯. Estimation initiale = celle inscrite au tableau (à comparer à la réalité lue).

4. **Identifier 1-2 risques concrets** (pas génériques) :
   - ❌ "complexité React" / "MediaRecorder peut être capricieux"
   - ✅ "TexteSource importe X (lib spécifique) qu'il faudra retirer + audit des Y callers" / "intégration au flux SequenceForm exige refactor du callback Z"

---

## 12. Message d'amorçage pour la nouvelle conversation

> Deux portes d'entrée distinctes pour Phase 3.1 :
> - **Brief équipe humaine + Claude en cours de session** → voir [TOPO_PHASE_3_1.md](TOPO_PHASE_3_1.md)
> - **Amorçage Claude au démarrage d'une nouvelle conversation** → utiliser le bloc ci-dessous
>
> Le présent handoff (REPRISE_PHASE_3_1.md, 14 sections) reste la référence canonique pointée par les deux.

> À coller intégralement dans le premier message de la prochaine session. Calque sur REPRISE_PHASE_2_2.md, adapté Phase 3.1.

```
Reprise projet aSchool — intégration STT Deepgram, Phase 3.1 (frontend WS + purge TexteSource).

Contexte général
- Migration dictée vocale Web Speech API → Deepgram Nova-3 streaming
- Spec : MesMD/DEEPGRAM/SPEC_DEEPGRAM_STT.md (v1.1), §10 frontend
- Suivi des phases : MesMD/DEEPGRAM/ROADMAP_PHASES.md (Phase 2 ✅ 2/2, Phase 3 ⏳ À VENIR)
- Handoff détaillé : MesMD/DEEPGRAM/REPRISE_PHASE_3_1.md — à lire en début de session
- Convention de travail validée 16-17/05/2026 : 2 réfléchissent, 1 seul écrit (Claude).
  Yes/no avant action environnement. Handoffs sans pré-décider.

Conventions codebase
Backend (identiques Phase 2.2) :
- SQLAlchemy ORM, logging.getLogger(__name__), @dataclass stdlib, typing moderne
- Scripts standalone à la racine (test_*.py), pas pytest
- Instance module-level pour singletons stateful (tracker)
- Pattern asyncio WS = create_task + cancel-in-finally OBLIGATOIRE

Frontend (à découvrir en ouverture — affinement Section 11 du handoff) :
- React + Vite, Edge navigateur de référence (CLAUDE.md règle absolue, pas de Chrome)
- showError() modal pour erreurs (mémoire feedback_error_dialog)
- Composants : frontend/src/components/, pages frontend/src/pages/
- Context d'état : AuthContext (frontend/src/context/AuthContext.jsx) = pattern existant état global

État actuel — Phase 2 COMPLÈTE (9/19 items global)
- Items completed : 0.2, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2
- 22 commits locaux non-pushés (push prévu Phase 5.5)
- Route WS /api/transcribe/stream opérationnelle (commit 9256cab Phase 2.1)
- 7/7 PASS tests robustesse (commit fc09c34 Phase 2.2)
- Filet de sécurité backend : test_phase22.py à relancer si modif transcribe.py
- Working tree dirty hors scope présent — cf. handoff Section 4 / Section 10 ;
  ne pas commiter accidentellement

Prochaine étape — Phase 3.1 : frontend WS + purge TexteSource
Objectif : remplacer webkitSpeechRecognition dans TexteSource.jsx par MediaRecorder
Opus + WebSocket vers /api/transcribe/stream, gérer les 6 états du bouton micro,
afficher transcripts (interim/final), purger le code mort.

Décisions ouvertes à trancher en début de Phase 3.1 (8 décisions imbriquées)
D7. État React : Context global / Hook custom / Logique inline ?
D8. Affichage transcripts : zone unique / interim séparée volatile / inline CSS ?
D9. Erreurs : modal showError / Toast / Banner ?
D10. sample_rate Opus 48 kHz : ajuster default backend + spec / query string / downsampler ?
D11. Détection MediaRecorder : mount / lazy click ? (fallback acté spec §10.3)
D14. Reconnect/retry policy : aucun (MVP) / 1 retry backoff / continu ?
D15. Désambiguïsation message pré-accept : générique / heuristique client / endpoint diagnostic ?
D16. Permission getUserMedia : prompt au click / au mount + gestion NotAllowedError /
     NotFoundError / NotReadableError ?

(D12 fusionné dans D11, D13 backpressure traité inline Section 6 du handoff)

Recos non tranchées dans le handoff : hook custom (D7), zone unique ou interim séparée
(D8), modal showError ou toast (D9), ajuster default 48 kHz + spec (D10), détection au
mount (D11), aucun retry MVP (D14), heuristique côté client (D15), prompt au click (D16).
À re-discuter et trancher explicitement.

Affinement ±30 min à faire en ouverture (cf. Section 11 handoff) :
1. Lire TexteSource.jsx + grep callers
2. Comparer scope perçu vs LOC réel
3. Mettre à jour CHECKLIST_PHASES.md ligne Phase 3.1 (📊 → 🎯) ± 30 min
4. Identifier 1-2 risques concrets

Items restants après Phase 3.1 : 9 (3.2, 4.1, 4.2, 4.3, 5.1 → 5.5)

Méthode : tu lis le handoff, tu critiques mes recos D7-D16, on aligne, je code.
```

---

## 13. Checklist "avant de couper" (validée 17/05/2026)

- [x] Phase 2.1 commitée proprement (`9256cab`)
- [x] Phase 2.2 commitée proprement (`fc09c34` — `test_phase22.py` 7/7 PASS)
- [x] Doc clôture Phase 2.2 (`db3e0a3` — TRACKER + ROADMAP + CHECKLIST + docstrings smoke/test_phase22)
- [x] Note TRACKER "STT Phase 2.2 architecture tests" retirée du NON RETENU (décision tranchée = option B)
- [x] Note TRACKER "STT Phase 2.2 test_phase22.py" ajoutée en FAIT ✅
- [x] ROADMAP_PHASES.md Phase 2.2 cochée, SHA `fc09c34` consigné, Phase 2 ✅ 2/2
- [x] CHECKLIST_PHASES.md Phase 2.2 section "mi-parcours → close" avec bilan post-mortem (7-8h dans fourchette 8-10h)
- [x] Docstrings `test_phase21_smoke.py` + `test_phase22.py` clarifient les rôles distincts
- [ ] Bootstrap Section 12 cohérent avec compteur commits + items completed à l'heure du commit final
- [ ] Commit handoff Phase 3.1 — à faire fin session (scope `docs(deepgram): handoff Phase 3.1`)

---

## 14. Roadmap restante (9 items après Phase 3.1)

3.1 (frontend WS + purge TexteSource) → 3.2 (tests Edge MediaRecorder Opus + vraie voix) → 4.1 (admin STT lecture seule) → 4.2 (cron monitoring crédit Deepgram) → 4.3 (alertes expiration clé) → 5.1 (iOS PWA + fallback codec) → 5.2 (CGU RGPD mention provider US) → 5.3 (TRACKER sync — audit final, pas traitement) → 5.4 (Aide section dictée prof) → 5.5 (push v3.3.0 MINOR + sync School.jsx afia.fr)

**Note d'ordre crucial** : Phase 3.2 (tests vraie voix MediaRecorder Opus) DOIT être close avant d'attaquer Phase 4.x (admin / cron / alertes). Sinon on bâtit le monitoring sur une route encore en stabilisation = dette assurée.
