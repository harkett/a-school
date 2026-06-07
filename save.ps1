# ─────────────────────────────────────────────────────────────
# Save A-SCHOOL → GitHub UNIQUEMENT
# Usage : .\save.ps1
# Sauvegarde distante. NE déploie PAS la prod. NE bump PAS la version.
# ─────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "Sauvegarde GitHub (aucun deploiement prod)..." -ForegroundColor Cyan

git push

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors du push GitHub." -ForegroundColor Red
    exit 1
}

Write-Host "GitHub OK -- la prod n'a pas bouge." -ForegroundColor Green
