#!/usr/bin/env python3
"""
Create sample data for testing the Admin Approvals Dashboard
"""

import os
import sys
from datetime import datetime, date, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Item, Supplier, PurchaseOrder, PurchaseOrderItem, Production, SalesOrder, SalesOrderItem
from werkzeug.security import generate_password_hash

def create_sample_approval_data():
    """Create sample data that requires approval"""
    app = create_app()
    
    with app.app_context():
        # Create admin user if not exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@factory.com',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin_user)
        
        # Create staff user if not exists
        staff_user = User.query.filter_by(username='staff').first()
        if not staff_user:
            staff_user = User(
                username='staff',
                email='staff@factory.com',
                password_hash=generate_password_hash('staff123'),
                role='staff'
            )
            db.session.add(staff_user)
        
        # Create supplier if not exists
        supplier = Supplier.query.filter_by(name='ABC Suppliers Ltd').first()
        if not supplier:
            supplier = Supplier(
                name='ABC Suppliers Ltd',
                contact_person='John Doe',
                email='john@abcsuppliers.com',
                phone='9876543210',
                address='123 Industrial Area, Mumbai',
                partner_type='supplier'
            )
            db.session.add(supplier)
        
        # Create items if not exist
        items = []
        item_names = ['Steel Rod 12mm', 'Aluminum Sheet', 'Copper Wire', 'Plastic Component']
        for item_name in item_names:
            item = Item.query.filter_by(name=item_name).first()
            if not item:
                item = Item(
                    name=item_name,
                    code=f'ITM-{len(items)+1:03d}',
                    item_type='raw_material',
                    unit_of_measure='KG',
                    unit_price=100.0 + len(items) * 50,
                    minimum_stock=10,
                    current_stock=50
                )
                db.session.add(item)
            items.append(item)
        
        db.session.commit()
        
        # Create Purchase Orders needing approval
        po_statuses = ['draft', 'sent']
        for i in range(3):
            po_number = f'PO-2025-{1000 + i:04d}'
            existing_po = PurchaseOrder.query.filter_by(po_number=po_number).first()
            if not existing_po:
                po = PurchaseOrder(
                    po_number=po_number,
                    supplier_id=supplier.id,
                    order_date=date.today() - timedelta(days=i),
                    status=po_statuses[i % 2],
                    prepared_by='staff',
                    approved_by='' if i < 2 else 'admin',  # First 2 need approval
                    created_by=staff_user.id,
                    subtotal=5000 + i * 1000,
                    gst_amount=900 + i * 180,
                    total_amount=5900 + i * 1180
                )
                db.session.add(po)
                db.session.flush()
                
                # Add items to PO with all required fields
                for j, item in enumerate(items[:2]):
                    qty = 10 + j * 5
                    rate = item.unit_price
                    amount = rate * qty
                    poi = PurchaseOrderItem(
                        purchase_order_id=po.id,
                        item_id=item.id,
                        qty=qty,
                        rate=rate,
                        amount=amount,
                        quantity_ordered=qty,
                        unit_price=rate,
                        total_price=amount,
                        uom=item.unit_of_measure,
                        hsn_code='1234'
                    )
                    db.session.add(poi)
        
        # Create Production Orders needing approval
        for i in range(2):
            prod_number = f'PROD-2025-{2000 + i:04d}'
            existing_prod = Production.query.filter_by(production_number=prod_number).first()
            if not existing_prod:
                production = Production(
                    production_number=prod_number,
                    item_id=items[0].id,
                    quantity_to_produce=100 + i * 50,
                    production_date=date.today() + timedelta(days=i + 1),
                    status='planned',  # Needs approval
                    created_by=staff_user.id,
                    notes=f'Batch production for {items[0].name}'
                )
                db.session.add(production)
        
        # Create Sales Orders needing approval
        for i in range(2):
            so_number = f'SO-2025-{3000 + i:04d}'
            existing_so = SalesOrder.query.filter_by(so_number=so_number).first()
            if not existing_so:
                so = SalesOrder(
                    so_number=so_number,
                    customer_id=supplier.id,  # Using supplier as customer for demo
                    order_date=date.today() - timedelta(days=i),
                    status='draft' if i == 0 else 'pending',
                    prepared_by='staff',
                    approved_by='' if i == 0 else None,
                    created_by=staff_user.id,
                    subtotal=8000 + i * 2000,
                    gst_amount=1440 + i * 360,
                    total_amount=9440 + i * 2360
                )
                db.session.add(so)
                db.session.flush()
                
                # Add items to SO
                soi = SalesOrderItem(
                    sales_order_id=so.id,
                    item_id=items[i].id,
                    qty=20 + i * 10,
                    rate=items[i].unit_price * 1.5,  # Selling price
                    amount=(items[i].unit_price * 1.5) * (20 + i * 10)
                )
                db.session.add(soi)
        
        db.session.commit()
        print("✓ Sample approval data created successfully!")
        print("\nCreated:")
        print("- 2 Purchase Orders needing approval (PO-2025-1000, PO-2025-1001)")
        print("- 2 Production Orders needing approval (PROD-2025-2000, PROD-2025-2001)")
        print("- 1 Sales Order needing approval (SO-2025-3000)")
        print("\nLogin as admin/admin123 to access the Admin Approvals Dashboard")

if __name__ == '__main__':
    create_sample_approval_data()