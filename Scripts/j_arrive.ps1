# ═════════════════════════════════════════════════════════════
#  A-SCHOOL — LA BASCULE D'UNE MACHINE À L'AUTRE, EN ENTIER
#  (ce cadre est identique dans les deux scripts : je_pars et j_arrive.
#   Vous ouvrez l'un ou l'autre, vous avez tout.)
#
#  LE RITUEL : UNE COMMANDE PAR POSTE, ET RIEN D'AUTRE.
#
#    1. sur la machine que vous QUITTEZ :   .\Scripts\je_pars.ps1
#    2. sur la machine où vous ARRIVEZ  :   .\Scripts\j_arrive.ps1
#
#  Rien à fermer, rien à rouvrir, rien à attendre, rien à glisser dans
#  l'explorateur. Si un programme doit être fermé, le script le ferme ;
#  s'il doit être ouvert, le script l'ouvre.
#
#    je_pars.ps1     enregistre et envoie votre code, sort la base dans
#                    Bagage\, ferme l'application, et DÉPOSE une valise
#                    A-SCHOOL-a-emporter à l'endroit que vous indiquez —
#                    demandé une seule fois : ensuite il s'en souvient.
#
#    j_arrive.ps1    trouve la valise, l'installe, récupère le code,
#                    refuse d'écraser quelque chose de plus récent,
#                    redémarre, puis jette la valise.
#
#  POURQUOI UNE VALISE, ET PAS LE DOSSIER DIRECTEMENT (02/08/2026)
#    Le départ écrivait droit dans le dossier vivant de l'autre poste, et
#    l'effaçait pour le remplacer. Or à cet instant rien ne tourne là-bas
#    pour se protéger : c'était donc à l'utilisateur d'y aller à la main
#    fermer l'application, fermer VS Code, puis revenir les rouvrir.
#    Quatre gestes sur une machine à laquelle il n'avait rien à demander,
#    et dont l'oubli faisait échouer la copie sur un fichier tenu ouvert.
#    Déposée à côté, la valise ne touche à rien : le dossier d'en face
#    peut tourner, être ouvert, être utilisé. C'est j_arrive, qui tourne
#    LÀ-BAS, qui installe — et un script qui tourne sur une machine sait
#    fermer et rouvrir ses propres programmes.
#
#  CE QUI VOYAGE : le dossier ENTIER, moins ce qui se refabrique.
#    Bagage\          la base de données (pg_dump) + la date du départ
#    REFERENTIELS\    les PDF déposés — hors dépôt, irremplaçables
#    .env             hors dépôt, identique sur les deux machines
#    .git             l'historique. Sans lui, plus de dépôt là-bas.
#    docker\hf-cache  4,3 Go, le modèle qui lit les référentiels. Lourd,
#                     mais il ne se retéléchargera PAS de lui-même :
#                     le dépôt pose HF_HUB_OFFLINE=1 partout. Sans lui,
#                     l'autre poste ne génère plus rien.
#    le code          et tout le reste du dossier
#
#  CE QUI NE VOYAGE PAS, parce que ça se refabrique vraiment sur place :
#    node_modules                 refait par le conteneur (15 300 fichiers)
#    docker\pgdata                un reste : la base vit dans le volume
#                                 nommé pgdata_dev, pas dans le dossier
#    __pycache__, .pytest_cache   caches de Python
#
#    .venv N'EXISTE PLUS — abandonné le 02/08/2026. Un environnement qui
#    ne survit pas à une bascule et qui exige internet pour renaître n'est
#    pas un outil, c'est une charge. Le seul Python du projet est celui du
#    conteneur : c'est lui qui fait tourner l'application, et désormais lui
#    aussi qui lance les tests (voir l'en-tête de n'importe quel fichier de
#    tests\). Les deux scripts le retirent encore s'ils en trouvent un :
#    c'est un reste, pas quelque chose qui renaîtra.
#
#    La copie ne se fait PAS dans l'explorateur Windows : il emporte les
#    fichiers inutiles, échoue sur les liens du cache du modèle, et saute
#    .git parce qu'il est caché.
#
#  PLACE DISQUE : la valise pèse le poids du dossier (6,5 Go, modèle
#    compris). Elle coexiste avec le dossier vivant le temps de la
#    bascule, puis j_arrive la jette. Prévoir 13 Go libres à l'arrivée.
#
#  « OÙ COPIER » = n'importe quel endroit atteignable des deux machines :
#    un chemin réseau de l'autre poste (\\FIXE\D$), une clé USB, un
#    disque externe, un dossier synchronisé. Demandé une seule fois.
#
#  EN CAS DE DOUTE : ces scripts s'arrêtent plutôt que de deviner, et
#    disent « Rien n'a été modifié » quand c'est le cas. Relancer un
#    script interrompu est toujours sans danger.
# ═════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────
#  j_arrive.ps1 — à lancer sur le poste où vous ARRIVEZ. Rien d'autre à faire.
#
#  Il ouvre le moteur si besoin, trouve la valise tout seul — sur une clé, un
#  disque, un dossier réseau — en tire tout ce qui ne voyage pas par le code,
#  vérifie chaque fichier, récupère le code, installe votre travail, redémarre
#  l'application, et jette la valise.
#
#  Rien à glisser dans l'explorateur, rien à fermer, rien à rouvrir : le départ
#  copiait et vérifiait, l'arrivée fait de même. Une commande à chaque bout.
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

