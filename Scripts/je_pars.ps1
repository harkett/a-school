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
#  je_pars.ps1 — à lancer sur le poste que vous QUITTEZ.
#
#  Il fait partir votre code, fait entrer votre travail dans le dossier,
#  ferme l'application, puis copie le dossier vers l'endroit que vous
#  indiquez et vérifie chaque fichier un par un.
#
#  Ce script ne connaît aucune lettre de lecteur : il se repère depuis
#  son propre emplacement. Il fonctionne à l'identique que le dossier
#  soit sur C:, sur D: ou ailleurs.
# ─────────────────────────────────────────────────────────────

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ── Lancé depuis le terminal intégré de VS Code, ce script se coupait lui-même ──
# Il ferme VS Code plus bas (VS Code tient .git\index ouvert et fausse la
# vérification). Or VS Code emporte son terminal en se fermant : le script mourait
# au milieu de son travail, sans un mot.
#
# La procédure disait donc « fermez VS Code avant, et ne lancez pas depuis son
# terminal ». Deux choses à savoir, à retenir, et dont l'oubli casse la bascule —
# pour un problème que le script peut régler seul en se relançant ailleurs.
if ($env:TERM_PROGRAM -eq 'vscode') {
    Write-Host ""
    Write-Host "  Je continue dans une fenêtre à part." -ForegroundColor Cyan
    Write-Host "  (VS Code va se fermer pendant le départ : il ne peut pas m'héberger)" -ForegroundColor DarkGray
    Write-Host ""
    Start-Process powershell -ArgumentList @(
        '-NoExit', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`""
    ) -ErrorAction SilentlyContinue
    exit 0
}

$racine = Split-Path -Parent $PSScriptRoot
Set-Location $racine

$bagage         = Join-Path $racine 'Bagage'
$fichierTravail = Join-Path $bagage 'travail.aschool'
$fichierDate    = Join-Path $bagage 'depart.txt'

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

Write-Host ""
Write-Host "  A-SCHOOL — je pars" -ForegroundColor Cyan
Write-Host "  ══════════════════" -ForegroundColor Cyan
Write-Host ""

# ── 1/4  Le moteur doit tourner ─────────────────────────────────────────
Write-Host "  1/4  Vérification..." -ForegroundColor Cyan

# On demande d'abord si la commande existe, avant de la lancer. Une commande
# absente ne touche pas à $LASTEXITCODE : elle laisse la valeur de la
# précédente, et un 0 hérité d'un succès passé se lit alors comme un succès.
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Echec ("Le moteur qui fait tourner aSchool n'est pas installé sur ce poste.`n" +
           "  Sans lui, votre travail ne peut pas être récupéré.")
}
if (-not (Demarrer-Le-Moteur)) {
    Echec ("Le moteur qui fait tourner aSchool ne répond pas, même après cinq minutes.`n" +
           "  Redémarrez ce poste, puis relancez ce script. Rien n'a été modifié.")
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Echec ("Ce poste ne sait pas mettre votre code à l'abri en ligne.`n" +
           "  Impossible de vérifier qu'il est bien parti : le départ s'arrête ici.")
}
Write-Host "       le moteur tourne." -ForegroundColor Green

# ── 2/4  Le code part, sinon il manquera là-bas ─────────────────────────
# Le code ne voyage pas dans la copie : il passe par le dépôt. Ce qui n'est pas
# envoyé n'existera donc pas sur l'autre poste.
#
# Ce script renvoyait l'utilisateur le faire lui-même. C'était le seul endroit
# où la bascule s'arrêtait, à chaque fois, pour un geste que le script sait
# faire. Il l'enregistre et l'envoie donc lui-même : un départ, c'est justement
# le moment où plus rien ne doit rester derrière.
#
# Une seule chose n'est PAS faite à la place de l'utilisateur : trancher un
# conflit. C'est le seul endroit où du travail peut se perdre pour de bon.
Write-Host "  2/4  Envoi du code..." -ForegroundColor Cyan

