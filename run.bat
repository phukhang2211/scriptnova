@echo off
setlocal

if not exist .venv (
    echo Virtual environment not found. Run setup.bat first.
    pause
    exit /b 1
)

start "ScriptNova" cmd /k ".venv\Scripts\activate.bat && python manage.py runserver 127.0.0.1:8000"

timeout /t 2 /nobreak >nul
start http://127.0.0.1:8000/

echo ScriptNova is starting in a separate window. Close that window to stop it.
