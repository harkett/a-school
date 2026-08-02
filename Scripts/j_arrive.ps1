# ═════════════════════════════════════════════════════════════
#  A-SCHOOL — LA BASCULE D'UNE MACHINE À L'AUTRE, EN ENTIER
#  (ce cadre est identique dans les deux scripts : je_pars et j_arrive.
#   Vous ouvrez l'un ou l'autre, vous avez tout.)
#
#  DEUX SCRIPTS, et un seul est à lancer à la fois.
#
#    je_pars.ps1     sur la machine que vous QUITTEZ.
#                    Enregistre et envoie votre code, sort la base dans
#                    Bagage\, ferme l'application, copie le dossier vers
#                    l'endroit que vous indiquez, et relit chaque fichier
#                    des deux côtés pour vérifier.
#
#    j_arrive.ps1    sur la machine où vous ARRIVEZ.
#                    Récupère le code, refuse d'écraser quelque chose de
#                    plus récent, installe votre travail, redémarre.
#
#  LE RITUEL, identique dans les deux sens :
#
#    1. sur la machine que vous quittez :   .\Scripts\je_pars.ps1
#       puis indiquez où copier quand il le demande.
#
#    2. sur l'autre machine :               .\Scripts\j_arrive.ps1
#
#    Plus aucun glisser-déposer : les deux bouts copient et vérifient.
#
#  CE QUI VOYAGE : le dossier ENTIER, moins ce qui se refabrique.
#    Bagage\        la base de données (pg_dump) + la date du départ
#    REFERENTIELS\  les PDF déposés — hors dépôt, irremplaçables
#    .env           hors dépôt, identique sur les deux machines
#    .git           l'historique. Sans lui, plus de dépôt là-bas.
#    le code        et tout le reste du dossier
#
#  CE QUI NE VOYAGE PAS, parce que ça se refabrique sur place — et c'est
#  ça, tout le volume. Six dossiers, 73 100 fichiers, 6,2 Go :
#    .venv, node_modules          réinstallés par pip et npm
#    docker\hf-cache              le modèle, 4,3 Go, retéléchargé seul
#    docker\pgdata                un reste : la base vit dans le volume
#                                 nommé pgdata_dev, pas dans le dossier
#    __pycache__, .pytest_cache   caches de Python
#
#    Le dossier fait 79 500 fichiers et 6,5 Go ; il en part 6 342 et
#    277 Mo. C'est pourquoi la copie ne se fait PAS dans l'explorateur
#    Windows : il emporte tout, échoue sur les liens du cache du modèle,
#    et saute .git parce qu'il est caché.
#
#  « OÙ COPIER » = n'importe quel endroit atteignable des deux machines :
#    un chemin réseau de l'autre poste (\\FIXE\D$), une clé USB, un
#    disque externe, un dossier synchronisé.
#
#  EN CAS DE DOUTE : ces scripts s'arrêtent plutôt que de deviner, et
#    disent « Rien n'a été modifié » quand c'est le cas. Relancer un
#    script interrompu est toujours sans danger.
# ═════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────
#  j_arrive.ps1 — à lancer sur le poste où vous ARRIVEZ, la clé branchée.
#
#  Il trouve la clé tout seul, y prend les trois éléments et les pose dans
#  le dossier en vérifiant chaque fichier, récupère le code, remet tout en
#  marche, et installe le travail que vous apportez.
#
#  Rien à glisser dans l'explorateur : le départ copiait et vérifiait,
#  l'arrivée fait de même. Un seul geste à chaque bout du voyage.
#
#  Avant d'installer, il pose une question et une seule : la base de ce
#  poste a-t-elle bougé APRÈS la date du travail que vous apportez ?
#  Si oui, il s'arrête sans rien toucher — installer effacerait ce
#  travail-là sans retour possible.
#
#  Ce script ne connaît aucune lettre de lecteur : il se repère depuis
#  son propre emplacement.
#
#  Il suppose que le dossier A-SCHOOL existe déjà sur ce poste.
# ─────────────────────────────────────────────────────────────

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$racine = Split-Path -Parent $PSScriptRoot
Set-Location $racine