# Le moteur, c'est Docker Desktop — mais ce nom ne sort jamais à l'écran. Il était
# demandé à l'utilisateur : « lancez-le, attendez qu'il soit vert, puis relancez ce
# script ». Trois choses à savoir, à retenir et à réussir dans l'ordre, pour un
# programme qu'un script sait ouvrir. S'il faut qu'il tourne, on l'ouvre.
#
# L'attente est celle du MOTEUR, pas de la fenêtre : Docker Desktop s'affiche bien
# avant de pouvoir répondre. On interroge donc le moteur jusqu'à ce qu'il réponde,
# et c'est cette réponse-là qui vaut « prêt ».
#
# (fonction identique dans je_pars.ps1 — les deux scripts se lisent seuls)
function Demarrer-Le-Moteur {
    docker info -f "{{.ServerVersion}}" 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { return $true }

    $exe = @("$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
             "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
             "$env:LOCALAPPDATA\Docker\Docker Desktop.exe") |
           Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $exe) { return $false }

    Write-Host "       démarrage du moteur, une minute environ..." -ForegroundColor DarkGray
    Start-Process -FilePath $exe -ErrorAction SilentlyContinue

    # 150 essais de 2 s = 5 minutes. Un poste qui sort de veille, ou qui démarre le
    # moteur pour la première fois, met couramment deux à trois minutes.
    for ($essai = 0; $essai -lt 150; $essai++) {
        Start-Sleep -Seconds 2
        docker info -f "{{.ServerVersion}}" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { return $true }
    }
    return $false
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

# CE QU'IL FAUT SORTIR DE LA VALISE : tout ce qui ne voyage pas par le code.
#
# Le modèle (docker\hf-cache) a rejoint cette liste le 02/08/2026, et c'est la
# conséquence directe de la valise. Tant que le départ écrasait le dossier d'en
# face, le modèle y arrivait tout seul, dans le tas. Déposé à côté, il n'arrive
# plus que si on l'en sort — et sans lui, plus une seule génération ne fonctionne
# (le mode hors-ligne du dépôt interdit de le retélécharger).
$A_SORTIR = @('Bagage', 'REFERENTIELS', '.env', 'docker\hf-cache')

# Les deux blobs du modèle pèsent 2,2 Go chacun. Les relire pour empreinte, des
# deux côtés, coûte des minutes pour un gain nul. Au-delà de ce poids on compare
# la TAILLE, qui est instantanée — même seuil et même raison qu'au départ.
$SEUIL_EMPREINTE = 20MB

