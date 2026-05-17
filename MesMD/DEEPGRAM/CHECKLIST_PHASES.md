# Estimation phases Deepgram STT — Affinement progressif

> Vue d'ensemble des phases restantes avec estimations heures + sessions.
> Source de vérité granulaire des SHAs et scopes : [ROADMAP_PHASES.md](ROADMAP_PHASES.md).
> **Politique d'affinement** : estimation serrée à **±30 min** en ouverture de chaque phase, après lecture du code réel concerné (cf. § Méthode d'affinement).
> Dernière mise à jour : 17/05/2026 (Phase 2.2 close, Phase 3.1 prochaine).

---

## État synthétique

| Bloc | Phases | Statut |
|---|---|---|
| Fondations backend | 1.1 → 1.6 + 0.2 | ✅ TERMINÉ (7/7) |
| Route + tests backend | 2.1 → 2.2 | ✅ TERMINÉ (2/2) |
| Frontend + e2e | 3.1 → 3.2 | ⏳ À VENIR |
| Admin monitoring | 4.1 → 4.3 | ⏳ À VENIR |
| PWA + doc + push | 5.1 → 5.5 | ⏳ À VENIR |

---

## Checklist phases (miroir ROADMAP_PHASES.md)

> Coche `[x]` à la clôture de chaque item (en même temps que le commit).

- [x] Phase 1.1 — `.env.example` STT (17 variables)
- [x] Phase 0.2 — Test exploratoire Deepgram (vocabulaire pédagogique FR + keyterm boost)
- [x] Phase 1.2 — BDD STT (4 tables + seed 8 messages + 80 keyterms)
- [x] Phase 1.3 — Interfaces `STTProvider`/`STTSession` async + clean break Groq Whisper batch
- [x] Phase 1.4 — `STTSessionTracker` (Lock+int) + test concurrence 41/40
- [x] Phase 1.5 — `DeepgramProvider` (SDK 3.11.0 pinné) + test d'intégration
- [x] Phase 1.6 — Factory `get_stt_provider()` dans `backend/stt/__init__.py`
- [x] Phase 2.1 — Route WebSocket `/api/transcribe/stream` (FastAPI)
- [x] Phase 2.2 — 7 tests wscat (route WS)
- [ ] Phase 3.1 — Frontend WebSocket + purge dead code TexteSource
- [ ] Phase 3.2 — Tests bout-en-bout Edge (MediaRecorder Opus + vraie voix)
- [ ] Phase 4.1 — Admin STT lecture seule (sessions actives, audit)
- [ ] Phase 4.2 — Cron monitoring crédit Deepgram
- [ ] Phase 4.3 — Alertes expiration clé Deepgram
- [ ] Phase 5.1 — iOS PWA (test MediaRecorder Opus + fallback)
- [ ] Phase 5.2 — CGU RGPD (mention dictée vocale + provider Deepgram)
- [ ] Phase 5.3 — TRACKER sync (audit final, pas traitement)
- [ ] Phase 5.4 — Aide (section dictée Deepgram pour prof)
- [ ] Phase 5.5 — Push v3.3.0 MINOR + sync School.jsx afia.fr

---

## Phase 2.2 — close 🎯 (17/05/2026)

> Phase fermée côté code, doc synchronisée. Bilan post-mortem.

**Heures totales consommées** : ~7-8h sur 2 sessions
- Session 16/05 (~5h) : discussion D1-D6, refactor γ+R4 (`7165a5e`), route ?encoding= (`b4ff416`), CHECKLIST + règle ±30 min (`5498400`), mini-clôture mi-parcours (`9319f1a`)
- Session 17/05 (~2-3h) : discussion B vs B', squelette critique itératif, écriture `test_phase22.py`, 2 runs (FAIL race scénario 3 fixé → 7/7 PASS), commit (`fc09c34`)

