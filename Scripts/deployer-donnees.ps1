# ─────────────────────────────────────────────────────────────
# deployer-donnees.ps1 — envoie les SIX bases du poste vers le VPS et les y remplace.
#
# CE QUE deploy.ps1 NE FAIT PAS, et pourquoi ce script existe. `deploy.ps1` pousse le CODE :
# git pull, dépendances, `alembic upgrade head`, build. Alembic crée des tables VIDES. Le
# contenu — cinq référentiels découpés, 384 unités vectorisées, les types, les précisions, et
# le contenu pédagogique des cinq démonstrations écrit à la main — n'existe que sur ce poste.
# Sans ce script-ci, le serveur reçoit une application parfaite et vide.
#
# CE QU'IL FAIT :
#   1. dumpe les six bases depuis le conteneur PostgreSQL local ;
#   2. les envoie par SCP dans deploy/dumps/ sur le VPS ;
#   3. y lance `deploy/restaurer-bases.sh`, qui sauvegarde puis REMPLACE.
#
# IL NE DÉPLOIE PAS LE CODE. Les deux sont séparés à dessein : on repousse du code dix fois par
# jour, on n'écrase les données du serveur que sciemment. L'ordre du jour J est : `deploy.ps1`
# d'abord (le code et le schéma), celui-ci ensuite (le contenu).
#
# Usage : .\Scripts\deployer-donnees.ps1
#         .\Scripts\deployer-donnees.ps1 -Simulation    (dumpe et vérifie, n'envoie rien)
# ─────────────────────────────────────────────────────────────

param(
    [switch]$Simulation
)

$ErrorActionPreference = 'Stop'

$VPS_USER = "ubuntu"
$VPS_HOST = "83.228.245.163"
$VPS_PATH = "/var/www/a-school"
$CONTENEUR_DB = "a-school-db-1"

$racine = Split-Path -Parent $PSScriptRoot
$listeDemos = Join-Path $racine "deploy\demos.conf"
$dossierDumps = Join-Path $racine "deploy\dumps"

if (-not (Test-Path $listeDemos)) {
    Write-Host "ERREUR : deploy\demos.conf introuvable." -ForegroundColor Red
    exit 1
}

# La base réelle se lit dans le .env — jamais recopiée ici, sinon elle divergera un jour.
$envLocal = Join-Path $racine ".env"
$ligneDb = (Get-Content $envLocal | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1)
if (-not $ligneDb) {
    Write-Host "ERREUR : DATABASE_URL absente du .env local." -ForegroundColor Red
    exit 1
}
$baseReelle = ($ligneDb -split '/')[-1] -replace '\?.*$', ''

# Les démonstrations viennent de la liste unique.
$basesDemo = Get-Content $listeDemos |
    Where-Object { $_ -notmatch '^\s*#' -and $_.Trim() -ne '' } |
    ForEach-Object { ($_ -split ':')[0] }

$bases = @($baseReelle) + $basesDemo

# LE NOM DU DUMP N'EST PAS LE NOM DE LA BASE, pour la base reelle seulement. Elle s'appelle
# `aschool_dev` sur le poste et `aschool` sur le serveur : un dump nomme d'apres la base locale
# serait cherche en vain la-bas. Il voyage donc sous `_reelle.dump`, et c'est le serveur qui
# lit SON propre .env pour savoir dans quelle base le verser. Les demonstrations, elles,
# portent le meme nom des deux cotes : leur nom EST leur identite.
function NomDump([string]$base) {
    if ($base -eq $baseReelle) { return "_reelle" } else { return $base }
}

Write-Host ""
Write-Host "Bases a envoyer : $($bases -join ', ')" -ForegroundColor Cyan
Write-Host "Base reelle locale : $baseReelle  (envoyee sous _reelle.dump)" -ForegroundColor DarkGray

# ── 1. Dumps ─────────────────────────────────────────────────
Write-Host ""
Write-Host "1/3  Dump des bases locales..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $dossierDumps | Out-Null

