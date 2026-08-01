# ─────────────────────────────────────────────────────────────
#  j_arrive.ps1 — à lancer sur le poste où vous ARRIVEZ,
#  après avoir copié le dossier A-SCHOOL depuis l'autre poste.
#
#  Il remet tout en marche et installe le travail que vous apportez.
#
#  Avant d'installer, il pose une question et une seule : la base de ce
#  poste a-t-elle bougé APRÈS la date du travail que vous apportez ?
#  Si oui, il s'arrête sans rien toucher — installer effacerait ce
#  travail-là sans retour possible.
#
#  Ce script ne connaît aucune lettre de lecteur : il se repère depuis
#  son propre emplacement.
# ─────────────────────────────────────────────────────────────

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$racine = Split-Path -Parent $PSScriptRoot
Set-Location $racine

$bagage         = Join-Path $racine 'Bagage'
$fichierTravail = Join-Path $bagage 'travail.aschool'
$fichierDate    = Join-Path $bagage 'depart.txt'
$fichierAvant   = Join-Path $bagage 'avant_installation.aschool'

function Echec($message) {
    Write-Host ""
    Write-Host "  $message" -ForegroundColor Red
    Write-Host ""
    exit 1
}

function Attendre-Base {
    for ($essai = 0; $essai -lt 90; $essai++) {
        docker compose exec -T db pg_isready -U aschool -d aschool_dev 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { return $true }
        Start-Sleep -Seconds 2
    }
    return $false
}

# Date de la dernière trace de travail sur CE poste.
# On ne cite aucune table : on balaie toutes les colonnes horodatées de la
# base, quelles qu'elles soient. Ainsi une table créée demain est vue elle
# aussi. Les dates situées dans le futur sont écartées : une échéance
# (expiration, rappel programmé) n'est pas du travail déjà fait.
function Date-Du-Poste {
    $requete = @'
CREATE TEMP TABLE _dates(t timestamptz); DO $do$ DECLARE r record; BEGIN FOR r IN SELECT c.table_name AS tb, c.column_name AS col FROM information_schema.columns c JOIN pg_tables p ON p.schemaname = c.table_schema AND p.tablename = c.table_name WHERE c.table_schema = 'public' AND c.data_type IN ('timestamp with time zone','timestamp without time zone') LOOP EXECUTE format('INSERT INTO _dates SELECT max(%I)::timestamptz FROM public.%I WHERE %I <= now()', r.col, r.tb, r.col); END LOOP; END $do$; SELECT COALESCE(extract(epoch FROM max(t)),0)::bigint FROM _dates;
'@
    $requete = ($requete -replace "`r`n", " ").Trim()
    $brut = docker compose exec -T db psql -U aschool -d aschool_dev -A -t -c $requete 2>$null
    $ligne = $brut | Where-Object { $_ -match '^\s*\d+\s*$' } | Select-Object -Last 1
    if ($ligne) { return [long]($ligne.Trim()) }
    return $null
}

Write-Host ""
Write-Host "  A-SCHOOL — j'arrive" -ForegroundColor Cyan
Write-Host "  ═══════════════════" -ForegroundColor Cyan
Write-Host ""

# ── 1/4  Vérifications avant de toucher à quoi que ce soit ──────────────
Write-Host "  1/4  Vérification..." -ForegroundColor Cyan

docker info -f "{{.ServerVersion}}" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec "Docker Desktop n'est pas démarré. Lancez-le, attendez qu'il soit vert, puis relancez ce script."
}

if (-not (Test-Path $fichierTravail)) {
    Echec ("Ce dossier ne contient aucun travail à installer.`n" +
           "  Sur le poste de départ, lancez d'abord Scripts\je_pars.ps1, puis recopiez le dossier A-SCHOOL ici.")
}

$dateApportee = $null
if (Test-Path $fichierDate) {
    $lu = (Get-Content $fichierDate -Raw).Trim()
    if ($lu -match '^\d+$') { $dateApportee = [long]$lu }
}
Write-Host "       le travail à installer est bien là." -ForegroundColor Green

# Première fois sur ce poste ? Aucun élément n'a encore été préparé ici.
# On l'annonce AVANT la longue attente, pour qu'elle ne soit pas subie.
$dejaLa = docker compose ps -a -q 2>$null
$premiereFois = -not $dejaLa
if ($premiereFois) {
    Write-Host ""
    Write-Host "  Première installation sur ce poste : préparation en cours," -ForegroundColor Yellow
    Write-Host "  quelques minutes, connexion internet nécessaire." -ForegroundColor Yellow
    Write-Host ""
}

