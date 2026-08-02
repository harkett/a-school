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
#    Bagage\          la base de données (pg_dump) + la date du départ
#    REFERENTIELS\    les PDF déposés — hors dépôt, irremplaçables
#    .env             hors dépôt, identique sur les deux machines
#    .git             l'historique. Sans lui, plus de dépôt là-bas.
#    docker\hf-cache  4,3 Go, le modèle qui lit les référentiels. Lourd,
#                     mais il ne se retéléchargera PAS de lui-même :
#                     backend/main.py:11 pose HF_HUB_OFFLINE=1. Sans lui,
#                     l'autre poste ne génère plus rien.
#    le code          et tout le reste du dossier
#
#  CE QUI NE VOYAGE PAS, parce que ça se refabrique vraiment sur place :
#    .venv, node_modules          réinstallés par pip et npm (70 700 fichiers)
#    docker\pgdata                un reste : la base vit dans le volume
#                                 nommé pgdata_dev, pas dans le dossier
#    __pycache__, .pytest_cache   caches de Python
#
#    La copie ne se fait PAS dans l'explorateur Windows : il emporte les
#    70 000 fichiers inutiles, échoue sur les liens du cache du modèle, et
#    saute .git parce qu'il est caché.
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
    Echec "Docker Desktop n'est pas installé sur ce poste. Sans lui, votre travail ne peut pas être récupéré."
}
docker info -f "{{.ServerVersion}}" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec "Docker Desktop n'est pas démarré. Lancez-le, attendez qu'il soit vert, puis relancez ce script."
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Echec "Git n'est pas installé sur ce poste. Impossible de vérifier que votre code est bien parti."
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
    Echec "Ce dossier n'est pas relié au dépôt du code. Rien n'a été modifié."
}