git rev-parse --is-inside-work-tree 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec ("Ce dossier n'est relié à aucun abri en ligne : votre code n'a nulle part`n" +
           "  où partir, et il manquerait sur l'autre poste. Rien n'a été modifié.")
}

# @{u} désigne l'endroit où le code part. Sans ce lien, il n'y a nulle part où
# envoyer, et les comparaisons plus bas ne renverraient rien — « rien » se
# lisant alors comme « tout est parti », alors que RIEN ne serait parti.
git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec ("Ce dossier n'envoie son code nulle part : il n'est relié à aucun abri en ligne.`n" +
           "  Rien de ce poste n'arriverait sur l'autre. Rien n'a été modifié.")
}

# Ce qui traîne est enregistré tel quel. Le message dit d'où et quand : ce n'est
# pas un commit de travail, c'est un point de sauvegarde avant un départ.
$enCours = @(git status --porcelain 2>$null | Where-Object { $_ })
if ($enCours.Count -gt 0) {
    Write-Host ("       {0} élément(s) à enregistrer :" -f $enCours.Count) -ForegroundColor DarkGray
    foreach ($f in $enCours | Select-Object -First 10) { Write-Host "          $f" -ForegroundColor DarkGray }
    if ($enCours.Count -gt 10) { Write-Host ("          ... et {0} autres" -f ($enCours.Count - 10)) -ForegroundColor DarkGray }

    git add -A 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Echec "Votre travail n'a pas pu être préparé pour l'envoi. Rien n'a été modifié."
    }
    $message = "bascule : depart de {0}, le {1}" -f $env:COMPUTERNAME, (Get-Date -Format 'dd/MM/yyyy a HH:mm')
    git commit --quiet -m $message 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Echec "Votre travail n'a pas pu être enregistré. Rien n'a été modifié."
    }
    Write-Host "       enregistré." -ForegroundColor Green
}

# Le dépôt a pu avancer pendant ce temps — l'autre poste, un autre outil. Si on
# envoie sans se remettre dessus, l'envoi est refusé. --rebase pose notre
# travail par-dessus le leur. En cas de conflit on annule et on s'arrête :
# rien n'est perdu, l'enregistrement ci-dessus tient toujours.
$depotJoignable = $true
git fetch --quiet 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { $depotJoignable = $false }

$nonPartis = @(git log --oneline '@{u}..HEAD' 2>$null | Where-Object { $_ })

if (-not $depotJoignable) {
    if ($nonPartis.Count -gt 0) {
        Echec ("L'abri en ligne est injoignable : votre code ne peut pas partir, et il manquerait`n" +
               "  sur l'autre poste. Votre travail est enregistré ici, rien n'est perdu.")
    }
    Write-Host "       (abri en ligne injoignable, mais rien n'attendait de partir)" -ForegroundColor DarkGray
}
else {
    $enRetard = @(git log --oneline 'HEAD..@{u}' 2>$null | Where-Object { $_ })
    if ($enRetard.Count -gt 0) {
        git rebase --quiet '@{u}' 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            git rebase --abort 2>$null | Out-Null
            Echec ("L'abri en ligne contient du travail qui touche les mêmes endroits que le vôtre.`n" +
                   "  Je ne tranche pas un conflit à votre place : c'est le seul endroit où`n" +
                   "  du travail peut se perdre. Réglez-le, puis relancez ce script.`n" +
                   "  Votre travail est enregistré ici, rien n'est perdu.")
        }
        $nonPartis = @(git log --oneline '@{u}..HEAD' 2>$null | Where-Object { $_ })
    }

    if ($nonPartis.Count -gt 0) {
        git push --quiet 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Echec ("Le code n'a pas pu être envoyé : il manquerait sur l'autre poste.`n" +
                   "  Votre travail est enregistré ici, rien n'est perdu.")
        }
        Write-Host ("       {0} enregistrement(s) envoyé(s)." -f $nonPartis.Count) -ForegroundColor Green
    }
}

