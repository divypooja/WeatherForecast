#!/bin/bash
# Unix/Mac shell script to start Factory Management System on localhost

echo "========================================"
echo "Factory Management System - Localhost"
echo "========================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.11+ from https://python.org"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -e .
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo ""
    echo "Please edit .env file with your configuration"
    echo "Press Enter to continue after editing .env..."
    read
fi

# Initialize database
echo "Initializing database..."
python3 -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized')"

# Create admin user
echo ""
echo "Creating admin user..."
echo "Please follow the prompts to create an admin user:"
python3 cli.py create-admin

# Start the application
echo ""
echo "Starting Factory Management System..."
echo "Application will be available at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""
python3 main.py