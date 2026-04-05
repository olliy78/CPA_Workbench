@echo off
chcp 65001 > nul
title CP/A Workbench

cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python nicht gefunden. Bitte Python 3 installieren.
    pause
    exit /b 1
)

python cpa_build.py %*
