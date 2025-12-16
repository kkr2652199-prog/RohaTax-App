@echo off
REM ================================================================
REM RohaTax Server - Python 3.14 ONLY
REM NO ROLLBACK TO OLDER VERSIONS
REM ================================================================

chcp 65001 > nul

echo ================================
echo RohaTax Server Start (Python 3.14)
echo ================================

REM Disable base conda environment
set CONDA_AUTO_ACTIVATE_BASE=0

REM Change to batch file directory
cd /d "%~dp0"
echo Current Directory: %CD%

REM Clean up test files before starting
echo Cleaning up test files...
if exist "*test*.py" del /q *test*.py > nul 2>&1
if exist "*test*.bat" del /q *test*.bat > nul 2>&1
if exist "*test*.cmd" del /q *test*.cmd > nul 2>&1
if exist "test_*.py" del /q test_*.py > nul 2>&1
if exist "test_*.bat" del /q test_*.bat > nul 2>&1
if exist "test_*.cmd" del /q test_*.cmd > nul 2>&1

REM Force Python 3.14 Only - No Rollback
echo.
echo ================================
echo CRITICAL: Python 3.14 ONLY
echo ================================

REM Disable all other Python versions
set PYTHONPATH=
set CONDA_DEFAULT_ENV=

REM Force Python 3.14 path
set PYTHON_PATH=C:\ProgramData\anaconda3\envs\python314\python.exe

REM Verify Python 3.14 version
echo Checking Python version...
for /f "tokens=*" %%i in ('"%PYTHON_PATH%" --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python Version: %PYTHON_VERSION%

REM Exit if not Python 3.14
echo %PYTHON_VERSION% | findstr /C:"3.14" > nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ==============================================
    echo ERROR: Python 3.14 REQUIRED
    echo Detected: %PYTHON_VERSION%
    echo ==============================================
    echo This script ONLY works with Python 3.14
    echo Please install Python 3.14 to continue
    pause
    exit /b 1
)

echo Python 3.14 confirmed: %PYTHON_VERSION%

echo.
echo Installing required packages...
"%PYTHON_PATH%" -m pip install python-dotenv flask flask-sqlalchemy flask-login flask-wtf pandas openpyxl xlrd python-magic python-magic-bin cryptography bcrypt > nul 2>&1

echo.
echo Starting server...
echo Server Address: http://localhost:5001
echo Stop Server: Ctrl+C
echo ================================

REM Set Google Gemini API Key (무료 티어: 월 60회)
set GOOGLE_API_KEY=AIzaSyCZh8sPRFRYPTTr7rBvmzw2UK8KwLDnpeY
echo Google Gemini API Key configured

REM Start server
REM 환경 변수를 명시적으로 설정 (dotenv override를 위해)
set PORT=5001
echo Port configured: %PORT%
"%PYTHON_PATH%" app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Server start failed!
    pause
)