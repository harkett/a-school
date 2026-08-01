# ─────────────────────────────────────────────────────────────
#  je_pars.ps1 — à lancer sur le poste que vous QUITTEZ.
#
#  Il prépare le départ, puis affiche EXACTEMENT ce qu'il faut copier
#  sur l'autre poste. Le reste du dossier n'est pas à copier : il
#  arrive tout seul là-bas.
#
#  Pourquoi : copier le dossier entier a été essayé et a échoué. 87 000
#  fichiers, dont 68 000 pour .venv et frontend/node_modules, et surtout
#  12 fichiers du cache du modèle que l'explorateur Windows ne sait pas
#  copier (ce sont des liens créés depuis Linux). Ne voyagent donc que
#  les trois choses qui n'existent nulle part ailleurs.
#
#  Ce script ne connaît aucune lettre de lecteur : il se repère depuis
#  son propre emplacement. Il fonctionne à l'identique que le dossier
#  soit sur C:, sur D: ou ailleurs.
#
#  Il suppose que le dossier A-SCHOOL existe déjà sur l'autre poste.
# ─────────────────────────────────────────────────────────────

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$racine = Split-Path -Parent $PSScriptRoot
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

# Poids et nombre de fichiers d'un élément, pour l'annoncer tel qu'il est.
function Mesure($chemin) {
    if (-not (Test-Path $chemin)) { return $null }
    $fichiers = @(Get-ChildItem $chemin -Recurse -Force -File -ErrorAction SilentlyContinue)
    $octets   = ($fichiers | Measure-Object -Sum Length).Sum
    if ($null -eq $octets) { $octets = 0 }
    if ($fichiers.Count -le 1) { return "{0:N1} Mo" -f ($octets / 1MB) }
    return "{0:N0} fichiers, {1:N0} Mo" -f $fichiers.Count, ($octets / 1MB)
}

Write-Host ""
Write-Host "  A-SCHOOL — je pars" -ForegroundColor Cyan
Write-Host "  ══════════════════" -ForegroundColor Cyan
Write-Host ""

# ── 1/4  Le moteur doit tourner ─────────────────────────────────────────
Write-Host "  1/4  Vérification..." -ForegroundColor Cyan

docker info -f "{{.ServerVersion}}" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec "Docker Desktop n'est pas démarré. Lancez-le, attendez qu'il soit vert, puis relancez ce script."
}
Write-Host "       le moteur tourne." -ForegroundColor Green

# ── 2/4  Le code doit être parti, sinon il manquera là-bas ──────────────
# Le code ne voyage plus dans la copie : il passe par le dépôt. Donc tout
# ce qui n'est pas encore envoyé n'existera pas sur l'autre poste. On le
# dit avant de partir, on n'envoie rien à la place de l'utilisateur.
Write-Host "  2/4  Le code est-il déjà parti ?" -ForegroundColor Cyan

git rev-parse --is-inside-work-tree 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec "Ce dossier n'est pas relié au dépôt du code. Rien n'a été modifié."
}

git fetch --quiet 2>$null | Out-Null

$enCours  = @(git status --porcelain 2>$null | Where-Object { $_ })
$nonPartis = @(git log --oneline '@{u}..HEAD' 2>$null | Where-Object { $_ })

if ($enCours.Count -gt 0 -or $nonPartis.Count -gt 0) {
    Write-Host ""
    Write-Host "  Du travail de ce poste n'est pas encore envoyé." -ForegroundColor Yellow
    Write-Host "  Il ne serait pas sur l'autre poste. Rien n'a été modifié." -ForegroundColor Yellow
    Write-Host ""
    if ($nonPartis.Count -gt 0) {
        Write-Host "    Enregistré ici, mais pas encore envoyé :" -ForegroundColor Yellow
        foreach ($c in $nonPartis) { Write-Host "      $c" -ForegroundColor Yellow }
        Write-Host ""
    }
    if ($enCours.Count -gt 0) {
        Write-Host "    Modifié ici, pas même enregistré :" -ForegroundColor Yellow
        foreach ($f in $enCours) { Write-Host "      $f" -ForegroundColor Yellow }
        Write-Host ""
    }
    Echec "Faites partir ce travail, puis relancez ce script."
}
Write-Host "       tout le code est parti." -ForegroundColor Green

