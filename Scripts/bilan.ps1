# ==============================================================================
# bilan.ps1 — Bilan des commits a faire, puis (sur demande) les commits eux-memes.
#
# Option A : le script ne "devine" pas le decoupage lui-meme — il DELEGUE l'analyse
# a Claude Code en mode non-interactif (claude -p). Claude lit le working tree REEL,
# regroupe les changements par theme, ecrit les messages, et — seulement si tu le
# demandes — execute les commits, un lot a la fois.
#
# --- LES DEUX MODES ---------------------------------------------------------
# PLAN (par defaut) : Claude LIT seulement et PROPOSE un plan de commits (quels
#   fichiers, quel message). Outils git restreints a la LECTURE : il lui est
#   physiquement impossible d'ecrire dans git. Sert a "faire le point".
# EXECUTION (-Go)   : Claude EXECUTE le plan — 'git add <chemins precis>' puis
#   'git commit', un commit a la fois. Outils limites a add + commit (pas de push,
#   pas de reset/clean). Le push n'est autorise QUE si -Push est passe.
#
# --- COMPORTEMENT ATTENDU DE CLAUDE -----------------------------------------
# Il regroupe par THEME (un commit = un sujet), reprend le style de messages du
# depot (type(scope): sujet, en francais), et met DE COTE sous "A verifier / ne
# pas committer" tout ce qu'il ne peut pas rattacher avec certitude a un chantier.
#
# --- SECURITE ---------------------------------------------------------------
# En headless, personne ne rattrape a la main : les garde-fous sont (1) la liste
# blanche d'outils git par mode, (2) le prompt. Interdits absolus : 'git add -A',
# committer un secret (.env, cles, tokens...), commit vide. Voir la consigne plus bas.
#
# --- MULTI-SESSIONS ---------------------------------------------------------
# Le depot est PARTAGE par 3 sessions de travail : les chantiers sont MELANGES
# dans le working tree. C'est tout l'interet de deleguer a Claude : il trie par
# SENS, ce qu'un script de chemins ne saurait pas faire.
#
# --- USAGE (depuis D:\A-SCHOOL\Scripts) -------------------------------------
#   .\bilan.ps1            BILAN seulement. Propose le plan. N'ECRIT RIEN dans git.
#   .\bilan.ps1 -Go        EXECUTE les commits thematiques. Ne pousse pas.
#   .\bilan.ps1 -Go -Push  Idem, puis 'git push' a la fin. (-Push seul = sans effet.)
# ==============================================================================
param(
  [switch]$Go,
  [switch]$Push
)
$ErrorActionPreference = "Stop"

# Le depot = le dossier PARENT de ce script (le script vit dans Scripts/).
$Repo = Split-Path -Parent $PSScriptRoot

# --- 0. Garde-fous d'entree ---
# -Push sans -Go n'a aucun effet (le push est dans la branche EXECUTION) : on previent.
if ($Push -and -not $Go) {
  Write-Host "ARRET : -Push n'a de sens qu'avec -Go. Utilise '.\bilan.ps1 -Go -Push'." -ForegroundColor Red
  exit 1
}
# Sans depot git valide, toute la suite est fausse (un 'git status' vide passerait
# pour "rien a committer"). On verifie AVANT de faire quoi que ce soit.
if (-not (Test-Path (Join-Path $Repo ".git"))) {
  Write-Host "ARRET : '$Repo' n'est pas un depot git (.git introuvable)." -ForegroundColor Red
  exit 1
}

# --- 1. Retrouver la CLI Claude Code (sans figer le numero de version) ---
$Claude = (Get-Command claude -ErrorAction SilentlyContinue).Source
if (-not $Claude) {
  $cand = Get-ChildItem "$env:APPDATA\Claude\claude-code\*\claude.exe" -ErrorAction SilentlyContinue |
          Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($cand) { $Claude = $cand.FullName }
}
if (-not $Claude) {
  Write-Host "ARRET : CLI 'claude' introuvable (ni dans le PATH, ni sous %APPDATA%\Claude\claude-code)." -ForegroundColor Red
  exit 1
}

# --- 2. Etat brut du depot, tout de suite (avant meme d'appeler Claude) ---
Write-Host "`n=== Etat du depot : $Repo ===" -ForegroundColor Cyan
git -C $Repo status --short --branch

# On lit le porcelain ET on verifie que git a REUSSI : sinon une sortie vide
# (git en erreur) serait prise a tort pour "rien a committer".
$porcelain = git -C $Repo status --porcelain
if ($LASTEXITCODE -ne 0) {
  Write-Host "`nARRET : 'git status' a echoue (code $LASTEXITCODE)." -ForegroundColor Red
  exit 1
}
if (-not $porcelain) {
  Write-Host "`nRien a committer : le working tree est propre." -ForegroundColor Green
  exit 0
}

