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
  - [x] gate maths retirée de generate.py ; collection morte supprimée de ChromaDB (23/06)
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
> ✅ **Phase 3 close (22/06)** : overlap + déduplication + seuil de score + alignement métadonnées livrés. Base CIEL définitive ré-ingérée (236 chunks, A:187/B:49).
- [x] **(2) Chevauchement (overlap) au chunking** — validé (21/06), code commité, ré-ingestion différée
  - mécanisme générique dans `chunker.py` (`overlap_chars`, défaut 0 = rétro-compatible) ; valeur `OVERLAP_CHARS=150` (~17 % de MAX_CHARS) dans la fiche CIEL ; passée par `ingest_referentiel.py`. Le moteur ne sait pas que c'est CIEL.
  - overlap sur la coupe de TAILLE uniquement (pas frontière, pas inter-pages) → tag A/B intact. Cas limite : ligne unique > overlap ⇒ coupe nette.
  - preuve : dry-run overlap=0 strictement identique (222 chunks, A:177/B:45) · mesure 0→222 / 100→234 / 150→238 / 200→244, **pages B identiques pour toutes** (partition A/B invariante) · `test_chunker.py` 6 verts · 13 tests verts au total.
- [x] **(3) Déduplication au chunking** — validé (21/06), code commité, ré-ingestion différée
  - mécanisme générique dans `chunker.py` (passe post-découpage, param `dedup_key`, défaut `None` = rétro-compatible) ; `dedup_key=(text, option)` dans la fiche CIEL (ignore la page, respecte l'option → protège A/B) ; passée par `ingest_referentiel.py`.
  - détection EXACTE (texte complet), garde la **1re occurrence** (page la plus basse) ; dédup au **chunk entier** uniquement → ne touche jamais au recouvrement de l'overlap.
  - preuve : dédup OFF identique (222/238) · ON overlap=0 → **222→220**, overlap=150 → **238→236** (2 boilerplate p.81-82 option A retirés) · **partition A/B invariante** (B-pages identiques) · overlap non amputé (−3 paires = effet mécanique du retrait de 2 chunks, prouvé par `test_dedup_ne_mange_pas_loverlap`) · **18 tests verts**.
- [x] **(1) Seuil de score minimal** — validé (21/06), base définitive ré-ingérée, code commité
  - constat (mesuré base définitive) : pas de coupure nette bruit/contenu ; l'administratif (annexes) peut scorer haut → le seuil n'est PAS un filtre de l'administratif, seulement un **filet anti-hors-sujet pur**. `SCORE_MIN=0.33` calibré sur la distribution mesurée (hors-sujet ≤0.28-0.34 vs intentions légitimes ≥0.35).
  - `SCORE_MIN=0.33` dans la fiche CIEL ; **filtre strict au niveau endpoint** (`exemple_referentiel.py`, `retrieve()` reste pur) : un chunk <0.33 n'entre jamais dans le prompt.
  - cas vide (rien ≥ seuil) → `available=False`, **`generate()` NON appelé**, champ `message` (wording C) renvoyé et affiché en **modale bloquante** côté prof (cascade frontend `TexteSource.jsx`, joignabilité).
  - preuve : « ventilateur plafonnier » → 0 génération + message C ; « cybersécurité » → génère ; **20 tests verts** ; build frontend OK.
- [x] **(4) Aligner métadonnées écriture/lecture** — validé (22/06), base ré-ingérée, code commité
  - constat (grep global, tests inclus) : la fiche CIEL écrivait 6 clés (`source, label, cycle, niveau, option, page`) ; `label` et `cycle` étaient **écrites mais lues NULLE PART** (ni code ni test). Le « programme » fantôme (clé *lue* dans `_build_rag_prefix` mort, jamais écrite) relève de la suppression du préfixe RAG mort → **reste en Phase 6** (ligne dédiée), non traité ici (volontaire).
  - action : retrait de `label`/`cycle` de `chunk_metadata` (fiche CIEL) + constantes `LABEL`/`CYCLE` orphelines supprimées ; commentaire `retrieve.py` aligné (`option, niveau, source, page…`). `chunk_metadata` ne pose plus que **{source, niveau, option, page}**.
  - preuve : ré-ingestion **236→236** (A:187/B:49, partition invariante) ; verrou `test_metadata_exactement_quatre_cles` (set des 4 clés sur base ré-ingérée) ; **55 tests verts**.

---

## Phase 4 — ADMINISTRABLE (piloter sans toucher au code)
- [ ] Centraliser les réglages LLM (modèle, fournisseur, max_tokens, température, prompts) en base
     * C’est exactement le cœur de la Phase 4. 
     * Découpé en sous-points (un par session) : 4.1.a modèle · 4.1.b UI+validation · 4.1.c max_tokens · 4.1.d température · 4.1.e fournisseur.
     * **[x] 4.1.a — modèle texte lu boot → runtime** — validé (22/06). Clé `ai_model` dans `SETTING_DEFAULTS` + résolveur `get_ai_model(db)` (réutilise `get_settings_dict`, table `Setting` existante, aucune table créée). `generate()` gagne `model` (reste pur, `src/` n'importe pas `backend/`) ; 6 routers câblés (`model=get_ai_model(db)`), `db` ajouté à `exemple_referentiel`. Lecture par requête → modèle **rechargeable à chaud** acquis en bonus. Preuve : `test_settings_model.py` (repli + lecture base + à chaud + chaîne `/api/generate`), **61 tests verts**. Reste : Whisper/OCR en dur (hors sujet), écriture du réglage = 4.1.b.
     * **[x] Structure Paramètres (options + onglets) — PRÉREQUIS de 4.1.b** — chantier à part. Menu admin `Paramètres` (entrée plate) → groupe d'**options** (motif Analytique : groupe nav + route imbriquée) ; **dans chaque option, des onglets locaux** (state de page, pas des routes). Croissance future dans l'option (max_tokens/température/prompts = onglets de « Génération LLM »), pas en empilant à plat. Démarrage = 2 options traitées ENSEMBLE (règle conversion sans orphelin) : **Génération LLM** (onglet Modèle, coquille) + **Email** (rehome de la carte email de bienvenue existante, sinon orpheline). À faire AVANT 4.1.b. **✅ Livré 22/06** (commit `0a8e8e5`) — testé OK (Paramètres se déplie en 2 options ; Email sans régression).
     * **[x] 4.1.b — écriture admin du modèle (combo fermée, Option 3)** — l'admin choisit `ai_model` dans une liste déroulante alimentée par le backend (`GET /admin/ai-models`), enregistrée via `PUT /admin/ai-model` (endpoints dédiés, garde-fou liste blanche conservé en filet, PUT email inchangé). Invalidité **structurellement impossible** (pas de texte libre) → règle « incohérence » poussée au max. Liste = constante `SUPPORTED_AI_MODELS` **en dur** (une ligne à éditer pour ajouter un modèle). **✅ Livré 22/06** (commit `987f686`) : combo dans l'onglet Modèle (`AdminParametresGeneration.jsx`) + reliquat backend + `test_admin_ai_model.py` ; aide « Génération LLM › Modèle » rédigée. Preuve : `67 passed` (suite complète) + test manuel admin OK (sélection persiste après rechargement).
       **Trajectoire ai_model (cap validé 22/06 — étape 1 LIVRÉE ; pistes 1-2 non codées) :** (1) maintenant = liste en dur, combo ; (2) piste 1 = liste vivante en **base**, gérée depuis l'écran admin sans code — exige son propre garde-fou « ce modèle existe-t-il vraiment chez le fournisseur ? » sinon on réintroduit le risque de la saisie libre ; (3) piste 2 = liste **remplie depuis l'API fournisseur** (Groq/Claude) — pas 100 % auto : l'API ne distingue pas un modèle de génération d'un Whisper/vision/TTS (filtrage à prévoir) et le listing est **par fournisseur**. Fil rouge des 3 étapes : « quels modèles sont valides POUR GÉNÉRER » reste un **jugement humain** qu'aucune API ne donne tout cuit ; l'étape 1 le tranche au plus simple. Pistes 1 et 2 = cap, **ni codées ni préparées**.
     * **[x] 4.1.c — max_tokens administrable (HYBRIDE)** — validé 22/06. **Fork tranché :** administrable, **hybride** (défaut global + surcharges), plancher dur **256** / plafond **interne CIEL 8000** (figé, indépendant du plafond théorique du modèle). Résolveur `get_max_tokens(db, outil)` sur le motif de `get_ai_model` (lecture par requête → rechargeable **à chaud**) ; 4 clés dans `SETTING_DEFAULTS` (`max_tokens_default=2048` + **3 surcharges semées 3000/4000/6000 = anti-régression**, sinon retombée à 2048) ; **6 routeurs câblés** (activité/exemple/consigne → défaut, ambiguïtés/séquence/optimiseur → surcharge ; consigne 2000→2048 assumé). Endpoints dédiés `GET`/`PUT /admin/max-tokens` (validation bornes → 400 humain, audit `UPDATE_MAX_TOKENS`, PUT email + PUT ai-model intacts) ; UI onglet « Longueur (tokens) » dans `AdminParametresGeneration.jsx` (1 défaut + 3 surcharges, bord rouge + bouton désactivé + **modale `showError`** hors bornes, jamais inline). OCR `generator.py:125` non touché. **Preuve :** `test_settings_max_tokens.py` **13/13** (résolveur hybride + surcharges semées sans BDD + à chaud + repli surcharge corrompue + chaîne `/api/generate` + GET/PUT/401/isolation) · suite complète **80 passed** · build frontend OK · **test manuel admin OK** (persistance après rechargement + modale hors bornes). **Compléments même chantier :** hints « valeur d'usine » sous chaque champ de l'onglet (commit `e5a93a9`) + **Aide admin** « Génération LLM › Longueur (tokens) » rédigée dans `AdminAide.jsx` (oubliée au 1er passage, rattrapée en session).
     * **[⏸️] 4.1.e — fournisseur** — suspendu après e.4, voir TRACKER_FOURNISSEURS_IA.md (acquis e.0/e.3/e.4 ; reprise = découpage B.1→B.5).
- [ ] Interface admin qui lit/écrit ces réglages (voir TRACKER_FOURNISSEURS_IA.md)
     * C’est la continuité logique de la table Setting, aucune ambiguïté.
- [ ] Validation des valeurs (modale bloquante sur saisie invalide)
     *  Indispensable : tu as déjà noté que PUT /admin/settings n’a aucune validation, c’est un point obligatoire.
- [ ] Réglages rechargeables à chaud (pas de redémarrage)
     * C’est la condition pour « administrable sans toucher au code ». Sans reload à chaud, la Phase 4 serait incomplète.

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
- [x] cleanup `src/prompts.py:_build_rag_prefix` — préfixe RAG mort supprimé le 23/06 (+ paramètre `rag_chunks` de `build_prompt`, plus aucun appelant).
- [ ] cleanup : sortir la base ChromaDB (`backend/rag/chroma_db/`) du suivi git → `.gitignore` + reconstruction par `ingest_referentiel` au déploiement (« données ≠ code »). Décision (c) du 21/06 ; aujourd'hui la base est versionnée et committée, ce nettoyage la décorrèle du repo plus tard.
- [ ] Aide : expliquer au prof que l'exemple généré peut varier à chaque essai
  (texte reformulé par le LLM) alors que l'ancrage référentiel, lui, reste
  identique (recherche déterministe). Prévoir une version courte côté prof et
  une version avec la distinction recherche/génération côté admin.
- [ ] À ÉTUDIER (complexe, laissé en option) : épreuves dont le détail vit en
  ANNEXE et diverge du corps du référentiel (ex. épreuve E6 du BTS CIEL). Les
  annexes des référentiels FR portent souvent du contenu aussi important que
  le corps → ne jamais présumer "annexe = bruit". Étude dédiée plus tard.

---

## 🖥️ Backlog — écran « RÉSULTAT GÉNÉRÉ » (écran central, ~90 % de l'usage prof)

> Réservoir VIVANT propre à cet écran : chaque bug ou idée repéré ici s'ajoute au fil de l'eau, on se met d'accord puis on traite en session(s) dédiée(s). (Emplacement provisoire dans ce tracker — déplaçable plus tard si on préfère.)

- [ ] **Éditer les RÉPONSES du résultat généré** : rétablir/créer la possibilité de corriger une réponse à la main (le crayon est sur les réponses, jamais sur le texte source). À cadrer : interaction avec « Régénérer » et « Mes activités ». Vérifier d'abord (historique git) si ça existait avant = régression, ou si c'est à créer.
- [ ] **Texte source éditable après génération — logique validée (21/06)** : le texte source RESTE modifiable même après génération. Le résultat n'est qu'une PHOTO, mise à jour UNIQUEMENT au clic « Régénérer » (pas de mise à jour silencieuse, le prof décide). La désynchro source↔résultat se traite par un SIGNAL discret (« le résultat ne correspond plus au texte source — Régénérez » et/ou exports neutralisés tant que désynchro), JAMAIS par un verrou du source.

---

## 📌 Rappels transverses (ne pas oublier)
- [ ] Le jour de la bascule Claude : vérifier temperature / mode JSON Opus → ajuster l'ADAPTATEUR, jamais le métier
- [ ] Adaptateur Anthropic : forme actuelle = SDK + clé API ; cible = `claude -p` (compte/abonnement). À rebrancher à la bascule Claude, en vérifiant que le timeout 60 s se reporte sur cette voie. Dans l'adaptateur, jamais le métier.
- [ ] Rectifier la doc d'archi (doc 2) : base réelle = SQLite, pas PostgreSQL
- [ ] Groq conservé uniquement pour : transcription audio (Whisper) + OCR/vision
