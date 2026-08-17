# ==============================================================================
# recette.ps1 — Joue l'application dans un vrai navigateur et dit ce qui est casse.
# Aucun appel a une IA depuis le script : 0 EUR (la generation testee, elle, passe
# par le fournisseur configure, comme un usage normal).
#
# C'EST UNE BARRIERE, PAS UN RAPPORT. Une fonctionnalite ne se livre pas tant que sa
# recette n'est pas verte : rouge, la migration de livraison ne part pas, donc rien
# n'arrive dans l'encart de l'administration et rien n'est annonce aux professeurs.
# Le rouge ne concerne que le developpement, qui corrige.
#
# Ce que fait le script, dans l'ordre :
#   1. verifie que Playwright est installe (l'installe au premier lancement) ;
#   2. verifie que l'application repond ; si non, la demarre et l'arrete en partant ;
#   3. joue les scenarios demandes ;
#   4. affiche une ligne par etape : OK, ou l'etape fautive avec sa capture d'ecran.
#
# --- USAGE ------------------------------------------------------------------
#   .\Scripts\recette.ps1                    # tous les scenarios
#   .\Scripts\recette.ps1 -Module admin      # le parcours de l'administration
#   .\Scripts\recette.ps1 -Module grilles    # la recette d'une fonctionnalite
#   .\Scripts\recette.ps1 -Voir              # navigateur visible
#   .\Scripts\recette.ps1 -Rapport           # ouvre le rapport HTML a la fin
#
# Identifiants : demandes au premier lancement et gardes dans Scripts\.recette.env
# (ignore par git). -Identifiants les redemande. Le compte professeur doit avoir un
# niveau — sans referentiel, aucune generation n'est possible.
# ==============================================================================

param(
  [string] $Module,
  [switch] $Voir,
  [switch] $Rapport,
  [switch] $Identifiants
)

$ErrorActionPreference = 'Stop'
$racine   = Split-Path -Parent $PSScriptRoot
$frontend = Join-Path $racine 'frontend'
$envFile  = Join-Path $PSScriptRoot '.recette.env'
$adresse  = 'http://localhost:5173'

function Titre($t) { Write-Host "`n=== $t ===" -ForegroundColor Cyan }
function Bien($t)  { Write-Host "  $t" -ForegroundColor Green }
function Mal($t)   { Write-Host "  $t" -ForegroundColor Red }

function Demander($libelle) {
  $s = Read-Host "  $libelle"
  return $s
}

function DemanderSecret($libelle) {
  $s = Read-Host "  $libelle" -AsSecureString
  return [Runtime.InteropServices.Marshal]::PtrToStringAuto(
           [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
}

# --- 1. Les identifiants ------------------------------------------------------
if ($Identifiants -and (Test-Path $envFile)) { Remove-Item $envFile }

if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') { Set-Item -Path "env:$($Matches[1].Trim())" -Value $Matches[2].Trim() }
  }
} else {
  Titre 'Identifiants'
  Write-Host '  Gardes dans Scripts\.recette.env, jamais commites.' -ForegroundColor DarkGray
  Write-Host '  Administration :' -ForegroundColor DarkGray
  $au = Demander 'Identifiant admin'
  $ap = DemanderSecret 'Mot de passe admin'
  Write-Host '  Professeur (compte reel, avec un niveau) :' -ForegroundColor DarkGray
  $pu = Demander 'Adresse e-mail du prof'
  $pp = DemanderSecret 'Mot de passe du prof'
  "ADMIN_USER=$au`nADMIN_PASS=$ap`nPROF_USER=$pu`nPROF_PASS=$pp" | Out-File $envFile -Encoding utf8
  $env:ADMIN_USER = $au; $env:ADMIN_PASS = $ap
  $env:PROF_USER  = $pu; $env:PROF_PASS  = $pp
}

Push-Location $frontend
try {
  # --- 2. Playwright ---------------------------------------------------------
  if (-not (Test-Path (Join-Path $frontend 'node_modules\@playwright\test'))) {
    Titre 'Installation de Playwright (une seule fois)'
    npm install -D '@playwright/test'
    npx playwright install chromium
  }

  # --- 3. L'application ------------------------------------------------------
  $lancee = $false
  try {
    Invoke-WebRequest -Uri $adresse -TimeoutSec 3 -UseBasicParsing | Out-Null
    Bien 'Application deja en ligne.'
  } catch {
    Titre 'Demarrage de l application'
    $serveur = Start-Process npm -ArgumentList 'run','dev' -PassThru -WindowStyle Hidden
    $lancee = $true
    $pret = $false
    foreach ($essai in 1..30) {
      Start-Sleep -Seconds 1
      try { Invoke-WebRequest -Uri $adresse -TimeoutSec 2 -UseBasicParsing | Out-Null; $pret = $true; break } catch { }
    }
    if (-not $pret) { Mal 'L application n a pas repondu en 30 secondes.'; exit 1 }
    Bien 'Application en ligne.'
  }

  # --- 4. Les scenarios ------------------------------------------------------
  Titre $(if ($Module) { "Recette : $Module" } else { 'Recette complete' })
  $arguments = @('playwright','test')
  if ($Module)  { $arguments += $Module }
  if ($Voir)    { $arguments += '--headed' }
  if ($Rapport) { $arguments += '--reporter=list,html' }

  npx @arguments
  $code = $LASTEXITCODE

  if ($code -eq 0) {
    Bien 'Recette verte — la livraison peut partir.'
  } else {
    Mal 'RECETTE ROUGE — NE PAS LIVRER.'
    Mal 'Capture, video et trace de l etape fautive : frontend\test-results.'
    if ($Rapport) { npx playwright show-report }
  }

  if ($lancee) { Stop-Process -Id $serveur.Id -Force -ErrorAction SilentlyContinue }
  exit $code
}
finally { Pop-Location }