# Chaque fichier est relu des deux côtés et comparé, exactement comme au départ.
# Une copie annoncée sans être vérifiée, c'est ce qui a coûté une journée.
function Poser-Depuis($valise) {
    $copies  = 0
    $ecarts  = @()
    $absents = @()
    foreach ($nom in $A_SORTIR) {
        $source = Join-Path $valise $nom
        if (-not (Test-Path $source)) { $absents += $nom; continue }
        $item = Get-Item $source -Force

        # On copie vers le dossier PARENT, pas vers la racine. « docker\hf-cache »
        # posé sur la racine donnerait un dossier « hf-cache » à côté de « docker »,
        # et le modèle serait là sans être là où on le cherche.
        $parent = Split-Path (Join-Path $racine $nom) -Parent
        New-Item -ItemType Directory -Force -Path $parent -ErrorAction SilentlyContinue | Out-Null
        Copy-Item -LiteralPath $source -Destination $parent -Recurse:$item.PSIsContainer -Force -ErrorAction SilentlyContinue

        if ($item.PSIsContainer) {
            # Le chemin est relevé depuis la VALISE, jamais depuis le dossier parent
            # de la source : sur un nom à deux étages, ce dernier rendait
            # « hf-cache\... » au lieu de « docker\hf-cache\... », et la vérification
            # allait chercher les fichiers au mauvais endroit.
            foreach ($f in Get-ChildItem -LiteralPath $source -Recurse -Force -File) {
                $relatif = $f.FullName.Substring($valise.TrimEnd('\').Length + 1)
                $arrivee = Join-Path $racine $relatif
                $copies++
                if (-not (Test-Path -LiteralPath $arrivee)) { $ecarts += $relatif; continue }
                if ($f.Length -ge $SEUIL_EMPREINTE) {
                    if ((Get-Item -LiteralPath $arrivee -Force).Length -ne $f.Length) { $ecarts += $relatif }
                    continue
                }
                if ((Get-FileHash -LiteralPath $arrivee).Hash -ne (Get-FileHash -LiteralPath $f.FullName).Hash) { $ecarts += $relatif }
            }
        } else {
            $arrivee = Join-Path $racine $nom
            $copies++
            if (-not (Test-Path -LiteralPath $arrivee)) { $ecarts += $nom }
            elseif ((Get-FileHash -LiteralPath $arrivee).Hash -ne (Get-FileHash -LiteralPath $item.FullName).Hash) { $ecarts += $nom }
        }
    }
    return [pscustomobject]@{ Copies = $copies; Ecarts = $ecarts; Absents = $absents }
}

# Venv-Etranger vivait ici. Elle lisait le chemin inscrit dans un environnement
# Python pour distinguer celui venu d'une autre machine (à retirer) de celui
# construit sur ce poste (à garder, « parce qu'il marche »). La distinction est
# morte avec la décision du 02/08/2026 : plus rien ne s'en sert, donc les deux
# se retirent. Retirée aussi, plutôt que laissée à dormir — une fonction que
# personne n'appelle finit par se faire rappeler par erreur.

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
    Echec ("Le moteur qui fait tourner aSchool n'est pas installé sur ce poste.`n" +
           "  Sans lui, votre travail ne peut pas être installé ici.")
}
if (-not (Demarrer-Le-Moteur)) {
    Echec ("Le moteur qui fait tourner aSchool ne répond pas, même après cinq minutes.`n" +
           "  Redémarrez ce poste, puis relancez ce script. Rien n'a été modifié.")
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Echec ("Ce poste ne sait pas aller chercher votre code en ligne.`n" +
           "  Il arriverait sans son code : l'arrivée s'arrête ici, rien n'a été modifié.")
}
Write-Host "       tout répond." -ForegroundColor Green

# ── 2/6  Ce que vous apportez entre dans le dossier ─────────────────────
Write-Host "  2/6  Ce que vous apportez..." -ForegroundColor Cyan

# L'application se ferme AVANT qu'on pose quoi que ce soit, et pas seulement par
# précaution : le dossier du modèle est partagé avec elle pendant qu'elle tourne
# (docker-compose.yml:86). Écrire dedans pendant qu'elle le lit, c'est le cas
# exact qui faisait échouer les copies — celui-là même qu'on demandait à
# l'utilisateur d'éviter à la main sur l'autre poste.
#
# Muet et sans conséquence si rien ne tourne : on ne dit donc rien ici.
docker compose stop 2>$null | Out-Null

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
    # Aucune valise trouvée. Si le dossier contient déjà le travail — c'est le cas
    # quand on a copié le dossier entier à la main — il n'y a rien à demander : on
    # s'en sert et on avance. Poser une question qui n'a qu'une seule réponse
    # possible, c'est offrir une occasion de se tromper pour rien.
    if (Test-Path $fichierTravail) {
        Write-Host "       déjà dans le dossier, rien à aller chercher." -ForegroundColor Green
    }
    else {
        # Là, en revanche, il n'y a vraiment rien : ni valise, ni travail dans le
        # dossier. La question a un sens, on la pose.
        Write-Host ""
        Write-Host "  Rien à installer n'a été trouvé sur ce poste." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "     Entrée      branchez la clé maintenant, je regarde à nouveau" -ForegroundColor White
        Write-Host "     un chemin   si ce que vous apportez est ailleurs (par exemple  E:\ )" -ForegroundColor White
        Write-Host ""
        $r = ''
        try { $r = Read-Host "  Votre choix" } catch { $r = '' }
        $r = "$r".Trim().Trim('"')

        if (-not $r) {
            $valises = @(Trouver-Valises)
            if ($valises.Count -ge 1) { $valise = $valises[0] }
            else {
                Echec ("Toujours rien trouvé. Rien n'a été modifié.`n" +
                       "  Sur le poste de départ, lancez  .\Scripts\je_pars.ps1  d'abord.")
            }
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
    Write-Host "       (le modèle en fait partie : comptez une minute)" -ForegroundColor DarkGray
    $bilan = Poser-Depuis $valise

    if ($bilan.Ecarts.Count -gt 0) {
        Write-Host ""
        Write-Host "  Ces fichiers ne sont pas arrivés correctement :" -ForegroundColor Red
        foreach ($e in $bilan.Ecarts | Select-Object -First 10) { Write-Host "      $e" -ForegroundColor Red }
        Echec "La copie n'est pas fiable. Relancez ce script ; s'il s'agit d'une clé, rebranchez-la."
    }
    if ($bilan.Absents.Count -gt 0) {
        Write-Host ("       (absent de ce que vous apportez : {0})" -f ($bilan.Absents -join ', ')) -ForegroundColor DarkGray
    }
    Write-Host ("       {0} fichiers posés, tous vérifiés un par un." -f $bilan.Copies) -ForegroundColor Green
}

# ── Les restes, retirés parce qu'ils ne servent plus ────────────────────
# On ne retire QUE ce dont on est sûr que rien ne le lit.
#
#   .venv          ABANDONNÉ le 02/08/2026, et donc retiré sans condition.
#                  Ce bloc ne retirait que celui venu d'une autre machine et
#                  gardait celui construit ici, « parce qu'il marche » — un
#                  raisonnement devenu faux le jour où plus rien ne s'en sert.
#                  Le commentaire promettait même son retour (python -m venv
#                  puis pip install) : promesse jamais tenue par ce script, et
#                  qui n'avait plus lieu d'être. Le seul Python du projet est
#                  celui de l'application, tests compris.
#   node_modules   jamais lu par l'application : le conteneur monte le sien
#                  (docker-compose.yml:104). Il se refait tout seul.
#   docker\hf-cache  JAMAIS retiré. C'est le modèle, 2,2 Go, et il vient
#                  d'être posé ci-dessus. Le retirer, c'est tout casser.
$retires = @()

foreach ($nom in @('.venv', 'venv')) {
    $chemin = Join-Path $racine $nom
    if (-not (Test-Path $chemin)) { continue }
    $poids = Poids-De $chemin
    Remove-Item $chemin -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path $chemin) {
        Write-Host "       (un ancien dossier d'outils n'a pas pu être retiré — sans gravité)" -ForegroundColor Yellow
    } else {
        $retires += ("un ancien dossier d'outils  ({0:N0} Mo, plus utilisé)" -f ($poids / 1MB))
    }
}

foreach ($nom in @('frontend\node_modules', 'node_modules')) {
    $chemin = Join-Path $racine $nom
    if (-not (Test-Path $chemin)) { continue }
    $poids = Poids-De $chemin
    Remove-Item $chemin -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path $chemin) {
        Write-Host "       (des fichiers d'affichage n'ont pas pu être retirés — sans gravité)" -ForegroundColor Yellow
    } else {
        $retires += ("les fichiers d'affichage  ({0:N0} Mo, refaits au démarrage)" -f ($poids / 1MB))
    }
}

