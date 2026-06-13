# aSchool — TRACKER

> **Vue de pilotage de l'utilisateur** : la liste COMPLÈTE de tout ce qui reste à faire, ordonnée.
> Le détail (score, description, synergies, audits, RAG, journal FAIT) vit dans [TABLEAU-DE-BORD.md](TABLEAU-DE-BORD.md).
>
> **Règle de tenue :** Statut / ordre / dépendance → ce TRACKER fait foi. Détail / score / journal FAIT → le TABLEAU fait foi.
> Le statut est mis à jour ICI, dans la même réponse où l'on démarre ou finit une tâche.
>
> **Tracker vivant :** quand le tracker dit « attaque la tâche XX (Dxx) », Claude vérifie d'abord que rien n'a bougé dans le projet (fiche Dxx + code concerné + FAIT) ; si quelque chose a changé, il ajuste le tracker (ordre, dépendances, tâches en +/−) **et montre le delta** AVANT de continuer.

**Statut :** ☐ à faire · 🔄 en cours · ⏸️ en pause / différé · ✅ fait

**Colonne vertébrale de l'ordre :** le **gel des features pendant la consolidation**. Donc :
**1.** finir la consolidation du cœur (D16) → **2.** rouvrir le push → **3.** dette / outillage → **4.** features (par dépendance puis valeur) → **5.** conditionnel.
Entre chaînes de features : pas d'ordre technique → l'utilisateur pique selon l'envie. **Dans** chaque chaîne : l'ordre est imposé.

---

## 🚫 BLOQUANT DÉPLOIEMENT — à faire AVANT tout `deploy.ps1`

> Migration `user_email → user_id` : **dev = ✅ prouvée** (commits expand + contract, comptes préservés, FK posées, `foreign_key_check` vide, pytest 19/19). **Prod = pas encore intégrée.**

| St | Tâche | Pourquoi bloquant | Preuve exigée (pas de parole) |
|---|---|---|---|
| ☐ | **Intégration prod de la migration `user_email → user_id`** — (1) brancher `run_migrations.py` dans `deploy/deploy.sh` (après `git pull`, **avant** le `restart systemd`) ; (2) garde-fou prod : **backup de la base + COUNT orphelins BLOQUANT** (no-go si > 0) **avant** tout DROP | le nouveau code n'écrit plus `user_email` ; sans migration jouée sur la prod, le schéma prod reste `user_email NOT NULL` → **crash certain au premier insert** (connexion, sauvegarde…) | montrer le `deploy.sh` qui **appelle réellement** le runner + le garde-fou orphelins qui **bloque pour de vrai**. Pas d'assurance verbale. |

> **Règle dure : aucun `deploy.ps1` / déploiement prod tant que cette ligne n'est pas faite ET prouvée.**
> Ordre : on ne câble la prod qu'**après** la migration dev prouvée — c'est acquis, mais la ligne reste différée par décision de l'utilisateur.

---

## 🧩 Refonte programmes (modèle relationnel niveaux/matières) — conçu, pas encore construit

> Origine du fil : `P5.11` (Supérieur dans le menu) → incohérence de la liste niveaux → besoin d'un vrai référentiel. Remplace les colonnes texte `users.subject` / `users.niveau` par 5 tables : `cycles`, `niveaux`, `matieres`, **`matiere_niveaux`** (programme officiel — l'intégrité référentielle interdit les paires impossibles type « Philo en 6e »), **`user_enseignements`** (ce que le prof couvre, FK vers le programme). Clé vers `users` = `user_id` (acquis de la migration). Modèle **validé 11/06**, dans `data/aschool.dbml` (section « PROPOSÉ »). **Rien encore en base ni en code.**

