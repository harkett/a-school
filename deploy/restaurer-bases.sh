#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# restaurer-bases.sh — REMPLACE les bases du VPS par celles envoyées depuis le poste.
#
# C'EST LE SCRIPT LE PLUS DESTRUCTEUR DU DÉPÔT. Il fait un `DROP DATABASE` sur la base réelle
# et sur les cinq démonstrations. Ce qui est sur le serveur disparaît. Trois garde-fous, dans
# cet ordre :
#   1. il SAUVEGARDE d'abord tout ce qu'il va détruire, dans /var/backups/aschool-avant-ecrasement/
#      — horodaté, et il s'arrête si le dump échoue ;
#   2. il exige la variable `JE_VEUX_ECRASER=oui` ; sans elle, il refuse et explique ;
#   3. il vérifie que CHAQUE dump attendu est présent AVANT de détruire quoi que ce soit — on ne
#      supprime jamais une base qu'on ne saurait pas remplacer.
#
# POURQUOI ÉCRASER PLUTÔT QUE MIGRER. Les démonstrations ne se « migrent » pas : leur contenu
# est écrit à la main sur le poste, il n'existe nulle part ailleurs. Et la base réelle du VPS
# n'a jamais servi — c'est le poste qui porte le travail. Le jour où ce ne sera plus vrai,
# ce script devra changer, et son garde-fou n° 2 est là pour qu'on s'en rende compte à temps.
#
# Usage : JE_VEUX_ECRASER=oui bash deploy/restaurer-bases.sh
#         (les dumps doivent être dans /var/www/a-school/deploy/dumps/)
# ─────────────────────────────────────────────────────────────────────────────
set -e

APP_DIR="${APP_DIR:-/var/www/a-school}"
cd "$APP_DIR"

DUMPS="deploy/dumps"
SAUVEGARDE="/var/backups/aschool-avant-ecrasement"
LISTE="deploy/demos.conf"
HORODATAGE=$(date +%Y%m%d-%H%M%S)

if [ "$JE_VEUX_ECRASER" != "oui" ]; then
    cat <<'EOF'
REFUS — ce script DÉTRUIT les bases du serveur.

Il supprime la base réelle et les cinq bases de démonstration, puis les remplace par les dumps
du poste. Si vous le vouliez vraiment :

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

lignes() { grep -vE "^\s*#|^\s*$" "$LISTE"; }

# LE NOM DU FICHIER N'EST PAS TOUJOURS LE NOM DE LA BASE. La base reelle s'appelle `aschool`
# ici et `aschool_dev` sur le poste : son dump voyage sous `_reelle.dump`, et c'est CE .env-ci
# qui dit dans quelle base le verser. Les demonstrations portent le meme nom des deux cotes.
dump_de() {
    if [ "$1" = "$BASE_REELLE" ]; then echo "$DUMPS/_reelle.dump"; else echo "$DUMPS/$1.dump"; fi
}

BASES=("$BASE_REELLE")
while IFS=: read -r base port sous_domaine; do BASES+=("$base"); done < <(lignes)

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
while IFS=: read -r base port sous_domaine; do
    sudo systemctl stop "aschool-demo@$base" 2>/dev/null || true
done < <(lignes)
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
echo "=== [bases 5/6] Adresses des démonstrations ==="
# LE DUMP COPIE LES DONNÉES TELLES QUELLES, y compris ce qui n'a de sens que sur le poste. La
# table `demos` (dans la base RÉELLE) porte l'adresse que l'écran d'administration propose pour
# aller visiter chaque démonstration : sur le poste, `http://localhost:5174`. Restaurée ici sans
# rien, elle enverrait l'administrateur du serveur vers SA PROPRE machine — le lien s'ouvre, il
# ne mène nulle part, et rien ne signale l'erreur.
#
# On les réécrit donc à partir de `demos.conf`, la même liste qui a servi à nginx : le sous-domaine
# y est déjà, il n'y a rien à inventer ni à recopier ailleurs. `nom_base` fait la jointure — c'est
# le seul lien possible, PostgreSQL ne sachant pas référencer une autre base.
maj=0
while IFS=: read -r base port sous_domaine; do
    modifiees=$(psql -tAd "$BASE_REELLE" -c         "UPDATE demos SET url = 'https://$sous_domaine' WHERE nom_base = '$base' RETURNING 1;" | wc -l)
    if [ "$modifiees" -gt 0 ]; then
        echo "  → $base : https://$sous_domaine"
        maj=$((maj + 1))
    else
        # Pas une erreur : une démonstration peut exister sur le poste sans que sa fiche ait été
        # déclarée. On le DIT, parce qu'elle sera alors invisible depuis l'écran d'administration.
        echo "  → $base : aucune fiche dans la table demos (démonstration non déclarée)"
    fi
done < <(lignes)
echo "  $maj adresse(s) mise(s) au nom du serveur"

# ET CELLES QU'ON N'A PAS VUES. La boucle ci-dessus part de `demos.conf` : une fiche dont la base
# n'y figure pas n'est jamais visitée, et garde donc son adresse locale sans que rien ne le dise.
# C'est exactement la forme de défaut qu'on passe la journée à traquer — on la nomme ici.
restantes=$(psql -tAd "$BASE_REELLE" -c     "SELECT nom_base || ' (' || url || ')' FROM demos WHERE url ILIKE '%localhost%' OR url ILIKE '%127.0.0.1%';")
if [ -n "$restantes" ]; then
    echo ""
    echo "  ATTENTION — ces fiches gardent une adresse locale, absente de deploy/demos.conf :"
    echo "$restantes" | sed 's/^/    /'
    echo "    → ajoutez-les à deploy/demos.conf, ou corrigez leur adresse depuis l'écran d'administration."
fi

echo ""
echo "=== [bases 6/6] Redémarrage et contrôle ==="
sudo systemctl start aschool
while IFS=: read -r base port sous_domaine; do
    sudo systemctl start "aschool-demo@$base" 2>/dev/null || true
done < <(lignes)
sleep 3

echec=0
curl -sf --max-time 5 http://127.0.0.1:8001/api/health > /dev/null \
    && echo "  OK   application réelle" || { echo "  ÉCHEC application réelle"; echec=1; }
while IFS=: read -r base port sous_domaine; do
    reponse=$(curl -sf --max-time 5 "http://127.0.0.1:$port/api/demo/etat" || echo "")
    if echo "$reponse" | grep -q '"mode_demo":true'; then
        echo "  OK   $sous_domaine  →  $(echo "$reponse" | sed -n 's/.*"couple":"\([^"]*\)".*/\1/p')"
    else
        echo "  ÉCHEC $sous_domaine : $reponse"
        echec=1
    fi
done < <(lignes)

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
