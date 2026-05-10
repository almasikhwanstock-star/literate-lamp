@echo off
echo Starting Shutterstock AI...

:: Start Backend in new terminal
start "Shutterstock AI - Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --reload --port 8000"

:: Wait 2 seconds then start Frontend
timeout /t 2 /nobreak >nul
start "Shutterstock AI - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

:: Open browser after 5 seconds
timeout /t 5 /nobreak >nul
start http://localhost:5173

echo Done! Two terminals opened.
exit
