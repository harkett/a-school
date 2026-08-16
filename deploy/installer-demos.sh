#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# installer-demos.sh — pose sur le VPS tout ce qu'il faut pour servir les démonstrations.
#
# CE QU'IL FAIT : il installe l'INFRASTRUCTURE (fichier d'environnement, service systemd, bloc
# nginx), puis il met les SCHÉMAS À JOUR avant de contrôler que tout répond.
#
# LA MISE À JOUR DES SCHÉMAS A ÉTÉ AJOUTÉE LE 15/08/2026, et ce n'est pas un ajout de confort :
# le `alembic upgrade head` du déploiement ne migre que le réel. Les démonstrations, qui ont
# chacune leur table de version dans leur schéma, restaient à la traîne — le service démarrait,
# puis rendait une 500 sur la première requête touchant une colonne absente. Le contenu des
# bases, lui, reste l'affaire de `deploy/restaurer-bases.sh` : ici on met à niveau, on ne
# remplit pas.
#
# UN SEUL SERVICE, UN SEUL BLOC NGINX (10/08/2026). Il y avait cinq services et cinq blocs, un
# par démonstration, parce qu'une démonstration était une BASE et qu'un process ne se connecte
# qu'à une base. Les cinq bases sont devenues cinq SCHÉMAS d'une seule : le sous-domaine suffit
# désormais à dire lequel servir, et un seul process les sert tous. Quatre gigaoctets rendus.
#
# CE FICHIER LIT ENCORE `demos.conf`, pour UNE seule raison : la liste des sous-domaines que le
# certificat doit couvrir. Les ports qu'il porte ne servent plus — un port unique les remplace.
#
# IL EST REJOUABLE. Chaque geste est idempotent : réécrire un fichier identique, réactiver un
# service déjà actif, relire une configuration nginx déjà en place.
#
# Usage : bash deploy/installer-demos.sh    (depuis /var/www/a-school)
# ─────────────────────────────────────────────────────────────────────────────
set -e

APP_DIR="${APP_DIR:-/var/www/a-school}"
cd "$APP_DIR"

LISTE="deploy/demos.conf"
FICHIER_ENV="deploy/demos.env"
NGINX_DEMOS="/etc/nginx/sites-available/aschool-demos"

# La base qui porte les cinq schémas, et le port du process unique. LE PORT EST NEUF : 8007 a
# servi à ciela, 8003 à 8006 aux autres. Un port ne se réutilise pas — une configuration nginx
# oubliée quelque part pointerait sur un service qui n'est plus celui qu'elle croit.
BASE_DEMOS="${BASE_DEMOS:-aschool_demos}"
PORT_DEMOS="${PORT_DEMOS:-8008}"

[ -f "$LISTE" ] || { echo "ERREUR : $LISTE introuvable."; exit 1; }

# La base réelle donne le modèle de la chaîne de connexion : les démonstrations vivent sur le
# MÊME PostgreSQL, seul le nom de la base change. On la relit du .env plutôt que de la
# réécrire — un identifiant recopié est un identifiant qui divergera.
DB_MODELE=$(grep -E "^DATABASE_URL=" .env | head -1 | cut -d= -f2-)
[ -n "$DB_MODELE" ] || { echo "ERREUR : DATABASE_URL absente du .env."; exit 1; }
DB_PREFIXE="${DB_MODELE%/*}"      # tout jusqu'au dernier / : le serveur et ses identifiants

lignes() { grep -vE "^\s*#|^\s*$" "$LISTE"; }

echo ""
echo "=== [demos 1/7] Fichier d'environnement ==="
# UN seul fichier, contre cinq auparavant. Plus de MODE_DEMO : le drapeau ne vient plus de
# l'environnement du process — qui sert maintenant les cinq — mais du schéma que la requête vise.
cat > "$FICHIER_ENV" <<EOF
# Écrit par deploy/installer-demos.sh — ne pas modifier à la main, il sera réécrit.
DATABASE_URL=$DB_PREFIXE/$BASE_DEMOS
PORT_DEMOS=$PORT_DEMOS
EOF
echo "  → $FICHIER_ENV (base $BASE_DEMOS, port $PORT_DEMOS)"

