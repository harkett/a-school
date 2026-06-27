# aSchool — DOCTRINE FONDATRICE & AUDIT « en base » vs « en dur »

> ## 🧭 OÙ J'EN SUIS (repère de navigation)
>
> Le chantier « REFONTE SOCLE » avance en **3 niveaux, dans l'ordre** :
>
> - **NIVEAU 0 — le PLAN de la base (MLD)** ............ ✅ **TERMINÉ** (27/06)
> - **NIVEAU 1 — le MOTEUR (SQLite → PostgreSQL)** ..... 🔄 **EN COURS** 🔴 ← je suis ici
> - **NIVEAU 2 — le REMPLISSAGE + bascules gelées** .... ⏳ pas commencé
>
> **Le Niveau 1 est devenu une migration découpée en 13 PAS** (détail dans la section NIVEAU 1 ci-dessous).
> Avancement : Pas 1 ✅ · Pas 3 ✅ · Pas 4 ✅ · Pas 5 ✅ · Pas 6 ✅ · Pas 7 ✅ · **Pas 8 ← prochain** · Pas 9 à 13 à venir.

---

> ## 🛠️ Maintenance de ce document
>
> - **Qui maintient** : c'est **Claude Code (CC)** qui tient ce document à jour — il a accès au code réel et le vérifie. L'**utilisateur surveille et vérifie**.
> - **Quand** : la progression est mise à jour **à la FIN de chaque pas validé** (et de chaque niveau), **pas en continu**.
> - **Comment** : chaque mise à jour est **montrée en avant/après AVANT d'être écrite**.
> - **Périmètre** : CC maintient les **faits et la progression** ; il ne touche **pas la doctrine ni la structure** sans demande explicite.

---

> # ⭐ DOCTRINE FONDATRICE (lettres d'or) ⭐
>
> **aSchool est un logiciel PROFESSIONNEL** — pas un bricolage, pas un prototype, pas « un truc qui marche à peu près ». Il ne vise pas à être un bon outil pour profs : il vise à être **LE logiciel de référence de sa catégorie**, au standard professionnel le plus exigeant, celui qui place la barre si haut qu'il ne laisse pas de place à un autre.
>
> **Socle non négociable :** aSchool tourne autour d'une **BASE DE DONNÉES RELATIONNELLE professionnelle**. TOUTES les données vivent en base — matières, niveaux, types d'activité, prompts, référentiels, réglages, contenus. **Rien de métier n'est codé en dur.** Une donnée en dur est un **défaut à corriger**, jamais un état acceptable.
>
> **Source de la donnée :** aSchool **ne s'invente rien**. Son contenu pédagogique est **EXTRAIT des référentiels officiels**, puis affiné et ciblé par un **RAG** (recherche augmentée) qui filtre et ne retient que ce qui est réellement pertinent pour le couple **matière + niveau**. Pas de référentiel pour un couple → **aSchool ne génère pas plutôt que d'inventer.**
>
> **Étalon de toute décision :** chaque ligne de code, chaque écran, chaque décision se juge à cette aune — *« est-ce digne d'un logiciel professionnel de référence, adossé à la base, ancré sur le référentiel ? »* Si la réponse est non, **ce n'est pas fini.**

---

## SOMMAIRE

- **Doctrine fondatrice** (ci-dessus) — le standard non négociable.
- **Plan de chantier — REFONTE SOCLE** (§ ci-dessous) — les 3 niveaux de travail.
- **Audit « en base / en dur »** (§0 à §7) — l'état réel du code, prouvé.
- **Annexe** — historique des 3 passes d'audit.

---

## PLAN DE CHANTIER — REFONTE SOCLE

**Objectif :** tout le logiciel adossé à la base, conforme à la doctrine. On avance par niveaux, **un seul à la fois**, et **on ne passe au suivant que quand le précédent est validé**. BTS CIEL reste intact (référence). On ne repart pas de zéro côté code applicatif.

