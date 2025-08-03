#!/usr/bin/env python3
"""
Script to fix database schema issues - specifically the missing 'status' column in notification_logs table
"""
import sqlite3
import os
from app import create_app, db

def check_and_fix_notification_logs():
    """Check if notification_logs table has all required columns and add missing ones"""
    db_path = 'instance/factory.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
    
    # Expected columns based on the model definition
    expected_columns = {
        'id': 'INTEGER PRIMARY KEY',
        'type': 'VARCHAR(20) NOT NULL',
        'recipient': 'VARCHAR(255) NOT NULL', 
        'subject': 'VARCHAR(255)',
        'message': 'TEXT',
        'status': 'VARCHAR(20) DEFAULT "pending"',
        'success': 'BOOLEAN NOT NULL',
        'response': 'TEXT',
        'error_message': 'TEXT',
        'event_type': 'VARCHAR(50)',
        'event_id': 'INTEGER',
        'module': 'VARCHAR(30)',
        'sent_at': 'DATETIME',
        'delivered_at': 'DATETIME',
        'read_at': 'DATETIME',
        'service_provider': 'VARCHAR(50)',
        'provider_message_id': 'VARCHAR(100)',
        'recipient_name': 'VARCHAR(100)',
        'recipient_role': 'VARCHAR(50)',
        'created_at': 'DATETIME'
    }
    
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
        print(f"Expected columns: {list(expected_columns.keys())}")
        
        # Find missing columns
        missing_columns = [col for col in expected_columns.keys() if col not in column_names]
        
        if missing_columns:
            print(f"Missing columns: {missing_columns}")
            
            # Add missing columns one by one
            for col_name in missing_columns:
                col_definition = expected_columns[col_name]
                try:
                    cursor.execute(f"ALTER TABLE notification_logs ADD COLUMN {col_name} {col_definition};")
                    print(f"Added column: {col_name}")
                except Exception as e:
                    print(f"Error adding column {col_name}: {e}")
            
            conn.commit()
            print("Successfully added all missing columns")
        else:
            print("All required columns are present")
        
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