| St | Tâche | Dépendance / réserve |
|---|---|---|
| ✅ | Modèle relationnel validé (5 tables, cardinalités, contraintes `unique`/PK composite) | dans le `.dbml` |
| ☐ | **Construire les tables** (modèles + migration expand) | après arbitrage du seed (réserve 1) |
| ☐ | **Réserve 1 — SEED de `matiere_niveaux`** : d'où viennent les paires matière×niveau ? Carré collège/lycée ; **flou Supérieur** (un BTS n'a pas de programme matière×niveau au même sens) **et Crèche**. Sans paires pour ces cycles, un prof du supérieur n'a rien à choisir. → arbitrage **avant** construction | + les 3 pièges déjà connus (Crèche = tranches d'âge, Supérieur = diplômes, discordance cycles Élémentaire / Formation continue) |
| ☐ | **Réserve 2 — BACKFILL `users.subject`/`niveau` → `user_enseignements`** : expand/contract + **COUNT des orphelins** (chaque `subject`/`niveau` existant doit matcher une paire de `matiere_niveaux`) **AVANT** bascule. Un subject sans paire = à savoir avant, pas pendant | même discipline que la migration `user_id` |
| ☐ | **Réserve 3 — Accès à l'historique en multi-cycles** : « Mes activités » filtre **dur** sur matière+niveau du profil (`MesActivites.jsx:121-125`, aucune échappatoire) → en multi, un prof 3e+2nde ne verrait jamais la moitié de son travail. **Cible = garantir l'accès à TOUT l'historique** (un « Voir tout », des chips de niveau, ou autre — UI à trancher), pas la mécanique du filtre. Données jamais perdues (tri client). | **À régler AVEC le passage multi** (la logique d'affichage change de toute façon), pas en isolé |

> 📐 **Échelle (réflexion validée 12/06/2026, pour PLUS TARD) :** à ~145 BTS + Masters/Licences/FC, le 1er mur n'est ni la base ni le VPS mais **l'interface admin** (grille matières×niveaux qui s'effondre dès quelques dizaines de niveaux/cycle). Réponse vue prof = **filtrage par `user_enseignements`**, avec 3 pièges (admin à refondre à part · picker cherchable pour la déclaration · 2 endpoints scopé+recherche). Détail complet : TABLEAU § OUTILLAGE/DETTE → **[Archi/Échelle]**.

> 🧪 **Procédure « référentiel officiel → matières » — en cours de mise au point. CAS-TEST n°1 : BTS CIEL option A (12/06/2026).** On met au point sur ce diplôme une méthode **répétable, pas un bricolage** : *référentiel officiel → extraire les matières → les intégrer comme un **niveau** (= le diplôme/option) avec ses **paires** matière×niveau → rendre dispo dans le menu prof via le CRUD*. **Liste validée pour CIEL option A : 9 matières** — 4 générales (Culture générale et expression · Anglais · Mathématiques · Physique) + 5 pro (Informatique · Réseaux · Cybersécurité · Développement · Maintenance). Source = réf. officiel éduscol STI (grille horaire p.81 + blocs de compétences p.29). Une fois la procédure propre sur ce cas → **généralisation** à tous les BTS puis aux autres cycles. Résout concrètement la **Réserve 1 (flou Supérieur)** ci-dessus.
>
> 📁 **Règle d'emplacement (12/06/2026) :** tout référentiel **officiel**, **tous cycles confondus**, se range dans **`REFERENTIELS/`** à la racine (un **sous-dossier par référentiel** : PDF d'origine + extraction). C'est la **source de départ** de la procédure. Voir `REFERENTIELS/README.md` (index + manques). État : BTS CIEL option A = PDF présent ; Maths cycle 4 = PDF **manquant** (seulement en ChromaDB).

> 🏗️ **À FAIRE — Catalogue d'activités CIEL : passer du repli générique (A) à un vrai catalogue dédié (B), comme NSI.** État au 13/06/2026 : les matières CIEL (Réseaux, Cybersécurité, Dév…) sont **hors** du catalogue d'activités → elles tombent sur un **repli générique provisoire (A)** = **3 types** universels (socle minimal, à élargir) à prompts **neutres** (`gen_*` dans `src/activities.py` + `src/prompts.py`). **A est un DÉPANNAGE, pas la cible.** **B (obligatoire)** = donner aux matières CIEL leurs **propres types taillés** + prompts qui **nomment la matière** (intégration au catalogue façon NSI, via la MATRICE). **Tant que B n'est pas fait, CIEL n'est PAS « traité » côté activités** — ne jamais laisser le générique (A) passer pour du sur-mesure, ni devenir définitif par négligence. Choix des types = décision pédagogique (utilisateur).

---

## HORIZON 1 — MAINTENANT : finir la consolidation du cœur (seul chantier ouvert)

