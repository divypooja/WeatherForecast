#!/usr/bin/env python3
"""
Configure Castor Wheel BOM with UOM Integration
This script demonstrates the complete BOM-UOM integration system
"""

from app import app, db
from models import Item, BOM, BOMItem, User
from models_uom import UnitOfMeasure, UOMConversion, ItemUOMConversion

def configure_castor_bom_with_uom():
    """Configure a complete Castor Wheel BOM with UOM conversions"""
    
    with app.app_context():
        print("🏭 Configuring Castor Wheel BOM with UOM Integration...")
        
        # Get admin user (first user)
        admin_user = User.query.first()
        if not admin_user:
            print("❌ No admin user found. Please create an admin user first.")
            return
        
        # Get or create Castor Wheel product
        castor_wheel = Item.query.filter_by(code='CASTOR-001').first()
        if not castor_wheel:
            print("❌ Castor Wheel product not found. Creating it...")
            castor_wheel = Item()
            castor_wheel.code = 'CASTOR-001'
            castor_wheel.name = 'Heavy Duty Castor Wheel'
            castor_wheel.item_type = 'product'
            castor_wheel.unit_of_measure = 'Pcs'
            castor_wheel.unit_price = 150.0
            castor_wheel.current_stock = 50
            castor_wheel.created_by = admin_user.id
            db.session.add(castor_wheel)
            db.session.commit()
            print(f"✅ Created Castor Wheel: {castor_wheel.code}")
        
        # Get UOM units
        kg_unit = UnitOfMeasure.query.filter_by(symbol='Kg').first()
        g_unit = UnitOfMeasure.query.filter_by(symbol='g').first()
        pcs_unit = UnitOfMeasure.query.filter_by(symbol='Pcs').first()
        mm_unit = UnitOfMeasure.query.filter_by(symbol='mm').first()
        m_unit = UnitOfMeasure.query.filter_by(symbol='M').first()
        ml_unit = UnitOfMeasure.query.filter_by(symbol='ml').first()
        
        if not all([kg_unit, g_unit, pcs_unit, mm_unit, m_unit, ml_unit]):
            print("❌ Required UOM units not found. Please run UOM initialization first.")
            return
        
        # Get or create BOM materials with UOM configurations
        materials = [
            {
                'code': 'METAL-BRACKET-001',
                'name': 'Metal Bracket (Steel)',
                'item_type': 'material',
                'inventory_unit': 'Pcs',  # Stored as pieces
                'purchase_unit': 'Pcs',   # Bought as pieces
                'sale_unit': 'Pcs',      # Not applicable for materials
                'unit_price': 25.0,
                'current_stock': 200,
                'bom_qty': 1,            # 1 piece per castor
                'bom_unit': 'Pcs'       # Specified in BOM as pieces
            },
            {
                'code': 'WHEEL-PU-001',
                'name': 'Polyurethane Wheel',
                'item_type': 'material',
                'inventory_unit': 'Pcs',
                'purchase_unit': 'Pcs',
                'sale_unit': 'Pcs',
                'unit_price': 45.0,
                'current_stock': 150,
                'bom_qty': 1,            # 1 wheel per castor
                'bom_unit': 'Pcs'
            },
            {
                'code': 'STEEL-ROD-001',
                'name': 'Steel Rod/Axle',
                'item_type': 'material',
                'inventory_unit': 'M',    # Stored in meters
                'purchase_unit': 'M',     # Bought in meters
                'sale_unit': 'M',
                'unit_price': 120.0,     # Per meter
                'current_stock': 50,     # 50 meters in stock
                'bom_qty': 80,           # 80mm = 0.08M per castor
                'bom_unit': 'mm'         # Specified in BOM as millimeters
            },
            {
                'code': 'BOLT-M8-001',
                'name': 'M8 Bolt',
                'item_type': 'material',
                'inventory_unit': 'Pcs',
                'purchase_unit': 'Pcs',
                'sale_unit': 'Pcs',
                'unit_price': 3.50,
                'current_stock': 500,
                'bom_qty': 2,            # 2 bolts per castor
                'bom_unit': 'Pcs'
            },
            {
                'code': 'WASHER-001',
                'name': 'Steel Washer',
                'item_type': 'material',
                'inventory_unit': 'Pcs',
                'purchase_unit': 'Pcs',
                'sale_unit': 'Pcs',
                'unit_price': 1.25,
                'current_stock': 1000,
                'bom_qty': 4,            # 4 washers per castor
                'bom_unit': 'Pcs'
            },
            {
                'code': 'GREASE-001',
                'name': 'Industrial Grease',
                'item_type': 'consumable',
                'inventory_unit': 'ml',   # Stored in milliliters
                'purchase_unit': 'L',     # Bought in liters
                'sale_unit': 'ml',
                'unit_price': 0.05,      # Per ml
                'current_stock': 5000,   # 5000ml in stock
                'bom_qty': 5,            # 5ml per castor
                'bom_unit': 'ml'         # Specified in BOM as milliliters
            }
        ]
        
        material_items = []
        for mat_data in materials:
            # Get or create material item
            material = Item.query.filter_by(code=mat_data['code']).first()
            if not material:
                material = Item()
                material.code = mat_data['code']
                material.name = mat_data['name']
                material.item_type = mat_data['item_type']
                material.unit_of_measure = mat_data['inventory_unit']
                material.unit_price = mat_data['unit_price']
                material.current_stock = mat_data['current_stock']
                material.created_by = admin_user.id
                db.session.add(material)
                db.session.commit()
                print(f"✅ Created material: {material.code}")
            
            # Configure UOM conversion for this item
            inventory_unit = UnitOfMeasure.query.filter_by(symbol=mat_data['inventory_unit']).first()
            purchase_unit = UnitOfMeasure.query.filter_by(symbol=mat_data['purchase_unit']).first()
            sale_unit = UnitOfMeasure.query.filter_by(symbol=mat_data['sale_unit']).first()
            
            if inventory_unit and purchase_unit and sale_unit:
                # Check if UOM conversion already exists
                item_uom = ItemUOMConversion.query.filter_by(item_id=material.id).first()
                if not item_uom:
                    item_uom = ItemUOMConversion()
                    item_uom.item_id = material.id
                    item_uom.purchase_unit_id = purchase_unit.id
                    item_uom.inventory_unit_id = inventory_unit.id
                    item_uom.sale_unit_id = sale_unit.id
                    
                    # Set default conversion factors (1:1 if same unit, or calculated)
                    if purchase_unit.id == inventory_unit.id:
                        item_uom.purchase_to_inventory = 1.0
                    else:
                        # For different units, try to find conversion in UOM system
                        conversion = UOMConversion.query.filter(
                            ((UOMConversion.from_unit_id == purchase_unit.id) & (UOMConversion.to_unit_id == inventory_unit.id)) |
                            ((UOMConversion.from_unit_id == inventory_unit.id) & (UOMConversion.to_unit_id == purchase_unit.id))
                        ).first()
                        if conversion:
                            if conversion.from_unit_id == purchase_unit.id:
                                item_uom.purchase_to_inventory = conversion.conversion_factor
                            else:
                                item_uom.purchase_to_inventory = 1.0 / conversion.conversion_factor
                        else:
                            item_uom.purchase_to_inventory = 1.0  # Default 1:1
                    
                    if inventory_unit.id == sale_unit.id:
                        item_uom.inventory_to_sale = 1.0
                    else:
                        # For different units, try to find conversion
                        conversion = UOMConversion.query.filter(
                            ((UOMConversion.from_unit_id == inventory_unit.id) & (UOMConversion.to_unit_id == sale_unit.id)) |
                            ((UOMConversion.from_unit_id == sale_unit.id) & (UOMConversion.to_unit_id == inventory_unit.id))
                        ).first()
                        if conversion:
                            if conversion.from_unit_id == inventory_unit.id:
                                item_uom.inventory_to_sale = conversion.conversion_factor
                            else:
                                item_uom.inventory_to_sale = 1.0 / conversion.conversion_factor
                        else:
                            item_uom.inventory_to_sale = 1.0
                    
                    # Calculate purchase to sale conversion
                    item_uom.purchase_to_sale = item_uom.purchase_to_inventory * item_uom.inventory_to_sale
                    item_uom.is_active = True
                    
                    db.session.add(item_uom)
                    print(f"✅ Configured UOM for {material.code}: Purchase({purchase_unit.symbol}) → Inventory({inventory_unit.symbol}) → Sale({sale_unit.symbol})")
            
            material_items.append({
                'item': material,
                'bom_qty': mat_data['bom_qty'],
                'bom_unit': mat_data['bom_unit']
            })
        
        # Create or update Castor Wheel BOM
        existing_bom = BOM.query.filter_by(product_id=castor_wheel.id, is_active=True).first()
        if existing_bom:
            print(f"⚠️  Deactivating existing BOM for {castor_wheel.code}")
            existing_bom.is_active = False
        
        # Create new BOM with UOM integration
        castor_bom = BOM()
        castor_bom.product_id = castor_wheel.id
        castor_bom.version = '2.0'
        castor_bom.description = 'Heavy Duty Castor Wheel with UOM Integration - Complete assembly including steel bracket, PU wheel, steel axle, bolts, washers, and grease'
        castor_bom.production_unit_id = pcs_unit.id  # Production planned in pieces
        castor_bom.is_active = True
        castor_bom.created_by = admin_user.id
        db.session.add(castor_bom)
        db.session.commit()
        print(f"✅ Created BOM v2.0 for {castor_wheel.code} with production unit: {pcs_unit.symbol}")
        
        # Add BOM items with proper UOM specifications
        for mat_info in material_items:
            material = mat_info['item']
            bom_unit_obj = UnitOfMeasure.query.filter_by(symbol=mat_info['bom_unit']).first()
            
            # Check if BOM item already exists
            existing_bom_item = BOMItem.query.filter_by(bom_id=castor_bom.id, item_id=material.id).first()
            if not existing_bom_item:
                bom_item = BOMItem()
                bom_item.bom_id = castor_bom.id
                bom_item.item_id = material.id
                bom_item.quantity_required = mat_info['bom_qty']
                bom_item.bom_unit_id = bom_unit_obj.id if bom_unit_obj else None
                bom_item.unit_cost = material.unit_price or 0
                bom_item.notes = f"Required for {castor_wheel.name} assembly"
                db.session.add(bom_item)
                print(f"✅ Added BOM item: {material.code} - {mat_info['bom_qty']} {mat_info['bom_unit']}")
        
        db.session.commit()
        
        # Test material availability calculation
        print("\n🧮 Testing Material Availability Calculation...")
        availability = castor_bom.check_material_availability(production_quantity=100)
        
        print(f"\n📊 Production Planning for 100 {castor_wheel.name}:")
        print("-" * 80)
        for material in availability['materials']:
            bom_item = material['bom_item']
            item = material['item']
            status = "✅ Sufficient" if material['is_sufficient'] else "❌ Shortage"
            
            print(f"{item.code:20} | Req: {material['required_qty']:8.3f} {item.unit_of_measure:5} | "
                  f"Avail: {material['available_qty']:8.3f} {item.unit_of_measure:5} | {status}")
            
            if not material['is_sufficient']:
                shortage = material['shortage_qty']
                print(f"{'':20} | Shortage: {shortage:.3f} {item.unit_of_measure}")
        
        print("-" * 80)
        total_cost = castor_bom.get_total_cost(production_quantity=100)
        print(f"Total Material Cost for 100 units: ₹{total_cost:.2f}")
        print(f"Cost per unit: ₹{total_cost/100:.2f}")
        
        if availability['can_produce']:
            print("✅ Production can proceed - all materials available!")
        else:
            print("❌ Production blocked - material shortages detected!")
        
        print(f"\n🎉 BOM-UOM Integration Complete!")
        print(f"📋 BOM ID: {castor_bom.id}")
        print(f"🎯 Product: {castor_wheel.code} - {castor_wheel.name}")
        print(f"📦 Components: {len(material_items)} materials with UOM conversions")
        print(f"⚖️  UOM Features: Cross-unit material planning (mm→M, L→ml, etc.)")
        
        # Print navigation instructions
        print(f"\n🔗 Access Points:")
        print(f"   • Production Dashboard: /production/dashboard")
        print(f"   • BOM Management: /production/bom")
        print(f"   • Edit This BOM: /production/bom/edit/{castor_bom.id}")
        print(f"   • UOM Management: /uom/dashboard")
        print(f"   • Login: admin/admin123")

if __name__ == "__main__":
    configure_castor_bom_with_uom()