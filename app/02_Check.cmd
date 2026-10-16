@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Check-Lab.ps1"
set "LAB_EXIT=%ERRORLEVEL%"
echo.
pause
exit /b %LAB_EXIT%