# Ce qu'on croit avoir fait, on le constate. Sans ce contrôle, un envoi
# silencieusement incomplet laisserait partir un dossier amputé de son code.
$resteIci    = @(git status --porcelain 2>$null | Where-Object { $_ })
$resteAPartir = @(git log --oneline '@{u}..HEAD' 2>$null | Where-Object { $_ })
if ($resteIci.Count -gt 0 -or $resteAPartir.Count -gt 0) {
    Echec ("Malgré l'envoi, du travail reste sur ce poste et manquerait sur l'autre.`n" +
           "  Rien d'autre n'a été modifié.")
}
Write-Host "       tout le code est parti." -ForegroundColor Green

# ── VS Code se ferme ici, et pas avant ──────────────────────────────────
# Il écrit en continu : état de session, caches d'extensions, et surtout
# .git\index que son extension git rafraîchit toute seule. Un fichier qui
# bouge entre la copie et la vérification serait signalé comme mal arrivé
# alors que tout va bien — une fausse alerte, c'est-à-dire le pire des
# messages, celui qui apprend à ne plus lire les messages.
#
# Mais on ne le ferme pas plus tôt : jusqu'ici, il fallait encore pouvoir
# enregistrer et envoyer. Une fois le code parti, il n'a plus rien à faire.
#
# Fermeture par la fenêtre, jamais par la force : VS Code met de côté les
# onglets non enregistrés et les retrouve au prochain lancement. Un arrêt
# brutal ne le garantit pas, et ce n'est pas à un script de bascule de
# décider du sort d'un texte que vous n'avez pas encore enregistré.
$vscode = @(Get-Process -Name 'Code' -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 })
if ($vscode.Count -gt 0) {
    Write-Host "  Fermeture de VS Code..." -ForegroundColor Cyan
    foreach ($p in $vscode) { $p.CloseMainWindow() | Out-Null }
    for ($essai = 0; $essai -lt 15; $essai++) {
        Start-Sleep -Seconds 1
        if (-not (Get-Process -Name 'Code' -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 })) { break }
    }
    if (Get-Process -Name 'Code' -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 }) {
        Write-Host "       VS Code ne s'est pas fermé — il attend sans doute une réponse à l'écran." -ForegroundColor Yellow
        Write-Host "       Fermez-le à la main. Sinon la vérification, tout à l'heure, pourra" -ForegroundColor Yellow
        Write-Host "       signaler des fichiers comme mal arrivés alors qu'ils vont bien." -ForegroundColor Yellow
    } else {
        Write-Host "       fermé." -ForegroundColor Green
    }
}

# ── 3/4  Votre travail entre dans le dossier ────────────────────────────
# Votre travail ne se trouve pas dans le dossier : il vit à côté. On le
# fait donc entrer dans le dossier, seul moyen de l'emporter.
Write-Host "  3/4  Je place votre travail dans le dossier..." -ForegroundColor Cyan

docker compose up -d db 2>$null | Out-Null
$pret = $false
for ($essai = 0; $essai -lt 60; $essai++) {
    docker compose exec -T db pg_isready -U aschool -d aschool_dev 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $pret = $true; break }
    Start-Sleep -Seconds 2
}
if (-not $pret) {
    Echec "Impossible d'accéder à votre travail sur ce poste. Rien n'a été modifié."
}

New-Item -ItemType Directory -Force -Path $bagage | Out-Null

# La copie de sécurité prise lors d'une arrivée appartient à CE poste : elle
# n'a rien à faire dans le voyage, et elle doublerait le poids à copier.
Remove-Item (Join-Path $bagage 'avant_installation.aschool') -Force -ErrorAction SilentlyContinue

docker compose exec -T db pg_dump -U aschool -d aschool_dev -Fc -f /tmp/aschool_bascule 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec "Votre travail n'a pas pu être récupéré. Rien n'a été modifié, vous pouvez relancer ce script."
}

docker compose cp db:/tmp/aschool_bascule "$fichierTravail" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $fichierTravail)) {
    Echec "Votre travail n'a pas pu être placé dans le dossier. Rien n'a été modifié, vous pouvez relancer ce script."
}
if ((Get-Item $fichierTravail).Length -lt 1024) {
    Echec "Le travail récupéré est vide, ce n'est pas normal. Rien n'a été modifié, vous pouvez relancer ce script."
}

