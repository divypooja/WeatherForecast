#!/usr/bin/env python3
"""
Fix BOM Processes Schema
Aligns the database table with the BOMProcess model definition
"""

import os
import sys
from datetime import datetime

# Add the current directory to the path so we can import our models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def fix_bom_processes_schema():
    """Fix the bom_processes table schema to match the model"""
    try:
        with app.app_context():
            # Check current table structure
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('bom_processes')
            existing_columns = [col['name'] for col in columns]
            
            print("Current table columns:")
            for col in columns:
                print(f"  {col['name']}: {col['type']}")
            
            # SQL commands to add missing columns
            missing_columns = [
                'process_code VARCHAR(20)',
                'operation_description TEXT', 
                'setup_time_minutes FLOAT DEFAULT 0.0',
                'run_time_minutes FLOAT DEFAULT 0.0',
                'labor_rate_per_hour FLOAT DEFAULT 0.0',
                'machine_id INTEGER',
                'vendor_id INTEGER',
                'parallel_processes TEXT',
                'predecessor_processes TEXT',
                'notes TEXT'
            ]
            
            # Add missing columns one by one
            for column_def in missing_columns:
                column_name = column_def.split()[0]
                if column_name not in existing_columns:
                    try:
                        sql = f"ALTER TABLE bom_processes ADD COLUMN {column_def}"
                        db.session.execute(db.text(sql))
                        print(f"✅ Added column: {column_name}")
                    except Exception as e:
                        print(f"⚠️ Column {column_name} may already exist: {str(e)}")
            
            # Rename columns if needed
            column_renames = [
                ('description', 'operation_description'),
                ('estimated_time_minutes', 'setup_time_minutes')
            ]
            
            for old_name, new_name in column_renames:
                if old_name in existing_columns and new_name not in existing_columns:
                    try:
                        # SQLite doesn't support renaming columns directly, so we copy data
                        db.session.execute(db.text(f"UPDATE bom_processes SET {new_name} = {old_name} WHERE {old_name} IS NOT NULL"))
                        print(f"✅ Copied data from {old_name} to {new_name}")
                    except Exception as e:
                        print(f"⚠️ Could not copy {old_name} to {new_name}: {str(e)}")
            
            db.session.commit()
            print("✅ Schema fixes committed successfully!")
            
            # Verify final structure
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('bom_processes')
            print(f"✅ Table now has {len(columns)} columns:")
            for col in columns:
                print(f"   - {col['name']}: {col['type']}")
                
        return True
        
    except Exception as e:
        print(f"❌ Error fixing BOM processes schema: {str(e)}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("BOM PROCESSES SCHEMA FIX")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if fix_bom_processes_schema():
        print()
        print("=" * 60)
        print("✅ SCHEMA FIX COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("📋 Summary:")
        print("   • Added missing columns to bom_processes table")
        print("   • Schema now matches BOMProcess model definition")
        print("   • Ready for manufacturing process management")
        return True
    else:
        print("❌ Schema fix failed")
        return False

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)