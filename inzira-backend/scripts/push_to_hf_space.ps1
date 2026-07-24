# Push inzira-backend to Hugging Face Space Liliane078/inzira
# Prereq: HF token with Write access → https://huggingface.co/settings/tokens

param(
    [string]$SpaceRepo = "https://huggingface.co/spaces/Liliane078/inzira",
    [string]$Token = $env:HF_TOKEN
)

$Backend = Split-Path $PSScriptRoot -Parent
$Work = Join-Path $env:TEMP "inzira-hf-space"

if (-not $Token) {
    Write-Host "Set your Hugging Face token first:" -ForegroundColor Yellow
    Write-Host '  $env:HF_TOKEN = "hf_..."' -ForegroundColor Cyan
    Write-Host "Create token: https://huggingface.co/settings/tokens (Write access)"
    exit 1
}

if (Test-Path $Work) { Remove-Item $Work -Recurse -Force }
New-Item -ItemType Directory -Path $Work | Out-Null

Write-Host "Cloning Space repo..."
git clone "https://Liliane078:$Token@huggingface.co/spaces/Liliane078/inzira" $Work 2>&1 | Out-Host

$exclude = @('.venv', '__pycache__', '.pytest_cache', 'models', 'deploy', '.env', 'inzira_local.db', 'inzira_prod.db')
Get-ChildItem $Backend -Force | Where-Object {
    $n = $_.Name
    $n -notin $exclude -and $n -ne 'deploy'
} | ForEach-Object {
    Copy-Item $_.FullName -Destination $Work -Recurse -Force
}

# Keep deploy/oracle only if small — skip large zip
if (Test-Path "$Backend\deploy\oracle") {
    New-Item -ItemType Directory -Path "$Work\deploy\oracle" -Force | Out-Null
    Copy-Item "$Backend\deploy\oracle\*" "$Work\deploy\oracle\" -Force
}

Set-Location $Work
git add -A
git status
git commit -m "Deploy Inzira web app + API (Docker)" 2>&1 | Out-Host
git push 2>&1 | Out-Host

Write-Host ""
Write-Host "Done. Open: https://huggingface.co/spaces/Liliane078/inzira" -ForegroundColor Green
Write-Host "Live app (after build): https://liliane078-inzira.hf.space" -ForegroundColor Green
Write-Host "Next: Space Settings -> Variables and secrets (see docs/DEPLOY_HUGGINGFACE.md)"
