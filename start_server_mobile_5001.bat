@echo off
REM ================================================================
REM [homepage1] 스마트폰 접속용 서버 시작
REM 포트: 5001 (homepage1 기본 포트)
REM 외부 접근 가능 (0.0.0.0)
REM ================================================================

chcp 65001 > nul

echo ================================================================
echo [homepage1] 스마트폰 접속용 서버 시작
echo 포트: 5001
echo ================================================================
echo.

REM 현재 디렉토리로 이동
cd /d "%~dp0"
echo 현재 디렉토리: %CD%

REM Python 경로 확인
set PYTHON_PATH=python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python을 찾을 수 없습니다. Anaconda Python 경로를 사용합니다.
    set PYTHON_PATH=C:\ProgramData\anaconda3\python.exe
)

REM 필수 패키지 확인 및 설치
echo.
echo [확인] 필수 패키지 확인 중...
"%PYTHON_PATH%" -c "import apscheduler" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [설치] APScheduler 설치 중...
    "%PYTHON_PATH%" -m pip install apscheduler --quiet
)

"%PYTHON_PATH%" -c "import flask_limiter" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [설치] Flask-Limiter 설치 중...
    "%PYTHON_PATH%" -m pip install flask-limiter --quiet
)

"%PYTHON_PATH%" -c "import flask_mail" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [설치] Flask-Mail 설치 중...
    "%PYTHON_PATH%" -m pip install flask-mail --quiet
)

echo.
echo ================================================================
echo [정보] 서버를 외부 접근 가능하게 시작합니다...
echo [정보] 같은 WiFi에 연결된 스마트폰에서 접근 가능합니다.
echo ================================================================
echo.

REM PC의 IP 주소 확인
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set LOCAL_IP=%%a
    set LOCAL_IP=!LOCAL_IP: =!
    goto :ip_found
)

:ip_found
echo ================================================================
echo [접속 주소 - 포트 5001]
echo ================================================================
echo   PC: http://localhost:5001
if defined LOCAL_IP (
    echo   스마트폰: http://%LOCAL_IP%:5001
    echo.
    echo [중요] 스마트폰에서 위 주소로 접속하세요!
) else (
    echo   스마트폰: http://[PC의 IP 주소]:5001
    echo.
    echo [중요] PC의 IP 주소를 확인하세요: ipconfig
)
echo.
echo [주의] 방화벽에서 포트 5001을 허용해야 할 수 있습니다.
echo ================================================================
echo.

REM 환경 변수 설정 (외부 접근 허용, 포트 5001)
set FLASK_RUN_HOST=0.0.0.0
set FLASK_RUN_PORT=5001

echo [시작] 서버 시작 중... (포트: 5001)
echo [중지] 서버를 중지하려면 Ctrl+C를 누르세요.
echo ================================================================
echo.

REM 서버 시작
"%PYTHON_PATH%" app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [오류] 서버 시작 실패!
    pause
)


