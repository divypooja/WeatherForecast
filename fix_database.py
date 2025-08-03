#!/usr/bin/env python3
"""
Script to fix database schema issues for all notification tables
"""
import sqlite3
import os
from app import create_app, db

def get_notification_table_schemas():
    """Get expected schemas for all notification tables"""
    return {
        'notification_logs': {
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
        },
        'notification_recipients': {
            'id': 'INTEGER PRIMARY KEY',
            'name': 'VARCHAR(100) NOT NULL',
            'email': 'VARCHAR(120)',
            'phone': 'VARCHAR(20)',
            'role': 'VARCHAR(50)',
            'department': 'VARCHAR(50)',
            'notification_types': 'VARCHAR(100)',
            'event_types': 'TEXT',
            'po_events': 'BOOLEAN DEFAULT 0',
            'grn_events': 'BOOLEAN DEFAULT 0',
            'job_work_events': 'BOOLEAN DEFAULT 0',
            'production_events': 'BOOLEAN DEFAULT 0',
            'sales_events': 'BOOLEAN DEFAULT 0',
            'accounts_events': 'BOOLEAN DEFAULT 0',
            'inventory_events': 'BOOLEAN DEFAULT 0',
            'immediate_notifications': 'BOOLEAN DEFAULT 1',
            'daily_summary': 'BOOLEAN DEFAULT 0',
            'weekly_summary': 'BOOLEAN DEFAULT 0',
            'is_active': 'BOOLEAN DEFAULT 1',
            'is_external': 'BOOLEAN DEFAULT 0',
            'created_at': 'DATETIME',
            'updated_at': 'DATETIME'
        },
        'notification_settings': {
            'id': 'INTEGER PRIMARY KEY',
            'email_enabled': 'BOOLEAN DEFAULT 1',
            'sms_enabled': 'BOOLEAN DEFAULT 1',
            'whatsapp_enabled': 'BOOLEAN DEFAULT 1',
            'in_app_enabled': 'BOOLEAN DEFAULT 1',
            'sendgrid_api_key': 'VARCHAR(255)',
            'sender_email': 'VARCHAR(120)',
            'sender_name': 'VARCHAR(100)',
            'twilio_account_sid': 'VARCHAR(255)',
            'twilio_auth_token': 'VARCHAR(255)',
            'twilio_phone_number': 'VARCHAR(20)',
            'po_notifications': 'BOOLEAN DEFAULT 1',
            'grn_notifications': 'BOOLEAN DEFAULT 1',
            'job_work_notifications': 'BOOLEAN DEFAULT 1',
            'production_notifications': 'BOOLEAN DEFAULT 1',
            'sales_notifications': 'BOOLEAN DEFAULT 1',
            'accounts_notifications': 'BOOLEAN DEFAULT 1',
            'inventory_notifications': 'BOOLEAN DEFAULT 1',
            'po_vendor_notification': 'BOOLEAN DEFAULT 1',
            'grn_rejection_notification': 'BOOLEAN DEFAULT 1',
            'job_work_vendor_notification': 'BOOLEAN DEFAULT 1',
            'customer_invoice_notification': 'BOOLEAN DEFAULT 1',
            'payment_overdue_notification': 'BOOLEAN DEFAULT 1',
            'low_stock_notifications': 'BOOLEAN DEFAULT 1',
            'scrap_threshold_notifications': 'BOOLEAN DEFAULT 1',
            'default_language': 'VARCHAR(5) DEFAULT "EN"',
            'time_format': 'VARCHAR(10) DEFAULT "24H"',
            'notification_summary': 'VARCHAR(20) DEFAULT "immediate"',
            'admin_email': 'VARCHAR(120)',
            'admin_phone': 'VARCHAR(20)',
            'created_at': 'DATETIME',
            'updated_at': 'DATETIME'
        }
    }

def check_and_fix_notification_tables():
    """Check all notification tables and add missing columns"""
    db_path = 'instance/factory.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
    
    table_schemas = get_notification_table_schemas()
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for table_name, expected_columns in table_schemas.items():
            print(f"\n--- Checking {table_name} ---")
            
            # Check if table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                print(f"{table_name} table does not exist - will be created by Flask app")
                continue
            
            # Get current table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            print(f"Current columns: {column_names}")
            print(f"Expected columns: {list(expected_columns.keys())}")
            
            # Find missing columns
            missing_columns = [col for col in expected_columns.keys() if col not in column_names]
            
            if missing_columns:
                print(f"Missing columns: {missing_columns}")
                
                # Add missing columns one by one
                for col_name in missing_columns:
                    col_definition = expected_columns[col_name]
                    try:
                        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_definition};")
                        print(f"Added column: {col_name}")
                    except Exception as e:
                        print(f"Error adding column {col_name}: {e}")
                
                conn.commit()
                print(f"Successfully updated {table_name}")
            else:
                print(f"All required columns are present in {table_name}")
        
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
    print("Checking and fixing all notification tables...")
    
    # First try to fix the existing tables
    if check_and_fix_notification_tables():
        print("Database fix completed successfully")
    else:
        print("Failed to fix existing tables, trying to recreate all tables...")
        if recreate_tables():
            print("Tables recreated successfully")
        else:
            print("Failed to recreate tables")