# --- 3. Construire la consigne pour Claude selon le mode ---
$base = @"
Tu travailles dans le depot git $Repo, PARTAGE par 3 sessions de travail differentes :
les changements de plusieurs chantiers sont donc MELANGES dans le working tree.

Marche a suivre :
1. Lis l'etat REEL : 'git status', 'git diff', 'git diff --staged'. Regarde aussi
   'git log --oneline -8' pour reprendre EXACTEMENT le style des messages du depot
   (type(scope): sujet, en francais).
2. Regroupe les changements en commits THEMATIQUES coherents (un commit = un sujet).
3. Pour CHAQUE commit : donne la liste EXACTE des fichiers a stager + le message.
   Exemple attendu (style du depot) :
     Commit 1 — message : "feat(outils): script bilan des commits delegue a Claude"
       git add Scripts/bilan.ps1
     Commit 2 — message : "feat(outils): vue detail par table dans la carte de la base"
       git add outils_bdd/carte_base/carte.py
4. Si un changement ressemble a un bout INACHEVE que tu ne peux PAS rattacher avec
   certitude a un chantier, ne le mets dans AUCUN commit : liste-le a part sous
   "A verifier / ne pas committer".

Regles absolues (tu commites sans me redemander, donc ces regles ne se discutent pas) :
- Jamais 'git add -A' ni 'git add .' : tu stages des chemins PRECIS, sujet par sujet.
- Jamais un commit fourre-tout : un commit = un seul sujet coherent.
- SECRETS : ne stage et ne committe JAMAIS un fichier sensible (.env, .env.*, *.key,
  *.pem, tokens, mots de passe, identifiants). Respecte le .gitignore. Si un fichier
  sensible NON ignore apparait dans le working tree, ne le stage PAS et signale-le
  sous "A verifier / ne pas committer". Jamais un secret affiche en clair.
- Jamais un commit vide, jamais '--allow-empty'.
- Si l'arbre est propre, ne fais rien.
"@

if ($Go) {
  $consignePush = if ($Push) {
    "Une fois TOUS les commits faits, execute 'git push'."
  } else {
    "Ne pousse PAS ('git push' interdit) : je pousserai moi-meme quand je le deciderai."
  }
  $prompt = $base + @"

MODE EXECUTION : execute le plan maintenant. Pour chaque commit, 'git add <chemins precis>'
PUIS 'git commit -m "..."', UN commit a la fois. Ne touche pas aux fichiers "a verifier".
$consignePush
A la fin, affiche un recap : 'git log --oneline' des commits crees + 'git status --short'.
"@
} else {
  $prompt = $base + @"

MODE PLAN : tu n'ECRIS RIEN. Aucun 'git add', 'git commit' ni 'git push'. Affiche
seulement, clairement, le plan de commits propose (et la section "a verifier").
"@
}

# --- 4. Liste blanche d'outils : le vrai garde-fou (headless = pas de validation main) ---
#   Lecture git : toujours autorisee (les deux modes en ont besoin).
#   add + commit : seulement en EXECUTION (-Go).
#   push         : seulement si -Push.
#   Tout le reste (reset, clean, rm, checkout...) reste NON autorise = impossible.
$tools = @("Bash(git status*)", "Bash(git diff*)", "Bash(git log*)", "Bash(git show*)",
           "Bash(git branch*)", "Bash(git remote*)", "Read", "Grep", "Glob")
if ($Go) {
  $tools += @("Bash(git add *)", "Bash(git commit *)")
  if ($Push) { $tools += "Bash(git push*)" }
}

# --- 5. Appel de Claude en non-interactif ---
#     Le prompt passe par STDIN (evite que la liste variadique --allowedTools
#     n'avale le texte du prompt). --allowedTools est donc en DERNIER.
Write-Host "`n=== Claude analyse... (mode $(if ($Go) {'EXECUTION'} else {'PLAN'})) ===`n" -ForegroundColor Cyan
$prompt | & $Claude -p --model opus --add-dir $Repo --allowedTools @tools

# On rapporte honnetement le sort de l'appel (Claude peut echouer : reseau, quota...).
if ($LASTEXITCODE -ne 0) {
  Write-Host "`nATTENTION : Claude s'est termine avec le code $LASTEXITCODE (l'analyse/les commits sont peut-etre incomplets)." -ForegroundColor Red
  exit $LASTEXITCODE
}
Write-Host "`n=== Termine (mode $(if ($Go) {'EXECUTION'} else {'PLAN'})). ===" -ForegroundColor Green
