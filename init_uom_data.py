#!/usr/bin/env python3
"""
Initialize essential UOM (Unit of Measure) data for BOM functionality
"""
import os
from main import app

def init_uom_data():
    with app.app_context():
        from models_uom import UnitOfMeasure
        from models import db
        
        print("🔄 Initializing essential UOM data...")
        
        # Essential UOM data for BOM functionality
        essential_uoms = [
            {'name': 'Pieces', 'symbol': 'Pcs', 'category': 'Count', 'is_base_unit': True},
            {'name': 'Numbers', 'symbol': 'Nos', 'category': 'Count', 'is_base_unit': False},
            {'name': 'Kilogram', 'symbol': 'Kg', 'category': 'Weight', 'is_base_unit': True},
            {'name': 'Gram', 'symbol': 'g', 'category': 'Weight', 'is_base_unit': False},
            {'name': 'Meter', 'symbol': 'M', 'category': 'Length', 'is_base_unit': True},
            {'name': 'Centimeter', 'symbol': 'cm', 'category': 'Length', 'is_base_unit': False},
            {'name': 'Liter', 'symbol': 'L', 'category': 'Volume', 'is_base_unit': True},
            {'name': 'Milliliter', 'symbol': 'ml', 'category': 'Volume', 'is_base_unit': False},
            {'name': 'Square Meter', 'symbol': 'sqm', 'category': 'Area', 'is_base_unit': True},
            {'name': 'Square Feet', 'symbol': 'sqft', 'category': 'Area', 'is_base_unit': False}
        ]
        
        created_count = 0
        
        for uom_data in essential_uoms:
            # Check if UOM already exists
            existing = UnitOfMeasure.query.filter_by(symbol=uom_data['symbol']).first()
            if not existing:
                uom = UnitOfMeasure(**uom_data)
                db.session.add(uom)
                created_count += 1
                print(f"✅ Created UOM: {uom_data['name']} ({uom_data['symbol']})")
            else:
                print(f"⚠️  UOM already exists: {uom_data['name']} ({uom_data['symbol']})")
        
        if created_count > 0:
            db.session.commit()
            print(f"🎉 Successfully created {created_count} UOM records!")
        else:
            print("ℹ️  All essential UOMs already exist in database")

if __name__ == '__main__':
    init_uom_data()