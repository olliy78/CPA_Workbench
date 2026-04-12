@echo off
chcp 65001 > nul
title CP/A Workbench

cd /d "%~dp0"

set "PYTHON_EXE="
set "PYTHONW_EXE="

where python >nul 2>&1
if not errorlevel 1 (
    python -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=python"
        where pythonw >nul 2>&1
        if not errorlevel 1 (
            set "PYTHONW_EXE=pythonw"
        )
    )
)

if not defined PYTHON_EXE (
    for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do (
        if exist "%%~fD\python.exe" (
            set "PYTHON_EXE=%%~fD\python.exe"
            if exist "%%~fD\pythonw.exe" (
                set "PYTHONW_EXE=%%~fD\pythonw.exe"
            )
        )
    )
)

if not defined PYTHON_EXE (
    echo [FEHLER] Python nicht gefunden. Bitte Python 3.8+ installieren.
    echo         Tipp: winget install --id Python.Python.3.12 -e --scope user
    pause
    exit /b 1
)

if defined PYTHONW_EXE (
    start "" /b "%PYTHONW_EXE%" cpa_workbench.py %*
    exit /b 0
)

"%PYTHON_EXE%" cpa_workbench.py %*
