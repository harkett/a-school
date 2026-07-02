# aSchool — TRACKER

## ON EN EST LÀ
- 🔄 **En cours :** remise en cohérence des docs de pilotage ([CHANTIER_COHERENCE.md](CHANTIER_COHERENCE.md), éphémère) — §3 TABLEAU fait (commit `1dd6cc7`), §4 TRACKER en cours.
- ✅ **Remplissage + nettoyage table `matieres` — cycles 1 à 6 FAITS (02/07) :** Crèche, École Maternelle, École Élémentaire, Collège, Lycée, Licence. Base dev **saine : 71 matières / 172 liens** (après nettoyage). Modèle `variante` en place (migration `e1f2a3b4c5d6`, index unique `(matiere_id, niveau_id, variante)`) ; langue A/B portée en `variante` sur la paire (8 couples A/B sur 3e/Seconde/Première/Terminale, une seule matière canonique « Langue vivante »). **Nettoyage (02/07, sauvegarde pg_dump avant, transaction réversible) :** fusion des doublons legacy/apostrophe — `Arts`→`Arts plastiques`, `Langues Vivantes (LV)`→`Langue vivante`, apostrophe courbe→droite (`Hygiène…`) ; suppression des `''` redondants avec une variante. Prouvé par requêtes SQL directes : 0 apostrophe courbe, 0 legacy, 0 orphelin, 0 doublon `(matiere,niveau,variante)`, seul (niveau,matière) en double = `Langue vivante` A/B. Injection **idempotente**. Source = `MesMD/aSchool_matiere.md`. **Restent (chantier SÉPARÉ, non fait) :** cycles 7-10 (Master / BTS / BUT / Doctorat) à réécrire en **niveau = spécialité** (en base ces niveaux sont des spécialités, pas des années) + cycle « 0-3 ans » (doublon de la Crèche, à retirer). *NB : `Histoire / Géographie` (Élémentaire) vs `Histoire-Géographie` (Collège) vs `Histoire-Géo` (Lycée) = libellés voulus par cycle, jamais au même niveau — laissés tels quels.*
- 🧹 **Parenthèse ménage (30/06) :** cailloux 1·2·3·4·7 faits — restent **5** (matières en dur depuis le référentiel ; ⚠️ `seed_programmes.py` désaligné, à traiter en premier) et **6** (état réel des vecteurs en base, PostgreSQL à allumer).
- ⏳ **En attente de :** rien.
- ⏭️ **Prochaine :** à arbitrer (l'ordre t'appartient) — reprendre la refonte pro du back-office + procédure CIEL, et/ou la suite de la réforme (Phase 4 administrable, Phases 5-6). Horizon 1 **clos** (restent P4.8/P4.9 cosmétiques, différés).
- ✅ **Dernière chose réellement finie :** **réforme moteur LLM + RAG** (Phases 0→3, base CIEL définitive 236 chunks) + **Phase 4 administrable** 4.1.a/b/c + **chantier fournisseurs** e.0→e.4 (suspendu) — **tout poussé**. Détail → [TRACKER_REFORME.md](TRACKER_REFORME.md) / [TRACKER_FOURNISSEURS_IA.md](TRACKER_FOURNISSEURS_IA.md). Puis §3 du chantier cohérence.
- 🗑️ **Décision 14/06 :** régression « matière vide » (8 activités à matière nulle — 4e×6, 2nde×1, 6e×1 — non rouvrables via Reprendre) = **ignorée volontairement** (vieilles activités de test = déchet). Aucun code.

---

> **Vue de pilotage de l'utilisateur** : la liste COMPLÈTE de tout ce qui reste à faire, ordonnée.
> Le détail (score, description, synergies, audits, RAG, journal FAIT) vit dans [TABLEAU-DE-BORD.md](TABLEAU-DE-BORD.md).
>
> **Règle de tenue :** Statut / ordre / dépendance → ce TRACKER fait foi. Détail / score / journal FAIT → le TABLEAU fait foi.
> Le statut est mis à jour ICI, dans la même réponse où l'on démarre ou finit une tâche.
> **Méthode « tracker vivant » : détail → Annexe A12.**

