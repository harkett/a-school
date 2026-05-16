# Roadmap Phases — Intégration STT Deepgram

> Source de vérité unique pour le suivi des phases d'implémentation.
> Spec technique complète : [SPEC_DEEPGRAM_STT.md](SPEC_DEEPGRAM_STT.md) (v1.1)
> Dernière mise à jour : 16/05/2026 (après commit Phase 2.1 `9256cab`)

---

## Checklist phases

> Vue rapide item-par-item. Coche `[x]` à la clôture de chaque item (en même temps que le commit).

- [x] Phase 1.1 — `.env.example` STT (17 variables)
- [x] Phase 0.2 — Test exploratoire Deepgram (vocabulaire pédagogique FR + keyterm boost)
- [x] Phase 1.2 — BDD STT (4 tables + seed 8 messages + 80 keyterms)
- [x] Phase 1.3 — Interfaces `STTProvider`/`STTSession` async + clean break Groq Whisper batch
- [x] Phase 1.4 — `STTSessionTracker` (Lock+int) + test concurrence 41/40
- [x] Phase 1.5 — `DeepgramProvider` (SDK 3.11.0 pinné) + test d'intégration
- [x] Phase 1.6 — Factory `get_stt_provider()` dans `backend/stt/__init__.py`
- [x] Phase 2.1 — Route WebSocket `/api/transcribe/stream` (FastAPI)
- [ ] Phase 2.2 — 7 tests wscat (route WS)
- [ ] Phase 3.1 — Frontend WebSocket + purge dead code TexteSource
- [ ] Phase 3.2 — Tests bout-en-bout Edge (MediaRecorder Opus + vraie voix)
- [ ] Phase 4.1 — Admin STT lecture seule (sessions actives, audit)
- [ ] Phase 4.2 — Cron monitoring crédit Deepgram
- [ ] Phase 4.3 — Alertes expiration clé Deepgram
- [ ] Phase 5.1 — iOS PWA (test MediaRecorder Opus + fallback)
- [ ] Phase 5.2 — CGU RGPD (mention dictée vocale + provider Deepgram)
- [ ] Phase 5.3 — TRACKER sync (dettes consignées)
- [ ] Phase 5.4 — Aide (section dictée Deepgram pour prof)
- [ ] Phase 5.5 — Push v3.3.0 MINOR + sync School.jsx afia.fr

---

## Vue d'ensemble

| Phase | Périmètre | Statut |
|---|---|---|
| **Phase 1** | Fondations backend (interfaces, tracker, provider, factory, BDD) | ✅ **TERMINÉE** (7/7) |
| **Phase 2** | Route WS + tests backend | 🟡 EN COURS (1/2) |
| **Phase 3** | Frontend WS + tests bout-en-bout | ⏳ À VENIR |
| **Phase 4** | Monitoring admin (crédit, sessions, alertes clé) | ⏳ À VENIR |
| **Phase 5** | PWA / RGPD / docs / push prod | ⏳ À VENIR |

**Compteur commits locaux** : 10 ahead (push prévu Phase 5.5, jamais avant).

---

## Phase 1 — Fondations backend (✅ TERMINÉE)

| # | Item | Commit | Notes |
|---|---|---|---|
| 1.1 | `.env.example` 17 variables STT | `0d85c34` | Liste complète § [3.1](SPEC_DEEPGRAM_STT.md) |
| 0.2 | Test validation préalable Deepgram (wscat brut) | `536682d` | 2/3 termes critiques — R1 ouvert |
| 1.2 | BDD STT — 4 tables + seed | `ca42905` | 8 messages + 80 keyterms transversaux |
| 1.3 | Interfaces `STTProvider`/`STTSession` async | `fd5f0e4` | Clean break Groq Whisper batch |
| 1.4 | `STTSessionTracker` Lock+int | `b4ba5da` | Test concurrence 41/40 ✓ |
| 1.5 | `DeepgramProvider` (SDK 3.11.0 pinné) | `536682d` | Test intégration validé |
| 1.6 | Factory `get_stt_provider()` + switch | `8872dfe` | Multi-provider ready |

---

