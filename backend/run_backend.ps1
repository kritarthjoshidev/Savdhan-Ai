# Start Backend - PowerShell script
# This script starts the Surveillance Backend FastAPI server

Clear-Host
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SURVEILLANCE BACKEND - PowerShell Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = py -3.14 --version 2>&1
    Write-Host "Python version: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.10+ from https://www.python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Check if dependencies are installed
Write-Host "Checking if dependencies are installed..." -ForegroundColor Yellow
try {
    py -3.14 -c "import fastapi" 2>$null
} catch {
    Write-Host ""
    Write-Host "Dependencies not installed. Installing now..." -ForegroundColor Yellow
    Write-Host "Running: pip install -r requirements.txt" -ForegroundColor Yellow
    Write-Host ""
    py -3.14 -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Starting FastAPI Server..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "WebSocket: ws://localhost:8000/ws/alerts" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Run the backend
py -3.14 run_backend.py

Read-Host "Press Enter to exit"