**Estimation initiale** : 8-10h sur 2-3 sessions. **Réalisé** : 7-8h sur 2 sessions. Dans la fourchette, intervalle bas.

**Apports session au-delà du code** :
- Pattern `dataclasses.replace(STTSessionConfig(), encoding=x)` validé future-proof (vs kwargs explicites fragiles)
- Élargissement R4 à 3 catégories (`saturated` en plus, écart conscient au handoff documenté en commit body)
- Code WebSocket pré-accept : 1003 (Unsupported Data, RFC 6455) plus précis que 1011 pour rejet client identifié
- Règle d'affinement ±30 min posée en mémoire feedback persistante
- Pattern threading pour TestClient WS (receive_* bloquant sans timeout natif) — réutilisable Phase 4.x
- Sentinel `_Skipped` distinct de PASS/FAIL pour dépendances externes (Deepgram)

**Décisions tranchées Phase 2.2** :
| Décision | Choix | Note |
|---|---|---|
| D1 encoding tests | LINEAR16 | `test_audio.wav` PCM 16 kHz mono prêt |
| D2 route paramètre | query string `?encoding=` | + close 1003 si hors-whitelist |
| D3 whitelist backend | `{"opus","linear16"}` | RFC 6455 1003 (Unsupported Data) |
| D4 cookie test | β JWT forgé `create_access_token(email)` | pas de round-trip login |
| D5 mutation env | γ + R4 bundle | `_read_max()` + 3 catégories pré-accept |
| D6 crédit épuisé | δ2 `FakeExhaustedProvider` local | swap `_PROVIDERS["deepgram"]` |
| Archi tests | B `TestClient` in-process | A éliminée, B' pesée puis B retenu |

**Risque dépassement** : aucun (Phase 2.2 fermée).

---

## Phase 3.1 — ouverture 🎯 (17/05/2026)

> Affinement réalisé en ouverture après lecture code (TexteSource 400 lignes, App.jsx skim, AuthContext, errorDialog, grep callers, grep route backend). Rapport complet en session.

**Découverte structurante** : la route `POST /api/transcribe` côté backend **n'existe pas** (grep project-wide vérifié `backend/main.py`, `backend/routers/`, `backend/groq_client.py`). TexteSource ligne 130 appelle un endpoint mort — c'est la raison du bouton désactivé. **Scope Phase 3.1 = travail purement frontend, pas de coordination back/front, pas de dépréciation backend à arbitrer.**

