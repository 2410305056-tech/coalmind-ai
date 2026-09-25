# CoalMind AI PowerShell Launcher
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host " COALMIND AI - SIH26023 (TEAM AGNIVAULT)" -ForegroundColor Yellow
Write-Host " 'From Documents to Decisions'" -ForegroundColor White
Write-Host "=====================================================================" -ForegroundColor Cyan

$root = $PSScriptRoot

Write-Host "Starting FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root'; python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

Write-Host "Starting Vite Frontend on http://127.0.0.1:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\frontend'; npm.cmd run dev"

Write-Host "`nCoalMind AI is active!" -ForegroundColor Cyan
Write-Host "Frontend: http://127.0.0.1:5173" -ForegroundColor White
Write-Host "Backend:  http://127.0.0.1:8000" -ForegroundColor White
Write-Host "API Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
