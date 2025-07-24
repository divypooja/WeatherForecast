#!/usr/bin/env python3
"""
CLI script to initialize permissions in the database
Run this script to set up the default permissions system
"""

from app import app, db
from models_permissions import init_permissions

if __name__ == '__main__':
    with app.app_context():
        print("Initializing permissions...")
        init_permissions()
        print("Permissions initialization complete!")