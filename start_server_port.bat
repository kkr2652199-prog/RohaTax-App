@echo off
REM ================================================================
REM RohaTax Server Starter (Custom Port)
REM Usage: start_server_port.bat [PORT]
REM Default PORT: 5000
REM ================================================================

chcp 65001 > nul

setlocal ENABLEDELAYEDEXPANSION

REM Determine script directory
cd /d "%~dp0"

echo ================================
echo RohaTax Server Start (Custom Port)
echo ================================

REM Read port argument or default
set PORT=%1
if "%PORT%"=="" set PORT=5000

echo Using PORT: %PORT%

REM Prefer Python 3.14 via py launcher, fallback to PATH python
set PY_CMD=python
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3.14 -V >nul 2>&1
    if %ERRORLEVEL% EQU 0 set PY_CMD=py -3.14
)
echo Using Python: %PY_CMD%
%PY_CMD% -V

REM Open info
echo Open: http://localhost:%PORT%

REM Start server with env PORT (Flask reads settings.PORT via env or config)
set PORT=%PORT%
start "RohaTax Server" cmd /c %PY_CMD% app.py

REM Optionally open browser after short delay
ping -n 2 127.0.0.1 > nul
start "" http://localhost:%PORT%

endlocal

