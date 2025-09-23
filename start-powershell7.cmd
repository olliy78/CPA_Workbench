@echo off
REM CP/A Build Environment für PowerShell 7
REM Setzt PATH-Variablen und startet PowerShell 7

title CP/A Build Environment - PowerShell 7

echo =============================================
echo   CP/A Build Environment - PowerShell 7
echo =============================================
echo.

REM Zum Skript-Verzeichnis wechseln
cd /d "%~dp0"
echo [INFO] Arbeitsverzeichnis: %CD%

REM PowerShell 7 finden
set "PWSH7="
if exist "C:\Program Files\PowerShell\7\pwsh.exe" set "PWSH7=C:\Program Files\PowerShell\7\pwsh.exe"
if exist "C:\Program Files (x86)\PowerShell\7\pwsh.exe" set "PWSH7=C:\Program Files (x86)\PowerShell\7\pwsh.exe"
if exist "%LOCALAPPDATA%\Microsoft\powershell\pwsh.exe" set "PWSH7=%LOCALAPPDATA%\Microsoft\powershell\pwsh.exe"

REM Fallback: pwsh im PATH suchen
if "%PWSH7%"=="" (
    pwsh --version >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set "PWSH7=pwsh"
        echo [INFO] PowerShell 7 gefunden im PATH
    ) else (
        echo [FEHLER] PowerShell 7 nicht gefunden!
        echo.
        echo Bitte installieren Sie PowerShell 7:
        echo https://github.com/PowerShell/PowerShell/releases
        echo.
        echo Oder verwenden Sie die PowerShell 5.1-Scripts
        pause
        exit /b 1
    )
) else (
    echo [INFO] PowerShell 7 gefunden: %PWSH7%
)

echo [INFO] Setze PATH-Variablen...

REM PATH-Variablen erweitern - OHNE tools\gnu um Wildcard-Probleme zu vermeiden
REM Nur make.exe wird separat hinzugefügt
set "NEW_PATH=%CD%\tools\greaseweazle;%CD%\tools\python3\Scripts;%CD%\tools\python3;%CD%\tools;%PATH%"

REM Make separat prüfen und hinzufügen
if exist "%CD%\tools\make.exe" (
    set "NEW_PATH=%CD%\tools;%NEW_PATH%"
    echo   [+] make.exe aus tools\ hinzugefuegt
) else if exist "%CD%\tools\gnu\make.exe" (
    echo   [WARNUNG] GNU-Tools können in PowerShell Probleme verursachen
    echo   [INFO] Verwenden Sie Git Bash für make-Befehle oder fix-gnu-tools.cmd
    set "NEW_PATH=%CD%\tools\gnu;%NEW_PATH%"
    echo   [+] make.exe aus tools\gnu\ hinzugefuegt ^(problematisch^)
)

echo   [+] Greaseweazle hinzugefuegt
echo   [+] Python3 und Scripts hinzugefuegt
echo   [+] CP/A Tools hinzugefuegt

echo.
echo =============================================
echo   Starte PowerShell 7 mit CP/A-Umgebung...
echo =============================================
echo.

