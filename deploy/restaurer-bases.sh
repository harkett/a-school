#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# restaurer-bases.sh — REMPLACE les bases du VPS par celles envoyées depuis le poste.
#
# C'EST LE SCRIPT LE PLUS DESTRUCTEUR DU DÉPÔT. Il fait un `DROP DATABASE` sur la base réelle.
# Ce qui est sur le serveur disparaît. Trois garde-fous, dans cet ordre :
#   1. il SAUVEGARDE d'abord tout ce qu'il va détruire, dans /var/backups/aschool-avant-ecrasement/
#      — horodaté, et il s'arrête si le dump échoue ;
#   2. il exige la variable `JE_VEUX_ECRASER=oui` ; sans elle, il refuse et explique ;
#   3. il vérifie que CHAQUE dump attendu est présent AVANT de détruire quoi que ce soit — on ne
#      supprime jamais une base qu'on ne saurait pas remplacer.
#
# POURQUOI ÉCRASER PLUTÔT QUE MIGRER. La base réelle du VPS n'a jamais servi — c'est le poste
# qui porte le travail. Le jour où ce ne sera plus vrai, ce script devra changer, et son
# garde-fou n° 2 est là pour qu'on s'en rende compte à temps.
#
# Usage : JE_VEUX_ECRASER=oui bash deploy/restaurer-bases.sh
#         (les dumps doivent être dans /var/www/a-school/deploy/dumps/)
# ─────────────────────────────────────────────────────────────────────────────
set -e

APP_DIR="${APP_DIR:-/var/www/a-school}"
cd "$APP_DIR"

DUMPS="deploy/dumps"
SAUVEGARDE="/var/backups/aschool-avant-ecrasement"
HORODATAGE=$(date +%Y%m%d-%H%M%S)

if [ "$JE_VEUX_ECRASER" != "oui" ]; then
    cat <<'EOF'
REFUS — ce script DÉTRUIT les bases du serveur.

Il supprime la base réelle, puis la remplace par le dump du poste. Si vous le vouliez
vraiment :

    JE_VEUX_ECRASER=oui bash deploy/restaurer-bases.sh

Une sauvegarde de ce qui existe est faite avant, dans /var/backups/aschool-avant-ecrasement/.
EOF
    exit 1
fi

# La base réelle et ses identifiants se lisent dans le .env : jamais recopiés ici.
DB_URL=$(grep -E "^DATABASE_URL=" .env | head -1 | cut -d= -f2-)
[ -n "$DB_URL" ] || { echo "ERREUR : DATABASE_URL absente du .env."; exit 1; }
BASE_REELLE="${DB_URL##*/}"
BASE_REELLE="${BASE_REELLE%%\?*}"        # au cas où la chaîne porte des paramètres

# LE NOM DU FICHIER N'EST PAS LE NOM DE LA BASE. La base reelle s'appelle `aschool` ici et
# `aschool_dev` sur le poste : son dump voyage sous `_reelle.dump`, et c'est CE .env-ci qui dit
# dans quelle base le verser.
dump_de() {
    echo "$DUMPS/_reelle.dump"
}

BASES=("$BASE_REELLE")

echo ""
echo "=== [bases 1/5] Contrôle des dumps ==="
# AVANT toute destruction : chaque base à remplacer doit avoir son dump, lisible.
manquants=""
for b in "${BASES[@]}"; do
    f=$(dump_de "$b")
    if [ ! -s "$f" ]; then
        manquants="$manquants $b"
    elif ! pg_restore --list "$f" > /dev/null 2>&1; then
        echo "ERREUR : $f n'est pas un dump PostgreSQL lisible."
        exit 1
    fi
done
if [ -n "$manquants" ]; then
    echo "ERREUR : dumps absents ou vides pour :$manquants"
    echo "  → rien n'a été détruit. Relancez l'envoi depuis le poste."
    exit 1
fi
echo "  → ${#BASES[@]} dumps présents et lisibles."

echo ""
echo "=== [bases 2/5] Sauvegarde de ce qui va être détruit ==="
sudo mkdir -p "$SAUVEGARDE"
sudo chown "$(whoami)" "$SAUVEGARDE"
for b in "${BASES[@]}"; do
    if psql -d postgres -lqt | cut -d\| -f1 | grep -qw "$b"; then
        pg_dump -Fc -d "$b" > "$SAUVEGARDE/${b}_$HORODATAGE.dump"
        echo "  → $b sauvegardée ($(du -h "$SAUVEGARDE/${b}_$HORODATAGE.dump" | cut -f1))"
    else
        echo "  → $b n'existe pas encore, rien à sauvegarder"
    fi
done

echo ""
echo "=== [bases 3/5] Arrêt des services qui tiennent les bases ==="
# Un DROP DATABASE échoue tant qu'une connexion reste ouverte. On coupe les backends AVANT,
# plutôt que de forcer la déconnexion des sessions : un `pg_terminate_backend` en pleine
# écriture laisserait une transaction à moitié faite dans la sauvegarde qu'on vient de prendre.
sudo systemctl stop aschool 2>/dev/null || true
echo "  → services arrêtés"

echo ""
echo "=== [bases 4/5] Remplacement ==="
for b in "${BASES[@]}"; do
    psql -d postgres -qc "DROP DATABASE IF EXISTS \"$b\";"
    psql -d postgres -qc "CREATE DATABASE \"$b\";"
    # `vector` est un geste superuser, hors migration : la migration qui crée la table des
    # embeddings le dit elle-même et ne le fait pas. Sans cette ligne, `alembic upgrade head`
    # tombe sur « type vector does not exist » — c'est exactement ce qui est arrivé le
    # 10/08/2026 en remontant les bases de démonstration.
    psql -d "$b" -qc "CREATE EXTENSION IF NOT EXISTS vector;"
    pg_restore --no-owner --no-privileges -d "$b" "$(dump_de "$b")"
    echo "  → $b remplacée"
done

echo ""
echo "=== [bases 5/5] Redémarrage et contrôle ==="
sudo systemctl start aschool
sleep 3

echec=0
curl -sf --max-time 5 http://127.0.0.1:8001/api/health > /dev/null \
    && echo "  OK   application réelle" || { echo "  ÉCHEC application réelle"; echec=1; }

echo ""
if [ "$echec" -eq 0 ]; then
    echo "Bases remplacées. La sauvegarde de l'état précédent est dans $SAUVEGARDE."
else
    echo "Au moins un service ne répond pas. L'état précédent est dans $SAUVEGARDE :"
    # --if-exists va AVEC --clean : sans lui, pg_restore essaie de supprimer des objets qui
    # n existent pas encore et remplit la sortie d erreurs qui font croire a un echec.
    echo "  pg_restore --clean --if-exists --no-owner -d <base> $SAUVEGARDE/<base>_$HORODATAGE.dump"
    exit 1
fi