if ($retires.Count -gt 0) {
    Write-Host "       retiré, parce que ça se refabrique tout seul :" -ForegroundColor DarkGray
    foreach ($r in $retires) { Write-Host "          $r" -ForegroundColor DarkGray }
}

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
        Echec ("L'historique de votre code n'est pas arrivé ici — sans lui, le code ne peut`n" +
               "  pas être mis à jour.`n`n" +
               "  Il est rangé dans le seul dossier CACHÉ du projet : si vous êtes entré dans`n" +
               "  A-SCHOOL puis avez fait Ctrl+A, il n'a pas été sélectionné.`n`n" +
               "  Recopiez le DOSSIER A-SCHOOL lui-même (clic droit dessus, Copier), et non`n" +
               "  son contenu. Rien n'a été modifié.")
    }
    Echec ("Ce dossier n'est relié à aucun abri en ligne : son code ne peut pas être mis`n" +
           "  à jour. Rien n'a été modifié.")
}

# Si ce poste a du travail à lui qui n'est pas parti, le récupérer par-dessus
# le mélangerait. On le dit et on s'arrête : rien n'est touché.
# @{u} désigne l'endroit d'où vient le code. Sans ce lien, la comparaison
# plus bas ne renvoie rien, et « rien » se lirait comme « ce poste n'a rien
# en retard » — alors qu'on ne sait tout simplement pas.
git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec ("Ce dossier ne sait pas d'où venir chercher son code : il n'est relié à aucun`n" +
           "  abri en ligne. Rien n'a été modifié.")
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

