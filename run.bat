@echo off
title CoalMind AI Launcher (SIH26023)
echo =====================================================================
echo  COALMIND AI - SIH26023 (TEAM AGNIVAULT)
echo  "From Documents to Decisions"
echo =====================================================================
echo Starting FastAPI Backend (Port 8000)...
start "CoalMind AI Backend" cmd /k "cd /d %~dp0 && python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting Vite React Frontend (Port 5173)...
start "CoalMind AI Frontend" cmd /k "cd /d %~dp0frontend && npm.cmd run dev"

echo.
echo Both servers are launching!
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:5173
echo.
pause
