# SPÉCIFICATION — Le mode démonstration d'aSchool

**Version 1 — 29 juillet 2026**

**Destinataires : l'équipe de développement.**
Ce document est autoportant. Il ne suppose aucune connaissance préalable du produit
ni des discussions qui l'ont précédé. Tout ce qui est nécessaire pour développer la
fonctionnalité — le besoin, les décisions et leurs raisons, l'état exact du code
existant, les pièges, les critères de recette — se trouve ici.

**Statut : rien n'est codé.** Aucune ligne de cette spécification n'a été implémentée
à ce jour. Les numéros de ligne cités décrivent le code **existant**, relu et vérifié
le 29/07/2026.

---

## Sommaire

1. [Le produit, en bref](#1-le-produit-en-bref)
2. [Le besoin](#2-le-besoin)
3. [Le comportement attendu](#3-le-comportement-attendu)
4. [Les décisions prises, et pourquoi](#4-les-décisions-prises-et-pourquoi)
5. [État du code existant](#5-état-du-code-existant)
6. [Les pièges identifiés](#6-les-pièges-identifiés)
7. [L'architecture cible](#7-larchitecture-cible)
8. [Les lots de développement](#8-les-lots-de-développement)
9. [Hors périmètre](#9-hors-périmètre)
10. [Les conventions maison à respecter](#10-les-conventions-maison-à-respecter)
11. [Glossaire](#11-glossaire)
12. [Annexe — inventaire des fichiers cités](#12-annexe--inventaire-des-fichiers-cités)

---

## 1. Le produit, en bref

aSchool est une application web qui aide un enseignant à préparer ses cours. Le
principe : l'administrateur dépose les **référentiels officiels** (les programmes de
l'Éducation nationale, en PDF) ; l'application les indexe ; ensuite, un enseignant
décrit ce qu'il veut travailler et l'application lui **génère une activité
pédagogique** (un exercice, une évaluation, une fiche…) ancrée dans le référentiel de
son niveau.

Architecture technique :

| Couche | Technologie |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy |
| Base de données | PostgreSQL 16 avec l'extension **pgvector** |
| Recherche documentaire | embeddings locaux (`BAAI/bge-m3`, 1024 dimensions, `sentence-transformers`) |
| Génération de texte | modèle de langage distant (Groq ou Anthropic selon réglage) |
| Frontend | React (Vite), navigation par état interne, pas par URL côté enseignant |
| Exécution locale | Docker Compose (services `db`, `db_test`, `backend`, `frontend`, `adminer`) |
| Migrations | Alembic |

Deux populations d'utilisateurs, avec deux systèmes d'authentification **distincts** :

- **L'enseignant** — un compte en base (table `users`), cookies `aschool_access` /
  `aschool_refresh`.
- **L'administrateur** — **il n'a pas de compte en base**. C'est un identifiant/mot
  de passe défini par variables d'environnement, avec un cookie et un secret de
  signature séparés (`aschool_admin`, `ADMIN_JWT_SECRET`). Ne pas chercher de colonne
  de rôle dans `users` : il n'y en a pas.

---

## 2. Le besoin

Aujourd'hui, pour présenter aSchool à quelqu'un — un enseignant qu'on veut convaincre,
un établissement, un partenaire — il n'existe que deux options, toutes deux mauvaises :

1. **Créer un compte vierge.** Tous les écrans sont vides. Le visiteur ne voit pas à
   quoi ressemble l'outil quand il a servi, et il ne peut rien générer puisque le
   référentiel de sa matière n'est pas déposé.
2. **Montrer le compte d'un vrai enseignant.** On expose des contenus réels, et on
   risque de les modifier ou de les détruire pendant la manipulation.

On veut donc un **mode démonstration** : un environnement pré-rempli, réaliste,
entièrement fonctionnel, dans lequel n'importe quel enseignant peut entrer, tout
essayer, et dont il ressort sans avoir rien abîmé.

### Le critère de réussite n°1 : la qualité du contenu

C'est le point sur lequel le commanditaire insiste le plus, et il doit primer sur
toute considération de performance ou de coût.

Le visiteur juge le produit sur ce qu'il voit à l'écran. S'il tombe sur « Séquence 1 /
Séance A » et une activité médiocre, il conclut que l'outil est médiocre, même si la
mécanique est irréprochable. **La démonstration n'est pas un jeu de données de test,
c'est une vitrine commerciale.**

Conséquences directes, à ne pas arbitrer autrement :

- Le temps de fabrication d'une démonstration **n'est pas un critère**. Si elle met
  une heure à se construire, c'est acceptable : c'est un traitement de fond avec une
  barre de progression, l'administrateur le lance et va faire autre chose.
- Le coût des appels au modèle de langage **n'est pas un critère** non plus.
- En revanche, une étape de **relecture humaine** du contenu produit est
  obligatoire avant qu'une démonstration soit publiée (lot 5). Une démonstration
  n'est pas terminée quand le script s'arrête, elle est terminée quand un humain a
  validé chaque contenu.

---

## 3. Le comportement attendu

### 3.1 Du point de vue de l'administrateur

1. Il ouvre une rubrique « Créer des démos » dans l'espace d'administration.
2. Il choisit un cycle d'enseignement (« BTS MCO », « 4e », « CAP Cuisine »… — le
   contenu importe peu, le mécanisme est le même pour tous), dépose le PDF du
   référentiel officiel correspondant, et lance la fabrication.
3. Un traitement de fond construit un environnement complet : le cycle et son niveau,
   les matières, un compte enseignant de démonstration, le référentiel **réellement
   indexé**, des séquences, des séances, et des activités **réellement générées**.
   Une barre de progression indique l'étape en cours en langage clair.
4. Quand c'est fini, il **relit** ce qui a été produit, contenu par contenu, et
   demande la régénération de ce qui n'est pas assez bon.
5. Quand tout lui convient, il publie la démonstration : elle devient visible par les
   enseignants.

### 3.2 Du point de vue de l'enseignant

1. Dans son écran « Mon profil », il voit une carte « Mode démonstration » avec la
   liste des démonstrations publiées.
2. Il en choisit une et clique sur « Entrer dans la démonstration ». Quelques secondes
   d'attente, avec un indicateur visible.
3. L'application se recharge. **Tous ses écrans montrent désormais le contenu de la
   démonstration** : sa bibliothèque, son historique, ses séquences. Ses vraies
   données ne sont plus visibles — et ne sont plus accessibles du tout.
4. **Un bandeau reste affiché en permanence en haut de chaque page**, indiquant qu'il
   est en démonstration et que rien n'y sera conservé.
5. **À l'intérieur, aucune restriction.** Il crée, modifie, supprime, génère. Toutes
   les fonctions marchent réellement, y compris la génération d'activité, qui appelle
   pour de bon le modèle de langage sur le référentiel de la démonstration. Une
   fonction bridée donnerait une fausse idée du produit.
6. Il clique sur « Quitter la démonstration ». Une boîte de confirmation lui rappelle
   que tout ce qu'il a fait dans la démonstration va être perdu. Il confirme.
7. Il retrouve ses vraies données, **strictement intactes**. La démonstration, elle,
   redevient exactement ce qu'elle était : le visiteur suivant ne verra aucune trace
   de son passage.

### 3.3 Invariants

Ces propriétés doivent être vraies en permanence. Elles constituent la base de la
recette.

| # | Invariant |
|---|---|
| I1 | Tant qu'un enseignant est en démonstration, **aucune** écriture ne peut atteindre ses données réelles. |
| I2 | Tant qu'un enseignant est en démonstration, **aucune** lecture ne peut atteindre ses données réelles — y compris la recherche dans le référentiel, qui est invisible à l'écran. |
| I3 | Ce qu'un enseignant fait dans une démonstration n'est jamais visible par un autre enseignant, ni pendant, ni après. |
| I4 | Deux enseignants peuvent être en démonstration en même temps sans se gêner. |
| I5 | La sortie de démonstration remet l'environnement dans son état de publication, sans intervention manuelle. |
| I6 | Un enseignant qui ferme son navigateur sans quitter proprement ne laisse pas de résidu permanent. |
| I7 | Rien de ce qui est fabriqué pour une démonstration ne peut écraser un fichier ou une donnée de production. |

---

## 4. Les décisions prises, et pourquoi

Ces arbitrages ont été rendus lors de la conception. Ils sont fermés : les
réimplémenter autrement demanderait de rouvrir la discussion avec le commanditaire.
Les raisons sont données pour que l'équipe puisse les défendre, pas pour être
rediscutées.

### D1 — C'est l'enseignant qui bascule, pas l'administrateur

**Retenu :** chaque enseignant entre et sort de la démonstration depuis son propre
profil.

**Écarté :** un interrupteur global côté administration qui ferait passer toute
l'application en mode démonstration.

**Pourquoi :** un interrupteur global bascule *tout le monde*. Pendant une
présentation, les autres enseignants ne pourraient plus travailler. C'est
inutilisable en journée. C'est aussi le modèle standard du marché : Stripe (« mode
test », interrupteur par utilisateur avec bandeau permanent), QuickBooks et Xero
(« société de démonstration » dans laquelle on entre à la demande), Salesforce
(« sandboxes » créées par l'administrateur, utilisées individuellement).

### D2 — Le bandeau permanent est obligatoire

**Pourquoi :** c'est l'erreur classique de tous les produits qui offrent un mode
test — l'utilisateur travaille une heure dans le bac à sable en croyant être sur ses
vraies données, puis perd tout. Le bandeau n'est pas une décoration : il est la
contrepartie du fait qu'on n'a bridé aucune fonction.

### D3 — Aucun bridage à l'intérieur de la démonstration

**Pourquoi :** si le visiteur clique sur « Générer » et qu'un message dit « non
disponible en démonstration », la démonstration ne prouve plus rien. Tout doit
fonctionner pour de vrai, appels au modèle de langage compris.

### D4 — La démonstration se remet à zéro toute seule à la sortie

**Retenu :** l'environnement est jetable ; il revient à son état de publication dès
que l'enseignant sort.

**Écarté :** verrouiller la démonstration en lecture seule pour qu'elle ne s'abîme pas.

**Pourquoi :** les deux exigences « le visiteur fait ce qu'il veut » et « la
démonstration reste intacte pour le suivant » semblent contradictoires. Elles se
réconcilient non pas en empêchant d'écrire, mais en **jetant** ce qui a été écrit.

### D5 — Pas de passerelle entre la démonstration et les vraies données

**Écarté :** permettre à l'enseignant de récupérer dans son vrai compte une séquence
ou une activité qu'il aurait aimée dans la démonstration (export puis import).

**Pourquoi :** étudié et volontairement abandonné comme prématuré. La démonstration
sert à montrer comment l'outil fonctionne, pas à produire du contenu à conserver. Le
visiteur en ressort les mains vides. À rouvrir seulement si un besoin réel se
manifeste.

**Note technique pour ce jour-là :** l'export Word/PDF existant ne se réimporte pas
(c'est du texte mis en page, la structure est perdue). Il faudrait un format qui
transporte la hiérarchie séquence → séances → activités.

### D6 — Une base de données PostgreSQL séparée par démonstration

**Retenu :** l'isolation se fait au niveau de la base de données.

**Écarté :** un marqueur `is_demo` sur chaque table, avec filtrage dans les requêtes.

**Pourquoi :** le filtrage par colonne repose sur le fait que *toutes* les requêtes
de l'application pensent à filtrer. Il y a plus de 150 points d'accès à la base ; un
seul oubli fait fuiter des données réelles dans la démonstration ou l'inverse, et
l'invariant I2 (la recherche dans le référentiel) serait particulièrement facile à
manquer puisque rien ne se voit à l'écran. L'isolation par base rend la fuite
structurellement impossible : la mauvaise donnée n'est pas dans la base ouverte.

**Sur le nombre de bases :** PostgreSQL n'impose aucune limite pratique ici ; des
dizaines de bases sur un même serveur sont courantes. Une base inutilisée ne consomme
que de l'espace disque. Le vrai coût est la maintenance : chaque base doit recevoir
les migrations. C'est pour cela que la création et la suppression doivent être
automatisées dès le premier lot, et qu'on raisonne en « quelques démonstrations
utiles », pas en « une par visiteur ».

### D7 — Le modèle figé et sa copie jetable

**Retenu :** la base fabriquée par l'administrateur est un **modèle** dans lequel
personne ne travaille jamais. À l'entrée d'un enseignant, on en fait une **copie**
qui lui est propre ; à sa sortie, on supprime la copie.

**Pourquoi :** fabriquer une démonstration prend des minutes (indexation +
générations). La refaire à chaque sortie serait inacceptable. PostgreSQL sait copier
une base entière en quelques secondes (`CREATE DATABASE … TEMPLATE …`, une copie de
fichiers). La remise à zéro devient donc gratuite (D4 / I5), et le problème de deux
enseignants simultanés (I4) disparaît puisque chacun travaille dans sa propre copie.

**Contraintes de ce mécanisme, à connaître :**
- `CREATE DATABASE … TEMPLATE x` échoue s'il existe la moindre connexion ouverte sur
  `x`. Le registre de connexions ne doit donc **jamais** ouvrir une base modèle.
- `CREATE DATABASE` et `DROP DATABASE` ne peuvent pas s'exécuter dans une transaction :
  il faut une connexion en `AUTOCOMMIT`.
- Il faut un garde-fou sur le nombre de copies simultanées, et un ménage des copies
  abandonnées (I6).

### D8 — Le routage se décide sur un cookie dédié, pas sur le jeton de connexion

**Retenu :** un cookie signé `aschool_demo`, posé à l'entrée en démonstration,
contenant le nom de la base à ouvrir.

**Écarté :** ajouter une information au jeton d'authentification (`aschool_access`).

**Pourquoi :** le jeton d'accès ne contient aujourd'hui que l'adresse e-mail
(`backend/auth.py:164-169`), et la fonction qui identifie l'utilisateur va chercher
la ligne correspondante **en base** (`backend/core/deps.py:23-35`). Si le choix de la
base dépendait de l'utilisateur, et que l'utilisateur se lit dans la base, la
dépendance serait circulaire. Le cookie tranche **avant** tout accès à la base.

Bénéfice secondaire : on ne touche pas à la mécanique d'authentification, de
rafraîchissement et de rotation des jetons — qui est délicate et partagée avec
d'autres travaux en cours.

### D9 — Dans la copie, le compte de démonstration prend l'adresse e-mail du visiteur

**Retenu :** au moment de copier le modèle pour un enseignant donné, on met à jour la
ligne `users` du compte de démonstration pour lui donner l'adresse e-mail réelle du
visiteur.

**Pourquoi :** toute l'application identifie l'utilisateur par son e-mail (le jeton
ne contient que ça) et cloisonne les données par `user_id`. Avec cette substitution,
aucun autre code n'a besoin de savoir qu'il est en démonstration : il cherche
l'utilisateur par e-mail, il le trouve, et cet utilisateur possède l'intégralité du
contenu de la démonstration. C'est ce qui permet de ne pas modifier les 150+ requêtes
existantes.

---

## 5. État du code existant

Tout ce qui suit a été relu et vérifié le 29/07/2026 sur la branche `main`.

### 5.1 La connexion à la base est unique et figée au démarrage

Fichier : `backend/core/database.py` (36 lignes).

```
ligne  8  DATABASE_URL = os.getenv("DATABASE_URL")
ligne  9-13  garde-fou : absente ou "sqlite*" → RuntimeError à l'import
ligne 16  engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=1800)
ligne 17  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ligne 20-21  class Base(DeclarativeBase)
ligne 24-29  def get_db(): générateur SessionLocal() / yield / close()
ligne 32-36  get_db_size_mb() : utilise l'engine global
```

Points structurants :

- `create_engine` s'exécute **au niveau module**, donc une seule fois, à l'import.
- **`get_db()` ne prend aucun paramètre** : ni `Request`, ni utilisateur. Elle ne peut
  pas savoir qui pose la question.
- `get_db` est injectée par `Depends(get_db)` dans **159 endroits répartis sur 22
  fichiers**. Les plus gros consommateurs : `backend/systeme/admin.py` (52),
  `backend/pedagogie/referentiels_admin.py` (38), `backend/prof/profil.py` (11),
  `backend/routers/auth.py` (10).
- **Bonne nouvelle** : `get_db` résout `SessionLocal` par recherche dans le module au
  moment de l'appel, pas par capture à la définition. Changer le corps de `get_db`
  suffit ; aucun des 159 appelants n'a besoin d'être touché.
- Il existe déjà un précédent de substitution, en test :
  `conftest.py:52` positionne `DATABASE_URL` **avant** l'import de
  `backend.core.database`, puis `conftest.py:57-60` réécrit `_dbmod.engine` et
  `_dbmod.SessionLocal`. C'est une bascule globale à l'import, pas par requête, mais
  elle prouve que la couture fonctionne.

### 5.2 Six modules court-circuitent `get_db`

Ils importent `SessionLocal` ou `engine` directement. Chacun doit faire l'objet d'une
décision explicite.

| Fichier | Import | Sites d'usage | Décision |
|---|---|---|---|
| `backend/core/middleware.py` | l. 9 | 32, 63 | **Forcer la base principale.** S'exécute sur **chaque requête**, hors injection de dépendances (monté `main.py:84`). Gère la validité de session et l'horodatage `last_seen` : ce sont des données de supervision, elles appartiennent à la base réelle. Non traité, le middleware chercherait la session de l'utilisateur dans la base de démonstration, ne la trouverait pas, et **renverrait un 401 en purgeant les cookies** (`middleware.py:39-47`). |
| `backend/rag/pgvector_store.py` | l. 25 | 115, 135, 207, 264 | **Doit suivre la base de la requête.** C'est la recherche documentaire dans le référentiel. Non traité, un enseignant en démonstration générerait ses activités à partir du **référentiel de production** : la démonstration serait fausse et **rien ne le montrerait à l'écran**. C'est la violation la plus grave et la plus discrète de l'invariant I2. |
| `backend/supervision/alerts.py` | l. 8 | 69, 108 | **Reste sur la base principale.** Tâche planifiée (APScheduler, `main.py:58`), hors contexte de requête. |
| `backend/supervision/incidents.py` | l. 11 | 45 | **Reste sur la base principale.** Flux d'événements de supervision. |
| `backend/pedagogie/referentiels_admin.py` | l. 28 | 882 | **Reste sur la base principale.** Écran d'administration. |
| `backend/systeme/admin.py` | l. 14 (`engine`) | 448, 459 | **Reste sur la base principale.** L'endpoint `GET /admin/base` (l. 443-459) exécute `SELECT current_database()` et classe le nom en `reelle` / `miroir` / `test` / `autre` : cette classification devra être étendue pour reconnaître les bases de démonstration. |

### 5.3 Authentification

**Enseignant** — `backend/routers/auth.py`, monté avec le préfixe `/api`
(`backend/main.py:101`).

- `POST /api/auth/login` — l. 106-125.
- Deux cookies **HttpOnly**, fabriqués l. 21-31 : `aschool_access` (15 min) et
  `aschool_refresh` (30 jours). Options : `httponly=True`, `samesite="lax"`,
  `secure` seulement en production.
- Durées : `backend/auth.py:20-21`. Secret : `JWT_SECRET` (`auth.py:18`).
- **Contenu du jeton d'accès** (`auth.py:164-169`) : `{"sub": email, "type":
  "access", "exp": …}` — **uniquement l'e-mail**. Ni identifiant numérique, ni rôle.
- Identification de l'utilisateur courant : `get_current_user` dans
  `backend/core/deps.py:23-35` — décode le cookie (l. 29) puis **interroge la base**
  (l. 32 : `db.query(User).filter(User.email == email)`).
- Attention : `get_current_user` n'est utilisée qu'à un seul endroit
  (`backend/contenu/mes_contenus.py:17,29`). Ailleurs, **dix modules redéfinissent
  chacun leur helper local `_get_email(aschool_access)`** :
  `prof/profil.py:57`, `analyse/ambiguites.py:38`, `analyse/consigne.py:40`,
  `analytique/stats.py:15`, `communication/feedback.py:58`,
  `contenu/mes_activites.py:61`, `pedagogie/exemple_referentiel.py:79`,
  `sequence/sequence.py:35`, `sequence/optimiseur.py:38`, plus un contrôle en ligne
  dans `reseau/bibliotheque.py:20-24`. Ces helpers ne lisent que le cookie et ne
  touchent pas à la base : ils ne sont **pas** impactés par ce chantier.
- Côté navigateur, rien n'est stocké (cookies HttpOnly). `frontend/src/utils/api.js`
  pose `credentials: 'include'` sur tous les appels (l. 110-126) et gère un
  rafraîchissement unique sur 401 (l. 77-99).

**Administrateur** — `backend/systeme/admin.py`.

- `POST /api/admin/login` — l. 387-429 ; compare à `ADMIN_USERNAME` /
  `ADMIN_PASSWORD` (l. 391-396) avec repli sur un hachage stocké en table `settings`
  (l. 394-402).
- Cookie dédié `aschool_admin`, 4 heures (l. 22-23, 425). Jeton
  `{"sub":"admin","role":"admin"}` signé avec `ADMIN_JWT_SECRET` (l. 27-38).
- Garde : `_require_admin` (l. 49-51), posée en `Depends` sur toutes les routes
  `/api/admin/*`.
- **Il n'existe aucune colonne de rôle dans `users`.** Le modèle est mono-rôle : tous
  les comptes de la table `users` sont des enseignants.

### 5.4 Cloisonnement des données

Il n'existe **aucune notion d'établissement, de client, ni de groupe** dans le
schéma : aucune des ~45 classes de `backend/core/models_db.py` ne porte de champ de
ce type.

Le cloisonnement se fait **uniquement par `user_id`**, filtre par filtre, dans chaque
requête. Il n'y a ni sécurité au niveau des lignes (RLS), ni portée automatique. Le
motif dominant est :

```python
.filter(X.user_id == db.query(User.id).filter(User.email == email).scalar())
```

Exception volontaire : le module « Mon réseau » (`backend/reseau/bibliotheque.py:13-58`)
expose à tous les enseignants authentifiés les activités marquées `partagee`.

C'est cet état de fait qui rend l'isolation par base de données nettement plus sûre
qu'un filtrage supplémentaire (cf. D6).

### 5.5 La chaîne des référentiels

C'est la partie la plus longue à reproduire dans un script de fabrication. Ce n'est
pas un simple téléversement : c'est un enchaînement de **cinq gestes administrateur**,
dont l'ordre est imposé par des drapeaux en base.

Fichier principal : `backend/pedagogie/referentiels_admin.py` (1491 lignes), monté
sous `/api` par `backend/main.py:119`. Toutes les routes sont protégées par
`_require_admin`.

**Étape A — mise en attente du PDF**
- `POST /api/admin/referentiels/preparer-depot` (l. 173-176, multipart) ou
  `POST /api/admin/referentiels/preparer-lien` (l. 157-170, JSON `{url}`).
- Les deux passent par `_stage()` (l. 113-148) : refus au-delà de 30 Mo
  (`MAX_PDF_BYTES`, l. 40), vérification de la signature `%PDF-` (l. 118), écriture
  dans `data/referentiels_staging/<uuid4().hex>.pdf` (l. 120-122), aperçu des 25
  premières lignes (l. 82-89), refus au-delà de 150 pages (réglable, l. 133).
- Retour : `{token, filename, taille_ko, pages, apercu}`.
- Purge automatique du dossier d'attente au bout de 24 h (l. 92-110).

**Étape B — validation du dépôt (c'est ici que la base est écrite)**
- `POST /api/admin/referentiels/valider` (l. 381-530), corps `ValiderBody` (l. 370-378) :
  `{token, cycle_id, niveau_id, fichier_origine, source, date_doc, forcage_motif,
  verif_couple}`.
- Déplace le PDF (`shutil.move`, l. 441-444), **extrait le texte et le fige** dans
  `referentiels.texte_epure` (l. 451-456), crée la ligne `referentiels`, remplit
  `matieres_candidates`.
- Idempotent par le haut : si le jeton a disparu mais que le référentiel du couple
  existe déjà, renvoie `{ok: true, deja_valide: true}` (l. 385-417).
- Extraction du texte : `backend/rag/extraction.py`, fonction `extraire_texte()`
  (l. 85-99), avec `pdfplumber` 0.11.9. Deux règles d'épuration déterministes
  (l. 25-82) : suppression des numéros de page, et détection géométrique du texte
  vertical des marges de tableaux.

**Étape C — les matières**
- `POST /api/admin/referentiels/matieres` (l. 976-1022) : création ou récupération de
  la `Matiere` par nom (insensible à la casse) et de la paire `matiere_niveaux`.
  Idempotent.

**Étape D — le prompt de découpe, puis la découpe**

⚠️ **Il n'y a pas de taille de morceau paramétrable.** Le découpage n'est ni à taille
fixe, ni à fenêtre glissante. Il est **sémantique**, piloté par un prompt que le
système fait générer **pour ce document précis**. Fichier :
`backend/rag/analyse_amont.py`.

1. `generer_prompt_decoupe()` (l. 148-174) — lit le méta-prompt en base
   (`Setting['prompt_meta_decoupe']`), appelle le modèle, puis auto-critique via
   `verifier_prompt_decoupe()` (l. 177-198). Résultat stocké dans
   `referentiels.prompt_decoupe`, drapeau `prompt_decoupe_valide` à faux.
   Endpoint : `POST /api/admin/referentiels/prompt-decoupe/generer`.
2. Validation par l'administrateur :
   `POST /api/admin/referentiels/prompt-decoupe/valider` → `prompt_decoupe_valide` à
   vrai. **Sans ce drapeau, l'indexation refuse de s'exécuter**
   (`pgvector_store.py:163-167`).
3. `decouper_texte()` (l. 231-256) — appelle le modèle en sortie structurée
   (`_SCHEMA_DECOUPE`, l. 43-58), `temperature=0`. Le modèle **ne renvoie que des
   titres**, jamais de contenu.
4. `_trancher_par_titres()` (l. 123-145) — fonction pure : retrouve chaque titre dans
   le texte réel et tranche. Garantie produit : le système ne réécrit jamais le
   référentiel.
- Les méta-prompts par défaut sont semés par la migration
  `alembic/versions/b5c6d7e8f9a0_seed_ai_modeles_prompts_decoupe.py`.

**Étape E — l'indexation (calcul et écriture des vecteurs)**
- `backend/rag/pgvector_store.py`, fonction `ingest_pgvector()` (l. 123-242).
- Embeddings : `backend/rag/embeddings.py` — modèle **`BAAI/bge-m3`** (l. 15),
  **dimension 1024**, exécuté **localement** via `sentence-transformers` (aucun appel
  distant). Environ 2,2 Go, singleton thread-safe (l. 21-33), préchauffé au démarrage
  du serveur (`main.py:65-75`), cache monté depuis `./docker/hf-cache`
  (`docker-compose.yml:86`), mode hors-ligne forcé (`main.py:11-12`).
  **Premier appel à froid : ~30 s de chargement.**
- Sauvegarde obligatoire avant purge (l. 55-105) : écrit un fichier JSONL dans
  `backend/rag/backups/`, le relit, et **lève une exception si le compte ne
  correspond pas** — le `DELETE` (l. 210) n'est alors jamais atteint.
- Vectorisation par lots de 4 (l. 197) pour l'avancement de la barre de progression.
- Déclenchement HTTP : `POST /api/admin/referentiels/decoupe/valider` (l. 898-917)
  lance `_ingest_en_fond()` (l. 864-895) dans un thread ; suivi par
  `GET /api/admin/referentiels/decoupe/statut` (l. 920-938). L'état d'avancement vit
  dans des dictionnaires en mémoire (l. 852-861) et **est perdu au redémarrage** —
  c'est un défaut connu, à ne pas reproduire dans le lot 4.
- **Voie directe, sans HTTP, recommandée pour un script** : appeler
  `ingest_pgvector(collection)` ou la ligne de commande
  `python -m backend.rag.pgvector_store --collection <nom_fixe>` (l. 307-315).
  ⚠️ Cette voie **ne positionne pas** `decoupe_valide=True` — c'est `_ingest_en_fond()`
  (l. 886) qui le fait. Un script doit donc l'écrire lui-même, sinon le référentiel
  restera marqué incomplet.

**Étape F — les types d'activité**
- `POST /api/admin/referentiels/types-activite/detecter` — le système propose les
  types pertinents et **pose le prompt de génération** de chaque couple
  (référentiel × type) dans `referentiel_types_activite.prompt`.

**La recherche, au moment de générer** — `retrieve_pg()`, `pgvector_store.py:245-304` :
calcule le vecteur de la question, ordonne par distance cosinus (opérateur pgvector),
limite à `rag_top_k` (réglage en base, défaut 4, `admin.py:233`), et renvoie un
`score = 1 − distance`. L'appelant filtre ensuite au seuil `referentiels.score_min`
(défaut 0.30) et **renvoie une erreur 400 si aucun passage ne passe le seuil**.

### 5.6 Modèle de données concerné

Fichier : `backend/core/models_db.py`.

| Classe | Table | Lignes | À retenir |
|---|---|---|---|
| `User` | `users` | 9-35 | `email` unique (l. 11,14) ; `subject_id`, `niveau_id` (profil) ; `travail_matiere_id`, `travail_niveau_id` (couple de travail, l. 31-32) ; **aucune colonne de rôle** |
| `Cycle` | `cycles` | 441-447 | `nom` unique |
| `Niveau` | `niveaux` | 449-455 | `cycle_id`, `nom` |
| `Matiere` | `matieres` | 458-466 | |
| `MatiereNiveau` | `matiere_niveaux` | 469-480 | paire activable/désactivable |
| `MatiereCandidate` | `matieres_candidates` | 483-494 | propositions, une ligne par niveau |
| `Referentiel` | `referentiels` | 546-592 | voir détail ci-dessous |
| `ReferentielChunk` | `referentiel_chunks` | 595-619 | `embedding Vector(1024)`, index HNSW cosinus (l. 603-608), `ON DELETE CASCADE` |
| `ActiviteType` | `types_activite` | 622-649 | catalogue global |
| `ReferentielActiviteType` | `referentiel_types_activite` | 652-676 | **porte le prompt de génération** du couple × type |
| `ReferentielTypePrecision` | `referentiel_type_precisions` | 679-697 | |
| `ActiviteSauvegardee` | `activites_sauvegardees` | 236-265 | l'activité conservée par l'enseignant |
| `SequenceSauvegardee` | `sequences_sauvegardees` | 219-233 | **ancienne** table, alimentée par l'écran actuel |
| `Sequence` | `sequences` | 277-291 | **nouvelle** table, lue seulement |
| `Seance` | `seances` | 294-311 | **nouvelle** table, lue seulement ; `sequence_id` nullable, `ON DELETE SET NULL` |
| `SeancePhase` | `seance_phases` | 314-325 | `ON DELETE CASCADE` |
| `Setting` | `settings` | 172-179 | réglages **globaux** ; il n'existe pas de table de préférences par utilisateur |
| `CahierProf` | | 38-53 | PDF « cahier des charges » déposé par chaque enseignant |
| `AdminAuditLog` | | 368 | `admin_email` est une simple chaîne |

Détail de `referentiels` (l. 546-592), colonnes qui comptent :

| Colonne | Rôle |
|---|---|
| `niveau_id` (obligatoire), `matiere_id` (nullable) | `matiere_id` à NULL = le référentiel couvre tout le niveau, c'est le cas nominal. Contrainte d'unicité sur le couple (l. 553) |
| `nom_fixe` | **UNIQUE au niveau global** (l. 558) ; dérivé du **nom du niveau seul**, en minuscules |
| `collection` | égal à `nom_fixe` ; clé de résolution de la recherche documentaire |
| `texte_epure` | le texte de travail, figé à la validation |
| `prompt_decoupe`, `prompt_decoupe_valide` | garde-fou de l'étape D |
| `decoupe_valide` | **seul drapeau « terminé »** (pastille verte dans l'écran d'administration) |
| `score_min` | seuil de pertinence, défaut 0.30 |

### 5.7 Génération d'une activité

- `POST /api/generate` — `backend/contenu/activites.py:275-438`. Réponse en **flux
  SSE** (`text/event-stream`), événements `delta` / `error` / `done`.
- Corps `GenerateRequest` (`backend/core/models.py:8-16`) : `texte`,
  `activite_type_id`, `sous_type`, `nb`, `avec_correction`, `ton`.
  **Ni matière ni niveau** : ils sont lus en base.
- Enchaînement (chaque étape peut renvoyer un 400 explicite) :

| # | Ligne | Contrôle |
|---|---|---|
| 0 | 300 | enseignant + couple de travail ; profil incomplet → 400 |
| 1 | 303-305 | référentiel du niveau (`matiere_id IS NULL`) ; absent → 400 |
| 2 | 308-312 | type d'activité actif ; inconnu → 400 |
| 3 | 316-323 | **prompt** lu sur `referentiel_types_activite.prompt` ; vide → 400 |
| 4 | 328-336 | recherche documentaire, filtrée au seuil ; **aucun passage → 400** |
| 5 | 340-379 | assemblage : prompt + cahier de l'enseignant + correction + ton + `controle_qualite` (**toujours ajouté**, l. 379) |
| 6 | 384-391 | réglages lus en base (fournisseur, modèle, clé, jetons, température) |
| 7 | 395-399 | créneau d'appel ; saturation → 429 |
| 8 | 409-413 | `generate_stream()` — `backend/llm/generator.py:267-291` |

- ⚠️ **`POST /api/generate` n'écrit rien en base.** Le résultat est un brouillon
  affiché. L'enregistrement est déclenché par un bouton « Valider » côté frontend
  (`App.jsx:476-497`) qui appelle `POST /api/mes-activites`
  (`backend/contenu/mes_activites.py:70-102`). Il n'existe **ni sauvegarde
  automatique, ni historique de versions** à ce jour, contrairement à ce qui est
  prévu par ailleurs dans le produit.

### 5.8 Séquences et séances : il n'existe aucun moyen de les créer

**C'est le constat le plus important pour le contenu de la démonstration.**

- Les tables `sequences`, `seances` et `seance_phases` existent (migration
  `alembic/versions/a3c7e9d1b5f2_socle_mes_contenus.py`).
- Elles sont **lues** par `GET /api/mes-contenus`
  (`backend/contenu/mes_contenus.py:27-98`), qui alimente l'écran
  `frontend/src/components/MesContenus.jsx`.
- **Aucun endpoint ne les crée.** Dans le menu « Créer » de cet écran (l. 217-241),
  seule « Une activité » est branchée ; « Une séance » et « Une séquence » sont des
  libellés grisés « bientôt » (l. 230-237). Les boutons modifier et dupliquer sont
  désactivés (l. 288-293).
- Un travail dans ce sens a existé (commit `6426c89`) puis a été **intégralement
  annulé** (commit `ed0df9d`). Le découpeur de phases est récupérable par
  `git show 6426c89:backend/sequence/phases.py` : une fonction
  `decouper_phases(texte)` qui reconnaît le format `## Phase N — Titre (X min)`.
- L'écran « Créer une séquence » actuel (`frontend/src/components/SequenceForm.jsx`)
  appelle `POST /api/generate-sequence` (`backend/sequence/sequence.py:44-102`) qui
  écrit dans l'**ancienne** table `sequences_sauvegardees`, pas dans `seances`.
- ⚠️ Le bouton « Sauvegarder » de cet écran (`SequenceForm.jsx:140-163`) est **cassé** :
  il envoie `activite_key: 'sequence'` alors que l'API attend `activite_type_id: int`
  → 422 systématique. **Ne pas s'appuyer dessus.**

**Conséquence à assumer dans la version 1 du mode démonstration :** on peut
parfaitement **afficher** des séquences et des séances pré-construites, l'écran les
lit très bien. Mais si le visiteur clique sur « Créer une séquence » pendant la
démonstration, il verra « bientôt ». Le mode démonstration ne doit pas chercher à
combler ce manque : c'est le chantier « Mes contenus » qui s'en charge, et la
démonstration en bénéficiera automatiquement. Ce que le visiteur peut réellement
fabriquer en direct, c'est **une activité** — et c'est le geste le plus démonstratif.

### 5.9 Configuration, migrations, exécution

- **URL de la base** : lue en `os.getenv("DATABASE_URL")`, à un seul endroit
  (`database.py:8`). Il n'existe pas d'objet de configuration centralisé pour la base
  (`backend/config.py` ne concerne que les réglages du modèle de langage).
  `backend/main.py:19` charge le `.env` avec `override=False` : **l'environnement du
  conteneur l'emporte**.
- **Alembic** : `alembic.ini:89` laisse `sqlalchemy.url` volontairement vide ;
  `alembic/env.py:30-36` lit `DATABASE_URL` dans l'environnement et le pose lui-même.
  **Aucune modification n'est nécessaire** pour migrer une autre base : il suffit de
  lancer la commande avec un `DATABASE_URL` différent.
- **Docker Compose** : services sans `container_name` explicite, donc nommés
  `a-school-<service>-1`.

| Service | Image | Détail |
|---|---|---|
| `db` | `pgvector/pgvector:pg16` | utilisateur `aschool`, mot de passe `aschool`, base `aschool_dev` ; port hôte 5433 → 5432 ; volume `pgdata_dev` ; scripts d'initialisation `./docker/initdb` |
| `db_test` | `pgvector/pgvector:pg16` | base `aschool_test`, en mémoire (tmpfs), aucun port publié |
| `backend` | build local | `DATABASE_URL` **forcé** à la ligne 76 ; commande ligne 81 : `alembic upgrade head && uvicorn backend.main:app …` |
| `frontend` | `node:24` | port 5173 |
| `adminer` | `adminer:5` | port 8082 |

⚠️ Les scripts de `./docker/initdb` ne s'exécutent qu'à la **première** initialisation
du serveur PostgreSQL. Une base créée après coup **n'aura pas l'extension pgvector** :
il faut exécuter `CREATE EXTENSION IF NOT EXISTS vector;` explicitement.

### 5.10 Les écrans d'administration

- Le menu est un tableau unique : `NAV_ITEMS` dans
  `frontend/src/components/AdminLayout.jsx` (l. 12-191). Deux formes : entrée simple
  `{to, label, aide, icon}` ou groupe repliable `{group: true, label, items: [...]}`.
- **Règle inscrite dans le fichier** (commentaire l. 9-11) : *« toute nouvelle page se
  range sous une famille existante, jamais une entrée à plat de plus »*.
- Familles existantes, dans l'ordre : Mise en route, Référentiel, Programmes, Contenu,
  Profs & communication, Supervision & sécurité, Analytique, Base de données,
  **Système** (Génération, Email, Paramètres, Maintenance — l. 136-152), Labo, puis
  séparateur, Mon compte, Aide.
- Routes React : `frontend/src/App.jsx:1444-1479`. Pages dans
  `frontend/src/pages/Admin*.jsx`.
- **Meilleur gabarit à copier pour ce chantier** :
  `frontend/src/pages/AdminMaintenance.jsx` (168 lignes) avec
  `backend/systeme/maintenance.py` — c'est exactement le motif « liste d'éléments
  décrits par le serveur + un bouton d'action par ligne + journal d'audit »
  (`log_admin_action`, `maintenance.py:159-166`).
- Montage d'un nouveau routeur : `backend/main.py`, section `include_router`
  (l. 100-120), toujours avec `prefix="/api"`.

### 5.11 L'écran « Mon profil » de l'enseignant

- `frontend/src/components/MonProfil.jsx` (406 lignes), affiché par
  `App.jsx:1349` — c'est une page pilotée par un état interne, **pas** une route.
- Cartes existantes : « Mon profil » (l. 195-322, identité + niveau + matière),
  « Programme officiel de votre niveau » (l. 331-359), « Mon cahier des charges »
  (l. 363-400, dépôt d'un PDF personnel).
- Endpoints : `GET`/`PATCH /api/user/profile` (`backend/prof/profil.py:75-105`).
- C'est ici que se place la carte « Mode démonstration ».
- Le bandeau permanent devra être posé au-dessus de la zone de contenu, à un endroit
  couvrant toutes les pages enseignant. `frontend/src/components/Header.jsx` affiche
  déjà une bannière conditionnelle (« Merci de compléter votre profil », l. 26-39) :
  c'est le point d'accroche naturel.

---

## 6. Les pièges identifiés

Chacun de ces points a été vérifié dans le code. Ils sont listés séparément parce que
ce sont eux qui feront échouer une implémentation naïve.

### P1 — La recherche documentaire est le trou d'isolation le plus dangereux

`backend/rag/pgvector_store.py` ouvre sa propre session (l. 25, utilisée l. 115, 135,
207, 264). Si on ne la fait pas suivre la base de la requête, un enseignant en
démonstration verra son activité générée à partir du **référentiel de production**.
Rien à l'écran ne le signalera : le texte produit sera plausible. Ce défaut peut
survivre à toute une recette manuelle. **Il doit être couvert par un test
automatisé.**

### P2 — Le middleware de session déconnecterait l'utilisateur

`backend/core/middleware.py` (monté `main.py:84`) s'exécute sur chaque requête,
décode le cookie de rafraîchissement, et **renvoie un 401 en purgeant les cookies**
si la session n'est pas trouvée ou a été désactivée (l. 39-47). Branché sur une base
de démonstration fraîchement copiée, il ne trouverait aucune session et déconnecterait
l'enseignant à sa première requête. Il doit être forcé sur la base principale.

### P3 — Les PDF de référentiels sont sur le disque, hors de la base

Un référentiel validé pose son PDF dans `REFERENTIELS/<CYCLE>/<NIVEAU>/referentiel.pdf`.
Le chemin est calculé à partir des **noms** du cycle et du niveau par `_dossier_cle()`
(`referentiels_admin.py:44-50`, **fonction dupliquée** dans `pgvector_store.py:39-44`
— penser aux deux).

Donc, même avec des bases de données parfaitement séparées, une démonstration dont le
cycle ou le niveau porterait un nom existant **écraserait le PDF de production**.
Violation de l'invariant I7. La racine de stockage doit dépendre du monde courant.

Le dossier `REFERENTIELS/` est exclu du dépôt (`.gitignore:41`).

### P4 — `referentiels.nom_fixe` est unique au niveau global, et dérivé du seul niveau

`nom_fixe` (`models_db.py:558`) est calculé à partir du nom du **niveau uniquement**,
sans le cycle. Deux niveaux homonymes dans deux cycles différents provoquent un 409
(`referentiels_admin.py:436-437`), et la résolution du référentiel à la génération
abandonne en cas d'homonymie (`activites.py:82-85`).

Comme chaque démonstration a sa propre base, il n'y a pas de conflit entre
démonstration et production. **Mais à l'intérieur d'une même démonstration, les
niveaux doivent porter des noms distincts.** À documenter pour l'administrateur.

### P5 — L'extension pgvector n'est pas automatique sur une base créée après coup

Les scripts `./docker/initdb` ne tournent qu'à la création du serveur. Toute base
créée par le code doit recevoir `CREATE EXTENSION IF NOT EXISTS vector;` avant de
jouer les migrations, sinon la migration des vecteurs échouera.

### P6 — `CREATE DATABASE` a deux contraintes fortes

- Impossible dans une transaction : connexion en `AUTOCOMMIT` obligatoire.
- `WITH TEMPLATE x` échoue s'il existe **une seule** connexion ouverte sur `x`. Le
  registre de connexions ne doit jamais ouvrir une base modèle, et la fabrication doit
  fermer proprement sa connexion avant de figer le modèle.

### P7 — Ne jamais créer un moteur de connexion par requête

`create_engine` construit un pool de connexions. En appeler un par requête épuise le
serveur PostgreSQL en quelques minutes. Le registre doit **mettre en cache** un
`sessionmaker` par nom de base, et prévoir la fermeture propre du moteur quand une
base de démonstration est supprimée (sinon `DROP DATABASE` échouera, connexions
ouvertes).

### P8 — Le nom de base venant du cookie doit être validé

Le cookie est signé, mais le nom de base qu'il contient sert à composer une chaîne de
connexion. Il doit être vérifié contre une expression stricte (préfixe attendu +
caractères alphanumériques et tirets bas) **et** contre la liste des bases de
démonstration connues, avant tout usage. Un cookie forgé ne doit jamais permettre
d'ouvrir une base arbitraire.

### P9 — L'avancement gardé en mémoire est perdu au redémarrage

Le mécanisme actuel d'indexation stocke sa progression dans des dictionnaires Python
(`referentiels_admin.py:852-861`). Un redémarrage du serveur pendant un traitement
laisse l'écran bloqué sans information. **Ne pas reproduire ce défaut** : l'avancement
de la fabrication d'une démonstration doit être écrit en base.

### P10 — Le premier calcul d'embeddings coûte 30 secondes

Le modèle `BAAI/bge-m3` pèse environ 2,2 Go et se charge en mémoire au premier usage.
Il est préchauffé au démarrage du serveur (`main.py:65-75`). En script hors serveur,
prévoir ce délai et s'assurer que le cache `./docker/hf-cache` est bien monté.

---

## 7. L'architecture cible

### 7.1 Vue d'ensemble

```
                         ┌────────────────────────────────┐
Requête HTTP ──────────► │ get_db(request)                │
  cookie aschool_demo ?  │  cookie absent → base réelle   │
                         │  cookie présent → base copie   │
                         └───────────────┬────────────────┘
                                         │
             ┌───────────────────────────┼───────────────────────────┐
             ▼                           ▼                           ▼
    ┌────────────────┐          ┌─────────────────┐        ┌──────────────────┐
    │  aschool_dev   │          │ aschool_demo_   │        │ aschool_demo_    │
    │  (production)  │          │   bts_mco       │        │   bts_mco__u42   │
    │                │          │  ← MODÈLE figé  │───────►│  ← copie de      │
    │  + registre    │          │    jamais ouvert│ TEMPLATE│    l'enseignant  │
    │    des démos   │          └─────────────────┘        │    n° 42         │
    │  + sessions    │                                     └──────────────────┘
    └────────────────┘                                        supprimée à la sortie
```

### 7.2 Nommage

| Objet | Convention |
|---|---|
| Base modèle | `aschool_demo_<cle>` où `<cle>` est un identifiant en minuscules, sans accent, dérivé du nom de la démonstration |
| Base copie | `aschool_demo_<cle>__u<user_id>` |
| Racine des PDF, production | `REFERENTIELS/` |
| Racine des PDF, démonstration | `REFERENTIELS_DEMO/<cle>/` |
| Cookie de routage | `aschool_demo`, HttpOnly, `samesite=lax`, `secure` en production, durée alignée sur la session |

L'URL de connexion d'une base de démonstration est **déduite** de `DATABASE_URL` en
remplaçant le nom de la base. **Aucune nouvelle variable d'environnement** n'est
introduite.

### 7.3 Tables ajoutées (dans la base principale uniquement)

Ces tables ne servent qu'au pilotage. Elles n'existent que dans `aschool_dev` — elles
seront présentes mais inutilisées dans les bases de démonstration (les migrations
étant les mêmes), ce qui est sans conséquence.

**`demos`** — le catalogue des démonstrations.

| Colonne | Type | Rôle |
|---|---|---|
| `id` | entier, clé primaire | |
| `cle` | texte, unique | identifiant technique, sert au nom de base et au dossier PDF |
| `libelle` | texte | ce que voit l'enseignant : « Démonstration BTS MCO » |
| `base_modele` | texte | nom de la base modèle |
| `statut` | texte | `fabrication` / `a_relire` / `publiee` / `echec` |
| `etape` | texte, nullable | libellé lisible de l'étape en cours |
| `progression` | entier 0-100 | |
| `message_erreur` | texte, nullable | |
| `cree_le`, `maj_le` | horodatages | |

Seules les démonstrations en statut `publiee` sont proposées aux enseignants.

**`demo_sessions`** — les copies vivantes.

| Colonne | Type | Rôle |
|---|---|---|
| `id` | entier, clé primaire | |
| `demo_id` | clé étrangère vers `demos` | |
| `user_id` | clé étrangère vers `users` | l'enseignant réel |
| `base_copie` | texte, unique | nom de la base copiée |
| `ouverte_le`, `derniere_activite` | horodatages | pour le ménage automatique |

**Réglages ajoutés** dans le registre `SETTING_DEFAULTS` (`backend/systeme/admin.py:54-117`) :

| Clé | Défaut | Rôle |
|---|---|---|
| `demo_max_sessions` | 5 | plafond de copies simultanées |
| `demo_ttl_heures` | 6 | au-delà de ce délai sans activité, la copie est supprimée |

### 7.4 Cycle de vie d'une session de démonstration

1. **Entrée.** L'enseignant choisit une démonstration publiée. Le serveur vérifie le
   plafond, copie le modèle (`CREATE DATABASE … TEMPLATE`), met à jour dans la copie
   l'e-mail du compte de démonstration avec celui de l'enseignant (D9), enregistre la
   ligne `demo_sessions`, pose le cookie.
2. **Pendant.** Chaque requête ouvre la copie. `demo_sessions.derniere_activite` est
   rafraîchie (dans la **base principale**).
3. **Sortie explicite.** Le serveur ferme le moteur de connexion de la copie, exécute
   `DROP DATABASE`, supprime la ligne, retire le cookie.
4. **Sortie implicite** (navigateur fermé, cookie expiré). Une tâche périodique
   supprime les copies dont `derniere_activite` dépasse `demo_ttl_heures`. La tâche
   s'accroche à l'ordonnanceur existant (`main.py:58`).
5. **Cas limite.** Si l'enseignant se déconnecte de l'application alors qu'il est en
   démonstration, la déconnexion doit aussi déclencher la sortie (sinon la copie ne
   sera nettoyée qu'au bout du délai).

---

## 8. Les lots de développement

Cinq lots, à livrer dans l'ordre. Chacun se termine par des critères de recette
vérifiables. On ne passe au suivant qu'une fois ceux-ci satisfaits.

---

### Lot 1 — Une requête peut viser une autre base

**Objectif.** Rendre l'application capable de servir une requête sur une base
différente selon un cookie, sans rien changer au comportement par défaut.

**Ce qui existe aujourd'hui.** Toute requête, quel que soit l'utilisateur, lit et
écrit dans la base nommée par `DATABASE_URL`.

**Ce qu'on veut.** Une requête portant un cookie `aschool_demo` valide lit et écrit
dans la base qu'il désigne. Sans cookie, comportement strictement inchangé.

**Travaux.**

1. **`backend/core/database.py`** — introduire un registre de `sessionmaker` mis en
   cache par nom de base, avec fabrication paresseuse d'un moteur par base et méthode
   de fermeture. `get_db()` devient `get_db(request: Request)` : elle lit et valide le
   cookie (P8), et rend une session sur la base correspondante. Les 159
   `Depends(get_db)` restent inchangés (cf. 5.1).
   Prévoir aussi une fonction explicite « session sur la base principale », pour les
   appelants qui doivent y rester.
2. **`backend/core/middleware.py`** — remplacer l'usage de `SessionLocal` par la
   session « base principale » explicite (P2), avec un commentaire expliquant
   pourquoi.
3. **`backend/rag/pgvector_store.py`** — faire recevoir la session en paramètre aux
   fonctions concernées (l. 115, 135, 207, 264) au lieu de l'ouvrir elles-mêmes, et
   propager depuis les appelants : `backend/contenu/activites.py:243-256` et
   `:328-336`, `backend/pedagogie/exemple_referentiel.py:115`. Conserver le
   fonctionnement de la ligne de commande (l. 307-315), qui n'a pas de requête HTTP :
   elle prendra la base indiquée par son environnement.
4. **`backend/supervision/alerts.py`, `incidents.py`, `backend/systeme/admin.py`,
   `backend/pedagogie/referentiels_admin.py`** — laisser sur la base principale, en
   remplaçant l'import implicite par l'accès explicite et un commentaire justifiant le
   choix. Étendre la classification de `GET /admin/base` (`admin.py:443-459`) pour
   reconnaître les bases de démonstration.
5. **Racine des PDF de référentiels** — la rendre dépendante du monde courant (P3),
   dans `referentiels_admin.py:35-50` **et** `pgvector_store.py:39-44` (fonction
   dupliquée).
6. **Boîte à outils des bases** (nouveau module) : créer une base avec l'extension
   pgvector et les migrations, copier une base depuis un modèle, supprimer une base
   (avec fermeture préalable du moteur, P7), lister les bases de démonstration.
   Connexion en `AUTOCOMMIT` (P6).
7. **Signature et vérification du cookie** `aschool_demo`.

**Critères de recette.**

- [ ] La suite de tests existante passe **sans aucune modification**.
- [ ] Test automatisé : deux bases jetables, un même appel `GET /api/mes-contenus`
      renvoie le contenu de l'une sans cookie et de l'autre avec le cookie.
- [ ] **Test automatisé dédié à P1** : avec le cookie posé, un appel de génération
      va chercher ses passages dans les `referentiel_chunks` de la base de
      démonstration. Ce test est obligatoire ; c'est le seul garde-fou contre une
      erreur invisible à l'œil.
- [ ] Test automatisé : avec le cookie posé, l'écriture de `last_seen` par le
      middleware atterrit dans la **base principale**, et l'utilisateur n'est pas
      déconnecté.
- [ ] Test automatisé : un cookie forgé désignant une base hors préfixe attendu est
      rejeté, et la requête tombe sur la base principale ou renvoie une erreur claire
      (jamais une connexion arbitraire).
- [ ] Un moteur de connexion est créé **au plus une fois par base** : vérifiable en
      comptant les connexions PostgreSQL après une série d'appels.

**Fichier partagé avec d'autres travaux en cours : `backend/main.py`.** À signaler
avant modification.

---

### Lot 2 — Fabriquer une démonstration, en ligne de commande

**Objectif.** Construire une base de démonstration complète et réellement
fonctionnelle, sans interface, pour valider la chaîne avant de l'habiller.

**Ce qu'on veut.** Une commande lancée dans le conteneur backend qui prend un nom de
démonstration, un cycle, un niveau et un PDF de référentiel, et produit une base prête
à l'emploi.

**Enchaînement à réaliser.**

1. Créer la base ; `CREATE EXTENSION IF NOT EXISTS vector;` (P5) ; jouer
   `alembic upgrade head` avec `DATABASE_URL` pointant sur elle (aucune modification
   d'Alembic n'est nécessaire, cf. 5.9).
2. Semer le cycle, le niveau, les matières (via les fonctions existantes de
   `backend/pedagogie/programmes.py`), et créer le compte enseignant de démonstration
   (`backend.auth.create_user`, `backend/auth.py:55-75`) avec son couple de travail
   renseigné.
3. Copier le PDF dans `REFERENTIELS_DEMO/<cle>/…` puis **dérouler la chaîne complète
   du §5.5** : extraction et figement du texte, génération puis validation du prompt
   de découpe, découpe, calcul des embeddings, écriture des `referentiel_chunks`, et
   **positionner `decoupe_valide=True`** (piège signalé au §5.5, étape E).
4. Faire détecter les types d'activité et poser leurs prompts (étape F).
5. Générer les activités de démonstration **en appelant le vrai moteur de
   génération**, puis les enregistrer comme le ferait l'enseignant
   (`POST /api/mes-activites` ou l'écriture équivalente).
6. Écrire les séquences et les séances **directement via SQLAlchemy** — aucun endpoint
   n'existe (§5.8). Format de phase attendu : `## Phase N — Titre (X min)`.
7. Marquer la base comme modèle et fermer toute connexion vers elle (P6).

**Ce sur quoi il ne faut pas transiger.** Le référentiel doit être **réellement
indexé**. Insérer des lignes décoratives donnerait une démonstration qui paraît pleine
mais s'écroule au premier clic sur « Générer » : la recherche ne trouverait aucun
passage au-dessus du seuil et l'API renverrait un 400 (§5.7, étape 4).

**Critères de recette.**

- [ ] La commande est **rejouable** : relancée sur une démonstration existante, elle
      la reconstruit proprement sans intervention manuelle.
- [ ] En posant le cookie à la main, tous les écrans enseignant sont peuplés.
- [ ] **Générer une activité neuve depuis la démonstration fonctionne réellement**,
      de bout en bout, y compris le flux SSE.
- [ ] La table `referentiel_chunks` de la base de démonstration contient des vecteurs
      de dimension 1024 avec `embedding_model = "BAAI/bge-m3"`, et `decoupe_valide`
      vaut vrai.
- [ ] Aucun fichier de `REFERENTIELS/` (production) n'a été créé, modifié ou supprimé
      (invariant I7).

---

### Lot 3 — L'enseignant entre et sort

**Objectif.** Livrer la bascule côté enseignant, avec ses garde-fous.

**Ce qui existe aujourd'hui.** Aucun moyen de basculer.

**Ce qu'on veut.**

1. **Carte « Mode démonstration »** dans `MonProfil.jsx`, avec une liste déroulante
   des démonstrations publiées. Comme partout dans l'application, la liste démarre sur
   un libellé neutre « Choisissez… » de valeur vide : **rien n'est présélectionné**
   (convention maison, §10).
2. **Bouton « Entrer dans la démonstration »**. La copie prend quelques secondes :
   bouton en attente **et** indicateur de progression visible, jamais d'écran figé
   (convention maison). Au retour, l'application se recharge sur le nouveau monde.
3. **Bandeau permanent** sur toutes les pages enseignant tant que le cookie est
   présent : libellé de la démonstration, mention explicite que rien n'y sera
   conservé, et bouton « Quitter la démonstration ». Visuellement impossible à
   manquer.
4. **Sortie avec confirmation.** Boîte de dialogue rappelant ce qui va être perdu
   (convention maison : aucune suppression au clic direct). À la confirmation :
   fermeture du moteur, `DROP DATABASE`, suppression de la ligne `demo_sessions`,
   retrait du cookie, retour au monde réel.
5. **Déconnexion en cours de démonstration** : traitée comme une sortie.
6. **Ménage automatique** des copies abandonnées, branché sur l'ordonnanceur existant
   (`main.py:58`), piloté par `demo_ttl_heures`.
7. **Plafond** `demo_max_sessions` : au-delà, message clair, pas d'erreur technique.

**Critères de recette.**

- [ ] Parcours complet sur l'environnement de développement : entrer, créer une
      activité dans la démonstration, sortir, constater que l'activité a disparu et
      que les contenus réels sont **strictement** inchangés.
- [ ] Deux enseignants entrent simultanément dans la même démonstration, travaillent
      chacun de leur côté ; la sortie de l'un n'affecte pas l'autre (invariant I4).
- [ ] Une copie dont l'activité est plus ancienne que le délai est supprimée par le
      ménage automatique (invariant I6).
- [ ] Le bandeau est présent sur **toutes** les pages enseignant, sans exception.
- [ ] Après la sortie, plus aucune base `aschool_demo_*__u*` ne subsiste pour cet
      enseignant.

---

### Lot 4 — L'écran d'administration « Créer des démos »

**Objectif.** Rendre la fabrication utilisable sans terminal.

**Ce qu'on veut.**

- Une rubrique listant les démonstrations : libellé, cycle, date de fabrication,
  statut, taille, nombre de sessions ouvertes.
- Trois actions : **fabriquer** (formulaire : libellé, cycle, niveau, dépôt du PDF),
  **refabriquer**, **supprimer** — cette dernière derrière une confirmation
  proportionnée, avec refus explicite si des sessions sont ouvertes.
- La fabrication tourne **en tâche de fond**. Son avancement est **écrit en base**
  dans `demos.etape` / `demos.progression` (P9), et l'écran affiche une barre de
  progression avec l'étape en langage clair : « indexation du référentiel »,
  « génération de l'activité 3 sur 8 ». Un rechargement de page ou un redémarrage du
  serveur ne perd pas le fil.
- Toutes les actions sont tracées via `log_admin_action`.

**Où le brancher.**

| Point | Emplacement |
|---|---|
| Menu | `frontend/src/components/AdminLayout.jsx`, sous-entrée du groupe **Système** (l. 136-152), à côté de « Maintenance ». La règle maison interdit une entrée de premier niveau supplémentaire (commentaire l. 9-11). |
| Route | `frontend/src/App.jsx`, bloc `/admin` (l. 1444-1479) |
| Page | `frontend/src/pages/AdminDemos.jsx`, sur le gabarit de `AdminMaintenance.jsx` |
| Backend | nouveau module `backend/systeme/demos.py`, sur le gabarit de `backend/systeme/maintenance.py`, chaque route sous `Depends(_require_admin)` |
| Montage | `backend/main.py`, section `include_router`, `prefix="/api"` |

**Fichiers partagés avec d'autres travaux en cours**, à signaler avant modification :
`backend/main.py`, `backend/core/models_db.py` (nouvelles tables),
`alembic/versions/` (migration à rebaser sur la tête courante),
`backend/systeme/admin.py` (registre `SETTING_DEFAULTS`).

**Critères de recette.**

- [ ] Fabriquer une démonstration entièrement depuis l'écran, sans terminal.
- [ ] Recharger la page pendant la fabrication : la progression est toujours juste.
- [ ] Redémarrer le serveur pendant la fabrication : l'état affiché reste cohérent et
      l'échec, s'il y a lieu, est explicite (pas de statut bloqué sans message).
- [ ] Supprimer une démonstration : la base modèle disparaît, le dossier
      `REFERENTIELS_DEMO/<cle>/` aussi, et la suppression est refusée tant qu'une
      session est ouverte.

---

### Lot 5 — La revue de qualité

**Ne pas sauter ce lot** : c'est lui qui sert le critère de réussite n°1 (§2).

**Ce qu'on veut.** À l'issue de la fabrication, la démonstration passe au statut
`a_relire` — **elle n'apparaît pas encore** dans la liste proposée aux enseignants.

L'administrateur dispose d'un écran de relecture qui liste tout ce qui a été produit
— chaque activité, chaque séance — avec son contenu lisible en entier. Pour chaque
élément, deux actions : **« je garde »** ou **« je refais »**. La régénération relance
la génération pour ce seul élément.

Quand tous les éléments sont marqués comme gardés, un bouton **« Publier la
démonstration »** fige la base comme modèle et fait passer le statut à `publiee`.

**Critères de recette.**

- [ ] Une démonstration en statut `a_relire` n'est **jamais** proposée à un
      enseignant.
- [ ] Régénérer un élément ne casse rien d'autre dans la base.
- [ ] Après publication, plus aucune connexion n'est ouverte sur la base modèle
      (sinon la copie échouera — P6).

---

## 9. Hors périmètre

| Sujet | Décision |
|---|---|
| Export d'un contenu de la démonstration vers les vraies données | Écarté (D5). À rouvrir sur besoin réel. |
| Création de séquences et de séances depuis l'application | Relève du chantier « Mes contenus ». La démonstration en bénéficiera automatiquement (§5.8). |
| Sauvegarde automatique et historique de versions des activités | Chantier distinct, non implémenté à ce jour (§5.7). |
| Une démonstration personnalisée par visiteur | Non retenu : une démonstration par cycle suffit. |
| Notion d'établissement ou de client | N'existe pas dans le produit et n'est pas introduite ici (§5.4). |

---

## 10. Les conventions maison à respecter

Ces règles s'appliquent à tout le produit. Elles ne sont pas négociables et elles sont
souvent invisibles pour qui découvre le code.

1. **Le mot « IA » ne doit jamais apparaître à l'écran.** Dans l'interface, c'est
   « aSchool » qui fait l'action. Le terme reste autorisé dans les commentaires de
   code.
2. **Aucune liste déroulante ne démarre sur une valeur présélectionnée.** Tout
   `<select>` commence sur un libellé neutre « Choisissez… » de valeur vide. Ne jamais
   se rabattre sur le premier élément d'une liste ; l'état dérivé (étape validée,
   champ dépendant) se cale sur le choix réel de l'utilisateur.
3. **Aucune suppression au clic direct.** Toujours une boîte de confirmation,
   proportionnée à l'importance de ce qui est détruit.
4. **Tout traitement long affiche à la fois le bouton en attente et une barre de
   progression.** Jamais d'écran figé.
5. **La base de données est la source unique.** Interdiction de prévoir une valeur de
   repli dans le code quand la base est vide : une base vide est une **erreur**, elle
   doit produire un message clair à l'écran, pas un comportement de secours silencieux.
   Les valeurs initiales se posent par migration.
6. **Ne jamais tester sur des données réelles.** Les preuves passent par des tests
   automatisés sur une base jetable.
7. **`git add -A` est proscrit.** Plusieurs chantiers avancent en parallèle sur ce
   dépôt ; chacun ne range que ses propres fichiers.

---

## 11. Glossaire

| Terme | Définition |
|---|---|
| **Référentiel** | Le programme officiel d'un niveau, déposé en PDF puis indexé. Base documentaire de toute génération. |
| **Cycle** | Un ensemble de niveaux (« Collège », « CAP », « Crèche »…). |
| **Niveau** | Une classe ou une année à l'intérieur d'un cycle (« 5e », « CAP Cuisine »…). Un référentiel est rattaché à un niveau. |
| **Couple** | Le duo (cycle, niveau) qui identifie un référentiel dans les écrans d'administration. |
| **Couple de travail** | La matière et le niveau sur lesquels un enseignant travaille en ce moment ; stockés sur sa ligne `users`. |
| **Type d'activité** | Ce que l'on veut produire (exercice, évaluation…). Catalogue global ; le prompt de génération est porté par la liaison (référentiel × type). |
| **Activité** | Le document pédagogique produit par la génération, éventuellement conservé par l'enseignant. |
| **Séance** | Un cours, découpé en phases. Table `seances` (nouvelle, non alimentée à ce jour). |
| **Séquence** | Un ensemble ordonné de séances. Deux tables coexistent : `sequences_sauvegardees` (ancienne, alimentée) et `sequences` (nouvelle, lue seulement). |
| **Morceau (chunk)** | Un fragment de référentiel, découpé sémantiquement, stocké avec son vecteur dans `referentiel_chunks`. |
| **Modèle (base)** | La base de démonstration fabriquée et figée par l'administrateur. Jamais ouverte directement. |
| **Copie** | La base créée à partir du modèle pour un enseignant entrant en démonstration, détruite à sa sortie. |

---

## 12. Annexe — inventaire des fichiers cités

**Backend — cœur**

| Fichier | Rôle dans ce chantier |
|---|---|
| `backend/core/database.py` | Connexion et session — **cœur du lot 1** |
| `backend/core/deps.py` | `get_current_user` (l. 23-35) |
| `backend/core/middleware.py` | Suivi de session — à forcer sur la base principale (P2) |
| `backend/core/models_db.py` | Tous les modèles ; tables à ajouter |
| `backend/core/models.py` | `GenerateRequest` (l. 8-16) |
| `backend/main.py` | Montage des routeurs, ordonnanceur, préchauffage — **fichier partagé** |
| `backend/auth.py` | Jetons, `create_user` (l. 55-75) |
| `backend/routers/auth.py` | Connexion, cookies (l. 21-31, 106-125) |
| `backend/config.py` | Réglages du modèle de langage (pas de configuration base) |

**Backend — métier**

| Fichier | Rôle |
|---|---|
| `backend/rag/pgvector_store.py` | Indexation et recherche — **P1**, lot 1 et lot 2 |
| `backend/rag/embeddings.py` | Modèle `BAAI/bge-m3`, dimension 1024 |
| `backend/rag/extraction.py` | Extraction du texte des PDF |
| `backend/rag/analyse_amont.py` | Prompt de découpe et découpe |
| `backend/pedagogie/referentiels_admin.py` | Toute la chaîne de dépôt (1491 lignes) |
| `backend/pedagogie/programmes.py` | Création cycles/niveaux/matières |
| `backend/contenu/activites.py` | Génération d'activité (l. 275-438) |
| `backend/contenu/mes_activites.py` | Enregistrement d'activité (l. 70-102) |
| `backend/contenu/mes_contenus.py` | Lecture de la bibliothèque (l. 27-98) |
| `backend/sequence/sequence.py` | Génération de séquence, ancienne table |
| `backend/llm/generator.py` | Appels au modèle (`generate_stream`, l. 267-291) |
| `backend/prof/profil.py` | Profil enseignant, couple de travail |
| `backend/systeme/admin.py` | Authentification admin, registre de réglages — **fichier partagé** |
| `backend/systeme/maintenance.py` | **Gabarit à copier** pour le lot 4 |
| `backend/supervision/alerts.py`, `incidents.py` | Restent sur la base principale |

**Frontend**

| Fichier | Rôle |
|---|---|
| `frontend/src/components/MonProfil.jsx` | Carte « Mode démonstration » (lot 3) |
| `frontend/src/components/Header.jsx` | Point d'accroche du bandeau (lot 3) |
| `frontend/src/components/MesContenus.jsx` | Bibliothèque (lecture seule) |
| `frontend/src/components/Sidebar.jsx` | Menu enseignant |
| `frontend/src/components/AdminLayout.jsx` | Menu d'administration (lot 4) |
| `frontend/src/pages/AdminMaintenance.jsx` | **Gabarit à copier** (lot 4) |
| `frontend/src/pages/AdminReferentiels.jsx` | Écran de la chaîne des référentiels |
| `frontend/src/App.jsx` | Routes admin, navigation enseignant — **fichier partagé** |
| `frontend/src/utils/api.js` | Appels HTTP, gestion du 401 |

**Infrastructure**

| Fichier | Rôle |
|---|---|
| `docker-compose.yml` | Services, `DATABASE_URL` forcé (l. 76) |
| `alembic.ini`, `alembic/env.py` | Migrations — aucune modification nécessaire |
| `conftest.py` | Précédent de substitution de base (l. 52, 57-60) |
| `tests/test_mes_contenus.py` | Gabarit de création de jeu de données (l. 33-60) |

---

*Fin du document.*
