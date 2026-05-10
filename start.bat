name=start.bat url=https://github.com/almasikhwanstock-star/literate-lamp/blob/main/start.bat
@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

cls
echo.
echo ════════════════════════════════════════════════════════════
echo   Literate Lamp - Starting Application
echo ════════════════════════════════════════════════════════════
echo.

REM Check if venv exists
if not exist "venv" (
    echo ❌ ERROR: Virtual environment not found!
    echo.
    echo Please run 'setup-python.bat' first to setup dependencies.
    echo.
    pause
    exit /b 1
)

REM Activate venv
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  WARNING: .env file not found!
    echo.
    echo 1. Copy .env.example to .env
    echo 2. Edit .env and add your API keys
    echo.
    pause
    exit /b 1
)

echo ✓ Virtual environment activated
echo.

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Node.js not found!
    echo Download: https://nodejs.org/
    pause
    exit /b 1
)

echo ✓ Backend environment ready
echo ✓ Frontend environment ready
echo.

REM Install frontend dependencies if needed
cd frontend
if not exist "node_modules" (
    echo ⏳ Installing frontend dependencies...
    call npm install --silent
    if %errorlevel% neq 0 (
        echo ❌ Failed to install frontend dependencies
        cd ..
        pause
        exit /b 1
    )
)
cd ..

echo ✓ All systems ready!
echo.

cls
echo.
echo ════════════════════════════════════════════════════════════
echo   ✓ STARTING SERVICES
echo ════════════════════════════════════════════════════════════
echo.
echo 📡 Backend:  http://localhost:8000
echo 🎨 Frontend: http://localhost:5173
echo.
echo Press Ctrl+C in this window to stop all services
echo.

REM Start backend in new window
start "Literate Lamp - Backend" cmd /k "venv\Scripts\activate.bat && cd backend && python -m uvicorn main:app --reload --port 8000"

REM Wait for backend to start
timeout /t 2 /nobreak

REM Start frontend in new window
start "Literate Lamp - Frontend" cmd /k "cd frontend && npm run dev"

echo ✓ Both services started!
echo.
pause