### NIVEAU 0 — le PLAN de la base ✅ TERMINÉ (27/06)

Vérifier que la base relationnelle est juste et logique : tables, relations, cardinalités.

> ✅ **FAIT le 27/06.** Le MLD propre a été régénéré depuis le code réel (`data/aschool.dbml`, 22 tables vivantes, `stt_*` exclues, 15 vraies FK, copie de sauvegarde `.bak-2026-06-26`). Relations et cardinalités jugées : **ossature saine** (table `users` centrale + chaîne référentiel). Les défauts trouvés (texte libre `users.subject/niveau`, `fiches_matieres` rattachée par nom, filtres/agrégations sur texte) sont **notés et rangés au Niveau 2** — pas corrigés ici. `referentiels` avec `matiere_id` NULL = design assumé justifié. `BASE-DE-DONNEES.md` marqué « à refaire complètement ».

⚠️ **Constat de départ (historique) : les documents de modèle étaient périmés, seul le code (`models_db.py`) était à jour.** Le Niveau 0 a donc commencé par **régénérer un MLD propre depuis le code réel**, puis juger la logique sur ce MLD à jour.

Points concrets à traiter :
1. `data/aschool.dbml` (MLD, daté 11/06) **ne contient pas la table `referentiels`** (créée depuis). À régénérer.
2. Tables `stt_*` (×4) → ✅ **élucidé (27/06)** : présentes dans `data/aschool.db` (certaines avec données : `stt_messages` 8 lignes, `stt_keyterms_global` 80) mais créées par **aucun code de `main`** ni aucune migration (`schema_migrations` ne liste que 001→012) → **tables mortes**, vraisemblablement vestiges de la branche gelée `wip/deepgram-streaming` (dictée). **Exclues du MLD régénéré.**
3. `MesMD/BASE-DE-DONNEES.md` **périmé** : décrit l'ancien schéma (pivot `email`, FK implicites) alors que le schéma actuel est passé en `user_id` avec FK déclarées.
4. Incohérence de modèle connue : `niveau` est une **colonne texte libre** (`users`, `activites_sauvegardees`, `sequences_sauvegardees`), pas une entité/relation — à repenser.

### NIVEAU 1 — le MOTEUR de base 🔄 EN COURS

**Décision GRAVÉE le 27/06 : moteur cible = PostgreSQL** (renverse sciemment le « rester SQLite » du 25/06).
Pourquoi : base quasi vide aujourd'hui → presque rien à migrer, c'est le bon moment ; et le Niveau 2 (modifications de tables) est pénible sous SQLite, simple sous PostgreSQL.

**4 décisions de méthode tranchées :** (1) **synchrone** (driver `psycopg`, pas async) ; (2) **schéma neuf** depuis l'ORM (`create_all`), pas de rejeu des vieilles migrations SQLite ; (3) tests sur SQLite en mémoire pour l'instant ; (4) PostgreSQL auto-hébergé sur le VPS + mot de passe dans `.env` (jamais en dur).

> **Filet de sécurité :** tant qu'aucune `DATABASE_URL` n'est posée, l'app reste sur SQLite. La prod ne bascule qu'au tout dernier moment (Pas 12). Chaque pas est réversible sauf la coupure finale (protégée par sauvegarde).

#### Les 13 PAS de la migration (avancement)