# ── 3/4  Votre travail entre dans le dossier ────────────────────────────
# Votre travail ne se trouve pas dans le dossier : il vit à côté. On le
# fait donc entrer dans le dossier, seul moyen de l'emporter.
Write-Host "  3/4  Je place votre travail dans le dossier..." -ForegroundColor Cyan

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

New-Item -ItemType Directory -Force -Path $bagage | Out-Null

docker compose exec -T db pg_dump -U aschool -d aschool_dev -Fc -f /tmp/aschool_bascule 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec "Votre travail n'a pas pu être récupéré. Rien n'a été modifié, vous pouvez relancer ce script."
}

docker compose cp db:/tmp/aschool_bascule "$fichierTravail" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $fichierTravail)) {
    Echec "Votre travail n'a pas pu être placé dans le dossier. Rien n'a été modifié, vous pouvez relancer ce script."
}
if ((Get-Item $fichierTravail).Length -lt 1024) {
    Echec "Le travail récupéré est vide, ce n'est pas normal. Rien n'a été modifié, vous pouvez relancer ce script."
}

# La date du départ voyage avec le travail : à l'arrivée, elle sert à
# vérifier que l'autre poste ne contient pas quelque chose de plus récent.
[DateTimeOffset]::UtcNow.ToUnixTimeSeconds().ToString() | Set-Content -Path $fichierDate -Encoding ascii
Write-Host "       c'est fait." -ForegroundColor Green

# ── 4/4  Fermer proprement ──────────────────────────────────────────────
# Après cette fermeture, plus rien ne bouge : le travail mis dans le
# dossier reste le reflet exact de ce poste.
Write-Host "  4/4  Fermeture de l'application..." -ForegroundColor Cyan
docker compose stop 2>$null | Out-Null
Write-Host "       fermée." -ForegroundColor Green

# ── Ce qu'il faut copier, nommé un par un ───────────────────────────────
$mBagage = Mesure $bagage
$mRefs   = Mesure (Join-Path $racine 'REFERENTIELS')
$mEnv    = Mesure (Join-Path $racine '.env')

Write-Host ""
Write-Host "  C'est prêt." -ForegroundColor Green
Write-Host ""
Write-Host "  Copiez SEULEMENT ces trois éléments, depuis ce dossier A-SCHOOL" -ForegroundColor Green
Write-Host "  vers le dossier A-SCHOOL de l'autre poste, en remplaçant :" -ForegroundColor Green
Write-Host ""
if ($mBagage) { Write-Host ("      Bagage           le dossier         ({0})" -f $mBagage) -ForegroundColor White }
if ($mRefs)   { Write-Host ("      REFERENTIELS     le dossier         ({0})" -f $mRefs)   -ForegroundColor White }
else          { Write-Host  "      REFERENTIELS     absent de ce poste — rien à copier" -ForegroundColor DarkGray }
if ($mEnv)    { Write-Host ("      .env             le fichier         ({0})" -f $mEnv)    -ForegroundColor White }
else          { Write-Host  "      .env             absent de ce poste — rien à copier" -ForegroundColor DarkGray }
Write-Host ""
Write-Host "  Ne copiez rien d'autre. Tout le reste du dossier arrive tout seul" -ForegroundColor Green
Write-Host "  là-bas : le code est déjà parti, et le reste se refabrique sur place." -ForegroundColor Green
Write-Host ""
Write-Host "  Ensuite, sur l'autre poste, lancez :  Scripts\j_arrive.ps1" -ForegroundColor Green
Write-Host ""
