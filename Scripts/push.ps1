# ─────────────────────────────────────────────────────────────
# push.ps1 — Sauvegarde sur GitHub
# Pousse vers GitHub les commits déjà créés et validés en local.
# Ne s'exécute qu'après au moins un commit, et seulement quand tu
# le valides : Claude le propose, tu valides, puis exécution.
# ─────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "Sauvegarde GitHub..." -ForegroundColor Cyan

git push

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors du push GitHub." -ForegroundColor Red
    exit 1
}

Write-Host "GitHub OK." -ForegroundColor Green
