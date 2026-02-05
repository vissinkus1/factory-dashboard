@echo off
REM Quick Start Script for Factory Productivity Dashboard on Windows

echo.
echo ======================================================================
echo   Factory Productivity Dashboard - Quick Start
echo ======================================================================
echo.

REM Check if Docker is available
where docker >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Docker is installed. Starting with Docker Compose...
    echo.
    docker-compose up --build
) else (
    echo Docker not found. Starting local development setup...
    echo.
    echo This script will start both backend and frontend.
    echo Two command windows will open.
    echo.
    pause
    
    REM Start backend in a new window
    echo Starting backend on port 5000...
    start "Factory Dashboard - Backend" cmd /k "cd backend && pip install -r requirements.txt && python app.py"
    
    REM Wait a moment for backend to start
    timeout /t 3 /nobreak
    
    REM Start frontend in a new window
    echo Starting frontend on port 8080...
    start "Factory Dashboard - Frontend" cmd /k "cd frontend && python -m http.server 8080"
    
    echo.
    echo ======================================================================
    echo   Services Starting...
    echo ======================================================================
    echo.
    echo Frontend:  http://localhost:8080
    echo Backend:   http://localhost:5000
    echo API Docs:  See README.md
    echo.
    echo Press Ctrl+C in each window to stop the services.
    echo.
)
