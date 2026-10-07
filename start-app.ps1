# ChainIntel Native Windows Desktop Application Launcher
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "       CHAININTEL NATIVE WINDOWS APP WORKSTATION LAUNCHER          " -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "[1/3] Launching Backend Service (FastAPI on Port 8001)..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd /d `"$ScriptDir\backend`" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload" -WindowStyle Minimized

Start-Sleep -Seconds 3

Write-Host "[2/3] Launching Frontend Interface (Next.js)..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd /d `"$ScriptDir\frontend`" && npm run dev" -WindowStyle Minimized

Start-Sleep -Seconds 4

Write-Host "[3/3] Opening ChainIntel Native Desktop Application Window..." -ForegroundColor Green
try {
    Start-Process "msedge" -ArgumentList "--app=http://localhost:3000", "--window-size=1440,900"
} catch {
    Start-Process "http://localhost:3000"
}

Write-Host "ChainIntel Native Workstation Application running!" -ForegroundColor Green
