# ─────────────────────────────────────────────────────────────
# deployer-donnees.ps1 — envoie la base reelle du poste vers le VPS et l'y remplace.
#
# CE QUE deploy.ps1 NE FAIT PAS, et pourquoi ce script existe. `deploy.ps1` pousse le CODE :
# git pull, dépendances, `alembic upgrade head`, build. Alembic crée des tables VIDES. Le
# contenu — les référentiels découpés, leurs unités vectorisées, les types, les précisions —
# n'existe que sur ce poste. Sans ce script-ci, le serveur reçoit une application parfaite
# et vide.
#
# CE QU'IL FAIT :
#   1. dumpe la base reelle depuis le conteneur PostgreSQL local ;
#   2. l'envoie par SCP dans deploy/dumps/ sur le VPS ;
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
$dossierDumps = Join-Path $racine "deploy\dumps"

# La base réelle se lit dans le .env — jamais recopiée ici, sinon elle divergera un jour.
$envLocal = Join-Path $racine ".env"
$ligneDb = (Get-Content $envLocal | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1)
if (-not $ligneDb) {
    Write-Host "ERREUR : DATABASE_URL absente du .env local." -ForegroundColor Red
    exit 1
}
$baseReelle = ($ligneDb -split '/')[-1] -replace '\?.*$', ''

$bases = @($baseReelle)

# LE NOM DU DUMP N'EST PAS LE NOM DE LA BASE. Elle s'appelle `aschool_dev` sur le poste et
# `aschool` sur le serveur : un dump nomme d'apres la base locale serait cherche en vain
# la-bas. Il voyage donc sous `_reelle.dump`, et c'est le serveur qui lit SON propre .env pour
# savoir dans quelle base le verser.
function NomDump([string]$base) {
    return "_reelle"
}

Write-Host ""
Write-Host "Base reelle locale : $baseReelle  (envoyee sous _reelle.dump)" -ForegroundColor DarkGray

# ── 1. Dumps ─────────────────────────────────────────────────
Write-Host ""
Write-Host "1/2  Dump de la base locale..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $dossierDumps | Out-Null

foreach ($b in $bases) {
    $cible = Join-Path $dossierDumps "$(NomDump $b).dump"

    # LE DUMP S'ÉCRIT DANS LE CONTENEUR, PUIS SE RECOPIE. Ne JAMAIS rediriger `docker exec`
    # vers un fichier avec `>` : PowerShell 5.1 — la seule version installée sur ce poste —
    # prend la sortie d'un programme pour du TEXTE. Il la décode, la réencode en UTF-8 et lui
    # colle un BOM en tête. Sur un dump binaire, le fichier GROSSIT au lieu d'être invalide de
    # façon visible : en-tête `EF BB BF` au lieu de `PGDMP`. `pg_restore` répond alors « input
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
    # un fichier GROS et illisible que produisait la redirection ci-dessus, et les dumps
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

if ($Simulation) {
    Write-Host ""
    Write-Host "Simulation : le dump est dans deploy\dumps\, rien n'a ete envoye." -ForegroundColor Yellow
    exit 0
}

# ── 2. Envoi et remplacement ────────────────────────────────
Write-Host ""
Write-Host "2/2  Envoi vers $VPS_HOST et remplacement..." -ForegroundColor Cyan
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
Write-Host "  Donnees deployees. La base reelle du VPS est celle du poste." -ForegroundColor Green
