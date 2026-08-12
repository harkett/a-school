#!/bin/bash
# Recolle une base dont l'estampille Alembic ne correspond plus a aucun fichier.
#
#     bash outils_bdd/recoller_migrations.sh          (depuis /var/www/a-school)
#
# CE QUI ARRIVE, ET POURQUOI CE SCRIPT EXISTE. Une refonte a supprime cinq migrations DEJA
# APPLIQUEES en production (b5f8e2a1d740, c9a2f7e4b613, a1c8f4e7b902, d3b7c1f8e5a4,
# e6d2b9a4c318) et les a remplacees par deux autres. La base porte donc une revision que les
# fichiers ne connaissent plus, et `alembic upgrade head` s'arrete net :
#     Can't locate revision identified by 'e6d2b9a4c318'
# Le deploiement echoue AVANT le build et le redemarrage — la production continue de tourner
# sur son code precedent, mais plus rien ne peut etre livre.
#
# COMMENT ON RECOLLE. Les deux chaines ont un tronc commun : f2b9d6c4a807. On redescend
# jusque-la en restaurant temporairement les anciens fichiers de migration depuis git — leurs
# `downgrade()` savent defaire ce qu'elles ont fait —, puis on remonte avec les fichiers
# actuels. Rien n'est devine ni force : ce sont les migrations elles-memes qui travaillent.
# `alembic stamp` ferait taire l'erreur en laissant la base dans un etat que personne ne
# connait ; c'est exactement ce qu'on ne veut pas.
#
# LES CINQ SCHEMAS DE DEMONSTRATION SUIVENT LE MEME CHEMIN, chacun avec sa propre table de
# version. Les oublier laisserait cinq bases a une revision disparue, et le prochain
# deploiement echouerait pour eux seuls, sans que rien ne le dise.
#
# LES DEUX BASES SONT DUMPEES AVANT LE PREMIER GESTE. Un downgrade supprime des tables : ici
# `ambiguite_exemples`, que la refonte a abandonnee avec l'ecran qui la lisait. Si le contenu
# comptait encore, il est dans le dump.
set -e

cd "${APP_DIR:-/var/www/a-school}"

TRONC="${TRONC:-f2b9d6c4a807}"      # la derniere revision commune aux deux chaines
ANCIEN="${ANCIEN:-e59ac78}"         # un commit ou les migrations supprimees existaient encore
NEUVES="${NEUVES:-b2c4e8f1a7d3 d7f3b1e9a5c2}"   # celles qui n'existaient pas a ce commit
SAUVE="${SAUVE:-/var/backups/aschool-recollage}"
BASE_DEMOS="${BASE_DEMOS:-aschool_demos}"

BASE_REELLE=$(grep -E "^DATABASE_URL=" .env | head -1 | sed -E 's|.*/([^/?]+).*|\1|')
URL_DEMOS=$(grep -E "^DATABASE_URL=" .env | head -1 | cut -d= -f2- | sed "s|/[^/]*$|/$BASE_DEMOS|")
ALEMBIC=.venv/bin/alembic
[ -x "$ALEMBIC" ] || ALEMBIC=alembic

echo ""
echo "=== [1/6] Sauvegarde ==="
mkdir -p "$SAUVE"
pg_dump -Fc "$BASE_REELLE" > "$SAUVE/$BASE_REELLE.dump"
pg_dump -Fc "$BASE_DEMOS"  > "$SAUVE/$BASE_DEMOS.dump"
ls -lh "$SAUVE"/*.dump | awk '{print "  " $9, $5}'

echo ""
echo "=== [2/6] Fichiers de migration : etat ancien ==="
mkdir -p /tmp/versions_neuves
for r in $NEUVES; do
    mv alembic/versions/${r}_*.py /tmp/versions_neuves/ 2>/dev/null || true
done
git checkout "$ANCIEN" -- alembic/versions/
# ON NOTE CE QU'ON VIENT D'AJOUTER. L'etape 5 doit retirer exactement ces fichiers-la, ni plus ni
# moins : un `git clean` balaierait aussi une migration en cours d'ecriture qui trainerait.
git diff --cached --name-only --diff-filter=A HEAD -- alembic/versions/ > /tmp/versions_restaurees.txt
echo "  $(wc -l < /tmp/versions_restaurees.txt) migrations restaurees, $(echo $NEUVES | wc -w) nouvelles mises de cote"

echo ""
echo "=== [3/6] $BASE_REELLE : retour au tronc commun ==="
$ALEMBIC downgrade "$TRONC" 2>&1 | grep -E "Running downgrade|ERROR" || true
echo -n "  $BASE_REELLE : "; psql -tAd "$BASE_REELLE" -c "SELECT version_num FROM alembic_version"

echo ""
echo "=== [4/6] Les schemas de demonstration ==="
for s in $(psql -tAd "$BASE_DEMOS" -c \
        "SELECT nspname FROM pg_namespace WHERE nspname NOT LIKE 'pg\_%' \
         AND nspname NOT IN ('public','information_schema') ORDER BY 1"); do
    DATABASE_URL="$URL_DEMOS" $ALEMBIC -x schema="$s" downgrade "$TRONC" > /dev/null 2>&1
    echo -n "  $s : "; psql -tAd "$BASE_DEMOS" -c "SELECT version_num FROM $s.alembic_version"
done

echo ""
echo "=== [5/6] Fichiers de migration : etat neuf ==="
# `git checkout HEAD -- <chemin>` NE SUPPRIME PAS les fichiers absents de HEAD. Les migrations
# restaurees a l'etape 2 sont dans l'index, donc elles SURVIVENT au checkout : Alembic voit alors
# deux tetes et refuse de remonter (« Multiple head revisions are present »). Mesure le
# 12/08/2026, le script s'y est casse.
#
# On retire NOMMEMENT ce que l'etape 2 a ajoute, plutot qu'un `git clean` qui emporterait aussi
# une migration en cours d'ecriture. Les fichiers mis de cote reviennent AVANT le checkout : ceux
# qui existent dans le depot sont alors normalises par lui, au lieu d'etre reecrits apres coup —
# sinon `git status` les voit modifies alors que rien n'a change d'autre que leurs fins de ligne.
git reset -q HEAD -- alembic/versions/
[ -s /tmp/versions_restaurees.txt ] && xargs -r rm -f < /tmp/versions_restaurees.txt
mv /tmp/versions_neuves/*.py alembic/versions/ 2>/dev/null || true
git checkout -f HEAD -- alembic/versions/
[ -z "$(git status --porcelain alembic/versions/)" ] || {
    echo "  ARRET : alembic/versions/ n'est pas revenu a l'etat du depot."
    git status --short alembic/versions/
    exit 1
}
# UNE SEULE TETE, ou on s'arrete. Remonter avec deux tetes echoue de toute facon, mais l'erreur
# d'Alembic ne dit pas d'ou elles viennent — celle-ci si.
tetes=$($ALEMBIC heads 2>/dev/null | grep -c "(head)")
echo -n "  tete : "; $ALEMBIC heads 2>/dev/null | tail -1
[ "$tetes" -eq 1 ] || { echo "  ARRET : $tetes tetes au lieu d'une."; exit 1; }

echo ""
echo "=== [6/6] Remontee vers la tete ==="
$ALEMBIC upgrade head 2>&1 | grep -E "Running upgrade|ERROR" || true
echo -n "  $BASE_REELLE : "; psql -tAd "$BASE_REELLE" -c "SELECT version_num FROM alembic_version"
DATABASE_URL="$URL_DEMOS" .venv/bin/python outils_bdd/migrer_les_demos.py 2>&1 | tail -14
