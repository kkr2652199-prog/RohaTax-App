@echo off
REM ================================================================
REM 새 데이터베이스 파일 적용 스크립트
REM Flask 서버를 재시작한 후 실행하세요
REM ================================================================

chcp 65001 > nul

echo ================================================================
echo 새 데이터베이스 파일 적용
echo ================================================================
echo.

cd /d "%~dp0\.."

if not exist "database\app.db.new" (
    echo [오류] app.db.new 파일이 없습니다.
    pause
    exit /b 1
)

echo [확인] 새 데이터베이스 파일 발견: database\app.db.new
echo.

REM 기존 파일 백업
if exist "database\app.db" (
    echo [백업] 기존 데이터베이스 백업 중...
    set BACKUP_NAME=app_backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.db
    set BACKUP_NAME=%BACKUP_NAME: =0%
    copy "database\app.db" "database\backups\%BACKUP_NAME%" > nul
    echo [완료] 백업 파일: database\backups\%BACKUP_NAME%
    echo.
)

REM 기존 파일 삭제
echo [삭제] 기존 데이터베이스 파일 삭제 중...
if exist "database\app.db" del /F /Q "database\app.db" > nul 2>&1
if exist "database\app.db-wal" del /F /Q "database\app.db-wal" > nul 2>&1
if exist "database\app.db-shm" del /F /Q "database\app.db-shm" > nul 2>&1

REM 새 파일을 메인 파일로 이름 변경
echo [적용] 새 데이터베이스 파일 적용 중...
ren "database\app.db.new" "app.db"

if exist "database\app.db" (
    echo [완료] 데이터베이스 복원 완료!
    echo.
    echo [확인] 파일 크기:
    dir "database\app.db" | find "app.db"
) else (
    echo [오류] 파일 이름 변경 실패
    pause
    exit /b 1
)

echo.
echo ================================================================
echo 적용 완료!
echo ================================================================
pause

