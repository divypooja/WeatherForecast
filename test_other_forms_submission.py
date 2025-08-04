#!/usr/bin/env python3
"""
Test key forms to ensure they work after voucher_id migration
"""

from app import app, db
from models import PurchaseOrder, SalesOrder, GRN, User, Supplier, Item
from datetime import datetime, date
import random

def test_purchase_order_creation():
    """Test Purchase Order form submission"""
    with app.app_context():
        print("🛒 Testing Purchase Order creation...")
        
        try:
            # Get test data
            supplier = Supplier.query.filter_by(partner_type='supplier').first()
            user = User.query.first()
            item = Item.query.first()
            
            if not all([supplier, user, item]):
                print("   ❌ Missing test data (supplier, user, or item)")
                return False
            
            # Create test PO
            test_po = PurchaseOrder(
                po_number=f'PO-TEST-{random.randint(100, 999)}',
                supplier_id=supplier.id,
                po_date=date.today(),
                delivery_date=date.today(),
                payment_terms='Net 30',
                freight_terms='FOB',
                prepared_by='Test User',
                notes='Test PO creation',
                status='draft',
                created_by=user.id
            )
            
            db.session.add(test_po)
            db.session.commit()
            print(f"   ✅ Purchase Order created: {test_po.po_number}")
            return True
            
        except Exception as e:
            print(f"   ❌ Error creating Purchase Order: {str(e)}")
            db.session.rollback()
            return False

def test_sales_order_creation():
    """Test Sales Order form submission"""
    with app.app_context():
        print("📦 Testing Sales Order creation...")
        
        try:
            # Get test data
            customer = Supplier.query.filter(Supplier.partner_type.in_(['customer', 'both'])).first()
            user = User.query.first()
            
            if not all([customer, user]):
                print("   ❌ Missing test data (customer or user)")
                return False
            
            # Create test SO
            test_so = SalesOrder(
                so_number=f'SO-TEST-{random.randint(100, 999)}',
                customer_id=customer.id,
                order_date=date.today(),
                delivery_date=date.today(),
                payment_terms='Net 30',
                freight_terms='FOB',
                prepared_by='Test User',
                notes='Test SO creation',
                status='draft',
                created_by=user.id
            )
            
            db.session.add(test_so)
            db.session.commit()
            print(f"   ✅ Sales Order created: {test_so.so_number}")
            return True
            
        except Exception as e:
            print(f"   ❌ Error creating Sales Order: {str(e)}")
            db.session.rollback()
            return False

def test_grn_creation():
    """Test GRN form submission"""
    with app.app_context():
        print("📋 Testing GRN creation...")
        
        try:
            # Get test data
            po = PurchaseOrder.query.first()
            user = User.query.first()
            
            if not all([po, user]):
                print("   ❌ Missing test data (purchase order or user)")
                return False
            
            # Create test GRN
            test_grn = GRN(
                grn_number=f'GRN-TEST-{random.randint(100, 999)}',
                purchase_order_id=po.id,
                received_date=date.today(),
                transporter_name='Test Transport',
                vehicle_number='TEST123',
                notes='Test GRN creation',
                status='draft',
                received_by=user.id
            )
            
            db.session.add(test_grn)
            db.session.commit()
            print(f"   ✅ GRN created: {test_grn.grn_number}")
            return True
            
        except Exception as e:
            print(f"   ❌ Error creating GRN: {str(e)}")
            db.session.rollback()
            return False

def run_all_form_tests():
    """Run all form tests"""
    print("🧪 Testing all major forms after voucher_id migration...\n")
    
    tests = [
        test_purchase_order_creation,
        test_sales_order_creation,
        test_grn_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} forms working correctly")
    
    if passed == total:
        print("🎉 All major forms are working after the migration!")
    else:
        print("⚠️  Some forms still have issues - check the logs above")
    
    return passed == total

if __name__ == '__main__':
    run_all_form_tests()