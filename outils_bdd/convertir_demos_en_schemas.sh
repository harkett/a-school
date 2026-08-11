#!/bin/sh
# Convertit les bases de démonstration en SCHÉMAS d'une seule base (étapes 7 et 8 de
# PROCEDURE_MIGRATION_DEMOS.md). `ciela_demo` devient le schéma `ciela` de `aschool_demos`.
#
# OÙ IL TOURNE.
#   Sur le VPS, PostgreSQL est natif et `psql` tourne sous l'identité système :
#     bash outils_bdd/convertir_demos_en_schemas.sh
#   En local, il est dans un conteneur et n'accepte que l'utilisateur `aschool` :
#     docker exec -i -e PGUSER=aschool a-school-db-1 sh -s < outils_bdd/convertir_demos_en_schemas.sh
#
# SUR COPIE, JAMAIS SUR LA PRODUCTION. Chaque base d'origine est DUMPÉE puis restaurée dans une
# base jetable `tmp_<x>` ; le renommage et le dump du schéma se font là. Les cinq bases d'origine
# ne sont jamais ouvertes en écriture et restent intactes (la Phase D les gardera une semaine).
#
# LE DÉTOUR PAR `_vecteur`, ET POURQUOI IL N'EST PAS FACULTATIF. `ALTER SCHEMA public RENAME TO
# ciela` emporte TOUT ce que `public` contient — y compris l'extension `vector`. Les colonnes
# d'embedding seraient alors typées `ciela.vector`, et le dump refuserait de se verser dans une
# base cible où `vector` vit dans `public`. On sort donc l'extension avant le renommage et on la
# remet dans le `public` neuf : le dump sort typé `public.vector`, ce que la cible attend.
#
# LA PREUVE EXIGÉE. Les comptages séquences / séances / activités sont relevés AVANT sur la base
# d'origine et APRÈS sur le schéma versé. Le moindre écart arrête tout et nomme le fautif : un
# schéma à moitié versé est pire qu'un schéma absent, parce qu'il répond.
set -eu

CIBLE=${CIBLE:-aschool_demos}

# L'UTILISATEUR POSTGRESQL SE DIT, IL NE SE DEVINE PAS. En local, PostgreSQL est dans un
# conteneur et n'accepte que `-U aschool`. Sur le VPS il est natif : `psql` y tourne sous
# l'identité système (`ubuntu`), et forcer `-U aschool` ferait échouer l'authentification.
# Vide par défaut = le comportement du VPS ; en local on pose `PGUSER=aschool`.
UTILISATEUR=${PGUSER:-}
[ -n "$UTILISATEUR" ] && OPT_U="-U $UTILISATEUR" || OPT_U=""
PSQL="psql -v ON_ERROR_STOP=1 $OPT_U -X -q -t -A"
TABLES="sequences seances activites"

compter() {   # $1 = base, $2 = schéma
    for t in $TABLES; do
        printf '%s=%s ' "$t" "$($PSQL -d "$1" -c "SELECT count(*) FROM $2.$t")"
    done
}

# La base d'accueil. `vector` y est installée UNE FOIS, dans `public`, et les cinq schémas la
# partagent : c'est la raison d'être du détour ci-dessus.
if [ -z "$($PSQL -d postgres -c "SELECT 1 FROM pg_database WHERE datname = '$CIBLE'")" ]; then
    $PSQL -d postgres -c "CREATE DATABASE $CIBLE"
    echo "base $CIBLE créée"
fi
$PSQL -d "$CIBLE" -c "CREATE EXTENSION IF NOT EXISTS vector"

for base in $($PSQL -d postgres -c \
        "SELECT datname FROM pg_database WHERE datname LIKE '%\_demo' ORDER BY datname"); do
    schema=${base%_demo}
    jetable="tmp_$schema"
    echo "──────── $base → $CIBLE.$schema"

    avant=$(compter "$base" public)
    echo "  avant : $avant"

    $PSQL -d postgres -c "DROP DATABASE IF EXISTS $jetable"
    $PSQL -d postgres -c "CREATE DATABASE $jetable"
    pg_dump $OPT_U -Fc "$base" > "/tmp/$base.dump"
    pg_restore $OPT_U -d "$jetable" --no-owner --no-acl "/tmp/$base.dump" >/dev/null

    $PSQL -d "$jetable" <<SQL
CREATE SCHEMA _vecteur;
ALTER EXTENSION vector SET SCHEMA _vecteur;
ALTER SCHEMA public RENAME TO $schema;
CREATE SCHEMA public;
ALTER EXTENSION vector SET SCHEMA public;
DROP SCHEMA _vecteur;
SQL

    # Le schéma est versé S'IL N'EXISTE PAS DÉJÀ. Écraser en silence effacerait ce qu'un visiteur
    # a fabriqué depuis la bascule ; on préfère s'arrêter et laisser l'humain trancher.
    if [ -n "$($PSQL -d "$CIBLE" -c \
            "SELECT 1 FROM information_schema.schemata WHERE schema_name = '$schema'")" ]; then
        echo "  ARRÊT : le schéma $schema existe déjà dans $CIBLE. Rien n'a été versé."
        exit 1
    fi
    pg_dump $OPT_U -n "$schema" --no-owner --no-acl "$jetable" > "/tmp/$schema.sql"
    $PSQL -d "$CIBLE" -f "/tmp/$schema.sql" >/dev/null

    apres=$(compter "$CIBLE" "$schema")
    echo "  après : $apres"
    if [ "$avant" != "$apres" ]; then
        echo "  ARRÊT : les comptages diffèrent pour $schema."
        exit 1
    fi

    $PSQL -d postgres -c "DROP DATABASE $jetable"
    rm -f "/tmp/$base.dump" "/tmp/$schema.sql"
    echo "  identique — $schema versé, base d'origine intacte"
done

echo "──────── schémas présents dans $CIBLE :"
$PSQL -d "$CIBLE" -c "SELECT schema_name FROM information_schema.schemata \
    WHERE schema_name NOT LIKE 'pg\_%' AND schema_name <> 'information_schema' ORDER BY 1"
