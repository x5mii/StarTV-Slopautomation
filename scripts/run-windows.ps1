# StarNews — start after install. Usage: powershell -File scripts/run-windows.ps1
$InstallDir = if ($env:STARNNEWS_DIR) { $env:STARNNEWS_DIR } else { Join-Path $env:USERPROFILE "StarTV-Slopautomation" }
Set-Location $InstallDir
starnews web
