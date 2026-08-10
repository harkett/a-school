# =============================================================================
# aSchool — POSE LA TACHE PLANIFIEE « aSchool-Sauvegarde »
#
# A LANCER UNE FOIS PAR POSTE. Elle appelle Scripts\sauvegarde.ps1 tous les
# jours a 12h30. Si la machine etait eteinte a cette heure-la, la tache part
# des le demarrage suivant (-StartWhenAvailable) : une sauvegarde qui saute un
# jour parce que le PC dormait ne vaut rien.
#
# SANS ELEVATION. La tache appartient a l'utilisateur courant et ne tourne que
# quand il est connecte — c'est suffisant, Docker Desktop ne tourne pas non
# plus sans session ouverte.
#
# POUR LA RETIRER :  Unregister-ScheduledTask -TaskName 'aSchool-Sauvegarde'
# POUR LA VOIR    :  Get-ScheduledTaskInfo -TaskName 'aSchool-Sauvegarde'
# =============================================================================

$ErrorActionPreference = 'Stop'

$nom     = 'aSchool-Sauvegarde'
$script  = Join-Path $PSScriptRoot 'sauvegarde.ps1'
if (-not (Test-Path $script)) { throw "Introuvable : $script" }

$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
          -Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "{0}"' -f $script)

$declencheur = New-ScheduledTaskTrigger -Daily -At '12:30'

# ExecutionTimeLimit : six bases a dumper prennent une trentaine de secondes ;
# une heure est large, et evite qu'une tache bloquee reste en vie indefiniment.
$reglages = New-ScheduledTaskSettingsSet -StartWhenAvailable `
            -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries `
            -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
            -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $nom -Action $action -Trigger $declencheur `
    -Settings $reglages -Description 'Sauvegarde quotidienne des bases aSchool (dev + demos) dans db_backup, rotation 14 jours.' `
    -Force | Out-Null

Write-Host "Tache « $nom » posee : tous les jours a 12h30." -ForegroundColor Green
Get-ScheduledTaskInfo -TaskName $nom | Format-List TaskName, NextRunTime, LastRunTime, LastTaskResult
