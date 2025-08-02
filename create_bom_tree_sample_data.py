#!/usr/bin/env python3
"""
Create sample multi-level BOM data to demonstrate tree view functionality
"""
import os
from main import app

def create_bom_tree_sample_data():
    with app.app_context():
        from models import Item, BOM, BOMItem, db
        from models_uom import UnitOfMeasure
        
        print("🔄 Creating sample multi-level BOM data for tree view...")
        
        # Ensure we have UOMs
        pcs_uom = UnitOfMeasure.query.filter_by(symbol='Pcs').first()
        kg_uom = UnitOfMeasure.query.filter_by(symbol='Kg').first()
        
        if not pcs_uom or not kg_uom:
            print("❌ UOM data not found. Please run init_uom_data.py first")
            return
        
        # Create sample items if they don't exist
        items_data = [
            {'code': 'CW001', 'name': 'Castor Wheel', 'item_type': 'finished_good'},
            {'code': 'MP001', 'name': 'Mounted Plate', 'item_type': 'semi_finished'},
            {'code': 'MS001', 'name': 'MS Sheet', 'item_type': 'material'},
            {'code': 'NUT001', 'name': 'M8 Nut', 'item_type': 'material'},
            {'code': 'BOLT001', 'name': 'M8 x 20mm Bolt', 'item_type': 'material'},
        ]
        
        created_items = {}
        for item_data in items_data:
            existing_item = Item.query.filter_by(code=item_data['code']).first()
            if not existing_item:
                item = Item(
                    code=item_data['code'],
                    name=item_data['name'],
                    item_type=item_data['item_type'],
                    unit_of_measure='Pcs',
                    unit_price=100.0,  # Sample price
                    current_stock=1000.0
                )
                db.session.add(item)
                db.session.flush()
                created_items[item_data['code']] = item
                print(f"✅ Created item: {item_data['name']} ({item_data['code']})")
            else:
                created_items[item_data['code']] = existing_item
                print(f"⚠️  Item already exists: {item_data['name']} ({item_data['code']})")
        
        # Create BOMs - Level 1: MS Sheet (base material - no BOM needed)
        
        # Level 2: Mounted Plate BOM (uses MS Sheet)
        mp_bom = BOM.query.filter_by(product_id=created_items['MP001'].id).first()
        if not mp_bom:
            mp_bom = BOM(
                bom_code='BOM-MP-001',
                product_id=created_items['MP001'].id,
                output_uom_id=pcs_uom.id,
                version='1.0',
                status='active',
                is_active=True,
                output_quantity=4.0,  # 1 MS Sheet makes 4 Mounted Plates
                description='Mounted Plate made from MS Sheet through cutting and forming',
                intermediate_product=True,  # This is an intermediate product
                bom_level=0,
                created_by=1
            )
            db.session.add(mp_bom)
            db.session.flush()
            
            # Add MS Sheet to Mounted Plate BOM
            mp_bom_item = BOMItem(
                bom_id=mp_bom.id,
                material_id=created_items['MS001'].id,
                item_id=created_items['MS001'].id,
                qty_required=1.0,
                quantity_required=1.0,
                uom_id=pcs_uom.id,
                unit='Pcs',
                unit_cost=250.0
            )
            db.session.add(mp_bom_item)
            print(f"✅ Created BOM: Mounted Plate (uses 1 MS Sheet → 4 Mounted Plates)")
        else:
            print(f"⚠️  BOM already exists for Mounted Plate")
        
        # Level 3: Castor Wheel BOM (uses Mounted Plate + direct materials)
        cw_bom = BOM.query.filter_by(product_id=created_items['CW001'].id).first()
        if not cw_bom:
            cw_bom = BOM(
                bom_code='BOM-CW-001',
                product_id=created_items['CW001'].id,
                output_uom_id=pcs_uom.id,
                version='1.0',
                status='active',
                is_active=True,
                output_quantity=1.0,  # 1 BOM produces 1 Castor Wheel
                description='Complete Castor Wheel assembly with intermediate products',
                intermediate_product=False,  # This is a final product
                bom_level=1,
                created_by=1
            )
            db.session.add(cw_bom)
            db.session.flush()
            
            # Add Mounted Plate to Castor Wheel BOM
            cw_bom_item1 = BOMItem(
                bom_id=cw_bom.id,
                material_id=created_items['MP001'].id,
                item_id=created_items['MP001'].id,
                qty_required=1.0,
                quantity_required=1.0,
                uom_id=pcs_uom.id,
                unit='Pcs',
                unit_cost=150.0
            )
            db.session.add(cw_bom_item1)
            
            # Add Nut to Castor Wheel BOM
            cw_bom_item2 = BOMItem(
                bom_id=cw_bom.id,
                material_id=created_items['NUT001'].id,
                item_id=created_items['NUT001'].id,
                qty_required=4.0,
                quantity_required=4.0,
                uom_id=pcs_uom.id,
                unit='Pcs',
                unit_cost=5.0
            )
            db.session.add(cw_bom_item2)
            
            # Add Bolt to Castor Wheel BOM
            cw_bom_item3 = BOMItem(
                bom_id=cw_bom.id,
                material_id=created_items['BOLT001'].id,
                item_id=created_items['BOLT001'].id,
                qty_required=4.0,
                quantity_required=4.0,
                uom_id=pcs_uom.id,
                unit='Pcs',
                unit_cost=8.0
            )
            db.session.add(cw_bom_item3)
            
            print(f"✅ Created BOM: Castor Wheel (uses Mounted Plate + 4 Nuts + 4 Bolts)")
        else:
            print(f"⚠️  BOM already exists for Castor Wheel")
        
        # Now set parent-child relationship
        if mp_bom and cw_bom:
            # Set Mounted Plate BOM as a child of Castor Wheel BOM
            mp_bom.parent_bom_id = cw_bom.id
            mp_bom.bom_level = 1  # Child level
            
        db.session.commit()
        print("🎉 Sample multi-level BOM data created successfully!")
        print("\nTree structure created:")
        print("Castor Wheel")
        print(" ├── Mounted Plate (Intermediate Product)")
        print(" │    └── MS Sheet")
        print(" ├── M8 Nut (4 pieces)")
        print(" └── M8 x 20mm Bolt (4 pieces)")

if __name__ == '__main__':
    create_bom_tree_sample_data()