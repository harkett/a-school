# Fabriquer une démonstration

Procédure suivie pour `ciela_demo`, `cielb_demo` et `creche_demo`. Elle tient en six temps et ne
coûte rien : **le référentiel se copie, le contenu s'écrit**. Aucun appel à un fournisseur d'IA,
aucun embedding recalculé, aucun prompt rejoué.

Les commandes sont données telles qu'exécutées, depuis la racine du dépôt.

---

## Avant de commencer

**Ce qui doit exister dans la base réelle** : un référentiel découpé et validé, ses unités toutes
vectorisées, ses matières et ses types d'activité. C'est ce qu'on va copier ; on ne le fabrique
pas ici.

**La règle qui n'a jamais bougé** : on n'écrit **que** dans la base de démonstration. La seule
exception est la ligne de la table `demos`, au temps 6 — c'est le pilotage, et il vit dans le
réel. Toute commande d'écriture porte `-d <nom>_demo`.

**Convention de nom** : `<option>_demo`, en minuscules, avec des soulignés — jamais de tiret (un
tiret oblige à guillemeter le nom dans chaque commande psql).

**Choisir deux ports libres.** Les piles existantes occupent 8002/5174, 8003/5175, 8004/5176.
Vérifier avant de réserver :

```bash
for p in 8005 5177; do echo -n "$p : "; curl -s -o /dev/null -w "%{http_code}\n" -m 2 http://localhost:$p/ || echo libre; done
```

---

## Temps 1 — La base et son schéma

```bash
docker compose exec -T db psql -U aschool -d postgres -c "CREATE DATABASE <nom>_demo OWNER aschool;"
docker compose exec -T db psql -U aschool -d <nom>_demo -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker compose exec -T -e DATABASE_URL=postgresql+psycopg://aschool:aschool@db:5432/<nom>_demo \
  backend alembic upgrade head
```

L'extension `vector` se pose **avant** les migrations : une table de vecteurs ne se crée pas sans
elle.

Contrôle : le compte de tables et la révision doivent être ceux de la base réelle.

```bash
docker compose exec -T db psql -U aschool -d <nom>_demo -tAc \
  "select count(*)||' tables, head '||(select version_num from alembic_version) from information_schema.tables where table_schema='public';"
```

---

## Temps 2 — Copier le référentiel, vecteurs compris

Les migrations sèment les cycles et les niveaux : **le couple existe déjà** dans la base neuve, et
le plus souvent avec les mêmes identifiants que dans le réel. À vérifier avant de copier, parce
que `referentiels.niveau_id` en dépend :

```bash
docker compose exec -T db psql -U aschool -d <nom>_demo -c \
  "select c.id cycle, c.nom, n.id niveau, n.nom from cycles c join niveaux n on n.cycle_id=c.id where n.nom='<NIVEAU>';"
```

Si l'identifiant du niveau diffère, corriger la colonne `niveau_id` du référentiel après la copie.

La copie se fait table par table, du parent vers les enfants. `\copy` sort et entre en TSV : les
vecteurs passent tels quels, **rien n'est recalculé**.

```bash
S="$PWD/.tmp_copie" && mkdir -p "$S"
for T in "referentiels|id=<REF_ID>" "matieres|referentiel_id=<REF_ID>" \
         "types_activite|referentiel_id=<REF_ID>" "referentiel_chunks|referentiel_id=<REF_ID>"; do
  TABLE="${T%%|*}"; WHERE="${T##*|}"
  docker compose exec -T db psql -U aschool -d aschool_dev -c "\copy (SELECT * FROM $TABLE WHERE $WHERE) TO STDOUT" > "$S/$TABLE.tsv"
  docker compose exec -T db psql -U aschool -d <nom>_demo -c "\copy $TABLE FROM STDIN" < "$S/$TABLE.tsv"
done
```

Les précisions n'ont pas de `referentiel_id` : elles se prennent par jointure sur leur type.

```bash
docker compose exec -T db psql -U aschool -d aschool_dev -c \
  "\copy (SELECT p.* FROM referentiel_type_precisions p JOIN types_activite t ON t.id=p.type_activite_id WHERE t.referentiel_id=<REF_ID>) TO STDOUT" > "$S/precisions.tsv"
docker compose exec -T db psql -U aschool -d <nom>_demo -c "\copy referentiel_type_precisions FROM STDIN" < "$S/precisions.tsv"
```