$bagage         = Join-Path $racine 'Bagage'
$fichierTravail = Join-Path $bagage 'travail.aschool'
$fichierDate    = Join-Path $bagage 'depart.txt'
$fichierAvant   = Join-Path $bagage 'avant_installation.aschool'
$cacheModele    = Join-Path $racine 'docker\hf-cache\hub'

function Echec($message) {
    Write-Host ""
    Write-Host "  $message" -ForegroundColor Red
    Write-Host ""
    exit 1
}

# La seule porte vers l'installation quand le contrôle n'a pas donné son feu vert.
# Elle ne rend vrai que sur le mot exact ; toute autre réponse, l'absence de
# réponse, ou une question qui ne peut même pas être posée valent refus.
function Demander-Remplacement {
    Write-Host ""
    Write-Host "  Tapez le mot  remplacer  puis Entrée pour l'installer quand même," -ForegroundColor Yellow
    Write-Host "  ou appuyez simplement sur Entrée pour ne rien changer." -ForegroundColor Yellow
    Write-Host ""
    $reponse = ''
    try { $reponse = Read-Host "  Votre choix" } catch { $reponse = '' }
    return ("$reponse".Trim().ToLower() -eq 'remplacer')
}

# ── Ce que vous apportez, pris sur la clé plutôt que glissé à la main ───
# Au départ, je_pars.ps1 copie sur la clé et vérifie chaque fichier. Laisser
# l'arrivée se faire dans l'explorateur remettait au milieu du rituel le seul
# geste manuel qui restait — et c'est celui où l'on se trompe : un REFERENTIELS
# collé à moitié, un .env oublié, et personne ne le dit.
$NOM_VALISE = 'A-SCHOOL-a-emporter'

