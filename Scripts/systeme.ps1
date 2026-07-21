# ─────────────────────────────────────────────────────
# aSchool — LE SYSTÈME (la boîte). Une seule commande.
# Usage : .\Scripts\systeme.ps1
# Identique sur A et sur B. Construit la boîte + lance tout,
# projet et données montés DEPUIS LE DOSSIER (dehors).
# ─────────────────────────────────────────────────────
$root = Split-Path -Parent $PSScriptRoot
docker compose -f "$root\docker-compose.yml" up --build
