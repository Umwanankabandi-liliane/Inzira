# Production start (Windows — local smoke test of prod path)
$Backend = Split-Path $PSScriptRoot -Parent
Set-Location $Backend
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

python scripts/download_deploy_assets.py
if ($env:DATABASE_URL) {
    python -m alembic -c alembic.ini upgrade head
}
$port = if ($env:PORT) { $env:PORT } else { 8000 }
Write-Host "Starting uvicorn on port $port"
python -m uvicorn main:app --host 0.0.0.0 --port $port