function Trouver-Valises {
    $trouvees = @()
    $disques = @(Get-CimInstance Win32_LogicalDisk -ErrorAction SilentlyContinue |
                 Where-Object { $_.DriveType -eq 2 -or $_.DriveType -eq 3 } |
                 Sort-Object @{ Expression = { if ($_.DriveType -eq 2) { 0 } else { 1 } } }, DeviceID)
    foreach ($d in $disques) {
        $c = Join-Path ($d.DeviceID + '\') $NOM_VALISE
        if (Test-Path $c -ErrorAction SilentlyContinue) { $trouvees += $c }
    }
    return $trouvees
}

# Chaque fichier est relu des deux côtés et comparé, exactement comme au départ.
# Une copie annoncée sans être vérifiée, c'est ce qui a coûté une journée.
function Poser-Depuis($valise) {
    $copies  = 0
    $ecarts  = @()
    $absents = @()
    foreach ($nom in @('Bagage', 'REFERENTIELS', '.env')) {
        $source = Join-Path $valise $nom
        if (-not (Test-Path $source)) { $absents += $nom; continue }
        $item = Get-Item $source -Force
        Copy-Item -LiteralPath $source -Destination $racine -Recurse:$item.PSIsContainer -Force -ErrorAction SilentlyContinue
        if ($item.PSIsContainer) {
            $base = Split-Path $source -Parent
            foreach ($f in Get-ChildItem -LiteralPath $source -Recurse -Force -File) {
                $relatif = $f.FullName.Substring($base.Length + 1)
                $arrivee = Join-Path $racine $relatif
                $copies++
                if (-not (Test-Path -LiteralPath $arrivee)) { $ecarts += $relatif; continue }
                if ((Get-FileHash -LiteralPath $arrivee).Hash -ne (Get-FileHash -LiteralPath $f.FullName).Hash) { $ecarts += $relatif }
            }
        } else {
            $arrivee = Join-Path $racine $item.Name
            $copies++
            if (-not (Test-Path -LiteralPath $arrivee)) { $ecarts += $item.Name }
            elseif ((Get-FileHash -LiteralPath $arrivee).Hash -ne (Get-FileHash -LiteralPath $item.FullName).Hash) { $ecarts += $item.Name }
        }
    }
    return [pscustomobject]@{ Copies = $copies; Ecarts = $ecarts; Absents = $absents }
}

# Un environnement Python inscrit le chemin qu'il croit occuper. S'il désigne
# un autre endroit que celui où il se trouve, c'est qu'il a été construit
# ailleurs : inutilisable ici, et il se refabrique. S'il désigne CE dossier,
# il a été construit sur ce poste et on n'y touche pas. C'est cette distinction
# qui permet de nettoyer à CHAQUE arrivée sans jamais détruire un environnement
# local qui marche.
function Venv-Etranger($chemin) {
    $marqueur = Join-Path $chemin 'Scripts\activate.bat'
    if (-not (Test-Path $marqueur)) { return $false }   # illisible : dans le doute, on garde
    $ligne = @(Get-Content $marqueur -ErrorAction SilentlyContinue |
               Where-Object { $_ -match 'VIRTUAL_ENV' })[0]
    if (-not $ligne) { return $false }
    $inscrit = (($ligne -replace '.*VIRTUAL_ENV\s*=\s*', '') -replace '"', '').Trim()
    if (-not $inscrit) { return $false }
    return ($inscrit.TrimEnd('\') -ne $chemin.TrimEnd('\'))
}

function Poids-De($chemin) {
    $o = (Get-ChildItem $chemin -Recurse -Force -File -ErrorAction SilentlyContinue |
          Measure-Object -Sum Length).Sum
    if ($null -eq $o) { $o = 0 }
    return $o
}

function Attendre-Base {
    for ($essai = 0; $essai -lt 90; $essai++) {
        docker compose exec -T db pg_isready -U aschool -d aschool_dev 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { return $true }
        Start-Sleep -Seconds 2
    }
    return $false
}

# Date de la dernière trace de travail sur CE poste.
# On ne cite aucune table : on balaie toutes les colonnes horodatées de la
# base, quelles qu'elles soient. Ainsi une table créée demain est vue elle
# aussi. Les dates situées dans le futur sont écartées : une échéance
# (expiration, rappel programmé) n'est pas du travail déjà fait.
function Date-Du-Poste {
    $requete = @'
CREATE TEMP TABLE _dates(t timestamptz); DO $do$ DECLARE r record; BEGIN FOR r IN SELECT c.table_name AS tb, c.column_name AS col FROM information_schema.columns c JOIN pg_tables p ON p.schemaname = c.table_schema AND p.tablename = c.table_name WHERE c.table_schema = 'public' AND c.data_type IN ('timestamp with time zone','timestamp without time zone') LOOP EXECUTE format('INSERT INTO _dates SELECT max(%I)::timestamptz FROM public.%I WHERE %I <= now()', r.col, r.tb, r.col); END LOOP; END $do$; SELECT COALESCE(extract(epoch FROM max(t)),0)::bigint FROM _dates;
'@
    $requete = ($requete -replace "`r`n", " ").Trim()
    $brut = docker compose exec -T db psql -U aschool -d aschool_dev -A -t -c $requete 2>$null
    $ligne = $brut | Where-Object { $_ -match '^\s*\d+\s*$' } | Select-Object -Last 1
    if ($ligne) { return [long]($ligne.Trim()) }
    return $null
}

Write-Host ""
Write-Host "  A-SCHOOL — j'arrive" -ForegroundColor Cyan
Write-Host "  ═══════════════════" -ForegroundColor Cyan
Write-Host ""

# ── 1/6  Vérifications avant de toucher à quoi que ce soit ──────────────
Write-Host "  1/6  Vérification..." -ForegroundColor Cyan

# On demande d'abord si la commande existe, avant de la lancer. Une commande
# absente ne touche pas à $LASTEXITCODE : elle laisse la valeur de la
# précédente. Ici git est appelé après docker : sans ce contrôle, un git
# manquant héritait du 0 de docker et l'étape 2 annonçait « code à jour »
# alors qu'aucune commande n'avait été exécutée.
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Echec "Docker Desktop n'est pas installé sur ce poste. Installez-le, puis relancez ce script."
}
docker info -f "{{.ServerVersion}}" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec "Docker Desktop n'est pas démarré. Lancez-le, attendez qu'il soit vert, puis relancez ce script."
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Echec "Git n'est pas installé sur ce poste. Installez-le, puis relancez ce script."
}
Write-Host "       tout répond." -ForegroundColor Green

# ── 2/6  Ce que vous apportez entre dans le dossier ─────────────────────
Write-Host "  2/6  Ce que vous apportez..." -ForegroundColor Cyan

$valises = @(Trouver-Valises)
$valise  = $null

if ($valises.Count -eq 1) {
    $valise = $valises[0]
}
elseif ($valises.Count -gt 1) {
    Write-Host ""
    Write-Host "  Plusieurs endroits portent un dossier $NOM_VALISE :" -ForegroundColor Yellow
    for ($i = 0; $i -lt $valises.Count; $i++) {
        Write-Host ("      {0}. {1}" -f ($i + 1), $valises[$i]) -ForegroundColor White
    }
    Write-Host ""
    $n = ''
    try { $n = Read-Host "  Lequel (son numéro)" } catch { $n = '' }
    $n = "$n".Trim()
    if ($n -match '^\d+$' -and [int]$n -ge 1 -and [int]$n -le $valises.Count) {
        $valise = $valises[[int]$n - 1]
    } else {
        Echec "Aucun choix compris. Rien n'a été modifié."
    }
}
else {
    # Aucune clé. Si le dossier contient déjà le travail — c'est le cas quand on
    # a copié le dossier entier plutôt que d'utiliser une clé — il n'y a rien à
    # demander : on s'en sert et on avance. Poser une question qui n'a qu'une
    # seule réponse possible, c'est offrir une occasion de se tromper pour rien.
    if (Test-Path $fichierTravail) {
        Write-Host "       déjà dans le dossier, rien à aller chercher." -ForegroundColor Green
    }
    else {
        # Là, en revanche, il n'y a vraiment rien : ni clé, ni travail dans le
        # dossier. La question a un sens, on la pose.
        Write-Host ""
        Write-Host "  Aucune clé branchée ne porte de dossier $NOM_VALISE," -ForegroundColor Yellow
        Write-Host "  et ce dossier ne contient aucun travail à installer." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "     Entrée      branchez la clé maintenant, je regarde à nouveau" -ForegroundColor White
        Write-Host "     un chemin   si votre clé est ailleurs (par exemple  E:\ )" -ForegroundColor White
        Write-Host ""
        $r = ''
        try { $r = Read-Host "  Votre choix" } catch { $r = '' }
        $r = "$r".Trim().Trim('"')

        if (-not $r) {
            $valises = @(Trouver-Valises)
            if ($valises.Count -ge 1) { $valise = $valises[0] }
            else { Echec "Toujours aucune clé trouvée. Rien n'a été modifié." }
        }
        elseif (Test-Path (Join-Path $r $NOM_VALISE)) { $valise = Join-Path $r $NOM_VALISE }
        elseif (Test-Path (Join-Path $r 'Bagage'))    { $valise = $r }
        else {
            Echec "Rien à apporter n'a été trouvé ici : $r"
        }
    }
}

if ($valise) {
    Write-Host "       depuis $valise" -ForegroundColor White
    $bilan = Poser-Depuis $valise

    if ($bilan.Ecarts.Count -gt 0) {
        Write-Host ""
        Write-Host "  Ces fichiers ne sont pas arrivés correctement :" -ForegroundColor Red
        foreach ($e in $bilan.Ecarts | Select-Object -First 10) { Write-Host "      $e" -ForegroundColor Red }
        Echec "La copie n'est pas fiable. Rebranchez la clé, puis relancez ce script."
    }
    if ($bilan.Absents.Count -gt 0) {
        Write-Host ("       (absent de la clé : {0})" -f ($bilan.Absents -join ', ')) -ForegroundColor DarkGray
    }
    Write-Host ("       {0} fichiers posés, tous vérifiés un par un." -f $bilan.Copies) -ForegroundColor Green
}

# ── Ce qu'une copie complète du dossier a ramené pour rien ──────────────
# Copier le dossier entier plutôt que de trier dans l'explorateur est un choix
# légitime : le tri se fait ici, où l'on peut vérifier, et pas à la main où
# l'on se trompe. On ne retire QUE ce dont on est sûr que ça se refabrique.
#
#   .venv          retiré seulement s'il vient d'une autre machine (son
#                  chemin est inscrit dedans). Construit ici → gardé.
#                  Se refabrique : python -m venv .venv puis
#                  pip install -r requirements.txt
#   node_modules   jamais lu par l'application : le conteneur monte le sien
#                  (docker-compose.yml:104). Se refabrique : npm ci
#   docker\hf-cache  JAMAIS retiré. C'est le modèle d'embedding, 2,2 Go.
#                  S'il est arrivé, c'est autant de téléchargement épargné.
$retires = @()
$gardes  = @()

foreach ($nom in @('.venv', 'venv')) {
    $chemin = Join-Path $racine $nom
    if (-not (Test-Path $chemin)) { continue }
    if (Venv-Etranger $chemin) {
        $poids = Poids-De $chemin
        Remove-Item $chemin -Recurse -Force -ErrorAction SilentlyContinue
        if (Test-Path $chemin) {
            Write-Host "       ($nom n'a pas pu être retiré — fermez ce qui l'utilise)" -ForegroundColor Yellow
        } else {
            $retires += ("{0}  ({1:N0} Mo, venu de l'autre machine)" -f $nom, ($poids / 1MB))
        }
    } else {
        $gardes += "$nom (construit sur ce poste)"
    }
}

foreach ($nom in @('frontend\node_modules', 'node_modules')) {
    $chemin = Join-Path $racine $nom
    if (-not (Test-Path $chemin)) { continue }
    $poids = Poids-De $chemin
    Remove-Item $chemin -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path $chemin) {
        Write-Host "       ($nom n'a pas pu être retiré entièrement — sans gravité)" -ForegroundColor Yellow
    } else {
        $retires += ("{0}  ({1:N0} Mo, refait par le conteneur)" -f $nom, ($poids / 1MB))
    }
}

