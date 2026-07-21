# ─────────────────────────────────────────────────────────────
# quitter_bureau.ps1 — À lancer sur le poste que tu QUITTES.
# Sauvegarde la base + pousse TOUT sur GitHub, et surveille ton .env.
# Ensuite, sur l'autre poste : retour_bureau.ps1 rend le poste identique.
# ─────────────────────────────────────────────────────────────
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# ── 1/4  Sauvegarde de la base dans un fichier ─────────────────
Write-Host "1/4  Sauvegarde de la base..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "$root\db_backup" | Out-Null
# Le dump est ecrit DANS le conteneur, puis copie octet par octet vers l'hote
# (docker compose cp = seule methode fiable ; une redirection '>' abimerait le fichier binaire).
docker compose exec -T db pg_dump -U aschool -d aschool_dev -Fc -f /tmp/aschool.dump
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERREUR : la base n'a pas pu etre sauvegardee. Docker est-il demarre ?" -ForegroundColor Red
    exit 1
}
docker compose cp db:/tmp/aschool.dump "$root\db_backup\aschool.dump"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERREUR : la copie de la sauvegarde a echoue." -ForegroundColor Red
    exit 1
}
Write-Host "     base sauvegardee -> db_backup\aschool.dump" -ForegroundColor Green

# ── 2/4  Empreinte du .env (pour te prevenir s'il a change) ────
# On calcule une SIGNATURE du .env (pas son contenu : aucun secret ne part sur GitHub).
# Si elle a change depuis la derniere fois -> gros rappel de le copier sur l'autre poste.
Write-Host "2/4  Verification du .env..." -ForegroundColor Cyan
if (Test-Path "$root\.env") {
    $empreinte = (Get-FileHash "$root\.env" -Algorithm SHA256).Hash
    $fichierEmpreinte = "$root\db_backup\env.empreinte.txt"
    $ancienne = if (Test-Path $fichierEmpreinte) { Get-Content $fichierEmpreinte } else { "" }
    $empreinte | Set-Content $fichierEmpreinte
    if ($empreinte -ne $ancienne) {
        Write-Host "  ATTENTION : ton .env a CHANGE depuis la derniere fois." -ForegroundColor Yellow
        Write-Host "  -> Copie ton .env sur l'autre poste (il ne part PAS sur GitHub)." -ForegroundColor Yellow
    } else {
        Write-Host "     .env inchange, rien a copier." -ForegroundColor Green
    }
} else {
    Write-Host "  (pas de .env trouve — rien a surveiller)" -ForegroundColor DarkGray
}

# ── 3/4  Tout ajouter + enregistrer (commit) ───────────────────
Write-Host "3/4  Enregistrement..." -ForegroundColor Cyan
git add -A
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "     Rien de nouveau a enregistrer." -ForegroundColor DarkGray
} else {
    git commit -m "sauvegarde bureau"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERREUR : l'enregistrement (commit) a echoue." -ForegroundColor Red
        exit 1
    }
}

# ── 4/4  Envoyer sur GitHub ────────────────────────────────────
Write-Host "4/4  Envoi sur GitHub..." -ForegroundColor Cyan
git push
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERREUR : l'envoi sur GitHub a echoue." -ForegroundColor Red
    exit 1
}
Write-Host ""
Write-Host "  TERMINE. Tout est sur GitHub. Tu peux quitter ce poste." -ForegroundColor Green
