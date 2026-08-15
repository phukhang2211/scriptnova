@echo off
echo Removing ScriptNova auto-start...
schtasks /end /tn "ScriptNova" >nul 2>nul
schtasks /delete /tn "ScriptNova" /f >nul 2>nul

echo Stopping the running app, if any...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%p >nul 2>nul

echo.
echo Done. ScriptNova will no longer start automatically when you log in.
echo You can still run it manually any time with run.bat.
pause
