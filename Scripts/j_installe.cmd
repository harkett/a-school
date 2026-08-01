@echo off
REM ============================================================
REM  j_installe.cmd -- le fichier a double-cliquer.
REM
REM  Windows refuse par defaut de lancer un script PowerShell
REM  (politique Restricted). Ce lanceur leve la restriction pour
REM  cette execution seulement, et garde la fenetre ouverte a la
REM  fin pour que le dernier message reste lisible.
REM
REM  A copier sur le Bureau AVEC j_installe.ps1, cote a cote.
REM  Fichier volontairement en ASCII pur : cmd.exe ne lit pas
REM  l'UTF-8 et refuserait le script des la premiere ligne.
REM ============================================================
setlocal
if not exist "%~dp0j_installe.ps1" (
    echo.
    echo   Le fichier j_installe.ps1 n'est pas a cote de ce lanceur.
    echo   Copiez les deux ensemble, puis relancez.
    echo.
    pause
    exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0j_installe.ps1"
echo.
pause
