@echo off
REM ================================================================
REM 스마트폰 접속을 위한 방화벽 설정
REM 관리자 권한으로 실행해야 합니다
REM ================================================================

chcp 65001 > nul
setlocal EnableExtensions EnableDelayedExpansion

echo ================================
echo 스마트폰 접속 설정 도우미
echo ================================
echo.

REM 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [주의] 관리자 권한이 필요합니다.
    echo 이 파일을 우클릭하여 "관리자 권한으로 실행"을 선택하세요.
    pause
    exit /b 1
)

echo [1단계] Windows 방화벽에서 포트 5000 허용 중...
netsh advfirewall firewall delete rule name="RohaTax Port 5000" >nul 2>&1
netsh advfirewall firewall add rule name="RohaTax Port 5000" dir=in action=allow protocol=TCP localport=5000

if %errorLevel% equ 0 (
    echo [성공] 포트 5000이 방화벽에서 허용되었습니다.
) else (
    echo [실패] 방화벽 규칙 추가에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo [2단계] PC의 로컬 IP 주소 확인 중...
echo.

set "PRIVATE_IP="
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set IP_ADDR=%%a
    set IP_ADDR=!IP_ADDR: =!
    echo 발견된 IP 주소: !IP_ADDR!

    REM 사설 IP 우선 선택 (192.168.x.x / 10.x.x.x / 172.16~31.x.x)
    echo !IP_ADDR! | findstr /R /C:"^192\.168\." /C:"^10\." /C:"^172\.\(1[6-9]\|2[0-9]\|3[0-1]\)\." >nul
    if !errorLevel! equ 0 (
        if not defined PRIVATE_IP set "PRIVATE_IP=!IP_ADDR!"
    )
)

echo.
echo ================================
echo 설정 완료!
echo ================================
echo.
echo 스마트폰 접속 방법:
echo 1. PC와 스마트폰이 같은 Wi-Fi에 연결되어 있는지 확인
echo 2. start_server_5000.bat를 실행하여 서버를 시작하세요
echo 3. 스마트폰 브라우저에서 아래 주소로 접속:
echo.
if defined IP_ADDR (
    if defined PRIVATE_IP (
        echo    http://%PRIVATE_IP%:5000
    ) else (
        echo [주의] 현재 사설 IP(192.168.x.x 등)가 감지되지 않았습니다.
        echo [주의] PC와 스마트폰을 같은 Wi-Fi(공유기)로 연결해야 192.168.x.x 주소로 접속됩니다.
        echo.
        echo    http://%IP_ADDR%:5000
    )
) else (
    echo    http://[PC의IP주소]:5000
    echo    (PC의 IP 주소는 ipconfig 명령어로 확인하세요)
)
echo.
echo ================================
pause


