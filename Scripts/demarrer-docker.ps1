# ─────────────────────────────────────────────────────
# aSchool — démarrage automatique de la pile à l'ouverture du projet.
# Appelé par .vscode/tasks.json (runOn: folderOpen). Peut aussi se lancer à la main :
#   .\Scripts\demarrer-docker.ps1
#
# POURQUOI UNE ATTENTE ET PAS UN SIMPLE « docker compose up ». Docker Desktop met dix à
# quarante secondes entre le moment où son processus apparaît et celui où son moteur accepte
# une commande. Un « compose up » lancé dans cet intervalle échoue sur « cannot connect to the
# Docker daemon » — l'erreur qu'on croit être une panne alors que c'est juste trop tôt.
#
# CE SCRIPT NE CONSTRUIT PAS LES IMAGES (pas de --build) : au démarrage quotidien elles existent
# déjà, et une reconstruction ferait attendre plusieurs minutes pour rien. Pour reconstruire
# après un changement de dépendances, c'est .\Scripts\systeme.ps1 qui reste la commande.
# ─────────────────────────────────────────────────────
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
$attenteMax = 180        # secondes — au-delà, on renonce en le disant

function Moteur-Repond {
    docker info 2>$null | Out-Null
    return $?
}

if (Moteur-Repond) {
    Write-Host "Docker repond deja."
} else {
    $exe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $exe) {
        Write-Host "Demarrage de Docker Desktop..."
        Start-Process $exe
    } else {
        Write-Host "Docker Desktop introuvable a l'emplacement attendu : $exe"
        Write-Host "Lancez-le a la main, la pile montera au prochain demarrage."
        exit 1
    }

    $debut = Get-Date
    while (-not (Moteur-Repond)) {
        if (((Get-Date) - $debut).TotalSeconds -gt $attenteMax) {
            Write-Host "Docker n'a pas repondu en $attenteMax secondes. Rien n'a ete lance."
            exit 1
        }
        Start-Sleep -Seconds 3
    }
    Write-Host "Docker repond."
}

Write-Host "Montage de la pile aSchool..."
docker compose -f "$root\docker-compose.yml" up -d
if ($?) {
    Write-Host ""
    Write-Host "  Prof         : http://localhost:5173"
    # UNE PORTE LOCALE PAR DEMONSTRATION (deploy/nginx-demos-local.conf) : nginx y ecrit
    # lui-meme le nom d'hote, c'est lui qui designe le schema servi.
    Write-Host "  Demos        : CIEL A 8091 · CIEL B 8092 · Creche 8093 · CRSA 8094 · Ergo 8095 · College 4e 8096"
    Write-Host "  Adminer      : http://localhost:8082"
}
