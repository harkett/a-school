# État de la migration des démonstrations — 11/08/2026

## Pourquoi ce document existe

Cinq fichiers non suivis par git existaient déjà au début de la session du 11/08. Ils ont été
**écrasés sans avoir été lus** :

- `backend/core/schema_requete.py`
- `deploy/aschool-demos.service`
- `deploy/nginx-demos-local.conf`
- `outils_bdd/convertir_demos_en_schemas.sh`
- `outils_bdd/migrer_les_demos.py`

Leur contenu d'origine n'est récupérable nulle part. Ce document ne le restitue pas : il décrit
**ce qui est en place à la place**, avec les décisions prises, pour que celui qui les avait
commencés puisse dire ce qui recoupe et ce qui contredit son travail.

---

## Ce qui est en place, fichier par fichier

### `backend/core/schema_requete.py`

La résolution `Host` → schéma, et le middleware qui la pose.

- `schema_du_host(host)` : expression `^demo-([a-z0-9_]{1,55})\.aschool\.fr$`, insensible à la
  casse, port retiré avant. Rend `None` hors sous-domaine démo — ce n'est pas une erreur, c'est
  le cas ordinaire du réel et du poste de développement.
- `schema_existe(nom)` : `SELECT 1 FROM information_schema.schemata`. **Aucun cache**, à dessein
  (un schéma retiré doit cesser de répondre tout de suite, un schéma versé doit répondre sans
  redémarrage).
- `schema_de(request)` : lit `request.state.schema_db`, **repli sur `public`**. Le réel est le
  seul repli sûr : se tromper vers une démonstration ferait écrire un prof dans un bac à sable
  sans qu'aucune erreur ne le signale.
- `SchemaRequeteMiddleware` : `BaseHTTPMiddleware`. Schéma inconnu → **404 JSON**, jamais une
  erreur SQL.

### `deploy/aschool-demos.service`

Service systemd unique remplaçant l'unité paramétrée `aschool-demo@`.
`EnvironmentFile=/var/www/a-school/deploy/demos.env` (un fichier au lieu de cinq),
`--port ${PORT_DEMOS}`. **Plus de `MODE_DEMO`.**

### `deploy/nginx-demos-local.conf`

Le routeur de la pile locale, même `server_name` en expression que la production, sans TLS.
Amonts : `backend_demos:8001` et `frontend_demos:5174` (serveur Vite proxifié, `Upgrade` et
`Connection` pour le rechargement à chaud). Un `default_server` en `return 444` attrape
`localhost` et les IP — sans lui, une adresse quelconque servirait un bac à sable.

### `outils_bdd/convertir_demos_en_schemas.sh`

Étapes 7-8. Pour chaque base `<x>_demo` : dump → base jetable `tmp_<x>` → renommage → dump du
schéma → versement dans `aschool_demos`. Comptages séquences/séances/activités relevés avant et
après, arrêt au moindre écart. Les bases d'origine ne sont jamais ouvertes en écriture.

**Le détour par `_vecteur`.** `ALTER SCHEMA public RENAME TO <x>` emporte l'extension `vector`
avec le schéma : les colonnes d'embedding seraient typées `<x>.vector` et le dump refuserait de
se verser. L'extension est donc sortie de `public` avant le renommage et remise dans le `public`
neuf après — le dump sort typé `public.vector`.

**Refus d'écraser** : si le schéma existe déjà dans la cible, le script s'arrête. Écraser en
silence effacerait ce qu'un visiteur aurait fabriqué depuis la bascule.

### `outils_bdd/migrer_les_demos.py`

Étape 9. Boucle sur les schémas de la base (liste tirée de `information_schema`, `public` exclu),
lance `alembic -x schema=<x> upgrade head`, **relit l'estampille dans la base et la compare à
`head`**, s'arrête au premier écart en nommant le schéma fautif.

La relecture n'est pas décorative : mesuré le 10/08, Alembic peut annoncer neuf migrations,
rendre 0 et n'avoir rien écrit. Un code de retour ne prouve rien.

---

## Les décisions qui peuvent contredire ce qui avait été commencé

