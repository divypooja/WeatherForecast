#!/usr/bin/env python3
"""
Update BOM table schema to add multi-level BOM columns
"""
import os
from main import app

def update_schema():
    with app.app_context():
        from models import db
        
        print("🔄 Updating BOM table schema for multi-level functionality...")
        
        # Get database connection
        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        
        try:
            # Check if columns exist and add them if they don't
            columns_to_add = [
                ("parent_bom_id", "INTEGER DEFAULT NULL"),
                ("bom_level", "INTEGER DEFAULT 0"), 
                ("is_phantom_bom", "BOOLEAN DEFAULT FALSE"),
                ("intermediate_product", "BOOLEAN DEFAULT FALSE")
            ]
            
            for column_name, column_def in columns_to_add:
                try:
                    # Try to add the column
                    cursor.execute(f"ALTER TABLE boms ADD COLUMN {column_name} {column_def}")
                    print(f"✅ Added column: {column_name}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"⚠️  Column {column_name} already exists")
                    else:
                        print(f"❌ Error adding {column_name}: {e}")
            
            # Create index for parent_bom_id for better performance
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_boms_parent_bom_id ON boms(parent_bom_id)")
                print("✅ Created index for parent_bom_id")
            except Exception as e:
                print(f"⚠️  Index creation: {e}")
            
            # Update existing BOMs to have default values
            try:
                cursor.execute("UPDATE boms SET bom_level = 0 WHERE bom_level IS NULL")
                cursor.execute("UPDATE boms SET is_phantom_bom = FALSE WHERE is_phantom_bom IS NULL")
                cursor.execute("UPDATE boms SET intermediate_product = FALSE WHERE intermediate_product IS NULL")
                print("✅ Updated existing BOMs with default values")
            except Exception as e:
                print(f"⚠️  Update existing records: {e}")
            
            connection.commit()
            print("🎉 BOM schema update completed successfully!")
            
        except Exception as e:
            print(f"❌ Schema update failed: {e}")
            connection.rollback()
        finally:
            cursor.close()
            connection.close()

if __name__ == '__main__':
    update_schema()