| Pas | Ce qu'il fait | État |
|---|---|---|
| **1** | Contrôle d'intégrité des données (aucune donnée orpheline) | ✅ fait (0 orphelin) |
| **2** | Décider quoi garder / recréer quand on repart sur une base neuve | ⏳ reporté au Pas 8 |
| **3** | Ajouter le driver PostgreSQL (`psycopg`) | ✅ fait |
| **4** | Interrupteur : adresse de la base pilotée par `.env`, défaut SQLite | ✅ fait |
| **5** | Adapter la fonction « taille de la base » selon le moteur | ✅ fait |
| **6** | Nettoyer le code des spécificités SQLite (schéma neutre) | ✅ fait |
| **7** | Installer PostgreSQL (en local d'abord) + poser la `DATABASE_URL` | ✅ fait |
| **8** | Recréer le schéma propre + remettre les données de référence (BTS CIEL intact) | 🔴 ← je suis ici (prochain) |
| **9** | Adapter le système de migrations (baseline PostgreSQL) | ⏳ à venir |
| **10** | Tout tester en local sur PostgreSQL | ⏳ à venir |
| **11** | Corriger les textes d'écran (« SQLite » → « PostgreSQL ») | ⏳ à venir |
| **12** | **Déploiement sur le VPS** (sauvegarde avant, bascule prod) | ⏳ à venir |
| **13** | **TON test en vrai, en conditions prof** (juge de paix) | ⏳ à venir |

Quand le Pas 13 est validé → le Niveau 1 est **terminé**, on passe au Niveau 2.

#### Tâches en attente du Niveau 1 (repérées au Pas 7, à traiter au moment dit)

> **Contexte install local (27/06) :** PostgreSQL **16.14** installé sous `C:\Users\harketti\PostgreSQL\16` (archive binaire EDB), instance **dédiée port 5433** (le 5432 est déjà pris par une autre instance PostgreSQL — isolée, jamais touchée), base + rôle `aschool` créés, serveur lancé via `pg_ctl` sous compte Windows **non-admin**. Auth encore en `trust` local (mot de passe `aschool` posé mais pas encore exigé tant que le `trust` est là).

- **(a) Durcissement admin — EN BLOC, impératif en prod (Pas 12).** Les quatre gestes vont ensemble : renommer `postgres` → identifiant choisi · poser le mot de passe admin · **couper le `trust`** (passer `pg_hba.conf` en `scram-sha-256`) · **refaire le mot de passe `aschool`** au même moment. Un mot de passe sans coupure du `trust` est ignoré → indissociables. En local : **optionnel** (écoute `127.0.0.1`, compte non-admin) ; en prod : **non négociable**.
- **(b) Service PostgreSQL auto-démarrant — optionnel.** Aujourd'hui le serveur tourne via `pg_ctl` (pas de redémarrage automatique au boot). Enregistrer un vrai service Windows demande un **terminal administrateur** (le compte courant n'est pas admin).
- **(c) Petit ménage `.pyc` du Pas 6 — trivial.** Le cache `backend/__pycache__/models_db.cpython-312.pyc` se régénère seul ; rien d'urgent (cache régénérable, pas du code source).

### NIVEAU 2 — le REMPLISSAGE

Mettre en base tout ce que l'audit ci-dessous a marqué « en dur » et qui doit y vivre (types d'activité, ~140 prompts, listes de référence, contenu éditorial…), directement dans la bonne base. Réparer au passage les 2 orphelins cassés et le vote fantôme (voir §5).

---
#### Avant d'attaquer ce point -REFAIRE UNE 4em PASSE pour est coforme suite aux derniers changements de code
> **Document de référence.** Issu de trois passes d'audit successives (1 → rapide, 2 → exhaustif, 3 → clôture sans trou). Ce fichier conserve **l'audit final complet (passe 3)** comme corps, précédé de la **preuve de couverture (passe 2)**. Les passes 1 et 2 étaient des versions intermédiaires, intégralement absorbées par la passe 3 ; seule leur section « méthode / couverture » est conservée ci-dessous car elle prouve l'exhaustivité.
>
> Date de consolidation : 26 juin 2026.
> État : rien codé, rien commité, rien supprimé pendant l'audit.

---

## 0. Preuve de couverture (méthode — repris de la passe 2 + clôture passe 3)

**Volume parcouru :**
- Backend : ~12 865 lignes, tous les `.py` de `backend/` + `src/` (51 fichiers).
- Frontend : ~16 601 lignes, tous les `.jsx` / `.js` de `frontend/src/` (78 fichiers).