### Le cycle de vie d'une idée (du berceau au rangement)

Une idée **naît dans la discussion** et se travaille dans un **tracker éphémère**
(son berceau) : on l'ancre, on la pèse, on la mûrit tranquillement. **Tant qu'elle
est une idée, elle reste dans l'éphémère — elle ne touche rien d'autre** (ni ce
TRACKER, ni le tableau de bord, ni une fiche).

Quand elle est **mûre et que tu la valides**, elle n'est plus une idée : c'est un
**travail**. Là seulement elle s'éclate dans les documents permanents :
- **TRACKER** → une ligne simple et humaine, le jour où on décide de la faire
  (ce que tu suis).
- **Fiche Dxx (BOUSSOLE)** → tout son détail technique.
- **Tableau de bord** → elle apparaît dans l'inventaire des travaux, avec un lien
  vers sa fiche.

Si ce qu'on a tranché est une **règle durable** (pas une tâche) → elle va dans
`CLAUDE.md`, jamais dans un tracker.

Puis le tracker éphémère, une fois vidé de cette idée, **finit à la poubelle**
(historique git).

**Statut :** ☐ à faire · 🔄 en cours · ⏸️ en pause / différé · ✅ fait

**Colonne vertébrale de l'ordre — état au 24/06 :** la consolidation du cœur (D16) est **close** et le **gel des features est levé** (réforme moteur LLM + RAG et chantier fournisseurs menés **ET poussés** depuis). Restent en parallèle, ordre à l'envie sauf dépendances :
**(a)** reprise produit (back-office, CIEL) · **(b)** suite de la réforme (Phase 4 administrable, Phases 5-6 dette/cosmétique → [TRACKER_REFORME.md](TRACKER_REFORME.md)) · **(c)** chaînes de features (Horizon 3 ci-dessous).
Entre chaînes de features : pas d'ordre technique → tu piques selon l'envie. **Dans** chaque chaîne : l'ordre est imposé.

---

## 🚫 PRÉREQUIS DÉPLOIEMENT — à faire AVANT tout `deploy.ps1`

> Migration `user_email → user_id` : **bascule de structure FAITE ✅** — la base PostgreSQL et la baseline Alembic (`c9ffe00af0fd_baseline_schema_postgresql.py`) sont nées directement sur `user_id` (les 10 tables filles ont `user_id`, aucune n'a plus `user_email`) ; code aligné (`deps.py:9` n'en garde que le nom du chantier, en commentaire). L'ancien mécanisme SQLite — runner maison `run_migrations.py` + fichiers `.sql` — est **abandonné** : dossier `migrations/` supprimé le 29/06 (résidu SQLite).

| St | Tâche | Détail |
|---|---|---|
| ☐ | **Transfert des données de prod vers le schéma `user_id`** — relève désormais du **Pas 13** (bascule prod SQLite → PostgreSQL, cf. `MesMD/AUDIT-EN-BASE-VS-EN-DUR.md`), **plus** du vieux runner. Garde-fou maintenu pour ce pas : **backup de la base + COUNT orphelins rédhibitoire (no-go si > 0)** avant la bascule. | besoin de fond conservé, déplacé → Pas 13 |

> **Règle dure : aucun `deploy.ps1` / déploiement prod tant que le transfert des données prod (Pas 13) n'est pas fait ET prouvé.**

---

## 🧩 Refonte programmes (modèle relationnel niveaux/matières) — modèle + seed construits (en code) ; restent backfill + historique

> Modèle **validé 11/06** (5 tables, FK vers `user_id`). **En code** : les 5 tables (`models_db.py:244-293`) + seed complet & arbitré (`seed_programmes.py`). *(Exécution sur la base = non vérifiée ici.)* Restent Réserve 2 (backfill) + Réserve 3. Contexte complet → **A2**.

