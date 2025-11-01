@echo off
REM ================================================================
REM Code Snapshot Restorer
REM Usage: code_backup_restore.bat "code_snapshots\YYYY-MM-DD_HH-MM-SS_사유.zip"
REM 안전 보관 후 원복: restore_backup_code/YYYY-MM-DD_HH-MM-SS/
REM ================================================================

chcp 65001 > nul
setlocal ENABLEDELAYEDEXPANSION

cd /d "%~dp0"

set ZIP=%~1
if "%ZIP%"=="" (
  echo 사용법: code_backup_restore.bat "code_snapshots\스냅샷.zip"
  exit /b 1
)

if not exist "%ZIP%" (
  echo 파일이 없습니다: %ZIP%
  exit /b 1
)

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

set SAFE=%cd%\restore_backup_code\%TS%
mkdir "%SAFE%" 2>nul

echo [1/3] 현재 코드 안전 보관...
robocopy app "%SAFE%\app" /e >nul
robocopy core "%SAFE%\core" /e >nul
robocopy routes "%SAFE%\routes" /e >nul
robocopy templates "%SAFE%\templates" /e >nul
robocopy static\js "%SAFE%\static\js" /e >nul
robocopy static\css "%SAFE%\static\css" /e >nul
robocopy config "%SAFE%\config" *.json >nul

echo [2/3] 스냅샷 해제...
powershell -NoProfile -Command "Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%cd%\__code_restore_stage' -Force" >nul 2>&1
if not exist "%cd%\__code_restore_stage" (
  echo 해제 실패
  exit /b 1
)

echo [3/3] 원복 적용...
robocopy "%cd%\__code_restore_stage\app" app /e >nul
robocopy "%cd%\__code_restore_stage\core" core /e >nul
robocopy "%cd%\__code_restore_stage\routes" routes /e >nul
robocopy "%cd%\__code_restore_stage\templates" templates /e >nul
robocopy "%cd%\__code_restore_stage\static\js" static\js /e >nul
robocopy "%cd%\__code_restore_stage\static\css" static\css /e >nul
robocopy "%cd%\__code_restore_stage\config" config *.json >nul

rd /s /q "%cd%\__code_restore_stage" >nul 2>&1

echo 완료. 안전 보관: %SAFE%
endlocal