if ($retires.Count -gt 0) {
    Write-Host "       retiré, parce que ça se refabrique tout seul :" -ForegroundColor DarkGray
    foreach ($r in $retires) { Write-Host "          $r" -ForegroundColor DarkGray }
}
foreach ($g in $gardes) { Write-Host "       gardé : $g" -ForegroundColor DarkGray }

# Le modèle n'est jamais retiré, mais on dit s'il est là : c'est la différence
# entre une première lecture instantanée et 2,2 Go à retélécharger.
if (Test-Path $cacheModele) {
    $pm = Poids-De $cacheModele
    if ($pm -gt 100MB) {
        Write-Host ("       gardé : le modèle ({0:N1} Go) — rien à retélécharger." -f ($pm / 1GB)) -ForegroundColor DarkGray
    }
}

if (-not (Test-Path $fichierTravail)) {
    Echec ("Ce dossier ne contient aucun travail à installer.`n" +
           "  Sur le poste de départ, lancez Scripts\je_pars.ps1 : il vous dira quoi copier ici.")
}

# Les deux autres éléments apportés à la main. Leur absence n'empêche pas
# d'installer, mais elle se dit maintenant, pas dans trois jours.
$manquants = @()
if (-not (Test-Path (Join-Path $racine 'REFERENTIELS'))) { $manquants += 'REFERENTIELS  (le dossier)' }
if (-not (Test-Path (Join-Path $racine '.env')))         { $manquants += '.env          (le fichier)' }
if ($manquants.Count -gt 0) {
    Write-Host ""
    Write-Host "  Attention : ces éléments n'ont pas été copiés ici." -ForegroundColor Yellow
    foreach ($m in $manquants) { Write-Host "      $m" -ForegroundColor Yellow }
    Write-Host "  L'application démarrera, mais il leur manquera cela." -ForegroundColor Yellow
    Write-Host ""
}

