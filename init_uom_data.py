#!/usr/bin/env python3
"""
Initialize UOM (Unit of Measure) system with common units and example conversions
Run this script to set up basic UOM data for your factory management system
"""

from app import app, db
from models_uom import UnitOfMeasure, UOMConversion, ItemUOMConversion
from models import Item

def create_basic_units():
    """Create basic units of measure"""
    units_data = [
        # Weight units
        {'name': 'Kilogram', 'symbol': 'Kg', 'category': 'Weight', 'is_base_unit': True, 'description': 'Base unit for weight measurements'},
        {'name': 'Gram', 'symbol': 'g', 'category': 'Weight', 'is_base_unit': False, 'description': 'Smaller weight unit'},
        {'name': 'Ton', 'symbol': 'T', 'category': 'Weight', 'is_base_unit': False, 'description': 'Large weight unit'},
        
        # Count units
        {'name': 'Pieces', 'symbol': 'Pcs', 'category': 'Count', 'is_base_unit': True, 'description': 'Individual items or pieces'},
        {'name': 'Units', 'symbol': 'Units', 'category': 'Count', 'is_base_unit': False, 'description': 'Generic counting unit'},
        {'name': 'Dozen', 'symbol': 'Doz', 'category': 'Count', 'is_base_unit': False, 'description': 'Set of 12 items'},
        
        # Length units
        {'name': 'Meter', 'symbol': 'M', 'category': 'Length', 'is_base_unit': True, 'description': 'Base unit for length measurements'},
        {'name': 'Centimeter', 'symbol': 'cm', 'category': 'Length', 'is_base_unit': False, 'description': 'Smaller length unit'},
        {'name': 'Millimeter', 'symbol': 'mm', 'category': 'Length', 'is_base_unit': False, 'description': 'Small precision length unit'},
        {'name': 'Feet', 'symbol': 'ft', 'category': 'Length', 'is_base_unit': False, 'description': 'Imperial length unit'},
        
        # Volume units
        {'name': 'Liter', 'symbol': 'L', 'category': 'Volume', 'is_base_unit': True, 'description': 'Base unit for volume measurements'},
        {'name': 'Milliliter', 'symbol': 'ml', 'category': 'Volume', 'is_base_unit': False, 'description': 'Smaller volume unit'},
        {'name': 'Gallon', 'symbol': 'gal', 'category': 'Volume', 'is_base_unit': False, 'description': 'Large volume unit'},
        
        # Area units
        {'name': 'Square Meter', 'symbol': 'sq.m', 'category': 'Area', 'is_base_unit': True, 'description': 'Base unit for area measurements'},
        {'name': 'Square Feet', 'symbol': 'sq.ft', 'category': 'Area', 'is_base_unit': False, 'description': 'Imperial area unit'},
    ]
    
    created_units = {}
    for unit_data in units_data:
        # Check if unit already exists
        existing = UnitOfMeasure.query.filter_by(symbol=unit_data['symbol']).first()
        if not existing:
            unit = UnitOfMeasure(**unit_data)
            db.session.add(unit)
            db.session.flush()  # Get the ID
            created_units[unit_data['symbol']] = unit
            print(f"Created unit: {unit.name} ({unit.symbol})")
        else:
            created_units[unit_data['symbol']] = existing
            print(f"Unit already exists: {existing.name} ({existing.symbol})")
    
    return created_units

def create_basic_conversions(units):
    """Create basic unit conversions"""
    conversions_data = [
        # Weight conversions
        {'from': 'Kg', 'to': 'g', 'factor': 1000, 'notes': 'Standard metric conversion'},
        {'from': 'g', 'to': 'Kg', 'factor': 0.001, 'notes': 'Standard metric conversion'},
        {'from': 'T', 'to': 'Kg', 'factor': 1000, 'notes': 'Standard metric conversion'},
        {'from': 'Kg', 'to': 'T', 'factor': 0.001, 'notes': 'Standard metric conversion'},
        
        # Count conversions
        {'from': 'Doz', 'to': 'Pcs', 'factor': 12, 'notes': 'Standard dozen conversion'},
        {'from': 'Pcs', 'to': 'Doz', 'factor': 0.0833333, 'notes': 'Standard dozen conversion'},
        
        # Length conversions
        {'from': 'M', 'to': 'cm', 'factor': 100, 'notes': 'Standard metric conversion'},
        {'from': 'cm', 'to': 'M', 'factor': 0.01, 'notes': 'Standard metric conversion'},
        {'from': 'M', 'to': 'mm', 'factor': 1000, 'notes': 'Standard metric conversion'},
        {'from': 'mm', 'to': 'M', 'factor': 0.001, 'notes': 'Standard metric conversion'},
        {'from': 'ft', 'to': 'M', 'factor': 0.3048, 'notes': 'Imperial to metric conversion'},
        {'from': 'M', 'to': 'ft', 'factor': 3.28084, 'notes': 'Metric to imperial conversion'},
        
        # Volume conversions
        {'from': 'L', 'to': 'ml', 'factor': 1000, 'notes': 'Standard metric conversion'},
        {'from': 'ml', 'to': 'L', 'factor': 0.001, 'notes': 'Standard metric conversion'},
        {'from': 'gal', 'to': 'L', 'factor': 3.78541, 'notes': 'US gallon to liter'},
        {'from': 'L', 'to': 'gal', 'factor': 0.264172, 'notes': 'Liter to US gallon'},
        
        # Area conversions
        {'from': 'sq.ft', 'to': 'sq.m', 'factor': 0.092903, 'notes': 'Imperial to metric area'},
        {'from': 'sq.m', 'to': 'sq.ft', 'factor': 10.7639, 'notes': 'Metric to imperial area'},
    ]
    
    for conv_data in conversions_data:
        from_unit = units.get(conv_data['from'])
        to_unit = units.get(conv_data['to'])
        
        if from_unit and to_unit:
            # Check if conversion already exists
            existing = UOMConversion.query.filter_by(
                from_unit_id=from_unit.id,
                to_unit_id=to_unit.id
            ).first()
            
            if not existing:
                conversion = UOMConversion(
                    from_unit_id=from_unit.id,
                    to_unit_id=to_unit.id,
                    conversion_factor=conv_data['factor'],
                    notes=conv_data['notes']
                )
                db.session.add(conversion)
                print(f"Created conversion: 1 {from_unit.symbol} = {conv_data['factor']} {to_unit.symbol}")
            else:
                print(f"Conversion already exists: {from_unit.symbol} → {to_unit.symbol}")