**Recaler les séquences d'identifiants.** `\copy` écrit les id tels quels sans toucher aux
compteurs : sans cette étape, la première insertion faite depuis l'écran échoue en doublon.

```bash
for T in referentiels matieres types_activite referentiel_type_precisions referentiel_chunks; do
  docker compose exec -T db psql -U aschool -d <nom>_demo -tAc \
    "select setval(pg_get_serial_sequence('$T','id'), (select coalesce(max(id),1) from $T));"
done
```

Contrôle — les compteurs et la dimension des vecteurs doivent être ceux de la source :

```bash
docker compose exec -T db psql -U aschool -d <nom>_demo -c \
  "select (select count(*) from referentiel_chunks) chunks, (select count(*) from referentiel_chunks where embedding is not null) vecteurs, (select vector_dims(embedding) from referentiel_chunks limit 1) dims, (select count(*) from matieres) matieres, (select count(*) from types_activite) types, (select count(*) from referentiel_type_precisions) precisions;"
```

---

## Temps 3 — Le compte modèle

Il porte le contenu d'exemple et **ne se connecte pas** (`is_active=false`) : le prof n'entre
jamais avec lui, il reçoit une copie de ce qu'il détient.

Le mot de passe n'a pas à être choisi : on reprend l'empreinte d'une démonstration existante.

```bash
HASH=$(docker compose exec -T db psql -U aschool -d ciela_demo -tAc \
  "select password_hash from users where email='demo.btsciela@aschool.fr';" | tr -d '\r')

docker compose exec -T db psql -U aschool -d <nom>_demo \
  -c "insert into users (email, password_hash, is_verified, is_active, failed_attempts, guide_creer_vu, prenom, nom, subject_id, niveau_id, created_at) values ('demo.<nom>@aschool.fr', '$HASH', true, false, 0, false, 'Prof', 'Démo', <MATIERE_ID>, <NIVEAU_ID>, now());" \
  -c "insert into settings (key, value) values ('demo_gabarit_email','demo.<nom>@aschool.fr') on conflict (key) do update set value=excluded.value;"
```

`settings.demo_gabarit_email` est ce qui **désigne** le compte : c'est cette clé que lit
`_copier_le_gabarit` à l'arrivée d'un visiteur. Sans elle, le prof entre dans une démonstration
vide.

---

## Temps 4 — Le contenu, écrit à la main

Trois fichiers SQL, versionnés dans `demos/<nom>_demo/` : les séquences, les séances, les
activités. On les injecte dans l'ordre — chaque niveau référence le précédent.

```bash
docker compose exec -T db psql -U aschool -d <nom>_demo < demos/<nom>_demo/<nom>_01_sequences.sql
```

**La règle de composition** : une séquence par matière, au moins deux activités par séance, et
**tous les types d'activité du référentiel représentés au moins une fois**. Une démonstration
sert à montrer ce que le produit sait faire pour ce référentiel-là ; un type jamais employé ne se
voit pas.

**Ce qui se reprend du référentiel, mot pour mot** : `activite_label` est le libellé du type,
`sous_type` une précision existante ou rien, `matiere` un nom de matière, `niveau` le nom du
niveau. Rien ne s'invente : ce qui ne vient pas du référentiel ne se rattache à rien à l'écran.

**Colonnes qui demandent attention** — `competences` est un tableau JSON de chaînes ;
`esquisse` un objet JSON `{a,b,c}` ; `mode` vaut `standard | remediation | approfondissement |
autonomie` et `style` (colonne `ton` pour les activités) `classique | ludique | structure |
concis` ; `statut` d'une activité terminée vaut `termine`.

**Adapter le ton au public.** Pour un BTS, des épreuves, des barèmes, des corrigés. Pour la
crèche, rien de tout cela : le vocabulaire du référentiel commande, et il parle de « jeu avec un
jouet » et de « rituel collectif ».

Les fichiers s'écrivent dans le dépôt, pas dans un dossier temporaire — c'est du travail, il se
perd sinon. Prendre `demos/cielb_demo/` ou `demos/creche_demo/` comme gabarit.

---

## Temps 5 — La pile Docker

Copier les quatre blocs d'un couple existant dans `docker-compose.yml` et changer trois lignes :
le nom du service, la base dans `DATABASE_URL`, et les deux ports.