$dateApportee = $null
if (Test-Path $fichierDate) {
    $lu = (Get-Content $fichierDate -Raw).Trim()
    if ($lu -match '^\d+$') { $dateApportee = [long]$lu }
}
Write-Host "       le travail à installer est bien là." -ForegroundColor Green

# Première fois sur ce poste ? Rien n'y a encore été préparé.
# On l'annonce AVANT la longue attente, pour qu'elle ne soit pas subie.
$dejaLa = docker compose ps -a -q 2>$null
$premiereFois = -not $dejaLa
if ($premiereFois) {
    Write-Host ""
    Write-Host "  Première installation sur ce poste : préparation en cours," -ForegroundColor Yellow
    Write-Host "  quelques minutes, connexion internet nécessaire." -ForegroundColor Yellow
    Write-Host ""
}

# ── 3/6  Le code, qui lui ne voyage pas dans la copie ───────────────────
Write-Host "  3/6  Récupération du code..." -ForegroundColor Cyan

git rev-parse --is-inside-work-tree 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    # Cause quasi certaine quand le dossier vient d'être copié à la main :
    # .git porte l'attribut « caché ». C'est le SEUL élément suivi par git
    # qui soit caché. Entrer dans le dossier et faire Ctrl+A prend donc tout
    # sauf lui. Copier le DOSSIER lui-même, en revanche, l'emporte.
    if (-not (Test-Path (Join-Path $racine '.git'))) {
        Echec ("Le dossier .git n'est pas arrivé ici — sans lui, le code ne peut pas être mis à jour.`n`n" +
               "  C'est le seul dossier caché du projet : si vous êtes entré dans A-SCHOOL puis`n" +
               "  avez fait Ctrl+A, il n'a pas été sélectionné.`n`n" +
               "  Recopiez le DOSSIER A-SCHOOL lui-même (clic droit dessus, Copier), et non`n" +
               "  son contenu. Rien n'a été modifié.")
    }
    Echec "Ce dossier n'est pas relié au dépôt du code. Rien n'a été modifié."
}

