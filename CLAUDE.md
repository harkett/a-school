# CLAUDE.md — Référence permanente aSchool

> Chargé automatiquement à chaque session. Règles + contexte technique — source unique de vérité.

★★★━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━★★★
★★★       RÈGLE N°0 — ORGANISATION DE CE FICHIER           ★★★
★★★━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━★★★

## 🗂️ Règle n°0 — Organisation de CLAUDE.md : regrouper par thème (absolue)

CLAUDE.md doit rester facile à lire et à chercher. Tout ce qui concerne un même thème vit dans UNE seule section dédiée, jamais éparpillé en plusieurs endroits du fichier.

Chaque section est encadrée d'un bandeau d'étoiles bien visible — comme la section « BASES DE DONNÉES » — pour la retrouver d'un coup d'œil.

À chaque fois que Claude Code ajoute une règle ou une information, il la range dans la bonne section existante ; il n'ajoute jamais une énième entrée isolée. Si le thème n'a pas encore de section, il en crée une, au même standard.

★★★━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━★★★
★★★                  FIN — RÈGLE N°0                       ★★★
★★★━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━★★★

## 🔍 Règle n°1 — Vérifier la cohérence AVANT de toucher (absolue)

Avant toute modification, ou tout appui, sur un élément du projet — document, fichier de code, n'importe quoi — **vérifier d'abord qu'il est cohérent** :
- le **lire en entier** (pas le diff, pas en survol) ;
- contrôler que ses **liens / chemins / références existent** réellement ;
- contrôler que son **contenu n'est pas périmé** ni contredit par la réalité (code, git, autres docs).

