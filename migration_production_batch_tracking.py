#!/usr/bin/env python3
"""
Migration: Add batch tracking columns to productions table
This migration adds comprehensive batch tracking functionality to the Production model
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import db, create_app
from models import Production, ProductionBatch
from sqlalchemy import text

def run_migration():
    """Add batch tracking columns to productions table"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Starting migration: Add batch tracking to productions table...")
            
            # Check if columns already exist
            result = db.session.execute(text("PRAGMA table_info(productions)"))
            existing_columns = [row[1] for row in result.fetchall()]
            
            columns_to_add = [
                ('batch_tracking_enabled', 'BOOLEAN DEFAULT 0'),
                ('output_batch_id', 'INTEGER'),
                ('bom_id', 'INTEGER'),
                ('production_shift', "VARCHAR(20) DEFAULT 'day'"),
                ('operator_id', 'INTEGER'),
                ('quality_control_passed', 'BOOLEAN DEFAULT 0'),
                ('updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
            ]
            
            # Add missing columns
            for column_name, column_def in columns_to_add:
                if column_name not in existing_columns:
                    try:
                        alter_sql = f"ALTER TABLE productions ADD COLUMN {column_name} {column_def}"
                        db.session.execute(text(alter_sql))
                        print(f"✓ Added column: {column_name}")
                    except Exception as e:
                        print(f"Warning: Could not add {column_name}: {str(e)}")
            
            # Create production_batches table if it doesn't exist
            try:
                db.session.execute(text("""
                    CREATE TABLE IF NOT EXISTS production_batches (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        production_id INTEGER NOT NULL,
                        material_batch_id INTEGER NOT NULL,
                        quantity_consumed REAL NOT NULL,
                        quantity_remaining REAL DEFAULT 0.0,
                        consumption_date DATE DEFAULT CURRENT_DATE,
                        bom_item_id INTEGER,
                        notes TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (production_id) REFERENCES productions (id),
                        FOREIGN KEY (material_batch_id) REFERENCES item_batches (id),
                        FOREIGN KEY (bom_item_id) REFERENCES bom_items (id)
                    )
                """))
                print("✓ Created production_batches table")
            except Exception as e:
                print(f"Warning: Production batches table creation: {str(e)}")
            
            # Add foreign key constraints if not exist
            foreign_keys = [
                ("productions", "output_batch_id", "item_batches", "id"),
                ("productions", "bom_id", "boms", "id"),
                ("productions", "operator_id", "users", "id")
            ]
            
            for table, column, ref_table, ref_column in foreign_keys:
                try:
                    # SQLite doesn't support adding foreign keys to existing tables
                    # This is handled through the relationship definitions in SQLAlchemy
                    pass
                except Exception as e:
                    print(f"Note: Foreign key constraint {table}.{column}: {str(e)}")
            
            # Commit all changes
            db.session.commit()
            print("✓ Migration completed successfully!")
            print("✓ Productions table now supports comprehensive batch tracking")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Migration failed: {str(e)}")
            raise e

if __name__ == "__main__":
    run_migration()