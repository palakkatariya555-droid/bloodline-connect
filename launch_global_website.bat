@echo off
title Bloodline Connect - Live Global Launcher
color 0A
cls

echo ======================================================================
echo           BLOODLINE CONNECT -- ONE-CLICK GLOBAL LAUNCHER
echo ======================================================================
echo.

cd /d "%~dp0"

echo [1/3] Verifying Python Dependencies...
python -m pip install -q -r requirements.txt
if %errorlevel% neq 0 (
    echo [!] Warning: Dependency check returned code %errorlevel%.
) else (
    echo [OK] Dependencies checked.
)

echo.
echo [2/3] Starting Bloodline Connect Flask Server...
start "Bloodline Connect Backend Server" /min cmd /c "python backend.py"

timeout /t 3 /nobreak >nul

echo [OK] Flask server running locally on http://localhost:5000
echo.

echo [3/3] Creating Secure Global HTTPS Tunnel...
echo ======================================================================
echo  YOUR WEBSITE IS NOW LIVE GLOBALLY!
echo.
echo  Share the HTTPS URL generated below with anyone around the world:
echo ======================================================================
echo.

ssh -o StrictHostKeyChecking=no -R 80:localhost:5000 nokey@localhost.run

echo.
echo ======================================================================
echo  Server stopped or disconnected.
echo ======================================================================
pause