# La date du départ voyage avec le travail : à l'arrivée, elle sert à vérifier
# que l'autre poste ne contient pas quelque chose de plus récent.
#
# Le fichier est d'abord RETIRÉ, puis réécrit. Le 02/08/2026, un depart.txt
# resté verrouillé par un pilote de filtrage a fait échouer Set-Content sans
# arrêter le script : le fichier est parti VIDE, et j_arrive, incapable de lire
# la date, réclamait le mot « remplacer » sur une bascule pourtant normale.
# Un chemin neuf s'écrit toujours ; c'est le fichier existant qui bloquait.
Remove-Item $fichierDate -Force -ErrorAction SilentlyContinue
[DateTimeOffset]::UtcNow.ToUnixTimeSeconds().ToString() | Set-Content -Path $fichierDate -Encoding ascii -ErrorAction SilentlyContinue

# Et on CONSTATE, au lieu de supposer que l'écriture a eu lieu. C'est ce
# contrôle qui manquait : sans lui, l'échec voyageait jusqu'à l'autre poste.
$dateEcrite = ''
if (Test-Path $fichierDate) { $dateEcrite = (Get-Content $fichierDate -Raw -ErrorAction SilentlyContinue).Trim() }
if ($dateEcrite -notmatch '^\d+$') {
    Echec ("La date du départ n'a pas pu être écrite dans  Bagage\depart.txt`n" +
           "  Sans elle, l'autre poste ne saura pas si ce que vous apportez est plus`n" +
           "  récent que ce qu'il a, et vous demandera de trancher à l'aveugle.`n`n" +
           "  Le fichier est retenu par un programme — antivirus, sauvegarde, ou`n" +
           "  synchronisation. Renommez-le à la main, puis relancez ce script.`n" +
           "  Votre travail est déjà dans le dossier, rien n'est perdu.")
}

# ── La carte des liens du modèle ────────────────────────────────────────
# Le cache du modèle est bâti en deux étages : blobs\ porte les octets sous des
# noms illisibles, snapshots\ porte 12 LIENS qui leur donnent leurs vrais noms
# (config.json, model.safetensors, tokenizer.json…). Sans ces liens, le modèle
# ne charge pas — et sans le modèle, plus une seule génération ne fonctionne.
#
# Ces liens viennent de Linux, et WINDOWS NE SAIT PAS LES LIRE. Aucun outil
# Windows ne les reproduira. On emporte donc leur CARTE, lue depuis Linux où
# elle est lisible, et j_arrive refera les liens là-bas, depuis Linux aussi.
# Le cache est monté dans le conteneur backend (docker-compose.yml:86).
$fichierLiens = Join-Path $bagage 'liens_modele.txt'
Remove-Item $fichierLiens -Force -ErrorAction SilentlyContinue

