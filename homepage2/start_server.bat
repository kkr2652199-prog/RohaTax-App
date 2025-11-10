@echo off
chcp 65001
cd /d "%~dp0"
echo ================================
echo 1Tax App Server Start
echo ================================
echo Current Directory: %CD%
echo Starting server...
python app.py
pause
