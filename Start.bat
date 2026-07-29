@echo off
title StarNews
cd /d "%~dp0"

echo Starte StarNews...
echo.

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -m starnews web
  goto :done
)

where python >nul 2>&1
if %ERRORLEVEL%==0 (
  python -m starnews web
  goto :done
)

echo Python nicht gefunden. Bitte Python installieren:
echo https://www.python.org/downloads/
echo Haken setzen: Add python.exe to PATH
pause
exit /b 1

:done
pause