# Si ce poste a du travail à lui qui n'est pas parti, le récupérer par-dessus
# le mélangerait. On le dit et on s'arrête : rien n'est touché.
# @{u} désigne l'endroit d'où vient le code. Sans ce lien, la comparaison
# plus bas ne renvoie rien, et « rien » se lirait comme « ce poste n'a rien
# en retard » — alors qu'on ne sait tout simplement pas.
git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec ("Ce dossier n'est relié à aucun dépôt distant : le code ne peut pas être mis à jour.`n" +
           "  Rien n'a été modifié.")
}

git fetch --quiet 2>$null | Out-Null
$enCours   = @(git status --porcelain 2>$null | Where-Object { $_ })
$nonPartis = @(git log --oneline '@{u}..HEAD' 2>$null | Where-Object { $_ })
if ($enCours.Count -gt 0 -or $nonPartis.Count -gt 0) {
    Write-Host ""
    Write-Host "  Ce poste a du travail à lui qui n'est pas encore parti." -ForegroundColor Yellow
    Write-Host "  Récupérer le code par-dessus le mélangerait. Rien n'a été modifié." -ForegroundColor Yellow
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

git pull --quiet 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec "Le code n'a pas pu être récupéré. Rien n'a été modifié, vous pouvez relancer ce script."
}
Write-Host "       code à jour." -ForegroundColor Green

