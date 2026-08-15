@echo off
setlocal

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Install Python 3.12+ from https://www.python.org/downloads/
    echo ^(check "Add python.exe to PATH" during install^), then run this script again.
    pause
    exit /b 1
)

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Installing dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -r requirements.txt

if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env >nul
)

echo Setting up the database...
python manage.py migrate

echo.
echo Setup complete. Run run.bat to start ScriptNova.
pause
