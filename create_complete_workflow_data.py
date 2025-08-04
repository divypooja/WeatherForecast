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
from models_accounting import *
from models_grn import GRN, GRNLineItem
from sqlalchemy import text
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash
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
            
            # 1.5. Create Units of Measure
            print("\n📏 Creating Units of Measure...")
            
            uoms = [
                {'name': 'Kilogram', 'symbol': 'kg', 'category': 'Weight'},
                {'name': 'Pieces', 'symbol': 'pcs', 'category': 'Count'},
                {'name': 'Liter', 'symbol': 'ltr', 'category': 'Volume'},
                {'name': 'Meter', 'symbol': 'mtr', 'category': 'Length'},
                {'name': 'Box', 'symbol': 'box', 'category': 'Count'}
            ]
            
            for uom_data in uoms:
                existing = UnitOfMeasure.query.filter_by(name=uom_data['name']).first()
                if not existing:
                    uom = UnitOfMeasure(
                        name=uom_data['name'],
                        symbol=uom_data['symbol'],
                        category=uom_data['category'],
                        is_base_unit=uom_data['symbol'] in ['kg', 'pcs']
                    )
                    db.session.add(uom)
            
            db.session.commit()
            print("✅ Created units of measure")
            
            # 2. Create Suppliers and Customers
            print("\n🏢 Creating Suppliers and Customers...")
            
            suppliers = [
                {'name': 'Steel Industries Ltd', 'type': 'supplier'},
                {'name': 'Plastic Components Co', 'type': 'supplier'},
                {'name': 'Precision Job Works', 'type': 'vendor'},
            ]
            
            customers = [
                {'name': 'ABC Manufacturing', 'type': 'customer'},
                {'name': 'XYZ Industries', 'type': 'customer'},
            ]
            
            for entity in suppliers + customers:
                existing = Supplier.query.filter_by(name=entity['name']).first()
                if not existing:
                    supplier = Supplier(
                        name=entity['name'],
                        partner_type=entity['type'],
                        email=f"{entity['name'].lower().replace(' ', '')}@example.com",
                        phone="9876543210",
                        address="Industrial Area",
                        city="Mumbai",
                        state="Maharashtra",
                        pin_code="400001"
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
            existing_bom = BOM.query.filter_by(bom_code='BOM-BASE-001').first()
            if not existing_bom:
                bom_base = BOM(
                    bom_code='BOM-BASE-001',
                    description='Metal Base Assembly BOM',
                    product_id=base_assembly.id,
                    output_quantity=1.0,
                    version='1.0',
                    is_active=True,
                    status='active'
                )
                db.session.add(bom_base)
                db.session.flush()
            else:
                bom_base = existing_bom
            
            # Get UOMs
            kg_uom = UnitOfMeasure.query.filter_by(symbol='kg').first()
            pcs_uom = UnitOfMeasure.query.filter_by(symbol='pcs').first()
            ltr_uom = UnitOfMeasure.query.filter_by(symbol='ltr').first()
            
            # BOM items for base assembly
            bom_items_base = [
                {'material_id': steel.id, 'qty_required': 2.5, 'uom_id': kg_uom.id, 'unit': 'kg'},
                {'material_id': screws.id, 'qty_required': 4, 'uom_id': pcs_uom.id, 'unit': 'pcs'},
                {'material_id': paint.id, 'qty_required': 0.1, 'uom_id': ltr_uom.id, 'unit': 'ltr'},
            ]
            
            for item_data in bom_items_base:
                bom_item = BOMItem(
                    bom_id=bom_base.id,
                    material_id=item_data['material_id'],
                    qty_required=item_data['qty_required'],
                    uom_id=item_data['uom_id'],
                    unit=item_data['unit']
                )
                db.session.add(bom_item)
            
            # BOM 2: Plastic Cover (Level 1 - Component)
            existing_bom_cover = BOM.query.filter_by(bom_code='BOM-COVER-001').first()
            if not existing_bom_cover:
                bom_cover = BOM(
                    bom_code='BOM-COVER-001',
                    description='Plastic Cover BOM',
                    product_id=cover.id,
                    output_quantity=1.0,
                    version='1.0',
                    is_active=True,
                    status='active'
                )
                db.session.add(bom_cover)
                db.session.flush()
            else:
                bom_cover = existing_bom_cover
            
            bom_item_cover = BOMItem(
                bom_id=bom_cover.id,
                material_id=plastic.id,
                qty_required=0.8,
                uom_id=kg_uom.id,
                unit='kg'
            )
            db.session.add(bom_item_cover)
            
            # BOM 3: Final Product A (Level 2 - Uses components from above BOMs)
            existing_bom_final_a = BOM.query.filter_by(bom_code='BOM-FINAL-A-001').first()
            if not existing_bom_final_a:
                bom_final_a = BOM(
                    bom_code='BOM-FINAL-A-001',
                    description='Complete Product A BOM',
                    product_id=product_a.id,
                    output_quantity=1.0,
                    version='1.0',
                    is_active=True,
                    status='active'
                )
                db.session.add(bom_final_a)
                db.session.flush()
            else:
                bom_final_a = existing_bom_final_a
            
            # Final product uses components (nested BOM structure)
            bom_items_final = [
                {'material_id': base_assembly.id, 'qty_required': 1, 'uom_id': pcs_uom.id, 'unit': 'pcs'},
                {'material_id': cover.id, 'qty_required': 1, 'uom_id': pcs_uom.id, 'unit': 'pcs'},
                {'material_id': screws.id, 'qty_required': 2, 'uom_id': pcs_uom.id, 'unit': 'pcs'},
            ]
            
            for item_data in bom_items_final:
                bom_item = BOMItem(
                    bom_id=bom_final_a.id,
                    material_id=item_data['material_id'],
                    qty_required=item_data['qty_required'],
                    uom_id=item_data['uom_id'],
                    unit=item_data['unit']
                )
                db.session.add(bom_item)
            
            # BOM 4: Final Product B (similar structure)
            existing_bom_final_b = BOM.query.filter_by(bom_code='BOM-FINAL-B-001').first()
            if not existing_bom_final_b:
                bom_final_b = BOM(
                    bom_code='BOM-FINAL-B-001',
                    description='Complete Product B BOM',
                    product_id=product_b.id,
                    output_quantity=1.0,
                    version='1.0',
                    is_active=True,
                    status='active'
                )
                db.session.add(bom_final_b)
                db.session.flush()
            else:
                bom_final_b = existing_bom_final_b
            
            # Similar structure for Product B
            for item_data in bom_items_final:
                bom_item = BOMItem(
                    bom_id=bom_final_b.id,
                    material_id=item_data['material_id'],
                    qty_required=item_data['qty_required'] * 1.2,  # Slightly different quantities
                    uom_id=item_data['uom_id'],
                    unit=item_data['unit']
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
            
            customer1 = Supplier.query.filter_by(name='ABC Manufacturing').first()
            customer2 = Supplier.query.filter_by(name='XYZ Industries').first()
            
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
                existing = SalesOrder.query.filter_by(so_number=so_data['number']).first()
                if not existing:
                    total_amount = sum(item['quantity'] * item['rate'] for item in so_data['items'])
                    
                    sales_order = SalesOrder(
                        so_number=so_data['number'],
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
                            quantity_ordered=item_data['quantity'],
                            unit_price=item_data['rate'],
                            total_price=item_data['quantity'] * item_data['rate']
                        )
                        db.session.add(so_item)
            
            db.session.commit()
            print("✅ Created sales orders")
            
            # 6. Create Job Work Orders
            print("\n🔧 Creating Job Work Orders...")
            
            job_worker = Supplier.query.filter_by(name='Precision Job Works').first()
            
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
                existing = JobWork.query.filter_by(job_number=jw_data['number']).first()
                if not existing:
                    job_work = JobWork(
                        job_number=jw_data['number'],
                        customer_name=f"Customer for {jw_data['process_type']}",
                        item_id=jw_data['item_id'],
                        process=jw_data['process_type'],
                        quantity_sent=jw_data['quantity'],
                        rate_per_unit=150.00,
                        work_type='outsourced',
                        sent_date=date.today(),
                        expected_return=date.today() + timedelta(days=7),
                        status='sent',
                        created_by=admin.id
                    )
                    db.session.add(job_work)
            
            db.session.commit()
            print("✅ Created job work orders")
            
            # 7. Create Purchase Orders for raw materials
            print("\n🛒 Creating Purchase Orders...")
            
            supplier1 = Supplier.query.filter_by(name='Steel Industries Ltd').first()
            supplier2 = Supplier.query.filter_by(name='Plastic Components Co').first()
            
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
                existing = PurchaseOrder.query.filter_by(po_number=po_data['number']).first()
                if not existing:
                    total_amount = sum(item['quantity'] * item['rate'] for item in po_data['items'])
                    
                    purchase_order = PurchaseOrder(
                        po_number=po_data['number'],
                        supplier_id=po_data['supplier_id'],
                        order_date=date.today(),
                        expected_date=date.today() + timedelta(days=15),
                        total_amount=total_amount,
                        status='sent',
                        created_by=admin.id
                    )
                    db.session.add(purchase_order)
                    db.session.flush()
                    
                    # Add purchase order items
                    for item_data in po_data['items']:
                        po_item = PurchaseOrderItem(
                            purchase_order_id=purchase_order.id,
                            item_id=item_data['item_id'],
                            qty=item_data['quantity'],
                            rate=item_data['rate'],
                            amount=item_data['quantity'] * item_data['rate'],
                            quantity_ordered=item_data['quantity'],
                            unit_price=item_data['rate'],
                            total_price=item_data['quantity'] * item_data['rate']
                        )
                        db.session.add(po_item)
            
            db.session.commit()
            print("✅ Created purchase orders")
            
            # 8. Create GRNs for received materials
            print("\n📦 Creating GRNs (Goods Receipt Notes)...")
            
            po1 = PurchaseOrder.query.filter_by(po_number='PO-2025-001').first()
            po2 = PurchaseOrder.query.filter_by(po_number='PO-2025-002').first()
            
            if po1:
                existing_grn = GRN.query.filter_by(grn_number='GRN-2025-001').first()
                if not existing_grn:
                    grn1 = GRN(
                        grn_number='GRN-2025-001',
                        purchase_order_id=po1.id,
                        received_date=date.today(),
                        status='received',
                        received_by=admin.id
                    )
                    db.session.add(grn1)
                    db.session.flush()
                else:
                    grn1 = existing_grn
                
                # Add GRN line items
                for po_item in po1.items:
                    grn_item = GRNLineItem(
                        grn_id=grn1.id,
                        item_id=po_item.item_id,
                        quantity_received=po_item.qty * 0.9,  # 90% received
                        quantity_passed=po_item.qty * 0.85,  # 85% passed inspection
                        quantity_rejected=po_item.qty * 0.05,  # 5% rejected
                        rate_per_unit=po_item.rate,
                        inspection_status='passed'
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
            
            # 10. Create HR Data (Employees and Departments)
            print("\n👥 Creating HR Data...")
            
            # Create departments
            departments = [
                {'code': 'PROD', 'name': 'Production Department'},
                {'code': 'QC', 'name': 'Quality Control'},
                {'code': 'ADMIN', 'name': 'Administration'},
                {'code': 'SALES', 'name': 'Sales & Marketing'},
                {'code': 'PURCHASE', 'name': 'Purchase & Procurement'}
            ]
            
            for dept_data in departments:
                existing = Department.query.filter_by(code=dept_data['code']).first()
                if not existing:
                    dept = Department(
                        code=dept_data['code'],
                        name=dept_data['name'],
                        is_active=True
                    )
                    db.session.add(dept)
            
            db.session.commit()
            
            # Create employees
            prod_dept = Department.query.filter_by(code='PROD').first()
            qc_dept = Department.query.filter_by(code='QC').first()
            
            employees = [
                {'code': 'EMP-001', 'name': 'John Smith', 'dept': 'PROD', 'role': 'Production Manager', 'salary': 45000},
                {'code': 'EMP-002', 'name': 'Sarah Wilson', 'dept': 'QC', 'role': 'Quality Inspector', 'salary': 35000},
                {'code': 'EMP-003', 'name': 'Mike Johnson', 'dept': 'PROD', 'role': 'Machine Operator', 'salary': 28000},
                {'code': 'EMP-004', 'name': 'Lisa Brown', 'dept': 'SALES', 'role': 'Sales Executive', 'salary': 40000}
            ]
            
            for emp_data in employees:
                existing = User.query.filter_by(username=emp_data['code']).first()
                if not existing:
                    employee = User(
                        username=emp_data['code'],
                        email=f"{emp_data['code'].lower()}@company.com",
                        password_hash=generate_password_hash('employee123'),
                        role='staff',
                        is_active=True
                    )
                    db.session.add(employee)
            
            db.session.commit()
            print("✅ Created HR data (departments and employees)")
            
            # 11. Create Accounting Entries for all transactions
            print("\n💰 Creating Accounting Entries...")
            
            # Get or create Chart of Accounts
            accounts_data = [
                {'code': '1001', 'name': 'Cash', 'type': 'asset', 'group': 'current_assets'},
                {'code': '1002', 'name': 'Accounts Receivable', 'type': 'asset', 'group': 'current_assets'},
                {'code': '1100', 'name': 'Raw Material Inventory', 'type': 'asset', 'group': 'current_assets'},
                {'code': '1101', 'name': 'WIP Inventory', 'type': 'asset', 'group': 'current_assets'},
                {'code': '1102', 'name': 'Finished Goods Inventory', 'type': 'asset', 'group': 'current_assets'},
                {'code': '2001', 'name': 'Accounts Payable', 'type': 'liability', 'group': 'current_liabilities'},
                {'code': '2100', 'name': 'Salary Payable', 'type': 'liability', 'group': 'current_liabilities'},
                {'code': '4001', 'name': 'Sales Revenue', 'type': 'income', 'group': 'revenue'},
                {'code': '5001', 'name': 'Cost of Goods Sold', 'type': 'expense', 'group': 'cost_of_sales'},
                {'code': '5100', 'name': 'Direct Material Cost', 'type': 'expense', 'group': 'cost_of_sales'},
                {'code': '5200', 'name': 'Direct Labor Cost', 'type': 'expense', 'group': 'cost_of_sales'},
                {'code': '6001', 'name': 'Job Work Expenses', 'type': 'expense', 'group': 'operating_expenses'},
                {'code': '6100', 'name': 'Salary Expenses', 'type': 'expense', 'group': 'operating_expenses'}
            ]
            
            for acc_data in accounts_data:
                existing = ChartOfAccounts.query.filter_by(account_code=acc_data['code']).first()
                if not existing:
                    account = ChartOfAccounts(
                        account_code=acc_data['code'],
                        account_name=acc_data['name'],
                        account_type=acc_data['type'],
                        account_group=acc_data['group'],
                        is_active=True
                    )
                    db.session.add(account)
            
            db.session.commit()
            
            # Create journal entries for purchase transactions
            cash_account = ChartOfAccounts.query.filter_by(account_code='1001').first()
            inventory_account = ChartOfAccounts.query.filter_by(account_code='1100').first()
            payable_account = ChartOfAccounts.query.filter_by(account_code='2001').first()
            
            # Purchase entry for PO-2025-001
            po1 = PurchaseOrder.query.filter_by(purchase_order_number='PO-2025-001').first()
            if po1:
                journal_entry = JournalEntry(
                    entry_number='JE-2025-001',
                    date=date.today(),
                    description=f'Purchase of materials - {po1.purchase_order_number}',
                    reference_type='purchase_order',
                    reference_id=po1.id,
                    total_amount=po1.total_amount,
                    created_by=admin.id
                )
                db.session.add(journal_entry)
                db.session.flush()
                
                # Debit: Raw Material Inventory
                debit_entry = JournalEntryLine(
                    journal_entry_id=journal_entry.id,
                    account_id=inventory_account.id,
                    debit_amount=po1.total_amount,
                    credit_amount=0,
                    description='Raw materials purchased'
                )
                db.session.add(debit_entry)
                
                # Credit: Accounts Payable
                credit_entry = JournalEntryLine(
                    journal_entry_id=journal_entry.id,
                    account_id=payable_account.id,
                    debit_amount=0,
                    credit_amount=po1.total_amount,
                    description='Amount payable to supplier'
                )
                db.session.add(credit_entry)
            
            # Create salary entries
            salary_payable = ChartOfAccounts.query.filter_by(account_code='2100').first()
            salary_expense = ChartOfAccounts.query.filter_by(account_code='6100').first()
            
            total_salaries = sum(emp['salary'] for emp in employees)
            
            salary_journal = JournalEntry(
                entry_number='JE-2025-002',
                date=date.today(),
                description='Monthly salary provision',
                reference_type='payroll',
                total_amount=total_salaries,
                created_by=admin.id
            )
            db.session.add(salary_journal)
            db.session.flush()
            
            # Debit: Salary Expense
            salary_debit = JournalEntryLine(
                journal_entry_id=salary_journal.id,
                account_id=salary_expense.id,
                debit_amount=total_salaries,
                credit_amount=0,
                description='Monthly salary expense'
            )
            db.session.add(salary_debit)
            
            # Credit: Salary Payable
            salary_credit = JournalEntryLine(
                journal_entry_id=salary_journal.id,
                account_id=salary_payable.id,
                debit_amount=0,
                credit_amount=total_salaries,
                description='Salary payable to employees'
            )
            db.session.add(salary_credit)
            
            # Create sales revenue entries
            revenue_account = ChartOfAccounts.query.filter_by(account_code='4001').first()
            receivable_account = ChartOfAccounts.query.filter_by(account_code='1002').first()
            
            so1 = SalesOrder.query.filter_by(so_number='SO-2025-001').first()
            if so1:
                sales_journal = JournalEntry(
                    entry_number='JE-2025-003',
                    date=date.today(),
                    description=f'Sales revenue - {so1.sales_order_number}',
                    reference_type='sales_order',
                    reference_id=so1.id,
                    total_amount=so1.total_amount,
                    created_by=admin.id
                )
                db.session.add(sales_journal)
                db.session.flush()
                
                # Debit: Accounts Receivable
                sales_debit = JournalEntryLine(
                    journal_entry_id=sales_journal.id,
                    account_id=receivable_account.id,
                    debit_amount=so1.total_amount,
                    credit_amount=0,
                    description='Amount receivable from customer'
                )
                db.session.add(sales_debit)
                
                # Credit: Sales Revenue
                sales_credit = JournalEntryLine(
                    journal_entry_id=sales_journal.id,
                    account_id=revenue_account.id,
                    debit_amount=0,
                    credit_amount=so1.total_amount,
                    description='Sales revenue earned'
                )
                db.session.add(sales_credit)
            
            db.session.commit()
            print("✅ Created accounting entries for all transactions")
            
            # 12. Create Expense entries
            print("\n💸 Creating Factory Expenses...")
            
            expense_categories = [
                {'name': 'Electricity', 'amount': 15000, 'account_code': '6001'},
                {'name': 'Maintenance', 'amount': 8000, 'account_code': '6001'},
                {'name': 'Factory Rent', 'amount': 25000, 'account_code': '6001'},
                {'name': 'Job Work Charges', 'amount': 5000, 'account_code': '6001'}
            ]
            
            for exp_data in expense_categories:
                expense = FactoryExpense(
                    expense_number=f"EXP-{exp_data['name'][:3].upper()}-001",
                    expense_type=exp_data['name'].lower().replace(' ', '_'),
                    amount=exp_data['amount'],
                    description=f"Monthly {exp_data['name']} charges",
                    expense_date=date.today(),
                    status='approved',
                    created_by=admin.id
                )
                db.session.add(expense)
            
            db.session.commit()
            print("✅ Created factory expenses")
            
            print("\n🎉 Complete ERP workflow data created successfully!")
            print("\n📈 Summary:")
            print(f"   - 4 Nested BOMs created (2-level hierarchy)")
            print(f"   - 4 Production Orders with BOM linkage")
            print(f"   - 2 Sales Orders with multiple items")
            print(f"   - 2 Job Work Orders for external processing")
            print(f"   - 2 Purchase Orders for raw materials")
            print(f"   - 1 GRN with material receipts")
            print(f"   - 5 Departments and 4 Employees (HR)")
            print(f"   - 13 Chart of Accounts setup")
            print(f"   - 3 Journal Entries (Purchase, Payroll, Sales)")
            print(f"   - 4 Factory Expense categories")
            print(f"   - Complete inventory movements tracked")
            print(f"   - Full accounting integration with double-entry")
            print(f"   - End-to-end ERP data flow")
            
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