# La sortie n'est plus jetée. Cette commande peut avoir à reconstruire l'image
# du backend, et cette reconstruction installe torch et sentence-transformers :
# plusieurs minutes la première fois sur un poste. Muette, elle se lisait comme
# un plantage. Docker dit ce qu'il fait au fur et à mesure — on le laisse dire.
Write-Host ""
Write-Host "       Démarrage de l'application." -ForegroundColor Cyan
Write-Host "       Si l'image doit être reconstruite, comptez plusieurs minutes :" -ForegroundColor DarkGray
Write-Host "       la progression s'affiche ci-dessous." -ForegroundColor DarkGray
Write-Host ""
docker compose up -d --build
Write-Host ""
$codeDemarrage = $LASTEXITCODE

# ── Refaire les liens du modèle ─────────────────────────────────────────
# Le cache est arrivé sans ses 12 liens : Windows ne sait ni les lire ni les
# écrire. Les octets, eux, sont là (blobs\). Il ne manque que les noms.
# je_pars a relevé la carte depuis Linux ; on la rejoue ici depuis Linux.
# Sans cette étape, le modèle ne charge pas et plus rien ne se génère.
$fichierLiens = Join-Path $bagage 'liens_modele.txt'
if ($codeDemarrage -eq 0 -and (Test-Path $fichierLiens)) {
    Write-Host "       Remise en place des liens du modèle..." -ForegroundColor Cyan
    # Découpage par expansion de paramètre (${l%%|*} et ${l#*|}) : ni guillemets
    # imbriqués, ni antislash. PowerShell détruit les deux en passant la commande
    # à Docker. Les chemins du cache ne contiennent ni espace ni « | ».
    # Le compte final ne compte PAS les liens : il compte ceux qui MÈNENT
    # quelque part (test -e). Un lien peut exister et ne rien viser — c'est
    # arrivé, sur model.safetensors, à cause d'un retour chariot en trop.
    # Compter les liens aurait dit « 12 en place » sur un modèle inutilisable.
    $sortie = docker compose run --rm --no-deps -T backend sh -c 'cd /root/.cache/huggingface; while read l; do n=${l%%|*}; c=${l#*|}; mkdir -p ${n%/*}; rm -f $n; ln -s $c $n; done < /app/Bagage/liens_modele.txt; for f in $(find . -type l); do if [ -e $f ]; then echo x; fi; done | wc -l'
    $n = 0
    $der = @($sortie) | ForEach-Object { "$_".Trim() } | Where-Object { $_ -match '^\d+$' } | Select-Object -Last 1
    if ($der) { $n = [int]$der }
    $attendus = @(Get-Content $fichierLiens -ErrorAction SilentlyContinue | Where-Object { $_ }).Count
    if ($n -ge $attendus -and $attendus -gt 0) {
        Write-Host ("       $n liens en place." -f $n) -ForegroundColor Green
    } else {
        Write-Host "       ATTENTION : les liens du modèle n'ont pas pu être refaits" -ForegroundColor Red
        Write-Host ("       ($n en place, $attendus attendus). Les générations échoueront.") -ForegroundColor Red
    }
}

