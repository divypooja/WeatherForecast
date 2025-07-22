#!/usr/bin/env python3
"""
Local development runner for Factory Management System
This script provides an easy way to run the application locally with proper configuration
"""

import os
import sys
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file if it exists"""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✓ Loaded environment variables from .env file")
    else:
        print("⚠ No .env file found. Using default configuration.")

def setup_default_env():
    """Set up default environment variables for local development"""
    defaults = {
        'DATABASE_URL': 'sqlite:///factory.db',
        'SESSION_SECRET': 'dev-secret-key-change-in-production',
        'FLASK_ENV': 'development',
        'FLASK_DEBUG': '1'
    }
    
    for key, value in defaults.items():
        if key not in os.environ:
            os.environ[key] = value
    
    print("✓ Default environment variables set")

def check_database():
    """Check if database is accessible and create tables if needed"""
    try:
        from app import app, db
        with app.app_context():
            db.create_all()
        print("✓ Database tables created/verified")
        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False

def check_admin_user():
    """Check if admin user exists"""
    try:
        from app import app
        from models import User
        with app.app_context():
            admin = User.query.filter_by(role='admin').first()
            if admin:
                print("✓ Admin user exists")
                return True
            else:
                print("⚠ No admin user found. Run 'python cli.py create-admin' to create one.")
                return False
    except Exception as e:
        print(f"✗ Could not check admin user: {e}")
        return False

def main():
    """Main runner function"""
    print("🏭 Factory Management System - Local Development Runner")
    print("=" * 60)
    
    # Load environment
    load_env_file()
    setup_default_env()
    
    # Check dependencies
    print("\n📋 Checking dependencies...")
    try:
        import flask
        import flask_sqlalchemy
        import flask_login
        import flask_wtf
        print("✓ All required packages installed")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Run: pip install -e .")
        sys.exit(1)
    
    # Check database
    print("\n🗄️ Checking database...")
    if not check_database():
        print("Please check your DATABASE_URL configuration")
        sys.exit(1)
    
    # Check admin user
    print("\n👤 Checking admin user...")
    check_admin_user()
    
    # Start application
    print("\n🚀 Starting Flask application...")
    print(f"Database: {os.environ.get('DATABASE_URL', 'Not set')}")
    print(f"Debug mode: {os.environ.get('FLASK_DEBUG', 'Not set')}")
    print("\n📱 Application will be available at: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    
    try:
        from main import app
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"✗ Failed to start application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()