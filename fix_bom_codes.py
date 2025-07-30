#!/usr/bin/env python3
"""
Fix BOMs with missing bom_code values
"""

from app import app, db
from models import BOM
from datetime import datetime

def fix_missing_bom_codes():
    """Fix BOMs that have NULL or empty bom_code"""
    with app.app_context():
        try:
            # Find BOMs with missing codes - use raw SQL to be more thorough
            from sqlalchemy import text
            result = db.session.execute(text("SELECT id, bom_code, product_id FROM boms WHERE bom_code IS NULL OR bom_code = ''"))
            problematic_boms = result.fetchall()
            
            print(f"Found {len(problematic_boms)} BOMs with missing codes using raw SQL")
            
            # Also check using ORM
            boms_without_codes = BOM.query.filter(
                (BOM.bom_code.is_(None)) | (BOM.bom_code == '')
            ).all()
            print(f"Found {len(boms_without_codes)} BOMs with missing codes using ORM")
            
            # Fix problematic BOMs directly with SQL
            for row in problematic_boms:
                bom_id, current_code, product_id = row
                print(f"Processing BOM ID {bom_id} with code '{current_code}' and product_id {product_id}")
                
                # Generate a new BOM code
                new_code = f"BOM-{bom_id:04d}"
                counter = 1
                
                # Check if code exists
                existing = db.session.execute(text("SELECT id FROM boms WHERE bom_code = :code"), {"code": new_code}).fetchone()
                while existing:
                    new_code = f"BOM-{bom_id:04d}-{counter}"
                    existing = db.session.execute(text("SELECT id FROM boms WHERE bom_code = :code"), {"code": new_code}).fetchone()
                    counter += 1
                
                # Update the BOM with new code
                db.session.execute(text("UPDATE boms SET bom_code = :code WHERE id = :id"), 
                                 {"code": new_code, "id": bom_id})
                print(f"Fixed BOM ID {bom_id}: assigned code '{new_code}'")
            
            db.session.commit()
            print("All BOM codes fixed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error fixing BOM codes: {e}")
            raise

if __name__ == '__main__':
    fix_missing_bom_codes()