@echo off
cd /d "%~dp0"

if exist "starnews.exe" (
  start "" "starnews.exe" web
) else if exist "py.exe" (
  start "" py -m starnews web
) else (
  where py >nul 2>&1
  if %ERRORLEVEL%==0 (
    start "" py -m starnews web
  ) else (
    start "" python -m starnews web
  )
)

timeout /t 2 /nobreak >nul
start http://127.0.0.1:8765