| St | Tâche | Dépendance / réserve |
|---|---|---|
| ✅ | Modèle relationnel validé (5 tables, cardinalités, contraintes `unique`/PK composite) | en code : `models_db.py:244-293` |
| ✅ | **Construire les tables** (modèles + migration expand) | fait : `models_db.py:244-293` (create_all `main.py:39`) |
| ✅ | **Réserve 1 — SEED de `matiere_niveaux`** | fait & arbitré : `seed_programmes.py` (3 pièges résolus) — détail → **A3** |
| ☐ | **Réserve 2 — BACKFILL `users.subject`/`niveau` → `user_enseignements`** | détail → **A4** |
| ☐ | **Réserve 3 — Accès à l'historique en multi-cycles** | détail → **A5** |
| ☐ | **Extraire les matières des BTS depuis leur référentiel** *(tâche séparée — ne bloque PAS le socle matières)* : les « niveaux » BTS sont des **spécialités** ; leurs matières s'extraient du référentiel de chaque spécialité (prouvé sur **BTS CIEL Option A** = ses 9 matières), jamais saisies à la main. Problème récurrent (d'autres référentiels le reposeront). | détail → **A7** |

> 📂 **Notes de fond rattachées (détail en annexe) :** Échelle → **A6** · Procédure « référentiel officiel → matières » (CAS-TEST BTS CIEL) → **A7** · Catalogue d'activités CIEL repli (A) → catalogue dédié (B) → **A8**.

---

## ⚙️ Réforme moteur LLM + RAG — menée et poussée (Phases 0→3 ✅, Phase 4 en cours)

> Chantier majeur de juin : rendre le moteur **LLM-agnostique** + refondre le **RAG** (moteur générique + une fiche par référentiel). Mené **et poussé**. **Pilotage fin (jetable) → [TRACKER_REFORME.md](TRACKER_REFORME.md).** Résumé :

| Phase | Objet | État |
|---|---|---|
| 0 | Audit (6 blocs) | ✅ |
| 1 | Nettoyage moteur LLM (tout via `generate()`, gate maths retirée, Groq texte mort supprimé) | ✅ |
| 2 | Refonte RAG (moteur générique + fiche CIEL) | ✅ |
| 3 | Qualité du différenciateur (overlap · dédup · seuil de score · métadonnées) — base CIEL définitive **236 chunks** | ✅ |
| 4 | Administrable (réglages LLM en base) | 🔄 4.1.a/b/c ✅ · 4.1.d ☐ · 4.1.e ⏸️ |
| 5 | Robustesse / dette | ☐ |
| 6 | Cosmétique / différé (P4.8/P4.9 aussi ici) | ☐ |