if (Test-Path (Join-Path $racine 'docker\hf-cache')) {
    Write-Host "       relevé des liens du modèle..." -ForegroundColor DarkGray

    # Deux listes plutôt qu'une, et PAS LA MOINDRE séquence d'échappement :
    # PowerShell mange les \t et \n en passant la commande à Docker (la sortie
    # revenait collée en un seul bloc), et casse les guillemets imbriqués.
    # find rend ses lignes tout seul, et « -exec … + » garde le même ordre de
    # parcours : les deux listes s'apparient donc rang par rang.
    $brut   = docker compose run --rm --no-deps -T backend sh -c 'cd /root/.cache/huggingface; find . -type l; echo ---; find . -type l -exec readlink {} +'
    $lignes = @($brut) | ForEach-Object { "$_".Trim() } | Where-Object { $_ }
    $sep    = [Array]::IndexOf($lignes, '---')

    $noms = @(); $cibles = @()
    if ($sep -gt 0 -and $sep -lt ($lignes.Count - 1)) {
        $noms   = @($lignes[0..($sep - 1)]                 | Where-Object { $_ -like './*' })
        $cibles = @($lignes[($sep + 1)..($lignes.Count -1)] | Where-Object { $_ -like '*blobs/*' })
    }

    # On n'écrit la carte que si les deux listes se correspondent. Une carte
    # bancale referait de MAUVAIS liens là-bas — pire que pas de carte du tout.
    if ($noms.Count -gt 0 -and $noms.Count -eq $cibles.Count) {
        $paires = for ($k = 0; $k -lt $noms.Count; $k++) { "{0}|{1}" -f $noms[$k], $cibles[$k] }

        # Écrit en fins de ligne UNIX, et surtout PAS avec Set-Content : celui-ci
        # termine le fichier par un CRLF, et le « read » du shell garde alors le
        # retour chariot. Il se collait au nom du blob de la DERNIÈRE ligne, qui
        # devenait introuvable — un lien sur douze cassé, et pas n'importe lequel :
        # model.safetensors, le modèle lui-même. Le symptôme était invisible
        # (le lien existait, il pointait juste un caractère à côté).
        [IO.File]::WriteAllText($fichierLiens, (($paires -join "`n") + "`n"))
        Write-Host ("       {0} liens relevés." -f $noms.Count) -ForegroundColor Green
    } else {
        # On ne se tait pas : sans cette carte, l'autre poste aura les octets du
        # modèle sans les noms, et ne pourra rien générer sans qu'on lui dise
        # pourquoi. C'est exactement le silence qui a coûté une bascule.
        Write-Host "       (aucun lien relevé — le modèle risque de ne pas charger là-bas)" -ForegroundColor Yellow
    }
}
Write-Host "       c'est fait." -ForegroundColor Green

# ── 4/4  Fermer proprement ──────────────────────────────────────────────
# Après cette fermeture, plus rien ne bouge : le travail mis dans le
# dossier reste le reflet exact de ce poste.
Write-Host "  4/4  Fermeture de l'application..." -ForegroundColor Cyan
docker compose stop 2>$null | Out-Null
Write-Host "       fermée." -ForegroundColor Green

# ── Les cinq dossiers qui ne voyagent pas ───────────────────────────────
# Ils font du volume et ils se refabriquent tous sur place :
#
#   .venv, node_modules   55 400 + 15 300 fichiers, réinstallés par pip et npm
#   pgdata                la base ne vit plus là : volume nommé pgdata_dev
#                         (docker-compose.yml:24). Ce dossier est un reste.
#   __pycache__, .pytest_cache   caches de Python
#
# DEUX dossiers lourds voyagent quand même, et il faut savoir pourquoi :
#
#   .git             sans lui, l'autre poste n'a plus de dépôt et j_arrive
#                    s'arrête à 3/6.
#   docker\hf-cache  4,3 Go, le modèle qui lit les référentiels. Il a été
#                    écarté d'ici le 02/08/2026, au motif qu'il « se
#                    retéléchargerait tout seul ». C'était faux :
#                    HF_HUB_OFFLINE=1 est posé partout (docker-compose.yml et
#                    backend/rag/embeddings.py), le backend a
#                    donc interdiction d'aller le chercher. Sans ce dossier,
#                    l'autre poste ne peut plus rien générer — ni activité,
#                    ni séance, ni thème, ni idée, ni exemple. Il coûte cher
#                    à copier ; ne pas le copier coûte l'application entière.
$ecartes = @('.venv', 'node_modules', '__pycache__', '.pytest_cache', 'pgdata')

# ── « Où copier » ne se demande qu'une fois dans une vie ────────────────
# La réponse est toujours la même — c'est le même autre poste. La redemander à
# chaque départ, c'est faire retaper un chemin réseau exact, à la main, au seul
# moment où une faute de frappe coûte une bascule.
#
# Retenue HORS du dossier, et volontairement : le dossier voyage. Écrite dedans,
# la réponse du portable arriverait sur le fixe et lui proposerait de copier vers
# lui-même. Chaque poste garde donc la sienne, dans ses réglages à lui.
$memoire = Join-Path $env:LOCALAPPDATA 'aSchool\dernier_endroit.txt'
$connu   = ''
if (Test-Path $memoire) { $connu = (Get-Content $memoire -Raw -ErrorAction SilentlyContinue).Trim() }

