@echo off
cd /d "%~dp0"

if exist "starnews.exe" (
  start "" "starnews.exe" web
) else (
  starnews web
)

timeout /t 2 /nobreak >nul
start http://127.0.0.1:8765