> **Fournisseurs IA (4.1.e + épic réservoir #45) :** chantier **suspendu** après e.4 → [TRACKER_FOURNISSEURS_IA.md](TRACKER_FOURNISSEURS_IA.md).

---

## HORIZON 1 — ✅ CLOS : consolidation du cœur terminée

| # | St | Tâche | Dépend de | Pourquoi ici | Fiche |
|---|---|---|---|---|---|
| 1 | ✅ | **P3.6** — protéger contre `KeyError` quand `nb`/`sous_type` manque | rien (filet de tests vert) | technique : ordre audit #1 restant, prérequis réouverture push | [D16](BOUSSOLE/D16.md) |
| 2 | ✅ | **P5.11 — réglé (sans objet)** : « Supérieur » est un *cycle* (en-tête du menu), pas un niveau sélectionnable → aucun bouton ni menu à corriger. Le flag `traite` ne montre que des niveaux supportés. | — | confusion cycle/niveau (audit 15/05) | [D16](BOUSSOLE/D16.md) |
| 3 | ✅ | **P3.5** — sur 401, renouvellement silencieux puis redirection `/login` si refresh token mort (single-flight partagé apiFetch ↔ AuthContext) | après P3.6 | technique : le + sensible ; flux refresh relu (pas de boucle) | [D16](BOUSSOLE/D16.md) |
| 4 | ✅ | **P4.7** — compteur few-shot `localStorage` → backend (table `few_shot_milestones`, jalon une fois) + toast → **modale** (lien Aide) | rien dur | technique : **socle de l'item 40** (badge) ; refactor d'état | [D16](BOUSSOLE/D16.md) |
| 5 | ✅ | **P5.10** — listes MATIERES en dur supprimées : champ `categorie` sur cycles + endpoint `/api/matieres` + hook `useMatieres` ; 8 écrans + phrase Aide lisent la base (source unique). Relève de la refonte « modèle matières propre » | rien | technique : supprime la duplication — **8 copies, pas 3** | [D16](BOUSSOLE/D16.md) |
| 6 | ⏸️ | **P4.8 / P4.9** — carte Activité btn-primary · toast reset params | — | cosmétique : **différés**, en fin de bloc | [D16](BOUSSOLE/D16.md) |

> 🎯 **Jalon atteint : push rouvert, gel levé** (réforme + fournisseurs menés et poussés depuis).

---

## HORIZON 2 — dette technique / outillage (hors features)

| # | St | Tâche | Pourquoi ici |
|---|---|---|---|
| 7 | ☐ | **[Infra] Filet de test front (Vitest + Testing Library)** | complément front du filet backend D16 — le front n'a aucun test |
| 8 | ☐ | **[Process] Tests à 3 étages + [Outillage] journal de versions** | grave qui teste quoi / quand + traçabilité feedback prof ↔ version |
| 9 | ☐ | **[Mémoire] Nettoyer les memory files périmés** (refs BACKLOG / BOUSSOLE / LEVIERS) | cohérence — la dette laissée volontairement lors de la création du TRACKER |
| 10 | ☐ | **[UX/Aide] Rubrique « Exemple » dans tous les « Comment ça marche »** | transverse, tous les outils |
| 11 | ☐ | **[Refactor] Migration React Query (TanStack)** | session dédiée, ne pas mélanger |
| 12 | ☐ | **[Maintenance] Dette technique transverse** (2 sessions) | deps obsolètes, gestion d'erreurs API, sécurité des routes |
| 13 | ☐ | **[Dette] Étendre `apiFetch` aux composants prof restants** — Notation, Mes stats, Mon réseau, Mes séquences, Feedback | reste de P3.5 (option b) : golden path couvert, ces écrans secondaires non migrés → leurs 401 n'aboutissent pas encore à une sortie propre |
| 14 | ☐ | **[Idée] Détection de session expirée SANS clic** — étendre le heartbeat existant pour rediriger dès la session morte | item séparé hors H1, à étudier : aujourd'hui la sortie propre n'a lieu qu'au prochain appel prof |

---

## HORIZON 3 — features (gel levé, librement attaquables)

> Chaînes **parallèles** : entre chaînes, pas d'ordre technique → pique selon l'envie. **Dans** chaque chaîne, l'ordre du haut vers le bas est imposé.

### Quick wins libres (aucune dépendance — à faire avant les chaînes lourdes)

| St | Tâche | Effort | Fiche |
|---|---|---|---|
| ☐ | **11** — Fiche de révision Français + Fiche pédagogique HG | 30 min | [D45](BOUSSOLE/D45.md) |
| ☐ | **06** — Civilité M./Mme dans le profil | 2h | [D30](BOUSSOLE/D30.md) |
| ☐ | **05** — Page /contact | 2h | [D29](BOUSSOLE/D29.md) |
| ☐ | **02** — Email admin → prof (3 templates) | 2h | [D42](BOUSSOLE/D42.md) |
| ☐ | **19** — Admin : menu Activités en groupe | 2h | [D44](BOUSSOLE/D44.md) |
| ☐ | **10** — Timeouts sessions | 2h | [D31](BOUSSOLE/D31.md) |
| ☐ | **27** — Validation texte source par LLM (Option B) | 2h | [D38](BOUSSOLE/D38.md) |
| ☐ | **28** — Stratégie de remédiation (absorbé L2) | 0,5 session | [D17](BOUSSOLE/D17.md) |
| ☐ | **08** — Analyse des notations Groq | 1 jour | [D43](BOUSSOLE/D43.md) |

### Chaîne Séquences (ordre imposé)

| Ordre | St | Tâche | Dépend de | Fiche |
|---|---|---|---|---|
| 1 | ⏸️ | **37** — Affinage interactif de séquence (câbler la route) | code dormant, parké | [D07](BOUSSOLE/D07.md) |
| 2 | ☐ | **38** — Sortie séquence en JSON structuré | après 37 | [D27](BOUSSOLE/D27.md) |
| 3 | ☐ | **39** — Tester Claude Sonnet 4.6 sur les séquences (~3 $/Mtok). ⚠️ Prémisse D28 périmée : génération déjà via `generate()` + adaptateur Anthropic existant → pas de `anthropic_client.py` à créer (switch fournisseur = 4.1.e) | après 38 | [D28](BOUSSOLE/D28.md) |
| 4 | ☐ | **35** — Versioning & transposition de séquences | prérequis D07 (37) | [D26](BOUSSOLE/D26.md) |
| 5 | ☐ | **D13** — PROD Séquences 100% fonctionnel (umbrella) | attend D07 clôturé | [D13](BOUSSOLE/D13.md) |

### Chaîne RAG (ordre imposé)

| Ordre | St | Tâche | Dépend de | Fiche |
|---|---|---|---|---|
| 1 | 🔄 | **INFRA-RAG** — moteur **pgvector** en place ; reste le branchement des consommateurs | hébergement résolu (vecteurs en base PostgreSQL) | [INFRA-RAG](RAG/INFRA-RAG.md) |
| 3 | ☐ | **04** — Détecteur d'équité (consommateur RAG) | attend INFRA-RAG | [D17](BOUSSOLE/D17.md) |
| 3 | ☐ | **30** — Différenciation DYS / FLE (consommateur RAG) | attend INFRA-RAG | [D23](BOUSSOLE/D23.md) |
| 3 | ☐ | **25** — Cohérence curriculaire (consommateur RAG) | attend INFRA-RAG | [D25](BOUSSOLE/D25.md) |
| 3 | ☐ | **31** — Appréciations bulletins & parents (consommateur RAG) | attend INFRA-RAG | [D19](BOUSSOLE/D19.md) |

> 🗃️ **Notes de fond chaîne RAG (détail en annexe) :** nœud binaire-en-git vs rebuild-au-déploiement → **A9** · Chantier B (référentiel = colonne vertébrale du RAG) → **A10**.

### Chaîne Visuels (ordre imposé)

| Ordre | St | Tâche | Dépend de | Fiche |
|---|---|---|---|---|
| 1 | ☐ | **32** — Visuels Mermaid / SVG (moteur) | rien | [D20](BOUSSOLE/D20.md) |
| 2 | ☐ | **33** — Mémo flash (format révision rapide) | après 32 | [D21](BOUSSOLE/D21.md) |
| 2 | ☐ | **34** — Supports de créativité élève | après 32 (+ grounding RAG créativité) | [D22](BOUSSOLE/D22.md) |

### Autres features (dépendance ponctuelle, sinon libres)

| St | Tâche | Dépend de | Fiche |
|---|---|---|---|
| ☐ | **40** — Badge « aSchool vous reconnaît » près du nom | après P4.7 (socle d'état) | — |
| ☐ | **26** — Pipeline qualité automatique | après 04 (besoin L2+03+04) | [D17](BOUSSOLE/D17.md) |
| ☐ | **14** — Bouton « Partagez avec vos collègues » | rien | [D41](BOUSSOLE/D41.md) |
| ☐ | **07** — Onboarding email J+2 / J+7 / J+14 | rien (APScheduler en place) | [D40](BOUSSOLE/D40.md) |
| ☐ | **29** — Mode expérience prof (T1 / confirmé / expert) | rien | [D18](BOUSSOLE/D18.md) |
| ☐ | **18** — Aide spécifique par matière | rien | [D35](BOUSSOLE/D35.md) |
| ☐ | **42** — Recherche globale dans l'application | rien (réf. ergo item 41) | — |
| ☐ | **15** — Gestion emails sortants (backoffice) | prérequis SMTP transactionnel | [D46](BOUSSOLE/D46.md) |
| ☐ | **01** — Pages légales CNIL | en attente — infos admin (externe) | [D39](BOUSSOLE/D39.md) |

### Gros chantiers (semaines)

| St | Tâche | Dépend de | Fiche |
|---|---|---|---|
| ☐ | **17** — Quiz interactif élèves | rien (archi propre) | [D34](BOUSSOLE/D34.md) |
| ☐ | **23** — Escape Game pédagogique | rien | [D37](BOUSSOLE/D37.md) |
| ☐ | **24** — Google OAuth | rien | [D32](BOUSSOLE/D32.md) |
| ☐ | **22** — Théâtre — 13e matière | attend un prof pilote théâtre | [D47](BOUSSOLE/D47.md) |
| ☐ | **D12** — PROD Activité 100% fonctionnel (umbrella « tous angles ») | — (à éclater le jour venu) | [D12](BOUSSOLE/D12.md) |

---

## HORIZON 4 — PLUS TARD / CONDITIONNEL

| St | Tâche | Note | Fiche |
|---|---|---|---|
| ☐ | **21** — Support niveau Supérieur (BTS/prépa/licence) | segment nouveau, « si ça accroche » | [D36](BOUSSOLE/D36.md) |
| ☐ | **43** — Module Petite Enfance 0-3 ans | futur stratégique, garde-fou IA dur | [D48](BOUSSOLE/D48.md) |
| ☐ | **51** — Moteur de granularisation des notions (12 briques) | futur / socle stratégique — spec prête (D49) ; dispatch en cours (brique 1/12) | [D49](BOUSSOLE/D49.md) |
| ✗ | **20** — Projet demo-perf FastAPI + PostgreSQL | hors-périmètre aSchool (projet séparé) | — |

> 🅿️ **Parking & hors-scope (détail en annexe) :** liste « NON RETENU » + liste « HORS SCOPE » → **A11**.

---

## Transverse / récurrent (hors ordre)

| St | Tâche | Quand |
|---|---|---|
| ⟳ | **12** — Synchronisation pages afia.fr (School.jsx) | automatique au prochain push **MINOR / MAJOR** |
| ✅ | **41** — Recherche dans la page Aide (plein-texte) | **fait en local (non déployé)** — part au prochain déploiement |

---

> **Pour ajuster :** à chaque tâche finie, l'utilisateur demande une relecture ; Claude vérifie l'état réel du projet et met à jour ordre / dépendances / tâches avant de continuer.

---
---

## ANNEXE — NOTES DE FOND

> Tout le détail déménagé hors de la vue de pilotage, **intact**. Référencé depuis le milieu par « → Ax ».

### A1 — Prérequis déploiement : pourquoi impératif + preuve exigée
*(détail de la ligne « Intégration prod de la migration `user_email → user_id` »)*
- **Pourquoi impératif :** le nouveau code n'écrit plus `user_email` ; sans migration jouée sur la prod, le schéma prod reste `user_email NOT NULL` → **crash certain au premier insert** (connexion, sauvegarde…).
- **Preuve exigée (pas de parole) :** montrer le `deploy.sh` qui **appelle réellement** le runner + le garde-fou orphelins qui **refuse pour de vrai**. Pas d'assurance verbale.

### A2 — Refonte programmes : contexte du modèle relationnel
Origine du fil : `P5.11` (Supérieur dans le menu) → incohérence de la liste niveaux → besoin d'un vrai référentiel. Remplace les colonnes texte `users.subject` / `users.niveau` par 5 tables : `cycles`, `niveaux`, `matieres`, **`matiere_niveaux`** (programme officiel — l'intégrité référentielle interdit les paires impossibles type « Philo en 6e »), **`user_enseignements`** (ce que le prof couvre, FK vers le programme). Clé vers `users` = `user_id` (acquis de la migration). Modèle **validé 11/06**. **En code** : 5 tables `models_db.py:244-293` + seed `seed_programmes.py` *(exécution base non vérifiée)*.

### A3 — Réserve 1 — SEED de `matiere_niveaux`
D'où viennent les paires matière×niveau ? Carré collège/lycée ; **flou Supérieur** (un BTS n'a pas de programme matière×niveau au même sens) **et Crèche**. Sans paires pour ces cycles, un prof du supérieur n'a rien à choisir. → arbitrage **avant** construction. + les 3 pièges déjà connus (Crèche = tranches d'âge, Supérieur = diplômes, discordance cycles Élémentaire / Formation continue). — ✅ **Résolu** dans `seed_programmes.py` (Crèche = 3 tranches, Supérieur = diplômes/axes, « Primaire » gardé + « Formation continue » en niveau, PROGRAMME défini).

