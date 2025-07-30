#!/usr/bin/env python3
"""
Migration script to add BOM integration fields to JobWork model
Run this once to update the database schema
"""

from app import app, db
from sqlalchemy import text

def add_bom_integration_columns():
    """Add BOM integration columns to job_works table"""
    with app.app_context():
        try:
            # Check if columns already exist by trying to select them
            try:
                db.session.execute(text("SELECT bom_id FROM job_works LIMIT 1"))
                print("bom_id column already exists")
            except Exception:
                # Column doesn't exist, add it
                db.session.execute(text("ALTER TABLE job_works ADD COLUMN bom_id INTEGER"))
                print("Added bom_id column to job_works table")
            
            try:
                db.session.execute(text("SELECT production_quantity FROM job_works LIMIT 1"))
                print("production_quantity column already exists")
            except Exception:
                # Column doesn't exist, add it
                db.session.execute(text("ALTER TABLE job_works ADD COLUMN production_quantity INTEGER"))
                print("Added production_quantity column to job_works table")
                
            db.session.commit()
            print("BOM integration columns migration completed successfully!")
            
        except Exception as e:
            print(f"Migration failed: {e}")
            db.session.rollback()

if __name__ == "__main__":
    add_bom_integration_columns()