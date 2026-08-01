# ─────────────────────────────────────────────────────────────
#  j_installe.ps1 — à copier sur le Bureau, et à lancer de là.
#
#  Il sert quand le dossier A-SCHOOL n'existe pas encore sur ce poste,
#  ou qu'il est à refaire. C'est le seul des trois scripts qui vit hors
#  du dossier : les deux autres sont dedans, ils ne peuvent donc pas le
#  créer.
#
#  Il installe le dossier, vous demande d'y coller les trois éléments
#  apportés, puis passe la main à j_arrive.ps1 qui fait le reste.
#
#  Aucune lettre de lecteur n'est écrite ici. L'endroit proposé est
#  calculé sur ce poste : le premier disque fixe autre que celui de
#  Windows, sinon celui de Windows. Sur un poste où C: est le système
#  et D: les données, cela propose D: ; sur un portable, C:.
# ─────────────────────────────────────────────────────────────

param([string]$Dossier)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$adresseDuCode = 'https://github.com/harkett/a-school.git'
$nomDuDossier  = 'A-SCHOOL'

function Echec($message) {
    Write-Host ""
    Write-Host "  $message" -ForegroundColor Red
    Write-Host ""
    exit 1
}

# Même porte que dans j_arrive.ps1 : ne rend vrai que sur le mot exact.
# Toute autre réponse, l'absence de réponse, ou une question qui ne peut
# même pas être posée valent refus.
function Demander-Remplacement {
    Write-Host ""
    Write-Host "  Tapez le mot  remplacer  puis Entrée pour le supprimer et repartir de zéro," -ForegroundColor Yellow
    Write-Host "  ou appuyez simplement sur Entrée pour ne rien changer." -ForegroundColor Yellow
    Write-Host ""
    $reponse = ''
    try { $reponse = Read-Host "  Votre choix" } catch { $reponse = '' }
    return ("$reponse".Trim().ToLower() -eq 'remplacer')
}

# L'endroit proposé, cherché sur ce poste plutôt que deviné. Si un dossier
# A-SCHOOL existe déjà à la racine d'un disque, c'est celui-là qu'on refait —
# c'est le cas courant. Sinon on propose le disque de Windows, et l'utilisateur
# tape autre chose s'il le veut.
function Endroit-Propose {
    $racines = @(Get-CimInstance Win32_LogicalDisk -Filter 'DriveType = 3' -ErrorAction SilentlyContinue |
                 Where-Object { $_.Size -gt 0 } | Sort-Object DeviceID |
                 ForEach-Object { $_.DeviceID + '\' })
    foreach ($r in $racines) {
        $candidat = Join-Path $r $nomDuDossier
        if (Test-Path $candidat -ErrorAction SilentlyContinue) { return $candidat }
    }
    return (Join-Path ((Get-Item $env:SystemDrive).Root.Name) $nomDuDossier)
}

Write-Host ""
Write-Host "  A-SCHOOL — j'installe" -ForegroundColor Cyan
Write-Host "  ═════════════════════" -ForegroundColor Cyan
Write-Host ""

# ── 1/5  Ce dont on a besoin doit répondre ──────────────────────────────
Write-Host "  1/5  Vérification..." -ForegroundColor Cyan

git --version 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec "Git n'est pas installé sur ce poste, ou il ne répond pas. Installez-le, puis relancez ce script."
}

docker info -f "{{.ServerVersion}}" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec "Docker Desktop n'est pas démarré. Lancez-le, attendez qu'il soit vert, puis relancez ce script."
}
Write-Host "       tout répond." -ForegroundColor Green

# ── 2/5  Où installer ───────────────────────────────────────────────────
if (-not $Dossier) {
    $propose = Endroit-Propose
    Write-Host ""
    Write-Host "  2/5  Où installer A-SCHOOL sur ce poste ?" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "       Appuyez sur Entrée pour :  $propose" -ForegroundColor White
    Write-Host "       ou tapez un autre endroit." -ForegroundColor White
    Write-Host ""
    $saisi = ''
    try { $saisi = Read-Host "  Votre choix" } catch { $saisi = '' }
    $Dossier = "$saisi".Trim().Trim('"')
    if (-not $Dossier) { $Dossier = $propose }
} else {
    Write-Host "  2/5  Endroit demandé : $Dossier" -ForegroundColor Cyan
}

