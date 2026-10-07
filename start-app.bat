@echo off
title ChainIntel Workstation App Launcher
cls
echo ===================================================================
echo               CHAININTEL WINDOWS APPLICATION LAUNCHER
echo ===================================================================
echo [1/3] Navigating to application root...

cd /d "%~dp0"

echo [2/3] Starting ChainIntel Backend Engine (FastAPI on Port 8001)...
start "ChainIntel Backend Engine" /min cmd /c "cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload"

timeout /t 3 /nobreak >nul

echo [3/3] Starting ChainIntel Workstation Frontend (Next.js)...
start "ChainIntel Workstation Server" /min cmd /c "cd frontend && npm run dev"

timeout /t 4 /nobreak >nul

echo [✓] Launching ChainIntel Native Standalone Windows App Window...
start msedge --app=http://localhost:3000 --window-size=1440,900 || start chrome --app=http://localhost:3000 || start "" "http://localhost:3000"

echo ===================================================================
echo  ChainIntel Desktop Application is running!
echo  - Native App Window: Launched
echo  - Frontend Web URL:   http://localhost:3000
echo  - Backend API Docs:   http://localhost:8001/docs
echo ===================================================================
timeout /t 3 /nobreak >nul
exit