Write-Host ""
Write-Host "  C'est prêt." -ForegroundColor Green
Write-Host ""
Write-Host "  Où copier le dossier ?" -ForegroundColor Cyan
Write-Host ""
if ($connu) {
    Write-Host ("      Entrée      le même endroit que la dernière fois  ({0})" -f $connu) -ForegroundColor White
    Write-Host  '      un chemin   pour copier ailleurs' -ForegroundColor White
} else {
    Write-Host '      un chemin réseau de l''autre poste    \\FIXE\D$' -ForegroundColor White
    Write-Host '      une clé, un disque externe           E:'         -ForegroundColor White
    Write-Host '      ou Entrée pour le faire vous-même.'              -ForegroundColor White
}
Write-Host ""
$ou = ''
try { $ou = Read-Host "  Où copier" } catch { $ou = '' }
$ou = "$ou".Trim().Trim('"')

# Entrée + un endroit retenu = cet endroit. On le redit à l'écran : une touche
# qui déclenche une copie de plusieurs gigaoctets doit dire où elle l'envoie.
if (-not $ou -and $connu) {
    $ou = $connu
    Write-Host ("       vers $ou") -ForegroundColor Green
}

# Entrée sans endroit retenu : il n'y a rien à deviner. Ce cas affichait une
# commande de copie à recopier soi-même — une ligne de trente caractères
# techniques, à taper juste, au seul moment où l'on ne sait pas quoi faire.
# C'était le contraire du but : donner du travail à celui qui vient de dire
# qu'il ne savait pas où copier.
#
# Rien n'est perdu ici : votre travail est déjà dans le dossier, et le code est
# déjà parti. Il ne manque que la destination, et elle ne se devine pas.
if (-not $ou) {
    Write-Host ""
    Write-Host "  Il me faut un endroit où déposer, sinon rien ne peut partir." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Relancez ce script et indiquez, par exemple :" -ForegroundColor Yellow
    Write-Host '      \\FIXE\D$    le disque de l''autre poste, par le réseau' -ForegroundColor White
    Write-Host '      E:           une clé ou un disque branché ici' -ForegroundColor White
    Write-Host ""
    Write-Host "  Vous ne l'indiquerez qu'une fois : ensuite je m'en souviens." -ForegroundColor Green
    Write-Host ""
    Write-Host "  Votre travail est déjà dans le dossier et votre code est déjà parti :" -ForegroundColor Green
    Write-Host "  rien n'est perdu, il manque seulement la destination." -ForegroundColor Green
    Write-Host ""
    exit 0
}

if (-not (Test-Path $ou)) {
    Echec "Cet endroit n'existe pas : $ou`n  Rien n'a été modifié."
}

# ── On dépose À CÔTÉ, jamais dans le dossier vivant d'en face ───────────
# C'est le changement du 02/08/2026, et il vaut quatre gestes.
#
# Avant, la copie allait droit dans le dossier A-SCHOOL de l'autre poste et le
# remplaçait. Or à cet instant, rien ne tourne là-bas pour se protéger : c'était
# donc à l'utilisateur d'y aller à la main fermer l'application, fermer VS Code,
# puis revenir les rouvrir. Quatre allers-retours sur une machine à laquelle il
# n'avait rien à demander, et dont l'oubli faisait échouer la copie sur un
# fichier tenu ouvert.
#
# Déposé à côté, le dossier vivant d'en face n'est pas touché : il peut tourner,
# être ouvert, être utilisé. C'est j_arrive, qui tourne LÀ-BAS, qui installera —
# et un script qui tourne sur une machine sait fermer et rouvrir ses programmes.
#
# La valise porte le nom que j_arrive cherche déjà sur les disques branchés.
$NOM_VALISE  = 'A-SCHOOL-a-emporter'
$destination = Join-Path $ou $NOM_VALISE

