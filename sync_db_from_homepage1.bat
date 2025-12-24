@echo off
REM Sync main app database from homepage1 (전초기지) to main (본진)

set SRC_DB=homepage1\database\app.db
set SRC_VERSIONS_DB=homepage1\database\versions.db
set DEST_DIR=database

echo [RohaTax] Sync DB from homepage1 to main...

IF NOT EXIST "%SRC_DB%" (
    echo [ERROR] Source DB not found: %SRC_DB%
    exit /b 1
)

IF NOT EXIST "%DEST_DIR%" (
    echo [INFO] Destination directory not found. Creating: %DEST_DIR%
    mkdir "%DEST_DIR%"
)

echo [INFO] Copying app.db ...
copy /Y "%SRC_DB%" "%DEST_DIR%\app.db" >nul
IF ERRORLEVEL 1 (
    echo [ERROR] Failed to copy app.db
    exit /b 1
)

IF EXIST "%SRC_VERSIONS_DB%" (
    echo [INFO] Copying versions.db ...
    copy /Y "%SRC_VERSIONS_DB%" "%DEST_DIR%\versions.db" >nul
)

echo [OK] Database sync from homepage1 to main completed.


