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
Write-Host "Zip and share: $Release"
Write-Host "Coworkers double-click Start-StarNews and choose their output folder."
