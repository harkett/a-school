#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# installer-demos.sh — pose sur le VPS tout ce qu'il faut pour servir les démonstrations.
#
# CE QU'IL FAIT, et rien d'autre : il installe l'INFRASTRUCTURE (fichiers d'environnement,
# services systemd, blocs nginx). Il ne touche à AUCUNE donnée — les bases sont l'affaire de
# `restaurer-bases.sh`. Les deux sont séparés parce qu'on les relance pour des raisons
# différentes : celui-ci à chaque déploiement, l'autre seulement quand on veut écraser le
# contenu du serveur par celui du poste.
#
# IL EST REJOUABLE. Chaque geste est idempotent : réécrire un fichier identique, réactiver un
# service déjà actif, relire une configuration nginx déjà en place. Un script de déploiement
# qu'on hésite à relancer est un script qu'on finit par ne plus lancer du tout.
#
# Usage : bash deploy/installer-demos.sh    (depuis /var/www/a-school)
# ─────────────────────────────────────────────────────────────────────────────
set -e

APP_DIR="${APP_DIR:-/var/www/a-school}"
cd "$APP_DIR"

LISTE="deploy/demos.conf"
DOSSIER_ENV="deploy/env-demos"
NGINX_DEMOS="/etc/nginx/sites-available/aschool-demos"

[ -f "$LISTE" ] || { echo "ERREUR : $LISTE introuvable."; exit 1; }

# La base réelle donne le modèle de la chaîne de connexion : les démonstrations vivent sur le
# MÊME PostgreSQL, seul le nom de la base change. On la relit du .env plutôt que de la
# réécrire — un identifiant recopié est un identifiant qui divergera.
DB_MODELE=$(grep -E "^DATABASE_URL=" .env | head -1 | cut -d= -f2-)
[ -n "$DB_MODELE" ] || { echo "ERREUR : DATABASE_URL absente du .env."; exit 1; }
DB_PREFIXE="${DB_MODELE%/*}"      # tout jusqu'au dernier / : le serveur et ses identifiants

lignes() { grep -vE "^\s*#|^\s*$" "$LISTE"; }

echo ""
echo "=== [demos 1/5] Fichiers d'environnement ==="
mkdir -p "$DOSSIER_ENV"
while IFS=: read -r base port sous_domaine; do
    cat > "$DOSSIER_ENV/$base.env" <<EOF
# Écrit par deploy/installer-demos.sh — ne pas modifier à la main, il sera réécrit.
# La seule chose qui distingue cette démonstration des autres.
DATABASE_URL=$DB_PREFIXE/$base
PORT_DEMO=$port
MODE_DEMO=1
EOF
    echo "  → $base.env (port $port)"
done < <(lignes)

echo ""
echo "=== [demos 2/5] Services systemd ==="
sudo cp deploy/aschool-demo@.service /etc/systemd/system/aschool-demo@.service
sudo systemctl daemon-reload
while IFS=: read -r base port sous_domaine; do
    sudo systemctl enable "aschool-demo@$base" >/dev/null
    sudo systemctl restart "aschool-demo@$base"
    echo "  → aschool-demo@$base démarré"
done < <(lignes)

echo ""
echo "=== [demos 3/5] Certificat HTTPS ==="
# LE PIÈGE QUE NGINX NE SIGNALE PAS. Les blocs ci-dessous réutilisent le certificat
# d'`aschool.fr`. Or un certificat ne vaut QUE pour les noms qu'il porte : servir
# `demo-crsa.aschool.fr` avec le certificat d'`aschool.fr` donne une alerte de sécurité en
# pleine figure du visiteur — et `nginx -t` la trouve parfaitement valide, puisque le fichier
# existe. On vérifie donc les noms du certificat, et on l'étend s'il en manque.
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
    # `--nginx` valide par HTTP-01 en modifiant nginx le temps de l'échange : pas besoin d'un
    # certificat joker, donc pas de validation DNS à configurer chez l'hébergeur.
    sudo certbot certonly --nginx --expand --cert-name aschool.fr \
        -d aschool.fr -d www.aschool.fr $absents \
        --non-interactive --agree-tos --keep-until-expiring
    echo "  → certificat étendu"
fi

echo ""
echo "=== [demos 4/5] Blocs nginx ==="
# UN SEUL BUILD FRONT sert les cinq : `root` pointe le même `dist` que l'application réelle.
# Ce qui change d'une démonstration à l'autre, c'est UNIQUEMENT le port derrière `/api/`.
# Le front n'a donc rien à savoir de la démonstration où il tourne — il interroge `/api/`,
# nginx l'envoie au bon backend, et c'est le backend qui répond `mode_demo: true`.
{
    echo "# Écrit par deploy/installer-demos.sh à partir de deploy/demos.conf."
    echo "# Toute modification faite ici sera perdue au prochain déploiement."
    while IFS=: read -r base port sous_domaine; do
        cat <<EOF

server {
    listen 80;
    server_name $sous_domaine;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name $sous_domaine;

    ssl_certificate     /etc/letsencrypt/live/aschool.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aschool.fr/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    root  /var/www/a-school/frontend/dist;
    index index.html;

    location /api/ {
        proxy_pass         http://127.0.0.1:$port;
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
    done < <(lignes)
} | sudo tee "$NGINX_DEMOS" > /dev/null

sudo ln -sf "$NGINX_DEMOS" /etc/nginx/sites-enabled/aschool-demos
sudo nginx -t
sudo systemctl reload nginx
echo "  → nginx rechargé"

echo ""
echo "=== [demos 5/5] Contrôle ==="
# On INTERROGE chaque démonstration au lieu de se contenter de « le service est actif » : un
# uvicorn qui démarre puis se plante sur une base absente reste « actif » quelques secondes.
# `/api/demo/etat` est la bonne question : elle dit le couple servi, donc que la base répond.
sleep 2
echec=0
while IFS=: read -r base port sous_domaine; do
    reponse=$(curl -sf --max-time 5 "http://127.0.0.1:$port/api/demo/etat" || echo "")
    if echo "$reponse" | grep -q '"mode_demo":true'; then
        couple=$(echo "$reponse" | sed -n 's/.*"couple":"\([^"]*\)".*/\1/p')
        echo "  OK   $sous_domaine  →  $couple"
    else
        echo "  ÉCHEC $sous_domaine (port $port) : $reponse"
        echec=1
    fi
done < <(lignes)

[ "$echec" -eq 0 ] || { echo ""; echo "Au moins une démonstration ne répond pas."; exit 1; }
echo ""
echo "Les démonstrations sont en ligne."
