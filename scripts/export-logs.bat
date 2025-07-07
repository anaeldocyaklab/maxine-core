@echo off
echo Exporting Docker container logs...
powershell -ExecutionPolicy Bypass -File "%~dp0export-logs.ps1" %*
pause
