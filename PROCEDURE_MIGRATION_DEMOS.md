# Migration des démonstrations — un process, un schéma par démo

## Mission

Les démonstrations tournent aujourd'hui en **un process uvicorn par démo** (5 process, 800 Mo chacun,
mesuré). Les passer à **un seul process**, avec **un schéma PostgreSQL par démo**, choisi d'après le
sous-domaine.

`demo-crsa.aschool.fr` → schéma `crsa`. Le schéma existe : on sert. Il n'existe pas : 404.
**Les schémas présents dans la base SONT la liste blanche** — il n'y a ni table de routage à créer,
ni cache, ni connexion vers une autre base.

L'application réelle **garde son propre service, séparé**. Le process unique ne sert que les démos.
La table `demos` **ne bouge pas** : elle est jointe à `Referentiel`, `Niveau` et `Cycle`
(`prof/demo.py:92`, `prof/demo.py:127`, `systeme/admin.py:2568`), l'admin continue de la lire comme
aujourd'hui.

## Faits déjà mesurés — ne pas les redécouvrir

- `backend/core/database.py:16` crée le moteur à l'import depuis `DATABASE_URL`. **C'est la ligne qui
  fige la base** et qui oblige aujourd'hui à un process par démo.
- **209 endpoints** passent par `Depends(get_db)`. Aucun n'est à modifier.
- **14 accès base hors `get_db`** : `core/middleware.py:35` et `:66`, `supervision/alerts.py:179,239,256,270`,
  `rag/pgvector_store.py:250,274,354,411`, `pedagogie/referentiels_admin.py:611`, `analytique/usage.py:39`,
  `supervision/incidents.py:45`.
- **40 modèles ORM, aucun ne déclare `schema=`** → `schema_translate_map={None: "<schema>"}` suffit,
  **aucun modèle à toucher**.
- **3 SQL brut `text()`**, non traduits par `schema_translate_map`, à reprendre à la main :
  `core/database.py:35`, `systeme/admin.py:640`, `systeme/admin.py:2650`.
- La recherche vectorielle est en **ORM pur** (`rag/pgvector_store.py:424`) → traduite automatiquement.
- `alembic/env.py:48` appelle `context.configure()` **sans** `version_table_schema` ni `include_schemas`.
- `MODE_DEMO` est lu dans l'environnement du process (`prof/demo.py:69`), **4 appels**, un seul fichier.
- L'extension `vector` doit rester dans `public` et y être trouvée.
- **Les démos ne sont pas en lecture seule** : aucun endpoint d'écriture ne consulte `mode_demo()`, et
  l'entrée crée un compte (`prof/demo.py:238`). Un visiteur écrit vraiment dans le schéma de la démo.

## Règles de travail

1. **Une phase à la fois.** Tu t'arrêtes à la fin de chaque phase et tu attends.
2. **Avant de coder** : trois lignes sur ce que tu as compris. Puis tu attends « GO Codes ».
3. **Chaque étape a son « vérifié quand »**. Pas de « c'est fait » sans cette preuve.
4. **Rien hors procédure.** Un défaut trouvé ailleurs : le dire, ne pas le corriger.
5. **Ne rien ajouter à la solution.** Elle est arrêtée telle qu'elle est écrite ici.
6. Aucun appel d'API payante.

---

## Phase A — préparer. Rien ne bascule, l'existant tourne.

**1.** Résolution `Host → schéma` : `demo-<x>.aschool.fr` donne le schéma `<x>`, servi seulement si ce
schéma existe dans la base.
*Vérifié quand* : `curl -H "Host: demo-inconnu.aschool.fr"` renvoie 404, jamais une erreur SQL.

**2.** Poser `schema_translate_map={None: "<schema>"}` sur la session, via `engine.execution_options(...)`.
Pas de `SET search_path`, pas de SQL brut.
*Vérifié quand* : un test qui commite puis relit trouve encore le bon schéma.

**3.** `get_db` porte le schéma résolu. Les 209 endpoints ne bougent pas.
*Vérifié quand* : la suite de tests passe à l'identique.

**4.** Les 14 `SessionLocal()` directs reçoivent un schéma explicite : le middleware prend celui de la
requête, les alertes visent le schéma réel en dur.
*Vérifié quand* : plus aucun `SessionLocal()` sans schéma.

**5.** `MODE_DEMO` déduit de la requête, plus de l'environnement.
*Vérifié quand* : le même process répond `mode_demo: false` sur le réel, `true` sur une démo.

**6.** `get_db_size_mb()` mesure le schéma, pas la base entière.

## Phase B — convertir les données. Sur copie, jamais sur la production.

**7.** Pour une démo : restaurer sa base dans une base jetable, `ALTER SCHEMA public RENAME TO <schema>`,
dumper ce schéma, le verser dans la base cible.
*Vérifié quand* : comptages séquences / séances / activités identiques avant et après.

**8.** Répéter pour les cinq. L'extension `vector` reste dans `public`, installée une seule fois.

**9.** Alembic : `include_schemas=True` **et `version_table_schema=<schema>`** — une table
`alembic_version` **par schéma**. Sans ça, un schéma migré fait croire que les cinq le sont.
Script qui boucle, s'arrête au premier échec, nomme le schéma fautif.
*Vérifié quand* : `upgrade head` passe sur les 5 schémas et le rapporte schéma par schéma.

## Phase C — basculer.

**10.** Un service systemd unique pour les démos. Un seul bloc nginx :
`server_name ~^demo-(?<demo>.+)\.aschool\.fr$`.
*Vérifié quand* : `nginx -t` passe.

**11.** Démarrer. Les 5 sous-domaines répondent, chacun son contenu, un seul process.
*Vérifié quand* : `/api/demo/etat` donne le bon couple sur les 5, et la RAM tient dans ~1 Go au lieu de 4.

**12.** Contrôle croisé anti-fuite : appeler les 5 en rafale, en boucle alternée.
*Vérifié quand* : 200 requêtes alternées, zéro croisement de contenu.

## Phase D — retirer l'ancien.

**13.** Arrêter et désactiver les 5 services `aschool-demo@`, supprimer les blocs nginx par sous-domaine
et `deploy/env-demos/`.

**14.** Garder les 5 anciennes bases intactes une semaine. Les supprimer ensuite, pas avant.

---

## Hors périmètre

La remise à zéro périodique d'une démonstration n'est pas tranchée. Elle ne fait pas partie de cette
migration.
