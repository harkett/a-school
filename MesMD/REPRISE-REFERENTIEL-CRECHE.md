# REPRISE — Procédure d'ajout d'un référentiel (cas crèche 0-3 ans)

> **Notre guide de travail.** Récupéré de la session du 06/07/2026 (23:34).
> C'est le document qu'on rouvre pour reprendre, étape par étape. Consigne de départ de Harketti + résultat de la vérification de cohérence.

---

## 0. Prérequis (à faire avant d'attaquer)

- ✅ Lire **CLAUDE.md**, surtout la section « MÉTHODE RÉFÉRENTIEL (RAG) », dont la règle **« Immuabilité de la structure d'un référentiel — casser et régénérer, jamais migrer »**.
- ✅ Lire la **mémoire projet** — mais ne jamais la croire sur parole : valider contre le code réel avant d'affirmer, signaler toute incohérence pour nettoyer la mémoire au fur et à mesure.
- ✅ **Vérifier la cohérence du dossier** réorganisé (structure par rôle : `backend/`, `frontend/`, `Scripts/`, `REFERENTIELS/`, `MesMD/`, `tests/`, `alembic/`). Signaler toute incohérence ou vestige, **ne rien corriger sans GO**. *(+ ménage résidus locaux fait le 07/07)*

---

## 1. Contexte

