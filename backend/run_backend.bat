@echo off
REM Start Backend - Windows batch file
REM This script starts the Surveillance Backend FastAPI server

cls
echo ========================================
echo SURVEILLANCE BACKEND - Windows Startup
echo ========================================
echo.

REM Check if Python is installed
py -3.14 --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org
    pause
    exit /b 1
)

echo Python version:
py -3.14 --version
echo.

REM Check if requirements are installed
echo Checking if dependencies are installed...
py -3.14 -c "import fastapi" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo Dependencies not installed. Installing now...
    echo Running: pip install -r requirements.txt
    echo.
    py -3.14 -m pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo Starting FastAPI Server...
echo ========================================
echo API Docs: http://localhost:8000/docs
echo WebSocket: ws://localhost:8000/ws/alerts
echo Press Ctrl+C to stop
echo ========================================
echo.

REM Run the backend
py -3.14 run_backend.py

pause
