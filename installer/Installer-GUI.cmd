@echo off
rem Installeur graphique du pont VRoid (Claude Code / DeepSeek Harness).
rem La version ligne de commande reste disponible : Installer.cmd
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -Sta -File "%~dp0Installer-GUI.ps1" %*
if errorlevel 1 pause