# @{u} désigne l'endroit où le code part. Sans ce lien, il n'y a nulle part où
# envoyer, et les comparaisons plus bas ne renverraient rien — « rien » se
# lisant alors comme « tout est parti », alors que RIEN ne serait parti.
git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Echec ("Ce dossier n'envoie son code nulle part : la branche n'est reliée à aucun dépôt.`n" +
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
        Echec ("Le dépôt est injoignable : votre code ne peut pas partir, et il manquerait`n" +
               "  sur l'autre poste. Votre travail est enregistré ici, rien n'est perdu.")
    }
    Write-Host "       (dépôt injoignable, mais rien n'attendait de partir)" -ForegroundColor DarkGray
}
else {
    $enRetard = @(git log --oneline 'HEAD..@{u}' 2>$null | Where-Object { $_ })
    if ($enRetard.Count -gt 0) {
        git rebase --quiet '@{u}' 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            git rebase --abort 2>$null | Out-Null
            Echec ("Le dépôt contient du travail qui touche les mêmes endroits que le vôtre.`n" +
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
#                    backend/main.py:11 pose HF_HUB_OFFLINE=1, le backend a
#                    donc interdiction d'aller le chercher. Sans ce dossier,
#                    l'autre poste ne peut plus rien générer — ni activité,
#                    ni séance, ni thème, ni idée, ni exemple. Il coûte cher
#                    à copier ; ne pas le copier coûte l'application entière.
$ecartes = @('.venv', 'node_modules', '__pycache__', '.pytest_cache', 'pgdata')

Write-Host ""
Write-Host "  C'est prêt." -ForegroundColor Green
Write-Host ""
Write-Host "  Où copier le dossier ?" -ForegroundColor Cyan
Write-Host ""
Write-Host '      un chemin réseau de l''autre poste    \\FIXE\D$' -ForegroundColor White
Write-Host '      une clé, un disque externe           E:'         -ForegroundColor White
Write-Host '      ou Entrée pour le faire vous-même.'              -ForegroundColor White
Write-Host ""
$ou = ''
try { $ou = Read-Host "  Où copier" } catch { $ou = '' }
$ou = "$ou".Trim().Trim('"')

if (-not $ou) {
    Write-Host ""
    Write-Host "  Entendu. N'utilisez pas l'explorateur Windows : il emporterait les" -ForegroundColor Green
    Write-Host "  79 000 fichiers, échouerait sur les liens du modèle, et sauterait" -ForegroundColor Green
    Write-Host "  .git parce qu'il est caché. Cette commande-ci fait le tri :" -ForegroundColor Green
    Write-Host ""
    Write-Host ("      robocopy `"{0}`" `"<destination>\A-SCHOOL`" /MIR /XJ /XD {1}" -f $racine, ($ecartes -join ' ')) -ForegroundColor White
    Write-Host ""
    Write-Host "  Puis, sur l'autre poste :  .\Scripts\j_arrive.ps1" -ForegroundColor Green
    Write-Host ""
    exit 0
}

if (-not (Test-Path $ou)) {
    Echec "Cet endroit n'existe pas : $ou`n  Rien n'a été modifié."
}

$destination = Join-Path $ou 'A-SCHOOL'

# /MIR aligne la destination sur la source, suppressions comprises. C'est
# nécessaire : un fichier qui n'existerait QUE là-bas resterait, et j_arrive
# s'arrêterait à 3/6 en le prenant pour du travail local de ce poste.
# Mais /MIR sur un mauvais chemin efface. On refuse donc d'écrire dans un
# dossier existant qui ne serait pas déjà un A-SCHOOL.
if ((Test-Path $destination) -and -not (Test-Path (Join-Path $destination 'docker-compose.yml'))) {
    Echec ("$destination existe déjà, mais ce n'est pas un dossier A-SCHOOL.`n" +
           "  Je refuse d'écrire dedans : /MIR y supprimerait ce qui s'y trouve.`n" +
           "  Rien n'a été modifié.")
}

# ── Docker doit être fermé LÀ-BAS, et surtout pas ici ───────────────────
# /MIR supprime et remplace à la destination. Un conteneur qui tourne là-bas
# tient des fichiers ouverts : la copie bute dessus, et l'application se fait
# retirer le sol sous les pieds en pleine marche.
# Ici, au contraire, Docker doit rester ouvert — l'étape 3/4 vient de s'en
# servir pour sortir votre base.
Write-Host ""
Write-Host "  AVANT DE CONTINUER" -ForegroundColor Yellow
Write-Host "  ══════════════════" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Fermez Docker Desktop sur le poste qui REÇOIT." -ForegroundColor Yellow
Write-Host "  (pas sur celui-ci : ici, il doit rester ouvert)" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  La copie remplace et supprime là-bas. Elle butera sur tout fichier" -ForegroundColor Yellow
Write-Host "  qu'un conteneur y tient ouvert." -ForegroundColor Yellow
Write-Host ""
try { Read-Host "  Entrée quand c'est fait" | Out-Null } catch { }

Write-Host ""
Write-Host "  Copie vers $destination" -ForegroundColor Cyan
Write-Host "  (le dossier entier, moins les six qui se refabriquent)" -ForegroundColor DarkGray
Write-Host ""

# /NFL tait la liste des fichiers — 6 000 lignes n'apprennent rien. Mais les
# DOSSIERS s'affichent : sans eux, robocopy reste muet le temps de la copie,
# et un écran figé pendant vingt minutes se lit comme un plantage.
#
# PAS de /XJ. Le cache du modèle est bâti en deux étages : blobs\ contient les
# octets sous des noms illisibles, snapshots\ contient 12 LIENS qui leur
# donnent leurs vrais noms (config.json, model.safetensors, tokenizer.json…).
# /XJ sautait ces 12 liens : l'autre poste recevait 4,3 Go de blobs et un
# snapshots vide, et le modèle ne se chargeait pas davantage. Sans /XJ,
# robocopy recrée les liens — vérifié : 0 octet chacun, rien n'est dupliqué.
# Ce sont les seuls liens du dossier ; il n'y a donc aucune boucle à craindre.
robocopy $racine $destination /MIR /XD @ecartes /NFL /R:2 /W:2

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
Write-Host ""
Write-Host "  C'est en place. Sur l'autre poste, ouvrez le dossier A-SCHOOL" -ForegroundColor Green
Write-Host "  et lancez :  .\Scripts\j_arrive.ps1" -ForegroundColor Green
Write-Host ""
