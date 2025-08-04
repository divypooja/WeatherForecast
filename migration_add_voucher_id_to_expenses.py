#!/usr/bin/env python3
"""
Add voucher_id column to factory_expenses table
"""

from app import app, db
import sqlite3

def add_voucher_id_column():
    """Add voucher_id column to factory_expenses table"""
    with app.app_context():
        try:
            # Check if column already exists using text() for raw SQL
            from sqlalchemy import text
            
            result = db.session.execute(text("PRAGMA table_info(factory_expenses)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'voucher_id' not in columns:
                print("Adding voucher_id column to factory_expenses table...")
                db.session.execute(text("ALTER TABLE factory_expenses ADD COLUMN voucher_id INTEGER"))
                db.session.commit()
                print("✅ Successfully added voucher_id column")
            else:
                print("✅ voucher_id column already exists")
                
        except Exception as e:
            print(f"❌ Error adding voucher_id column: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    add_voucher_id_column()