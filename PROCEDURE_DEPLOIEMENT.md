# Déployer aSchool — la procédure, et les pièges déjà rencontrés

## Le geste

```bash
ssh ubuntu@83.228.245.163
cd /var/www/a-school && bash deploy/deploy.sh
```

C'est tout. `deploy.sh` enchaîne : `git pull`, dépendances, **`alembic upgrade head` sur la base
réelle**, build du frontend, `restart aschool`, nginx, test de l'API — puis, en étape 8/8, il
appelle **`installer-demos.sh`**, qui pose le service unique des démonstrations, le bloc nginx et
le contrôle des cinq sous-domaines.

## Ce que `deploy.sh` ne fait PAS

**Il ne migre pas les schémas de démonstration.** Les cinq vivent dans `aschool_demos`, chacun
avec sa propre table `alembic_version` ; un `upgrade head` ordinaire ne voit que `public`. Après
toute migration, il faut donc :

```bash
DATABASE_URL=$(grep ^DATABASE_URL= .env | cut -d= -f2- | sed 's|/[^/]*$|/aschool_demos|') \
    .venv/bin/python outils_bdd/migrer_les_demos.py
```

Le script relit l'estampille en base et la compare à `head` : il ne se contente pas du code de
retour d'Alembic, qui peut valoir zéro sans que rien n'ait été écrit.

## Les trois pièges, tous rencontrés en production les 11 et 12/08/2026

### 1. `deploy.sh` bascule les démonstrations, même si leur base n'existe pas encore

Le jour de la migration, `installer-demos.sh` a posé le bloc nginx qui envoie les cinq
sous-domaines vers le port 8008 — alors que `aschool_demos` n'avait pas encore été créée. Les cinq
démonstrations sont tombées jusqu'à ce que la conversion soit faite.

**Sur un serveur qui n'a pas encore `aschool_demos`**, l'ordre est : `git pull`, puis
`outils_bdd/convertir_demos_en_schemas.sh`, puis `migrer_les_demos.py`, et `deploy.sh` seulement
après. Jamais l'inverse.

### 2. Un schéma versé n'appartient pas à l'application

`pg_dump` verse sous l'identité de celui qui lance la commande — `ubuntu` sur le VPS — alors que
l'application se connecte sous son propre rôle. Les vues `information_schema` étant filtrées par
les droits, l'application ne VOIT pas un schéma qu'elle ne possède pas : elle rend 404 sur une
démonstration parfaitement présente, sans la moindre erreur pour l'expliquer.

`convertir_demos_en_schemas.sh` réattribue désormais le schéma à l'utilisateur de la chaîne de
connexion, et `schema_existe()` interroge `pg_namespace` au lieu d'`information_schema`. Le
défaut ne pouvait pas se voir en local, où tout appartient au même rôle.

### 3. Une migration supprimée APRÈS avoir été appliquée bloque tout

Une refonte a retiré cinq migrations déjà passées en production et les a remplacées par deux
autres. La base portait alors une révision que les fichiers ne connaissaient plus :

```
Can't locate revision identified by 'e6d2b9a4c318'
```

`deploy.sh` s'arrête à l'étape 2.2, **avant** le build et le redémarrage — la production continue
de tourner sur son code précédent, mais plus rien ne peut être livré, ni le réel ni les cinq
démonstrations.

La réparation est dans [outils_bdd/recoller_migrations.sh](outils_bdd/recoller_migrations.sh) :
il redescend jusqu'au tronc commun aux deux chaînes avec les anciens fichiers restaurés depuis
git — leurs `downgrade()` défont leur propre travail — puis remonte avec les fichiers actuels.
Les variables `TRONC`, `ANCIEN` et `NEUVES` en tête du script se règlent au cas rencontré.

**Jamais `alembic stamp`** pour faire taire cette erreur : la base resterait dans un état que
personne ne connaît, et le défaut ressortirait à la migration suivante, sans rapport apparent.

**La vraie règle est en amont** : une migration appliquée en production ne se supprime pas. On en
écrit une nouvelle qui défait la précédente.

## Vérifier après coup

```bash
systemctl is-active aschool aschool-demos
journalctl -u aschool -u aschool-demos --since "10 min ago" -p err --no-pager

curl -s https://aschool.fr/api/health
for s in ciela cielb creche crsa ergo; do
    curl -s "https://demo-$s.aschool.fr/api/demo/etat"; echo
done
```

Les cinq doivent rendre **cinq couples différents**. Un couple identique sur deux sous-domaines
est une fuite de schéma, pas un détail d'affichage : on arrête tout et on cherche.

## L'architecture, en deux phrases

Deux services, deux bases. `aschool` sert le réel depuis la base `aschool` ; `aschool-demos` sert
les cinq démonstrations depuis `aschool_demos`, où chacune est un schéma choisi d'après le
sous-domaine. Le détail est dans [ETAT_MIGRATION_DEMOS.md](ETAT_MIGRATION_DEMOS.md).
