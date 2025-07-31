#!/usr/bin/env python3
"""
Migration: Add material_destination column to purchase_order_items table
Date: July 31, 2025
Purpose: Allow differentiation of incoming materials (raw material, finished goods, WIP, scrap)
"""

from app import app, db
from sqlalchemy import text

def run_migration():
    """Add material_destination column to purchase_order_items table"""
    
    with app.app_context():
        try:
            # Check if column already exists (SQLite version)
            result = db.session.execute(text("""
                PRAGMA table_info(purchase_order_items)
            """))
            
            columns = [row[1] for row in result.fetchall()]  # column names are in index 1
            if 'material_destination' in columns:
                print("✓ material_destination column already exists in purchase_order_items table")
                return
            
            # Add the column
            print("Adding material_destination column to purchase_order_items table...")
            db.session.execute(text("""
                ALTER TABLE purchase_order_items 
                ADD COLUMN material_destination VARCHAR(20) DEFAULT 'raw_material'
            """))
            
            # Update existing records to have default value
            print("Setting default values for existing records...")
            db.session.execute(text("""
                UPDATE purchase_order_items 
                SET material_destination = 'raw_material' 
                WHERE material_destination IS NULL
            """))
            
            db.session.commit()
            print("✓ Migration completed successfully!")
            print("  - Added material_destination column to purchase_order_items table")
            print("  - Set default value 'raw_material' for all existing records")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    print("=== Purchase Order Material Destination Migration ===")
    run_migration()
    print("=== Migration Complete ===")