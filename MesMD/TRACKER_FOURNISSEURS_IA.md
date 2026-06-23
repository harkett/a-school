# TRACKER FOURNISSEURS IA — aSchool

> **Version : 0.3** (brouillon chat — à finaliser par CC, puis validation HARKETTI)
> **Rôle :** référence partagée unique sur le sujet « fournisseurs IA ». Toi, CC et le chat
> partent du même état, pour éviter les divergences (ex. écart constaté sur `max_tokens`).
> **Source des faits code :** audit terrain CC (20–22/06). Le terrain fait foi.
> **Indicateur de désync :** le numéro de version en tête.

---

## 1. Règle cadre — Tout en base, sauf les secrets (règle absolue)

C'est le principe directeur de tout le sujet, et de toute la Phase 4 « Administrable ».

- **Tout va en base.** Toute donnée, tout réglage, toute liste de référence a pour source
  de vérité finale la base (`Setting`). Jamais une valeur en dur dans le code, jamais une
  valeur figée dans le `.env`.
- **Seule exception : les secrets.** Clés API, mots de passe, `JWT_SECRET`, tokens restent
  au `.env` (ou gestionnaire de secrets). Un secret n'est pas un réglage administrable : il
  ne va **jamais** en base.
- **Gradation de tolérance.** Une valeur en dur n'est qu'un échafaudage transitoire, le temps
  de faire marcher localement. Elle se resserre : tolérée en brouillon local → à proscrire au
  commit → pire au push → **interdite en prod**. Avant la prod, c'est relié à la base. Point.

Raccords avec l'existant : cette règle **chapeaute** « pas de liste de référence en dur dans
le frontend » (15/06, qui en devient un cas particulier), donne son **principe directeur** à
la Phase 4, **complète** la règle « secrets » (un secret reste hors base), et **prolonge**
« profil = source unique » (une seule source de vérité, jamais dupliquée ni figée).

> Écriture de cette règle dans `CLAUDE.md` + fiche `feedback` : relève de la **mémoire CC**,
> à finaliser dans la discussion « CLAUDE_MD — GESTION DES RÈGLES ». Pas dans ce tracker.

---

## 2. Le mécanisme commun (le moule à calquer)

Tout réglage administrable suit le même pont (terrain CC) :

- Table `Setting` (couples clé/valeur). Pont : `get_settings_dict(db)` (`admin.py:70-75`) —
  part des défauts codés (`SETTING_DEFAULTS`) et écrase chaque clé par la ligne en base.
- **Un réglage « branché » = 3 critères :** (1) se lit via un **GET** ; (2) s'écrit via un
  **PUT** qui fait un **upsert** dans `Setting` ; (3) se relit en base à chaque requête
  (= rechargeable **à chaud**).
- **Contrainte d'archi :** `src/` n'importe **jamais** `backend/`. La résolution se fait dans
  le routeur, qui passe la valeur déjà résolue à `generate()`. Le moteur reste pur.

C'est exactement ce gabarit que 4.1.e transpose au fournisseur (`ai_provider`).

---

## 3. État réel du code (terrain CC)

Moteur : `src/generator.py`, `src/config.py`.

- **Point d'entrée unique texte :** `generate(prompt, *, model, max_tokens, temperature, json_mode)`.
  Reste pur (ne lit aucune base) ; `model` lui est passé déjà résolu.
- **Routage fournisseur :** `if AI_PROVIDER == …`, lit la constante module `AI_PROVIDER`,
  figée au boot depuis le `.env` (`src/generator.py:23-30`).
