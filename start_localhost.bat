@echo off
REM Windows batch file to start Factory Management System on localhost

echo ========================================
echo Factory Management System - Localhost
echo ========================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -e .
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
    echo.
    echo Please edit .env file with your configuration
    echo Press any key to continue after editing .env...
    pause
)

REM Initialize database and create admin user
echo Initializing database...
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized')"

echo.
echo Creating admin user...
echo Please follow the prompts to create an admin user:
python cli.py create-admin

REM Start the application
echo.
echo Starting Factory Management System...
echo Application will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
python main.py

pause