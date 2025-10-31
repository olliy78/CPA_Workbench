@echo off
REM Diese Datei ist für Windows und kann per Doppelklick ausgeführt werden.
REM Es wird geprüft, ob eine git bash vorhanden ist. Falls vorhanden, wird diese gestartet.

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
if exist "%~dp0tools\Git\bin\bash.exe" set "GIT_BASH=%~dp0tools\Git\bin\bash.exe"
if exist "%~dp0tools\PortableGit\bin\bash.exe" set "GIT_BASH=%~dp0tools\PortableGit\bin\bash.exe"
if exist "%~dp0..\Git\bin\bash.exe" set "GIT_BASH=%~dp0..\Git\bin\bash.exe"
if exist "%~dp0..\PortableGit\bin\bash.exe" set "GIT_BASH=%~dp0..\PortableGit\bin\bash.exe"

if "%GIT_BASH%"=="" (
    echo [FEHLER] Git Bash nicht gefunden!
    echo.
    echo Eventuell muss die Datei tools/win_tools.zip noch ausgepackt werden.
    echo Im Ordner tools muss es die Ordner make, python3, greaseweazle und PortableGit geben.
    echo falls die Tools woanders liegen, bitte den Pfad in dieser Datei anpassen.
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
