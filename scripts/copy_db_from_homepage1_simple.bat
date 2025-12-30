@echo off
REM ================================================================
REM homepage1에서 데이터베이스만 복사 (단순 버전)
REM ================================================================

chcp 65001 > nul

echo ================================================================
echo homepage1에서 데이터베이스 복사
echo ================================================================
echo.

cd /d "%~dp0\.."

REM homepage1 데이터베이스 확인
if not exist "homepage1\database\app.db" (
    echo [오류] homepage1에 데이터베이스 파일이 없습니다.
    echo 경로: homepage1\database\app.db
    pause
    exit /b 1
)

echo [확인] homepage1 데이터베이스 파일 발견
echo.

REM 백업 디렉토리 생성
if not exist "database\backups" mkdir "database\backups"

REM 본진 데이터베이스 백업
if exist "database\app.db" (
    echo [백업] 본진 데이터베이스 백업 중...
    set BACKUP_NAME=app_backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.db
    set BACKUP_NAME=%BACKUP_NAME: =0%
    copy "database\app.db" "database\backups\%BACKUP_NAME%" > nul
    echo [완료] 백업 파일: database\backups\%BACKUP_NAME%
    echo.
)

REM homepage1 데이터베이스를 임시 파일로 복사
echo [복사] homepage1 데이터베이스 복사 중...
copy /Y "homepage1\database\app.db" "database\app.db.from_homepage1" > nul

if %ERRORLEVEL% EQU 0 (
    echo [완료] 복사 완료: database\app.db.from_homepage1
    echo.
    echo [정보] Flask 서버를 재시작한 후 다음 명령어로 적용하세요:
    echo   ren database\app.db app.db.old
    echo   ren database\app.db.from_homepage1 app.db
    echo.
    echo 또는 배치 파일을 다시 실행하면 자동으로 적용됩니다.
    echo.
) else (
    echo [오류] 복사 실패
    pause
    exit /b 1
)

REM Flask 서버가 종료되어 있으면 자동으로 적용 시도
echo [적용] 데이터베이스 파일 적용 시도 중...
if exist "database\app.db" (
    ren "database\app.db" "app.db.old" > nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        ren "database\app.db.from_homepage1" "app.db" > nul 2>&1
        if %ERRORLEVEL% EQU 0 (
            echo [완료] 데이터베이스 복원 완료!
            echo.
            echo [확인] 파일 크기:
            dir "database\app.db" | find "app.db"
        ) else (
            echo [정보] 파일 교체 실패 - Flask 서버가 사용 중일 수 있습니다.
            echo [정보] Flask 서버를 재시작한 후 수동으로 교체하세요.
        )
    ) else (
        echo [정보] 기존 파일 이름 변경 실패 - Flask 서버가 사용 중일 수 있습니다.
        echo [정보] Flask 서버를 재시작한 후 수동으로 교체하세요.
    )
) else (
    ren "database\app.db.from_homepage1" "app.db" > nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [완료] 데이터베이스 복원 완료!
    ) else (
        echo [오류] 파일 이름 변경 실패
    )
)

echo.
echo ================================================================
pause