foreach ($b in $bases) {
    $cible = Join-Path $dossierDumps "$(NomDump $b).dump"

    # LE DUMP S'ÉCRIT DANS LE CONTENEUR, PUIS SE RECOPIE. Ne JAMAIS rediriger `docker exec`
    # vers un fichier avec `>` : PowerShell 5.1 — la seule version installée sur ce poste —
    # prend la sortie d'un programme pour du TEXTE. Il la décode, la réencode en UTF-8 et lui
    # colle un BOM en tête. Sur un dump binaire, le fichier GROSSIT au lieu d'être invalide de
    # façon visible : 935 921 octets au lieu de 570 931 pour `ciela_demo` (mesuré le
    # 10/08/2026), en-tête `EF BB BF` au lieu de `PGDMP`. `pg_restore` répond alors « input
    # file does not appear to be a valid archive » — mais côté serveur seulement, une fois les
    # dumps envoyés. `-f` fait écrire pg_dump lui-même, `docker cp` transporte les octets tels
    # quels : aucun décodage nulle part.
    $tampon = "/tmp/aschool-dump.tmp"
    docker exec $CONTENEUR_DB pg_dump -U aschool -Fc -d $b -f $tampon
    if ($LASTEXITCODE -ne 0) {
        Write-Host "     ERREUR : le dump de $b a echoue." -ForegroundColor Red
        exit 1
    }
    docker cp "${CONTENEUR_DB}:$tampon" $cible | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "     ERREUR : la recopie du dump de $b a echoue." -ForegroundColor Red
        exit 1
    }
    docker exec $CONTENEUR_DB rm -f $tampon | Out-Null

    $taille = [math]::Round((Get-Item $cible).Length / 1MB, 1)
    if ($taille -eq 0) {
        Write-Host "     ERREUR : le dump de $b est vide." -ForegroundColor Red
        exit 1
    }

    # ON RELIT CE QU'ON VIENT D'ÉCRIRE. Le contrôle de taille ne prouve rien : c'est justement
    # un fichier GROS et illisible que produisait la redirection ci-dessus, et les six dumps
    # sont passés au vert pendant une journée d'essais sans que personne ne les ouvre. On fait
    # donc ici, sur le poste, EXACTEMENT le test que `deploy/restaurer-bases.sh` fera sur le
    # serveur avant de détruire quoi que ce soit — la seule différence étant qu'ici, le rattraper
    # ne coûte rien. Le fichier repart dans le conteneur : c'est le fichier PARTANT qu'on teste,
    # pas le tampon d'origine.
    docker cp $cible "${CONTENEUR_DB}:/tmp/aschool-verif.tmp" | Out-Null
    docker exec $CONTENEUR_DB pg_restore --list /tmp/aschool-verif.tmp | Out-Null
    $lisible = ($LASTEXITCODE -eq 0)
    docker exec $CONTENEUR_DB rm -f /tmp/aschool-verif.tmp | Out-Null
    if (-not $lisible) {
        Write-Host "     ERREUR : le dump de $b n'est pas une archive PostgreSQL lisible." -ForegroundColor Red
        Write-Host "     Le serveur le refuserait. Rien n'a ete envoye." -ForegroundColor Red
        exit 1
    }

    Write-Host "     $b  ->  $taille Mo  (relu : archive valide)" -ForegroundColor Green
}

# ── 2. Controle de coherence AVANT d'envoyer ────────────────
# On vérifie ici ce que le serveur ne pourra plus vérifier une fois les bases détruites : que
# chaque démonstration porte bien un référentiel, et que son niveau concorde avec la base
# réelle. C'est le défaut du 10/08/2026 (CRSA à 101 côté démo contre 89 côté réel) — il ne
# doit pas partir en production.
Write-Host ""
Write-Host "2/3  Controle de coherence des demos..." -ForegroundColor Cyan
$sqlReel = "SELECT r.nom_fixe || '=' || r.niveau_id FROM referentiels r ORDER BY r.nom_fixe;"
$reel = @{}
(docker exec $CONTENEUR_DB psql -U aschool -d $baseReelle -tAc $sqlReel) |
    Where-Object { $_.Trim() -ne '' } |
    ForEach-Object { $p = $_ -split '='; $reel[$p[0]] = $p[1] }

$ecarts = @()
foreach ($b in $basesDemo) {
    $ligne = (docker exec $CONTENEUR_DB psql -U aschool -d $b -tAc $sqlReel | Where-Object { $_.Trim() -ne '' } | Select-Object -First 1)
    if (-not $ligne) { $ecarts += "$b : aucun referentiel"; continue }
    $p = $ligne -split '='
    if ($reel[$p[0]] -ne $p[1]) {
        $ecarts += "$b : $($p[0]) porte niveau_id=$($p[1]) alors que la base reelle dit $($reel[$p[0]])"
    }
}
if ($ecarts.Count -gt 0) {
    Write-Host "     ECART(S) DETECTE(S) — rien n'a ete envoye :" -ForegroundColor Red
    $ecarts | ForEach-Object { Write-Host "       $_" -ForegroundColor Red }
    exit 1
}
Write-Host "     Les $($basesDemo.Count) demos concordent avec la base reelle." -ForegroundColor Green

if ($Simulation) {
    Write-Host ""
    Write-Host "Simulation : les dumps sont dans deploy\dumps\, rien n'a ete envoye." -ForegroundColor Yellow
    exit 0
}

# ── 3. Envoi et remplacement ────────────────────────────────
Write-Host ""
Write-Host "3/3  Envoi vers $VPS_HOST et remplacement..." -ForegroundColor Cyan
ssh "$VPS_USER@$VPS_HOST" "mkdir -p $VPS_PATH/deploy/dumps"
if ($LASTEXITCODE -ne 0) { Write-Host "     ERREUR : connexion SSH impossible." -ForegroundColor Red; exit 1 }

foreach ($b in $bases) {
    $nom = NomDump $b
    scp (Join-Path $dossierDumps "$nom.dump") "${VPS_USER}@${VPS_HOST}:$VPS_PATH/deploy/dumps/$nom.dump"
    if ($LASTEXITCODE -ne 0) { Write-Host "     ERREUR : envoi de $b echoue." -ForegroundColor Red; exit 1 }
    Write-Host "     $b envoye" -ForegroundColor Green
}

ssh "$VPS_USER@$VPS_HOST" "cd $VPS_PATH && JE_VEUX_ECRASER=oui bash deploy/restaurer-bases.sh"
if ($LASTEXITCODE -ne 0) {
    Write-Host "     ERREUR lors du remplacement. L'etat precedent est sauvegarde sur le VPS." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "  Donnees deployees. Les six bases du VPS sont celles du poste." -ForegroundColor Green
