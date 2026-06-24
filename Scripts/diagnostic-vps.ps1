# ─────────────────────────────────────────────────────────────
# diagnostic-vps.ps1 — A-SCHOOL : diagnostic serveur, LECTURE SEULE
# Usage : .\Scripts\diagnostic-vps.ps1
# Ne modifie RIEN sur le VPS — uniquement des commandes de lecture.
# ─────────────────────────────────────────────────────────────
$VPS_USER = "ubuntu"
$VPS_HOST = "83.228.245.163"

Write-Host "Diagnostic VPS aSchool ($VPS_HOST) - lecture seule" -ForegroundColor Cyan

ssh "$VPS_USER@$VPS_HOST" @'
echo '===== CHARGE MOYENNE 1/5/15 min ====='; uptime
echo; echo '===== COEURS ====='; nproc
echo; echo '===== MEMOIRE ====='; free -h
echo; echo '===== DISQUE ====='; df -h /
echo; echo '===== TOP 10 PROCESSUS CPU ====='; top -bn1 | head -17
echo; echo '===== HISTORIQUE CPU DU JOUR sar, par 10 min ====='; LC_ALL=C sar | tail -20
'@