Cette vérification est **systématique et ne dépend d'aucune demande** : elle précède toute action. Si une incohérence est trouvée, **la signaler avant d'agir** — ne jamais construire par-dessus. (Règle née le 09/06/2026 : sans elle, je bâtis sur du périmé jusqu'à ce qu'on m'arrête.)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🔒 Règle de périmètre — le dossier aSchool, rien d'autre (absolue, permanente)

**Le seul périmètre de travail est le dossier `D:\A-SCHOOL` et son environnement direct** (comme un dossier ouvert dans VS Code — ce dossier et son environnement, c'est tout le monde de Claude). En dehors de ce dossier : **interdiction absolue** d'aller chercher, lire, scanner ou fouiller quoi que ce soit — **surtout pas le disque `C:\`, ni Windows, ni les autres installations / bases / applications** de la machine. Elles appartiennent à d'autres projets de Harketti et **ne regardent pas aSchool**.

Si quelque chose **hors** du dossier aSchool est nécessaire (un binaire, un chemin, une info système), **le demander explicitement à Harketti et attendre son GO** — ou le laisser fournir la réponse lui-même. **On ne sort jamais du dossier de son propre chef.**

(Règle née le 30/06/2026 : un scan de tout Windows est tombé sur le PostgreSQL d'une **autre** application, pris à tort pour celui d'aSchool ; tout un faux diagnostic bâti dessus, et la suppression des données d'un projet tiers **qui fonctionne** évitée de justesse. Une journée perdue. Ne se reproduit plus.)

> **Seule exception, explicitement désignée par Harketti :** le cluster PostgreSQL d'aSchool vit hors du dossier projet, dans `C:\Users\harketti\PostgreSQL\16` (port 5433). On n'y touche **que** parce que Harketti l'a nommément rattaché à aSchool. **Tout autre PostgreSQL de la machine est hors périmètre** (notamment l'install v17 `Program Files` / port 5432 = autres applications).
>
> **Démarrer / arrêter ce cluster (PAS de service Windows — ne survit pas à un reboot ; désormais `run.ps1` le démarre s'il est arrêté, idempotent — sinon à la main ci-dessous) :**
> ```powershell
> # démarrer (port 5433)
> & "C:\Users\harketti\PostgreSQL\16\pgsql\bin\pg_ctl.exe" -D "C:\Users\harketti\PostgreSQL\16\data" -l "C:\Users\harketti\PostgreSQL\16\data\startup.log" -w start
> # arrêter
> & "C:\Users\harketti\PostgreSQL\16\pgsql\bin\pg_ctl.exe" -D "C:\Users\harketti\PostgreSQL\16\data" stop
> ```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

★★★━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━★★★
★★★           VISION — QUI EST aSCHOOL & POUR QUI          ★★★
★★★━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━★★★

## Vision

Plateforme web de génération d'activités pédagogiques pour les enseignants, sans compétences techniques requises. Construit étape par étape, validé avec des profs pilotes réels.

**Tagline few-shot :** "À partir de quelques utilisations, aSchool s'adapte à votre façon de formuler les exercices."

**Vision multi-niveaux (cap, non engagé) :** aSchool décliné par niveau — Crèche · Maternelle · Primaire · Collège · Lycée · Supérieur. Détail + statut : `MesMD/TABLEAU-DE-BORD.md` → § « Direction produit ».

### 🏆 Le cap — en lettres d'or (ambition fondatrice, absolue)

> **aSchool vise à être un logiciel PROFESSIONNEL — pas un bricolage, pas un prototype, pas « un truc qui marche à peu près ». L'ambition n'est pas d'être *un* bon outil pour profs : c'est d'être *LE* logiciel de référence de sa catégorie, au standard professionnel le plus exigeant, celui qui place la barre si haut qu'il ne laisse pas de place à un autre.**
>
> **Socle non négociable : aSchool doit tourner autour d'une BASE DE DONNÉES RELATIONNELLE professionnelle. TOUTES les données doivent vivre en base — matières, niveaux, types d'activité, prompts, référentiels, réglages, contenus. Rien de métier ne doit être codé en dur. Une donnée en dur est un défaut à corriger, jamais un état acceptable.**
>
> **Source de la donnée : aSchool ne doit rien s'inventer. Son contenu pédagogique doit être EXTRAIT des référentiels officiels, puis affiné et ciblé par un RAG (recherche augmentée) qui filtre et ne retient que ce qui est réellement pertinent pour le couple matière + niveau. Pas de référentiel pour un couple → aSchool ne génère pas plutôt que d'inventer.**
>
> **Chaque ligne de code, chaque écran, chaque décision se juge à cette aune : « est-ce digne d'un logiciel professionnel de référence, adossé à la base, ancré sur le référentiel ? » Si la réponse est non, ce n'est pas fini.**

### 🎯 Pour qui — aSchool est POUR l'enseignant (règle absolue)

Le **public unique d'aSchool, à tous les niveaux** (Crèche → Supérieur), est **l'enseignant**. Une fonctionnalité qui ne sert pas le prof à enseigner est **hors périmètre**, même si elle est « pédagogique ». Sont **exclus** : tout ce qui s'adresse directement à l'étudiant (emploi, CV, portfolio personnel) ou à un autre public (conseillers d'orientation, recruteurs). Tout ce que l'IA produit pour les étudiants est généré **par le prof**, qui reste l'unique utilisateur de l'outil.

**Concrètement.** aSchool n'est **pas** un logiciel qu'on met entre les mains des enfants pour jouer. L'utilisateur, c'est le **prof** (ou l'animatrice de crèche). Il se connecte avec son couple — son cycle, son niveau, sa matière — et aSchool lui **génère une activité fidèle au référentiel officiel**. L'enfant, lui, **ne touche jamais le logiciel** : il **vit** l'activité que le prof a préparée avec aSchool. **Même en crèche**, l'utilisateur est l'adulte, jamais le tout-petit.

★★★━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━★★★
★★★                     FIN — VISION                       ★★★
★★★━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━★★★

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📜 Script éphémère — le SEUL moyen de remplir la base (règle absolue)

**Le mot « seed » est banni. On dit « script éphémère ».**

Toutes les données métier **doivent vivre** dans la **BASE** — **aucune donnée métier ne doit être codée en dur** (cap fondateur ci-dessus). Quand il faut **remplir la base**, on n'écrit **jamais** un fichier permanent qui porte des données en dur (comme l'était `seed_programmes.py`, supprimé). On écrit un **script éphémère**.

**Définition.** Un script éphémère est un script **jetable**, créé dans un **seul but** : lire une **source officielle**, **alimenter la base une fois**, puis **être supprimé**. Il ne fait **jamais** partie de l'application, il ne **reste jamais** dans le projet.

**Cycle de vie, non négociable :** **créer → alimenter la base → supprimer.** Une fois la base remplie, le script **disparaît** (historique git si besoin). Un script qui *reste* dans le projet en portant de la donnée métier est un **défaut** — c'est exactement ce qu'on ne veut plus.

**Distinction clé :** ce n'est pas l'usage d'un script qui est interdit, c'est qu'un script **persiste** en portant la donnée. Remplir puis disparaître = sain. Rester avec des données en dur = à virer.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Stack technique

| Composant | Détail |
|---|---|
| Backend | FastAPI — `backend/main.py` — port 8001 (local, cohabitation) / 8001 (VPS) |
| Frontend | React + Vite — `frontend/` — port 5173 |
| BDD | **PostgreSQL** (psycopg, port 5433) — moteur **unique** ; SQLite **banni** (garde-fou `backend/database.py` qui refuse de démarrer sans `DATABASE_URL` PostgreSQL ; tests sur base dédiée `aschool_test` via `conftest.py`, 3 verrous). pgvector pour le RAG. |
| IA | Groq API — `llama-3.3-70b-versatile` |
| Dictée | Groq Whisper API — batch `whisper-large-v3` (streaming Deepgram gelé sur `wip/deepgram-streaming`) |
| Auth profs | email + bcrypt + JWT (python-jose) + httpOnly cookies |
| Auth admin | Cookie `aschool_admin` — JWT séparé `{"role": "admin"}` |
| Emails | Infomaniak (SMTP) — voir § Gestion des emails |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## VPS production

| Info | Valeur |
|---|---|
| URL | https://aschool.fr |
| IP | 83.228.245.163 |
| SSH | ubuntu@83.228.245.163 |
| Chemin | /var/www/a-school/ |
| Service | `aschool.service` (systemd) |
| Port | 8001 (8000 occupé par Django AFIA-FR) |
| OS | Ubuntu 24.04.4 LTS |
| SSL expiry | 2026-08-05 |

**Statut : production ARRÊTÉE — aSchool ne tourne plus en ligne et aucun prof ne l'utilise actuellement (prod stoppée par Harketti). Le VPS reste la cible de redéploiement le jour venu ; ne jamais présumer que la prod est active.**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Scripts clés

```powershell
.\Scripts\run.ps1              # Démarre PostgreSQL (5433, si arrêté) + backend (:8001) + frontend (:5173) — sync dépendances Python + logos avant · param -BackendPort (défaut 8001)
.\Scripts\push.ps1             # Sauvegarde GitHub UNIQUEMENT (git push seul) — ne déploie PAS la prod, ne bump PAS la version
.\Scripts\deploy.ps1 "message" # Bump PATCH auto → commit → push GitHub → déploiement VPS (geste sous validation explicite)
```

**Deux gestes, deux scripts, jamais confondus :** `git push` / `push.ps1` = sauvegarde GitHub, n'affecte **pas** la prod. `deploy.ps1` = déploiement VPS, **sous validation explicite**.

La version vit dans `frontend/package.json`. Le PATCH est incrémenté automatiquement par `deploy.ps1` (`npm version patch`). MINOR et MAJOR sont manuels.

**Cohabitation locale :** le port 8000 local est souvent pris par un autre projet (A-VIEWCAM). `run.ps1` lance donc aSchool sur **8001** (paramètre `-BackendPort`, défaut 8001), ne tue jamais le 8000 voisin, et passe `VITE_API_PORT` au frontend (proxy Vite configurable via `process.env.VITE_API_PORT`). Cohérent avec le VPS (aSchool en 8001 derrière Django AFIA-FR).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Taxonomie des outils — note de conception (classement, pas mode d'emploi prof)

> Grille pour RANGER tout outil prof. À usage interne (nous / futur dev), jamais
> dans l'aide prof. Actée le 12/06/2026.

Les exemples ci-dessous illustrent le classement : ils incluent des outils déjà livrés et des outils encore à venir. Cette grille range les outils, elle ne dit pas ce qui est disponible.

**4 verbes, pas un fourre-tout :**

| Verbe | Définition | Exemples |
|---|---|---|
| **CRÉER** | Produire un contenu **de zéro** (point de départ vierge) | Activité, Séquence — et les *types de sortie* : Mémo flash, Fiche, Escape game, Supports de créativité, Quiz… |
| **ANALYSER** | Examiner un contenu **existant** et constater (sans le modifier) | Ambiguïtés, Consigne, Équité |
| **AMÉLIORER** | Agir sur l'**existant** pour l'optimiser (même finalité, en mieux) | Optimiseur de séquences |
| **ADAPTER** | Transformer un contenu **existant** pour un besoin élève (re-ciblage) | Différenciation (proactif, AVANT : DYS/FLE/approfondissement) + Remédiation (réactif, APRÈS : combler un écart constaté) |

**Critère de tri d'un nouvel outil (la question qui tranche) :**
« Point de départ vierge (**Créer**) OU action sur un contenu déjà là ? »
Si action sur l'existant → constater (**Analyser**) / optimiser à finalité égale
(**Améliorer**) / re-cibler pour un autre besoin (**Adapter**).

**Reclassements actés :**
- **Remédiation n'est PAS un type créé de zéro** → elle transforme l'existant →
  **ADAPTER** (avec Différenciation). Générée de zéro, elle serait indiscernable
  d'une Activité « plus facile » → sans valeur propre. C'est sa transformation de
  l'existant qui la justifie.
- **Différenciation n'est pas une simple « option »** → c'est une opération
  **ADAPTER** à part entière.

**Ne pas confondre les niveaux :**
- Les **verbes** (Créer/Analyser/Améliorer/Adapter) = familles d'outils (frères).
- Sous Créer/Activité, les **types de sortie** (QCM, fiche, mémo flash…) = enfants, pas frères.
- Les **options** de génération (avec/sans correction, nb de questions, visuels…) = réglages, pas des outils.

**Hors menu (à ne pas remonter au rang d'outil) :**
- Les fonctions « méta séquence » (versioning, affinage interactif, sortie JSON)
  ne sont PAS des entrées de menu → fonctions internes à l'écran Séquence.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Routes API principales

Source de vérité = `backend/routers/` (le code fait foi). Deux endpoints utilitaires, health et version, vivent à part dans `backend/main.py`.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Cycle vs Niveau — distinction absolue (ne jamais confondre)

**Un cycle et un niveau sont deux choses différentes.** Un **niveau** = une seule année scolaire (ex. la 4e). Un **cycle** = un **groupe de niveaux** (ex. le cycle 4 de l'EN = 5e + 4e + 3e). Le cycle **contient** des niveaux : c'est le **contenant**, le niveau est le **contenu**. Jamais l'un pour l'autre — surtout en codant (`cycle_id` ≠ `niveau_id`, requête « par cycle » ≠ « par niveau »).

Dans aSchool : table `cycles` = Crèche · Maternelle · Primaire · Collège · Lycée · Supérieur ; table `niveaux` = 6e, 5e, 4e, 3e, 2nde… (chaque niveau rattaché à un cycle). **Piège connu** : l'Éducation nationale appelle aussi « cycle » ses **cycles 1 à 4**, qui regroupent les niveaux **autrement** et **ne s'alignent pas** sur nos cycles (ex. la 6e est en cycle 3 EN mais dans notre cycle Collège).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Matière, variante, spécialité — trois distinctions, trois emplacements (règle absolue)

Trois questions différentes, à ne jamais confondre. Le test qui départage :

- **Ça duplique UNE matière au même niveau → variante.**
- **Ça change QUELLES matières existent → niveau.**

**1. Variante — la même matière apparaît deux fois au même niveau.**
Exemple : « Langue vivante » en 3e existe en A et en B en même temps. La matière ne se dédouble pas : une seule ligne canonique dans `matieres` (« Langue vivante »), et la variante est portée sur le couple, dans `matiere_niveaux.variante` (`NOT NULL default ''`, vide = pas de variante — même choix que `option_ab`). Index unique du couple = `(matiere_id, niveau_id, variante)`. Injection : table d'alias explicite (« Langue vivante A » → matière « Langue vivante » + variante « A »), jamais de devinette sur le libellé. Affichage prof : composer « nom + variante », sinon la matière sort deux fois à l'identique.

**2. Spécialité — elle décide quelles matières existent.**
Exemple : un BTS. « BTS 1re année » seul ne veut rien dire ; c'est la spécialité (CIEL…) qui sélectionne l'ensemble des matières. Ce n'est pas une variante d'une matière (la mettre en `variante` la répéterait partout — « CIEL » sur chaque ligne — et serait faux de sens). Sa place est le **niveau** : niveau = année + spécialité. C'est déjà la convention du référentiel (`NIVEAU = "BTS CIEL option A"`).

**3. Option A/B du diplôme — déjà gérée par `option_ab`.**
L'option A/B d'un même diplôme (ex. BTS CIEL option A / B) est taguée sur les chunks du référentiel (`referentiel_chunks.option_ab`, NOT NULL) et sert de filtre au RAG. On n'y touche pas, et on ne la remodélise ni en variante ni en niveau.

`variante` reste `''` partout, sauf les rares cas type Langue A/B — y compris pour tout le BTS.

(Décidé le 02/07/2026.)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

★★★━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━★★★
★★★                    BASES DE DONNÉES                    ★★★
★★★    (tout ce qui concerne les bases est regroupé ici)   ★★★
★★★━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━★★★

### Tables BDD (PostgreSQL — base `aschool`)

Source de vérité = `backend/models_db.py` (le code fait foi).

### La base "miroir" (règle absolue)

Trois bases, trois noms, à ne jamais confondre :
- aschool         = la vraie base de dev (les vraies données)
- aschool_test    = la base vide des tests automatiques (remise à zéro à chaque run, fausses données)
- aschool_miroir  = le miroir (une copie des vraies données de aschool)

La vraie base n'est jamais touchée tant que ce n'est pas prouvé sur le miroir.

Quand un travail a besoin d'une base pour être répété sans risque, Claude Code fabrique un miroir : un dump de la vraie base de dev, restauré dans une copie, avec les vraies données. On répète le travail sur le miroir, on vérifie qu'il marche, et seulement une fois prouvé sur le miroir l'admin (DEV) refait le geste (run.ps1) pour de vrai sur la vraie base. Ensuite, on jette le miroir.

Ce miroir n'est PAS `aschool_test` (la base vide des tests automatiques).

### Base vectorielle (PostgreSQL / pgvector) — Règle absolue

Les vecteurs du RAG vivent dans **PostgreSQL** (table `referentiel_chunks`, colonne `embedding` de type `vector` via **pgvector**) — **plus aucun dossier `chroma_db/`**, ChromaDB a été **retiré définitivement le 29/06/2026**. Comme toute base, c'est une **donnée GÉNÉRÉE**, pas du code : « données ≠ code ». Source de vérité = le **PDF du référentiel** (`REFERENTIELS/`) + le **script d'ingestion** (`backend/rag/pgvector_store.py`). Les vecteurs ne vivent **jamais dans git** (ils sont en base), **reconstruits au déploiement** via `python -m backend.rag.pgvector_store` (étape `[2.5/7]` de `deploy/deploy.sh`).

Prérequis d'ingestion : la table `referentiel_chunks` doit être **migrée** (Alembic) et la ligne `referentiels` du couple présente — sinon l'ingestion lève une **erreur claire** (jamais une base trouée en silence).

(Bascule pgvector actée le 29/06/2026 — éradication de ChromaDB : code, dépendance et dossier `chroma_db/` supprimés ; le moteur RAG est désormais PostgreSQL unique, cohérent avec « SQLite banni ».)

### Renvois — la base ailleurs dans ce fichier (elle reste à sa place utile)

- **Cluster PostgreSQL** (où il vit : `C:\Users\harketti\PostgreSQL\16`, port 5433 ; comment le démarrer / arrêter) → voir la **Règle de périmètre** (haut du fichier).
- **Ligne BDD de la stack** (psycopg, port 5433 ; garde-fou `backend/database.py` ; `aschool_test` via `conftest.py`) → voir le tableau **Stack technique**.

★★★━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━★★★
★★★                 FIN — BASES DE DONNÉES                 ★★★
★★★━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━★★★

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Variables d'environnement

Source de vérité = `.env.example` (le code fait foi). Secrets jamais affichés, jamais en base (cf. règle Secrets).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Streamlit est MORT — depuis le 24/04/2026

Streamlit a été abandonné définitivement le 24/04/2026. Le projet tourne sur **FastAPI + React**.

**Fichiers morts supprimés :**
- `app.py` — ancienne UI Streamlit (supprimé)
- `src/auth.py` — ancienne auth Streamlit avec magic links (supprimé)
- `.streamlit/secrets.toml` — config Streamlit (supprimé)

**Ce qui n'existe plus :**
- Magic links (remplacé par email token 60 min + JWT httpOnly cookies)
- `st.secrets` (remplacé par `os.getenv()`)
- `send_magic_link()` / `notify_admin_connexion()` (supprimées)
- `streamlit_cookies_controller`, `streamlit_mic_recorder` (supprimés)

**Règle absolue :** toute référence à Streamlit, magic link, `st.secrets`, `send_magic_link`, `notify_admin_connexion` trouvée dans le code ou la doc est du **code mort à supprimer immédiatement**, sans demander.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Gestion des emails

Tout ce qui concerne les emails est regroupé ici. Le détail complet (chaque
adresse, chaque fonction d'envoi) vit dans `MesMD/EMAILS.md`, à lire avant toute
modification email.

### Fournisseur
aSchool envoie ses emails via Infomaniak (`mail.infomaniak.com`, port `587`).
Ne jamais changer de fournisseur sans demande explicite.

### Connexion — le point qui nous a coûté cher
Pour se connecter au serveur d'envoi, Infomaniak refuse le mot de passe du
webmail. Il faut un mot de passe dédié, généré dans Infomaniak (Service Mail,
puis l'adresse, puis Appareils, puis Ajouter un appareil). C'est ce mot de passe
que l'on met dans le `.env`. Sans lui, la connexion est refusée avec l'erreur
« 535 Invalid login or password ».

### Où vivent les réglages
Toutes les adresses et le mot de passe vivent dans le `.env`. On ne les recopie
jamais dans ce fichier, jamais dans le code, et on ne les affiche jamais en clair.
Le compte de connexion et l'adresse d'expéditeur doivent être la même adresse,
car Infomaniak l'exige. Les emails d'aSchool sont **envoyés depuis** le domaine
aschool.fr (identité expéditrice). Seule exception : les alertes techniques
d'administration sont **reçues** sur `ADMIN_EMAIL`, qui reste une adresse afia.fr
par choix.

### Une seule porte de sortie
Tout le code d'envoi passe par la fonction `_smtp_send()` dans `backend/auth.py`.
Ne jamais ouvrir une connexion SMTP ailleurs.

### Qui reçoit quoi
Les emails aux profs (activation, bienvenue, mot de passe oublié) partent vers
l'adresse de chaque prof. Les notifications que l'administrateur lit (feedbacks,
nouvelles inscriptions) arrivent dans l'adresse `FEEDBACK_NOTIFY_EMAIL` du `.env`.
Les alertes techniques du serveur arrivent dans `ADMIN_EMAIL` du `.env`.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Auth — Ne pas toucher

L'auth JWT (bcrypt + python-jose, httpOnly cookies) fonctionne parfaitement depuis le 25/04/2026. Ne jamais modifier `backend/auth.py` ni `backend/routers/auth.py` sans demande explicite.

**Routes sensibles** (request-reset, resend-verification) : toujours retourner `{"status": "ok"}` qu'il y ait un utilisateur ou non — anti-énumération d'adresses email.

**Architecture profs :**
- Cookie `aschool_refresh` — JWT avec `type: "refresh"`, `sub: email`, `jti: session_key`
- Middleware `UserSessionMiddleware` crée une entrée `UserSession` à chaque requête prof

**Architecture admin :**
- Cookie `aschool_admin` — JWT avec `{"sub": "admin", "role": "admin"}` — sans `type: "refresh"`
- Le middleware NE crée PAS de `UserSession` pour l'admin
- Garde-fou `force-logout` : refus 403 si `user_email == ADMIN_EMAIL` (env var)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Déploiement VPS — Convention obligatoire

Toutes les applications web sont dans `/var/www/<nom-app>/` — standard Linux FHS.

| Application | Chemin | .env |
|---|---|---|
| aSchool | `/var/www/a-school/` | `/var/www/a-school/.env` |
| AFIA-FR | `/home/ubuntu/AFIA-FR/` ⚠️ | `/home/ubuntu/AFIA-FR/backend/.env` ⚠️ à migrer |

Ne jamais suggérer `/home/ubuntu/` pour un nouveau déploiement — toujours `/var/www/`.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Renommage — Règle de cascade obligatoire

Dès qu'un nom UI change (page, section, composant, route), produire dans la même réponse la liste complète des impacts : fichiers frontend, page IDs dans App.jsx, composants, routes backend, noms de fichiers. Demander si on traite maintenant ou si on note dans le TABLEAU DE BORD sous "En attente de cascade". Ne jamais clore la session sans que chaque impact soit traité ou noté.

### Remplacement / suppression — jamais de lien mort (règle absolue)

**Avant de remplacer A par B (ou de supprimer A), chercher dans TOUT le projet ce qui référence A. Si des liens vers A existent, on ne remplace pas tant qu'on ne les a pas traités (corrigés ou supprimés). Jamais de remplacement qui laisse des liens morts derrière.**

Corollaire (le BA-ba) : du nouveau qui remplace de l'ancien = on va d'abord chercher **tout** l'ancien et on le vire/corrige, dans le même geste — jamais du neuf posé par-dessus du périmé laissé traîner (c'est ce périmé qu'on relit ensuite par erreur).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Workflow obligatoire

Proposer → valider → coder → **tester en deux étages, dans cet ordre, jamais sautés** :

1. **Proposer** — analyser, proposer, attendre validation. Jamais coder sans validation explicite.
2. **Coder** — une tâche à la fois.
3. **Étage 1 — Claude teste, pour de vrai.** Avant toute affirmation, j'**exécute réellement** ce que j'ai produit, avec mes propres moyens (lancer le script, le test, le build, l'appel…). **Deviner est interdit** : « ça devrait marcher » n'est pas un test. Je ne dis « c'est bon, j'en suis sûr » **que si je l'ai exécuté et que j'en suis réellement sûr**. Si je ne peux pas l'exécuter, je le dis explicitement (« non testé ») — jamais de fausse certitude.
4. **Étage 2 — l'utilisateur teste derrière.** Une fois mon étage validé, l'utilisateur teste à son tour, en conditions réelles d'**admin ou de prof**, **chaque fois que c'est possible** (parfois aucun geste réel n'atteint le cas → on s'appuie alors sur l'étage 1 + les tests auto, et je le dis).

Deviner au lieu de tester = faute. (Règle durcie le 24/06/2026 : script de diagnostic committé sans avoir jamais été lancé, bug révélé seulement à la 1re vraie exécution.)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Vocabulaire — le mot « blocage / bloqué par » est banni (règle absolue)

Le mot **« blocage »** et la formule **« bloqué par »** ne doivent apparaître **nulle part** dans le projet (TRACKER, docs, code, commits, UI). Logique : un obstacle qu'on peut lever, on le lève tout de suite (règle du caillou) → ce n'est plus un blocage ; un obstacle qu'on ne peut pas lever maintenant est une **tâche en attente** qui part au backlog → pas un blocage non plus. Le mot n'a donc jamais lieu d'être.

Vocabulaire de remplacement, selon le sens :
- **« dépend de »** — dépendance technique entre deux tâches réelles du tracker (B a besoin que A soit fait d'abord).
- **« en attente de »** — la tâche attend un élément extérieur ou non encore planifiable (info admin, arbitrage non tranché).
- **« prérequis / impératif »** — condition dure avant une action (ex. avant `deploy.ps1`).
- **« désactiver » / « refuser » / « neutraliser »** — pour une action de code qui empêche quelque chose (un bouton, un insert). Jamais « bloquer ».

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Règles de conduite Claude — absolues

1. Pas de réponse hâtive — prendre le temps de lire avant de répondre.
2. Ne jamais présenter une supposition comme une certitude. Si l'info n'est pas connue : dire « je ne sais pas ».
3. Vérifier la doc officielle avant d'affirmer un fait technique. La doc fait foi, pas la mémoire.
4. Rester strictement dans le périmètre du bloc en cours. Une tâche = un bloc, pas de « tant qu'on y est ».
5. 🔒 Ne rien exécuter sans demande explicite — analyser, proposer, attendre validation.
6. Ne pas lire de fichiers locaux non fournis explicitement dans la tâche.
7. Une chose à la fois — traiter un point, le finir, passer au suivant.
8. 🔒 Tout point critique codé s'accompagne de son test automatisé, écrit dans la même session, sinon la fonction est inachevée.
9. 🔒 **Joignabilité AVANT la chaîne.** Pour toute affirmation « live / vert / fonctionnel », le **premier** contrôle est : *l'entrée est-elle exposée à l'utilisateur ?* (point d'entrée non gaté dans l'UI — pas `disabled`, pas « bientôt »). Seulement **après**, vérifier la chaîne de code. Un chemin de code qui marche mais que le prof ne peut pas atteindre n'est **PAS** fonctionnel — le dire « live » est faux. (Règle née le 14/06/2026 : « Consigne fonctionnel » affirmé sur la foi du backend, alors que la sidebar la masquait « bientôt ».)

10. 🔒 **La mémoire guide, elle ne prouve rien — tout ce qui vient de la mémoire se vérifie dans le réel AVANT d'être dit.** Je lis ma mémoire (et mes souvenirs de la conversation) uniquement pour m'orienter, jamais comme une vérité. Avant d'écrire quoi que ce soit — un fait, un « problème », un choix à trancher — je le confirme sur le réel (le fichier, une commande), la preuve sous les yeux. Sans preuve vérifiée, je n'en parle pas : ni supposition, ni « problème » soulevé de tête. Je pars du principe que je ne crois pas ma propre mémoire tant que le réel ne l'a pas confirmée. (Règle née le 06/07/2026 : j'ai théorisé de mémoire un faux problème de balisage PDF contre `.md`, au lieu d'extraire le texte une seule fois pour voir qu'il était propre — une heure perdue à débattre d'un souci qui n'existait pas.)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Synchronisation afia.fr — Règle absolue

À chaque push **MINOR ou MAJOR**, appliquer cette procédure :

**Claude (session aSchool) :**
1. Générer automatiquement le contenu complet et mis à jour de `School.jsx` reflétant l'état réel de l'app en production
2. Le produire prêt à coller — bloc JSX complet, rien à reformater

**Utilisateur (session AFIA-FR, à chaud après le push) :**
1. Ouvrir `D:\AFIA-FR\frontend-web\src\pages\School.jsx`
2. Remplacer le contenu par le bloc généré par Claude
3. Déployer AFIA-FR

**Ne pas modifier AFIA-FR depuis ce projet.** Claude produit, l'utilisateur applique.

PATCH = aucune action requise.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Nom du produit — aSchool

Le nom du produit s'écrit **aSchool** : un « a » minuscule et un « S » majuscule. On ne l'écrit jamais « ASchool ».

**Choix de marque.** aSchool est présenté aux utilisateurs comme un logiciel pédagogique, jamais comme « une IA ». Dans tout ce que voit l'utilisateur (les écrans, les textes, les boutons, les messages), on n'affiche jamais les mots « IA » ni « intelligence artificielle ». Cette règle concerne seulement ce que voit l'utilisateur. Elle ne concerne pas les documents internes comme ce fichier, le code, ou les messages de commit.

**Ressources graphiques (hors projet — ne pas modifier depuis ici) :**
- Charte graphique : `D:\A-PUB\PUB_ASCHOOL\PLAN_CAMPAGNE-ASCHOOL\Charte_Graphique.md`
- Brief logo principal : `D:\A-PUB\PUB_ASCHOOL\PLAN_CAMPAGNE-ASCHOOL\Logo_aSchool.md`
- Brief logo vertical : `D:\A-PUB\PUB_ASCHOOL\PLAN_CAMPAGNE-ASCHOOL\Logo_Vertical.md`
- Brief icône carrée : `D:\A-PUB\PUB_ASCHOOL\PLAN_CAMPAGNE-ASCHOOL\Icone8carre.md`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Bulles d'aide — Règle absolue

Tout bouton, lien d'action ou icône cliquable doit avoir un attribut `title="..."` décrivant ce qu'il fait. Sans exception. Vérifier également que le texte est lisible : `color: white !important` sur tout fond foncé.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Incohérences & erreurs de saisie — modale bloquante (règle absolue, toute l'app)

**Toute incohérence ou erreur de saisie = boîte de dialogue bloquante qui explique le problème en langage humain et force la correction. JAMAIS un avertissement passif inline.**

Un marqueur passif (étiquette grise à côté d'un champ, texte « à mettre à jour », badge discret) **n'est pas un garde-fou** : c'est un raisonnement de machine (« je signale »). L'humain ne le lit pas, ne comprend pas qu'il doit agir, ferme la page — et reste dans un état faux que le système l'a **laissé** créer. Un logiciel sérieux **arrête** l'utilisateur et **l'oblige** à corriger.

Donc, à chaque fois qu'un état devient incohérent ou invalide :
1. **Modale** (overlay plein écran, impossible à ignorer) — réutiliser `showError()` de `frontend/src/errorDialog.js`, rendu par `App.jsx`.
2. **Message en langage de l'utilisateur** (prof) : dire le **problème** ET l'**action attendue**. Pas de jargon, pas de « mettre à jour ».
3. **Forcer la correction** : neutraliser la valeur fautive et **bloquer l'action principale** (bouton désactivé) tant que l'état n'est pas redevenu cohérent. Pas d'échappatoire.
4. Pour un cas important, ne pas hésiter à être **très explicite**, quitte à enchaîner deux confirmations.

**Cas fondateur (12/06/2026) :** `MonProfil.jsx` — matière du profil incohérente avec le niveau choisi (ex. « Français » + « Master »). Déclenchée **à l'ouverture** (profil hérité) ET **à chaque changement de niveau**, modale + matière vidée + `Valider` bloqué (`profilPretAValider`, `utils/profil.js`). C'est le patron à répliquer partout.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Pilotage — deux docs, deux rôles, un seul pilote par couche (règle absolue)

**Deux documents vivants, jamais deux pilotes qui se contredisent :**

| Document | Fait foi sur | Pour qui |
|---|---|---|
| `MesMD/TRACKER.md` | **Pilotage** — ordre + statut (☐ 🔄 ⏸️ ✅) + dépendance en clair | l'utilisateur (vue lisible d'un coup d'œil) |
| `MesMD/TABLEAU-DE-BORD.md` | **Détail** — score, description, synergies, audits, RAG + **journal FAIT** | Claude (référence de fond) |

> **Règle de tenue (absolue) :** Le TRACKER fait foi sur le pilotage (ordre + statut + dépendance). Le TABLEAU fait foi sur le détail (score, description, journal FAIT). Le statut est mis à jour dans le TRACKER, dans la même réponse où l'on démarre ou finit une tâche. Le tableau est synchronisé en fin de session, pour le journal FAIT seulement.

> Les fiches `MesMD/BOUSSOLE/Dxx.md` restent la **couche détail** d'un chantier.

- **Le statut vit à UN SEUL endroit : le TRACKER.** Le tableau de bord ne porte plus de colonne « État ». Garder un statut des deux côtés recrée le double pilote — interdit.
- **L'ordre appartient à l'utilisateur** (priorité P1/P2/P3 dans le TRACKER) ; **les dépendances techniques à Claude**, écrites noir sur blanc dans le TRACKER et **prouvées en citant la fiche** — jamais gardées de tête.
- **Aucun autre document ne ré-ordonne les priorités.** Tout plan, diagnostic ou audit ponctuel est **absorbé** en chantier `Dxx` (détail dans le TABLEAU) — jamais un pilote concurrent.
- **Toute idée mentionnée en session → notée immédiatement dans le réservoir du `TABLEAU-DE-BORD.md`**, dans la même réponse. Quand l'utilisateur décide de l'attaquer, elle remonte en une ligne dans le TRACKER.
- **Les checklists de chantier ☐/☑** vivent dans les fiches `Dxx`.
- **Pas de doc-archive dans l'arbre de travail.** Les anciens états (vieux CR, plans clôturés) vivent dans l'**historique git**, pas dans un fichier vivant. Ne jamais recréer de document d'archive dans l'arbre. Claude ne consulte l'historique git **que sur demande explicite** — un état daté lu spontanément induit en erreur (c'est ce piège qui a motivé la règle).
- **Périmètre de lecture = `main` uniquement.** Le contenu des autres branches (ex. `wip/deepgram-streaming` = chantier Deepgram gelé) n'est jamais lu spontanément — c'est du git, donc lecture **sur demande explicite** seulement. Mes outils par défaut ne voient que le checkout courant ; je ne lance pas de commande git large (`git grep --all`, `git log --all`, checkout d'une autre branche) de moi-même.
- **Durable → `CLAUDE.md` ; les trackers ne portent que l'éphémère.** Toute information qui doit rester **pérenne** (décision d'architecture, règle, choix techno durable) vit dans **`CLAUDE.md`** (et/ou la mémoire Claude) — **jamais seulement dans un tracker**. Les trackers de **chantier** (`TRACKER_REFORME.md`, `TRACKER_FOURNISSEURS_IA.md`…) sont **jetables** : une fois le chantier fini, archivés/supprimés. **Nuance : `TRACKER.md` et `TABLEAU-DE-BORD.md` sont des docs de pilotage *vivants/continus*** — ils ne sont pas jetés, **mais n'hébergent pas non plus une décision pérenne** : leur rôle est le pilotage/détail **courant**, pas la mémoire durable. Un tracker peut **pointer** vers la décision dans `CLAUDE.md`, jamais en être l'unique dépositaire.

### Le cycle de vie d'une idée (du berceau au rangement)

Une idée **naît dans la discussion** et se travaille dans un **tracker éphémère**
(son berceau) : on l'ancre, on la pèse, on la mûrit tranquillement. **Tant qu'elle
est une idée, elle reste dans l'éphémère — elle ne touche rien d'autre** (ni TRACKER,
ni tableau de bord, ni fiche).

Quand elle est **mûre et validée par l'utilisateur**, elle n'est plus une idée :
c'est un **travail**. Là seulement elle s'éclate dans les documents permanents :
- **TRACKER** → une ligne simple et humaine, le jour où on décide de la faire
  (ce que l'utilisateur suit).
- **Fiche Dxx (BOUSSOLE)** → tout son détail technique.
- **Tableau de bord** → elle apparaît dans l'inventaire des travaux, avec un lien
  vers sa fiche.

Si ce qu'on a tranché est une **règle durable** (pas une tâche) → elle va dans
**`CLAUDE.md`**, jamais dans un tracker.

Le tracker éphémère, une fois vidé de cette idée, **finit à la poubelle**
(historique git).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Cadence de travail — une ligne du TRACKER par session (règle par défaut)

**Par défaut : une session = une ligne du `TRACKER.md`.** On finit et on
committe une ligne avant d'attaquer la suivante — jamais plusieurs en
parallèle. C'est ce qui garde le statut du TRACKER honnête (rien à moitié fait).

Deux exceptions, **jugées par Claude au moment d'« attaquer XX »,
signalées AVANT de coder, tranchées par l'utilisateur** :
- **Ligne minuscule** (cosmétique, ~30 min) → Claude propose de la regrouper
  avec la ligne voisine.
- **Gros chantier** (plusieurs semaines) → Claude propose de le découper en
  plusieurs sessions.

**Découpage d'un gros chantier — « stable » n'est pas « fini » :** chaque
sous-session se clôt sur un état **stable et committable** (le code tourne,
rien de cassé, c'est committé), pas forcément sur la feature entière livrée.
On ne laisse jamais de code cassé entre deux sessions, mais on ne s'impose
pas de tout boucler en une fois — intenable sur un chantier de semaines.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Règles UI permanentes

- **Profil = source unique** pour matière et niveau. Jamais de `<select>` matière/niveau dans les features — toujours lire depuis le profil.
- **Aucune liste de référence en dur dans le frontend.** Les matières — et toute liste de référence (niveaux, cycles…) — se lisent depuis la base via l'API, jamais une liste codée en dur dans un composant. Pour les matières : hook `useMatieres` → `GET /api/matieres`. Une liste en dur se périme en silence le jour où la donnée bouge. (Règle née 15/06/2026, P5.10 : 8 écrans dupliquaient la même liste de 12 matières.)
- **Bouton d'action principale** = classe `btn-primary` + icône SVG + `title=` tooltip + positionné en bas à droite. Référence : bouton "Générer l'activité" dans `App.jsx` (écran « Créer une activité »).
- **Header** : `height: 65px`, `overflow: hidden`. **Logo** : `height: 140px`. INTOUCHABLES.
- **Tagline** "Générateur d'activités pédagogiques" = `<span>` HTML blanc dans le header, toujours présent, jamais dans le PNG seul.
- Pas d'emojis dans l'interface.
- Navigateur de référence : **Edge** (jamais Chrome dans les instructions).
- **Menu / navigation = du général au détaillé.** Tout menu se range en **familles (catégories) → options**, jamais une liste à plat où l'on ajoute une entrée de plus à chaque page. Toute nouvelle page se loge **sous une famille existante**. Standard pro appliqué au back-office le 23/06 (5 catégories + accordéon repliable, chevron visible, hiérarchie de tailles titre>option, liseré **bleu = section active** / **bordeaux #A63045 = page active**, shell figé sidebar+header+footer, header = fil d'Ariane « catégorie › page »). Même esprit que la taxonomie outils prof (« ne pas confondre les niveaux »).
- **Dans une page admin : maître-détail, jamais une rangée d'onglets en haut.** Les sections d'une page se rangent en **liste verticale à gauche** (l'item actif porte le liseré bordeaux `#A63045`), et le **détail s'affiche à droite**. Une rangée d'onglets en haut ne tient pas quand le nombre de sections grandit : elle déborde et devient inutilisable. Référence du motif : la liste des modèles de l'écran des mails (`AdminParametresEmail.jsx`) et l'écran Programmes (passé en maître-détail). Appliqué à l'écran Génération LLM le 08/07/2026.

### Layout général

Shell figé : **header + sidebar + contenu + footer**. Le menu réel (source de vérité) = `frontend/src/components/Sidebar.jsx` — ne pas le recopier ici (il dérive).

### Couleurs

| Rôle | Valeur |
|---|---|
| Bordeaux accent | `#A63045` |
| Bordeaux hover | `#832538` |
| Bleu primaire | `#1F6EEB` |
| Bleu hover | `#1558C0` |

### Classes boutons

| Classe | Usage | Style |
|---|---|---|
| `btn-primary` | Action principale (Générer…) | Bleu, blanc, icône SVG + texte |
| `btn-action` | Actions secondaires (Fichier, Dicter…) | Gris `#E5E7EB`, bordure, icône SVG + texte |
| `btn-secondary` | Télécharger, Fermer… | Blanc, bordure, icône SVG + texte |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Responsive mobile — Règle PWA

Toute adaptation mobile utilise `const isMobile = window.innerWidth < 768` défini localement dans chaque composant. Ne jamais casser le layout desktop (> 768px). Patterns établis :
- Sidebar : `useState(() => window.innerWidth < 768)` → repliée par défaut sur mobile
- Header : tagline masquée, matière sous le nom, bouton "Déconnecter" raccourci
- Grilles `1fr Xpx` → `1fr` sur mobile
- Boutons hover-only → toujours visibles sur mobile (`isMobile || hovered`)
- Longs blocs tutoriel/aide → masqués sur mobile (`!isMobile`)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Fournisseur IA — Règle absolue

Deux fournisseurs, pour pouvoir basculer de l'un à l'autre : **Groq** (`llama-3.3-70b-versatile`) par défaut + **Anthropic** (Claude) comme cible de bascule. Gemini n'est **pas** banni — l'adaptateur `_gemini` existe et reste fonctionnel, mais **dormant** : ni défaut, ni cible.

**L'app appelle l'IA dès qu'elle en a besoin — un seul point d'entrée `generate()`.** Y compris pour préparer un référentiel (analyser le PDF, proposer la règle de découpe). Règle : l'IA **propose**, l'admin ou le prof **valide** ; jamais l'IA seule (cap « aSchool n'invente rien »). Le fournisseur est **administrable à chaud** (écran Génération LLM → onglet Fournisseur) ; la combo affiche **tous** les fournisseurs connus, les non-opérationnels **grisés « pas encore disponible »** (jamais un choix qui échoue). Vision : basculer entre plusieurs IA selon l'usage (réservoir item #45). Aujourd'hui **Groq seul** est opérationnel ; ouvrir une 2e IA (clé par fournisseur + modèle Claude) est un chantier **en attente de la décision « quelle IA + quel accès (clé API ou abonnement) »**.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Modèle d'embedding (RAG) — décision (cap « le meilleur »)

Le modèle d'embedding transforme le texte en vecteurs pour la recherche RAG. Il est défini dans `backend/rag/embeddings.py` (constante `EMBEDDING_MODEL`), et sert **à l'ingestion ET à la recherche** (le même des deux côtés, sinon les scores sont faux).

- **Phase actuelle (local, CPU) : BGE-M3 (`BAAI/bge-m3`)** — 1024 dimensions, open-source, licence MIT, gratuit, tourne sur CPU sans carte graphique. Meilleur modèle atteignable aujourd'hui sans GPU.
- **Cible du produit commercialisé : Qwen3-Embedding-8B** — n°1 des benchmarks, meilleur en français. À activer quand la machine de production aura un GPU (8 milliards de paramètres, ~5 Go quantifié, trop lourd pour du CPU seul).

On n'abandonne pas Qwen3 : c'est le sommet visé. BGE-M3 est le meilleur sans GPU, pas un renoncement. Le petit modèle historique (paraphrase-multilingual-MiniLM, 384 dim) était sous la barre du cap et est remplacé.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Aide — Règle absolue

**Le signal, c'est le COMMIT.** Un bloc est bouclé quand il est committé et qu'on n'y touche
plus. L'aide se rédige à la maille du **bloc committé** — jamais à la brique interne (1a/1b,
un endpoint, un bout de front que l'utilisateur ne voit pas encore). Documenter un rouage
invisible n'a pas de sens ; c'est ce qui faisait rater la règle.

**Règle : Aide + commit, dans le même geste.** Aucun commit qui clôt un bloc sans que son aide
soit écrite et incluse dans ce même commit. Au moment de committer, je vérifie « son aide
existe-t-elle et est-elle à jour ? » — si non, je l'écris avant de committer. Contrôle
accroché au commit, pas un pari sur la mémoire.

**Portée** : aide **admin** dans `AdminAide.jsx`, aide **prof** dans `Aide.jsx`, selon qui
utilise la fonction. Si le bloc **modifie un comportement déjà documenté**, on **corrige
l'aide périmée** dans le même commit — jamais laisser une aide qui décrit l'ancien
fonctionnement.

On ne diffère **jamais** l'aide « à la fin de l'application » : ce serait laisser l'aide fausse
pendant des mois et tout concentrer en une passe où l'on oublie le plus.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

★★★━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━★★★
★★★       MÉTHODE RÉFÉRENTIEL (RAG) — EN VIGUEUR           ★★★
★★★    (fait foi ; l'ancienne méthode est MORTE)          ★★★
★★★━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━★★★

Cette section fait foi sur la façon dont un référentiel est **découpé, indexé et cherché**. Toute autre méthode (l'ancienne) est **morte** : on ne raisonne plus jamais dessus. Si un vieux réglage traîne quelque part (code, doc, commentaire), on le **SIGNALE** — on ne l'applique pas.

1. **Découpage : 1 unité de contenu = 1 chunk.** La frontière de chunk est la frontière d'une **unité du document**, définie par la routine du document : une **fiche** (BTS) ou une **activité** (crèche 0-3 : le titre d'activité, la ligne juste au-dessus de la ligne « Âge »). Jamais de coupe à taille fixe. → L'ancien découpage **à 900 caractères aveugle est ABANDONNÉ** (il coupait au milieu d'une unité et collait la queue de l'une sur la tête de la suivante).

2. **La matière n'est PAS taguée dans le document — elle est trouvée par le SENS.** Un document peut ranger son contenu par un autre axe que la matière (le 0-3 crèche est rangé par activité et par âge, et une activité « *développe aussi* » plusieurs compétences). La matière du prof est rapprochée du texte de l'unité par l'embedding (requête `{matiere}`/`{niveau}`), jamais par une étiquette « Matière : ». → L'ancienne règle « 1 activité = 1 matière, sans développe aussi » est **ABANDONNÉE** (elle servait l'ancien découpage par taille).

3. **Modèle d'embedding : BGE-M3 (1024 dim)**, le même à l'ingestion ET à la recherche. **MiniLM (384 dim) est ABANDONNÉ.** Détail + cible future (Qwen3) → section « Modèle d'embedding (RAG) » ci-dessus.

4. **La matière ne figure pas comme étiquette dans le chunk.** Sous l'ancien modèle, chaque chunk s'ouvrait sur sa ligne « Matière : … » → **ABANDONNÉ**. Désormais la matière est portée par le **contenu** de l'unité (ses objectifs nomment les compétences) et retrouvée par le sens ; seul le **critère de tri propre au document** (option A/B, âge…) est tagué sur le chunk.

Repère code : l'extraction propre au document renvoie une « page » autonome par unité (crèche 0-3 : `backend/rag/referentiels/creche_0_3_ans.py`, une page par **activité**, la ligne « Âge » remontée en tête comme marqueur) ; le chunker générique (`backend/rag/chunker.py`) en fait un chunk par unité.

### Architecture : socle commun + routine par document (+ analyse amont)

**Un socle commun, une routine par document.** Le moteur RAG (client, embedding, découpage générique, recherche) **ne connaît aucun référentiel** : c'est le socle, commun à tous (`backend/rag/referentiels/__init__.py`). Au-dessus, **chaque document a sa routine** (une « fiche » : `creche_0_3_ans.py`) qui sait lire CE document et poser SON critère de tri. **La maille est le document, pas le cycle** : un même document peut servir plusieurs niveaux — le 0-3 crèche sert Bébés, Moyens et Grands, d'où 3 collections pour 1 seule fiche. Ajouter un cycle plus tard, c'est écrire une nouvelle routine, sans toucher aux autres.

**Le squelette de la procédure est universel — une seule chose change d'un document à l'autre.** Ajouter n'importe quel référentiel suit la même suite d'étapes (choisir le couple, déposer le PDF, le lire, découper, rattacher au niveau, arbitrer le flou, filtrer, vectoriser, ingérer, calibrer le seuil, tester, valider, basculer, nettoyer, activer). Ce qui change selon le document, c'est **uniquement** le **découpage** (où sont les frontières d'une unité) et le **rattachement au niveau** (quel critère trie le document) — ces deux étapes vivent dans la **fiche** (`backend/rag/referentiels/<doc>.py`), jamais dans le socle. Tout le reste est du **socle commun**, réutilisé tel quel. Ajouter un référentiel = écrire **UNE** fiche, sans toucher au squelette ni au moteur. *(Le guide de reprise éphémère détaille cette suite en 16 étapes, dont seules les étapes 5 « découper » et 6 « rattacher » sont propres au document.)*

**Code d'un côté, donnée de l'autre.** Le parsing du PDF (colonnes, frontières d'activité) est du **code** propre au document, légitimement en dur. Mais les **valeurs métier** — tranches d'âge, option A/B, seuil — sont de la **donnée** : elles vivent en base (`referentiels.filtres`, `SCORE_MIN`), jamais écrites en dur dans le code.

**L'analyse amont — une étape AVANT le découpage.** Avant de découper, on analyse le document, dans deux buts : repérer le **critère** qui le structure (l'axe de filtre : option A/B, âge…), et détecter les **cas flous** qui casseraient le découpage. L'outil fait environ 90 % seul (lire, trier les cas nets, isoler les flous) ; l'humain tranche les 10 % flous. **Règle absolue : sur un cas flou, l'outil ne décide jamais seul en silence — il signale et attend l'arbitrage** (cap « aSchool n'invente rien »). L'analyse produit le critère rangé en base et un document assaini, prêt au découpage. Menée aujourd'hui par le **dev** (prototype) ; cible = **fonction de l'app**, l'admin arbitrant le flou à la place du dev. On la bâtit donc **portable** — fonction pure et testable — jamais jetable.

> Procédure d'exécution complète (dépôt jusqu'à la recherche) et application à la crèche : fiche `MesMD/BOUSSOLE/D60.md`.

### La règle de découpe — validée par l'admin, deux faces, PAR COUPLE (règle absolue)

Comment un document est **découpé** (où sont les frontières d'une unité) est piloté par une **règle de découpe** — un petit objet à **deux faces**, rangé **par couple**, à côté du PDF : `REFERENTIELS/<CYCLE>/<NIVEAU>/regle-decoupe.json`.

- **Deux faces.** `explication_clair` = ce que **l'admin lit** pour valider, en français, sans code (« une unité = une activité, elle commence à chaque ligne d'âge »). `critere_technique` = le **motif** (regex) que la **fiche** exécute pour trouver les frontières. Les deux disent la même chose : l'une pour l'humain, l'autre pour la machine. L'admin valide **toujours** sur la face claire, jamais sur le code.
- **Par couple, jamais par cycle.** Un niveau = un référentiel = un document = **sa** règle. La règle vit dans le dossier du couple (comme le PDF, comme `matieres-candidates.json`), résolue par **cycle + niveau**. Jamais une règle unique posée au niveau du cycle : deux documents d'un même cycle (ex. deux spécialités BTS) se découpent différemment. *(Même pour la crèche, dont les 3 niveaux partagent le même document, le code voit 3 référentiels distincts → 3 fichiers de règle.)*
- **Garde-fou — pas de découpage sans règle validée.** Le champ `valide` doit être `true` : la fiche **refuse d'ingérer** (lève) si la règle est absente ou non validée (cap « aSchool n'invente rien »). La fiche lit le motif **du fichier validé**, plus aucun regex en dur.
- **Deux sens (le champ `depose_par`).** Sens 1 (branché) : le **dev propose** la règle, l'**admin Valide/Rejette**. Sens 2 (pas encore branché) : l'**admin propose** lui-même sa règle, le **dev vérifie**. Le champ `depose_par` (`"dev"`/`"admin"`) anticipe déjà les deux sens.

Repère code : la fiche crèche dérive le chemin de la règle du dossier du PDF (`_regle_path_for(pdf_path)`), lit + compile le motif validé (`_charger_motif_valide`), et lève si non validé (`backend/rag/referentiels/creche_0_3_ans.py`). Endpoints admin (lire / valider / rejeter / aperçu) résolus par cycle + niveau (`backend/pedagogie/referentiels_admin.py`).

### Ajouter un nouveau référentiel — quels acteurs on touche

| Acteur | On y touche ? | Pourquoi |
|---|---|---|
| **Modèle** | Non | Global (BGE-M3), un seul pour tous — on le réutilise, on ne le refait pas. |
| **PDF (extraction + contenu)** | **Oui** | Par référentiel : son PDF, son extraction/découpage, son contenu de fiches. La *méthode* (1 fiche = 1 chunk) est réutilisée ; l'extraction propre au document et le contenu sont neufs. |
| **Requête** | Non | Gabarit global (`{matiere}`/`{niveau}`), s'applique à tout couple sans y retoucher. |
| **Seuil** | **Oui** | Par référentiel (`get_fiche(collection).SCORE_MIN`), à recalibrer : il dépend de la distribution des scores de ce PDF-là. |

Règle de lecture : **Modèle + Requête = leviers globaux** (bâtis une fois) ; **PDF + Seuil = par référentiel**.

### Immuabilité de la structure d'un référentiel — casser et régénérer, jamais migrer (règle absolue)

La structure d'un référentiel — les cycles, les niveaux, et le **tri par niveau fait à l'ingestion** (chaque collection ne reçoit que le contenu de son niveau) — est **immuable** et n'est pilotée par **aucun champ configurable**. Le **seul intrant qui bouge est le PDF** : on le remplace, on ré-ingère, c'est tout.

Si un jour la **structure elle-même** doit changer (par exemple la crèche passe à 0-4 ans, donc un niveau de plus), on **ne migre pas** et on **ne rustine pas** : on **casse la génération existante et on la reconstruit entièrement** par ré-ingestion — geste **automatique**.

C'est pour cela qu'on **ne touche jamais à la base** pour ce filtrage : **aucune colonne ajoutée, aucun champ de règle**. La règle « quel contenu appartient à quel niveau » vit dans le **code de la fiche** (elle reçoit le niveau en paramètre et ne renvoie que le bon contenu), **jamais dans la donnée**. Le niveau est déjà tenu de bout en bout du flux admin (l'admin choisit cycle + niveau au départ) : on le passe, on ne le stocke pas en plus. Corollaire : l'isolement par niveau est **structurel** (le mauvais contenu n'est même pas dans la collection), pas un filtre conditionnel qu'on pourrait oublier à la recherche.

★★★━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━★★★
★★★             FIN — MÉTHODE RÉFÉRENTIEL (RAG)            ★★★
★★★━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━★★★

## Référentiel = source de vérité unique (règle absolue)

Le **référentiel officiel** du couple matière+niveau est **LA source de vérité**. **Un couple sans référentiel ne génère pas** : il reste « en construction ». La génération (`/api/generate`) **doit s'ancrer sur le référentiel du couple** — décision tranchée le **26/06/2026**, **pas encore branchée** : aujourd'hui seul le bouton « Tester un exemple » (`/api/exemple-referentiel`) lit le référentiel ; `/api/generate` n'en lit **aucun** (le niveau n'est qu'une étiquette dans le prompt).

Intégrer un nouveau couple suit la procédure de [`REFERENTIELS/README.md`](REFERENTIELS/README.md) : l'admin choisit cycle+niveau dans des **combos** (liste fermée) → aSchool génère le **dossier-clé** = nom du niveau normalisé en `MAJUSCULES_UNDERSCORE` (ex. `BEBES_0_1_AN/`, unique et non renommable) → **l'admin fournit lui-même le PDF** (par lien ou dépôt) → l'admin **valide** → découper / **relier** / tester. *(3e mode « Par IA » — **chantier acté le 08/07/2026** : l'app fait une **vraie recherche web** pour trouver la source **officielle** du couple ; l'IA trie et vérifie de **vrais liens**, jamais un lien inventé de mémoire ; officiel non trouvé → ne propose rien ; l'admin valide toujours. Requiert une **capacité de recherche web** — décidée, **pas encore branchée**.)* Deux preuves distinctes : « le bon référentiel remonte » (indexation) ≠ « la génération s'appuie dessus » (cœur).

**Reste à faire (chantier à part) :** « automatiser le Temps 3 » — routage couple→référentiel **data-driven** (aujourd'hui en dur dans `exemple_referentiel.py`) **+ branchement du cœur** `/api/generate`.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Procédure — un couple devient utilisable : de l'admin au prof (règle absolue)

**Principe fondateur.** aSchool ne génère rien sans référentiel officiel. La seule condition pour générer, c'est qu'un référentiel existe pour le couple du prof : son cycle, sa matière, son niveau.

**Le déclencheur.** Un prof appelle l'admin. Exemple : une animatrice de crèche dit qu'elle est en cycle Crèche, niveau Bébés (0-1 an), matière Développement affectif, et demande si elle peut utiliser aSchool. L'admin répond qu'il s'en occupe.

**Côté admin — préparer le couple.**
1. Les 11 cycles et les 88 niveaux existent déjà en base. On n'en crée pas.
2. Les matières du niveau doivent être présentes en base et reliées au niveau. On les remplit depuis le fichier des matières avec un script éphémère (créer, remplir, supprimer).
3. L'admin ouvre aSchool, va dans Paramètres puis Référentiels. Il choisit le cycle, puis le niveau.
4. Il dépose le PDF du référentiel officiel et valide. C'est ce dépôt qui rend le couple utilisable.

**Ce qu'on fait du PDF (deux choses).**
1. Le texte est extrait et rangé, et la provenance est enregistrée dans la table des référentiels.
2. Le PDF est découpé en extraits (les chunks) et vectorisé, pour que la génération puisse s'appuyer dessus.

**Le drapeau (dans le code, pas dans les tables).**
1. À la connexion du prof, le code pose un drapeau vrai ou faux.
2. Il est vrai si un référentiel existe pour le couple du prof : cycle, matière, niveau. Sinon il est faux.
3. Ce drapeau vit pendant toute la session du prof, dans cet état.
4. C'est le même drapeau partout. Tout ce qui s'appuie sur le référentiel s'y réfère.

**Côté prof — ce qu'il vit.**
1. Le prof se connecte librement dès qu'il a une matière et un niveau. On ne le bloque jamais à l'entrée.
2. Il peut se promener partout : accueil, centre d'aide, mon réseau, mon profil, mes feedbacks, mes stats, l'historique de ses activités.
3. Tout ce qui utilise le référentiel dépend du drapeau. Ce qui utilise le référentiel, ce sont ses extraits, les chunks. Si le drapeau est faux, on affiche un message clair qui dit qu'il n'y a pas encore de référentiel pour ce niveau, et rien n'est généré. Le reste, qui n'utilise pas le référentiel, reste ouvert.

**Portée dans le temps — défini maintenant, appliqué au fur et à mesure.** On pose ce garde-fou maintenant, on l'applique à mesure que les outils sont branchés sur le référentiel. Aujourd'hui, un seul élément côté prof utilise le référentiel : « Tester un exemple », et il se protège déjà tout seul (pas de référentiel, il répond indisponible et n'invente rien). « Créer une activité » et les autres outils ne lisent pas encore le référentiel. Ils dépendront du drapeau une fois branchés sur les chunks. C'est un chantier à part.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Gérer les matières d'un référentiel — écran admin, mode DEV (procédure + règle absolue)

**Où, et nulle part ailleurs.** On ajoute, modifie ou supprime une matière **uniquement** sur
l'écran admin, en dev, dans le contexte d'un couple Cycle → Niveau déjà choisi. Aucun autre
endroit de l'app ne touche aux matières.

**Qui lit le référentiel.** aSchool a le droit d'appeler l'IA (Groq) pour préparer un référentiel :
c'est le même appel unique `generate()` qui sert déjà à générer les activités. Principe (cap) :
l'IA **repère / propose**, l'admin **valide**, jamais l'IA seule. **État au 08/07/2026** : cette
analyse (extraire/filtrer les matières) est **encore faite en DEV par Claude** (sur Max) et rangée
dans un fichier que l'app lit (`matieres-candidates.json`) ; la faire faire **par l'app via Groq**
est la **cible, pas encore branchée**. Les étapes 4 à 6 (comparer, afficher, enregistrer) restent
de l'app pure, sur les données déjà en base.

**Les étapes.**
1. Lire le PDF du référentiel (dans `REFERENTIELS/<CYCLE>/<NIVEAU>/`).
2. Extraire la liste des domaines/fiches.
3. Filtrer : garder ce qui est une matière vécue par l'enfant (langage, jeu, arts, alimentation…),
   écarter le pro/institutionnel (relation aux parents, management, procédures…).
4. Comparer la liste filtrée avec la base (matières déjà reliées à ce niveau).
5. Afficher une **table en ligne** (sous la zone PDF de l'écran Référentiels) avec la liste filtrée
   + cases à cocher :
   - matière déjà en base pour ce niveau → **case cochée figée** (rien à faire ; pour l'enlever,
     passer par « Retirer ») ;
   - matière absente → **non cochée** → l'admin coche celles à ajouter ;
   - sur cet écran, l'admin peut aussi **ajouter** une matière à la main (ex. donnée par un prof,
     non détectée), **renommer** un libellé, **retirer** une matière.
6. Un **seul bouton** (« Récupérer » = « Valider », même sens) : enregistre en base le
   **coché-ET-nouveau** (jamais de doublon : on réutilise la matière existante), puis affiche un
   bilan (ex. « 3 ajoutées, 7 déjà présentes »).

**Source de la table (pas de bricolage).** La liste filtrée produite par Claude en dev est rangée
dans un vrai fichier du référentiel — `matieres-candidates.json`, à côté de `extraction-texte.txt`
dans `REFERENTIELS/<CYCLE>/<NIVEAU>/` — que l'écran lit pour remplir la table. Ni collage, ni
endpoint bricolé : un fichier qui part en prod avec le reste.

**Sécurité (à ne jamais casser).** Les liens (niveaux, profs, chunks) référencent la matière par
son **ID** : un renommage garde l'id et ne casse rien (mais le libellé change partout où la matière
est partagée entre niveaux). On ne laisse **jamais** une matière orpheline. Une suppression =
**désactivation** (historique conservé), jamais un effacement dur ; si elle touche un prof ou un
chunk qui l'utilise, **prévenir AVANT** (modale), ne rien casser en silence.

**Règle à graver — on fige après validation.** On règle les matières d'un couple Cycle → Niveau
**en une seule fois, à fond**, au moment où on le traite. Une fois **Validé, c'est FIGÉ** : on n'y
touche plus. Une modification ultérieure (ajouter/renommer/retirer plus tard) reste **possible** —
uniquement par l'admin, en dev, sur cet écran, dans ce contexte — mais elle est **exceptionnelle,
une porte de secours**, pas un usage courant.

(Procédure + règle actées le 03/07/2026.)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Secrets — Règle absolue

Ne jamais afficher mots de passe, clés API ou tokens en clair dans la discussion, même si l'utilisateur le demande.

**Où vivent les secrets.** Les secrets (clés API, mots de passe, `JWT_SECRET`, tokens) vivent dans le `.env` — hors git, hors base — un par environnement (local + VPS prod). **Jamais en base, jamais administrables depuis l'UI admin.** À l'échelle actuelle (prod avec profs pilotes), le `.env` bien tenu est le bon niveau : **être en prod ne change rien**. **Seul déclencheur d'une marche suivante = une explosion d'aSchool** (croissance massive, gros volume d'utilisateurs réels) → gestionnaire de secrets cloud (Secret Manager Infomaniak ou autre), **pas un HSM**. YAGNI jusque-là.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Sync docs — Règle de fin de session

En fin de chaque session de dev importante : mettre à jour ce fichier (version, règles nouvelles) + synchroniser TABLEAU-DE-BORD.md.