# /MIR aligne la destination sur la source, suppressions comprises. C'est
# nécessaire : un fichier qui n'existerait QUE dans la valise y resterait d'une
# bascule à l'autre, et repartirait indéfiniment.
# Mais /MIR sur un mauvais chemin efface. On refuse donc d'écrire dans un
# dossier existant qui ne serait pas déjà une valise.
if ((Test-Path $destination) -and -not (Test-Path (Join-Path $destination 'docker-compose.yml'))) {
    Echec ("$destination existe déjà, mais ce n'est pas une valise aSchool.`n" +
           "  Je refuse d'écrire dedans : la copie y supprimerait ce qui s'y trouve.`n" +
           "  Rien n'a été modifié.")
}

# Le garde-fou qui manquait : on ne dépose pas la valise DANS le dossier d'où
# l'on part. Elle se copierait elle-même en se remplissant.
if ($destination.TrimEnd('\').ToLower().StartsWith($racine.TrimEnd('\').ToLower())) {
    Echec ("Cet endroit est à l'intérieur du dossier de travail : la copie se`n" +
           "  recopierait elle-même sans jamais finir. Choisissez un autre endroit.`n" +
           "  Rien n'a été modifié.")
}

Write-Host ""
Write-Host "  Copie vers $destination" -ForegroundColor Cyan
Write-Host "  (le dossier entier, moins les six qui se refabriquent)" -ForegroundColor DarkGray
Write-Host ""

# /NFL tait la liste des fichiers — 6 000 lignes n'apprennent rien. Mais les
# DOSSIERS s'affichent : sans eux, robocopy reste muet le temps de la copie,
# et un écran figé pendant vingt minutes se lit comme un plantage.
#
# /XJ écarte les 12 liens du cache du modèle, et c'est volontaire.
#
# Ils ont été créés depuis Linux, par Docker. Windows ne sait pas les LIRE —
# pas seulement les copier : les lire. Get-Content répond « le système ne peut
# pas accéder au fichier », LinkType et Target sont vides. Sans /XJ, robocopy
# les tente, échoue (code 9), et laisse douze fichiers VIDES à l'arrivée : le
# modèle ne charge pas davantage, et l'échec passe pour un problème de droits.
#
# Ce ne sont que des noms : les octets, eux, sont dans blobs\ et voyagent.
# La carte « nom -> blob » part dans Bagage\liens_modele.txt (étape 3/4), et
# j_arrive refait les liens là-bas depuis Linux, qui sait les faire.
robocopy $racine $destination /MIR /XJ /XD @ecartes /NFL /R:2 /W:2

# robocopy ne suit pas la convention des autres commandes : 0 à 7 sont des
# succès (0 = rien à faire, 1 = fichiers copiés, 2 = extras supprimés, et les
# combinaisons), 8 et au-delà sont de vrais échecs. Lire « -ne 0 » comme
# ailleurs déclarerait en échec la copie la plus normale qui soit.
if ($LASTEXITCODE -ge 8) {
    Echec "La copie a échoué (code $LASTEXITCODE). Vérifiez que $ou est accessible en écriture. Rien n'a été modifié ici."
}

# Vérification : chaque fichier est relu des deux côtés et comparé. Une copie
# annoncée sans être vérifiée, c'est ce qui a coûté une journée. robocopy dit
# ce qu'il a fait ; il ne dit pas ce qui est arrivé.
Write-Host ""
Write-Host "  Vérification de chaque fichier des deux côtés..." -ForegroundColor Cyan

$motifEcartes = ($ecartes | ForEach-Object { [regex]::Escape("\$_\") }) -join '|'

# On compte d'abord, pour pouvoir dire où on en est. Ce comptage prend quelques
# secondes ; le quart d'heure qui suit se passait sans un mot, et un écran figé
# se lit comme un plantage. C'est arrivé.
$fichiers = @(Get-ChildItem -LiteralPath $racine -Recurse -Force -File -ErrorAction SilentlyContinue |
              Where-Object { "\$($_.FullName.Substring($racine.Length + 1))\" -notmatch $motifEcartes })
$total = $fichiers.Count
Write-Host ("       $total fichiers à relire des deux côtés. Les octets de la destination") -ForegroundColor DarkGray
Write-Host  "       repassent par le réseau : comptez le même temps que la copie." -ForegroundColor DarkGray
Write-Host ""

# Deux cas ne se vérifient PAS par empreinte, et il faut savoir pourquoi.
#
#   Les liens (snapshots\ du modèle) : leur contenu EST le blob vers lequel ils
#   pointent, et ce blob est déjà vérifié pour lui-même. Les relire ferait
#   repasser les mêmes octets une seconde fois. On contrôle qu'ils existent.
#
#   Les gros fichiers : les deux blobs du modèle pèsent 2,2 Go chacun. Les
#   relire depuis le réseau coûtait quatre heures et demie sur un lien lent,
#   pour un gain nul — robocopy relit, réessaie et signale ses échecs sur ces
#   fichiers-là. On compare leur taille, qui est instantanée.
#
# Tout le reste — le code, .git, les référentiels, la base — passe à l'empreinte.
$SEUIL_EMPREINTE = 20MB

$chrono  = [System.Diagnostics.Stopwatch]::StartNew()
$ecarts  = @()
$comptes = 0
foreach ($f in $fichiers) {
    $relatif = $f.FullName.Substring($racine.Length + 1)
    $arrivee = Join-Path $destination $relatif
    $comptes++

    # Une seule ligne réécrite sur place, plutôt que 6 000 lignes qui défilent.
    # Après cinquante fichiers, la cadence est connue : on annonce ce qui reste.
    if ($comptes % 25 -eq 0 -or $comptes -eq $total) {
        $reste = ''
        if ($comptes -gt 50) {
            $s = [int](($chrono.Elapsed.TotalSeconds / $comptes) * ($total - $comptes))
            $reste = "  —  encore {0} min {1:00} s" -f [int]($s / 60), ($s % 60)
        }
        Write-Host ("`r       {0}/{1}  ({2} %){3}          " -f $comptes, $total, [int](100 * $comptes / $total), $reste) -NoNewline -ForegroundColor DarkGray
    }

    if (-not (Test-Path -LiteralPath $arrivee)) { $ecarts += $relatif; continue }

    if ($f.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        continue                                   # un lien : sa présence suffit
    }
    if ($f.Length -ge $SEUIL_EMPREINTE) {
        $la = (Get-Item -LiteralPath $arrivee -Force).Length
        if ($la -ne $f.Length) { $ecarts += $relatif }
        continue                                   # gros fichier : taille seulement
    }
    if ((Get-FileHash -LiteralPath $arrivee).Hash -ne (Get-FileHash -LiteralPath $f.FullName).Hash) { $ecarts += $relatif }
}
$chrono.Stop()
Write-Host ""

if ($ecarts.Count -gt 0) {
    Write-Host ""
    Write-Host "  Ces fichiers ne sont pas arrivés correctement :" -ForegroundColor Red
    foreach ($e in $ecarts | Select-Object -First 10) { Write-Host "      $e" -ForegroundColor Red }
    if ($ecarts.Count -gt 10) { Write-Host ("      ... et {0} autres" -f ($ecarts.Count - 10)) -ForegroundColor Red }
    Echec "La copie n'est pas fiable. Relancez ce script."
}

Write-Host ("       $comptes fichiers copiés, tous vérifiés un par un.") -ForegroundColor Green

# L'endroit n'est retenu qu'ICI : une copie vérifiée fichier par fichier. Le
# retenir plus tôt reviendrait à proposer par défaut, la prochaine fois, un
# endroit qui n'a jamais reçu quoi que ce soit.
New-Item -ItemType Directory -Force -Path (Split-Path $memoire -Parent) -ErrorAction SilentlyContinue | Out-Null
Set-Content -Path $memoire -Value $ou -Encoding utf8 -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "  C'est en place." -ForegroundColor Green
Write-Host ""
Write-Host "  Sur l'autre poste, une seule chose à faire :" -ForegroundColor Green
Write-Host "      .\Scripts\j_arrive.ps1" -ForegroundColor White
Write-Host ""
Write-Host "  Rien à fermer, rien à rouvrir, rien à attendre : il s'en charge." -ForegroundColor DarkGray
Write-Host ""