- **3 adaptateurs :**
  - `_groq` — température OK, JSON via `response_format`.
  - `_anthropic` — température **ignorée volontairement**, JSON par instruction système, timeout 60 s.
  - `_gemini` — **dormant**, complet. (Voir §5 : c'est un fournisseur comme un autre, hors périmètre 4.1.e.)
- **Périmètre Groq exclusif (légitime, pas du code mort) :**
  - `backend/groq_client.py` ne sert plus qu'à `transcribe_audio` (Whisper), via `backend/routers/transcribe.py:20`.
  - OCR image (`transcribe_image`, modèle vision Groq en dur) dans `src/generator.py:101`.

---

## 4. Administrable / pas administrable (aujourd'hui)

| Réglage (UI admin) | Relié à `Setting` ? | Le moteur lit-il la base ? |
|---|---|---|
| Email de bienvenue (objet/corps) | ✅ oui (`PUT /admin/settings`) | s'applique à l'envoi |
| **Modèle** (`ai_model`) | ✅ oui (`PUT /admin/ai-model`) | ✅ oui — `get_ai_model(db)`, 6 routeurs câblés |
| **max_tokens** (par outil) | ✅ oui (`PUT /admin/max-tokens`) | ✅ oui — `get_max_tokens(db, outil)` |
| **Fournisseur** (`ai_provider`) | ✅ oui — clé `ai_provider` en base (`SETTING_DEFAULTS` + `get_ai_provider(db)`) ; **écriture admin (combo) = e.4** | ✅ oui — 6 routeurs passent `provider=get_ai_provider(db)`, lu **à chaud** (e.3 fait) |
| **Clé API** (`AI_API_KEY`) | ❌ non (et **doit** rester ❌ : c'est un secret) | ❌ non — `.env`, une seule clé |

→ **e.3 fait (22/06)** : le fournisseur est désormais **lu en base à chaud** (les deux ❌ fermés, comportement inchangé = Groq). Reste l'**écriture admin** (combo UI = e.4) — la clé API demeure un sujet séparé, hors base.

---

## 5. Périmètre 4.1.e — Groq et Anthropic

Les deux IA cibles : **Groq** et **Anthropic**. **Anthropic n'entre dans la combo que
lorsque sa clé (e.1) et un modèle Claude (e.2) sont provisionnés** — sinon la combo n'expose
que les fournisseurs réellement opérationnels (Groq aujourd'hui). On n'offre jamais un
fournisseur sélectionnable qui échouerait à la génération (règle joignabilité).

**Gemini, réglé une fois pour toutes :** c'est un fournisseur comme un autre, sans statut
particulier. Il n'est ni à part, ni « à clarifier ». S'il revient un jour, il sera traité
comme n'importe quel autre fournisseur. Hors périmètre 4.1.e.

---

## 6. Les deux points durs de 4.1.e (à trancher — décisions HARKETTI)

Conditions d'une bascule réellement vivante. Non nommés dans le tracker réforme, sortis
renforcés par l'audit.

1. **Clé API par fournisseur.** Une seule `AI_API_KEY` = clé Groq. Basculer vers Anthropic
   enverrait la clé Groq à Anthropic → échec auth. « Basculer sans toucher au `.env` » exige
   une clé par fournisseur. **La règle §1 tranche le cadre :** la clé reste un **secret**
   (hors base), donc la solution se cherche côté `.env`/secrets, pas en base. Le *comment*
   reste à proposer par CC.
2. **Couplage modèle↔fournisseur.** `SUPPORTED_AI_MODELS` = Groq seul. Provider Anthropic +
   modèle Groq = état incohérent (Anthropic reçoit un nom de modèle Groq → 400).

**Ordre 4.1.d / 4.1.e :** non figé. Le point « température ignorée chez Anthropic » touche
les deux. Décision HARKETTI.

---

## 7. Dettes rendues explicites par la règle §1 (visibles, à ne pas oublier)

Tant qu'aSchool est en DEV, on est dans les clous (interdit seulement *en prod*). Mais ces
valeurs en dur, non-secrètes, sont en dette par rapport à « tout en base » :

- **Modèles Whisper (`whisper-large-v3`) et OCR vision (`generator.py:101`)** : en dur, hors
  `AI_MODEL`, donc hors base. À rapatrier un jour (timing : YAGNI, mais dette tracée ici).
- **`SUPPORTED_AI_MODELS`** : liste de référence en dur. La règle §1 reclasse l'étape 2 de
  sa trajectoire (liste en code → **liste en base** → liste depuis l'API fournisseur) de
  « évolution possible » à **due à terme**.

---

## 8. Cap — épic #45 « Multi-fournisseurs IA »

Item réservoir #45 (`TABLEAU-DE-BORD.md`), 3 niveaux :
**failover** (principal + secours, bascule auto) → **tableau de bord fournisseurs**
(comparer perf/coût/fiabilité) → **routage auto** (vers le meilleur du moment).
Prérequis dur écrit noir sur blanc : « rendre le fournisseur administrable d'abord » = **4.1.e**.
Lien Phase 5 : codes d'erreur 503/429/500 distincts = prérequis de la détection de panne.
Voisin : item #39 / D28 — tester Claude Sonnet 4.6 sur les séquences (~3 $/Mtok).

---

## 9. Chronologie d'avancement 4.1.e (pilotage — CC propose le « comment »)

Étapes ordonnées par dépendance, avec preuve attendue. **L'ordre, les dépendances et les
preuves sont du pilotage ; la solution technique de chaque étape, c'est CC qui la propose.**
Une étape = un échange. Rien n'est codé tant que le GO explicite n'est pas donné.

| # | Sous-objectif | Dépend de | Preuve attendue |
|---|---|---|---|
| **e.0** | **Constat fin** : CC lit le code réel, montre la chaîne `.env → config → generate`, confirme le périmètre exact | — | Constat seul, zéro plan, zéro code |
| **e.1** | **Trancher la clé API** (point dur n°1) — cadre §1 : la clé est un secret, reste hors base | e.0 | Décision HARKETTI actée dans ce tracker |
| **e.2** | **Trancher la cohérence modèle↔fournisseur** (point dur n°2) — éviter « provider Anthropic + modèle Groq » | e.0 | Décision HARKETTI actée |
| **e.3** | **Résolveur fournisseur boot → runtime** : `ai_provider` en base, lu par appel (moule §2, `get_ai_provider(db)`) | e.1, e.2 | **`test_settings_provider.py`** dédié (moule de `test_settings_model.py`) : repli `.env`, lecture base, à chaud (valeur changée entre 2 appels, même process), chaîne via un routeur + suite verte |
| **e.4** | **UI admin** : combo fermée **Groq / Anthropic**, sauvegarde via PUT + **Aide admin « Génération LLM › Fournisseur » rédigée même session** (règle Aide à chaud — l'oubli de 4.1.c ne se répète pas) | e.3 | Geste réel (toi) : changer le fournisseur depuis l'écran, sans éditer le `.env` ni redémarrer ; Aide visible et juste |
| **e.5** | **Clôture** : staging sélectif montré, message FR sans accents, push sur GO PUSH | e.4 | Liste stagée validée avant commit |

> Circuit : idée → CC propose son plan → tu décides → le chat ne réagit qu'au concret
> (erreur ou risque réel), ne dicte pas le « où/comment ».

> **Décision EN ATTENTE — taille de la livraison (tranchée en e.1/e.2, NON pré-jugée ici).**
> Deux options ouvertes, aucune choisie :
> - **light** — on livre le mécanisme avec **Groq seul** sélectionnable aujourd'hui ; Anthropic
>   activable quand HARKETTI fournira sa clé (e.1) + un modèle Claude (e.2).
> - **complete** — provider en base + clé Anthropic + modèle Claude + combo + Aide + tests,
>   pour une **bascule prouvable tout de suite**.
> Le choix dépend de e.1 (clé) et e.2 (modèle Claude) ; il se prend à ce moment-là. Dans les
> deux cas, la combo n'affiche que les fournisseurs opérationnels (§5, correction 1).

---

## 10. Historique des inflexions (terrain CC)

| Date | Commit | Événement |
|---|---|---|
| 16/04 | `9e99113` | 3 adaptateurs présents dès le commit initial, défaut **Gemini** |
| 14/05 | `af31f6c` | Défaut Gemini → **Groq** |
| 18/05 | `c9ef030` | Chaîne de repli Groq (`FALLBACK_CHAIN`) + infra RAG |
| 20/06 | (audit) | Constat : `generate()` propre mais **contourné** (4 routeurs appelaient `call_groq()` en direct) |
| 21/06 | `aa79351` | Tâche 2 : tout réunifié via `generate()`, `call_groq`/`FALLBACK_CHAIN` supprimés |
| 22/06 | `5a4e26e→862d9ec` | 4.1.a/b/c : modèle puis max_tokens administrables à chaud |
| 22/06 | `ef384cf` | Gemini clarifié : dormant, plus banni ; Groq défaut ; Anthropic cible |

Capacité multi-fournisseurs **native depuis avril** ; pilotage propre (point d'entrée unique
puis réglages en base) seulement en juin avec la réforme moteur.

---

## 11. Incohérences à corriger (docs CC — hors périmètre chat)

Relevées par l'audit, à traiter côté CC/docs (le chat les signale, ne les modifie pas) :

- `D28.md:12` et `TABLEAU #39` **périmés** : « tout passe par Groq via `backend/groq_client.py` »
  + proposition d'un `anthropic_client.py` parallèle. Faux depuis la Tâche 2 (21/06) — la
  génération texte passe par `generate()`, l'adaptateur Anthropic existe déjà.
- Tracker : `config.py:6` / `generator.py:23-30` écrits sans le préfixe `src/`. Numéros justes,
  chemin à corriger pour la rigueur.
