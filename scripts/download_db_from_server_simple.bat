@echo off
REM ================================================================
REM 배포 서버에서 데이터베이스 다운로드 (간단 버전)
REM ================================================================

chcp 65001 > nul

echo ================================================================
echo 배포 서버에서 데이터베이스 다운로드
echo ================================================================
echo.

cd /d "%~dp0\.."

echo [다운로드] 배포 서버에서 데이터베이스 다운로드 중...
echo 서버: ubuntu@52.78.116.159
echo 경로: /home/ubuntu/RohaTax-App/database/app.db
echo.

REM 백업 디렉토리 생성
if not exist "database\backups" mkdir "database\backups"

REM 기존 파일 백업
if exist "database\app.db" (
    echo [백업] 기존 데이터베이스 백업 중...
    set BACKUP_NAME=app_backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.db
    set BACKUP_NAME=%BACKUP_NAME: =0%
    copy "database\app.db" "database\backups\%BACKUP_NAME%" > nul
    echo [완료] 백업 파일: database\backups\%BACKUP_NAME%
    echo.
)

REM SCP로 다운로드
echo [다운로드] 서버에서 데이터베이스 다운로드 중...
scp ubuntu@52.78.116.159:/home/ubuntu/RohaTax-App/database/app.db database\app.db.from_server

if %ERRORLEVEL% EQU 0 (
    echo [완료] 다운로드 성공!
    echo.
    
    REM 다운로드한 파일을 메인 파일로 교체
    echo [적용] 데이터베이스 파일 적용 중...
    
    REM Flask 서버가 사용 중일 수 있으므로 .old로 백업 후 교체
    if exist "database\app.db" (
        ren "database\app.db" "app.db.old"
    )
    
    ren "database\app.db.from_server" "app.db"
    
    if exist "database\app.db" (
        echo [완료] 데이터베이스 복원 완료!
        echo.
        echo [확인] 파일 크기:
        dir "database\app.db" | find "app.db"
        echo.
        echo [중요] Flask 서버를 재시작하세요.
    ) else (
        echo [오류] 파일 교체 실패
    )
) else (
    echo [오류] 다운로드 실패
    echo.
    echo [해결 방법]
    echo 1. SSH 키가 설정되어 있는지 확인
    echo 2. 또는 AWS Lightsail 콘솔에서 직접 다운로드
    echo 3. 또는 서버에서 Python으로 데이터베이스 확인 후 수동 복원
)

echo.
echo ================================================================
pause


