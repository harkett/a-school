#!/bin/bash
# A-SCHOOL — Script de déploiement VPS
# Usage : bash deploy/deploy.sh (depuis /var/www/a-school)
set -e

APP_DIR="/var/www/a-school"
cd "$APP_DIR"

echo ""
echo "=== [1/7] Git pull ==="
git pull

echo ""
echo "=== [2/7] Python venv + dépendances ==="
[ ! -d .venv ] && python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

echo ""
echo "=== [3/7] Build frontend React ==="
cd frontend
npm ci --silent
npm run build
cd "$APP_DIR"

echo ""
echo "=== [4/7] Variables .env manquantes ==="
if ! grep -q "JWT_SECRET" .env; then
    JWT=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    echo "JWT_SECRET=$JWT" >> .env
    echo "  → JWT_SECRET généré et ajouté"
fi
grep -q "APP_URL" .env         || echo "APP_URL=https://school.afia.fr"   >> .env
grep -q "ADMIN_EMAIL" .env     || echo "ADMIN_EMAIL=harketti@afia.fr"     >> .env
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
echo "=== [7/7] Test API ==="
sleep 1
curl -sf http://127.0.0.1:8001/api/health && echo " → Backend OK" || echo " → ERREUR backend"

echo ""
echo "================================================"
echo "  DEPLOY TERMINE"
echo "  https://school.afia.fr"
echo "================================================"
echo ""