# On refuse la racine d'un disque : l'étape suivante peut supprimer, et
# supprimer un disque entier n'est jamais ce qu'on voulait dire.
try { $Dossier = [System.IO.Path]::GetFullPath($Dossier) } catch {
    Echec "Cet endroit n'est pas compréhensible : $Dossier"
}
$parent = Split-Path -Parent $Dossier
if (-not $parent) {
    Echec "Cet endroit est la racine d'un disque. Indiquez un dossier, par exemple D:\$nomDuDossier"
}
if (-not (Test-Path $parent)) {
    Echec "Cet endroit n'existe pas sur ce poste : $parent"
}
Write-Host "       ce sera : $Dossier" -ForegroundColor Green

# ── 3/5  S'il y a déjà quelque chose là ─────────────────────────────────
Write-Host "  3/5  Préparation de l'endroit..." -ForegroundColor Cyan

if (Test-Path $Dossier) {
    $fichiers = @(Get-ChildItem $Dossier -Recurse -Force -File -ErrorAction SilentlyContinue)
    $octets   = ($fichiers | Measure-Object -Sum Length).Sum
    if ($null -eq $octets) { $octets = 0 }
    Write-Host ""
    Write-Host "  Il y a déjà quelque chose à cet endroit :" -ForegroundColor Yellow
    Write-Host ("      $Dossier  ({0:N0} fichiers, {1:N0} Mo)" -f $fichiers.Count, ($octets / 1MB)) -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Continuer le supprimerait entièrement et définitivement." -ForegroundColor Yellow
    Write-Host "  Votre travail, lui, ne s'y trouve pas : il est gardé ailleurs sur ce poste." -ForegroundColor Yellow

    if (-not (Demander-Remplacement)) {
        Write-Host ""
        Write-Host "  Rien n'a été modifié." -ForegroundColor Green
        Write-Host ""
        exit 0
    }

    Write-Host "       suppression..." -ForegroundColor Cyan
    Remove-Item $Dossier -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path $Dossier) {
        Echec ("Cet endroit n'a pas pu être vidé entièrement : $Dossier`n" +
               "  Fermez ce qui l'utilise (éditeur, explorateur, terminal), puis relancez ce script.")
    }
    Write-Host "       supprimé." -ForegroundColor Green
}

# ── 4/5  Récupérer le code ──────────────────────────────────────────────
Write-Host "  4/5  Récupération du code (quelques minutes)..." -ForegroundColor Cyan

git clone --quiet $adresseDuCode "$Dossier" 2>$null | Out-Null
$jArrive = Join-Path $Dossier 'Scripts\j_arrive.ps1'
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $jArrive)) {
    Echec ("Le code n'a pas pu être récupéré. Vérifiez la connexion internet, puis relancez ce script.`n" +
           "  Rien n'a été laissé à moitié : supprimez $Dossier avant de recommencer.")
}
Write-Host "       code en place." -ForegroundColor Green

# ── 5/5  Les trois éléments apportés à la main ──────────────────────────
Write-Host ""
Write-Host "  5/5  Il manque encore ce que vous apportez de l'autre poste." -ForegroundColor Cyan
Write-Host ""
Write-Host "  Collez maintenant ces trois éléments dans :" -ForegroundColor White
Write-Host "      $Dossier" -ForegroundColor White
Write-Host ""
Write-Host "      Bagage           le dossier" -ForegroundColor White
Write-Host "      REFERENTIELS     le dossier" -ForegroundColor White
Write-Host "      .env             le fichier" -ForegroundColor White
Write-Host ""
try { Read-Host "  Puis appuyez sur Entrée" | Out-Null } catch { }

$manquants = @()
if (-not (Test-Path (Join-Path $Dossier 'Bagage\travail.aschool'))) { $manquants += 'Bagage         (le dossier, avec le travail dedans)' }
if (-not (Test-Path (Join-Path $Dossier 'REFERENTIELS')))           { $manquants += 'REFERENTIELS   (le dossier)' }
if (-not (Test-Path (Join-Path $Dossier '.env')))                   { $manquants += '.env           (le fichier)' }

if ($manquants.Count -gt 0) {
    Write-Host ""
    Write-Host "  Ceci n'a pas été collé :" -ForegroundColor Red
    foreach ($m in $manquants) { Write-Host "      $m" -ForegroundColor Red }
    Write-Host ""
    Write-Host "  Le dossier est en place, il ne manque que cela." -ForegroundColor Red
    Echec "Collez-les, puis lancez :  $jArrive"
}
Write-Host "       tout est là." -ForegroundColor Green

# ── La main passe à j_arrive, qui sait faire le reste ───────────────────
Write-Host ""
Write-Host "  L'installation continue toute seule." -ForegroundColor Green
& $jArrive
exit $LASTEXITCODE
