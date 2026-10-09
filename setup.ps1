# 1. Setup Environment
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in your PATH."
    Exit 1
}

Write-Host "Setting up Python environment..." -ForegroundColor Cyan
python -m venv .venv
& .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# 2. Extract credentials from .env to run SQL
if (Test-Path .env) {
    Get-Content .env | Foreach-Object {
        $name, $value = $_.split('=', 2)
        if ($name -and $value) { Set-Item -Path "env:$name" -Value $value }
    }
}

Write-Host "Running database migration..." -ForegroundColor Cyan
#Get-Content
Get-Content database.sql | mysql -h $env:DB_HOST -u $env:DB_USER -p"$env:DB_PASSWORD"

# 3. Run the Application
Write-Host "Launching app.py..." -ForegroundColor Green
python app.py
