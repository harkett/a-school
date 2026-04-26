# ─────────────────────────────────────────────────────────────
# Push A-SCHOOL → GitHub + déploiement automatique sur VPS
# Usage : .\push.ps1
#         .\push.ps1 "mon message de commit"
# ─────────────────────────────────────────────────────────────

param(
    [string]$msg = ""
)

$VPS_USER = "ubuntu"
$VPS_HOST = "83.228.245.163"
$VPS_PATH = "/var/www/a-school"

if ($msg -eq "") {
    $msg = Read-Host "Message du commit (Entrée = 'mise à jour')"
    if ($msg -eq "") { $msg = "mise à jour" }
}

# ── 1. Push GitHub ────────────────────────────────────────────
Write-Host ""
Write-Host "1/2  Push GitHub..." -ForegroundColor Cyan
git add .
git commit -m $msg
git push

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors du push GitHub." -ForegroundColor Red
    exit 1
}

Write-Host "     GitHub OK" -ForegroundColor Green

# ── 2. Déploiement VPS ───────────────────────────────────────
Write-Host "2/2  Déploiement sur $VPS_HOST..." -ForegroundColor Cyan

ssh "$VPS_USER@$VPS_HOST" "cd $VPS_PATH && bash deploy/deploy.sh"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors du déploiement VPS." -ForegroundColor Red
    exit 1
}

Write-Host "     VPS OK" -ForegroundColor Green
Write-Host ""
Write-Host "Deploye sur https://school.afia.fr" -ForegroundColor Green
