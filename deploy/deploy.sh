#!/bin/bash
# A-SCHOOL — Script de déploiement VPS
# Usage : bash deploy/deploy.sh (depuis /var/www/a-school)
set -e

APP_DIR="/var/www/a-school"
cd "$APP_DIR"

echo ""
echo "=== [Controle] Verification des variables .env requises ==="
# Garde-fou : on verifie la PRESENCE (ligne non vide) des variables obligatoires — jamais leur VALEUR.
# ENV fait exception : sa valeur doit etre exactement 'production' (sinon cookies de session non securises).
if [ ! -f .env ]; then
    echo "ERREUR : fichier .env introuvable dans $APP_DIR — deploiement interrompu."
    exit 1
fi
# ADMIN_JWT_SECRET n'est PAS requis : le code retombe sur JWT_SECRET si absent (backend/systeme/admin.py:32).
REQUISES="DATABASE_URL ADMIN_USERNAME ADMIN_PASSWORD CLAUDE_API_KEY_TEXTE SMTP_HOST SMTP_PORT SMTP_USERNAME SMTP_PASSWORD SMTP_FROM"
manquantes=""
for v in $REQUISES; do
    grep -qE "^${v}=.+" .env || manquantes="$manquantes $v"
done
grep -qE "^ENV=production$" .env || manquantes="$manquantes ENV(doit=production)"
if [ -n "$manquantes" ]; then
    echo "ERREUR : variables .env absentes/vides ou incorrectes :$manquantes"
    echo "  → completer le .env du serveur puis relancer. Deploiement interrompu."
    exit 1
fi
echo "  → toutes les variables requises sont presentes."

echo ""
echo "=== [1/7] Git pull ==="
git pull

echo ""
echo "=== [2/7] Python venv + dépendances ==="
[ ! -d .venv ] && python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

echo ""
echo "=== [2.2/7] Migrations base (Alembic) ==="
.venv/bin/alembic upgrade head

echo ""
echo "=== [3/7] Build frontend React ==="
cd frontend
npm ci --silent
npm run build
cd "$APP_DIR"

echo ""
echo "=== [4/7] Variables .env manquantes ==="
# ANCRÉ (`^JWT_SECRET=`) et pas `grep -q "JWT_SECRET"` : le motif large est aussi satisfait par
# une ligne ADMIN_JWT_SECRET=… — donc un serveur portant le secret admin RECOMMANDÉ, et lui
# seul, faisait croire au script que JWT_SECRET existait et repartait sans le générer. Les
# jetons des PROFS étaient alors signés avec le repli du code (mesuré le 02/08 :
# « change-me-in-production », un jeton forgé accepté). Le repli a disparu — sans cette
# correction, le même .env ferait maintenant refuser le démarrage, ce qui est mieux mais
# n'était pas la peine.
if ! grep -qE "^JWT_SECRET=.+" .env; then
    JWT=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    echo "JWT_SECRET=$JWT" >> .env
    echo "  → JWT_SECRET généré et ajouté"
fi
grep -q "APP_URL" .env              || echo "APP_URL=https://aschool.fr"        >> .env
grep -q "ADMIN_EMAIL" .env          || echo "ADMIN_EMAIL=harketti@afia.fr"           >> .env
grep -q "FEEDBACK_NOTIFY_EMAIL" .env || echo "FEEDBACK_NOTIFY_EMAIL=contact@afia.fr" >> .env
# ALLOWED_EMAILS volontairement absent — comportement identique au dev (tout le monde peut s'inscrire)

echo ""
echo "=== [5/7] Service systemd ==="
sudo cp deploy/aschool.service /etc/systemd/system/aschool.service
sudo systemctl daemon-reload
sudo systemctl enable aschool
sudo systemctl restart aschool
sleep 2
sudo systemctl status aschool --no-pager

echo ""
echo "=== [6/7] Nginx ==="
sudo cp deploy/nginx-aschool.conf /etc/nginx/sites-available/aschool
sudo ln -sf /etc/nginx/sites-available/aschool /etc/nginx/sites-enabled/aschool
# Désactiver l'ancienne config Streamlit si elle existe
[ -L /etc/nginx/sites-enabled/default ] && sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

echo ""
echo "=== [7/8] Test API ==="
sleep 1
curl -sf http://127.0.0.1:8001/api/health && echo " → Backend OK" || echo " → ERREUR backend"

echo ""
echo "=== [8/8] Demonstrations ==="
# L'INFRASTRUCTURE des cinq demonstrations : fichiers d'environnement, services systemd, blocs
# nginx. Ce geste ne touche AUCUNE donnee — le contenu des bases est l'affaire de
# `deploy/restaurer-bases.sh`, lance separement depuis le poste par `Scripts\deployer-donnees.ps1`.
# Il est rejouable : on le passe a chaque deploiement pour qu'une demonstration ajoutee dans
# `deploy/demos.conf` soit servie sans geste manuel.
if [ -f deploy/installer-demos.sh ]; then
    bash deploy/installer-demos.sh
else
    echo "  deploy/installer-demos.sh absent — demonstrations non installees."
fi

echo ""
echo "================================================"
echo "  DEPLOY TERMINE"
echo "  https://aschool.fr"
echo "================================================"
echo ""