| # | St | Tâche | Dépend de | Pourquoi ici | Fiche |
|---|---|---|---|---|---|
| 1 | ✅ | **P3.6** — protéger contre `KeyError` quand `nb`/`sous_type` manque | rien (filet de tests vert) | technique : ordre audit #1 restant, prérequis réouverture push | [D16](BOUSSOLE/D16.md) |
| 2 | ☐ | **P5.11** — niveau « Supérieur » : retirer du menu *ou* bloquer le bouton | après P3.6 | technique : ordre audit ; **à clarifier menu vs bouton** avant de coder | [D16](BOUSSOLE/D16.md) |
| 3 | ☐ | **P3.5** — sur 401, rediriger vers /login | après P5.11 | technique : le + sensible ; **relire le flux refresh token** avant (risque de boucle) | [D16](BOUSSOLE/D16.md) |
| 4 | ☐ | **P4.7** — compteur few-shot `localStorage` → backend | rien dur | technique : **socle de l'item 40** (badge) ; refactor d'état | [D16](BOUSSOLE/D16.md) |
| 5 | ☐ | **P5.10** — centraliser la liste MATIERES (DRY, 3 endroits) | rien | technique : isole une régression | [D16](BOUSSOLE/D16.md) |
| 6 | ⏸️ | **P4.8 / P4.9** — carte Activité btn-primary · toast reset params | — | cosmétique : **différés** (sous gel), en fin de bloc | [D16](BOUSSOLE/D16.md) |

> 🎯 **Jalon de fin d'horizon : push rouvert.** Tant que H1 n'est pas clos, tout le reste est gelé.

---

## HORIZON 2 — À LA RÉOUVERTURE : dette technique / outillage (hors features)

| # | St | Tâche | Pourquoi ici |
|---|---|---|---|
| 7 | ☐ | **[Infra] Filet de test front (Vitest + Testing Library)** | complément front du filet backend D16 — le front n'a aucun test |
| 8 | ☐ | **[Process] Tests à 3 étages + [Outillage] journal de versions** | grave qui teste quoi / quand + traçabilité feedback prof ↔ version |
| 9 | ☐ | **[Mémoire] Nettoyer les memory files périmés** (refs BACKLOG / BOUSSOLE / LEVIERS) | cohérence — la dette laissée volontairement lors de la création du TRACKER |
| 10 | ☐ | **[UX/Aide] Rubrique « Exemple » dans tous les « Comment ça marche »** | transverse, tous les outils |
| 11 | ☐ | **[Refactor] Migration React Query (TanStack)** | session dédiée, ne pas mélanger |
| 12 | ☐ | **[Maintenance] Dette technique transverse** (2 sessions) | deps obsolètes, gestion d'erreurs API, sécurité des routes |

---

## HORIZON 3 — ENSUITE : features (gelées jusqu'au jalon H1)

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
| 3 | ☐ | **39** — Switch provider séquence → Claude Sonnet 4.6 | après 38 | [D28](BOUSSOLE/D28.md) |
| 4 | ☐ | **35** — Versioning & transposition de séquences | prérequis D07 (37) | [D26](BOUSSOLE/D26.md) |
| 5 | ☐ | **D13** — PROD Séquences 100% fonctionnel (umbrella) | attend D07 clôturé | [D13](BOUSSOLE/D13.md) |

### Chaîne RAG (ordre imposé)

| Ordre | St | Tâche | Dépend de | Fiche |
|---|---|---|---|---|
| 1 | 🔄 | **INFRA-RAG** — décision hébergement chroma_db (VPS) | DEV validé, prod à décider | [INFRA-RAG](RAG/INFRA-RAG.md) |
| 2 | 🔄 | **36** — Corpus Programmes MEN (producteur) | attend INFRA-RAG | [D24](BOUSSOLE/D24.md) |
| 3 | ☐ | **04** — Détecteur d'équité (consommateur RAG) | attend INFRA-RAG | [D17](BOUSSOLE/D17.md) |
| 3 | ☐ | **30** — Différenciation DYS / FLE (consommateur RAG) | attend INFRA-RAG | [D23](BOUSSOLE/D23.md) |
| 3 | ☐ | **25** — Cohérence curriculaire (consommateur RAG) | attend INFRA-RAG + corpus 36 | [D25](BOUSSOLE/D25.md) |
| 3 | ☐ | **31** — Appréciations bulletins & parents (consommateur RAG) | attend INFRA-RAG | [D19](BOUSSOLE/D19.md) |

