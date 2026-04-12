@echo off
setlocal

rem Inno Setup suchen – Klammern in %ProgramFiles(x86)% vermeiden,
rem indem literal-Pfade statt Umgebungsvariablen verwendet werden.
set "ISCC="
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
if not defined ISCC set "PFIS=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%PFIS%" set "ISCC=%PFIS%"

if not defined ISCC (
    echo [FEHLER] Inno Setup ISCC.exe nicht gefunden.
    echo         Bitte Inno Setup 6 installieren:
    echo           winget install --id JRSoftware.InnoSetup -e
    echo         oder: https://jrsoftware.org/isdl.php
    exit /b 1
)

cd /d "%~dp0"
set "OUTDIR=%CD%\Output"
set "OUTBASE=CPA_Workbench_Setup"

if exist "%OUTDIR%\%OUTBASE%.exe" (
    del /f /q "%OUTDIR%\%OUTBASE%.exe" >nul 2>&1
)

if exist "%OUTDIR%\%OUTBASE%.exe" (
    for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "OUTBASE=CPA_Workbench_Setup_%%I"
    echo [HINWEIS] Vorhandene Setup-Datei ist gesperrt. Verwende neuen Namen: %OUTBASE%.exe
)

"%ISCC%" /F"%OUTBASE%" "CPA_Workbench_Windows.iss"
if errorlevel 1 exit /b 1

echo [OK] Installer erstellt: installer\Output\%OUTBASE%.exe
