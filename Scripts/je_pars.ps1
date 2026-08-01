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
# L'unité suit la taille réelle : un .env de 4 Ko ne doit pas s'afficher « 0,0 Mo ».
function Poids($octets) {
    if ($octets -ge 1MB) { return "{0:N0} Mo" -f ($octets / 1MB) }
    if ($octets -ge 1KB) { return "{0:N0} Ko" -f ($octets / 1KB) }
    return "{0:N0} octets" -f $octets
}

function Mesure($chemin) {
    if (-not (Test-Path $chemin)) { return $null }
    $fichiers = @(Get-ChildItem $chemin -Recurse -Force -File -ErrorAction SilentlyContinue)
    $octets   = ($fichiers | Measure-Object -Sum Length).Sum
    if ($null -eq $octets) { $octets = 0 }
    if ($fichiers.Count -le 1) { return (Poids $octets) }
    return "{0:N0} fichiers, {1}" -f $fichiers.Count, (Poids $octets)
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

# La copie de sécurité prise lors d'une arrivée appartient à CE poste : elle
# n'a rien à faire dans le voyage, et elle doublerait le poids à copier.
Remove-Item (Join-Path $bagage 'avant_installation.aschool') -Force -ErrorAction SilentlyContinue

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

# ── La copie, faite ici plutôt que laissée à faire ──────────────────────
# Choisir cinq choses à la main dans l'explorateur, c'est l'endroit où on se
# trompe. Si la clé est branchée, on copie et on vérifie chaque fichier.
Write-Host ""
Write-Host "  Branchez votre clé maintenant et indiquez-la (par exemple  E:  )," -ForegroundColor Cyan
Write-Host "  je copie tout dessus et je vérifie. Ou Entrée pour le faire vous-même." -ForegroundColor Cyan
Write-Host ""
$ou = ''
try { $ou = Read-Host "  Où copier" } catch { $ou = '' }
$ou = "$ou".Trim().Trim('"')

if (-not $ou) {
    Write-Host ""
    Write-Host "  Entendu. Ensuite, sur l'autre poste, lancez :  Scripts\j_arrive.ps1" -ForegroundColor Green
    Write-Host ""
    exit 0
}

if (-not (Test-Path $ou)) {
    Echec "Cet endroit n'existe pas : $ou`n  Le dossier est prêt : copiez les trois éléments vous-même."
}

$valise = Join-Path $ou 'A-SCHOOL-a-emporter'
Write-Host ""
Write-Host "  Copie vers $valise ..." -ForegroundColor Cyan
if (Test-Path $valise) { Remove-Item -LiteralPath $valise -Recurse -Force -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Force -Path $valise | Out-Null

# Les deux fichiers d'installation partent aussi : ils ne servent que sur un
# poste où le dossier n'existe pas encore, et là-bas rien d'autre ne les fournit.
$aCopier = @($bagage, (Join-Path $racine 'REFERENTIELS'), (Join-Path $racine '.env'),
             (Join-Path $PSScriptRoot 'j_installe.ps1'), (Join-Path $PSScriptRoot 'j_installe.cmd'))

foreach ($element in $aCopier) {
    if (-not (Test-Path $element)) { continue }
    if ((Get-Item $element -Force).PSIsContainer) {
        Copy-Item -LiteralPath $element -Destination $valise -Recurse -Force -ErrorAction SilentlyContinue
    } else {
        Copy-Item -LiteralPath $element -Destination $valise -Force -ErrorAction SilentlyContinue
    }
}

# Vérification : chaque fichier est relu des deux côtés et comparé. Une copie
# annoncée sans être vérifiée, c'est ce qui a coûté une journée.
$ecarts = @()
$comptes = 0
foreach ($element in $aCopier) {
    if (-not (Test-Path $element)) { continue }
    $item = Get-Item $element -Force
    if ($item.PSIsContainer) {
        $base = Split-Path $element -Parent
        foreach ($f in Get-ChildItem -LiteralPath $element -Recurse -Force -File) {
            $relatif = $f.FullName.Substring($base.Length + 1)
            $arrivee = Join-Path $valise $relatif
            $comptes++
            if (-not (Test-Path -LiteralPath $arrivee)) { $ecarts += $relatif; continue }
            if ((Get-FileHash -LiteralPath $arrivee).Hash -ne (Get-FileHash -LiteralPath $f.FullName).Hash) { $ecarts += $relatif }
        }
    } else {
        $arrivee = Join-Path $valise $item.Name
        $comptes++
        if (-not (Test-Path -LiteralPath $arrivee)) { $ecarts += $item.Name }
        elseif ((Get-FileHash -LiteralPath $arrivee).Hash -ne (Get-FileHash -LiteralPath $item.FullName).Hash) { $ecarts += $item.Name }
    }
}

if ($ecarts.Count -gt 0) {
    Write-Host ""
    Write-Host "  Ces fichiers ne sont pas arrivés correctement :" -ForegroundColor Red
    foreach ($e in $ecarts | Select-Object -First 10) { Write-Host "      $e" -ForegroundColor Red }
    Echec "La copie n'est pas fiable. Videz la clé et relancez ce script."
}

Write-Host ("       $comptes fichiers copiés, tous vérifiés un par un.") -ForegroundColor Green
Write-Host ""
Write-Host "  Votre clé est prête. Sur l'autre poste :" -ForegroundColor Green
Write-Host ""
Write-Host "     — s'il a déjà le dossier A-SCHOOL : collez-y Bagage, REFERENTIELS" -ForegroundColor Green
Write-Host "       et .env, puis lancez Scripts\j_arrive.ps1" -ForegroundColor Green
Write-Host ""
Write-Host "     — s'il ne l'a pas, ou qu'il est à refaire : posez j_installe.ps1" -ForegroundColor Green
Write-Host "       et j_installe.cmd sur le Bureau, et double-cliquez j_installe.cmd" -ForegroundColor Green
Write-Host ""
