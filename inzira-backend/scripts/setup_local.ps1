# First-time local setup for Inzira backend (Windows PowerShell)
# Run from repo root:  .\inzira-backend\scripts\setup_local.ps1

$Backend = Split-Path $PSScriptRoot -Parent
Set-Location $Backend

Write-Host "`n=== Inzira local setup ===`n" -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[OK] Created .env from .env.example — edit it with your keys." -ForegroundColor Green
} else {
    Write-Host "[OK] .env already exists" -ForegroundColor Green
}

Write-Host "`nNext steps (manual):`n"
Write-Host "1. PostgreSQL: create database 'inzira', set DATABASE_URL in .env"
Write-Host "2. Firebase Console: enable Email + Phone auth, download service account JSON"
Write-Host "   Set FIREBASE_SERVICE_ACCOUNT_PATH in .env"
Write-Host "3. Edit web/index.html — replace INZIRA_FIREBASE_CONFIG placeholders"
Write-Host "4. Groq: set GROQ_API_KEY in .env (for AI Assistant)"
Write-Host "5. Set INZIRA_MIFOTRA_STAFF_PASSWORD in .env"
Write-Host ""

if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "Installing Python deps..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt -q
    Write-Host "Running migrations..." -ForegroundColor Yellow
    python -m alembic -c alembic.ini upgrade head 2>&1
    Write-Host "`nRunning setup check..." -ForegroundColor Yellow
    python scripts/check_setup.py
} else {
    Write-Host "[!!] Python not found in PATH" -ForegroundColor Red
}

Write-Host "`nStart server:  cd inzira-backend; python main.py"
Write-Host "Open app:      http://localhost:8000/web#/login`n"
