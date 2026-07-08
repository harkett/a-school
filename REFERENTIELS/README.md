# REFERENTIELS — référentiels officiels (emplacement unique)

**Règle (procédure) :** tout référentiel **officiel**, **quel que soit le cycle** (Crèche → Supérieur), se range **ICI**, dans un **sous-dossier par référentiel**. C'est la source de départ de la procédure « référentiel officiel → matières → niveau + paires » (cf. TRACKER § Refonte programmes).

Pour chaque référentiel, idéalement : le **document officiel d'origine** (PDF), + éventuellement son **extraction texte** (pour recherche).

---

## Index — état au 12/06/2026

| Référentiel | Sous-dossier | État | Contenu réel |
|---|---|---|---|
| **BTS CIEL option A** (Informatique et réseaux) — éduscol STI, rénovation 2023 | *(dossier retiré le 08/07/2026)* | ⏳ à régénérer | Contenu (PDF + 236 chunks) retiré ; **structure cycle/niveau BTS conservée**. À recréer via la procédure standard. |

---

## Cycle de vie d'un référentiel (procédure)

> **Deux moments à ne jamais confondre :**
> - **Construction de la base** (à l'ajout, puis à chaque mise à jour) : on lit le PDF **une seule fois**, on le découpe, on remplit la table `referentiel_chunks` (PostgreSQL/pgvector). Seul moment où le PDF sert.
> - **Usage quotidien** (chaque génération) : on lit **`referentiel_chunks` (pgvector)**, **jamais** le PDF.

### Principes
- **P1 — L'IA propose, l'admin valide.** L'IA cherche le document sur la **source officielle** (éduscol / Bulletin Officiel) et le **propose** ; l'**admin certifie** (c'est bien le bon, en vigueur) et **télécharge**. Le garde-fou humain reste — **déplacé** de « chercher » à « valider la proposition ». (Remplace l'ancienne règle « téléchargement entièrement manuel, pas de robot » — acté 26/06/2026.)
- **P2 — Nom interne fixe, décidé par nous.** Chaque référentiel a un identifiant stable (nom de sous-dossier + nom de collection, ex. `bts_ciel_optionA`). Le **nom volatil de l'EN** — qui change à chaque sortie (« 15324… » → « 32368… ») — **n'entre jamais dans le code**.
- **P3 — Métadonnées en base, pas dans un fichier écrit à la main.** La table PostgreSQL `referentiels` porte **deux choses** : (a) la **provenance** — `nom_fixe` (nom interne stable) · `fichier` (vrai nom du PDF) · `date_doc` · `source`/URL ; (b) le **routage** — le **couple** (`niveau_id` + `matiere_id`, ce dernier **NULL = tout le niveau**) et **où chercher** (`collection` + `filtres` JSON, ex. `{"option":"A"}`). Clé par **id** (FK `niveaux`/`matieres`) pour l'intégrité ; la lecture retrouvera la ligne par **jointure sur les libellés** (`niveaux.nom`). Table définie dans `backend/models_db.py` (schéma géré par Alembic), seedée avec la ligne **BTS CIEL option A** (matiere_id NULL = tout le diplôme). (Donnée administrable — l'écran admin de saisie reste à construire.)

### Procédure complète validée (cible — 26/06/2026)
> Vue d'ensemble côté produit. Le détail technique reste « A — Premier ajout » ci-dessous.
- **Temps 1 — Déclarer le niveau.** L'admin choisit le **cycle** puis le **niveau** dans des combos (liste fermée, jamais de saisie libre — cf. `MesMD/aSchool-cycles-niveaux.md`). aSchool en déduit le **nom de dossier-clé** = le nom du niveau normalisé en **MAJUSCULES_UNDERSCORE** (accents enlevés), ex. `BEBES_0_1_AN/`. Le référentiel couvre **tout le niveau** ; les matières en sont **extraites** ensuite (Temps 3), pas déclarées à la main. Clé **unique et non renommable** ; l'identifiant interne `nom_fixe` en est la version minuscule (`bebes_0_1_an`).
- **Temps 2 — Trouver / valider le document.** L'IA propose le document officiel (cf. P1) ; l'admin certifie et le dépose dans `REFERENTIELS/<dossier>/` + renseigne (vrai nom, date, source).
- **Temps 3 — Intégrer.** aSchool découpe → relie → teste. *(Aujourd'hui manuel/dev. L'étape « relier » porte deux manques connus : routage en dur + cœur `/api/generate` non branché → chantier « automatiser le Temps 3 : routage data-driven + branchement du cœur ».)*
- **Temps 4 — Ouvert.** Couple relié = génère sur le vrai programme ; sans référentiel = « en construction ».
- **Deux preuves distinctes :** « le bon référentiel remonte » (indexation) ≠ « la génération s'appuie dessus » (cœur).

### A — Premier ajout
1. **(Admin)** télécharge le PDF officiel et le dépose dans `REFERENTIELS/<DOSSIER_CLE>/` (nom du niveau normalisé, ex. `BEBES_0_1_AN/`).
2. **(Admin)** renseigne en base (table `referentiels`) : nom interne fixe, vrai nom du fichier, date, source.
3. **(Dev)** écrit la **fiche** (`backend/rag/referentiels/<nomfixe>.py`) : règles de découpe + étiquetage (niveau, option).
4. **(Dev)** lance la construction : `python -m backend.rag.pgvector_store` → chunks insérés dans `referentiel_chunks`, tagués (niveau via jointure, option).
5. **(Dev)** test de raccordement (`retrieve_pg()` remonte du bon référentiel).

### B — Mise à jour (l'EN sort une nouvelle version, avec un nouveau nom)
1. **(Admin)** télécharge le nouveau PDF, **remplace** l'ancien dans le dossier.
2. **(Admin)** met à jour la ligne en base (nouveau vrai nom + date).
3. **(Dev)** relance la construction : idempotente → efface les anciens chunks du référentiel, reconstruit à neuf.
4. **(Dev)** test.
→ Le **nom interne fixe ne change jamais** → rien d'autre à toucher.

### C — Coexistence ancien / nouveau programme
Réglée **par nature** : **un référentiel par couple matière + niveau**, mis à jour indépendamment. Jamais deux versions dans une même collection (c'est le piège « cycle en bloc » supprimé le 23/06).

### Côté admin (à construire)
Page **« Référentiels »**, rangée **près de Programmes** (zone contenu, pas Paramètres) : elle est en **amont** (référentiel → matières → paires). Contient le **champ de téléversement du PDF** + la liste des référentiels + leur statut (indexé / nb de chunks). À l'échelle (300+ référentiels) : **recherche d'abord** (barre de recherche + filtres par famille + pagination), jamais « tout afficher » — même principe que côté profil prof.