echo ""
echo "=== [demos 2/7] Service systemd ==="
sudo cp deploy/aschool-demos.service /etc/systemd/system/aschool-demos.service
sudo systemctl daemon-reload
sudo systemctl enable aschool-demos >/dev/null
sudo systemctl restart aschool-demos
echo "  → aschool-demos démarré"

echo ""
echo "=== [demos 3/7] Certificat HTTPS ==="
# LE PIÈGE QUE NGINX NE SIGNALE PAS. Le bloc ci-dessous réutilise le certificat d'`aschool.fr`.
# Or un certificat ne vaut QUE pour les noms qu'il porte : servir `demo-crsa.aschool.fr` avec le
# certificat d'`aschool.fr` donne une alerte de sécurité en pleine figure du visiteur — et
# `nginx -t` la trouve parfaitement valide, puisque le fichier existe. Le `server_name` étant
# devenu une EXPRESSION, il ne dit plus quels noms sont servis : c'est `demos.conf` qui les
# tient, et c'est la raison pour laquelle ce fichier survit à la migration.
CERT="/etc/letsencrypt/live/aschool.fr/fullchain.pem"
NOMS_CERT=""
if [ -f "$CERT" ]; then
    # Les noms d'un certificat sont dans son extension « Subject Alternative Name ».
    NOMS_CERT=$(sudo openssl x509 -in "$CERT" -noout -text 2>/dev/null \
        | grep -A1 "Subject Alternative Name" | tail -1 \
        | tr -d " " | tr "," "\n" | sed "s/^DNS://")
fi

absents=""
while IFS=: read -r base port sous_domaine; do
    echo "$NOMS_CERT" | grep -qx "$sous_domaine" || absents="$absents -d $sous_domaine"
done < <(lignes)

if [ -z "$absents" ]; then
    echo "  → le certificat couvre déjà les $(lignes | wc -l) sous-domaines."
else
    echo "  → noms manquants au certificat :$absents"
    if ! command -v certbot > /dev/null; then
        echo "  ERREUR : certbot introuvable. Sans lui, les démonstrations seraient servies avec"
        echo "  un certificat qui ne les couvre pas — alerte de sécurité chez le visiteur."
        exit 1
    fi
    # `--expand` AJOUTE les noms au certificat existant au lieu d'en créer un second : deux
    # certificats pour le même domaine, c'est le renouvellement qui devient une loterie.
    sudo certbot certonly --nginx --expand --cert-name aschool.fr \
        -d aschool.fr -d www.aschool.fr $absents \
        --non-interactive --agree-tos --keep-until-expiring
    echo "  → certificat étendu"
fi

