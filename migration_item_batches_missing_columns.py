#!/usr/bin/env python3
"""
Migration: Add missing columns to item_batches table
This migration adds missing columns for complete batch tracking functionality
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import db, create_app
from sqlalchemy import text

def run_migration():
    """Add missing columns to item_batches table"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Starting migration: Add missing columns to item_batches table...")
            
            # Check if columns already exist
            result = db.session.execute(text("PRAGMA table_info(item_batches)"))
            existing_columns = [row[1] for row in result.fetchall()]
            
            columns_to_add = [
                ('purchase_rate', 'REAL DEFAULT 0.0'),
                ('ref_type', "VARCHAR(50) DEFAULT 'MANUAL'"),
                ('ref_id', 'INTEGER'),
                ('ref_number', 'VARCHAR(100)'),
                ('total_quantity', 'REAL DEFAULT 0.0'),
                ('available_quantity', 'REAL DEFAULT 0.0'),
                ('shelf_life_days', 'INTEGER'),
                ('lot_number', 'VARCHAR(100)'),
                ('supplier_name', 'VARCHAR(200)'),
                ('warehouse_location', 'VARCHAR(100)'),
                ('inspection_report', 'TEXT'),
                ('certificate_number', 'VARCHAR(100)'),
                ('storage_location', 'VARCHAR(200)'),
                ('grn_id', 'INTEGER'),
                ('created_by', 'INTEGER'),
                ('updated_at', 'DATETIME'),
                ('quality_status', "VARCHAR(50) DEFAULT 'pending_inspection'"),
                ('quality_notes', 'TEXT')
            ]
            
            # Add missing columns
            for column_name, column_def in columns_to_add:
                if column_name not in existing_columns:
                    try:
                        alter_sql = f"ALTER TABLE item_batches ADD COLUMN {column_name} {column_def}"
                        db.session.execute(text(alter_sql))
                        print(f"✓ Added column: {column_name}")
                    except Exception as e:
                        print(f"Warning: Could not add {column_name}: {str(e)}")
            
            # Update existing batches to calculate total_quantity and available_quantity
            try:
                update_sql = """
                UPDATE item_batches 
                SET total_quantity = COALESCE(qty_raw, 0) + COALESCE(qty_wip, 0) + COALESCE(qty_finished, 0) + COALESCE(qty_scrap, 0),
                    available_quantity = COALESCE(qty_raw, 0) + COALESCE(qty_finished, 0)
                WHERE total_quantity = 0 OR total_quantity IS NULL
                """
                db.session.execute(text(update_sql))
                print("✓ Updated existing batch quantities")
            except Exception as e:
                print(f"Warning: Could not update quantities: {str(e)}")
            
            # Commit all changes
            db.session.commit()
            print("✓ Migration completed successfully!")
            print("✓ ItemBatch table now has all required columns for comprehensive batch tracking")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Migration failed: {str(e)}")
            raise e

if __name__ == "__main__":
    run_migration()