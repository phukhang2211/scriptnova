@echo off
setlocal enabledelayedexpansion

set "APPDIR=%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Install it from https://www.python.org/downloads/
    echo ^(check "Add python.exe to PATH" during install^), then run this script again.
    pause
    exit /b 1
)

if not exist "%APPDIR%.venv" (
    echo Creating virtual environment...
    python -m venv "%APPDIR%.venv"
)

echo Installing dependencies...
call "%APPDIR%.venv\Scripts\activate.bat"
python -m pip install --upgrade pip >nul
pip install -r "%APPDIR%requirements.txt"

if not exist "%APPDIR%.env" (
    echo Creating .env from .env.example...
    copy "%APPDIR%.env.example" "%APPDIR%.env" >nul
)

echo Setting up the database...
python "%APPDIR%manage.py" migrate

REM Prefer pythonw.exe (no console window). Fall back to python.exe if it's
REM missing for some reason — the app still works, it just shows a window.
set "PYEXE=%APPDIR%.venv\Scripts\pythonw.exe"
if not exist "%PYEXE%" set "PYEXE=%APPDIR%.venv\Scripts\python.exe"

echo Registering ScriptNova to start automatically when you log in...
schtasks /create /tn "ScriptNova" ^
    /tr "\"%PYEXE%\" \"%APPDIR%manage.py\" runserver 127.0.0.1:8000" ^
    /sc onlogon /rl limited /f >nul

if errorlevel 1 (
    echo Could not register the auto-start task. You can still start the app
    echo manually any time by double-clicking run.bat.
    pause
    exit /b 1
)

echo Stopping any previous copy still running...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%p >nul 2>nul

echo Starting ScriptNova now...
schtasks /run /tn "ScriptNova" >nul

timeout /t 3 /nobreak >nul
start http://127.0.0.1:8000/

echo.
echo Done. ScriptNova will now start automatically every time you log into
echo Windows, running quietly in the background — no window, nothing to
echo double-click. Just open http://127.0.0.1:8000/ in your browser whenever
echo you want to use it.
echo.
echo To turn this off later, double-click uninstall-autostart.bat.
pause
