# ─────────────────────────────────────────────────────
# A-SCHOOL — Lancer l'environnement de dev complet
# Usage : .\run.ps1
# ─────────────────────────────────────────────────────

$root    = $PSScriptRoot
$pidFile = "$root\.run_pids"

# 1. Tuer les processus du lancement précédent via les PIDs sauvegardés
if (Test-Path $pidFile) {
    Get-Content $pidFile | ForEach-Object {
        $p = $_.Trim()
        if ($p -match '^\d+$') {
            Stop-Process -Id ([int]$p) -Force -ErrorAction SilentlyContinue
        }
    }
    Remove-Item $pidFile -Force
    Start-Sleep -Milliseconds 800
}

# 2. Sécurité : tuer tout ce qui tourne encore sur les ports
foreach ($port in @(8000, 5173)) {
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique |
        ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
}

Start-Sleep -Milliseconds 600

# 3. Synchroniser les dépendances Python (évite les crashs au démarrage)
Write-Host "  Sync dependances Python..." -ForegroundColor Yellow
& "$root\.venv\Scripts\pip.exe" install -r "$root\requirements.txt" --quiet --disable-pip-version-check
Write-Host ""

# 4. Synchroniser les logos et icônes vers frontend/public/Logo_aSchool/
Write-Host "  Synchronisation logos..." -ForegroundColor Yellow
$logoSrc = "$root\Logo_aSchool"
$logoDst = "$root\frontend\public\Logo_aSchool"
if (-not (Test-Path $logoDst)) { New-Item -ItemType Directory -Path $logoDst | Out-Null }
Get-ChildItem "$logoSrc\*.png","$logoSrc\*.svg","$logoSrc\*.webp" -ErrorAction SilentlyContinue |
    Copy-Item -Destination $logoDst -Force
Write-Host ""

# 5. Régénérer les activités depuis la matrice markdown
Write-Host "  Regeneration activities..." -ForegroundColor Yellow
& "$root\.venv\Scripts\python.exe" "$root\parse_markdown.py"
Write-Host ""

# 5. Démarrer le backend FastAPI et sauvegarder son PID
$backend = Start-Process powershell -PassThru -ArgumentList "-Command",
    "`$host.ui.RawUI.WindowTitle = 'A-SCHOOL Backend'; cd '$root'; Write-Host '=== BACKEND FastAPI ===' -ForegroundColor Cyan; .\.venv\Scripts\uvicorn backend.main:app --reload --port 8000; pause"

# 6. Démarrer le frontend React + Vite et sauvegarder son PID
$frontend = Start-Process powershell -PassThru -ArgumentList "-Command",
    "`$host.ui.RawUI.WindowTitle = 'A-SCHOOL Frontend'; cd '$root\frontend'; Write-Host '=== FRONTEND React ===' -ForegroundColor Green; npm run dev; pause"

# 7. Sauvegarder les PIDs pour le prochain lancement
@($backend.Id, $frontend.Id) | Set-Content $pidFile

Write-Host ""
Write-Host "  Backend  -> http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Frontend -> http://localhost:5173" -ForegroundColor Green
Write-Host ""
