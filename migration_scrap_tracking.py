#!/usr/bin/env python3
"""
Database Migration Script for Comprehensive Scrap Tracking System
Adds scrap tracking fields across Production, JobWork, and related models
"""

from app import app, db
from sqlalchemy import text
import sys

def migrate_scrap_tracking():
    """Add scrap tracking fields to database tables"""
    
    with app.app_context():
        try:
            print("Starting scrap tracking migration...")
            
            # Production table scrap tracking columns
            production_migrations = [
                "ALTER TABLE productions ADD COLUMN good_uom TEXT DEFAULT 'pcs'",
                "ALTER TABLE productions ADD COLUMN damaged_uom TEXT DEFAULT 'pcs'", 
                "ALTER TABLE productions ADD COLUMN scrap_quantity REAL DEFAULT 0.0",
                "ALTER TABLE productions ADD COLUMN scrap_uom TEXT DEFAULT 'kg'"
            ]
            
            # JobWork table enhanced scrap tracking
            jobwork_migrations = [
                "ALTER TABLE job_works ADD COLUMN finished_uom TEXT DEFAULT 'pcs'",
                "ALTER TABLE job_works ADD COLUMN expected_scrap_uom TEXT DEFAULT 'kg'"
            ]
            
            # QualityControlLog scrap tracking
            quality_migrations = [
                "ALTER TABLE quality_control_logs ADD COLUMN scrap_quantity REAL DEFAULT 0.0",
                "ALTER TABLE quality_control_logs ADD COLUMN scrap_uom TEXT DEFAULT 'kg'"
            ]
            
            # GRN scrap tracking enhancement
            grn_migrations = [
                "ALTER TABLE grn_line_items ADD COLUMN scrap_uom TEXT DEFAULT 'kg'"
            ]
            
            all_migrations = production_migrations + jobwork_migrations + quality_migrations + grn_migrations
            
            for migration in all_migrations:
                try:
                    print(f"Executing: {migration}")
                    db.session.execute(text(migration))
                    db.session.commit()
                    print("✓ Success")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"⚠ Column already exists - skipping")
                        db.session.rollback()
                    else:
                        print(f"✗ Error: {e}")
                        db.session.rollback()
                        
            print("\n✅ Scrap tracking migration completed successfully!")
            print("\nNew fields added:")
            print("- Production: good_uom, damaged_uom, scrap_quantity, scrap_uom")
            print("- JobWork: finished_uom, expected_scrap_uom") 
            print("- QualityControlLog: scrap_quantity, scrap_uom")
            print("- GRNLineItem: scrap_uom")
            
        except Exception as e:
            print(f"Migration failed: {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == "__main__":
    migrate_scrap_tracking()