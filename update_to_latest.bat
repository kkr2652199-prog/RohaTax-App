@echo off
REM ================================================================
REM Python 패키지 최신 버전으로 업데이트
REM ================================================================

chcp 65001 > nul

echo ================================
echo Python 패키지 최신 버전 업데이트
echo ================================
echo.

REM Python 3.14 경로 설정
set PYTHON_PATH=C:\ProgramData\anaconda3\envs\python314\python.exe

REM pip 최신 버전으로 업데이트
echo [1/4] pip 최신 버전으로 업데이트 중...
"%PYTHON_PATH%" -m pip install --upgrade pip
echo.

REM 현재 설치된 패키지 확인
echo [2/4] 현재 설치된 패키지 확인 중...
"%PYTHON_PATH%" -m pip list
echo.

REM requirements.txt의 패키지들을 최신 버전으로 업데이트
echo [3/4] requirements.txt 패키지 최신 버전으로 업데이트 중...
echo.
echo 업데이트 중인 패키지:
echo   - Flask 및 관련 패키지
echo   - SQLAlchemy
echo   - pandas, openpyxl, xlrd
echo   - requests
echo   - psutil
echo   - python-dotenv
echo   - APScheduler
echo   - bcrypt
echo   - Flask-Limiter
echo   - gunicorn
echo.

"%PYTHON_PATH%" -m pip install --upgrade Flask Werkzeug Jinja2 MarkupSafe itsdangerous click blinker
"%PYTHON_PATH%" -m pip install --upgrade sqlalchemy
"%PYTHON_PATH%" -m pip install --upgrade pandas openpyxl xlrd
"%PYTHON_PATH%" -m pip install --upgrade requests
"%PYTHON_PATH%" -m pip install --upgrade psutil
"%PYTHON_PATH%" -m pip install --upgrade python-dotenv
"%PYTHON_PATH%" -m pip install --upgrade APScheduler
"%PYTHON_PATH%" -m pip install --upgrade bcrypt
"%PYTHON_PATH%" -m pip install --upgrade Flask-Limiter
"%PYTHON_PATH%" -m pip install --upgrade gunicorn

echo.
echo [4/4] 업데이트된 패키지 버전 확인 중...
"%PYTHON_PATH%" -m pip list | findstr /C:"Flask" /C:"Werkzeug" /C:"Jinja2" /C:"SQLAlchemy" /C:"pandas" /C:"openpyxl" /C:"requests" /C:"psutil" /C:"python-dotenv" /C:"APScheduler" /C:"bcrypt" /C:"Flask-Limiter" /C:"gunicorn"

echo.
echo ================================
echo 업데이트 완료!
echo ================================
echo.
echo 주의: requirements.txt 파일도 업데이트해야 합니다.
echo       업데이트된 버전을 확인한 후 requirements.txt를 수정하세요.
echo.

pause