## Phase 2 — Route WS + tests backend (🟡 1/2)

### 2.1 — Route WS `/api/transcribe/stream` ✅

**Commit** : `9256cab` — 16/05/2026

Livré :
- Auth JWT cookie httpOnly avant `accept()` (pattern cas C, lecture directe `websocket.cookies`)
- Acquisition atomique slot via `STTSessionTracker.acquire()` (déni propre si saturé)
- 3 tasks concurrentes : `audio_pump`, `transcript_pump`, `watchdog`
- Pattern `create_task` + `cancel`-in-finally (évite leak zombie Deepgram)
- Watchdog avec warning `EXPIRING_SOON` à T-60s (option α)
- Logs structurés `user=` à toutes les étapes clés
- Wrap défensif `verify_access_token` (cookie tordu → log warning, pas stack trace)
- Smoke test `test_phase21_smoke.py` : rejet HTTP 403 sans cookie ET avec cookie bidon ✓

### 2.2 — 7 tests wscat backend ⏳

Spec : [§12.2](SPEC_DEEPGRAM_STT.md)

| # | Scénario | Code attendu | Setup |
|---|---|---|---|
| 1 | Sans cookie | denial 403 (4401 déclaratif) | rien — déjà smoke Phase 2.1 |
| 2 | Cookie invalide / expiré | denial 403 (4401 déclaratif) | rien — déjà smoke Phase 2.1 |
| 3 | Cookie valide → accept + audio bidon | `transcript` ou close 4502 | login local pour cookie |
| 4 | Saturation | denial 403 (4429 déclaratif) | `STT_MAX_CONCURRENT_SESSIONS=1`, 2 sessions |
| 5 | Crédit épuisé | close 4402 | mock provider ou clé invalide |
| 6 | Idle timeout | close 4408 IDLE | `STT_SESSION_IDLE_TIMEOUT_SECONDS=2`, attendre 3s |
| 7 | Max duration + warning | `session_warning` puis close 4408 | `STT_SESSION_MAX_DURATION_SECONDS=70` |

**Décision préalable** : tester avec audio réel (.wav stocké ou MediaRecorder live) ou simulation pure bytes random ? Le test 0.2 a déjà validé l'intégration brute Deepgram, donc simulation backend pure suffit pour 2.2.

---

## Phase 3 — Frontend WS + tests bout-en-bout (⏳)

### 3.1 — Frontend WS + purge dead code

Spec : [§10](SPEC_DEEPGRAM_STT.md)

- Remplacer `webkitSpeechRecognition` par `MediaRecorder` Opus 16 kHz mono chunks 250ms
- WebSocket vers `/api/transcribe/stream`
- États bouton micro : disponible / en cours / saturé (4429) / indisponible (4402,4502) / timeout (4408) / non supporté
- Affichage interim en gris/italique, final en noir
- Gestion message serveur `session_warning` → toast info
- **Purger** : code mort `TexteSource` ancien Web Speech API
- Frontend Phase 3.1 doit gérer "connection failed" = "auth manquante / saturation" (Q2 documentée Phase 2.1)

### 3.2 — Tests Edge MediaRecorder Opus + vraie voix

Spec : [§12.2](SPEC_DEEPGRAM_STT.md)

- Énoncés mathématiques ("Soit P de x égal à...")
- Noms propres scientifiques ("Lavoisier", "Avogadro")
- Consignes pédagogiques ("Justifiez votre réponse")
- Coupure réseau pendant dictée
- États visuels bouton corrects dans chaque cas
- **R1 à reclôre** : retest "hypoténuse" + Smart Format sur nombres ("deux x au carré" vs "10 au carré")

---

## Phase 4 — Monitoring admin (⏳)

### 4.1 — Admin lecture seule `/admin/stt-status`

Spec : [§8.1](SPEC_DEEPGRAM_STT.md)

Affichage :
- Crédit Deepgram restant (montant + barre %)
- Sessions STT actives temps réel (rafraîchissement 5s)
- Max sessions configuré
- Jours restants avant expiration clé API
- Compteur transcriptions (jour/semaine/mois)
- Bannière région US Phase 1
- Historique snapshots crédit (graphique 30 jours)

