@echo off
rem Lance l'installation (ou la mise a jour) du pont MCP pour VRoid Studio.
rem Options : Installer.cmd -GameDir "D:\...\VRoid Studio"   |   Installer.cmd -Uninstall
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
echo.
pause
