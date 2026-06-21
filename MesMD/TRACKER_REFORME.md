# 🛠️ Tracker — Réforme A-School (moteur LLM + RAG)

> Suivi partagé Harketti / Claude Code.
Ce Mini-Tacker complet. Il reflète l'état réel d'aujourd'hui : "le suivre et le mettre à jour". Ne touche à rien d'autre.
Il couvre les 6 phases + les rappels transverses (la note Claude/température, la rectif doc SQLite, et Groq gardé pour Whisper/OCR uniquement) — pour qu'on n'oublie rien.



> Règle :le suivre et le mettre a jour une tâche à la fois, Plan Mode → GO → code → preuve → validation.
> `[x]` = fait et validé · `[~]` = en cours · `[ ]` = à faire

---

## Phase 0 — AUDIT (constat strict, 6 blocs) ✅ TERMINÉ
- [x] Bloc 2 — LLM-agnostique (2.1 → 2.5)
- [x] Bloc 1 — Coût / Quota / Batch (1.1 → 1.7)
- [x] Bloc 3 — Administrable (3.1 → 3.5)
- [x] Bloc 4 — Scalable (4.1 → 4.5)
- [x] Bloc 5 — Future-proof (5.1 → 5.5)
- [x] Bloc 6 — RAG / Embeddings (6.1 → 6.7)
- [x] Croisement 2.4 ↔ 5.2 (cohérent, aucune divergence)
- [x] Décision d'archi RAG (moteur neutre + fiche par référentiel) — confirmée par CC

---

## Phase 1 — CŒUR VITAL (nettoyage du moteur LLM) ✅ TERMINÉE
- [x] **Tâche 1** — Supprimer le chemin RAG « maths »
  - [x] gate maths/cycle4 + collection retirées (generate.py)
  - [x] flag RAG_ENABLED + RAG_PROGRAMME_DEFAULT retirés (.env)
  - [x] champ `chunks` retiré de GenerateResponse
  - [x] tests verts (36/36), CIEL intact, commit fait
- [x] **Tâche 2** — Unifier tous les appels LLM via generate() — validée + commit `aa79351` (21/06)
  - [x] generate() paramétrable (max_tokens, temperature, json_mode) — intentions neutres, traduites par adaptateur (JSON Claude = instruction système ; température ignorée chez Anthropic)
  - [x] 4 routeurs basculés sur generate() — valeurs reportées : ambiguites 3000, consigne 2000, sequence 4000, optimiseur 6000+temp 0+json_mode (capture du body : conforme)
  - [x] code Groq texte mort supprimé (call_groq, GROQ_URL, FALLBACK_CHAIN, FALLBACK_STATUSES, _headers) — Whisper conservé
  - [x] tests adaptés (patch generate, 4 tests repli retirés, propagation → 500) — 35/35 verts
- [x] **Tâche 4** — Sécuriser Claude : timeout explicite (60 s) à la construction du client Anthropic — voie propre du SDK, aligné sur les autres branches. py_compile + 35/35 verts. Validée (21/06).

---

## Phase 2 — REFONTE RAG (moteur neutre + fiche CIEL)
- [x] **Tâche 3** — Séparer l'algorithme générique de la logique CIEL — validée + preuve bout en bout (21/06)
  - [x] sortir les constantes CIEL (MAX_CHARS, MIN_CHARS, OPTION_B_SECTIONS, regex…) vers une fiche de réglages (`backend/rag/referentiels/bts_ciel_option_a.py`)
  - [x] séparer découpe générique / sectionnement + tag option A/B (`backend/rag/chunker.py` ← ex-ingest_referentiel.py:94-102 ; décision A/B émigrée dans la fiche)
  - [x] neutraliser la forme de retour de retrieve() (clé « programme » retirée, champ `meta` brut ajouté)
  - [x] critère tenu : ajouter un référentiel = écrire une fiche, zéro ligne touchée au moteur
  - preuve : dry-run avant/après identique (222 chunks A:177/B:45) · ingestion réelle 222 chunks niveau posé · extraction UTF-8 propre (0 caractère cassé) · retrieve() sans « programme » · /exemple-referentiel available=True · 7 tests verts

---

