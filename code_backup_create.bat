@echo off
REM ================================================================
REM Code Snapshot Creator
REM Usage: code_backup_create.bat "사유(한글 가능)"
REM Output: code_snapshots/YYYY-MM-DD_HH-MM-SS_사유.zip
REM ================================================================

chcp 65001 > nul
setlocal ENABLEDELAYEDEXPANSION

cd /d "%~dp0"

set REASON=%~1
if "%REASON%"=="" set REASON=코드스냅샷

REM sanitize reason for filename
set REASON_SAFE=%REASON:
= %
for /f "delims=\/:*?\"<>|" %%A in ("%REASON_SAFE%") do set REASON_SAFE=%%~A

for /f "tokens=1-4 delims=/:. " %%a in ("%date% %time%") do (
  set YYYY=%%a
  set MM=%%b
  set DD=%%c
)
for /f "tokens=1-3 delims=:., " %%h in ("%time%") do (
  set HH=%%h
  set MI=%%i
  set SS=%%j
)
set TS=%YYYY%-%MM%-%DD%_%HH%-%MI%-%SS%

set SNAP_DIR=%cd%\code_snapshots
set STAGE_DIR=%SNAP_DIR%\%TS%_%REASON_SAFE%
set ZIP_PATH=%SNAP_DIR%\%TS%_%REASON_SAFE%.zip

mkdir "%SNAP_DIR%" 2>nul
mkdir "%STAGE_DIR%" 2>nul

echo [1/3] 수집 중...
robocopy . "%STAGE_DIR%\app" app /e /xf /xd .git code_snapshots snapshots logs user_data output database *.pyc __pycache__ >nul
robocopy . "%STAGE_DIR%\core" core /e /xf /xd __pycache__ >nul
robocopy . "%STAGE_DIR%\routes" routes /e /xf /xd __pycache__ >nul
robocopy . "%STAGE_DIR%\templates" templates /e >nul
robocopy . "%STAGE_DIR%\static\js" static\js /e >nul
robocopy . "%STAGE_DIR%\static\css" static\css /e >nul
robocopy config "%STAGE_DIR%\config" *.json >nul

echo {^"name^":^"%TS%_%REASON_SAFE%^",^"reason^":^"%REASON%^",^"created_at^":^"%date% %time%^"} > "%STAGE_DIR%\code_snapshot.json"

echo [2/3] 압축 생성...
powershell -NoProfile -Command "Compress-Archive -Path '%STAGE_DIR%\*' -DestinationPath '%ZIP_PATH%' -Force" >nul 2>&1

if not exist "%ZIP_PATH%" (
  echo 압축 생성 실패
  exit /b 1
)

echo [3/3] 완료: %ZIP_PATH%
endlocal





