@echo off
echo ========================================
echo Factory Management System - Windows Setup
echo ========================================

REM Check if we're in the right directory
if not exist "main.py" (
    echo ERROR: main.py not found. Please run this script from the factory management system directory.
    echo Make sure you downloaded ALL the files to the same folder.
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found. Creating virtual environment...

REM Remove existing venv if it exists
if exist "venv" (
    rmdir /s /q venv
)

REM Create virtual environment
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install --upgrade pip

REM Install each package individually to see which one fails
echo Installing Flask...
pip install Flask>=3.1.1
if errorlevel 1 (
    echo ERROR: Failed to install Flask
    pause
    exit /b 1
)

echo Installing Flask extensions...
pip install Flask-SQLAlchemy>=3.1.1
pip install Flask-Login>=0.6.3
pip install Flask-WTF>=1.2.2

echo Installing database support...
pip install SQLAlchemy>=2.0.41
pip install psycopg2-binary>=2.9.10

echo Installing form validation...
pip install WTForms>=3.2.1
pip install email-validator>=2.2.0

echo Installing security and server...
pip install Werkzeug>=3.1.3
pip install gunicorn>=23.0.0
pip install Click>=8.2.1

echo Creating environment file...
if not exist ".env" (
    echo DATABASE_URL=sqlite:///factory.db > .env
    echo SESSION_SECRET=dev-secret-key-change-in-production >> .env
    echo FLASK_ENV=development >> .env
    echo FLASK_DEBUG=1 >> .env
    echo Environment file created successfully!
)

echo Initializing database...
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database tables created successfully!')"
if errorlevel 1 (
    echo ERROR: Failed to initialize database
    pause
    exit /b 1
)

echo.
echo Creating admin user...
echo Please follow the prompts to create an admin user:
python cli.py create-admin

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo To start the application:
echo 1. Make sure your virtual environment is activated: call venv\Scripts\activate.bat
echo 2. Run: python main.py
echo 3. Open your browser to: http://localhost:5000
echo.
echo Starting the application now...
python main.py

pause