**Réutilisation pattern audio existant** : ~60% du code MediaRecorder de TexteSource est conservable tel quel (`pickAudioMime`, `getUserMedia`, instanciation `MediaRecorder` + fallback, `stopMediaStream`, `activeRef` anti-race, bips audio WebAudio, 3 zones d'état UI). Le travail = câblage WS + refactor `recorder.onstop` + extension à 6 états + 3 erreurs `getUserMedia` distinctes.

**Estimation** : 5-8h (initial 📊) → **4-6h, 1-2 sessions** (🎯). Gain : -1h dépréciation backend sans objet + -1h pattern audio frontend réutilisable.

**Décisions D7-D16 — état après affinement** :
| # | Reco confirmée | Note |
|---|---|---|
| D7 | Hook custom `useTranscribeStream` | Renforcé — AuthContext = auth only, 1 seul caller TexteSource = inutile Context global |
| D8 | β (interim volatile au-dessus du champ + final injecté) | Pré-cadrage UX maintenu |
| D9 | **α (modal `showError`) pour Phase 3.1** | **Nuance importante** : retenu pour MVP (zéro code nouveau, `errorDialog.js` minimaliste 10 lignes). **Revue prévue Phase 5.x si feedback utilisateur sur lourdeur** (D16 induit 3 erreurs `getUserMedia` distinctes = potentiellement 3 modales blocantes dans le flow dictée). Cette nuance doit apparaître dans le post-mortem Phase 3.1. |
| D10 | α + δ (default 48 kHz backend + maj spec §10.2) | À tester en ouverture (5 min `MediaRecorder.isTypeSupported` + log) |
| D11 | Détection au mount (`pickAudioMime` existe déjà) | 5 min de travail |
| D14 | Aucun retry (MVP) | Confirmé |
| D15 | Heuristique client (cookie absent → "session expirée") | Renforcé — AuthContext refresh proactif 10 min rend l'heuristique fiable >95% |
| D16 | Prompt au click + 3 erreurs distinctes | Code partiellement présent (lignes 157-161 gèrent `NotAllowedError` + `SecurityError`), ajouter `NotFoundError` + `NotReadableError` = ~10 min |

**Risques concrets identifiés** :
1. **Cookie httpOnly cross-port en dev local** : Vite `:5173` ↔ backend `:8000`. Vérifier que `vite.config.js` proxy `ws: true` activé (sinon le cookie n'est pas transmis sur la WS). Smoke test 5 min avant d'écrire le hook.
2. **Timeslice `recorder.start(250)` obligatoire** : sans timeslice, `ondataavailable` ne fire qu'au `stop()` → comportement identique au batch (bug silencieux). À ne pas oublier dans la spec du hook `useTranscribeStream`.

**Items à faire en clôture Phase 3.1** :
- Retirer item DoD "Route POST /api/transcribe backend dépréciée" (sans objet)
- Acter la nuance D9 dans le post-mortem (revue Phase 5.x conditionnelle)
- Renommer dette TRACKER "REMPLACER webkitSpeechRecognition" → "Migrer dictée batch → WS Deepgram streaming" puis déplacer en FAIT

---

## Tableau estimatif

> Légende **Affinement** : 🎯 affiné (±30 min vérifié sur code) · 📊 large (estimation initiale non confrontée au code).

| Phase | Scope perçu | Heures | Sessions | Affinement | Risque dépassement |
|---|---|---|---|---|---|
| 3.1 | Frontend WS (refactor TexteSource batch→stream — backend déjà OK) | 4-6h | 1-2 | 🎯 | Faible-Moyen (cookie cross-port proxy Vite WS + timeslice `recorder.start(250)`) |
| 3.2 | Tests Edge MediaRecorder Opus + vraie voix | 2-4h | 1-2 | 📊 | **Élevé** (debug vocabulaire, voix réelle imprévisible) |
| 4.1 | Admin STT lecture seule | 2-3h | 1 | 📊 | Faible (`snapshot()` déjà prêt grâce à 2.2 D5γ) |
| 4.2 | Cron monitoring crédit Deepgram | 1-2h | 1 (groupable 4.3) | 📊 | Faible |
| 4.3 | Alertes expiration clé Deepgram | 1h | 1 (groupable 4.2) | 📊 | Faible |
| 5.1 | iOS PWA + fallback codec | 2-4h | 1-2 | 📊 | **Élevé** (Safari iOS MediaRecorder imprévisible) |
| 5.2 | CGU RGPD (mention provider US) | 1-2h | 1 (groupable 5.4) | 📊 | Faible (rédaction, pas de code) |
| 5.3 | TRACKER sync audit final | 1h | 0.5 (groupable 5.5) | 📊 | Faible |
| 5.4 | Aide section dictée prof | 1-2h | 1 (groupable 5.2) | 📊 | Faible |
| 5.5 | Push v3.3.0 MINOR + sync afia.fr | 1-2h | 1 | 📊 | Moyen (premier push réel, stress prod) |

---

## Hypothèses de calcul

1. **Durée d'une session ≈ 2-3h** de travail effectif (discussion + code + tests + commit). Calibré sur la session Phase 2.2 en cours. Si tes sessions sont plus courtes (1h) ou plus longues (4h+), ajuster proportionnellement.
2. **Temps humain ≠ temps session** — une phase de doc (ex : 5.2 CGU) peut prendre 1 session courte mais nécessiter ensuite plusieurs jours de macération avant validation. Le tableau parle de **sessions de travail actif**, pas de temps calendaire.

---

## Synthèses possibles

### Groupage agressif — 8 sessions, ~18-25h

| Bloc | Contenu | Sessions |
|---|---|---|
| Frontend | 3.1 | 2-3 |
| Tests réels | 3.2 | 1-2 |
| Admin | 4.1 | 1 |
| Monitoring | 4.2 + 4.3 | 1 |
| iOS | 5.1 | 1-2 |
| Doc | 5.2 + 5.4 | 1 |
| Release | 5.3 + 5.5 | 1 |

### Granulaire (1 phase = 1 session) — 10-12 sessions

Plus de marge pour respirer entre phases, mais plus de context-switch d'ouverture/clôture par phase.

---

## Méthode d'affinement (règle validée 16/05/2026)

**Les estimations larges sans toucher le code = piège classique de la planification.** Pour chaque phase, **affiner à ±30 min en ouverture**, après lecture rapide du code/contexte réel.

### Procédure en 4 étapes

1. **Lire les fichiers concernés** avant de tomber dans le code de la phase :
   - Phase 3.1 → composants React `TexteSource*`, hooks audio existants, App.jsx routing
   - Phase 4.1 → routes admin existantes (`backend/routers/admin*.py`), composants `Admin/`
   - Phase 5.1 → manifest PWA actuel, détection UA existante
2. **Comparer le scope perçu à la réalité du code** (LOC, complexité, dépendances cachées, libs à ajouter/retirer)
3. **Réviser ±30 min l'estimation** dans le tableau ci-dessus — colonne Affinement passe de 📊 → 🎯
4. **Identifier 1-2 risques concrets** pas génériques :
   - ❌ "complexité React"
   - ✅ "TexteSource importe `react-speech-recognition` qu'il faudra retirer + audit des callers"

### Pourquoi maintenant

Éviter de naviguer 6 mois avec des estimations approximatives qui ne se confrontent jamais à la réalité du code. Confronter en ouverture économise la friction de dérapage en cours.

---

## Trois facteurs de dérapage connus

### 1. Phase 3.2 = la grande inconnue

Tester avec une vraie voix sur MediaRecorder Opus va probablement révéler :
- Vocabulaire pédagogique mal reconnu (cf. R1 "hypoténuse" déjà noté dans ROADMAP_PHASES.md)
- Latence inattendue
- Smart Format trop agressif (R2)

Chaque bug → mini-cycle "ajuster paramètres Deepgram → retester → re-ajuster". 1-2 sessions de prudence ; peut s'étaler si blocker structurel.

### 2. Phase 5.1 iOS = boîte de Pandore connue

Safari iOS sur MediaRecorder Opus = historiquement capricieux. Le fallback peut nécessiter une stratégie complète (upload batch au lieu de stream ? feature flag par User-Agent ? détection codec en runtime ?) qui dépasse "un petit fallback". **Surveiller le scope** pour ne pas tirer le fil trop loin — si ça déborde, isoler dans une Phase 5.1.bis.

### 3. L'effet "trop calme" des phases finales

5.2 / 5.3 / 5.4 paraissent triviales mais ce sont des phases de **rédaction** qui exigent de la concentration et s'enchaînent mal en fin de chantier (fatigue accumulée). Prévoir mentalement qu'une "petite" phase de doc peut prendre une session calendaire complète même si 1h suffit techniquement.

---

## Politique de mise à jour

- À chaque **ouverture** de phase : passer affinement 📊 → 🎯 après lecture du code, ajuster ±30 min, noter 1-2 risques concrets
- À chaque **clôture** de phase : cocher la checklist + retirer la ligne du tableau estimatif (ou marquer ✅)
- Hypothèses + facteurs de dérapage : mettre à jour si on découvre un nouveau pattern récurrent
