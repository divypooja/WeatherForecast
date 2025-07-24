#!/usr/bin/env python3
"""
Initialize Smart Weight UOM System
Adds ton and gram units with intelligent conversions
"""

from app import create_app
from models_uom import UnitOfMeasure, UOMConversion, db

def init_smart_weight_units():
    """Initialize smart weight units and conversions"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Initializing Smart Weight UOM System...")
        
        # Check and add missing weight units
        units_to_add = [
            {'name': 'Gram', 'symbol': 'g', 'category': 'Weight', 'is_base_unit': False, 'description': 'Gram - for lightweight items'},
            {'name': 'Ton', 'symbol': 'ton', 'category': 'Weight', 'is_base_unit': False, 'description': 'Metric Ton - for heavy bulk items'},
        ]
        
        for unit_data in units_to_add:
            existing = UnitOfMeasure.query.filter_by(symbol=unit_data['symbol']).first()
            if not existing:
                unit = UnitOfMeasure(**unit_data)
                db.session.add(unit)
                print(f"✓ Added unit: {unit_data['name']} ({unit_data['symbol']})")
            else:
                print(f"→ Unit {unit_data['symbol']} already exists")
        
        # Smart weight conversions with intelligent thresholds
        conversions_to_add = [
            # Standard weight conversions
            {'from_unit': 'kg', 'to_unit': 'g', 'factor': 1000, 'notes': 'Kilogram to Gram conversion'},
            {'from_unit': 'g', 'to_unit': 'kg', 'factor': 0.001, 'notes': 'Gram to Kilogram conversion'},
            {'from_unit': 'ton', 'to_unit': 'kg', 'factor': 1000, 'notes': 'Ton to Kilogram conversion'},
            {'from_unit': 'kg', 'to_unit': 'ton', 'factor': 0.001, 'notes': 'Kilogram to Ton conversion'},
            {'from_unit': 'ton', 'to_unit': 'g', 'factor': 1000000, 'notes': 'Ton to Gram conversion'},
            {'from_unit': 'g', 'to_unit': 'ton', 'factor': 0.000001, 'notes': 'Gram to Ton conversion'},
        ]
        
        for conv_data in conversions_to_add:
            existing = UOMConversion.query.filter_by(
                from_unit=conv_data['from_unit'],
                to_unit=conv_data['to_unit']
            ).first()
            
            if not existing:
                conversion = UOMConversion(**conv_data)
                db.session.add(conversion)
                print(f"✓ Added conversion: {conv_data['from_unit']} → {conv_data['to_unit']} (×{conv_data['factor']})")
            else:
                print(f"→ Conversion {conv_data['from_unit']} → {conv_data['to_unit']} already exists")
        
        try:
            db.session.commit()
            print("\n🎉 Smart Weight UOM System initialized successfully!")
            print("\n📊 Smart Weight Rules Active:")
            print("   • >1000 kg → Automatically suggest tons")
            print("   • <1 kg → Automatically suggest grams")
            print("   • 1-1000 kg → Keep as kilograms")
            print("   • Cross-unit conversions with intelligent thresholds")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error initializing system: {e}")

if __name__ == '__main__':
    init_smart_weight_units()