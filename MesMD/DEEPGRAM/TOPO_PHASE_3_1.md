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
5. **Identifier la route POST batch actuelle** (`POST /api/transcribe`, confirmé ligne 130 de TexteSource.jsx) qui sera supprimée avec le refactor — vérifier qu'aucun autre caller ne l'utilise avant dépréciation

---

## 5. Décisions à trancher en ouverture (8 décisions imbriquées)

> Recos non tranchées dans le handoff. D8 désormais pré-cadrée (voir ci-dessous). À discuter et valider avant de coder.

| # | Décision | Reco |
|---|---|---|
| **D7** | État React (Context / Hook custom / inline) | **Hook custom** `useTranscribeStream(...)` |
| **D8** | Affichage interim/final (zone unique / interim séparée / inline CSS) | **β — zone interim volatile au-dessus du champ, final injecté dans le champ principal.** Justifié par UX de relecture avant validation : la dictée aSchool sert à saisir des énoncés pédagogiques (vocabulaire technique sensible à Smart Format, ex. "hypoténuse" → "hypothèse"). Le prof doit pouvoir valider visuellement chaque phrase avant qu'elle s'inscrive. Voir Smart Format spec §R2. |
| **D9** | Erreurs (modal showError / Toast / Banner) | **α (modal, cohérence) ou β (toast pour récupérables)** |
| **D10** | sample_rate Opus 48 kHz (default backend + spec / query string / downsampler) | **α + δ** (ajuster default + maj spec §10.2) |
| **D11** | Détection MediaRecorder (mount / lazy click) | **Mount** (`MediaRecorder.isTypeSupported`) |
| **D14** | Reconnect/retry sur close inattendu | **Aucun retry (MVP)**, message clair |
| **D15** | Désambiguïsation pré-accept (générique / heuristique client / endpoint diagnostic) | **Heuristique client** (cookie absent → "session expirée", sinon → "service saturé") |
| **D16** | Permission `getUserMedia` (click / mount + 3 erreurs : NotAllowed / NotFound / NotReadable) | **Prompt au click** + messages distincts par type |

*(D12 fusionné dans D11, D13 backpressure traité inline Section 6 du handoff)*

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
- [ ] Route `POST /api/transcribe` backend dépréciée (ou ticket de dépréciation ouvert si caller résiduel)
- [ ] `ROADMAP_PHASES.md` Phase 3.1 cochée + SHA consigné
- [ ] `CHECKLIST_PHASES.md` Phase 3.1 bilan post-mortem (réel vs estimation affinée)
- [ ] TRACKER : déplacer la dette "Migrer dictée batch → WS Deepgram streaming" en FAIT
- [ ] Commit propre `feat(stt): Phase 3.1 — frontend WS + refactor TexteSource batch→stream`

---

**Items restants après Phase 3.1** : 9 (3.2 → 5.5). Ordre crucial : **Phase 3.2 (tests vraie voix Edge) DOIT être close avant 4.x** (sinon monitoring bâti sur route encore instable = dette assurée).