REM PowerShell 7 Startup-Script erstellen
echo # CP/A Build Environment für PowerShell 7 > temp_ps7_startup.ps1
echo $Host.UI.RawUI.WindowTitle = "CP/A Build Environment - PowerShell 7" >> temp_ps7_startup.ps1
echo $env:PATH = "%NEW_PATH%" >> temp_ps7_startup.ps1
echo Write-Host "=============================================" -ForegroundColor Cyan >> temp_ps7_startup.ps1
echo Write-Host "  CP/A Build Environment (PowerShell 7)" -ForegroundColor Yellow >> temp_ps7_startup.ps1
echo Write-Host "=============================================" -ForegroundColor Cyan >> temp_ps7_startup.ps1
echo Write-Host "" >> temp_ps7_startup.ps1
echo Write-Host "[INFO] Arbeitsverzeichnis: $(Get-Location)" -ForegroundColor Green >> temp_ps7_startup.ps1
echo Write-Host "[INFO] PowerShell Version: $($PSVersionTable.PSVersion)" -ForegroundColor Green >> temp_ps7_startup.ps1
echo Write-Host "" >> temp_ps7_startup.ps1
echo Write-Host "[INFO] Teste verfügbare Tools..." -ForegroundColor Yellow >> temp_ps7_startup.ps1
echo try { >> temp_ps7_startup.ps1
echo   $makeVersion = ^& make --version 2^>$null ^| Select-Object -First 1 >> temp_ps7_startup.ps1
echo   if ($makeVersion) { >> temp_ps7_startup.ps1
echo     Write-Host "  [✓] make: $makeVersion" -ForegroundColor Green >> temp_ps7_startup.ps1
echo   } else { >> temp_ps7_startup.ps1
echo     Write-Host "  [✗] make: Nicht gefunden" -ForegroundColor Red >> temp_ps7_startup.ps1
echo   } >> temp_ps7_startup.ps1
echo } catch { >> temp_ps7_startup.ps1
echo   Write-Host "  [✗] make: Nicht verfügbar" -ForegroundColor Red >> temp_ps7_startup.ps1
echo } >> temp_ps7_startup.ps1
echo try { >> temp_ps7_startup.ps1
echo   $pythonVersion = ^& python --version 2^>$null >> temp_ps7_startup.ps1
echo   if ($pythonVersion) { >> temp_ps7_startup.ps1
echo     Write-Host "  [✓] python: $pythonVersion" -ForegroundColor Green >> temp_ps7_startup.ps1
echo   } else { >> temp_ps7_startup.ps1
echo     Write-Host "  [✗] python: Nicht gefunden" -ForegroundColor Red >> temp_ps7_startup.ps1
echo   } >> temp_ps7_startup.ps1
echo } catch { >> temp_ps7_startup.ps1
echo   Write-Host "  [✗] python: Nicht verfügbar" -ForegroundColor Red >> temp_ps7_startup.ps1
echo } >> temp_ps7_startup.ps1
echo Write-Host "" >> temp_ps7_startup.ps1
echo Write-Host "=============================================" -ForegroundColor Cyan >> temp_ps7_startup.ps1
echo Write-Host "  Verfügbare Befehle:" -ForegroundColor Yellow >> temp_ps7_startup.ps1
echo Write-Host "=============================================" -ForegroundColor Cyan >> temp_ps7_startup.ps1
echo Write-Host "" >> temp_ps7_startup.ps1
echo Write-Host "Build-Befehle:" -ForegroundColor Green >> temp_ps7_startup.ps1
echo Write-Host "  make menuconfig        # Konfigurationsmenü" -ForegroundColor Blue >> temp_ps7_startup.ps1
echo Write-Host "  make config os         # Betriebssystem bauen" -ForegroundColor Blue >> temp_ps7_startup.ps1
echo Write-Host "  make config diskimage  # Diskettenimage erstellen" -ForegroundColor Blue >> temp_ps7_startup.ps1
echo Write-Host "" >> temp_ps7_startup.ps1
echo Write-Host "WARNUNG: 'make clean' kann in PowerShell einfrieren!" -ForegroundColor Red >> temp_ps7_startup.ps1
echo Write-Host "Verwenden Sie stattdessen:" -ForegroundColor Yellow >> temp_ps7_startup.ps1
echo Write-Host "  .\clean.ps1            # PowerShell Clean (sicher)" -ForegroundColor Blue >> temp_ps7_startup.ps1
echo Write-Host "  .\start-cpa-environment.cmd  # Git Bash (empfohlen für make)" -ForegroundColor Blue >> temp_ps7_startup.ps1
echo Write-Host "" >> temp_ps7_startup.ps1
echo Write-Host "PowerShell-Scripts:" -ForegroundColor Green >> temp_ps7_startup.ps1
echo Write-Host "  .\menuconfig.ps1       # Konfigurationsmenü (PS)" -ForegroundColor Blue >> temp_ps7_startup.ps1
echo Write-Host "  .\build-os.ps1         # OS bauen (PS)" -ForegroundColor Blue >> temp_ps7_startup.ps1
echo Write-Host "  .\clean.ps1            # Aufräumen (PS)" -ForegroundColor Blue >> temp_ps7_startup.ps1
echo Write-Host "" >> temp_ps7_startup.ps1
echo Write-Host "Verwenden Sie 'exit' um die Umgebung zu verlassen." -ForegroundColor Gray >> temp_ps7_startup.ps1
echo Write-Host "" >> temp_ps7_startup.ps1

REM PowerShell 7 mit Startup-Script starten
"%PWSH7%" -NoExit -ExecutionPolicy Bypass -File temp_ps7_startup.ps1

REM Aufräumen
del temp_ps7_startup.ps1 2>nul

echo.
echo [INFO] PowerShell 7-Session beendet
pause