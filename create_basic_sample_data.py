#!/usr/bin/env python3
"""
Basic Sample Data Creation Script for Factory Management System
Creates essential sample data for testing all modules
"""

from app import app, db
from models import User, Supplier, Item, Employee, PurchaseOrder, PurchaseOrderItem, SalesOrder, SalesOrderItem, JobWork, CompanySettings
from models_uom import UnitOfMeasure, UOMConversion, ItemUOMConversion
from datetime import datetime, timedelta
import random

def create_basic_sample_data():
    """Create basic sample data for testing"""
    
    with app.app_context():
        print("🚀 Creating basic sample data...")
        
        # 1. Create Admin User if not exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User()
            admin_user.username = 'admin'
            admin_user.email = 'admin@akinnovations.com'
            admin_user.role = 'admin'
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Admin user created")
        
        # 2. Create Staff User
        staff_user = User.query.filter_by(username='staff1').first()
        if not staff_user:
            staff_user = User()
            staff_user.username = 'staff1'
            staff_user.email = 'staff1@akinnovations.com'
            staff_user.role = 'staff'
            staff_user.set_password('staff123')
            db.session.add(staff_user)
            db.session.commit()
            print("✅ Staff user created")
        
        # 3. Setup Company Settings
        settings = CompanySettings.get_settings()
        settings.company_name = "AK Innovations Pvt Ltd"
        settings.address_line1 = "Industrial Area, Phase-2"
        settings.city = "Mumbai"
        settings.state = "Maharashtra"
        settings.pin_code = "400001"
        settings.phone = "+91-9876543210"
        settings.gst_number = "27ABCDE1234F1Z5"
        db.session.commit()
        print("✅ Company settings updated")
        
        # 4. Create Suppliers
        suppliers_data = [
            {
                'name': 'Steel Suppliers Ltd',
                'contact_person': 'Rajesh Kumar',
                'phone': '+91-9876543211',
                'email': 'rajesh@steelsuppliers.com',
                'partner_type': 'supplier'
            },
            {
                'name': 'Mumbai Engineering Works',
                'contact_person': 'Priya Sharma',
                'phone': '+91-9876543212',
                'email': 'priya@mumbaieng.com',
                'partner_type': 'both'
            },
            {
                'name': 'Precision Tools Ltd',
                'contact_person': 'Sunita Desai',
                'phone': '+91-9876543213',
                'email': 'sunita@precisiontools.com',
                'partner_type': 'customer'
            }
        ]
        
        for data in suppliers_data:
            existing = Supplier.query.filter_by(name=data['name']).first()
            if not existing:
                supplier = Supplier()
                for key, value in data.items():
                    setattr(supplier, key, value)
                db.session.add(supplier)
        
        db.session.commit()
        print("✅ Suppliers created")
        
        # 5. Create Items
        items_data = [
            {
                'code': 'ITEM-0001',
                'name': 'Steel Rod 12mm',
                'description': 'High grade steel rods',
                'unit_of_measure': 'Kg',
                'hsn_code': '72142000',
                'gst_rate': 18.0,
                'current_stock': 500.0,
                'minimum_stock': 100.0,
                'unit_price': 55.0,
                'item_type': 'material'
            },
            {
                'code': 'ITEM-0002',
                'name': 'Metal Bracket L-Type',
                'description': 'L-shaped metal brackets',
                'unit_of_measure': 'Pcs',
                'hsn_code': '73181500',
                'gst_rate': 18.0,
                'current_stock': 200.0,
                'minimum_stock': 50.0,
                'unit_price': 25.0,
                'item_type': 'material'
            },
            {
                'code': 'ITEM-0003',
                'name': 'Castor Wheel 50mm',
                'description': 'Heavy duty castor wheels',
                'unit_of_measure': 'Pcs',
                'hsn_code': '87089900',
                'gst_rate': 18.0,
                'current_stock': 150.0,
                'minimum_stock': 30.0,
                'unit_price': 45.0,
                'item_type': 'product'
            },
            {
                'code': 'ITEM-0004',
                'name': 'Industrial Paint',
                'description': 'High quality industrial paint',
                'unit_of_measure': 'L',
                'hsn_code': '32081010',
                'gst_rate': 18.0,
                'current_stock': 80.0,
                'minimum_stock': 20.0,
                'unit_price': 150.0,
                'item_type': 'material'
            }
        ]
        
        for data in items_data:
            existing = Item.query.filter_by(code=data['code']).first()
            if not existing:
                item = Item()
                for key, value in data.items():
                    setattr(item, key, value)
                db.session.add(item)
        
        db.session.commit()
        print("✅ Items created")
        
        # 6. Create Employees
        employees_data = [
            {
                'employee_code': 'EMP-0001',
                'name': 'Ramesh Gupta',
                'designation': 'Production Manager',
                'department': 'Production',
                'salary_type': 'monthly',
                'rate': 45000.0,
                'phone': '+91-9876543220',
                'joining_date': datetime.now().date() - timedelta(days=365)
            },
            {
                'employee_code': 'EMP-0002', 
                'name': 'Kavita Singh',
                'designation': 'Quality Inspector',
                'department': 'Quality Control',
                'salary_type': 'monthly',
                'rate': 35000.0,
                'phone': '+91-9876543221',
                'joining_date': datetime.now().date() - timedelta(days=200)
            }
        ]
        
        for data in employees_data:
            existing = Employee.query.filter_by(employee_code=data['employee_code']).first()
            if not existing:
                employee = Employee()
                for key, value in data.items():
                    setattr(employee, key, value)
                db.session.add(employee)
        
        db.session.commit()
        print("✅ Employees created")
        
        # 7. Create Purchase Orders
        suppliers = Supplier.query.filter(Supplier.partner_type.in_(['supplier', 'both'])).all()
        items = Item.query.all()
        
        if suppliers and items:
            for i in range(3):
                supplier = suppliers[i % len(suppliers)]
                po = PurchaseOrder()
                po.po_number = f"PO-2025-{i+1:04d}"
                po.supplier_id = supplier.id
                po.po_date = datetime.now().date() - timedelta(days=random.randint(1, 30))
                po.delivery_date = datetime.now().date() + timedelta(days=random.randint(7, 21))
                po.status = ['draft', 'approved', 'received'][i]
                po.notes = f'Sample Purchase Order {i+1}'
                po.total_amount = 0.0
                po.created_by = admin_user.id
                db.session.add(po)
                db.session.commit()
                
                # Add PO Items
                selected_items = items[:2]  # Use first 2 items
                total_amount = 0.0
                
                for item in selected_items:
                    quantity = random.randint(10, 50)
                    rate = item.unit_price
                    amount = quantity * rate
                    total_amount += amount
                    
                    po_item = PurchaseOrderItem()
                    po_item.purchase_order_id = po.id
                    po_item.item_id = item.id
                    po_item.quantity = quantity
                    po_item.unit_price = rate
                    po_item.total_price = amount
                    po_item.hsn_code = item.hsn_code
                    po_item.gst_rate = item.gst_rate
                    po_item.specification = f'Standard {item.name}'
                    # Legacy fields
                    po_item.quantity_ordered = quantity
                    po_item.qty = quantity
                    po_item.rate = rate
                    po_item.amount = amount
                    db.session.add(po_item)
                
                po.total_amount = total_amount
                db.session.commit()
        
        print("✅ Purchase Orders created")
        
        # 8. Create Sales Orders
        customers = Supplier.query.filter(Supplier.partner_type.in_(['customer', 'both'])).all()
        
        if customers and items:
            for i in range(2):
                customer = customers[i % len(customers)]
                so = SalesOrder()
                so.so_number = f"SO-2025-{i+1:04d}"
                so.customer_id = customer.id
                so.order_date = datetime.now().date() - timedelta(days=random.randint(1, 20))
                so.delivery_date = datetime.now().date() + timedelta(days=random.randint(10, 30))
                so.status = ['draft', 'confirmed'][i]
                so.notes = f'Sample Sales Order {i+1}'
                so.total_amount = 0.0
                so.created_by = admin_user.id
                db.session.add(so)
                db.session.commit()
                
                # Add SO Items
                selected_items = items[2:4]  # Use product items
                total_amount = 0.0
                
                for item in selected_items:
                    quantity = random.randint(5, 25)
                    rate = item.unit_price * 1.3  # Sales markup
                    amount = quantity * rate
                    total_amount += amount
                    
                    so_item = SalesOrderItem()
                    so_item.sales_order_id = so.id
                    so_item.item_id = item.id
                    so_item.quantity_ordered = quantity
                    so_item.unit_price = rate
                    so_item.total_price = amount
                    db.session.add(so_item)
                
                so.total_amount = total_amount
                db.session.commit()
        
        print("✅ Sales Orders created")
        
        # 9. Create Job Work Orders
        if suppliers and items:
            for i in range(2):
                supplier = suppliers[i % len(suppliers)]
                item = items[i % len(items)]
                
                jobwork = JobWork()
                jobwork.job_number = f"JOB-2025-{i+1:04d}"
                jobwork.customer_name = supplier.name
                jobwork.item_id = item.id
                jobwork.quantity_sent = random.randint(20, 100)
                jobwork.rate_per_unit = random.randint(10, 50)
                jobwork.sent_date = datetime.now().date() - timedelta(days=random.randint(1, 15))
                jobwork.expected_return = datetime.now().date() + timedelta(days=random.randint(7, 21))
                jobwork.status = ['sent', 'completed'][i]
                jobwork.notes = f'Sample Job Work {i+1}'
                jobwork.created_by = admin_user.id
                
                if jobwork.status == 'completed':
                    jobwork.quantity_received = jobwork.quantity_sent - random.randint(0, 5)
                    jobwork.received_date = datetime.now().date() - timedelta(days=random.randint(1, 7))
                
                db.session.add(jobwork)
        
        db.session.commit()
        print("✅ Job Work Orders created")
        
        print("\n✅ Basic sample data creation completed!")
        print(f"👤 Users: {User.query.count()}")
        print(f"🤝 Suppliers: {Supplier.query.count()}")
        print(f"📦 Items: {Item.query.count()}")
        print(f"👨‍💼 Employees: {Employee.query.count()}")
        print(f"📋 Purchase Orders: {PurchaseOrder.query.count()}")
        print(f"💰 Sales Orders: {SalesOrder.query.count()}")
        print(f"🔧 Job Work Orders: {JobWork.query.count()}")

if __name__ == '__main__':
    create_basic_sample_data()