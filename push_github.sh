#!/bin/bash
# ─────────────────────────────────────────────
# Script de push initial A-SCHOOL vers GitHub
# Usage : bash push_github.sh
# ─────────────────────────────────────────────

echo ""
echo "=== Push A-SCHOOL vers GitHub ==="
echo ""

# 1. Demander l'URL du repo GitHub
read -p "URL du repo GitHub (ex: https://github.com/tonuser/a-school.git) : " REPO_URL

if [ -z "$REPO_URL" ]; then
  echo "❌ URL manquante. Abandon."
  exit 1
fi

# 2. Initialiser git si pas déjà fait
if [ ! -d ".git" ]; then
  echo "→ Initialisation du repo git..."
  git init
  git branch -M main
fi

# 3. Ajouter le remote si pas déjà configuré
if ! git remote | grep -q "origin"; then
  echo "→ Ajout du remote origin..."
  git remote add origin "$REPO_URL"
else
  echo "→ Remote origin déjà configuré."
  git remote set-url origin "$REPO_URL"
fi

# 4. Ajouter les fichiers et committer
echo "→ Ajout des fichiers..."
git add .
git status

echo ""
read -p "Message du commit (Entrée = 'Initial commit A-SCHOOL') : " MSG
MSG=${MSG:-"Initial commit A-SCHOOL"}

git commit -m "$MSG"

# 5. Pousser
echo "→ Push vers GitHub..."
git push -u origin main

echo ""
echo "✅ Projet poussé sur GitHub : $REPO_URL"
echo "   Prêt pour le déploiement sur le VPS."
