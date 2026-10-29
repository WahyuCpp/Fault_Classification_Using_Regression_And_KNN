# ============================================================
# MONTREAL-VT  —  First-Time Setup Script
# Run once to create the virtual environment and install deps.
# After setup, use  .\run.ps1  to start the application.
# ============================================================

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Verify Python 3.12 is available
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Write-Error "Python Launcher (py.exe) not found. Install Python 3.12 from python.org."
    Exit 1
}

# 2. Create virtual environment with Python 3.12
Write-Host "Creating virtual environment (.venv)..." -ForegroundColor Cyan
py -3.12 -m venv "$projectDir\.venv"

# 3. Install dependencies
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Cyan
& "$projectDir\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "$projectDir\.venv\Scripts\pip.exe" install -r "$projectDir\requirements.txt"

# 4. Copy .env template if .env does not already exist
if (-not (Test-Path "$projectDir\.env")) {
    Copy-Item "$projectDir\.env.example" "$projectDir\.env"
    Write-Host ".env created from .env.example — edit it to set DB credentials." -ForegroundColor Yellow
}

# 5. Initialise the database (creates SQLite fallback automatically if MySQL is offline)
Write-Host "Initialising database..." -ForegroundColor Cyan
& "$projectDir\.venv\Scripts\python.exe" -m src.database.init_database

# 6. Done
Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "To start the application run:  .\run.ps1" -ForegroundColor Green
Write-Host ""
