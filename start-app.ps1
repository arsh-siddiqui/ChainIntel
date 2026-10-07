# ChainIntel Desktop Application Launcher Script
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "         CHAININTEL PRO WORKSTATION LAUNCHER (PowerShell)          " -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "[1/2] Launching Backend Service (FastAPI on Port 8001)..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d `"$ScriptDir\backend`" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload" -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host "[2/2] Launching Frontend Interface (Next.js)..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d `"$ScriptDir\frontend`" && npm run dev" -WindowStyle Normal

Start-Sleep -Seconds 4

Write-Host "Opening ChainIntel Workstation Application..." -ForegroundColor Green
Start-Process "http://localhost:3000"

Write-Host "ChainIntel Workstation active at http://localhost:3000" -ForegroundColor Green