> 🗃️ **INFRA-RAG — binaire-en-git vs rebuild-au-déploiement (à trancher plus tard, NŒUD BLOQUÉ).** Le store ChromaDB est committé en binaire (`maths_cycle4` ; + `bts_ciel_optionA` depuis le 13/06/2026). Question ouverte : garder les vecteurs en git, ou les rebâtir au déploiement via le script d'ingestion ? **Blocage dur :** « rebuild-au-déploiement » n'est PAS faisable uniformément — **maths n'a pas de PDF source** (manquant, cf. `REFERENTIELS/README.md`), donc maths **ne peut pas** être reconstruit : son **unique source de vérité est le binaire committé**. Tant que la source maths manque, la seule option sûre reste binaire-en-git. **Débloquer = récupérer le BOEN cycle 4 (PDF)** pour rendre maths reconstructible, puis seulement trancher. (Note : ouvrir le store re-churne les octets des segments — contenu intact ; cosmétique.)

> 🏗️ **Chantier B — Référentiel = colonne vertébrale du RAG (cadré 13/06/2026, GELÉ tant que H1 ouvert ; ordre dans la chaîne à fixer par l'utilisateur).** Rendre concret « dériver du référentiel », en deux briques : **(1)** un **script d'ingestion re-jouable** *référentiel → découpe → vecteurs → ChromaDB AVEC métadonnée `niveau`* — absente aujourd'hui : corpus actuel « cycle 4 en bloc », filtre niveau explicitement désactivé ([generate.py:78](../backend/routers/generate.py#L78)) ; **(2)** un **harnais de tests** qui vérifie que `retrieve()` remonte les bons extraits (= mesure la **qualité du RAG**, **pas** un « entraînement » du LLM — le Llama de Groq reste figé ; on alimente un référentiel, on ne ré-entraîne rien). **1er pas = ingestion BTS CIEL** : seule source vectorisable sous la main (référentiel en SQL) ; **maths n'a PAS de PDF source**, seulement ses ~699 vecteurs déjà en place. **Discipline (comme partout) : prouver l'apport du RAG sur UN couple** (BTS CIEL, une matière, sortie **avec vs sans** RAG) **avant d'élargir les gates** `SUBJECT_RAG_ELIGIBLE` / `CYCLE4_LEVELS`. But structurel : relier les **deux référentiels qui ne se parlent pas** — (a) SQL/menus ↔ (b) ChromaDB/RAG. Prolonge l'item **36** (corpus producteur) et la procédure « référentiel officiel → matières ».

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
| ☐ | **01** — Pages légales CNIL | attend infos admin (blocage externe) | [D39](BOUSSOLE/D39.md) |

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
| ✗ | **20** — Projet demo-perf FastAPI + PostgreSQL | hors-périmètre aSchool (projet séparé) | — |

> **Parking — NON RETENU** (à reconsidérer) : capture d'écran feedback · `logoutManager.ts` · recrutement profs Facebook/X · trajectoires multi-séances · labo simulation classe · modal multi-actions Oui/Non · tuning latence Deepgram · bug auth WS longues · etc. → détail dans [TABLEAU-DE-BORD.md](TABLEAU-DE-BORD.md) § NON RETENU.
> **HORS SCOPE** (refusé) : ENT/Pronote · multi-profs établissement · SQLite→PostgreSQL · cartographie cognitive · PPD. → § HORS SCOPE.

---

## Transverse / récurrent (hors ordre)

| St | Tâche | Quand |
|---|---|---|
| ⟳ | **12** — Synchronisation pages afia.fr (School.jsx) | automatique au prochain push **MINOR / MAJOR** |
| ✅ | **41** — Recherche dans la page Aide (plein-texte) | **fait en local (non déployé)** — part au prochain déploiement |

---

> **Pour ajuster :** à chaque tâche finie, l'utilisateur demande une relecture ; Claude vérifie l'état réel du projet et met à jour ordre / dépendances / tâches avant de continuer.