### A4 — Réserve 2 — BACKFILL `users.subject`/`niveau` → `user_enseignements`
expand/contract + **COUNT des orphelins** (chaque `subject`/`niveau` existant doit matcher une paire de `matiere_niveaux`) **AVANT** bascule. Un subject sans paire = à savoir avant, pas pendant. Même discipline que la migration `user_id`.

### A5 — Réserve 3 — Accès à l'historique en multi-cycles
« Mes activités » filtre **dur** sur matière+niveau du profil (`MesActivites.jsx:121-125`, aucune échappatoire) → en multi, un prof 3e+2nde ne verrait jamais la moitié de son travail. **Cible = garantir l'accès à TOUT l'historique** (un « Voir tout », des chips de niveau, ou autre — UI à trancher), pas la mécanique du filtre. Données jamais perdues (tri client). À régler **AVEC** le passage multi (la logique d'affichage change de toute façon), pas en isolé.

### A6 — Échelle (réflexion validée 12/06/2026, pour PLUS TARD)
À ~145 BTS + Masters/Licences/FC, le 1er mur n'est ni la base ni le VPS mais **l'interface admin** (grille matières×niveaux qui s'effondre dès quelques dizaines de niveaux/cycle). Réponse vue prof = **filtrage par `user_enseignements`**, avec 3 pièges (admin à refondre à part · picker cherchable pour la déclaration · 2 endpoints scopé+recherche). Détail complet : TABLEAU § OUTILLAGE/DETTE → **[Archi/Échelle]**.

### A7 — Procédure « référentiel officiel → matières » (CAS-TEST BTS CIEL option A, 12/06/2026)
On met au point sur ce diplôme une méthode **répétable, pas un bricolage** : *référentiel officiel → extraire les matières → les intégrer comme un **niveau** (= le diplôme/option) avec ses **paires** matière×niveau → rendre dispo dans le menu prof via le CRUD*. **Liste validée pour CIEL option A : 9 matières** — 4 générales (Culture générale et expression · Anglais · Mathématiques · Physique) + 5 pro (Informatique · Réseaux · Cybersécurité · Développement · Maintenance). Source = réf. officiel éduscol STI (grille horaire p.81 + blocs de compétences p.29). Une fois la procédure propre sur ce cas → **généralisation** à tous les BTS puis aux autres cycles. Résout concrètement la **Réserve 1 (flou Supérieur)** (A3).

📁 **Règle d'emplacement (12/06/2026) :** tout référentiel **officiel**, **tous cycles confondus**, se range dans **`REFERENTIELS/`** à la racine (un **sous-dossier par référentiel** : PDF d'origine + extraction). C'est la **source de départ** de la procédure. Voir `REFERENTIELS/README.md` (index). État : BTS CIEL option A = PDF présent + 236 chunks ingérés dans `referentiel_chunks` (PostgreSQL/pgvector).

### A8 — Catalogue d'activités CIEL : repli générique (A) → catalogue dédié (B), comme NSI
État au 13/06/2026 : les matières CIEL (Réseaux, Cybersécurité, Dév…) sont **hors** du catalogue d'activités → elles tombent sur un **repli générique provisoire (A)** = **3 types** universels (socle minimal, à élargir) à prompts **neutres** (`gen_*` dans `src/activities.py` + `src/prompts.py`). **A est un DÉPANNAGE, pas la cible.** **B (obligatoire)** = donner aux matières CIEL leurs **propres types taillés** + prompts qui **nomment la matière** (intégration au catalogue façon NSI, via la MATRICE). **Tant que B n'est pas fait, CIEL n'est PAS « traité » côté activités** — ne jamais laisser le générique (A) passer pour du sur-mesure, ni devenir définitif par négligence. Choix des types = décision pédagogique (utilisateur).

### A9 — INFRA-RAG : binaire-en-git vs rebuild-au-déploiement (TRANCHÉ — bascule pgvector, 29/06/2026)
Tranché par la **bascule pgvector** : les vecteurs vivent désormais dans **PostgreSQL** (table `referentiel_chunks`), **jamais en git**, et sont **reconstruits au déploiement** (`python -m backend.rag.pgvector_store`, étape `[2.5/7]` de `deploy.sh`). La question « binaire en git vs rebuild » **disparaît** avec ChromaDB (retiré le 29/06). Source de vérité inchangée : le PDF officiel (`REFERENTIELS/BTS_CIEL_OPTION_A/`).

### A10 — Chantier B — Référentiel = colonne vertébrale du RAG (cadré 13/06/2026 ; H1 clos, briques 1+2 livrées — reste : prouver l'apport RAG sur un couple)
Rendre concret « dériver du référentiel », en deux briques : **(1)** un **script d'ingestion re-jouable** *référentiel → découpe → vecteurs → pgvector AVEC métadonnée `niveau`* — **livré** pour CIEL (`backend/rag/pgvector_store.py` + fiche `bts_ciel_option_a.py`, niveau posé sur **chaque** chunk dès l'ingestion) ; **(2)** un **harnais de tests** qui vérifie que `retrieve_pg()` remonte les bons extraits (`test_rag_ciel.py`) — **livré** (mesure la **qualité du RAG**, **pas** un « entraînement » du LLM — le Llama de Groq reste figé ; on alimente un référentiel, on ne ré-entraîne rien). **Granularité non négociable : un référentiel par couple matière+niveau** — jamais un corpus « cycle en bloc » qui mélange plusieurs programmes. **Reste : prouver l'apport du RAG sur UN couple** (BTS CIEL, une matière, sortie **avec vs sans** RAG) **avant d'élargir**. But structurel : relier les **deux référentiels qui ne se parlent pas** — (a) SQL/menus ↔ (b) pgvector/RAG.

### A11 — Parking & hors-scope
**Parking — NON RETENU** (à reconsidérer) : capture d'écran feedback · `logoutManager.ts` · recrutement profs Facebook/X · trajectoires multi-séances · labo simulation classe · modal multi-actions Oui/Non · tuning latence Deepgram · bug auth WS longues · etc. → détail dans [TABLEAU-DE-BORD.md](TABLEAU-DE-BORD.md) § NON RETENU.
**HORS SCOPE** (refusé) : ENT/Pronote · multi-profs établissement · cartographie cognitive · PPD. → § HORS SCOPE.

### A12 — Méthode « tracker vivant »
Quand le tracker dit « attaque la tâche XX (Dxx) », Claude vérifie d'abord que rien n'a bougé dans le projet (fiche Dxx + code concerné + FAIT) ; si quelque chose a changé, il ajuste le tracker (ordre, dépendances, tâches en +/−) **et montre le delta** AVANT de continuer.


