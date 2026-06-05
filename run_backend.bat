@echo off
REM anti-impulse-buyer — Backend Launcher (Windows)
cd /d "%~dp0"
call venv\Scripts\activate.bat
python -m backend.main
pause