**Comment la recherche a été menée :**
- Inventaire : `find backend src -name "*.py"` + `find frontend/src`.
- Sweep des structures backend : `grep` des constantes au niveau module (`^NOM =`) **et** des structures indentées à l'intérieur des fonctions.
- Ouverture manuelle des fichiers porteurs de données : `admin.py`, `stats.py`, `fiches.py`, `programmes.py`, `maintenance.py`.
- `grep` des prompts/templates inline (`Tu es`, `f"""`) sur tout le backend.
- Sweep frontend : `grep` des `const = {…} / […]` + ouverture des porteurs (`App.jsx` TUTOS, `BientotDisponible`, `MonProfil`, `Signup`, `MesFeedbacks`, `AdminFiches`…) + `grep` final des `<option>` et listes inline.
- Vérification du flux matières/niveaux (API vs dur) via `useMatieres.js`, `profil.js`, `App.jsx`.
- **Exécution réelle** pour confirmer les points qui restaient en suspens (D1, D3 ci-dessous).

**Exclus volontairement (et pourquoi) :** `test_*.py` (vérification, pas l'appli) ; `seed_*.py` (données destinées à la base, caractérisées comme graines) ; `__pycache__` (bytecode).

---

## 1. Vue d'ensemble (la photo en une phrase)

Le **référentiel** (cycles, niveaux, matières, couples, routage couple→collection) est **en base**.
**Tout le reste du moteur de génération** — types d'activité et prompts d'activité — est **en dur** dans le code.
Un second jeu de prompts (les **outils** : ambiguïtés, consigne, séquence, optimiseur) est en dur **mais surchargeable en base** (demi-pont).

---

## 2. Ce qui est DÉJÀ EN BASE ✅ (lecture runtime depuis SQLite)

| Élément | Table(s) | Preuve |
|---|---|---|
| Cycles / niveaux / matières / couples | `cycles`, `niveaux`, `matieres`, `matiere_niveaux` | `models_db.py:243-293` ; API `programmes.py` ; front `useMatieres.js:21` |
| Ce que le prof enseigne *(structure seulement)* | `user_enseignements` — **table créée mais DORMANTE** (0 ligne, jamais lue ni écrite) | `models_db.py:288-293` ; mécanisme réel aujourd'hui = le texte `users.subject/niveau` (cf. Annexe Niveau 2) |
| Routage couple → collection RAG | `referentiels` | `models_db.py:296-316`, `012_create_referentiels.sql`, `exemple_referentiel.py:41-70` |
| Ligne BTS CIEL option A | `referentiels` (seed migration) | `012:25-28` |
| Réglages LLM texte (provider, modèle, max_tokens, température) | `settings` | `admin.py:104-161`, `generate.py:70` |
| Prompts des 5 OUTILS (override) | `settings` (`prompt_<clé>`) | `admin.py:164-172` |
| Activités / séquences / feedbacks / votes / fiches (données utilisateur) | tables dédiées | `models_db.py` |

> **Nuance :** les valeurs initiales de cycles/niveaux/matières sont écrites en clair dans `seed_programmes.py` (chargeur unique), mais ce sont des **graines idempotentes** : le runtime lit la base, l'admin édite la base via le CRUD. **Source de vérité = base**, graine initiale en code.

---

## 3. LA TOTALITÉ de ce qui est EN DUR

### Bucket 1 — Données métier en dur, qui devraient/pourraient vivre en base ⚠️

| # | Élément | Fichier:ligne | En base ? |
|---|---|---|---|
| 1 | Types d'activité (`ACTIVITES_PAR_MATIERE` **vide** + 3 génériques) | `activities.py:8,13` | ❌ |
| 2 | ~140 prompts d'activité (`PROMPTS`, `PROMPTS_HISTGEO`, `PROMPTS_AUTRES`, `PROMPTS_GENERIQUES`) | `prompts.py:1,321,594,2663` | ❌ aucun override |
| 3 | Réglages découpe RAG d'un référentiel (`SCORE_MIN=0.33`, `MAX_CHARS`, sections option B, regex) | `bts_ciel_option_a.py:31-42` | ❌ fiche Python |
| 4 | Liste des langues LV (8) — **en double** | `MonProfil.jsx:7` + `Signup.jsx:121-128` | ❌ |
| 5 | Chaîne magique `'Langues Vivantes (LV)'` (branchement) — **5 endroits** | `App.jsx:86,291` ; `MonProfil.jsx:196` ; `Signup.jsx:36,111` | ❌ |
| 6 | Catalogue roadmap votable — **2 sources désynchronisées** | `votes.py:13-24` + `BientotDisponible.jsx:4` | ❌ |
| 7 | Catégories feedback (bug/suggestion/question) | `Feedback.jsx:4` + `MesFeedbacks.jsx:4` | ❌ |
| 8 | Statuts feedback + transitions (front+back) | `admin.py:294` + `feedback.py:29` + `MesFeedbacks.jsx:10-16` | ❌ |
| 9 | Statuts fiches (brouillon/publie/a_reviser) — option en dur = valeurs du modèle | `AdminFiches.jsx:197-199` | ❌ |
| 10 | Durées de séquence `{30,45,50,55,60,90,120}` (front+back) | `sequence.py:14` + `SequenceForm.jsx:5` | ❌ |
| 11 | Catégories de maintenance BDD | `maintenance.py:20` | ❌ |
| 12 | IDs des modèles IA non-texte (Whisper, embeddings, OCR) — *le texte, lui, est en base* | `groq_client.py:7`, `embeddings.py:15`, `generator.py:140` | ❌ |

### Bucket 2 — Prompts / templates en dur (contenu généré ou éditorial)

| # | Élément | Fichier:ligne | Override base ? |
|---|---|---|---|
| 13 | Prompt génération « fiche matière » (inline) | `fiches.py:287` | ❌ non override-able |
| 14 | Prompt OCR (inline) | `generator.py:150` | ❌ |
| 15 | Emails HTML : welcome, notif feedback, notif activation, feedback modifié | `auth.py:319,391,442,540,581` | 🟡 seul le corps *welcome* a un override (`admin.py:53`) |
| 16 | Email HTML d'alerte admin | `alerts.py:36` | ❌ |
| 17 | Page HTML publique « fiche matière » | `fiches.py:85` | ❌ |
| 18 | Aide prof complète (sections, options, catégories) | `Aide.jsx:173,236,1164` | ❌ |
| 19 | Aide admin | `AdminAide.jsx:1` | ❌ |
| 20 | Tutoriels par écran (`TUTOS`) | `App.jsx:453` | ❌ |
| 21 | Tips d'accueil | `Accueil.jsx:3` | ❌ |

### Bucket 3 — EN DUR à juste titre (config / infra / style — NE PAS mettre en base) ✅

- **Secrets & infra :** `SECRET_KEY`, durées tokens, lockout (`auth.py:17-22`) · `DATABASE_URL` (dans `.env` depuis le Pas 4 — `database.py` la lit via `os.getenv`, défaut SQLite ; plus « en dur ») · défauts LLM `.env` (`config.py`) · cookies / algos JWT · bornes max_tokens/température · limites upload/audio/MIME (`feedback.py`, `transcribe.py`).
- **Navigation / structure UI :** `NAV_ITEMS` (`AdminLayout.jsx:12`), pages Sidebar.
- **Style :** toutes les constantes couleurs/CSS (`TYPE_COLOR`, `SCORE_COLORS`, `HR`, `S`, `UL`…) sur tout le front.

---

## 4. Confirmations par EXÉCUTION (plus aucune supposition)

**D1 — « Fiches matières » et « AdminActivités » sont cassés (catalogue vidé).**
Exécuté :
```
ACTIVITES_PAR_MATIERE = {}   → fiches.MATIERES = []
GET /api/admin/fiches  → []   ;  'Français' not in MATIERES → 404 (idem toutes matières)
```
→ Confirmé : `fiches.py:21` et `admin.py:341-384` dérivent tout d'un dict vide. Les deux pages admin renvoient du vide / 404. **Fait, pas hypothèse.**

**D3 — Roadmap des votes désynchronisée, vote fantôme.**
Exécuté (diff sur fichiers réels) :
```
Front SANS back (vote → 400) = ['ambiguites-cognitives', 'coherence-curriculaire']
Back  SANS front (jamais affiché) = ['app-mobile']
```
`BientotDisponible.jsx:104-118` fait une MAJ optimiste **sans rollback** sur réponse non-ok → cliquer ces 2 features affiche un vote pris alors que `votes.py:61` renvoie 400 → **vote fantôme** qui disparaît au rechargement. **Confirmé.**

---

## 5. Issues structurelles trouvées (en plus du « en dur »)

1. **2 orphelins cassés** par la suppression du catalogue : pages *Fiches matières* et *AdminActivités* (D1, confirmé exécution).
2. **Vote fantôme** sur 2 features de la roadmap (D3, confirmé exécution).
3. **Duplications front/back qui dérivent déjà** : langues LV (×2), roadmap (désynchro avérée), statuts feedback, durées séquence.
4. **Bytecode mort** : `src/__pycache__/generated_activities.cpython-312.pyc` sans source (`generated_activities.py` et `parse_markdown.py` supprimés) — plus aucun import, juste un commentaire résiduel dans `activities.py:4`.
5. **Incohérence modèles IA** : le modèle texte est administrable en base, mais Whisper / embeddings / OCR restent en dur (#12).

---

## 6. Tableau de synthèse

| Brique | En base | En dur | Fichier en dur |
|---|---|---|---|
| Cycles / niveaux / matières / couples | ✅ runtime | graine seed | `seed_programmes.py` |
| Matières BTS CIEL + paires | ✅ | graine seed | `seed_programmes.py` (DIPLOMES) |
| Routage couple → collection | ✅ table | — | (012 + table) |
| Règles découpe + seuil référentiel | — | ✅ | `bts_ciel_option_a.py` |
| Types d'activité | ❌ | ✅ (3 génériques, reste supprimé) | `src/activities.py` |
| Prompts d'activité (~140) | ❌ | ✅ | `src/prompts.py` |
| Prompts outils (5) | 🟡 override | défaut | `backend/llm_prompts.py` |
| Réglages LLM | ✅ | défaut .env | `src/config.py` |

---

## 7. Déclaration de complétude

Tout le code applicatif (backend `.py` + frontend `.jsx`/`.js`) a été parcouru, au niveau module **et** dans le corps des fonctions, les points en suspens confirmés par exécution. Ceci est **la totalité de ce qui est en dur** dans le logiciel ; après cette lecture, il n'y a rien d'autre.

**Réserve honnête, par rigueur :** les 3254 lignes de `seed_exemples.py` (24 activités de démo) n'ont pas été relues ligne à ligne — caractérisées comme graine destinée à la base, pas comme donnée de référence runtime. À éplucher uniquement si besoin.

---

## Annexe — historique des passes

- **Passe 1** — audit rapide (tableau de synthèse seul). Version intermédiaire, absorbée par la passe 3.
- **Passe 2** — audit exhaustif (méthode `find`/`grep`, sections A/B/C/D, premiers points nouveaux). Version intermédiaire ; sa section « méthode / couverture » est conservée au §0 ci-dessus.
- **Passe 3** — clôture, deux trous fermés (intérieur des fonctions `admin.py`/`stats.py` + points « à vérifier » confirmés par exécution). **C'est le corps de ce document.**

---

## ANNEXE NIVEAU 2 — le défaut « texte libre » (constat prouvé, à corriger plus tard)

> Ce constat a été établi sur le code réel. Il documente le principal défaut à corriger au **Niveau 2** (relier par identifiant au lieu du texte). **Rien n'est corrigé ici** — c'est une fiche de référence pour le moment venu.

J'ai tracé le code réel. Voici le constat factuel (pas de reco). Je réponds à tes 3 questions.

**1. Où le texte libre est stocké — 6 colonnes, 3 endroits**

| Endroit | Colonnes | Écrit par | Lu par |
|---|---|---|---|
| `users` (profil prof) | `subject` (matière), `niveau` | inscription (`auth.py:82`), édition profil (`profil.py:55-56`), édition admin (`admin.py:427-428`) | profil/dashboard (`profil.py:40-41`) + voir §2 |
| `activites_sauvegardees` | `matiere`, `niveau` | sauvegarde activité (`mes_activites.py:80-81`) | liste (`mes_activites.py:113-114`) + voir §2 |
| `sequences_sauvegardees` | `matiere`, `niveau` | sauvegarde séquence (`sequence.py:89-90`) | liste (`sequence.py:121-122, 201-202`) + voir §2 |
2. À quoi sert vraiment chaque valeur — clé ou étiquette ?
users.niveau / users.subject → les DEUX, et c'est le cas sensible :

Étiquette : affiché dans le profil et le tableau de bord.
CLÉ par chaîne (le point dur) : le niveau du profil arrive jusqu'à exemple_referentiel.py:60 où il sert de jointure texte : .filter(Niveau.nom == niveau). Si le texte ne matche pas exactement un niveaux.nom, le référentiel n'est pas trouvé → available:false en silence. C'est exactement le risque « 4e vs 4ème ».
CLÉ d'agrégation : admin.py:367-370 fait group_by(User.subject) pour les stats.
activites_sauvegardees.matiere/niveau → étiquette FIGÉE, mais aussi clé secondaire :

Snapshot volontaire : recopié à la génération, immuable par design (docstring models_db.py:101-111 : modifier le profil ne réécrit aucune activité passée).
Mais réutilisé comme CLÉ de filtre (bibliotheque.py:34-36, « Mon réseau ») et d'agrégation (stats.py:144-146, 242-244, group_by(matiere)).
sequences_sauvegardees.matiere/niveau → même profil que les activités :

Étiquette + injecté dans le prompt (sequence.py:64-65, 72-73).
CLÉ de filtre (sequence.py:193-195).
(Snapshot : la séquence recopie aussi la valeur à la sauvegarde.)
À noter : dans /api/generate, niveau ne sert que d'étiquette dans le prompt (generate.py:55), et matiere n'y est même pas utilisée.

3. Les différences à ne PAS mettre dans le même sac
users.* = valeur VIVANTE, la source. C'est elle qui sert de clé vivante vers le référentiel (jointure texte Niveau.nom == niveau). Une faute de frappe ou un renommage casse le lien en silence. → c'est le vrai défaut que tu pressentais.
activites_* / sequences_* = SNAPSHOT figé assumé. Le texte y est volontairement immuable (on ne veut pas réécrire l'historique). Le hic n'est pas le snapshot lui-même, mais qu'on s'en serve en plus comme clé de regroupement dans les stats/réseau — donc un libellé figé qui ne colle plus au nommage actuel mal-groupe discrètement.
Résumé en une phrase : users mélange étiquette et clé vivante (à corriger en relation) ; les sauvegardes sont des snapshots figés voulus, mais détournés en clés de regroupement (cas plus subtil, à juger séparément).

C'est le constat. On décide après, sur cette base.





------------------------ LES NIVEAUX------------------------------------
# CHANTIER aSchool — SOMMAIRE

fait ✅Niveau 0 : vérifier le plan de la base (le MLD) → 
fait ✅ Niveau 1 : changer le moteur, SQLite → PostgreSQL → en cours (on est au Pas 8)
pas commencé ⏳ Niveau 2 : sortir tout ce qui est encore en dur (prompts, types d'activité, aide, durées, langues...) et le mettre en 

## RÈGLES PERMANENTES (rappel)
- Zéro "sqlite" dans le code après bascule
- On relie par IDENTIFIANT, jamais par texte
- Suppression = sauvegarde .bak + preuve avant
- CC installe, Harketti supervise (sauf saisie mot de passe)
- CC écrit dans .env, Harketti pose juste le mot de passe
- Un GO par étape, jamais global


## NIVEAUX (les 3 grands blocs)
- NIVEAU 0 — Plan de la base (MLD)              ✅ terminé
- NIVEAU 1 — Moteur SQLite → PostgreSQL         🔄 EN COURS
- NIVEAU 2 — Sortir tout ce qui est en dur      ⏳ pas commencé

## NIVEAU 1 — les 13 PAS
- Pas 1  — Intégrité des données                ✅
- Pas 2  — Décider quoi garder (base neuve)     ✅ (fait au Pas 8)
- Pas 3  — Driver PostgreSQL (psycopg)          ✅
- Pas 4  — Interrupteur .env (DATABASE_URL)     ✅
- Pas 5  — Taille de la base selon moteur       ✅
- Pas 6  — Nettoyer les spécificités SQLite     ✅
- Pas 7  — Installer PostgreSQL local + .env    ✅
- Pas 8  — Schéma + données réf. (BTS CIEL)     ✅
- Pas 9  — Système de migrations (Alembic)      🔄 EN COURS  ← ON EST LA
- Pas 10 — Tout tester en local sur PostgreSQL  ⏳
- Pas 11 — Corriger les textes d'écran          ⏳
- Pas 12 — Déploiement VPS (bascule prod)       ⏳
- Pas 13 — Test final en conditions prof        ⏳

## PAS 9 — les sous-étapes (lettres)
- A — Installer Alembic                         ✅
- B — Câbler Alembic (env.py)                   ✅
- C — Poser la baseline                         ✅
- D — Retirer le create_all                     ✅
- E — Ranger la ligne BTS CIEL                  ✅ (absorbée dans le chargeur unique)
- (chantier) Chargeur unique data-driven        ✅  ← gros travail du jour
- (commits A + B)                               🔄 EN COURS
- F — Retirer le runner maison + .sql           ⏳  ← prochain
- G — Preuves finales du Pas 9                  ⏳



************

# ----> F. Retirer le runner maison
Supprimer migrations/run_migrations.py + les 12 .sql SQLite + le README (l'historique reste dans git). C'est sans risque : vérifié, il n'est pas branché au déploiement. (À valider — suppression.)

# G. Comment je prouve que rien n'est cassé
alembic current → la base est bien à la révision baseline.
alembic check (autogenerate à blanc) → « no changes detected » = le modèle correspond exactement à la base (preuve que la baseline reflète le schéma réel).
recompte des 22 tables + données de référence (cycles/niveaux/matières/référentiel BTS CIEL) → inchangés.
l'app démarre + pytest inchangé (mêmes 4 rouges préexistants).

# H. Hors Pas 9 (noté)
Brancher Alembic dans le déploiement VPS = Pas 12 (le runner maison n'y était pas branché de toute façon).

Décisions que tu valides avant que je touche à quoi que ce soit :

Dossier alembic/ à la racine — OK ?
Baseline = migration initiale complète + stamp sur la base existante — OK ?
Retirer le create_all du boot (Alembic devient l'autorité) — OK ?
Ligne référentiel → dans le chargeur unique `seed_programmes.py` (DIPLOMES) — fait.
Supprimer le runner maison + 12 .sql — OK ?
Tu valides (tout ou point par point), et seulement après j'exécute, étape par étape.

#  ----> et avce BIENSUR
Pas 10 = tester l'app en vrai sur PostgreSQL (vérifier que ça marche)
Pas 11 = corriger les textes d'écran (« SQLite » → « PostgreSQL »)
Pas 12 = déploiement sur le VPS (basculer la prod)
Pas 13 = ton test final en conditions prof