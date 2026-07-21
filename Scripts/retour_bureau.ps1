# ─────────────────────────────────────────────────────────────
# retour_bureau.ps1 — À lancer sur le poste où tu ARRIVES.
# Récupère GitHub + réinstalle la base -> ce poste devient identique
# à celui que tu as quitté.
# Sécurité : si CE poste a du travail PLUS RÉCENT que GitHub, il s'arrête
# (sauf si tu forces avec -Force).
# ─────────────────────────────────────────────────────────────
param([switch]$Force)
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# ── 1/3  Récupérer GitHub (code + sauvegarde de la base) ───────
Write-Host "1/3  Recuperation depuis GitHub..." -ForegroundColor Cyan
git pull
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERREUR : la recuperation GitHub a echoue." -ForegroundColor Red
    exit 1
}
$dump = "$root\db_backup\aschool.dump"
if (-not (Test-Path $dump)) {
    Write-Host "  ERREUR : aucune sauvegarde trouvee (db_backup\aschool.dump)." -ForegroundColor Red
    exit 1
}

# ── 2/3  Sécurité par date (get, zéro copie) ───────────────────
# On compare en SECONDES UNIX (aucun souci de fuseau) :
#   - date de la derniere activite dans la base de CE poste
#   - date de la sauvegarde venue de GitHub (date du commit du dump)
Write-Host "2/3  Verification des dates..." -ForegroundColor Cyan
$sqlEpoch = "SELECT COALESCE(extract(epoch from GREATEST(" +
"(SELECT MAX(created_at)::timestamptz FROM activites_sauvegardees)," +
"(SELECT MAX(created_at)::timestamptz FROM admin_alerts)," +
"(SELECT MAX(timestamp)::timestamptz FROM admin_audit_log)," +
"(SELECT MAX(created_at)::timestamptz FROM connexion_logs)," +
"(SELECT MAX(created_at)::timestamptz FROM feedbacks)," +
"(SELECT MAX(updated_at)::timestamptz FROM feedbacks)," +
"(SELECT MAX(updated_at)::timestamptz FROM fiches_matieres)," +
"(SELECT MAX(created_at)::timestamptz FROM referentiels)," +
"(SELECT MAX(created_at)::timestamptz FROM referentiel_chunks)," +
"(SELECT MAX(created_at)::timestamptz FROM tool_usage_logs)," +
"(SELECT MAX(created_at)::timestamptz FROM types_activite)," +
"(SELECT MAX(last_seen)::timestamptz FROM user_sessions)," +
"(SELECT MAX(created_at)::timestamptz FROM users)," +
"(SELECT MAX(last_login)::timestamptz FROM users)" +
")),0)::bigint;"
$localEpoch  = (docker compose exec -T db psql -U aschool -d aschool_dev -A -t -c $sqlEpoch | Out-String).Trim()
$githubEpoch = (git log -1 --format=%ct -- db_backup/aschool.dump | Out-String).Trim()

if ($localEpoch -match '^\d+$' -and $githubEpoch -match '^\d+$') {
    $dl = [DateTimeOffset]::FromUnixTimeSeconds([long]$localEpoch).LocalDateTime
    $dg = [DateTimeOffset]::FromUnixTimeSeconds([long]$githubEpoch).LocalDateTime
    if ([long]$localEpoch -gt [long]$githubEpoch -and -not $Force) {
        Write-Host "  STOP : ce poste a du travail PLUS RECENT que GitHub." -ForegroundColor Yellow
        Write-Host "    Derniere activite ICI    : $dl" -ForegroundColor Yellow
        Write-Host "    Sauvegarde GitHub        : $dg" -ForegroundColor Yellow
        Write-Host "    Restaurer ecraserait ton travail recent. Rien n'a ete touche." -ForegroundColor Yellow
        Write-Host "    Pour ecraser quand meme : .\Scripts\retour_bureau.ps1 -Force" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "     OK (ici : $dl  /  GitHub : $dg)" -ForegroundColor Green
} else {
    Write-Host "     (pas de date a comparer — on restaure)" -ForegroundColor DarkGray
}

# ── 3/3  Réinstaller la base ───────────────────────────────────
# On copie la sauvegarde dans le conteneur, on arrete le backend (libere les
# connexions), on restaure, puis on redemarre le backend.
Write-Host "3/3  Reinstallation de la base..." -ForegroundColor Cyan
docker compose cp "$dump" db:/tmp/aschool.dump
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERREUR : impossible de copier la sauvegarde dans le conteneur." -ForegroundColor Red
    exit 1
}
docker compose stop backend | Out-Null
docker compose exec -T db pg_restore --clean --if-exists --no-owner -U aschool -d aschool_dev /tmp/aschool.dump
$restoreCode = $LASTEXITCODE
docker compose start backend | Out-Null
if ($restoreCode -ne 0) {
    Write-Host "  ATTENTION : la restauration a signale des avertissements (code $restoreCode)." -ForegroundColor Yellow
    Write-Host "  Verifie l'appli ; si besoin relance." -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "  TERMINE. Ce poste est identique a celui que tu as quitte." -ForegroundColor Green
}
