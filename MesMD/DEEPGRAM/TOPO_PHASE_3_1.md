# Topo Phase 3.1 — Frontend WS Deepgram + refactor TexteSource

**Branche** : `main` · **Commits ahead** : 22 (non pushés) · **Push prévu** : Phase 5.5 (v3.3.0 MINOR)
**Handoff complet** : [REPRISE_PHASE_3_1.md](REPRISE_PHASE_3_1.md) — référence canonique pour tous les détails

> **Document de cadrage opérationnel** pour l'équipe humaine + Claude en cours de session.
> Pour amorçage Claude au démarrage d'une nouvelle conversation, voir [REPRISE_PHASE_3_1.md](REPRISE_PHASE_3_1.md) Section 12.

---

## 1. Ce qu'on doit livrer

> **Écart découvert vs handoff** : `webkitSpeechRecognition` est **absent du code** (vérifié grep project-wide 17/05/2026). [TexteSource.jsx](../../frontend/src/components/TexteSource.jsx) utilise **déjà** `MediaRecorder` + `getUserMedia`, et envoie le blob en POST batch (`POST /api/transcribe`, ligne 130). La dictée est désactivée avec un message d'attente (ligne 389). Le scope réel de Phase 3.1 est donc **refactor batch → streaming WS**, pas remplacement Web Speech API.

Dans [frontend/src/components/TexteSource.jsx](../../frontend/src/components/TexteSource.jsx) :
- **Capture audio** : `MediaRecorder` Opus mono, chunks 250 ms (pattern déjà en place, à ajuster)
- **Transport** : remplacer `POST /api/transcribe` (batch) par WebSocket `/api/transcribe/stream` (cookie httpOnly `aschool_access` transmis automatiquement)
- **Streaming** : chaque chunk `dataavailable` → `ws.send(blob)` au lieu d'attendre le blob final
- **Réception** : messages JSON `transcript` (interim/final) + `session_warning` (T-60s)
- **Affichage** : interim gris/italique, final noir (spec §10.4)
- **Bouton micro** : 6 états (disponible / en cours / saturé / indisponible / timeout / non supporté) — réactiver le bouton actuellement grisé
- **Cleanup unmount** : `MediaRecorder.stop()` + `MediaStream.getTracks().stop()` + `ws.close(1000)` (sinon LED micro reste allumée — pattern déjà partiellement présent `stopMediaStream`)
- **Dépréciation** : retirer la route `POST /api/transcribe` batch côté backend une fois la nouvelle dictée validée (vérifier zéro caller restant)

---

## 2. Acquis solides — ne PAS rejouer

