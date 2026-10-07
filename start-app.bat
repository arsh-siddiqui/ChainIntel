@echo off
title ChainIntel Pro Workstation Launcher
cls
echo ===================================================================
echo               CHAININTEL PRO WORKSTATION LAUNCHER
echo ===================================================================
echo [1/3] Checking environment & dependencies...

cd /d "%~dp0"

echo [2/3] Starting ChainIntel Backend Server (FastAPI on Port 8001)...
start "ChainIntel Backend API" cmd /k "cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload"

timeout /t 3 /nobreak >nul

echo [3/3] Starting ChainIntel Workstation Frontend (Next.js)...
start "ChainIntel Desktop Frontend" cmd /k "cd frontend && npm run dev"

timeout /t 5 /nobreak >nul

echo Launching ChainIntel Desktop Application Window...
start "" "http://localhost:3000"

echo ===================================================================
echo  ChainIntel Workstation is now running!
echo  - Frontend App: http://localhost:3000
echo  - Backend API:  http://localhost:8001/docs
echo ===================================================================
pause