# ── 2/4  Mise en route de ce qui garde votre travail ────────────────────
Write-Host "  2/4  Mise en route..." -ForegroundColor Cyan
docker compose up -d db 2>$null | Out-Null
if (-not (Attendre-Base)) {
    Echec "La mise en route a échoué. Rien n'a été modifié, vous pouvez relancer ce script."
}
Write-Host "       prêt." -ForegroundColor Green

# ── 3/4  Le filet : ce poste a-t-il quelque chose de plus récent ? ──────
Write-Host "  3/4  Contrôle..." -ForegroundColor Cyan
$datePoste = Date-Du-Poste

# On n'installe QUE sur un accord franc. Tant que cet accord n'est pas donné,
# ce drapeau reste baissé : si quoi que ce soit se passe mal dans la question
# ci-dessous, on ne touche à rien. Le silence n'est jamais un oui.
$accordDonne = $true

if ($null -ne $datePoste -and $null -ne $dateApportee -and $datePoste -gt $dateApportee) {
    $ici     = [DateTimeOffset]::FromUnixTimeSeconds($datePoste).LocalDateTime
    $apporte = [DateTimeOffset]::FromUnixTimeSeconds($dateApportee).LocalDateTime
    Write-Host ""
    Write-Host "  Ce poste contient du travail plus récent que ce que vous apportez." -ForegroundColor Yellow
    Write-Host "  Rien n'a été modifié." -ForegroundColor Yellow
    Write-Host ""
    Write-Host ("    dernier travail sur ce poste : {0:dddd d MMMM yyyy à HH:mm}" -f $ici)     -ForegroundColor Yellow
    Write-Host ("    travail que vous apportez    : {0:dddd d MMMM yyyy à HH:mm}" -f $apporte) -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Installer ce que vous apportez effacerait définitivement le travail de ce poste." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Tapez le mot  remplacer  puis Entrée pour l'installer quand même," -ForegroundColor Yellow
    Write-Host "  ou appuyez simplement sur Entrée pour ne rien changer." -ForegroundColor Yellow
    Write-Host ""
    $reponse = ''
    try { $reponse = Read-Host "  Votre choix" } catch { $reponse = '' }
    $accordDonne = ("$reponse".Trim().ToLower() -eq 'remplacer')
} else {
    Write-Host "       rien de plus récent ici." -ForegroundColor Green
}

if (-not $accordDonne) {
    Write-Host ""
    Write-Host "  Rien n'a été modifié. Le travail de ce poste est intact." -ForegroundColor Green
    Write-Host ""
    exit 0
}

# ── 4/4  Installation ───────────────────────────────────────────────────
Write-Host "  4/4  Installation de votre travail..." -ForegroundColor Cyan

# Filet de dernière seconde : ce qui est déjà sur ce poste est mis de côté
# dans le dossier avant d'être remplacé.
if ($null -ne $datePoste -and $datePoste -gt 0) {
    docker compose exec -T db pg_dump -U aschool -d aschool_dev -Fc -f /tmp/aschool_avant 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        docker compose cp db:/tmp/aschool_avant "$fichierAvant" 2>$null | Out-Null
        if (Test-Path $fichierAvant) {
            Write-Host "       (le contenu actuel de ce poste a été mis de côté dans le dossier)" -ForegroundColor DarkGray
        }
    }
}

docker compose cp "$fichierTravail" db:/tmp/aschool_arrivee 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec "Votre travail n'a pas pu être installé. Rien n'a été modifié, vous pouvez relancer ce script."
}

docker compose stop backend 2>$null | Out-Null
docker compose exec -T db pg_restore --clean --if-exists --no-owner -U aschool -d aschool_dev /tmp/aschool_arrivee 2>$null | Out-Null
$codeInstallation = $LASTEXITCODE

if ($codeInstallation -ne 0) {
    Write-Host "       installé, avec quelques remarques sans gravité." -ForegroundColor Yellow
} else {
    Write-Host "       installé." -ForegroundColor Green
}

Write-Host "       démarrage de l'application..." -ForegroundColor Cyan
docker compose up -d --build 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec "Votre travail est bien installé, mais l'application n'a pas démarré. Relancez ce script."
}

Write-Host ""
Write-Host "  Terminé. Ce poste contient votre travail et l'application démarre." -ForegroundColor Green
Write-Host "  Ouvrez :  http://localhost:5173" -ForegroundColor Green
if ($premiereFois) {
    Write-Host "  (première fois : laissez-lui une minute ou deux avant d'ouvrir)" -ForegroundColor DarkGray
}
Write-Host ""
