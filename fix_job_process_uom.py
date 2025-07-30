#!/usr/bin/env python3
"""
Fix job_work_processes table by adding missing UOM columns
"""

from app import app, db
from sqlalchemy import text

def fix_job_processes_schema():
    """Add missing UOM columns to job_work_processes table"""
    with app.app_context():
        try:
            # Check if columns exist first
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('job_work_processes')]
            
            # Add missing columns
            if 'input_uom' not in columns:
                db.session.execute(text("ALTER TABLE job_work_processes ADD COLUMN input_uom VARCHAR(20)"))
                print("✓ Added input_uom column")
            
            if 'output_uom' not in columns:
                db.session.execute(text("ALTER TABLE job_work_processes ADD COLUMN output_uom VARCHAR(20)"))
                print("✓ Added output_uom column")
                
            if 'scrap_uom' not in columns:
                db.session.execute(text("ALTER TABLE job_work_processes ADD COLUMN scrap_uom VARCHAR(20)"))
                print("✓ Added scrap_uom column")
            
            db.session.commit()
            print("✅ Job work processes schema updated successfully")
            
        except Exception as e:
            print(f"❌ Error updating schema: {e}")
            db.session.rollback()

def initialize_dynamic_templates():
    """Initialize dynamic form templates"""
    try:
        from models_dynamic_forms import DynamicFormManager
        DynamicFormManager.create_default_templates()
        print("✅ Dynamic form templates initialized")
    except Exception as e:
        print(f"❌ Error initializing templates: {e}")

if __name__ == "__main__":
    print("🔧 Fixing job_work_processes schema and initializing dynamic forms...")
    fix_job_processes_schema()
    initialize_dynamic_templates()
    print("🎉 Setup complete!")