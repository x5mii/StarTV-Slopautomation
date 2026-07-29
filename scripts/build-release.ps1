# Build a folder you can zip and send to teammates (Windows).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Test-Path "starnews\team_defaults.yaml")) {
    Write-Host "Optional: starnews\team_defaults.yaml not found."
    Write-Host "Coworkers will import team-secrets.env in the setup screen."
}

py -m pip install pyinstaller 2>$null
py -m PyInstaller starnews.spec --noconfirm

$Release = Join-Path $Root "release\StarNews-Windows"
if (Test-Path $Release) { Remove-Item -Recurse -Force $Release }
New-Item -ItemType Directory -Path $Release | Out-Null

Copy-Item -Recurse (Join-Path $Root "dist\starnews\*") $Release
Copy-Item (Join-Path $Root "config.yaml") $Release
Copy-Item (Join-Path $Root "config.local.example.yaml") $Release
Copy-Item (Join-Path $Root "team-secrets.env.example") $Release
Copy-Item (Join-Path $Root "scripts\Start-StarNews.bat") $Release

$Zip = Join-Path $Root "release\StarNews-Windows.zip"
if (Test-Path $Zip) { Remove-Item -Force $Zip }
Compress-Archive -Path $Release -DestinationPath $Zip

Write-Host ""
Write-Host "Built: $Release"
Write-Host "Zip:   $Zip"
Write-Host "Share the zip + team-secrets.env with coworkers."