- ✅ **1.1** — On reprend **à zéro** la procédure d'ajout d'un référentiel, sur la **crèche** : un référentiel **unique 0-3 ans**, partagé par **3 niveaux** — Bébés (0-1), Moyens (1-2), Grands (2-3). *(Point 1 validé le 07/07 : 2 bandes d'âge `0-1`/`1-3`, 3 collections ; Moyens+Grands partagent `1-3`.)*
- ✅ **1.2** — Nouvelle base miroir **`aschool_creche_miroir`** (minuscules) — **créée et vérifiée le 07/07** : copie fidèle de `aschool` (24 tables, 236 chunks, `matieres`=71, `niveaux`=88, extension `vector` 0.8.3), via dump/restore (restauration par `postgres` pour l'extension pgvector). Ancienne `aschool_miroir` supprimée. On ne cible QUE cette base, jamais la vraie. *(MAJ 07/07 : `.env` **a été repointé** `DATABASE_URL` → `aschool_creche_miroir` — cf. §1.3.)*
- ✅ **1.3 — Nettoyage préalable : suppression de la colonne `traite`** (parenthèse ouverte avant l'étape 1, **fermée le 07/07**). En creusant, on est tombé sur un os : la table `niveaux` portait une colonne `traite` (drapeau true/false « ce niveau a son vrai référentiel »). **Non prévue à l'analyse, ajoutée par Claude Code**, elle viole la doctrine « rien en dur / séparer CODE et DONNÉE » : une **colonne-de-règle** en base, alors que l'info est **dérivable** de `referentiels` (un niveau a son référentiel ⟺ une ligne existe pour lui avec **≥1 chunk ingéré**).
    - **Décision** : supprimer la colonne, **dériver** la valeur à la volée (jamais la stocker). Clé d'affichage renommée `traite` → **`refDisponible`** (un nom qui dit ce qu'il est).
    - **Procédure (miroir d'abord, puis vraie base)** : **A1** miroir monté au head Alembic (rattrapage de 3 migrations email en retard) · **A2** code + migration `DROP COLUMN niveaux.traite` + renommage de la clé (Bloc 1) · **A3** drop appliqué sur le miroir, `aschool` intacte · **A4** endpoint `/programmes` prouvé sain (ne crashe plus sans la colonne, dérivation correcte, `refDisponible=true` atteignable) · **A5** application à la vraie base `aschool` (**fait le 07/07** : vraie base au head Alembic, colonne `traite` supprimée, tables email créées, cycles=11/niveaux=88 intacts ; `.env` remis sur `aschool_creche_miroir`). **→ Parenthèse fermée. On revient à l'étape 1 du §2.**
    - **Bloc 2 — FAIT le 07/07** : fonction `niveauxTraites` → `niveauxRefDisponibles` (6 fichiers front) + commentaires « traité » → « disponible ». Test front `profil.test.js` : 10/10 verts.
    - **Honnêteté (l'écart avec « cosmétique »)** : ce n'était PAS que cosmétique. Le drop de la colonne avait laissé **4 tests backend cassés** — réparés : `test_referentiel_disponible`, `test_rag_ciel`, `test_exemple_referentiel`, `test_endpoints_coeur` (dont un test réécrit pour la valeur dérivée) — et révélé que **`aschool_test` était périmée** (colonne `variante` manquante) → schéma reconstruit. Preuve finale : suite backend **153 passés**.
    - **2 tests rouges PRÉEXISTANTS, HORS `traite` — RÉPARÉS le 08/07/2026** : (a) `test_activites_ciel.py` → l'invariant « une matière du catalogue garde ses clés » est désormais testé sur une matière fictive injectée (le catalogue réel est vide) ; (b) `test_rag_ingest_robuste.py` (×3) réécrit sur l'API actuelle (`get_fiche` + `build_chunks`), agnostique au référentiel. Les deux verts.
    - **Règle qui en ressort** : l'état « ce niveau a-t-il un référentiel » se **calcule** (existence d'une ligne `referentiels` + chunks ingérés), il ne se **stocke jamais** dans une colonne. **Aucune colonne-de-règle en base.**

---

## 2. La procédure générique — 16 étapes (universelle, pas seulement la crèche)

Le squelette des 16 étapes est **universel**. Seul le contenu des **étapes 5 et 6** est spécifique et vit dans la **fiche du référentiel** (`backend/rag/referentiels/creche_0_3_ans.py`). Le socle, lui, ne change jamais.



**Légende :** 🧍 = l'admin agit · ⚙ = automatique

| ✓ | # | Étape | Acteur |
|---|---|---|---|
| ✅ | 1 | Sélectionner le cycle et le niveau | 🧍 |
## Prérequis - 3 Tâches
- ✅ **Prérequis 1 — FAIT le 07/07** : filet de reproductibilité cycles/niveaux reconstruit et committé (`353c89b`).
  - **Vérifié** : le script de remplissage d'origine **n'existe nulle part dans git** — recherche `-S` sur les noms de cycles actuels (« Doctorat », « Lycée professionnel ») = 0 résultat dans les `.py`. C'était un script **éphémère** (créé → utilisé → supprimé, jamais committé, conforme à la doctrine). La crainte « il est probablement dans l'historique git » est donc **fausse**.
  - **Vérifié aussi** : `MesMD/aSchool_matiere.md` n'est **PAS** la source de la base (il porte 35 niveaux, un cycle « 0-3 ans » parasite, pas de « Lycée professionnel ») → inexploitable comme source de reproductibilité. La seule chose qui détenait les vrais 88 niveaux, c'était la **base elle-même**.
  - **Solution livrée** : dossier `outils_bdd/` (nouveau, outils Python de maintenance BDD, hors `backend/` et hors `Scripts/`) contenant `cycles_niveaux.json` (snapshot fidèle, ids figés — source de vérité committée), `rebuild_cycles_niveaux.py` (capture `--export` / rejeu idempotent, insert-si-absent + recalage des séquences) et `README.md`. **Reconstruction d'une base neuve, PAS correction d'une base existante.**
  - **Testé de bout en bout** : `--export` (11/88 écrits) · rejeu sur base pleine (0 inséré, tout sauté) · rejeu sur schéma vide jetable (11+88 insérés, séquences recalées, prochain id sans collision), `public` du miroir intact.
- ✅ **Prérequis 2 — FAIT le 07/07** : inventaire des 11 cycles / 88 niveaux, **vérifié sur la vraie base** (miroir `aschool_creche_miroir`, interrogation directe). L'inventaire **détaillé** (les 88 noms de niveaux + rattachement + ids) est désormais capturé dans **`outils_bdd/cycles_niveaux.json`** (source de vérité committée). Répartition confirmée :

  | Cycle | Niveaux | | Cycle | Niveaux |
  |---|---|---|---|---|
  | École élémentaire | 5 | | Crèche | 3 |
  | Collège | 4 | | BTS | 17 |
  | École maternelle | 3 | | Master | 15 |
  | Lycée | 3 | | BUT | 15 |
  | Licence | 3 | | Doctorat | 15 |
  | Lycée professionnel | 5 | | **Total** | **88** |
- ✅ **Étape 1 franchissable pour la crèche** : le cycle Crèche (id 7) et ses 3 niveaux (Bébés/Moyens/Grands, ids 24-26) existent déjà en base → rien à créer. *(L'ajout/suppression de cycle via un écran admin a été exploré puis abandonné le 07/07 — trop compliqué pour le résultat ; trace en git.)*

*********** FIN - Etape 1 - Sélectionner le cycle et le niveau********


| ✅ | 2 | Déposer le PDF (+ relecture « Voir le référentiel », commit `1923e64`) | 🧍 |
| ✅ | 3 | Enregistrer le PDF (nommé `referentiel.pdf`, vrai nom conservé) | ⚙ |
| ✅ | 4 | Lire le texte du PDF *(⚠ voir bloc Reprise : `extraction-texte.txt` = trace morte)* | ⚙ |
| ✅ | 5 | Découper en unités (1 unité = 1 chunk) | ⚙ (le *comment* vient de la fiche) |
| ✅ | 6 | Rattacher chaque unité à son niveau | ⚙ (le *critère* vient de la fiche) |
| ☐ | 7 | Arbitrer les cas ambigus | 🧍 (la machine signale, l'admin tranche) |
| ☐ | 8 | Filtrer par niveau | ⚙ |
| ☐ | 9 | Vectoriser | ⚙ |
| ☐ | 10 | Ingérer sur la base miroir | ⚙ |
| ☐ | 11 | Calibrer le seuil | ⚙ propose / 🧍 valide |
| ☐ | 12 | Tester (recherche par matière) | ⚙ / 🧍 vérifie |
| ☐ | 13 | Valider le résultat | 🧍 |
| ☐ | 14 | Basculer miroir → base réelle | ⚙, sur GO 🧍 *(vision cible, pas encore construit)* |
| ☐ | 15 | Nettoyer la base miroir | ⚙ *(vision cible, pas encore construit)* |
| ☐ | 16 | Activer le référentiel (visible côté prof) | ⚙ |

---

### Reprise — où on en est (07/07, fin de session)

**Étapes 1 à 4 : validées des deux côtés — rien à coder, machinerie déjà en place.**

- **1 (sélection)** : combos Cycle → Niveau déjà là (`frontend/src/pages/AdminReferentiels.jsx`), alimentés par la vraie base.
- **2 (dépôt)** : chaîne dépôt/lien → aperçu → `valider` déjà en place, et **déjà faite** pour la crèche (3 `referentiel.pdf` + 3 lignes `referentiels`). **Ajout de cette session** : lien « Voir le référentiel » sur la ligne « déjà traité » → fenêtre PDF repliable, via l'endpoint **générique** `GET /admin/referentiels/pdf` (`cycle_id` + `niveau`). Committé + poussé (`1923e64`).
- **3-4 (enregistrer + extraire)** : faites par `valider` (range `referentiel.pdf`, extrait le texte). Testées par l'utilisateur.

**Découverte sur `extraction-texte.txt` (étape 4) — TRACE MORTE.** Écrit par `valider` (`backend/pedagogie/referentiels_admin.py:183`), mais **lu par personne** : la fiche crèche lit le **PDF** (`creche_0_3_ans.extract_pages`). Les 3 extractions crèche ont été **régénérées cohérentes** (~20 Ko, identiques) et **gardées** — aucun impact fonctionnel.

**2 nettoyages différés (pas maintenant) :** (1) arrêter d'écrire le fichier mort `extraction-texte.txt` ; (2) corriger le commentaire trompeur `referentiels_admin.py:177` (« même brique que l'ingestion » — faux, l'ingestion lit le PDF). *(Le 3e nettoyage — retirer la constante `EXTRACTION_TXT` — est sans objet : la fiche BTS a été supprimée le 08/07/2026.)*

**Working-tree crèche non committé** (swap PDF en cours) : les 3 `referentiel.pdf` sont désormais **identiques** (md5 `b12497…`, un seul document 0-3 copié dans les 3 dossiers, conforme à D60 §Dépôt) + les 3 `extraction-texte.txt` identiques (md5 `5a47cd…`). À committer avec le swap quand décidé.

**Étapes 5-6 FAITES (08/07/2026).** Le moteur découpe via la **règle de découpe validée** (motif lu **EN BASE** — `referentiels.regle_motif`, via `charger_regle(ref)` appelé par le socle avant `extract_pages` ; plus de regex en dur ni de fichier ; garde-fou : pas de découpage sans validation) et le **tag d'âge** rattache chaque unité à son niveau — prouvé **18 / 27 / 27** (Bébés / Moyens / Grands). *(MAJ 09/07/2026 — migration « tout en base » #3+#4 : règle de découpe et arbitrage des cas flous versés en colonnes de `referentiels` ; les `regle-decoupe.json` supprimés.)* **Prochaine étape = 7 (arbitrer les cas flous) puis ingestion (8-10) sur le miroir.** L'arbitrage réel du flou reste à construire : aujourd'hui la carte « Résultat du découpage » **signale** « âge à confirmer », mais l'admin ne **tranche** pas encore la tranche d'âge (cf. [D60](BOUSSOLE/D60.md) § Reste à faire).

---

## 3. Méthode de travail (stricte)

- Harketti **guide point par point, ne code pas**.
- Claude : **un seul point à la fois**. Avant chaque geste de code, dire **QUOI** on fait et **DANS QUEL FICHIER** (chemin + ligne), et **montrer le passage exact AVANT de l'écrire**.
- On s'arrête, Harketti valide, on avance. **Rien sans son GO.**
- **Tout sur la nouvelle base miroir, jamais la vraie base.**
- **Rien de committé sans GO.**

---

## 4. Direction déjà validée (à respecter, ne pas re-débattre)

- On travaille avec le **niveau, identifié par son identifiant unique (`niveau_id`)** — c'est lui qu'on passe partout. Le nom en clair se retrouve en base via l'id ; on ne manipule **jamais** le libellé pour décider.
- Le **filtrage par niveau se fait à l'ingestion** : chaque collection ne reçoit que le contenu de son niveau (étape 8).
- La **recherche (`retrieve_pg`) n'est pas touchée** (elle isole déjà par `referentiel_id`).
- Pour le **tri par niveau** UNIQUEMENT (quel contenu → quel niveau) : **aucune colonne** en base — cette logique **structurelle** vit dans le **code de la fiche** (`backend/rag/referentiels/creche_0_3_ans.py`). *(MAJ 09/07/2026 : à ne pas confondre avec « tout en base » — la **règle de découpe**, l'**arbitrage**, le **seuil** et les **matières candidates** sont des **données** et vivent bien **en base**, cf. migrations #1/#3/#4/#5.)*
- **Vocabulaire : on dit « tranche d'âge », jamais « bande ».**
- **Ne pas compliquer.** Solution simple d'abord. Pas de concept intermédiaire inventé.

---

## 5. Vérification de cohérence du dossier — résultat (06/07/2026, sur le réel)

**Structure par rôle : cohérente et vivante.** Le `backend/` est réorganisé en dossiers-métier (`activite/`, `analyse/`, `analytique/`, `communication/`, `contenu/`, `core/`, `dictee/`, `pedagogie/`, `prof/`, `reseau/`, `securite/`, `sequence/`, `supervision/`, `systeme/`). `backend/main.py` importe bien depuis ces nouveaux chemins ; **aucun import ne pointe vers un ancien emplacement** — la bascule est propre.

- `core/` regroupe `database.py`, `models_db.py`, `middleware.py`, `deps.py`, `limiter.py`… — cohérent.
- Auth volontairement à part : `backend/auth.py` + `backend/routers/auth.py` — conforme à « Auth — Ne pas toucher ».
- `src/` à la racine (`prompts.py`, `generator.py`, `config.py`, `activities.py`) est **encore vivant** (importé par `activite/`, `analyse/`, `contenu/`, `core/`) — **pas** un vestige.
- `REFERENTIELS/` (BTS + CRECHE 3 niveaux), `tests/`, `Scripts/`, `alembic/`, `MesMD/` : conformes.

**Vestiges signalés (rien touché sans GO) :**
- ☐ `backend/main.py.bak-2026-06-27` et `backend/main.py.bak-2026-06-27-pas9` — sauvegardes de `main.py`.
- ☐ `backend/seed_bts_ciel.py.bak-2026-06-27` et `backend/seed_programmes.py.bak-2026-06-27` — sauvegardes de scripts **seed** (mot banni ; même en `.bak` ça ne devrait plus traîner).
- ☐ `rag_demo/` — dossier `.venv` à l'intérieur (confirmé le 07/07, pas vide).

Rien de cassé ; résidus à nettoyer, pas des incohérences d'import.

> ⚠️ **À revérifier ce matin** : cet état date du 06/07 au soir. Avant de le tenir pour vrai, le reconfirmer sur le réel (les vestiges ont pu être nettoyés depuis).

---

## 6. Premier geste attendu

Rien coder. Confirmer la lecture de CLAUDE.md + mémoire, redonner le résultat de la vérification de cohérence, redire en 3 lignes ce qu'on fait, **et attendre le premier point de Harketti** (ainsi que le nom de la nouvelle base miroir).
