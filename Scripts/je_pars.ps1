# ─────────────────────────────────────────────────────────────
#  je_pars.ps1 — à lancer sur le poste que vous QUITTEZ.
#
#  Il place TOUT votre travail dans le dossier A-SCHOOL, puis ferme
#  l'application. Ensuite vous copiez le dossier A-SCHOOL sur l'autre
#  poste, et vous y lancez Scripts\j_arrive.ps1.
#
#  Ce script ne connaît aucune lettre de lecteur : il se repère depuis
#  son propre emplacement. Il fonctionne donc à l'identique que le
#  dossier soit sur C:, sur D: ou ailleurs.
# ─────────────────────────────────────────────────────────────

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$racine  = Split-Path -Parent $PSScriptRoot
Set-Location $racine

$bagage         = Join-Path $racine 'Bagage'
$fichierTravail = Join-Path $bagage 'travail.aschool'
$fichierDate    = Join-Path $bagage 'depart.txt'

function Echec($message) {
    Write-Host ""
    Write-Host "  $message" -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "  A-SCHOOL — je pars" -ForegroundColor Cyan
Write-Host "  ══════════════════" -ForegroundColor Cyan
Write-Host ""

# ── 1/3  Tout doit être en marche pour pouvoir récupérer votre travail ──
Write-Host "  1/3  Vérification..." -ForegroundColor Cyan

docker info -f "{{.ServerVersion}}" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec "Docker Desktop n'est pas démarré. Lancez-le, attendez qu'il soit vert, puis relancez ce script."
}

docker compose up -d db 2>$null | Out-Null
$pret = $false
for ($essai = 0; $essai -lt 60; $essai++) {
    docker compose exec -T db pg_isready -U aschool -d aschool_dev 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $pret = $true; break }
    Start-Sleep -Seconds 2
}
if (-not $pret) {
    Echec "Impossible d'accéder à votre travail sur ce poste. Rien n'a été modifié."
}
Write-Host "       tout répond." -ForegroundColor Green

# ── 2/3  Votre travail entre dans le dossier ────────────────────────────
# C'est la raison d'être de ce script : votre travail ne se trouve pas
# dans le dossier, il vit à côté. On le fait donc entrer dans le dossier,
# pour que la copie l'emporte réellement.
Write-Host "  2/3  Je place votre travail dans le dossier..." -ForegroundColor Cyan

New-Item -ItemType Directory -Force -Path $bagage | Out-Null

docker compose exec -T db pg_dump -U aschool -d aschool_dev -Fc -f /tmp/aschool_bascule 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec "Votre travail n'a pas pu être récupéré. Rien n'a été modifié, vous pouvez relancer ce script."
}

docker compose cp db:/tmp/aschool_bascule "$fichierTravail" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec "Votre travail n'a pas pu être placé dans le dossier. Rien n'a été modifié, vous pouvez relancer ce script."
}

if (-not (Test-Path $fichierTravail)) {
    Echec "Votre travail n'a pas pu être placé dans le dossier. Rien n'a été modifié, vous pouvez relancer ce script."
}
$taille = (Get-Item $fichierTravail).Length
if ($taille -lt 1024) {
    Echec "Le travail récupéré est vide, ce n'est pas normal. Rien n'a été modifié, vous pouvez relancer ce script."
}

# La date du départ voyage avec le travail : à l'arrivée, elle sert à
# vérifier que l'autre poste ne contient pas quelque chose de plus récent.
[DateTimeOffset]::UtcNow.ToUnixTimeSeconds().ToString() | Set-Content -Path $fichierDate -Encoding ascii

Write-Host ("       c'est fait ({0:N0} Ko)." -f ($taille / 1KB)) -ForegroundColor Green

# ── 3/3  Fermer l'application pour libérer le dossier ───────────────────
Write-Host "  3/3  Fermeture de l'application..." -ForegroundColor Cyan
docker compose stop 2>$null | Out-Null
Write-Host "       fermée." -ForegroundColor Green

Write-Host ""
Write-Host "  C'est prêt. Copiez maintenant le dossier A-SCHOOL sur l'autre poste." -ForegroundColor Green
Write-Host "  Là-bas, lancez :  Scripts\j_arrive.ps1" -ForegroundColor Green
Write-Host ""
