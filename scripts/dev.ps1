# ChainIntel local development launcher (Windows PowerShell)
# Starts the backend (uvicorn :8000) and frontend (next dev :3000) in separate windows.

Write-Host "ChainIntel dev launcher" -ForegroundColor Cyan

# 1. Backend
Push-Location "$PSScriptRoot\..\backend"
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; uvicorn app.main:app --reload --port 8000"
Pop-Location

# 2. Frontend
Push-Location "$PSScriptRoot\..\frontend"
if (-not (Test-Path ".env.local")) { Copy-Item ".env.local.example" ".env.local" }
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev"
Pop-Location

Write-Host ""
Write-Host "Backend:  http://localhost:8000  (docs at /docs)" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Green