echo ""
echo "=== [demos 4/7] Bloc nginx ==="
# UN SEUL BLOC POUR LES CINQ, et il ne les nomme pas : `server_name` est une expression
# régulière qui accepte tout `demo-<x>.aschool.fr`. Ajouter une démonstration ne demandera plus
# de toucher à nginx — créer son schéma suffira. Un `<x>` sans schéma reçoit un 404 du backend,
# jamais une erreur SQL : la liste blanche, ce sont les schémas présents dans la base.
#
# `proxy_set_header Host $host` EST LA LIGNE QUI FAIT TOUT. C'est par cet en-tête, et par lui
# seul, que le backend sait quel schéma servir. Sans elle, nginx enverrait le nom du serveur
# amont (127.0.0.1), le backend n'y lirait aucun sous-domaine et rendrait le réel à tout le
# monde. Elle était déjà là avant la migration, où elle ne servait qu'aux journaux ; elle porte
# désormais l'aiguillage.
{
    echo "# Écrit par deploy/installer-demos.sh. Toute modification faite ici sera perdue."
    cat <<EOF

server {
    listen 80;
    server_name ~^demo-(?<demo>.+)\.aschool\.fr\$;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name ~^demo-(?<demo>.+)\.aschool\.fr\$;

    ssl_certificate     /etc/letsencrypt/live/aschool.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aschool.fr/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    root  /var/www/a-school/frontend/dist;
    index index.html;

    # CE QUE L'ON ACCEPTE DE RECEVOIR. Sans cette ligne, nginx s'en tient a son defaut : UN
    # megaoctet. Tout ce qui depasse est refuse AVANT d'atteindre l'application, avec une page
    # d'erreur HTML — le navigateur n'a donc aucun message a montrer, et l'ecran affiche son
    # texte de repli. Constate en production le 16/08/2026 : l'import d'un referentiel de 2,9 Mo
    # rendait « Import impossible. », sans plus, et rien cote application ne l'expliquait (le
    # journal de nginx, lui, le disait : « client intended to send too large body »).
    #
    # 64 Mo : un export de referentiel pese quelques megaoctets (ses vecteurs), un PDF officiel
    # peut monter plus haut. La borne existe pour qu'un envoi aberrant soit refuse tot, pas pour
    # arbitrer entre deux fichiers legitimes.
    client_max_body_size 64m;

    location /api/ {
        proxy_pass         http://127.0.0.1:$PORT_DEMOS;
        proxy_set_header   Host              \$host;
        proxy_set_header   X-Real-IP         \$remote_addr;
        proxy_set_header   X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto \$scheme;

        # Même réglage que l'application réelle : le flux SSE de la génération ne doit pas
        # être tamponné, sinon le « fil de l'eau » arrive d'un bloc à la fin.
        proxy_buffering     off;
        proxy_http_version  1.1;
        proxy_read_timeout  3600s;
    }

    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF
} | sudo tee "$NGINX_DEMOS" > /dev/null

sudo ln -sf "$NGINX_DEMOS" /etc/nginx/sites-enabled/aschool-demos
sudo nginx -t
sudo systemctl reload nginx
echo "  → nginx rechargé"

echo ""
echo "=== [demos 5/7] Propriété des schémas ==="
# LE PIÈGE QUI NE SE VOIT PAS, rencontré en production le 11/08/2026 sur les CINQ démonstrations
# à la fois. Un schéma versé par `pg_dump` appartient au rôle qui a lancé le versement. Versé en
# `postgres` — le réflexe, puisque c'est le rôle qui a le droit de créer — il reste INVISIBLE
# pour l'application, qui se connecte sous le sien. Le serveur répond alors 404 sur une
# démonstration parfaitement présente, sans la moindre erreur dans les journaux : le contrôle de
# `schema_existe` interroge `pg_namespace` et ne voit rien qui lui appartienne.
#
# POURQUOI ICI ET PAS DANS UNE PROCÉDURE ÉCRITE. Il A ÉTÉ documenté, et il est revenu : la
# démonstration suivante a été versée le lendemain, par quelqu'un qui n'avait pas la note sous
# les yeux. Un piège qui dépend de la mémoire de celui qui tape la commande n'est pas réglé. Ces
# quelques lignes le règlent pour toutes les démonstrations, y compris celles qui n'existent pas
# encore.
#
# REJOUABLE et sans effet quand tout va bien : reprendre la propriété d'un objet qu'on possède
# déjà ne change rien.
ROLE_APP=$(printf '%s' "$DB_MODELE" | sed -E 's|^[^:]+://([^:/]+).*|\1|')
if [ -z "$ROLE_APP" ] || [ "$ROLE_APP" = "$DB_MODELE" ]; then
    echo "  ERREUR : rôle de l'application illisible dans DATABASE_URL."
    exit 1
fi
sudo -u postgres psql -d "$BASE_DEMOS" -v ON_ERROR_STOP=1 -q <<SQL
DO \$\$
DECLARE
    s text;
    o record;
BEGIN
    FOR s IN
        SELECT nspname FROM pg_namespace
         WHERE nspname NOT LIKE 'pg\\_%'
           AND nspname NOT IN ('public', 'information_schema')
    LOOP
        EXECUTE format('ALTER SCHEMA %I OWNER TO %I', s, '$ROLE_APP');
        -- Le schéma ne suffit pas : chaque table, vue et séquence porte SON propre
        -- propriétaire. Un schéma rendu sans son contenu laisse l'application devant des
        -- tables qu'elle ne peut pas lire — le même 404, une couche plus bas.
        FOR o IN
            SELECT c.relname, c.relkind FROM pg_class c
              JOIN pg_namespace n ON n.oid = c.relnamespace
             WHERE n.nspname = s AND c.relkind IN ('r', 'v', 'm', 'S', 'p')
        LOOP
            EXECUTE format('ALTER %s %I.%I OWNER TO %I',
                CASE o.relkind
                    WHEN 'S' THEN 'SEQUENCE'
                    WHEN 'v' THEN 'VIEW'
                    WHEN 'm' THEN 'MATERIALIZED VIEW'
                    ELSE 'TABLE'
                END, s, o.relname, '$ROLE_APP');
        END LOOP;
    END LOOP;
END
\$\$;
SQL
echo "  → schémas et objets rendus à « $ROLE_APP »"

echo ""
echo "=== [demos 6/7] Schémas à jour ==="
# LE GESTE QUI MANQUAIT. Chaque démonstration est un SCHÉMA, avec sa propre table
# `alembic_version` : le `alembic upgrade head` du déploiement ne migre que le réel, dans
# `public`, et les schémas de démonstration restent au niveau où le dernier déploiement les a
# laissés. Une migration qui ajoute une colonne passe donc sur le réel et pas sur eux — le
# process démarre, sert la démonstration, et rend une 500 sur la première requête qui touche la
# colonne absente. C'est exactement ce qui s'est produit.
#
# ON APPELLE L'OUTIL EXISTANT plutôt que de refaire sa boucle ici : lui lit la liste des schémas
# DANS LA BASE — donc un schéma ajouté sans passer par `demos.conf` est rattrapé quand même — et
# il s'arrête au premier échec en nommant le fautif. Deux endroits qui savent migrer des
# démonstrations, c'est un endroit de trop.
#
# REJOUABLE : un schéma déjà à jour ne fait rien. On le passe à chaque déploiement.
#
# AVANT LE CONTRÔLE, jamais après : le contrôle interroge chaque démonstration, et une
# démonstration en retard d'une migration est précisément ce qu'il doit trouver en panne.
PYTHON_APP="${PYTHON_APP:-$APP_DIR/.venv/bin/python}"
if [ -x "$PYTHON_APP" ] && [ -f outils_bdd/migrer_les_demos.py ]; then
    DATABASE_URL="$DB_PREFIXE/$BASE_DEMOS" "$PYTHON_APP" outils_bdd/migrer_les_demos.py
else
    echo "  ATTENTION : $PYTHON_APP ou outils_bdd/migrer_les_demos.py introuvable."
    echo "  Les schémas de démonstration N'ONT PAS été mis à jour."
    exit 1
fi

echo ""
echo "=== [demos 7/7] Contrôle ==="
# On INTERROGE chaque démonstration au lieu de se contenter de « le service est actif » : un
# uvicorn qui démarre puis se plante sur un schéma absent reste « actif » quelques secondes.
# La question se pose maintenant au SEUL port, en variant l'en-tête `Host` — c'est exactement
# ce que fait nginx, et c'est le seul contrôle qui prouve que l'aiguillage fonctionne.
sleep 2
echec=0
while IFS=: read -r base port sous_domaine; do
    reponse=$(curl -sf --max-time 5 -H "Host: $sous_domaine" \
        "http://127.0.0.1:$PORT_DEMOS/api/demo/etat" || echo "")
    if echo "$reponse" | grep -q '"mode_demo":true'; then
        couple=$(echo "$reponse" | sed -n 's/.*"couple":"\([^"]*\)".*/\1/p')
        echo "  OK   $sous_domaine  →  $couple"
    else
        echo "  ÉCHEC $sous_domaine : $reponse"
        echec=1
    fi
done < <(lignes)

[ "$echec" -eq 0 ] || { echo ""; echo "Au moins une démonstration ne répond pas."; exit 1; }
echo ""
echo "Les démonstrations sont en ligne, servies par un seul process."