**À envisager Phase 4** : compteur agrégé rejets pré-accept (anonymous + bad_token) pour monitoring sans log par tentative (anti-énumération préservé) — noté 16/05/2026.

### 4.2 — Cron monitoring crédit Deepgram

Spec : [§7](SPEC_DEEPGRAM_STT.md)

- APScheduler horaire → `GET /v1/projects/{id}/balances` Deepgram
- Snapshot dans table `stt_credit_history`
- Alerte email admin si reste ≤ `STT_CREDIT_ALERT_THRESHOLD_PCT` (défaut 10%)
- Activation mode "préventif" (bannière user) puis "service indisponible" si épuisé

### 4.3 — Alertes expiration clé API

Spec : [§8.3](SPEC_DEEPGRAM_STT.md)

- J-30 : info bleue dashboard admin
- J-15 : warning orange
- J-7 : alerte rouge + email quotidien
- J-0 : bloquant + email quotidien
- Lit `DEEPGRAM_API_KEY_EXPIRES_AT` (env)

---

## Phase 5 — Finalisation prod (⏳)

### 5.1 — iOS PWA

Spec : [§15.2](SPEC_DEEPGRAM_STT.md)

- Détection support `audio/webm;codecs=opus` OU `audio/ogg;codecs=opus`
- Si non supporté → bouton micro grisé permanent + tooltip
- Pas de tentative fallback codec en Phase 1 (multiplie les chemins de test)

### 5.2 — CGU RGPD (région US Phase 1)

Spec : [§3.4](SPEC_DEEPGRAM_STT.md)

- Mention obligatoire région US dans CGU + politique confidentialité
- Profs pilotes informés explicitement
- **Bloquant avant scale >50 profs** : migration EU ou bascule provider EU

### 5.3 — TRACKER sync

- Reporter dans `MesMD/TRACKER.md` l'avancement Phase Deepgram STT
- Cocher items livrés
- Ajouter idées émergées en cours de session

### 5.4 — Aide

- Rédiger section Aide dictée vocale (règle CLAUDE.md "à chaud, même session")
- Tutoriel court : clic micro → parler → stop → texte inséré
- Messages d'état : "Service saturé", "Session expirée", "Indisponible"

### 5.5 — Push v3.3.0 MINOR + sync School.jsx afia.fr

Conformément à [CLAUDE.md](../../CLAUDE.md) — section "Synchronisation afia.fr" :

- Bump MINOR manuel (`v3.2.X` → `v3.3.0`)
- `git push` → déploiement automatique VPS via `push.ps1`
- Générer le contenu de `School.jsx` à coller dans `D:\AFIA-FR\frontend-web\src\pages\School.jsx`
- Utilisateur applique côté AFIA-FR (Claude ne touche jamais AFIA-FR depuis ce projet)

---

## Notes de vigilance (à clôre avant Phase 5.5)

| # | Sujet | Détail | Phase cible |
|---|---|---|---|
| R1 | Hypoténuse substituée "hypothèse" | malgré 80 keyterms BDD chargés — retest avec vraie voix | 3.2 |
| R2 | Smart Format agressif sur nombres | "deux x au carré" → "10 au carré" — tester `smart_format=false` pour maths notationnels | 3.2 |
| R3 | Région US Phase 1 — temporaire | Bloquant avant scale >50 profs : migrer EU ou changer de provider | 4 (avant 5.5) |
| R4 | Compteur agrégé pré-accept rejects | Anti-énumération préservé, observabilité ajoutée — choix Phase 2.2 ou 4 | 2.2 ou 4 |

---

## Politique de mise à jour de ce fichier

- À chaque clôture d'item Phase X.Y : cocher dans la table de la phase + ajouter le SHA du commit
- À chaque décision technique nouvelle (R5+) : ajouter ligne dans le tableau "Notes de vigilance"
- À chaque fin de session de travail STT : mettre à jour le compteur "commits locaux ahead" en haut
- Ne JAMAIS dupliquer les détails techniques de `SPEC_DEEPGRAM_STT.md` ici — linker la section spec à la place