# ── 4/6  Mise en route de ce qui garde votre travail ────────────────────
Write-Host "  4/6  Mise en route..." -ForegroundColor Cyan
docker compose up -d db 2>$null | Out-Null
if (-not (Attendre-Base)) {
    Echec "La mise en route a échoué. Rien n'a été modifié, vous pouvez relancer ce script."
}
Write-Host "       prêt." -ForegroundColor Green

# ── 5/6  Le filet : ce poste a-t-il quelque chose de plus récent ? ──────
Write-Host "  5/6  Contrôle..." -ForegroundColor Cyan
$datePoste = Date-Du-Poste

# On n'installe QUE sur un accord constaté. Le drapeau part baissé et ne se
# lève que dans deux cas prouvés : ce poste n'a rien de plus récent, ou le mot
# a été tapé. Tout le reste — date illisible, contrôle qui échoue, question qui
# tourne mal — le laisse baissé et rien n'est touché. Le silence n'est pas un oui,
# et « je ne sais pas » non plus.
$accordDonne = $false

if ($null -eq $datePoste -or $null -eq $dateApportee) {
    # On n'a pas pu établir la date d'un des deux côtés. Sans cette preuve,
    # on ne suppose rien : c'est à l'utilisateur de trancher en connaissance.
    Write-Host ""
    Write-Host "  Impossible de savoir si ce poste contient du travail plus récent" -ForegroundColor Yellow
    Write-Host "  que ce que vous apportez. Rien n'a été modifié." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Installer ce que vous apportez effacerait définitivement le travail de ce poste." -ForegroundColor Yellow
    $accordDonne = Demander-Remplacement
}
elseif ($datePoste -gt $dateApportee) {
    $ici     = [DateTimeOffset]::FromUnixTimeSeconds($datePoste).LocalDateTime
    $apporte = [DateTimeOffset]::FromUnixTimeSeconds($dateApportee).LocalDateTime
    Write-Host ""
    Write-Host "  Ce poste contient du travail plus récent que ce que vous apportez." -ForegroundColor Yellow
    Write-Host "  Rien n'a été modifié." -ForegroundColor Yellow
    Write-Host ""
    Write-Host ("    dernier travail sur ce poste : {0:dddd d MMMM yyyy à HH:mm}" -f $ici)     -ForegroundColor Yellow
    Write-Host ("    travail que vous apportez    : {0:dddd d MMMM yyyy à HH:mm}" -f $apporte) -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Installer ce que vous apportez effacerait définitivement le travail de ce poste." -ForegroundColor Yellow
    $accordDonne = Demander-Remplacement
}
else {
    Write-Host "       rien de plus récent ici." -ForegroundColor Green
    $accordDonne = $true
}

if (-not $accordDonne) {
    Write-Host ""
    Write-Host "  Rien n'a été modifié. Le travail de ce poste est intact." -ForegroundColor Green
    Write-Host ""
    exit 0
}

# ── 6/6  Installation ───────────────────────────────────────────────────
Write-Host "  6/6  Installation de votre travail..." -ForegroundColor Cyan

# Filet de dernière seconde : ce qui est déjà sur ce poste est mis de côté
# dans le dossier avant d'être remplacé.
#
# On ne saute cette sauvegarde que sur une base vide, où il n'y a rien à
# sauver. Quand la date n'a PAS pu être établie, on sauvegarde : c'est
# précisément le cas où l'on ignore ce qu'on s'apprête à écraser, donc celui
# où le filet compte le plus. L'ancienne condition l'écartait.
if ($null -eq $datePoste -or $datePoste -gt 0) {
    $sauvegarde = $false
    docker compose exec -T db pg_dump -U aschool -d aschool_dev -Fc -f /tmp/aschool_avant 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        docker compose cp db:/tmp/aschool_avant "$fichierAvant" 2>$null | Out-Null
        if ((Test-Path $fichierAvant) -and (Get-Item $fichierAvant).Length -ge 1024) { $sauvegarde = $true }
    }
    if ($sauvegarde) {
        Write-Host "       (le contenu actuel de ce poste a été mis de côté dans le dossier)" -ForegroundColor DarkGray
    } else {
        Write-Host "       (attention : le contenu actuel de ce poste n'a PAS pu être mis de côté)" -ForegroundColor Yellow
    }
}

