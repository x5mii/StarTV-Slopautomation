# StarNews — install once, then run. Usage: powershell -ExecutionPolicy Bypass -File scripts/install-windows.ps1
$ErrorActionPreference = "Stop"

$InstallDir = if ($env:STARNNEWS_DIR) { $env:STARNNEWS_DIR } else { Join-Path $env:USERPROFILE "StarTV-Slopautomation" }
$Branch = "cursor/starnews-daily-pipeline"
$Repo = "https://github.com/x5mii/StarTV-Slopautomation.git"

Write-Host "=== StarNews Install (Windows) ===" -ForegroundColor Cyan
Write-Host ""

function Get-Py {
    if (Get-Command py -ErrorAction SilentlyContinue) { return "py" }
    if (Get-Command python -ErrorAction SilentlyContinue) { return "python" }
    return $null
}

$Py = Get-Py
if (-not $Py) {
    Write-Host "Python fehlt. Installiere es von https://www.python.org/downloads/"
    Write-Host "Wichtig: Haken setzen bei 'Add python.exe to PATH'"
    exit 1
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Git fehlt. Installiere es von https://git-scm.com/download/win"
    exit 1
}

if (Test-Path (Join-Path $InstallDir ".git")) {
    Write-Host "Update vorhandene Installation in $InstallDir"
    git -C $InstallDir fetch origin
    git -C $InstallDir checkout $Branch
    git -C $InstallDir pull origin $Branch
} else {
    Write-Host "Lade StarNews nach $InstallDir"
    git clone -b $Branch $Repo $InstallDir
}

Set-Location $InstallDir
& $Py -m pip install -e .

Write-Host ""
Write-Host "=== Fertig! Starte StarNews... ===" -ForegroundColor Green
Write-Host "Ordner: $InstallDir"
Write-Host ""
& $Py -m starnews web
