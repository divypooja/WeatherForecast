#!/usr/bin/env python3

"""
Create Multi-State Inventory Examples
Creates 2 sample items to demonstrate the multi-state inventory tracking workflow
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Item

def create_multistate_examples():
    """Create 2 example items for multi-state inventory demonstration"""
    
    with app.app_context():
        print("Creating Multi-State Inventory Examples...")
        
        # Example 1: Steel Plate (Raw Material Processing)
        steel_plate = Item.query.filter_by(code='STEEL-001').first()
        if not steel_plate:
            steel_plate = Item(
                code='STEEL-001',
                name='Steel Plate 10mm',
                description='High-grade steel plate for cutting and machining',
                unit_of_measure='pcs',
                unit_price=150.00,
                current_stock=75,
                minimum_stock=20,
                qty_raw=75.0,  # 75 pieces in raw state
                qty_wip=0.0,
                qty_finished=0.0,
                qty_scrap=0.0,
                material_classification='raw_material',
                gst_rate=18.0,
                hsn_code='7208'
            )
            db.session.add(steel_plate)
            print("✓ Created Steel Plate example")
        else:
            # Update existing item with multi-state values
            steel_plate.qty_raw = 75.0
            steel_plate.qty_wip = 0.0
            steel_plate.qty_finished = 0.0
            steel_plate.qty_scrap = 0.0
            steel_plate.current_stock = 75
            print("✓ Updated Steel Plate with multi-state values")
        
        # Example 2: Aluminum Bracket (Finished Manufacturing)
        aluminum_bracket = Item.query.filter_by(code='ALU-BRACKET-001').first()
        if not aluminum_bracket:
            aluminum_bracket = Item(
                code='ALU-BRACKET-001',
                name='Aluminum L-Bracket',
                description='Precision machined aluminum bracket for assembly',
                unit_of_measure='pcs',
                unit_price=85.00,
                current_stock=45,  # Available stock (raw + finished)
                minimum_stock=15,
                qty_raw=25.0,     # 25 pieces ready to process
                qty_wip=20.0,     # 20 pieces currently being machined
                qty_finished=20.0, # 20 pieces completed and ready
                qty_scrap=5.0,    # 5 pieces damaged during processing
                material_classification='production_use',
                gst_rate=18.0,
                hsn_code='7604'
            )
            db.session.add(aluminum_bracket)
            print("✓ Created Aluminum Bracket example")
        else:
            # Update existing item with multi-state values
            aluminum_bracket.qty_raw = 25.0
            aluminum_bracket.qty_wip = 20.0
            aluminum_bracket.qty_finished = 20.0
            aluminum_bracket.qty_scrap = 5.0
            aluminum_bracket.current_stock = 45  # raw + finished
            print("✓ Updated Aluminum Bracket with multi-state values")
        
        try:
            db.session.commit()
            print("\n" + "="*60)
            print("MULTI-STATE INVENTORY EXAMPLES CREATED SUCCESSFULLY!")
            print("="*60)
            
            print("\nExample 1: Steel Plate 10mm (STEEL-001)")
            print(f"├── Raw Material: {steel_plate.qty_raw} pieces (ready for processing)")
            print(f"├── WIP: {steel_plate.qty_wip} pieces (being processed)")
            print(f"├── Finished: {steel_plate.qty_finished} pieces (completed)")
            print(f"├── Scrap: {steel_plate.qty_scrap} pieces (rejected)")
            print(f"├── Total Stock: {steel_plate.total_stock} pieces")
            print(f"└── Available Stock: {steel_plate.available_stock} pieces")
            
            print("\nExample 2: Aluminum L-Bracket (ALU-BRACKET-001)")
            print(f"├── Raw Material: {aluminum_bracket.qty_raw} pieces (ready for processing)")
            print(f"├── WIP: {aluminum_bracket.qty_wip} pieces (being machined)")
            print(f"├── Finished: {aluminum_bracket.qty_finished} pieces (completed)")
            print(f"├── Scrap: {aluminum_bracket.qty_scrap} pieces (rejected)")
            print(f"├── Total Stock: {aluminum_bracket.total_stock} pieces")
            print(f"└── Available Stock: {aluminum_bracket.available_stock} pieces")
            
            print("\nNOW YOU CAN:")
            print("1. Visit the Multi-State Inventory View to see these examples")
            print("2. Create Job Work with Steel Plate to see Raw → WIP transition")
            print("3. Complete Material Inspection to see WIP → Finished/Scrap transition")
            print("4. Monitor the complete manufacturing workflow in real-time")
            
            return True
            
        except Exception as e:
            print(f"Error creating examples: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    create_multistate_examples()