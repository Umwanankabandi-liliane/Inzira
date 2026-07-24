# Package models + registry for cloud upload
$Backend = Split-Path $PSScriptRoot -Parent
Set-Location $Backend

$out = Join-Path $Backend "deploy\inzira_deploy_assets.zip"
if (Test-Path $out) { Remove-Item $out -Force }

$items = @()
if (Test-Path "models") { $items += "models" }
if (Test-Path "registry.db") { $items += "registry.db" }

if (-not $items) {
    Write-Host "[FAIL] Nothing to pack - need models/ and registry.db" -ForegroundColor Red
    exit 1
}

Compress-Archive -Path $items -DestinationPath $out -Force
$sizeMb = [math]::Round((Get-Item $out).Length / 1MB, 1)
Write-Host "[OK] Created $out - ${sizeMb} MB" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Upload inzira_deploy_assets.zip to Google Drive or Hugging Face"
Write-Host "  2. Get a direct HTTPS download link"
Write-Host "  3. Set INZIRA_ASSETS_BUNDLE_URL on your host (deploy/inzira_deploy_assets.zip upload)"
Write-Host "  4. Or copy models/ and registry.db into Docker build context"
