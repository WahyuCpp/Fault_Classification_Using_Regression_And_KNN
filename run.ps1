# ============================================================
# MONTREAL-VT  —  Run Script
# Usage: .\run.ps1
# ============================================================

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $projectDir ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Error "Virtual environment not found. Run .\setup.ps1 first to create it."
    Exit 1
}

Write-Host ""
Write-Host "  MONTREAL-VT Motor Condition Monitoring" -ForegroundColor Cyan
Write-Host "  =======================================" -ForegroundColor Cyan
Write-Host "  URL : http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "  Stop: Ctrl+C" -ForegroundColor Yellow
Write-Host ""

& $venvPython app.py

