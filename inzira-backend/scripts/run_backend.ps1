# Start the Inzira FastAPI backend (listens on all interfaces for phone + emulator)
Set-Location $PSScriptRoot

if (-not (Test-Path ".env")) {
    Write-Host 'Creating .env from .env.example - add your GROQ_API_KEY for the AI assistant.'
    Copy-Item ".env.example" ".env"
}

Write-Host 'Starting Inzira API on http://0.0.0.0:8000'
Write-Host 'Web app:          http://localhost:8000'
Write-Host 'Emulator app URL: http://10.0.2.2:8000'
Write-Host 'Physical phone:   http://YOUR_PC_WIFI_IP:8000 (set in app Settings, API server)'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
python main.py
