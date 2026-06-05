@echo off
REM anti-impulse-buyer — One-time setup script (Windows)
echo Setting up anti-impulse-buyer...
echo.

REM Create virtual environment
echo [1/4] Creating Python virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Install Python deps
echo [2/4] Installing Python dependencies...
pip install -r requirements.txt

REM Install JS deps and build popup
echo [3/4] Building popup dashboard...
cd extension\popup
call npm install
call npx vite build
cd ..\..

REM Done
echo [4/4] Setup complete!
echo.
echo =============================================
echo  anti-impulse-buyer is ready!
echo.
echo  To start: run run_backend.bat
echo  Then load extension\ folder in Chrome:
echo    chrome://extensions -> Load unpacked
echo =============================================
pause
