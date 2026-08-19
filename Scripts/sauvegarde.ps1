# =============================================================================
# aSchool — SAUVEGARDE QUOTIDIENNE DES BASES
#
# CE QU'IL FAIT. Un pg_dump de aschool_dev et de aschool_demos,
# vers db_backup\, un fichier horodaté par base, puis efface ce qui a plus de
# 14 jours. Rien d'autre : il ne restaure pas, il ne touche à aucune base.
#
# POURQUOI IL EXISTE. Les deux pg_dump du projet (je_pars.ps1, j_arrive.ps1)
# servent la BASCULE entre postes : ils ne partent que si on lance le script à
# la main. Constaté le 10/08/2026 : la derniere copie d'aschool_dev datait du
# 2 aout, et tout le travail depuis — BTS CRSA, Licence Ergotherapie, 75 types
# d'activite et leurs 134 precisions — n'existait qu'a un seul endroit, le
# volume Docker. Une sauvegarde qui depend d'un geste humain n'est pas une
# sauvegarde.
#
# QUAND IL TOURNE. Chaque jour, par la tache planifiee « aSchool-Sauvegarde »
# (posee par installer-sauvegarde.ps1). Et a la main, avant une migration qui
# touche aux donnees : c'est le point de retour si le downgrade se revele
# menteur.
#
# CE QU'IL FAIT SI DOCKER DORT. Il demarre le seul conteneur db, prend ses
# dumps, et le laisse tourner : arreter une pile qu'on n'a pas demarree est le
# genre d'initiative qui casse une session de travail en cours.
#
# CE QU'IL NE FAIT JAMAIS. Ecraser un fichier existant (chaque nom porte
# l'horodatage a la minute), ni supprimer un dump du jour meme, ni s'arreter
# sur la premiere base en echec : les autres doivent partir quand meme.
# =============================================================================

# 'Continue' et non 'Stop' : en PowerShell 5.1, la moindre ligne de stderr d'un
# executable natif (docker) devient une erreur terminante et interrompt tout le
# script, meme quand la commande a reussi. Ici, chaque appel est juge sur son
# code de sortie ($LASTEXITCODE), jamais sur son bavardage.
$ErrorActionPreference = 'Continue'

$projet   = Split-Path -Parent $PSScriptRoot
$dossier  = Join-Path $projet 'db_backup'
$journal  = Join-Path $dossier 'sauvegarde.log'
$jours    = 14
$bases    = @('aschool_dev', 'aschool_demos')

New-Item -ItemType Directory -Force -Path $dossier | Out-Null
Set-Location $projet

function Dire($texte, $couleur = 'Gray') {
    $ligne = "{0}  {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $texte
    Write-Host $ligne -ForegroundColor $couleur
    Add-Content -Path $journal -Value $ligne -Encoding utf8
}

# --- Le conteneur db doit repondre -------------------------------------------
$etat = (docker compose ps --status running --services)
if ($etat -notcontains 'db') {
    Dire 'Le conteneur db ne tourne pas : demarrage.' 'Yellow'
    docker compose up -d db | Out-Null
    # pg_isready plutot qu'une attente en aveugle : Postgres accepte les
    # connexions plusieurs secondes apres que le conteneur est « up ».
    $pret = $false
    foreach ($i in 1..30) {
        docker compose exec -T db pg_isready -U aschool | Out-Null
        if ($LASTEXITCODE -eq 0) { $pret = $true; break }
        Start-Sleep -Seconds 2
    }
    if (-not $pret) {
        Dire 'ECHEC : la base ne repond pas apres 60 s. Aucune sauvegarde prise.' 'Red'
        exit 1
    }
}

# --- Un dump par base ---------------------------------------------------------
$horodatage = Get-Date -Format 'yyyyMMdd-HHmm'
$pris = 0
$rates = @()

foreach ($base in $bases) {
    # La base peut avoir disparu (une demo retiree) : on ne rate pas la
    # sauvegarde des autres pour autant.
    $existe = docker compose exec -T db psql -U aschool -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$base'"
    if (-not ("$existe".Trim() -eq '1')) {
        Dire "$base : absente du serveur, ignoree." 'DarkGray'
        continue
    }

    $nom = "{0}_{1}.dump" -f $base, $horodatage
    $cible = Join-Path $dossier $nom

    docker compose exec -T db pg_dump -U aschool -d $base -Fc -f "/tmp/$nom" | Out-Null
    if ($LASTEXITCODE -ne 0) { $rates += $base; Dire "$base : pg_dump en echec." 'Red'; continue }

    docker compose cp "db:/tmp/$nom" "$cible" | Out-Null
    docker compose exec -T db rm -f "/tmp/$nom" | Out-Null

    # Un fichier minuscule n'est pas un dump : le dire plutot que de le compter.
    if (-not (Test-Path $cible) -or (Get-Item $cible).Length -lt 1024) {
        $rates += $base
        Dire "$base : le fichier obtenu est vide ou absent." 'Red'
        Remove-Item $cible -Force -ErrorAction SilentlyContinue
        continue
    }

    $pris++
    Dire ("{0} : {1:N0} Ko" -f $base, ((Get-Item $cible).Length / 1KB)) 'Green'
}

# --- Rotation : au-dela de 14 jours, on efface --------------------------------
# Jamais un fichier du jour, et jamais les deux archives d'avant la bascule
# Docker (aschool.dump, aschool_dev_avant-volume) : elles ne portent pas
# d'horodatage au format de ce script et sont la seule trace de l'ancienne base.
$limite = (Get-Date).AddDays(-$jours)
$vieux = Get-ChildItem $dossier -Filter '*_[0-9]*.dump' -File |
         Where-Object { $_.LastWriteTime -lt $limite }
foreach ($f in $vieux) {
    Remove-Item $f.FullName -Force
    Dire ("rotation : {0} efface (plus de {1} jours)" -f $f.Name, $jours) 'DarkGray'
}

if ($rates.Count -gt 0) {
    Dire ("TERMINE AVEC DES ECHECS — prises : {0}, ratees : {1}" -f $pris, ($rates -join ', ')) 'Red'
    exit 1
}
Dire ("Termine — {0} base(s) sauvegardee(s) dans db_backup\." -f $pris) 'Cyan'
