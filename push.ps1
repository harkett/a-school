# ─────────────────────────────────────
# Push rapide A-SCHOOL vers GitHub
# Usage : .\push.ps1
#         .\push.ps1 "mon message"
# ─────────────────────────────────────

param(
    [string]$msg = ""
)

if ($msg -eq "") {
    $msg = Read-Host "Message du commit (Entrée = 'mise à jour')"
    if ($msg -eq "") { $msg = "mise à jour" }
}

git add .
git commit -m $msg
git push

Write-Host ""
Write-Host "✅ Poussé sur GitHub : https://github.com/harkett/a-school" -ForegroundColor Green
