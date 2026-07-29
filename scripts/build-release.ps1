# Build a folder you can zip and send to teammates (Windows).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

py -m pip install pyinstaller 2>$null
py -m PyInstaller starnews.spec --noconfirm

$Release = Join-Path $Root "release\StarNews-Windows"
if (Test-Path $Release) { Remove-Item -Recurse -Force $Release }
New-Item -ItemType Directory -Path $Release | Out-Null

Copy-Item -Recurse (Join-Path $Root "dist\starnews\*") $Release
Copy-Item (Join-Path $Root "config.yaml") $Release
Copy-Item (Join-Path $Root "config.local.example.yaml") $Release
Copy-Item (Join-Path $Root "scripts\Start-StarNews.bat") $Release

Write-Host ""
Write-Host "Built: $Release"
Write-Host "1. Copy config.local.example.yaml -> config.local.yaml and fill in team keys"
Write-Host "2. Zip the StarNews-Windows folder and send it privately"
Write-Host "3. Teammate double-clicks Start-StarNews.bat"
