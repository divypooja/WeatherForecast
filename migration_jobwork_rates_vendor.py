#!/usr/bin/env python3
"""
Migration script to add vendor_name column to job_work_rates table
"""

from app import app, db
from models import JobWorkRate
from sqlalchemy import text

def migrate_jobwork_rates_vendor():
    """Add vendor_name column to job_work_rates table"""
    with app.app_context():
        try:
            # Check if column already exists using SQLite pragma
            result = db.session.execute(text("PRAGMA table_info(job_work_rates)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'vendor_name' in columns:
                print("✓ vendor_name column already exists in job_work_rates table")
                return
            
            # Add the vendor_name column
            db.session.execute(text("""
                ALTER TABLE job_work_rates 
                ADD COLUMN vendor_name VARCHAR(200)
            """))
            
            db.session.commit()
            print("✓ Successfully added vendor_name column to job_work_rates table")
            
        except Exception as e:
            print(f"✗ Error adding vendor_name column: {e}")
            db.session.rollback()

if __name__ == '__main__':
    migrate_jobwork_rates_vendor()