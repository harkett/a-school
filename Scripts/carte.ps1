# Carte visuelle de la base aSchool - lanceur.
# Usage habituel :  .\Scripts\carte.ps1
# Regenere la carte depuis la base REELLE et l'ouvre dans Edge.
# Ne deploie rien, ne touche pas la PROD.
# $args transmis a carte.py (ex. .\Scripts\carte.ps1 --no-open = regenere sans ouvrir Edge)
#
# Le Python du projet est celui de l'application, et lui seul. Ce script appelait
# .venv\Scripts\python.exe : cet environnement a ete abandonne le 02/08/2026 parce qu'il ne
# survivait pas a un changement de machine et exigeait internet pour renaitre. Depuis, la
# ligne appelait un fichier absent — le lanceur etait mort sans que rien ne le dise.
#
# La carte s'ecrit dans le dossier du projet (il est partage avec l'application), donc le
# fichier apparait bien ici. L'ouverture d'Edge, en revanche, reste dehors : l'application
# tourne dans un Linux sans navigateur.
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$carte = Join-Path $root 'outils_bdd\carte_base\carte_base.html'
$avant = if (Test-Path $carte) { (Get-Item $carte).LastWriteTimeUtc } else { $null }

docker compose exec -T backend python outils_bdd/carte_base/carte.py --no-open @args
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  La carte n'a pas pu etre regeneree." -ForegroundColor Red
    Write-Host "  Verifiez que l'application est demarree, puis relancez." -ForegroundColor Red
    Write-Host ""
    exit 1
}

# On n'ouvre que ce qui vient d'etre ecrit. Ouvrir une carte de la semaine derniere parce que
# l'ecriture a echoue en silence, c'est afficher une base qui n'existe plus en croyant la lire.
$apres = if (Test-Path $carte) { (Get-Item $carte).LastWriteTimeUtc } else { $null }
if ($null -eq $apres -or $apres -eq $avant) {
    Write-Host "  La carte n'a pas ete reecrite — rien a ouvrir." -ForegroundColor Yellow
    exit 1
}

if ($args -notcontains '--no-open') {
    Start-Process msedge $carte
}
