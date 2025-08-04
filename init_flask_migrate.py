#!/usr/bin/env python3
"""
Initialize Flask-Migrate for schema management
"""

from flask import Flask
from flask_migrate import Migrate, init, migrate, upgrade
from main import app
from app import db
import os

def setup_flask_migrate():
    """Initialize Flask-Migrate for the project"""
    
    print("Setting up Flask-Migrate...")
    
    # Initialize Flask-Migrate
    migrate_obj = Migrate(app, db)
    
    # Create migrations directory if it doesn't exist
    if not os.path.exists('migrations'):
        print("Creating migrations directory...")
        with app.app_context():
            init()
        print("✓ Migrations directory created")
    else:
        print("✓ Migrations directory already exists")
    
    print("\nFlask-Migrate setup complete!")
    print("\nUsage:")
    print("1. Create migration: flask db migrate -m 'description'")
    print("2. Apply migration: flask db upgrade")
    print("3. View current revision: flask db current")
    print("4. View migration history: flask db history")

if __name__ == "__main__":
    setup_flask_migrate()