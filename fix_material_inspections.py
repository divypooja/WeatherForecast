#!/usr/bin/env python3
"""
Fix Material Inspections table - add missing columns for batch tracking
"""

from app import app, db
from sqlalchemy import text

def fix_material_inspections():
    """Add missing columns to material_inspections table"""
    with app.app_context():
        try:
            # Check if columns exist first
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('material_inspections')]
            
            missing_columns = []
            required_columns = {
                'received_uom': 'VARCHAR(20)',
                'inspected_uom': 'VARCHAR(20)', 
                'passed_uom': 'VARCHAR(20)',
                'damaged_uom': 'VARCHAR(20)',
                'rejected_uom': 'VARCHAR(20)',
                'scrap_uom': 'VARCHAR(20)'
            }
            
            for col_name, col_type in required_columns.items():
                if col_name not in columns:
                    missing_columns.append((col_name, col_type))
            
            if missing_columns:
                print(f"Adding {len(missing_columns)} missing columns to material_inspections table...")
                for col_name, col_type in missing_columns:
                    try:
                        db.session.execute(text(f"ALTER TABLE material_inspections ADD COLUMN {col_name} {col_type}"))
                        print(f"✓ Added column: {col_name}")
                    except Exception as e:
                        print(f"✗ Failed to add {col_name}: {e}")
                
                db.session.commit()
                print("✓ Material inspections table fixed successfully!")
            else:
                print("✓ Material inspections table already has all required columns")
                
        except Exception as e:
            print(f"Error fixing material inspections: {e}")
            db.session.rollback()

if __name__ == "__main__":
    fix_material_inspections()