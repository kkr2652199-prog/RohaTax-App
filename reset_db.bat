@echo off
REM ================================================================
REM 데이터베이스 초기화 (빈 데이터베이스로 재생성)
REM ================================================================

chcp 65001 > nul

echo ================================================================
echo ⚠️  경고: 데이터베이스 초기화
echo ================================================================
echo.
echo 이 작업은 현재 데이터베이스의 모든 데이터를 삭제하고
echo 빈 데이터베이스로 재생성합니다.
echo.
echo [주의사항]
echo - 모든 사용자 데이터가 삭제됩니다
echo - 모든 로그 데이터가 삭제됩니다
echo - 복구할 수 없습니다!
echo.
set /p CONFIRM="정말로 초기화하시겠습니까? (yes/no): "

if /i not "%CONFIRM%"=="yes" (
    echo 작업이 취소되었습니다.
    pause
    exit /b 0
)

echo.
echo [백업] 기존 데이터베이스 백업 중...
cd /d "%~dp0"

if exist "database\app.db" (
    set BACKUP_NAME=app_backup_before_reset_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.db
    set BACKUP_NAME=%BACKUP_NAME: =0%
    if not exist "database\backups" mkdir "database\backups"
    copy "database\app.db" "database\backups\%BACKUP_NAME%" > nul
    echo [완료] 백업 파일: database\backups\%BACKUP_NAME%
    echo.
)

echo [삭제] 기존 데이터베이스 파일 삭제 중...
if exist "database\app.db" del /F /Q "database\app.db" > nul
if exist "database\app.db-shm" del /F /Q "database\app.db-shm" > nul
if exist "database\app.db-wal" del /F /Q "database\app.db-wal" > nul

echo [초기화] 새 데이터베이스 생성 중...
set PYTHON_PATH=C:\ProgramData\anaconda3\envs\python314\python.exe

"%PYTHON_PATH%" -c "from core.db import init_db; init_db(); print('✅ 데이터베이스 초기화 완료!')"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================
    echo ✅ 데이터베이스 초기화 완료!
    echo ================================================================
    echo.
    echo 이제 서버를 시작하면 빈 데이터베이스로 시작됩니다.
) else (
    echo.
    echo ================================================================
    echo ❌ 데이터베이스 초기화 실패
    echo ================================================================
)

echo.
pause



