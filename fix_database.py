#!/usr/bin/env python3
"""
Script to fix database schema issues - specifically the missing 'status' column in notification_logs table
"""
import sqlite3
import os
from app import create_app, db

def check_and_fix_notification_logs():
    """Check if notification_logs table has the status column and add it if missing"""
    db_path = 'instance/factory.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if notification_logs table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notification_logs';")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("notification_logs table does not exist - will be created by Flask app")
            conn.close()
            return True
        
        # Get current table schema
        cursor.execute("PRAGMA table_info(notification_logs);")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"Current columns in notification_logs: {column_names}")
        
        # Check if status column exists
        if 'status' not in column_names:
            print("Adding missing 'status' column...")
            cursor.execute("ALTER TABLE notification_logs ADD COLUMN status VARCHAR(20) DEFAULT 'pending';")
            conn.commit()
            print("Successfully added 'status' column")
        else:
            print("'status' column already exists")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error fixing database: {e}")
        return False

def recreate_tables():
    """Recreate all tables using Flask app context"""
    try:
        app = create_app()
        with app.app_context():
            # Drop and recreate all tables
            db.drop_all()
            db.create_all()
            print("Successfully recreated all database tables")
            return True
    except Exception as e:
        print(f"Error recreating tables: {e}")
        return False

if __name__ == "__main__":
    print("Checking and fixing notification_logs table...")
    
    # First try to fix the existing table
    if check_and_fix_notification_logs():
        print("Database fix completed successfully")
    else:
        print("Failed to fix existing table, trying to recreate all tables...")
        if recreate_tables():
            print("Tables recreated successfully")
        else:
            print("Failed to recreate tables")