## Phase 3 — QUALITÉ DU DIFFÉRENCIATEUR (RAG CIEL fiable)
> Ordre acté : **2 overlap → 3 déduplication → 1 seuil de score → 4 alignement métadonnées**.
> ⚠️ Ré-ingestion réelle de la collection CIEL **différée à la fin du chunking** : overlap ET dédup touchent le découpage → on ne ré-ingère qu'**une seule fois**, les deux ensemble. La base reste à overlap=0 d'ici là (volontaire et assumé).
- [x] **(2) Chevauchement (overlap) au chunking** — validé (21/06), code commité, ré-ingestion différée
  - mécanisme générique dans `chunker.py` (`overlap_chars`, défaut 0 = rétro-compatible) ; valeur `OVERLAP_CHARS=150` (~17 % de MAX_CHARS) dans la fiche CIEL ; passée par `ingest_referentiel.py`. Le moteur ne sait pas que c'est CIEL.
  - overlap sur la coupe de TAILLE uniquement (pas frontière, pas inter-pages) → tag A/B intact. Cas limite : ligne unique > overlap ⇒ coupe nette.
  - preuve : dry-run overlap=0 strictement identique (222 chunks, A:177/B:45) · mesure 0→222 / 100→234 / 150→238 / 200→244, **pages B identiques pour toutes** (partition A/B invariante) · `test_chunker.py` 6 verts · 13 tests verts au total.
- [ ] (3) Déduplication au chunking
- [ ] (1) Seuil de score minimal (calibré sur données CIEL — mesurer, pas inventer)
  - constat (21/06, mesuré sur la vraie base) : scores faibles — requête courte « Réseaux » → 0.31–0.42 ; requête longue de domaine → ~0.62 max. À calibrer ICI, pas avant (hors périmètre Tâche 3).
- [ ] (4) Aligner métadonnées écriture/lecture (supprimer le « programme » fantôme)

---

## Phase 4 — ADMINISTRABLE (piloter sans toucher au code)
- [ ] Centraliser les réglages LLM (modèle, max_tokens, température, prompts) en base
- [ ] Interface admin qui lit/écrit ces réglages
- [ ] Validation des valeurs (modale bloquante sur saisie invalide)
- [ ] Réglages rechargeables à chaud (pas de redémarrage)

---

## Phase 5 — ROBUSTESSE / DETTE (non bloquant)
- [ ] Régulation de concurrence (file/limite) — protège serveur ET quota
- [ ] Unifier la stratégie de migration (garder versionné, retirer ALTER inline silencieux)
- [ ] Décision produit : rester SQLite ou migrer PostgreSQL
- [ ] Affiner les codes d'erreur (503/429/500 distincts)
- [ ] Robustesse indexation (filet autour de col.add, reprise/checkpoint)

---

## Phase 6 — COSMÉTIQUE / DIFFÉRÉ (en dernier)
- [ ] Hardcoding frontend (exemples, abréviations, défaut 'Français') — avec le CRUD Gap A
- [ ] CRUD Gap A : créer de nouvelles matières via interface admin
- [ ] P4.8 — alignement styling des cartes
- [ ] P4.9 — toast sur réinitialisation paramètres
- [ ] Bug Accueil : dernière SÉQUENCE affiche du Markdown brut
- [ ] cleanup `src/prompts.py:_build_rag_prefix` (l.2720-2748) : préfixe RAG « programme MEN cycle 4 », mort depuis Phase 1 (jamais appelé — `generate.py` ne passe pas `rag_chunks`). À supprimer.

---

## 📌 Rappels transverses (ne pas oublier)
- [ ] Le jour de la bascule Claude : vérifier temperature / mode JSON Opus → ajuster l'ADAPTATEUR, jamais le métier
- [ ] Adaptateur Anthropic : forme actuelle = SDK + clé API ; cible = `claude -p` (compte/abonnement). À rebrancher à la bascule Claude, en vérifiant que le timeout 60 s se reporte sur cette voie. Dans l'adaptateur, jamais le métier.
- [ ] Rectifier la doc d'archi (doc 2) : base réelle = SQLite, pas PostgreSQL
- [ ] Groq conservé uniquement pour : transcription audio (Whisper) + OCR/vision
