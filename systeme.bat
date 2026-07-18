@echo off
setlocal
cd /d "%~dp0"

rem ============================================================
rem  aSchool - LE SYSTEME (une seule commande, identique A ^<-^> B)
rem  1 = arriver sur un poste : Claude du disque + restaure la base + lance l'appli (run.ps1)
rem  2 = quitter un poste     : sauvegarde la base + renvoie Claude vers le disque
rem  .credentials.json (login Claude) n'est JAMAIS copie.
rem ------------------------------------------------------------
rem  VS Code : PAS gere par ce script -> Settings Sync (meme compte GitHub/Microsoft sur A et B).
rem    VS Code > roue crantee > "Backup and Sync Settings..." (ou Ctrl+Shift+P > Settings Sync: Turn On)
rem    Cocher : Settings, Keybindings, Extensions, Snippets, UI State. Meme compte sur A et B.
rem ------------------------------------------------------------
rem  PROCEDURE :
rem    0) 1re fois sur A   : systeme.bat -> 2   (remplit _ClaudePortable + backup\aschool.sql)
rem    1) Copier D:\A-SCHOOL sur le disque externe (une seule fois)
rem    2) Arriver (A ou B) : brancher le disque -> systeme.bat -> 1
rem    3) Travailler
rem    4) Partir           : systeme.bat -> 2
rem    5) Reprendre sur B  : brancher -> systeme.bat -> 1  (tu reprends a l'identique)
rem ============================================================

rem --- Claude Code : profil Windows <-> miroir dans le dossier (voyage avec la copie) ---
set "SRC=%USERPROFILE%\.claude"
set "SRCJSON=%USERPROFILE%\.claude.json"
set "MIR=%~dp0_ClaudePortable\.claude"
set "MIRJSON=%~dp0_ClaudePortable\.claude.json"

rem --- PostgreSQL natif (port 5433) ---
set "PGBIN=C:\Users\harketti\PostgreSQL\16\pgsql\bin"
set "PGDATA=C:\Users\harketti\PostgreSQL\16\data"
set "DUMP=%~dp0backup\aschool.sql"

rem  Connexion lue depuis .env (jamais ecrite en clair ici). On retire le dialecte +psycopg.
rem  DBADMIN = meme connexion mais base "postgres" (pour le DROP/CREATE pendant la restauration).
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /b "DATABASE_URL=" ".env"`) do set "DBURL=%%B"
set "DBURL=%DBURL:postgresql+psycopg=postgresql%"
set "DBADMIN=%DBURL:aschool_creche_miroir=postgres%"

echo ============================================================
echo   aSchool - LE SYSTEME
echo ============================================================
echo    1 = DEMARRER ici   (Claude + base + appli)
echo    2 = SAUVEGARDER    (base + Claude vers le disque)
echo.
set /p CHOIX=Ton choix (1 ou 2) :

if "%CHOIX%"=="1" goto START
if "%CHOIX%"=="2" goto SAVE
echo Choix invalide.
goto FIN

:START
echo.
echo --- 1/3  Claude Code depuis le disque ---
robocopy "%MIR%" "%SRC%" /MIR /XF .credentials.json /XD shell-snapshots ide session-env /R:1 /W:1 /NFL /NDL
if exist "%MIRJSON%" copy /Y "%MIRJSON%" "%SRCJSON%" >nul
echo.
echo --- 2/3  Base : demarrage PostgreSQL + restauration ---
"%PGBIN%\pg_ctl.exe" -D "%PGDATA%" -w start
if exist "%DUMP%" ( "%PGBIN%\psql.exe" -d "%DBADMIN%" -f "%DUMP%" ) else ( echo (aucune sauvegarde a restaurer^) )
echo.
echo --- Node.js : verification (requis par le frontend) ---
where npm >nul 2>nul
if errorlevel 1 (
    echo   Node.js absent -^> installation via winget...
    where winget >nul 2>nul
    if errorlevel 1 (
        echo   ERREUR : winget introuvable. Installe Node.js LTS a la main : https://nodejs.org/
    ) else (
        winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements --silent
    )
) else (
    echo   Node.js present.
)
echo.
echo --- 3/3  Lancement de l'appli (run.ps1) ---
rem  On recharge le PATH depuis le registre (Machine+User) : si Node vient d'etre
rem  installe ci-dessus, cette session cmd garde l'ancien PATH -> le frontend ne
rem  verrait pas npm. run.ps1 herite de ce PATH rafraichi, et ses fenetres aussi.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$m=[Environment]::GetEnvironmentVariable('Path','Machine');$u=[Environment]::GetEnvironmentVariable('Path','User');$env:Path=$m+';'+$u; & '%~dp0Scripts\run.ps1'"
goto FIN

:SAVE
echo.
echo --- 1/2  Base : sauvegarde vers le dossier ---
if not exist "%~dp0backup" mkdir "%~dp0backup"
"%PGBIN%\pg_ctl.exe" -D "%PGDATA%" -w start
"%PGBIN%\pg_dump.exe" --create --clean --if-exists -d "%DBURL%" -f "%DUMP%"
echo.
echo --- 2/2  Claude Code vers le disque ---
robocopy "%SRC%" "%MIR%" /MIR /XF .credentials.json /XD shell-snapshots ide session-env /R:1 /W:1 /NFL /NDL
if exist "%SRCJSON%" copy /Y "%SRCJSON%" "%MIRJSON%" >nul
echo.
echo OK - base + Claude sauvegardes sur le disque (sans .credentials.json).
goto FIN

:FIN
echo.
pause
