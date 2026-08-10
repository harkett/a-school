# =============================================================================
# aSchool — MIGRER LA BASE, AVEC SON POINT DE RETOUR
#
# CE QU'IL FAIT, DANS CET ORDRE :
#   1. une sauvegarde complete (Scripts\sauvegarde.ps1) ;
#   2. alembic upgrade head, dans le conteneur backend ;
#   3. la version atteinte, affichee.
# Si la sauvegarde echoue, la migration N'A PAS LIEU.
#
# POURQUOI. Un downgrade() n'est verifie que le jour ou on s'en sert, et c'est
# toujours le mauvais jour. Le seul retour arriere sur lequel on peut compter
# est un dump pris juste avant. Regle posee le 10/08/2026 : aucune migration
# qui touche aux donnees sans sauvegarde immediatement anterieure.
#
# USAGE :  .\Scripts\migrer.ps1              (jusqu'a la derniere revision)
#          .\Scripts\migrer.ps1 -Cible abc123   (jusqu'a une revision precise)
#          .\Scripts\migrer.ps1 -SansSauvegarde (uniquement si un dump vient
#                                                d'etre pris a la main)
# =============================================================================

param(
    [string] $Cible = 'head',
    [switch] $SansSauvegarde
)

# 'Continue' et non 'Stop' : en PowerShell 5.1, la moindre ligne de stderr d'un
# executable natif devient une erreur terminante. Chaque appel est juge sur son
# code de sortie.
$ErrorActionPreference = 'Continue'

$projet = Split-Path -Parent $PSScriptRoot
Set-Location $projet

if (-not $SansSauvegarde) {
    Write-Host '1/3  Sauvegarde avant migration...' -ForegroundColor Cyan
    & (Join-Path $PSScriptRoot 'sauvegarde.ps1')
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'ARRET : la sauvegarde a echoue, la migration n a PAS ete lancee.' -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host '1/3  Sauvegarde SAUTEE (-SansSauvegarde).' -ForegroundColor Yellow
}

Write-Host "2/3  alembic upgrade $Cible ..." -ForegroundColor Cyan
docker compose exec -T backend alembic upgrade $Cible
if ($LASTEXITCODE -ne 0) {
    Write-Host 'La migration a echoue. Le dump de db_backup\ est le point de retour.' -ForegroundColor Red
    exit 1
}

Write-Host '3/3  Version en base :' -ForegroundColor Cyan
docker compose exec -T backend alembic current
