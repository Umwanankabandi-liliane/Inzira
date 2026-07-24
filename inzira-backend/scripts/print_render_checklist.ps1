# Prints Render env vars to set after Blueprint deploy (reads local .env — never commit output)
$envFile = Join-Path $PSScriptRoot "..\.env"
if (-not (Test-Path $envFile)) {
    Write-Host "Missing inzira-backend/.env"
    exit 1
}

$vars = @{}
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
    $i = $_.IndexOf('=')
  $k = $_.Substring(0, $i).Trim()
  $v = $_.Substring($i + 1).Trim()
  $vars[$k] = $v
}

$serviceUrl = Read-Host "Your Render URL (e.g. https://inzira.onrender.com)"
if (-not $serviceUrl) { $serviceUrl = "https://inzira.onrender.com" }

Write-Host "`n=== Paste these in Render → inzira → Environment ===`n"
Write-Host "CORS_ORIGINS=$serviceUrl"
@(
  "GROQ_API_KEY",
  "INZIRA_MIFOTRA_STAFF_PASSWORD",
  "INZIRA_VAPID_PUBLIC_KEY",
  "INZIRA_VAPID_PRIVATE_KEY",
  "INZIRA_ASSETS_BUNDLE_URL"
) | ForEach-Object {
    if ($vars.ContainsKey($_)) {
        Write-Host "$_=$($vars[$_])"
    } else {
        Write-Host "$_=  (missing from .env)"
    }
}
Write-Host "`nAfter deploy: add $([uri]$serviceUrl).Host to Firebase Authorized domains`n"