- **Backend WS livré et testé** : route `/api/transcribe/stream` opérationnelle (commit `9256cab`), 7/7 PASS robustesse (commit `fc09c34`)
- **Auth WS** : lecture directe `websocket.cookies.get("aschool_access")`, déjà câblé
- **Pattern asyncio backend** : `create_task` + `cancel`-in-finally (côté serveur, on n'y touche pas)
- **Encoding query string** : `?encoding=opus|linear16` whitelistés, hors-whitelist → close 1003
- **Watchdog warning T-60s** : payload `session_warning` envoyé automatiquement par le serveur
- **Filet de sécurité** : `python test_phase22.py` doit rester 7/7 PASS pendant toute Phase 3.1 — à relancer si on touche par accident à `transcribe.py`, `session_tracker.py` ou `deepgram_provider.py`

---

## 3. Pré-requis avant la première ligne de code

1. Lancer `.\run.ps1` → vérifier que backend (`:8000`) et frontend (Vite) démarrent
2. `GET /api/health` → `{"status":"ok","service":"aSchool API"}`
3. `python test_phase22.py` → 7/7 PASS exit 0
4. Edge installé + micro physique branché (pour tester `getUserMedia`)
5. **`DEEPGRAM_API_KEY`** présente dans `.env`

---

## 4. Affinement 30-45 min (procédure d'ouverture obligatoire)

À exécuter **avant** de toucher au code Phase 3.1 :

1. **Lire** [frontend/src/components/TexteSource.jsx](../../frontend/src/components/TexteSource.jsx) (400 lignes — pattern MediaRecorder déjà en place, voir écart découvert Section 1) + grep des imports `TexteSource` dans `frontend/src/**/*.jsx` pour identifier les callers
2. **Lire** [frontend/src/App.jsx](../../frontend/src/App.jsx) (1043 lignes, routing), [frontend/src/context/AuthContext.jsx](../../frontend/src/context/AuthContext.jsx) (pattern état global), [frontend/src/errorDialog.js](../../frontend/src/errorDialog.js) (pattern `showError`)
3. **Comparer** scope perçu vs LOC réel → mettre à jour [CHECKLIST_PHASES.md](CHECKLIST_PHASES.md) ligne Phase 3.1 (📊 → 🎯) 30-45 min
4. **Identifier 1-2 risques concrets** (ex : "TexteSource importe X qu'il faut retirer + Y callers à migrer"), pas génériques
5. ✅ **Vérification effectuée 17/05/2026** — la route `POST /api/transcribe` côté backend **n'existe pas** (grep project-wide `backend/main.py`, `backend/routers/`, `backend/groq_client.py`). TexteSource ligne 130 appelle un endpoint mort, c'est la raison du bouton désactivé. **Scope Phase 3.1 = purement frontend, pas de dépréciation backend à faire.**

---

## 5. Décisions D7-D16 — ✅ ACTÉES 17/05/2026 (8/8)

> Validées après affinement complet (rapport en CHECKLIST_PHASES.md section "Phase 3.1 — ouverture 🎯"). Snapshot final pour A3.

| # | Décision | **Reco actée** |
|---|---|---|
| **D7** ✅ | État React pour la session WS | **Hook custom `useTranscribeStream(...)`** — encapsule MediaRecorder + WS + cleanup en unité locale à TexteSource. AuthContext = auth only, 1 seul caller TexteSource = inutile Context global |
| **D8** ✅ | Affichage interim/final | **β — zone interim volatile insérée entre textarea et boutons (gris/italique), final injecté dans le textarea principal via `onChange` existant.** Justifié par UX de relecture (Smart Format §R2 — "hypoténuse" → "hypothèse"). |
| **D9** ✅ | Erreurs UX | **α — modal `showError` pour tout (MVP Phase 3.1)**. Nuance importante : **revue prévue Phase 5.x si feedback utilisateur sur lourdeur** (D16 induit 3 modales possibles dans le flow dictée). Trace dans CHECKLIST post-mortem obligatoire. |
| **D10** ✅ | sample_rate Opus 48 kHz | **α + δ — ajuster default `STTSessionConfig.sample_rate = 48000` côté backend quand `encoding=opus` + maj spec §10.2 (16 kHz → 48 kHz).** Patch backend reporté commit 2 (clôture) après validation empirique 5 min en A3 (`MediaRecorder.isTypeSupported('audio/webm;codecs=opus')` + log `audioBitsPerSecond` réel sur Edge). Si surprise → arbitrage à ce moment-là. |
| **D11** ✅ | Détection MediaRecorder | **Mount — `pickAudioMime()` (déjà présent lignes 105-116 de TexteSource) exécuté en `useEffect([])`** → state `isSupported`. Bouton grisé permanent + tooltip si false. Tooltip = attribut `title=""` HTML natif (pattern projet confirmé : 5 usages déjà dans TexteSource lignes 262, 358, 367, 378, 389). |
| **D14** ✅ | Reconnect/retry close inattendu | **Aucun retry MVP — `showError` au close 4502/4408/1011, le prof re-clique**. Pas de backoff, pas de compteur. Revisitable Phase 4.x après observation patterns réels. |
| **D15** ✅ | Désambiguïsation pré-accept | **Pivot vers AuthContext** (correction : `document.cookie` ne voit pas les cookies httpOnly, le pattern initial était mort dans l'œuf). Le hook consomme `const { user } = useAuth()` en interne ; sur close pré-accept (1008 ou 4401 — à confirmer A3 par grep `backend/routers/transcribe.py`) : `user` présent → "Service de dictée saturé. Réessayez dans quelques minutes." / `user` null → "Session expirée. Reconnectez-vous pour utiliser la dictée." Fiabilité estimée >95%. Edge case "logout cross-tab entre 2 refresh AuthContext" → noté en dette légère Phase 5.x (refresh AuthContext sur `visibilitychange` au réveil onglet). |
| **D16** ✅ | Permission `getUserMedia` | **Prompt au click + 3 erreurs distinctes** étendant lignes 157-161 existantes : `NotAllowedError` → "Accès au microphone refusé. Pour utiliser la dictée, autorisez l'accès dans les paramètres du navigateur." / `NotFoundError` → "Aucun microphone détecté. Branchez un micro et réessayez." / `NotReadableError` → "Le microphone est occupé par une autre application (Teams, Zoom...). Fermez l'autre application et réessayez." |

*(D12 fusionné dans D11, D13 backpressure traité inline Section 6 du handoff)*

### Notes à appliquer pendant l'écriture du code A3 (pas des décisions à rouvrir)

- **D8** : zone interim avec toggle CSS `display: interim.length > 0 ? 'block' : 'none'` plutôt qu'un container permanent qui réserve sa place → évite le saut visuel quand la dictée démarre/s'arrête
- **D10** : patch backend `STTSessionConfig.sample_rate = 48000` reporté au commit 2 après validation empirique Edge (si surprise, arbitrage)
- **D11** : `title=""` HTML natif suffit, pas de composant `<Tooltip>` à créer
- **D15** : grep `1008|4401|websocket.close` dans `backend/routers/transcribe.py` en début A3 pour confirmer le mapping codes close pré-accept réellement utilisé (30 sec)

### Dette légère notée hors scope Phase 3.1

- **Refresh AuthContext sur `visibilitychange`** : durcir l'edge case "logout cross-tab entre 2 refresh 10 min" → à évaluer Phase 5.x si pertinent

---

## 6. Dettes TRACKER connexes (à traiter dans la foulée si possible)

1. **REMPLACER webkitSpeechRecognition** → **dette mal nommée** (le code n'utilise pas webkit, c'est un refactor batch → stream) → à reformuler en "Migrer dictée batch → WS Deepgram streaming" puis cocher en FAIT à la clôture
2. **sample_rate paramétrable** → directement lié à **D10**, à trancher ici ou explicitement reporter à 3.2
3. **Aide — Rubrique dictée (réactivation micro)** → **à enrichir obligatoirement dans Phase 3.1** (dette TRACKER + règle CLAUDE.md absolue Aide à chaud). D16 traite `getUserMedia` par définition du scope MediaRecorder, donc l'Aide micro n'est pas conditionnelle, elle est induite.
4. **Modal multi-actions** (`showConfirm`) → groupable avec **D9** si on retient α

---

## 7. Garde-fous absolus

- **Ne pas commiter** les modifs hors scope du working tree (RAG, L5 Consigne, errorDialog refonte, Groq fallback, prompts, specs déplacées) → cf. Section 4 et 10 du handoff pour la liste
- **Ne pas toucher** à `backend/auth.py` ni `backend/routers/auth.py` (règle CLAUDE.md absolue)
- **Edge uniquement** comme navigateur de test (jamais Chrome — règle CLAUDE.md absolue)
- **Pas de nouvelle dépendance npm** prévue : `MediaRecorder` + `WebSocket` sont natifs

---

## 8. Méthode de travail (validée 16-17/05/2026)

- 2 réfléchissent (chef de projet + Claude), 1 seul écrit le code (Claude : Edit/Write/Bash)
- Yes/no avant action environnement (pip install, git push, suppression de fichier)
- Pas de pré-décision dans les handoffs : recos étiquetées "non tranchée"
- Propositions indifférentes : l'un ou l'autre propose, on s'aligne, Claude édite

---

## 9. Définition de "Phase 3.1 close"

- [ ] `TexteSource.jsx` : dictée refactorée batch (`POST /api/transcribe`) → streaming WS (`/api/transcribe/stream`)
- [ ] 6 états du bouton micro implémentés et testables visuellement
- [ ] Cleanup unmount validé (LED micro éteinte, pas de WS leak)
- [ ] Smoke test manuel Edge : dictée → texte transcrit en direct → final injecté
- [ ] `test_phase22.py` toujours 7/7 PASS
- [ ] Section Aide enrichie — réactivation micro + 3 erreurs `getUserMedia` (`NotAllowedError` / `NotFoundError` / `NotReadableError`)
- [ ] `ROADMAP_PHASES.md` Phase 3.1 cochée + SHA consigné
- [ ] `CHECKLIST_PHASES.md` Phase 3.1 bilan post-mortem (réel vs estimation affinée)
- [ ] TRACKER : déplacer la dette "Migrer dictée batch → WS Deepgram streaming" en FAIT
- [ ] Commit propre `feat(stt): Phase 3.1 — frontend WS + refactor TexteSource batch→stream`

---

**Items restants après Phase 3.1** : 9 (3.2 → 5.5). Ordre crucial : **Phase 3.2 (tests vraie voix Edge) DOIT être close avant 4.x** (sinon monitoring bâti sur route encore instable = dette assurée).
