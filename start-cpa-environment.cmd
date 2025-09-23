@echo off
REM CP/A Build Environment Launcher - Startet Git Bash mit CP/A-Umgebung

chcp 65001

title CP/A Build Environment Launcher

echo =============================================
echo   CP/A Build Environment Launcher
echo =============================================
echo.

REM Zum Skript-Verzeichnis wechseln
cd /d "%~dp0"

REM Git Bash finden
set "GIT_BASH="
if exist "C:\Program Files\Git\bin\bash.exe" set "GIT_BASH=C:\Program Files\Git\bin\bash.exe"
if exist "C:\Program Files (x86)\Git\bin\bash.exe" set "GIT_BASH=C:\Program Files (x86)\Git\bin\bash.exe"
if exist "C:\tools\Git\bin\bash.exe" set "GIT_BASH=C:\tools\Git\bin\bash.exe"
if exist "C:\tools\PortableGit\bin\bash.exe" set "GIT_BASH=C:\tools\PortableGit\bin\bash.exe"

if "%GIT_BASH%"=="" (
    echo [FEHLER] Git Bash nicht gefunden!
    echo.
    echo Bitte installieren Sie Git oder geben Sie den Pfad an.
    echo Git Download: https://git-scm.com/
    pause
    exit /b 1
)

echo [INFO] Git Bash gefunden: %GIT_BASH%
echo [INFO] Starte CP/A Build Environment...
echo.

REM Setup-Script ausführen
"%GIT_BASH%" --login -i "./setup-environment.sh"

echo.
echo [INFO] CP/A Build Environment beendet
pause