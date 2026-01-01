@echo off
title Pixel Art Converter Setup

echo.
echo ===============================================
echo         Pixel Art Converter Setup
echo ===============================================
echo.

echo Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo Creating directories...
if not exist uploads mkdir uploads
if not exist outputs mkdir outputs
if not exist logs mkdir logs

echo.
echo ===============================================
echo              Setup Complete!
echo ===============================================
echo.
echo Usage:
echo   1. Run start.bat to start the application
echo   2. Open browser: http://localhost:8000
echo.
pause