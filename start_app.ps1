# SETUP & START SCRIPT (Windows PowerShell)
Write-Host "🚀 Starting Frost Night Factory App..." -ForegroundColor Green

# 1. Installera Backend
Write-Host "📦 Setting up Python backend..." -ForegroundColor Cyan
cd backend
if (-Not (Test-Path "venv")) {
    python -m venv venv
}
.\venv\Scripts\activate
pip install -r requirements.txt
cd ..

# 2. Installera Frontend
Write-Host "📦 Setting up Next.js frontend..." -ForegroundColor Cyan
npm install --legacy-peer-deps

# 3. Starta Allt
Write-Host "🚀 Starting both Frontend and Backend..." -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host "Backend: http://localhost:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop both servers." -ForegroundColor Gray

# Starta backend i bakgrunden
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\activate; uvicorn main:app --reload --port 8000"

# Starta frontend (blockerar)
npm run dev
