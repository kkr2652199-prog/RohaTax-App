@echo off
REM ================================================================
REM 본진에서 데이터베이스 복사 (homepage1로 동기화)
REM ================================================================

chcp 65001 > nul

echo ================================
echo 본진 → homepage1 데이터베이스 동기화
echo ================================
echo.

REM 현재 위치 확인
cd /d "%~dp0"
echo 현재 위치: %CD%

REM 본진 데이터베이스 확인
if not exist "..\database\app.db" (
    echo [오류] 본진에 데이터베이스 파일이 없습니다.
    echo 경로: ..\database\app.db
    pause
    exit /b 1
)

echo [확인] 본진 데이터베이스 파일 발견
echo.

REM 백업 생성
if exist "database\app.db" (
    echo [백업] 기존 데이터베이스 백업 중...
    set BACKUP_NAME=app_backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.db
    set BACKUP_NAME=%BACKUP_NAME: =0%
    copy "database\app.db" "database\%BACKUP_NAME%" > nul
    echo [완료] 백업 파일: database\%BACKUP_NAME%
    echo.
)

REM 데이터베이스 복사
echo [복사] 본진 데이터베이스 → homepage1...
copy /Y "..\database\app.db" "database\app.db" > nul
if %ERRORLEVEL% EQU 0 (
    echo [완료] 데이터베이스 동기화 완료!
    echo.
    echo [확인] 파일 크기:
    dir "database\app.db" | find "app.db"
) else (
    echo [오류] 데이터베이스 복사 실패
    pause
    exit /b 1
)

echo.
echo ================================
echo 동기화 완료!
echo ================================
pause