1. **`retrieve_pg` prend le schéma de la requête**, pas le réel en dur. Paramètre `schema` en
   mot-clé **obligatoire, sans valeur par défaut**, passé par `schema_de_session(db)` aux sept
   appels. Un défaut à `public` aurait fait chercher une démonstration dans le référentiel du
   réel — sans erreur, avec le mauvais contenu.
2. **La base des démonstrations est séparée** (`aschool_demos`), pas un jeu de schémas dans la
   base réelle. Le process des démonstrations n'a donc pas le réel dans sa chaîne de connexion.
3. **Un seul `text()` traité en Phase A** : `get_db_size_mb`, à qui le schéma est passé en
   paramètre puisqu'il ouvre `engine.connect()` hors session. `admin.py:640` lit
   `current_database()` (insensible au schéma) et `admin.py:2650` s'exécute sur un moteur jetable
   vers une autre base — les qualifier serait faux.
4. **Alembic reçoit `search_path` EN PLUS de `schema_translate_map`**, et par `connect_args`, pas
   par un `SET`. Sept migrations écrivent du SQL à la main (`DELETE FROM settings`,
   `UPDATE fonctionnalites`) que le translate_map ne traduit pas. Le `SET` équivalent ouvre une
   transaction, Alembic cesse alors de valider et n'écrit rien en annonçant tout.
5. **Port 8008** pour le service unique, neuf : 8007 a servi à ciela, 8003-8006 aux autres.
6. **`demos.conf` survit**, pour une seule raison : la liste des sous-domaines que le certificat
   doit couvrir. Le `server_name` étant devenu une expression, il ne les nomme plus. Les ports
   qu'il porte ne servent plus.

---

## Ce qui a changé dans les fichiers déjà suivis

`database.py` (`session_pour`, `schema_de_session`, `get_db(request)`, `get_db_size_mb(schema)`),
`middleware.py`, `main.py` (le middleware ajouté **après** `UserSessionMiddleware`, donc exécuté
avant lui), `demo.py` (`mode_demo(request)`), `pgvector_store.py`, les trois appelants de
`retrieve_pg`, `alerts.py` / `incidents.py` / `usage.py` / `referentiels_admin.py`
(`session_pour(SCHEMA_REEL)`), `admin.py`, `maintenance.py`, `alembic/env.py`,
`deploy/installer-demos.sh`, `docker-compose.yml`, et cinq fichiers de tests dont les points
d'accroche ont changé de nom.

Aucun des 209 endpoints ni des 40 modèles n'a été touché.

---

## Les preuves obtenues

| | |
|---|---|
| Suite de tests | 676 passed |
| Sous-domaine sans schéma | 404 JSON, jamais une erreur SQL |
| Isolation | écrit dans `verif`, relu dans `verif`, invisible depuis `public` |
| `SessionLocal()` nus | aucun ne subsiste |
| Conversion | comptages identiques avant/après sur les cinq |
| `vector` | installée une fois, dans `public` |
| Schémas migrés | les cinq à `d5b1f8c3e604`, estampille relue |
| `nginx -t` | *test is successful* sur la conf réellement produite |
| Un seul process | 5 couples distincts, 826 Mio contre 4 040 |
| Contrôle croisé | 200 requêtes alternées, 5 en vol, 0 croisement |

---

## Ce qui n'est pas fait

- Le VPS : Phases B et C n'y sont pas jouées. Ordre obligatoire — conversion et migration des
  schémas **avant** `installer-demos.sh`, sinon le service unique démarre sur une base absente.
- La Phase D : les 5 services `aschool-demo@` tournent encore, `deploy/env-demos/` est en place,
  les 5 bases `_demo` sont intactes.
- Hors procédure, signalé sans être corrigé : `admin.py:2645` compte les contenus d'une démo en
  ouvrant un moteur vers `nom_base` — après bascule, ces contenus sont dans un schéma d'une autre
  base. Et `crsa` / `ergo` ont 48 réglages contre 61 aux autres (13 lignes de `settings`
  manquantes, dont `ai_provider` et `ai_model`) alors que leur estampille dit le contraire :
  défaut antérieur à la migration, vérifié dans `crsa_demo` d'origine.
