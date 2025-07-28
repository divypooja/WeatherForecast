#!/usr/bin/env python3

"""
Debug Job Work Creation Issues
Test job work creation functionality and identify the problem
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import JobWork, Item, Supplier
from forms import JobWorkForm
from datetime import datetime, date

def debug_jobwork_creation():
    """Debug job work creation process"""
    
    with app.app_context():
        print("=== DEBUGGING JOB WORK CREATION ===")
        
        # Check items
        items = Item.query.all()
        print(f"\nAvailable Items: {len(items)}")
        for item in items[:5]:
            print(f"  - {item.code}: {item.name} (Raw: {item.qty_raw}, Stock: {item.current_stock})")
        
        # Check suppliers
        suppliers = Supplier.query.all()
        print(f"\nAvailable Suppliers: {len(suppliers)}")
        for supplier in suppliers[:5]:
            print(f"  - {supplier.name}")
        
        # Test form creation
        print("\n=== TESTING FORM ===")
        try:
            form = JobWorkForm()
            print(f"Form created successfully")
            print(f"Item choices: {len(form.item_id.choices)}")
            print(f"Customer choices: {len(form.customer_name.choices)}")
        except Exception as e:
            print(f"Form creation failed: {e}")
            return
        
        # Test job work creation manually
        print("\n=== TESTING MANUAL JOB WORK CREATION ===")
        try:
            # Get test data
            test_item = Item.query.filter_by(code='STEEL-001').first()
            test_supplier = Supplier.query.first()
            
            if not test_item:
                print("ERROR: Steel Plate test item not found")
                return
            if not test_supplier:
                print("ERROR: No suppliers found")
                return
            
            print(f"Using item: {test_item.name}")
            print(f"Using supplier: {test_supplier.name}")
            print(f"Item raw stock: {test_item.qty_raw}")
            
            # Create job work manually
            job = JobWork(
                job_number="TEST-2025-001",
                customer_name=test_supplier.name,
                item_id=test_item.id,
                process="Cutting",
                work_type="outsourced",
                quantity_sent=10.0,
                rate_per_unit=5.0,
                sent_date=date.today(),
                created_by=1  # Assuming admin user exists
            )
            
            db.session.add(job)
            db.session.commit()
            print("✓ Manual job work creation SUCCESSFUL!")
            
            # Test inventory update
            if test_item.move_to_wip(10.0):
                db.session.commit()
                print("✓ Inventory move_to_wip SUCCESSFUL!")
                print(f"  Raw: {test_item.qty_raw}, WIP: {test_item.qty_wip}")
            else:
                print("✗ Inventory move_to_wip FAILED!")
            
        except Exception as e:
            print(f"Manual creation failed: {e}")
            db.session.rollback()
            return
        
        print("\n=== JOB WORK CREATION WORKING! ===")
        print("The issue might be in the form validation or web form processing.")

if __name__ == "__main__":
    debug_jobwork_creation()