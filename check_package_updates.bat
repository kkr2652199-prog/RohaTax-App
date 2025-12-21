@echo off
REM ================================================================
REM Python 패키지 업데이트 확인 스크립트
REM ================================================================

chcp 65001 > nul

echo ================================
echo Python 패키지 버전 확인
echo ================================
echo.

REM Python 3.14 경로 설정
set PYTHON_PATH=C:\ProgramData\anaconda3\envs\python314\python.exe

REM Python 버전 확인
echo [Python 버전]
"%PYTHON_PATH%" --version
echo.

REM pip 버전 확인
echo [pip 버전]
"%PYTHON_PATH%" -m pip --version
echo.

echo ================================
echo 설치된 주요 패키지 버전
echo ================================
echo.

REM 주요 패키지 버전 확인
"%PYTHON_PATH%" -m pip show Flask Werkzeug Jinja2 SQLAlchemy pandas openpyxl requests 2>nul | findstr /C:"Name:" /C:"Version:"
echo.

echo ================================
echo 업데이트 가능한 패키지 확인
echo ================================
echo.

"%PYTHON_PATH%" -m pip list --outdated

echo.
echo ================================
echo 업데이트 명령어
echo ================================
echo.
echo 모든 패키지 업데이트:
echo   "%PYTHON_PATH%" -m pip install --upgrade -r requirements.txt
echo.
echo 특정 패키지 업데이트:
echo   "%PYTHON_PATH%" -m pip install --upgrade ^<패키지명^>
echo.

pause