def create_example_item_conversions(units):
    """Create example item-specific conversions for demonstration"""
    # Get some sample items (if they exist)
    sample_items = Item.query.limit(3).all()
    
    if not sample_items:
        print("No items found. Please add some items first to see UOM conversion examples.")
        return
    
    kg_unit = units.get('Kg')
    pcs_unit = units.get('Pcs')
    
    if not (kg_unit and pcs_unit):
        print("Required units (Kg, Pcs) not found for example conversions")
        return
    
    example_conversions = [
        # Example: Steel rods - buy in Kg, sell in pieces
        {
            'weight_per_piece': 0.025,  # 25 grams per piece
            'pieces_per_kg': 40,        # 40 pieces per Kg
            'notes': 'Example: Steel rods - 25g per piece'
        },
        # Example: Bolts - buy in Kg, sell in pieces  
        {
            'weight_per_piece': 0.010,  # 10 grams per piece
            'pieces_per_kg': 100,       # 100 pieces per Kg
            'notes': 'Example: Small bolts - 10g per piece'
        },
        # Example: Heavy components - buy in Kg, sell in pieces
        {
            'weight_per_piece': 0.500,  # 500 grams per piece
            'pieces_per_kg': 2,         # 2 pieces per Kg
            'notes': 'Example: Heavy components - 500g per piece'
        }
    ]
    
    for i, item in enumerate(sample_items[:3]):
        # Check if item already has conversion
        existing = ItemUOMConversion.query.filter_by(item_id=item.id).first()
        if existing:
            print(f"Item {item.name} already has UOM conversion")
            continue
        
        conv_data = example_conversions[i]
        
        item_conversion = ItemUOMConversion(
            item_id=item.id,
            purchase_unit_id=kg_unit.id,      # Buy in Kg
            inventory_unit_id=kg_unit.id,     # Track in Kg
            sale_unit_id=pcs_unit.id,         # Sell in pieces
            purchase_to_inventory=1.0,        # 1 Kg = 1 Kg
            inventory_to_sale=conv_data['pieces_per_kg'],  # 1 Kg = X pieces
            purchase_to_sale=conv_data['pieces_per_kg'],   # Direct conversion
            weight_per_piece=conv_data['weight_per_piece'],
            pieces_per_kg=conv_data['pieces_per_kg'],
            notes=conv_data['notes']
        )
        
        db.session.add(item_conversion)
        print(f"Created example conversion for {item.name}: 1 Kg = {conv_data['pieces_per_kg']} pieces")

def main():
    """Main initialization function"""
    with app.app_context():
        print("Initializing UOM system...")
        
        # Create tables if they don't exist
        db.create_all()
        
        # Create basic units
        print("\n1. Creating basic units of measure...")
        units = create_basic_units()
        
        # Create basic conversions
        print("\n2. Creating basic conversions...")
        create_basic_conversions(units)
        
        # Create example item conversions
        print("\n3. Creating example item conversions...")
        create_example_item_conversions(units)
        
        # Commit all changes
        db.session.commit()
        
        print("\n✅ UOM system initialization complete!")
        print("\nSummary:")
        print(f"• Units created: {UnitOfMeasure.query.count()}")
        print(f"• Conversions created: {UOMConversion.query.count()}")
        print(f"• Item conversions: {ItemUOMConversion.query.count()}")
        print("\nYou can now:")
        print("• Go to /uom/dashboard to manage UOM system")
        print("• Add item-specific conversions for your products")
        print("• Use the UOM calculator for quick conversions")

if __name__ == '__main__':
    main()