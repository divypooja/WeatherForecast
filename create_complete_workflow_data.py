#!/usr/bin/env python3
"""
Create comprehensive ERP workflow data including:
- Nested BOMs (2 levels)
- Production Orders
- Inventory movements
- Job Work Orders
- Sales Orders
- Complete data flow integration
"""

from app import app, db
from models import *
from sqlalchemy import text
from datetime import datetime, date, timedelta
import random

def create_complete_workflow():
    with app.app_context():
        try:
            print("🚀 Creating comprehensive ERP workflow data...")
            
            # 1. Create Raw Materials and Components
            print("\n📦 Creating Raw Materials and Components...")
            
            # Raw materials
            raw_materials = [
                {'code': 'RM-STEEL-001', 'name': 'Steel Sheet 2mm', 'unit': 'kg', 'stock': 1000},
                {'code': 'RM-PLASTIC-001', 'name': 'ABS Plastic', 'unit': 'kg', 'stock': 500},
                {'code': 'RM-SCREW-001', 'name': 'M6x20 Screws', 'unit': 'pcs', 'stock': 5000},
                {'code': 'RM-PAINT-001', 'name': 'Blue Paint', 'unit': 'ltr', 'stock': 200},
            ]
            
            for rm in raw_materials:
                existing = Item.query.filter_by(code=rm['code']).first()
                if not existing:
                    item = Item(
                        code=rm['code'],
                        name=rm['name'], 
                        unit_of_measure=rm['unit'],
                        current_stock=rm['stock'],
                        item_type='raw_material'
                    )
                    db.session.add(item)
            
            # Semi-finished components
            components = [
                {'code': 'COMP-BASE-001', 'name': 'Metal Base Assembly', 'unit': 'pcs'},
                {'code': 'COMP-COVER-001', 'name': 'Plastic Cover', 'unit': 'pcs'},
                {'code': 'PROD-FINAL-001', 'name': 'Complete Product A', 'unit': 'pcs'},
                {'code': 'PROD-FINAL-002', 'name': 'Complete Product B', 'unit': 'pcs'},
            ]
            
            for comp in components:
                existing = Item.query.filter_by(code=comp['code']).first()
                if not existing:
                    item = Item(
                        code=comp['code'],
                        name=comp['name'],
                        unit_of_measure=comp['unit'],
                        current_stock=0,
                        item_type='finished_good' if 'PROD' in comp['code'] else 'semi_finished'
                    )
                    db.session.add(item)
            
            db.session.commit()
            print("✅ Created materials and components")
            
            # 2. Create Suppliers and Customers
            print("\n🏢 Creating Suppliers and Customers...")
            
            suppliers = [
                {'code': 'SUP-001', 'name': 'Steel Industries Ltd', 'type': 'supplier'},
                {'code': 'SUP-002', 'name': 'Plastic Components Co', 'type': 'supplier'},
                {'code': 'JW-001', 'name': 'Precision Job Works', 'type': 'job_worker'},
            ]
            
            customers = [
                {'code': 'CUST-001', 'name': 'ABC Manufacturing', 'type': 'customer'},
                {'code': 'CUST-002', 'name': 'XYZ Industries', 'type': 'customer'},
            ]
            
            for entity in suppliers + customers:
                existing = Supplier.query.filter_by(code=entity['code']).first()
                if not existing:
                    supplier = Supplier(
                        code=entity['code'],
                        name=entity['name'],
                        partner_type=entity['type'],
                        email=f"{entity['code'].lower()}@example.com",
                        phone="9876543210",
                        address="Industrial Area"
                    )
                    db.session.add(supplier)
            
            db.session.commit()
            print("✅ Created suppliers and customers")
            
            # 3. Create Nested BOMs
            print("\n🏗️ Creating Nested BOMs...")
            
            # Get items for BOM creation
            steel = Item.query.filter_by(code='RM-STEEL-001').first()
            plastic = Item.query.filter_by(code='RM-PLASTIC-001').first()
            screws = Item.query.filter_by(code='RM-SCREW-001').first()
            paint = Item.query.filter_by(code='RM-PAINT-001').first()
            base_assembly = Item.query.filter_by(code='COMP-BASE-001').first()
            cover = Item.query.filter_by(code='COMP-COVER-001').first()
            product_a = Item.query.filter_by(code='PROD-FINAL-001').first()
            product_b = Item.query.filter_by(code='PROD-FINAL-002').first()
            
            # BOM 1: Metal Base Assembly (Level 1 - Component)
            bom_base = BOM(
                code='BOM-BASE-001',
                name='Metal Base Assembly BOM',
                item_id=base_assembly.id,
                quantity=1.0,
                version='1.0',
                is_active=True,
                bom_type='production'
            )
            db.session.add(bom_base)
            db.session.flush()
            
            # BOM items for base assembly
            bom_items_base = [
                {'item_id': steel.id, 'quantity': 2.5, 'unit': 'kg'},
                {'item_id': screws.id, 'quantity': 4, 'unit': 'pcs'},
                {'item_id': paint.id, 'quantity': 0.1, 'unit': 'ltr'},
            ]
            
            for item_data in bom_items_base:
                bom_item = BOMItem(
                    bom_id=bom_base.id,
                    item_id=item_data['item_id'],
                    quantity=item_data['quantity'],
                    unit_of_measure=item_data['unit'],
                    item_type='raw_material'
                )
                db.session.add(bom_item)
            
            # BOM 2: Plastic Cover (Level 1 - Component)
            bom_cover = BOM(
                code='BOM-COVER-001',
                name='Plastic Cover BOM',
                item_id=cover.id,
                quantity=1.0,
                version='1.0',
                is_active=True,
                bom_type='production'
            )
            db.session.add(bom_cover)
            db.session.flush()
            
            bom_item_cover = BOMItem(
                bom_id=bom_cover.id,
                item_id=plastic.id,
                quantity=0.8,
                unit_of_measure='kg',
                item_type='raw_material'
            )
            db.session.add(bom_item_cover)
            
            # BOM 3: Final Product A (Level 2 - Uses components from above BOMs)
            bom_final_a = BOM(
                code='BOM-FINAL-A-001',
                name='Complete Product A BOM',
                item_id=product_a.id,
                quantity=1.0,
                version='1.0',
                is_active=True,
                bom_type='production'
            )
            db.session.add(bom_final_a)
            db.session.flush()
            
            # Final product uses components (nested BOM structure)
            bom_items_final = [
                {'item_id': base_assembly.id, 'quantity': 1, 'unit': 'pcs'},
                {'item_id': cover.id, 'quantity': 1, 'unit': 'pcs'},
                {'item_id': screws.id, 'quantity': 2, 'unit': 'pcs'},
            ]
            
            for item_data in bom_items_final:
                bom_item = BOMItem(
                    bom_id=bom_final_a.id,
                    item_id=item_data['item_id'],
                    quantity=item_data['quantity'],
                    unit_of_measure=item_data['unit'],
                    item_type='semi_finished' if item_data['item_id'] in [base_assembly.id, cover.id] else 'raw_material'
                )
                db.session.add(bom_item)
            
            # BOM 4: Final Product B (similar structure)
            bom_final_b = BOM(
                code='BOM-FINAL-B-001',
                name='Complete Product B BOM',
                item_id=product_b.id,
                quantity=1.0,
                version='1.0',
                is_active=True,
                bom_type='production'
            )
            db.session.add(bom_final_b)
            db.session.flush()
            
            # Similar structure for Product B
            for item_data in bom_items_final:
                bom_item = BOMItem(
                    bom_id=bom_final_b.id,
                    item_id=item_data['item_id'],
                    quantity=item_data['quantity'] * 1.2,  # Slightly different quantities
                    unit_of_measure=item_data['unit'],
                    item_type='semi_finished' if item_data['item_id'] in [base_assembly.id, cover.id] else 'raw_material'
                )
                db.session.add(bom_item)
            
            db.session.commit()
            print("✅ Created nested BOMs (4 levels)")
            
            # 4. Create Production Orders
            print("\n🏭 Creating Production Orders...")
            
            # Get admin user
            admin = User.query.filter_by(username='admin').first()
            
            production_orders = [
                {
                    'number': 'PROD-2025-101',
                    'item_id': base_assembly.id,
                    'quantity': 50,
                    'bom_id': bom_base.id,
                    'status': 'planned'
                },
                {
                    'number': 'PROD-2025-102', 
                    'item_id': cover.id,
                    'quantity': 50,
                    'bom_id': bom_cover.id,
                    'status': 'in_progress'
                },
                {
                    'number': 'PROD-2025-103',
                    'item_id': product_a.id,
                    'quantity': 25,
                    'bom_id': bom_final_a.id,
                    'status': 'planned'
                },
                {
                    'number': 'PROD-2025-104',
                    'item_id': product_b.id,
                    'quantity': 20,
                    'bom_id': bom_final_b.id,
                    'status': 'planned'
                }
            ]
            
            for po_data in production_orders:
                existing = Production.query.filter_by(production_number=po_data['number']).first()
                if not existing:
                    production = Production(
                        production_number=po_data['number'],
                        item_id=po_data['item_id'],
                        quantity_planned=po_data['quantity'],
                        bom_id=po_data['bom_id'],
                        status=po_data['status'],
                        production_date=date.today() + timedelta(days=random.randint(1, 10)),
                        created_by=admin.id,
                        batch_tracking_enabled=True
                    )
                    db.session.add(production)
            
            db.session.commit()
            print("✅ Created production orders")
            
            # 5. Create Sales Orders
            print("\n📋 Creating Sales Orders...")
            
            customer1 = Supplier.query.filter_by(code='CUST-001').first()
            customer2 = Supplier.query.filter_by(code='CUST-002').first()
            
            sales_orders = [
                {
                    'number': 'SO-2025-001',
                    'customer_id': customer1.id,
                    'items': [
                        {'item_id': product_a.id, 'quantity': 15, 'rate': 2500.00},
                        {'item_id': product_b.id, 'quantity': 10, 'rate': 3000.00}
                    ]
                },
                {
                    'number': 'SO-2025-002', 
                    'customer_id': customer2.id,
                    'items': [
                        {'item_id': product_a.id, 'quantity': 20, 'rate': 2400.00}
                    ]
                }
            ]
            
            for so_data in sales_orders:
                existing = SalesOrder.query.filter_by(sales_order_number=so_data['number']).first()
                if not existing:
                    total_amount = sum(item['quantity'] * item['rate'] for item in so_data['items'])
                    
                    sales_order = SalesOrder(
                        sales_order_number=so_data['number'],
                        customer_id=so_data['customer_id'],
                        order_date=date.today(),
                        delivery_date=date.today() + timedelta(days=30),
                        total_amount=total_amount,
                        status='confirmed',
                        created_by=admin.id
                    )
                    db.session.add(sales_order)
                    db.session.flush()
                    
                    # Add sales order items
                    for item_data in so_data['items']:
                        so_item = SalesOrderItem(
                            sales_order_id=sales_order.id,
                            item_id=item_data['item_id'],
                            quantity=item_data['quantity'],
                            unit_price=item_data['rate'],
                            total_price=item_data['quantity'] * item_data['rate']
                        )
                        db.session.add(so_item)
            
            db.session.commit()
            print("✅ Created sales orders")
            
            # 6. Create Job Work Orders
            print("\n🔧 Creating Job Work Orders...")
            
            job_worker = Supplier.query.filter_by(code='JW-001').first()
            
            job_orders = [
                {
                    'number': 'JW-2025-001',
                    'vendor_id': job_worker.id,
                    'process_type': 'painting',
                    'item_id': base_assembly.id,
                    'quantity': 25
                },
                {
                    'number': 'JW-2025-002',
                    'vendor_id': job_worker.id, 
                    'process_type': 'assembly',
                    'item_id': product_a.id,
                    'quantity': 15
                }
            ]
            
            for jw_data in job_orders:
                existing = JobWork.query.filter_by(job_work_number=jw_data['number']).first()
                if not existing:
                    job_work = JobWork(
                        job_work_number=jw_data['number'],
                        vendor_id=jw_data['vendor_id'],
                        process_type=jw_data['process_type'],
                        status='in_progress',
                        start_date=date.today(),
                        expected_completion_date=date.today() + timedelta(days=7),
                        created_by=admin.id
                    )
                    db.session.add(job_work)
                    db.session.flush()
                    
                    # Add job work items
                    jw_item = JobWorkItem(
                        job_work_id=job_work.id,
                        item_id=jw_data['item_id'],
                        quantity_sent=jw_data['quantity'],
                        quantity_received=0,
                        rate_per_unit=50.00
                    )
                    db.session.add(jw_item)
            
            db.session.commit()
            print("✅ Created job work orders")
            
            # 7. Create Purchase Orders for raw materials
            print("\n🛒 Creating Purchase Orders...")
            
            supplier1 = Supplier.query.filter_by(code='SUP-001').first()
            supplier2 = Supplier.query.filter_by(code='SUP-002').first()
            
            purchase_orders = [
                {
                    'number': 'PO-2025-001',
                    'supplier_id': supplier1.id,
                    'items': [
                        {'item_id': steel.id, 'quantity': 500, 'rate': 45.00},
                        {'item_id': screws.id, 'quantity': 2000, 'rate': 0.50}
                    ]
                },
                {
                    'number': 'PO-2025-002',
                    'supplier_id': supplier2.id,
                    'items': [
                        {'item_id': plastic.id, 'quantity': 200, 'rate': 120.00},
                        {'item_id': paint.id, 'quantity': 50, 'rate': 250.00}
                    ]
                }
            ]
            
            for po_data in purchase_orders:
                existing = PurchaseOrder.query.filter_by(purchase_order_number=po_data['number']).first()
                if not existing:
                    total_amount = sum(item['quantity'] * item['rate'] for item in po_data['items'])
                    
                    purchase_order = PurchaseOrder(
                        purchase_order_number=po_data['number'],
                        supplier_id=po_data['supplier_id'],
                        order_date=date.today(),
                        expected_delivery_date=date.today() + timedelta(days=15),
                        total_amount=total_amount,
                        status='approved',
                        created_by=admin.id
                    )
                    db.session.add(purchase_order)
                    db.session.flush()
                    
                    # Add purchase order items
                    for item_data in po_data['items']:
                        po_item = PurchaseOrderItem(
                            purchase_order_id=purchase_order.id,
                            item_id=item_data['item_id'],
                            quantity=item_data['quantity'],
                            unit_price=item_data['rate'],
                            total_price=item_data['quantity'] * item_data['rate']
                        )
                        db.session.add(po_item)
            
            db.session.commit()
            print("✅ Created purchase orders")
            
            # 8. Create GRNs for received materials
            print("\n📦 Creating GRNs (Goods Receipt Notes)...")
            
            po1 = PurchaseOrder.query.filter_by(purchase_order_number='PO-2025-001').first()
            po2 = PurchaseOrder.query.filter_by(purchase_order_number='PO-2025-002').first()
            
            if po1:
                grn1 = GRN(
                    grn_number='GRN-2025-001',
                    purchase_order_id=po1.id,
                    supplier_id=po1.supplier_id,
                    received_date=date.today(),
                    status='received',
                    created_by=admin.id
                )
                db.session.add(grn1)
                db.session.flush()
                
                # Add GRN line items
                for po_item in po1.items:
                    grn_item = GRNLineItem(
                        grn_id=grn1.id,
                        item_id=po_item.item_id,
                        ordered_quantity=po_item.quantity,
                        received_quantity=po_item.quantity * 0.9,  # 90% received
                        unit_price=po_item.unit_price,
                        status='received'
                    )
                    db.session.add(grn_item)
            
            db.session.commit()
            print("✅ Created GRNs")
            
            # 9. Update inventory levels based on transactions
            print("\n📊 Updating Inventory Levels...")
            
            # Update stock for received materials
            steel.current_stock += 450  # 90% of 500
            screws.current_stock += 1800  # 90% of 2000
            
            db.session.commit()
            print("✅ Updated inventory levels")
            
            print("\n🎉 Complete ERP workflow data created successfully!")
            print("\n📈 Summary:")
            print(f"   - 4 Nested BOMs created")
            print(f"   - 4 Production Orders")
            print(f"   - 2 Sales Orders with multiple items")
            print(f"   - 2 Job Work Orders")
            print(f"   - 2 Purchase Orders")
            print(f"   - 1 GRN with material receipts")
            print(f"   - Inventory movements tracked")
            print(f"   - Complete data flow integration")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating workflow data: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = create_complete_workflow()
    if success:
        print("\n✅ Ready to test complete ERP workflow!")
    else:
        print("\n❌ Failed to create workflow data")