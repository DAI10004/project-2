@echo off
title Pixel Art Converter

echo.
echo ===============================================
echo         Pixel Art Converter
echo ===============================================
echo.

echo Checking virtual environment...
if not exist venv (
    echo Error: Virtual environment not found
    echo Please run install.bat first
    echo.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Checking dependencies...
python -c "import fastapi, cv2, numpy" >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Dependencies check failed
    echo Please run install.bat to reinstall dependencies
    pause
    exit /b 1
)

echo.
echo ===============================================
echo         Starting Server...
echo ===============================================
echo.
echo Local access: http://localhost:8000
echo Network access: http://YOUR_IP:8000
echo.
echo Press Ctrl+C to stop the server
echo.

python run.py

echo.
echo Server stopped
echo.
pause