if ($codeDemarrage -ne 0) {
    Echec "Votre travail est bien installé, mais l'application n'a pas démarré. Relancez ce script."
}

# ── La valise est jetée, et seulement maintenant ────────────────────────
# Elle pèse le poids du dossier, modèle compris : la laisser, c'est garder deux
# fois aSchool sur ce poste jusqu'à la prochaine bascule, et risquer qu'une
# arrivée future réinstalle une valise périmée en la prenant pour la bonne.
#
# On ne la jette qu'ICI : après une installation vérifiée ET un démarrage
# réussi. Tant que l'un des deux n'est pas acquis, elle reste — c'est le seul
# exemplaire complet de ce que vous apportiez, et on ne détruit pas la copie
# de secours avant d'être sûr que l'original tient debout.
#
# Le dossier de départ, lui, n'a jamais été touché : rien n'est perdu même ici.
if ($valise -and (Test-Path $valise)) {
    $poidsValise = Poids-De $valise
    Remove-Item -LiteralPath $valise -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path $valise) {
        Write-Host ("       (ce que vous apportiez est resté à $valise — sans gravité)") -ForegroundColor DarkGray
    } else {
        Write-Host ("       {0:N1} Go rendus : ce que vous apportiez est installé, la copie est jetée." -f ($poidsValise / 1GB)) -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "  Terminé. Ce poste contient votre travail et l'application démarre." -ForegroundColor Green
Write-Host "  Ouvrez :  http://localhost:5173" -ForegroundColor Green
if ($premiereFois) {
    Write-Host "  (première fois : laissez-lui une minute ou deux avant d'ouvrir)" -ForegroundColor DarkGray
}
# Ce message disait que le modèle « revient tout seul ». C'était faux, et ça a
# coûté une bascule : HF_HUB_OFFLINE=1 est posé partout (docker-compose.yml et
# backend/rag/embeddings.py), le backend a
# donc interdiction d'aller le chercher. Absent, il le reste — et sans lui,
# plus une seule génération ne fonctionne. Ce n'est pas une lenteur au premier
# usage, c'est une panne, et elle se dit comme telle.
$cacheVide = -not (Test-Path $cacheModele) -or -not (Get-ChildItem $cacheModele -Force -ErrorAction SilentlyContinue)
if ($cacheVide) {
    Write-Host ""
    Write-Host "  ATTENTION : le modèle qui lit les référentiels n'est pas sur ce poste." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Générer une activité, une séance, un thème, une idée ou un exemple," -ForegroundColor Red
    Write-Host "  et découper un référentiel, ne fonctionneront pas." -ForegroundColor Red
    Write-Host ""
    Write-Host "  Il ne se retéléchargera pas de lui-même : le backend est réglé en" -ForegroundColor Yellow
    Write-Host "  mode hors-ligne. Il doit voyager dans la copie." -ForegroundColor Yellow
    Write-Host "  Relancez je_pars.ps1 depuis l'autre poste : il l'emporte désormais." -ForegroundColor Yellow
}
Write-Host ""
