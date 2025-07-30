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
            # Find BOMs with missing codes
            boms_without_codes = BOM.query.filter(
                (BOM.bom_code.is_(None)) | (BOM.bom_code == '')
            ).all()
            
            print(f"Found {len(boms_without_codes)} BOMs with missing codes")
            
            for bom in boms_without_codes:
                # Generate a new BOM code
                if bom.product:
                    # Use product name for code generation
                    base_code = bom.product.name[:3].upper()
                    counter = 1
                    new_code = f"BOM-{base_code}-{counter:03d}"
                    
                    # Ensure uniqueness
                    while BOM.query.filter_by(bom_code=new_code).first():
                        counter += 1
                        new_code = f"BOM-{base_code}-{counter:03d}"
                else:
                    # Fallback to BOM-ID format
                    new_code = f"BOM-{bom.id:04d}"
                    
                    # Ensure uniqueness
                    counter = 1
                    while BOM.query.filter_by(bom_code=new_code).first():
                        new_code = f"BOM-{bom.id:04d}-{counter}"
                        counter += 1
                
                bom.bom_code = new_code
                print(f"Fixed BOM ID {bom.id}: assigned code '{new_code}'")
            
            db.session.commit()
            print("All BOM codes fixed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error fixing BOM codes: {e}")
            raise

if __name__ == '__main__':
    fix_missing_bom_codes()