```bash
docker compose up -d backend_demo_<x> frontend_demo_<x>
```

Attendre que les deux répondent — le premier démarrage du frontend installe ses dépendances et
prend plusieurs minutes :

```bash
for i in $(seq 1 40); do c=$(curl -s -o /dev/null -w "%{http_code}" -m 5 http://localhost:<PORT_API>/api/demo/etat); [ "$c" = 200 ] && break; sleep 5; done
curl -s http://localhost:<PORT_API>/api/demo/etat   # doit rendre le bon couple
```

`{"mode_demo":true,"couple":"..."}` : si le couple est faux, c'est le `DATABASE_URL` du service
qui pointe la mauvaise base.

---

## Temps 6 — La fiche de pilotage

**Seule écriture autorisée dans la base réelle.** La ligne existe déjà si la démonstration a été
déclarée depuis l'écran Admin → Base de données → Démos ; sinon la créer là-bas.

```bash
docker compose exec -T db psql -U aschool -d aschool_dev -c \
  "update demos set statut='fait', url='http://localhost:<PORT_WEB>', nb_activites=<N>, nb_sequences=<N>, nb_seances=<N>, date_generation=now(), notes='…' where nom_base='<nom>_demo';"
```

**Le statut commande l'accès des profs** : seuls `teste` et `valide` ouvrent la porte. Tant qu'on
n'a pas parcouru la démonstration soi-même, elle reste en `fait` — et l'admin la relit par le
bouton **Visiter**, qui ouvre n'importe quelle démonstration quel que soit son statut.

**L'adresse est indispensable** : sans elle, l'entrée « Démonstration » du menu prof reste grisée,
même en statut `valide`.

---

## Contrôles avant de déclarer la démonstration faite

Une seule requête, à passer dans la base de démonstration. Tout doit rendre zéro.

```bash
docker compose exec -T db psql -U aschool -d <nom>_demo -c "
select 'sequences dont la matiere n existe pas' ctrl, count(*) from sequences s where not exists (select 1 from matieres m where m.nom=s.matiere)
union all select 'seances hors niveau', count(*) from seances where niveau<>'<NIVEAU>'
union all select 'activites sans seance', count(*) from activites a where not exists (select 1 from seances s where s.id=a.seance_id)
union all select 'contenu hors compte modele', count(*) from (select user_id from sequences union all select user_id from seances union all select user_id from activites) x where user_id<>(select id from users where email='demo.<nom>@aschool.fr')
union all select 'label qui ne colle pas au type', count(*) from activites a join types_activite t on t.id=a.activite_type_id where t.label<>a.activite_label
union all select 'sous_type inconnu du referentiel', count(*) from activites a where a.sous_type is not null and not exists (select 1 from referentiel_type_precisions p where p.libelle=a.sous_type and p.type_activite_id=a.activite_type_id);"
```

Puis, dans le navigateur : ouvrir la démonstration par **Visiter**, parcourir une séquence, une
séance et deux activités, vérifier que le filigrane **DÉMONSTRATION** est bien là — à l'écran, à
l'impression, dans le Word et dans le PDF.

---

## Ce qu'il ne faut pas faire

- **Recalculer les vecteurs.** Ils se copient. Une ré-ingestion coûte des appels et ne donne rien
  de plus.
- **Rejouer les prompts** du référentiel dans la base de démonstration : le découpage est déjà
  fait, il arrive avec la copie.
- **Écrire le contenu ailleurs que dans `demos/`.** Un dossier temporaire de session est purgé
  par le système ; le travail disparaît avec.
- **Laisser une démonstration en `fait` alors qu'elle a été relue** — ou l'inverse : la passer en
  `teste` sans l'avoir ouverte. Le statut est une promesse faite aux profs.

---

## Les bases existantes

| Base | Référentiel | API | Écran | Statut |
|---|---|---|---|---|
| `ciela_demo` | BTS CIEL Option A | 8002 | 5174 | testée |
| `cielb_demo` | BTS CIEL Option B | 8003 | 5175 | fabriquée |
| `creche_demo` | Crèche · BMG_0-3 | 8004 | 5176 | fabriquée |
| `crsa_demo` | — | — | — | base vide, créée d'avance |
| `ergo_demo` | — | — | — | base vide, créée d'avance |