docker compose cp "$fichierTravail" db:/tmp/aschool_arrivee 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec "Votre travail n'a pas pu être installé. Rien n'a été modifié, vous pouvez relancer ce script."
}

docker compose stop backend 2>$null | Out-Null

# pg_restore renvoie la même valeur pour une remarque anodine et pour un échec
# réel. « sans gravité » était donc affirmé sans être su. On garde ce qu'il dit
# et on sépare : les lignes « error » comptent, les « warning » non.
$journalRestauration = Join-Path $env:TEMP 'aschool_restauration.txt'
Remove-Item $journalRestauration -Force -ErrorAction SilentlyContinue

docker compose exec -T db pg_restore --clean --if-exists --no-owner -U aschool -d aschool_dev /tmp/aschool_arrivee 2>$journalRestauration | Out-Null
$codeInstallation = $LASTEXITCODE

$erreurs = @()
if (Test-Path $journalRestauration) {
    $erreurs = @(Get-Content $journalRestauration -ErrorAction SilentlyContinue |
                 Where-Object { $_ -match 'error:' -and $_ -notmatch 'does not exist|n.existe pas' })
    Remove-Item $journalRestauration -Force -ErrorAction SilentlyContinue
}

if ($erreurs.Count -gt 0) {
    Write-Host ""
    Write-Host "  Votre travail n'a pas été installé entièrement :" -ForegroundColor Red
    foreach ($e in $erreurs | Select-Object -First 8) { Write-Host "      $e" -ForegroundColor Red }
    Write-Host ""
    if (Test-Path $fichierAvant) {
        Write-Host "  Le contenu précédent de ce poste est dans  Bagage\avant_installation.aschool" -ForegroundColor Yellow
        Write-Host ""
    }
    Echec "N'utilisez pas l'application dans cet état : elle contiendrait un travail incomplet."
}
if ($codeInstallation -ne 0) {
    Write-Host "       installé, avec quelques remarques sans gravité." -ForegroundColor Yellow
} else {
    Write-Host "       installé." -ForegroundColor Green
}

Write-Host "       démarrage de l'application..." -ForegroundColor Cyan
docker compose up -d --build 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec "Votre travail est bien installé, mais l'application n'a pas démarré. Relancez ce script."
}

Write-Host ""
Write-Host "  Terminé. Ce poste contient votre travail et l'application démarre." -ForegroundColor Green
Write-Host "  Ouvrez :  http://localhost:5173" -ForegroundColor Green
if ($premiereFois) {
    Write-Host "  (première fois : laissez-lui une minute ou deux avant d'ouvrir)" -ForegroundColor DarkGray
}
# Le modèle qui lit les référentiels ne voyage pas : il pèse 4 Go en 12 fichiers
# que Windows ne sait pas copier. Il revient tout seul, mais pas instantanément.
$cacheVide = -not (Test-Path $cacheModele) -or -not (Get-ChildItem $cacheModele -Force -ErrorAction SilentlyContinue)
if ($cacheVide) {
    Write-Host ""
    Write-Host "  La première lecture d'un référentiel sera plus longue sur ce poste :" -ForegroundColor DarkGray
    Write-Host "  aSchool doit d'abord récupérer de quoi les lire (environ 2 Go, une seule fois)." -ForegroundColor DarkGray
}
Write-Host ""
