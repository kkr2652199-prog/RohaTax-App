@echo off
REM ================================================================
REM Ngrok 터널링 - 로컬 서버를 인터넷에 노출
REM ================================================================

chcp 65001 > nul

echo ================================
echo Ngrok 터널 시작 (포트 5001)
echo ================================
echo.

REM Ngrok 설치 확인 (현재 폴더 우선 확인)
if exist "ngrok.exe" (
    set NGROK_CMD=ngrok.exe
    goto :ngrok_found
)

REM 시스템 PATH에서 확인
where ngrok >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set NGROK_CMD=ngrok
    goto :ngrok_found
)

REM Ngrok을 찾을 수 없음
echo [오류] Ngrok이 설치되어 있지 않습니다.
echo.
echo ================================================================
echo 설치 방법 (3가지 중 선택):
echo ================================================================
echo.
echo [방법 1] 직접 다운로드 (가장 간단) - 추천
echo   1. 브라우저에서 https://ngrok.com/download 접속
echo   2. Windows 버전 다운로드
echo   3. 압축 해제 후 ngrok.exe를 이 폴더에 복사
echo      (현재 폴더: %CD%)
echo.
echo [방법 2] Chocolatey 사용 (관리자 권한 필요)
echo   choco install ngrok
echo.
echo [방법 3] Scoop 사용
echo   scoop install ngrok
echo.
echo ================================================================
echo.
echo 자세한 설치 가이드: NGROK_설치_및_사용_가이드.md 파일을 참고하세요.
echo.
pause
exit /b 1

:ngrok_found
echo [확인] Ngrok을 찾았습니다: %NGROK_CMD%

REM Ngrok 버전 확인
echo [확인] Ngrok 버전 확인 중...
%NGROK_CMD% version
echo.

REM 서버가 실행 중인지 확인
echo [확인] 로컬 서버(포트 5001)가 실행 중인지 확인 중...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:5001' -TimeoutSec 2 -UseBasicParsing; Write-Host '[확인] 서버가 실행 중입니다.' -ForegroundColor Green } catch { Write-Host '[경고] 서버가 실행 중이지 않을 수 있습니다. 먼저 start_server_5001.bat를 실행하세요.' -ForegroundColor Yellow }"

echo.
echo ================================
echo Ngrok 터널 시작 중...
echo ================================
echo.
echo [중요] Ngrok이 생성한 공개 URL이 표시됩니다.
echo 이 URL을 인터넷 어디서나 접속할 수 있습니다.
echo.
echo [사용 방법]
echo 1. 아래에 표시되는 "Forwarding" URL을 복사하세요
echo    예: https://xxxx-xxx-xxx-xxx.ngrok-free.app
echo 2. 이 URL을 브라우저에서 열거나 다른 사람에게 공유하세요
echo 3. Ngrok 웹 인터페이스: http://127.0.0.1:4040
echo.
echo [주의사항]
echo - 무료 버전은 세션이 일정 시간 후 종료될 수 있습니다.
echo - 보안을 위해 테스트 목적으로만 사용하세요.
echo - 서버를 중지하려면 Ctrl+C를 누르세요.
echo.
echo ================================
echo.

REM Ngrok 실행 (포트 5001 - homepage1 기본 포트)
echo [중요] 포트 5001로 터널을 생성합니다.
echo [중요] 서버가 포트 5001에서 실행 중이어야 합니다.
echo.
%NGROK_CMD% http 5001

pause







